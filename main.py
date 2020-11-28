import sys

from PySide2.QtCore import QSize
from PySide2.QtGui import (Qt, QIcon)
from PySide2.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                               QWidget, QApplication, QDesktopWidget, QStyle)

import msg_box
from gb import GLOBAL
from info import APP_NAME, APP_VERSION
from widget_camera import WidgetCamera
from widget_config import WidgetConfig


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'{APP_NAME} {APP_VERSION}')
        self.setWindowIcon(QIcon('img/yologo.png'))

        GLOBAL.init_config()

        self.camera = WidgetCamera()  # 摄像头
        self.config = WidgetConfig()  # Yolo配置界面

        self.btn_camera = QPushButton('Open/Close Camera')  # 开启或关闭摄像头
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

        # ---------- 自适应不同大小的屏幕  ---------- #
        screen = QDesktopWidget().screenGeometry(self)
        available = QDesktopWidget().availableGeometry(self)
        title_height = self.style().pixelMetric(QStyle.PM_TitleBarHeight)
        if screen.width() < 1280 or screen.height() < 768:
            self.setWindowState(Qt.WindowMaximized)  # 窗口最大化显示
            self.setFixedSize(
                available.width(),
                available.height() - title_height)  # 固定窗口大小
        else:
            self.setMinimumSize(QSize(1100, 700))  # 最小宽高
        self.show()  # 显示窗口

    def oc_camera(self):
        if self.camera.cap.isOpened():
            self.camera.close_camera()  # 关闭摄像头
            self.camera.stop_video_recorder()  # 关闭写入器
        else:
            ret = self.camera.open_camera(
                use_camera=self.config.check_camera.isChecked(),
                video=self.config.line_video.text()
            )
            if ret:
                fps = 0 if self.config.check_camera.isChecked() else 30
                self.camera.show_camera(fps=fps)  # 显示画面
                if self.config.check_record.isChecked():
                    self.camera.run_video_recorder()  # 录制视频
                if self.reload_yolo():
                    self.camera.start_detect()  # 目标检测

    def reload_yolo(self):
        """重新加载YOLO模型"""
        # 目标检测
        self.config.save_config()
        check = self.camera.yolo.set_config(
            weights=self.config.line_weights.text(),
            device=self.config.line_device.text(),
            img_size=self.config.combo_size.currentData(),
            conf=round(self.config.spin_conf.value(), 1),
            iou=round(self.config.spin_iou.value(), 1),
            agnostic=self.config.check_agnostic.isChecked(),
            augment=self.config.check_augment.isChecked()
        )
        if not check:
            msg = msg_box.MsgWarning()
            msg.setText('配置信息有误，无法正常加载YOLO模型！')
            msg.exec()
            self.camera.stop_detect()  # 关闭摄像头
            return False
        self.camera.yolo.load_model()
        return True

    def resizeEvent(self, event):
        self.update()

    def closeEvent(self, event):
        if self.camera.cap.isOpened():
            self.camera.close_camera()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
