import sys
import threading
import time

import cv2
from PySide2.QtCore import QRect
from PySide2.QtGui import (QPainter, QBrush, QColor, QImage, QPixmap, Qt, QFont,
                           QPen)
from PySide2.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout,
                               QHBoxLayout, QWidget, QGroupBox, QLabel,
                               QLineEdit, QApplication, QFileDialog, QCheckBox, QComboBox,
                               QGridLayout, QListView, QDoubleSpinBox)

import msg_box
from gb import GLOBAL
from yolo import YOLO5


def thread_runner(func):
    """多线程"""

    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs).start()

    return wrapper


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('YOLOv5 Object Detection')
        self.setMinimumSize(1200, 800)

        GLOBAL.init_config()

        self.camera = WidgetCamera()  # 摄像头
        self.config = WidgetConfig()  # Yolo配置界面

        self.btn_camera = QPushButton('开启/关闭摄像头')  # 开启或关闭摄像头
        self.btn_camera.setFixedHeight(60)
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.config)
        vbox1.addStretch()
        vbox1.addWidget(self.btn_camera)

        self.btn_camera.clicked.connect(self.oc_camera)

        hbox = QHBoxLayout()
        hbox.addWidget(self.camera, 3)
        hbox.addLayout(vbox1, 1)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)

        self.central_widget = QWidget()
        self.central_widget.setLayout(vbox)

        self.setCentralWidget(self.central_widget)
        self.show()

    def oc_camera(self):
        if self.camera.cap.isOpened():
            self.camera.close_camera()  # 关闭摄像头
        else:
            self.camera.open_camera(
                use_camera=self.config.check_camera.isChecked(),
                video=self.config.line_video.text()
            )
            self.camera.show_camera()

            # 目标检测
            self.config.save_config()
            check = self.camera.yolo.set_config(
                weights=GLOBAL.config['weights'],
                device=GLOBAL.config['device'],
                img_size=GLOBAL.config['img_size'],
                conf=GLOBAL.config['conf_thresh'],
                iou=GLOBAL.config['iou_thresh'],
                agnostic=GLOBAL.config['agnostic'],
                augment=GLOBAL.config['augment']
            )
            if not check:
                msg = msg_box.MsgWarning()
                msg.setText('配置信息有误，无法正常加载YOLO模型！')
                msg.exec()
                return
            self.camera.yolo.load_model()
            self.camera.start_detect()

    def resizeEvent(self, event):
        self.update()

    def closeEvent(self, event):
        if self.camera.cap.isOpened():
            self.camera.close_camera()


class WidgetCamera(QWidget):
    def __init__(self):
        super(WidgetCamera, self).__init__()

        self.yolo = YOLO5()

        self.opened = False  # 摄像头已打开
        self.cap = cv2.VideoCapture()

        self.pix_image = None  # QPixmap视频帧
        self.image = None  # 当前读取到的图片
        self.scale = 1  # 比例
        self.objects = []

        self.fps = 0  # 帧率

    def open_camera(self, use_camera, video):
        """打开摄像头，成功打开返回True"""
        cam = 0  # 默认摄像头
        if not use_camera:
            cam = video  # 视频流文件
        flag = self.cap.open(cam)  # 打开camera
        if flag:
            self.opened = True  # 已打开
            return True
        else:
            msg = msg_box.MsgWarning()
            msg.setText('视频流开启失败！\n'
                        '请确保摄像头已打开或视频文件真实存在！')
            msg.exec()
            return False

    def close_camera(self):
        self.opened = False  # 先关闭目标检测线程再关闭摄像头
        self.cap.release()

    @thread_runner
    def show_camera(self):
        while self.opened:
            self.read_image()
            time.sleep(0.033)  # 每33毫秒(对应30帧的视频)执行一次show_camera方法
            self.update()

    def read_image(self):
        ret, image = self.cap.read()
        if ret:
            # 删去最后一层
            if image.shape[2] == 4:
                image = image[:, :, :-1]
            self.image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # image

    @thread_runner
    def start_detect(self):
        # 初始化yolo参数
        while self.opened:
            if self.image is None:
                continue
            # 检测
            t0 = time.time()
            self.objects = self.yolo.obj_detect(self.image)
            t1 = time.time()
            self.fps = 1 / (t1 - t0)
            self.update()

    def resizeEvent(self, event):
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        qp.setWindow(0, 0, self.width(), self.height())  # 设置窗口
        # 画框架背景
        qp.setBrush(QColor('#cecece'))  # 框架背景色
        qp.setPen(Qt.NoPen)
        rect = QRect(0, 0, self.width(), self.height())
        qp.drawRect(rect)

        sw, sh = self.width(), self.height()  # 图像窗口宽高
        pw, ph = 0, 0  # 缩放后的QPixmap大小

        # 画图
        yh = 0
        if self.image is not None:
            ih, iw, _ = self.image.shape
            self.scale = sw / iw if sw / iw < sh / ih else sh / ih  # 缩放比例
            yh = round((self.height() - ih * self.scale) / 2)
            qimage = QImage(self.image.data, iw, ih, 3 * iw, QImage.Format_RGB888)  # 转QImage
            qpixmap = QPixmap.fromImage(qimage.scaled(self.width(), self.height(), Qt.KeepAspectRatio))  # 转QPixmap
            pw, ph = qpixmap.width(), qpixmap.height()
            qp.drawPixmap(0, yh, qpixmap)

        font = QFont()
        font.setFamily('Microsoft YaHei')
        if self.fps > 0:
            font.setPointSize(14)
            qp.setFont(font)
            pen = QPen()
            pen.setColor(Qt.white)
            qp.setPen(pen)
            qp.drawText(self.width() - 150, yh + 40, 'FPS: ' + str(round(self.fps, 2)))

        # 画目标框
        pen = QPen()
        pen.setWidth(2)  # 边框宽度
        for obj in self.objects:
            font.setPointSize(10)
            qp.setFont(font)
            rgb = [round(c) for c in obj['color']]
            pen.setColor(QColor(rgb[0], rgb[1], rgb[2]))  # 边框颜色
            brush1 = QBrush(Qt.NoBrush)  # 内部不填充
            qp.setBrush(brush1)
            qp.setPen(pen)
            # 坐标 宽高
            tx, ty = round(pw * obj['x']), yh + round(ph * obj['y'])
            tw, th = round(pw * obj['w']), round(ph * obj['h'])
            obj_rect = QRect(tx, ty, tw, th)
            qp.drawRect(obj_rect)  # 画矩形框
            # 画 类别 和 置信度
            qp.drawText(tx, ty - 5, str(obj['class']) + str(round(obj['confidence'], 2)))


