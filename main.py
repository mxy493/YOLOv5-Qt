import json
import sys
import threading
import time
import cv2
from PySide2.QtCore import QTimer, QRect
from PySide2.QtGui import (QPainter, QBrush, QColor, QImage, QPixmap, Qt, QFont,
                           QPen)
from PySide2.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout,
                               QHBoxLayout, QWidget, QGroupBox, QLabel,
                               QLineEdit, QApplication, QFileDialog, QCheckBox, QComboBox)

import msg_box
from gb import GLOBAL
from detect import Yolo5


def thread_runner(func):
    """多线程"""

    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs).start()

    return wrapper


def init_config():
    try:
        with open('config/config.json', 'r') as file_settings:
            GLOBAL.config = json.loads(file_settings.read())
    except FileNotFoundError as err_file:
        print('配置文件不存在: ' + str(err_file))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('YOLOv5目标检测')
        self.setMinimumSize(1200, 800)

        init_config()

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
            self.camera.close_camera()
        else:
            if self.config.check.isChecked():
                self.camera.cam = 0
            else:
                self.camera.cam = self.config.line_video.text()
            self.camera.open_camera()
            self.camera.show_camera()

            # 目标检测
            opt = self.get_yolo_config()
            self.camera.start_detect(opt)

            self.save_config()  # 保存配置

    def get_yolo_config(self):
        # 设置视频
        opt = {
            'weights': self.config.line_weight.text(),
            'output': 'inference/output',
            'img_size': self.config.combo_size.currentData(),
            'conf_thresh': 0.4,
            'iou_thresh': 0.5,
            'device': '',
            'view_img': True,
            'classes': '',
            'agnostic_nms': True,
            'augment': True,
        }
        return opt

    def save_config(self):
        GLOBAL.record_config('video', self.config.line_video.text())
        GLOBAL.record_config('weight', self.config.line_weight.text())
        GLOBAL.record_config('size', self.config.combo_size.currentData())

    def resizeEvent(self, event):
        self.update()

    def closeEvent(self, event):
        if self.camera.cap.isOpened():
            self.camera.close_camera()


class WidgetCamera(QWidget):
    def __init__(self):
        super(WidgetCamera, self).__init__()

        self.yolo = Yolo5()
        self.can_yolo = False  # yolo是否配置正确

        self.setStyleSheet('background-color: #cecece')

        self.opened = False  # 摄像头已打开
        self.cap = cv2.VideoCapture()
        self.cam = 0  # 摄像头序号或视频文件，0为默认摄像头
        self.timer_camera = QTimer()

        self.pix_image = None  # QPixmap视频帧
        self.image = None  # 当前读取到的图片
        self.scale = 1  # 比例
        self.objects = []

        self.fps = 0  # 帧率

    def open_camera(self):
        """打开摄像头，成功打开返回True"""
        flag = self.cap.open(self.cam)  # 打开一个视频
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
        self.timer_camera.stop()
        self.cap.release()
        self.opened = False  # 已关闭
        self.can_yolo = False

    @thread_runner
    def show_camera(self):
        while self.opened:
            self.read_image()
            time.sleep(0.033)  # 每33毫秒(对应30帧的视频)执行一次show_camera方法
            self.update()

    def read_image(self):
        retval, image = self.cap.read()
        if retval:
            # 删去最后一层
            if image.shape[2] == 4:
                image = image[:, :, :-1]
            self.image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # image

    @thread_runner
    def start_detect(self, opt):
        if not self.yolo.init_opt(opt):
            self.can_yolo = False
            msg = msg_box.MsgWarning()
            msg.setText('YOLO配置异常！')
            msg.exec()  # 此处会阻塞
            return
        else:
            self.can_yolo = True
        self.yolo.init_opt(opt)
        # 初始化yolo参数
        time0 = time.time()
        while self.opened:
            if self.image is None:
                continue
            # 检测
            self.objects = self.yolo.obj_detect(self.image)
            time1 = time.time()
            tt = time1 - time0
            self.fps = 1 / tt
            self.update()
            time0 = time1

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
        brush0 = QBrush(QColor('#cecece'))  # 框架背景色
        qp.setBrush(brush0)
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

        # 使用默认摄像头复选框
        self.check = QCheckBox('使用默认摄像头')
        self.check.setChecked(True)
        self.check.stateChanged.connect(self.check_state_changed)

        # 选择视频文件
        label_video = QLabel('视频文件')
        self.line_video = QLineEdit()
        self.line_video.setEnabled(False)
        self.btn_video = QPushButton('选择文件')
        self.btn_video.setEnabled(False)
        self.btn_video.clicked.connect(self.choose_video_file)
        hboxa = QHBoxLayout()
        hboxa.addWidget(label_video)
        hboxa.addWidget(self.line_video)
        hboxa.addWidget(self.btn_video)

        # 选择权重文件
        label_weight = QLabel('Weights')
        self.line_weight = QLineEdit()
        self.line_weight.editingFinished.connect(
            lambda: GLOBAL.record_config('weights', self.line_weight.text()))
        self.btn_weight = QPushButton('选择文件')
        self.btn_weight.clicked.connect(self.choose_weights_file)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(label_weight)
        hbox1.addWidget(self.line_weight)
        hbox1.addWidget(self.btn_weight)

        # 设置图像大小
        label_size = QLabel('Size')
        self.combo_size = QComboBox()
        self.combo_size.addItem('320', 320)
        self.combo_size.addItem('416', 416)
        self.combo_size.addItem('480', 480)
        self.combo_size.addItem('544', 544)
        self.combo_size.addItem('640', 640)
        self.combo_size.setCurrentIndex(2)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(label_size)
        hbox2.addWidget(self.combo_size)

        vbox = QVBoxLayout()
        vbox.addWidget(self.check)
        vbox.addLayout(hboxa)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)

        self.init_config()  # 初始化配置

    def init_config(self):
        try:
            self.line_video.setText(GLOBAL.config['video'])
            self.line_weight.setText(GLOBAL.config['weight'])
            self.combo_size.setCurrentIndex(
                self.combo_size.findData(GLOBAL.config['size']))
        except KeyError as err_key:
            print('参数项不存在: ' + str(err_key))

    def check_state_changed(self):
        if self.check.isChecked():
            self.line_video.setEnabled(False)
            self.btn_video.setEnabled(False)
        else:
            self.line_video.setEnabled(True)
            self.btn_video.setEnabled(True)

    def choose_weights_file(self):
        """从系统中选择权重文件"""
        file = QFileDialog.getOpenFileName(self, "Pre-trained YOLO weights", "./",
                                           "Weights Files (*.pt);;All Files (*)")
        self.line_weight.setText(file[0])
        GLOBAL.record_config('weights', file[0])

    def choose_video_file(self):
        """从系统中选择视频文件"""
        file = QFileDialog.getOpenFileName(self, "Pre-trained YOLO weights", "./",
                                           "Video Files (*)")
        self.line_video.setText(file[0])
        GLOBAL.record_config('video', file[0])


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
