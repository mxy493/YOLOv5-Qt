import json
import sys
import threading
import time
import cv2
from PyQt5.QtCore import QTimer, QRect, Qt
from PyQt5.QtGui import *
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import *

import msg_box
from global_data import GLOBAL
from detect import Yolo5


def threading_runner(func):
    """多线程"""

    def wrapped():
        threading.Thread(target=func).start()

    return wrapped


def init_config():
    try:
        with open('config/config.json', 'r') as file_settings:
            GLOBAL.config = json.loads(file_settings.read())
    except FileNotFoundError as err_file:
        print('配置文件不存在: ' + str(err_file))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('目标检测')
        self.setMinimumSize(1200, 800)

        init_config()

        self.camera = CameraWidget()  # 摄像头
        self.yolo_config = YoloConfig()  # Yolo配置界面

        self.btn_camera = QPushButton('开启/关闭')  # 开启或关闭摄像头
        self.btn_camera.setFixedHeight(60)
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.yolo_config)
        vbox1.addStretch()
        vbox1.addWidget(self.btn_camera)

        self.btn_camera.clicked.connect(self.oc_camera)

        hbox = QHBoxLayout()
        hbox.addWidget(self.camera, 4)
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
            self.camera.show_camera()

    # def start(self):
    #     self.camera.show_camera()

    def resizeEvent(self, event):
        self.update()

    def closeEvent(self, event):
        if self.camera.cap.isOpened():
            self.camera.close_camera()


class CameraWidget(QWidget):
    def __init__(self):
        super(CameraWidget, self).__init__()

        self.yolo = Yolo5()
        self.can_yolo = False  # yolo是否配置正确

        self.setStyleSheet('background-color: #cecece')

        self.opened = False  # 摄像头已打开
        self.cap = cv2.VideoCapture()
        self.CAM_NUM = 0
        self.timer_camera = QTimer()

        self.pix_image = None  # QPixmap视频帧
        self.image = None  # 当前读取到的图片
        self.scale = 1  # 比例
        self.objects = []

        self.fps = 0  # 帧率

    def show_camera(self):
        @threading_runner
        def start_read():
            while self.opened:
                self.read_image()
                time.sleep(0.034)  # 每34毫秒(对应30帧的视频)执行一次show_camera方法
                self.update()

        @threading_runner
        def start_detect():
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

        # 初始化yolo参数
        opt = {
            'weights': GLOBAL.config['weights'],
            'output': 'inference/output',
            'img_size': 416,
            'conf_thres': 0.4,
            'iou_thres': 0.5,
            'device': '',
            'view_img': True,
            'classes': '',
            'agnostic_nms': True,
            'augment': True,
            'update': True
        }
        if not self.yolo.init_opt(opt):
            self.can_yolo = False
            msg = msg_box.MsgWarning()
            msg.setText('YOLO配置异常！')
            msg.exec()  # 此处会阻塞
        else:
            self.can_yolo = True
        # flag = self.cap.open(self.CAM_NUM)  # 打开摄像头，比较耗时
        flag = self.cap.open('car1.avi')  # 打开一个视频
        self.opened = True  # 已打开
        if flag:
            start_read()  # 启动读帧线程
            if self.can_yolo:
                start_detect()  # 启动目标检测线程
        else:
            msg = msg_box.MsgWarning()
            msg.setText('视频流开启失败！\n'
                        '请确保摄像头已打开或视频文件真实存在！')
            msg.exec()  # 此处会阻塞

    def read_image(self):
        retval, image = self.cap.read()
        if retval:
            # 删去最后一层
            if image.shape[2] == 4:
                image = image[:, :, :-1]
            self.image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # image

    def close_camera(self):
        self.timer_camera.stop()
        self.cap.release()
        self.opened = False  # 已关闭
        self.can_yolo = False

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
            qp.drawText(self.width() - 100, yh + 30, 'FPS: ' + str(round(self.fps, 2)))

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


class YoloConfig(QGroupBox):
    def __init__(self):
        super(YoloConfig, self).__init__()

        label_weight = QLabel('Weights')
        label_weight.setMinimumWidth(50)
        self.line_weights = QLineEdit()
        self.line_weights.setMinimumWidth(200)
        self.line_weights.editingFinished.connect(lambda: GLOBAL.record_config('weights', self.line_weights.text()))
        self.btn_weight = QPushButton('选择文件')
        self.btn_weight.clicked.connect(self.choose_weights_file)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(label_weight)
        hbox1.addWidget(self.line_weights)
        hbox1.addWidget(self.btn_weight)

        label_size = QLabel('Size')
        label_size.setMinimumWidth(50)
        self.line_size = QLineEdit()
        self.line_size.setMinimumWidth(200)
        self.line_size.editingFinished.connect(lambda: GLOBAL.record_config('size', self.line_sizes.text()))
        self.btn_size = QPushButton('选择文件')

        hbox2 = QHBoxLayout()
        hbox2.addWidget(label_size)
        hbox2.addWidget(self.line_size)
        hbox2.addWidget(self.btn_size)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)

        self.init_config()  # 初始化配置

    def init_config(self):
        try:
            self.line_weights.setText(GLOBAL.config['weights'])
        except KeyError as err_key:
            print('参数项不存在: ' + str(err_key))

    def choose_weights_file(self):
        """从系统中选择升级文件"""
        file = QFileDialog.getOpenFileName(self, "Pre-trained YOLO weights", "./",
                                           "Weights Files (*.pt);;All Files (*)")
        self.line_weights.setText(file[0])
        GLOBAL.record_config('weights', file[0])


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