class WidgetConfig(QGroupBox):
    def __init__(self):
        super(WidgetConfig, self).__init__()

        HEIGHT = 30

        grid = QGridLayout()

        # 使用默认摄像头复选框
        self.check_camera = QCheckBox('Use default camera')
        self.check_camera.setChecked(True)
        self.check_camera.stateChanged.connect(self.slot_check_camera)

        grid.addWidget(self.check_camera, 0, 0, 1, 3)  # 一行三列

        # 选择视频文件
        label_video = QLabel('Source')
        self.line_video = QLineEdit()
        if 'video' in GLOBAL.config:
            self.line_video.setText(GLOBAL.config['video'])
        self.line_video.setFixedHeight(HEIGHT)
        self.line_video.setEnabled(False)
        self.line_video.editingFinished.connect(lambda: GLOBAL.record_config(
            {'video': self.line_video.text()}
        ))

        self.btn_video = QPushButton('Choose')
        self.btn_video.setFixedHeight(HEIGHT)
        self.btn_video.setEnabled(False)
        self.btn_video.clicked.connect(self.choose_video_file)

        self.slot_check_camera()

        grid.addWidget(label_video, 1, 0)
        grid.addWidget(self.line_video, 1, 1)
        grid.addWidget(self.btn_video, 1, 2)

        # 选择权重文件
        label_weights = QLabel('Weights')
        self.line_weights = QLineEdit()
        if 'weights' in GLOBAL.config:
            self.line_weights.setText(GLOBAL.config['weights'])
        self.line_weights.setFixedHeight(HEIGHT)
        self.line_weights.editingFinished.connect(lambda: GLOBAL.record_config(
            {'weights': self.line_weights.text()}
        ))

        self.btn_weights = QPushButton('Choose')
        self.btn_weights.setFixedHeight(HEIGHT)
        self.btn_weights.clicked.connect(self.choose_weights_file)

        grid.addWidget(label_weights, 2, 0)
        grid.addWidget(self.line_weights, 2, 1)
        grid.addWidget(self.btn_weights, 2, 2)

        # 是否使用GPU
        label_device = QLabel('CUDA device')
        self.line_device = QLineEdit('cpu')
        if 'device' in GLOBAL.config:
            self.line_device.setText(GLOBAL.config['device'])
        else:
            self.line_device.setText('cpu')
        self.line_device.setPlaceholderText('cpu or 0 or 0,1,2,3')
        self.line_device.setFixedHeight(HEIGHT)
        self.line_device.editingFinished.connect(lambda: GLOBAL.record_config(
            {'device': self.line_device.text()}
        ))

        grid.addWidget(label_device, 3, 0)
        grid.addWidget(self.line_device, 3, 1, 1, 2)

        # 设置图像大小
        label_size = QLabel('Img Size')
        self.combo_size = QComboBox()
        self.combo_size.setFixedHeight(HEIGHT)
        self.combo_size.setStyleSheet(
            'QAbstractItemView::item {height: 40px;}')
        self.combo_size.setView(QListView())
        self.combo_size.addItem('320', 320)
        self.combo_size.addItem('416', 416)
        self.combo_size.addItem('480', 480)
        self.combo_size.addItem('544', 544)
        self.combo_size.addItem('640', 640)
        self.combo_size.setCurrentIndex(2)
        self.combo_size.currentIndexChanged.connect(lambda: GLOBAL.record_config(
            {'img_size': self.combo_size.currentData()}
        ))

        grid.addWidget(label_size, 4, 0)
        grid.addWidget(self.combo_size, 4, 1, 1, 2)

        # 设置置信度阈值
        label_conf = QLabel('Confidence')
        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setFixedHeight(HEIGHT)
        self.spin_conf.setDecimals(1)
        self.spin_conf.setRange(0.1, 0.9)
        self.spin_conf.setSingleStep(0.1)
        if 'conf_thresh' in GLOBAL.config:
            self.spin_conf.setValue(GLOBAL.config['conf_thresh'])
        else:
            self.spin_conf.setValue(0.4)  # 默认值
            GLOBAL.record_config({'conf_thresh': 0.4})
        self.spin_conf.valueChanged.connect(lambda: GLOBAL.record_config(
            {'conf_thresh': round(self.spin_conf.value(), 1)}
        ))

        grid.addWidget(label_conf, 5, 0)
        grid.addWidget(self.spin_conf, 5, 1, 1, 2)

        # 设置IOU阈值
        label_iou = QLabel('IOU')
        self.spin_iou = QDoubleSpinBox()
        self.spin_iou.setFixedHeight(HEIGHT)
        self.spin_iou.setDecimals(1)
        self.spin_iou.setRange(0.1, 0.9)
        self.spin_iou.setSingleStep(0.1)
        if 'iou_thresh' in GLOBAL.config:
            self.spin_iou.setValue(GLOBAL.config['iou_thresh'])
        else:
            self.spin_iou.setValue(0.5)  # 默认值
            GLOBAL.record_config({'iou_thresh': 0.5})
        self.spin_iou.valueChanged.connect(lambda: GLOBAL.record_config(
            {'iou_thresh': round(self.spin_iou.value(), 1)}
        ))

        grid.addWidget(label_iou, 6, 0)
        grid.addWidget(self.spin_iou, 6, 1, 1, 2)

        # class-agnostic NMS
        self.check_agnostic = QCheckBox('Agnostic')
        if 'agnostic' in GLOBAL.config:
            self.check_agnostic.setChecked(GLOBAL.config['agnostic'])
        else:
            self.check_agnostic.setChecked(True)
        self.check_agnostic.stateChanged.connect(lambda: GLOBAL.record_config(
            {'agnostic': self.check_agnostic.isChecked()}
        ))

        grid.addWidget(self.check_agnostic, 7, 0, 1, 3)  # 一行三列

        # augmented inference
        self.check_augment = QCheckBox('Augment')
        if 'augment' in GLOBAL.config:
            self.check_augment.setChecked(GLOBAL.config['augment'])
        else:
            self.check_augment.setChecked(True)
        self.check_augment.stateChanged.connect(lambda: GLOBAL.record_config(
            {'augment': self.check_augment.isChecked()}
        ))

        grid.addWidget(self.check_augment, 8, 0, 1, 3)  # 一行三列

        self.setLayout(grid)  # 设置布局

    def slot_check_camera(self):
        check = self.check_camera.isChecked()
        GLOBAL.record_config({'use_camera': check})  # 保存配置
        if check:
            self.line_video.setEnabled(False)
            self.btn_video.setEnabled(False)
        else:
            self.line_video.setEnabled(True)
            self.btn_video.setEnabled(True)

    def choose_weights_file(self):
        """从系统中选择权重文件"""
        file = QFileDialog.getOpenFileName(self, "Pre-trained YOLOv5 Weights", "./",
                                           "Weights Files (*.pt);;All Files (*)")
        if file[0] != '':
            self.line_weights.setText(file[0])
            GLOBAL.record_config({'weights': file[0]})

    def choose_video_file(self):
        """从系统中选择视频文件"""
        file = QFileDialog.getOpenFileName(self, "Video Files", "./",
                                           "Video Files (*)")
        if file[0] != '':
            self.line_video.setText(file[0])
            GLOBAL.record_config({'video': file[0]})

    def save_config(self):
        """保存当前的配置到配置文件"""
        config = {
            'use_camera': self.check_camera.isChecked(),
            'video': self.line_video.text(),
            'weights': self.line_weights.text(),
            'device': self.line_device.text(),
            'img_size': self.combo_size.currentData(),
            'conf_thresh': round(self.spin_conf.value(), 1),
            'iou_thresh': round(self.spin_iou.value(), 1),
            'agnostic': self.check_agnostic.isChecked(),
            'augment': self.check_augment.isChecked()
        }
        GLOBAL.record_config(config)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
