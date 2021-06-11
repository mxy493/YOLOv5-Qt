import sys
import threading

from PySide2.QtCore import QSize, Signal
from PySide2.QtGui import (Qt, QIcon)
from PySide2.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                               QWidget, QApplication, QDesktopWidget, QStyle)

import msg_box
from gb import GLOBAL
from info import APP_NAME, APP_VERSION
from settings_dialog import SettingsDialog
from widget_camera import WidgetCamera
from widget_config import WidgetConfig


class MainWindow(QMainWindow):
    signal_config_error = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'{APP_NAME} {APP_VERSION}')
        self.setWindowIcon(QIcon('img/yologo.png'))

        GLOBAL.init_config()

        self.signal_config_error.connect(self.slot_config_error)

        self.camera = WidgetCamera()  # 摄像头
        self.config = WidgetConfig()  # Yolo配置界面
        self.settings = SettingsDialog()

        # 模型加载线程
        self.load_model_thread = threading.Thread(target=self.load_yolo)
        self.load_model_thread.start()

        self.config.btn_settings.clicked.connect(self.settings.exec)
        self.settings.accepted.connect(self.reload)

        self.btn_camera = QPushButton('Open/Close Camera')  # 开启或关闭摄像头
        self.btn_camera.setEnabled(False)
        self.btn_camera.clicked.connect(self.oc_camera)
        self.btn_camera.setFixedHeight(60)
        vbox1 = QVBoxLayout()
        vbox1.setContentsMargins(0, 0, 0, 0)
        vbox1.addWidget(self.config)
        vbox1.addStretch()
        vbox1.addWidget(self.btn_camera)

        right_widget = QWidget()
        right_widget.setMaximumWidth(400)
        right_widget.setLayout(vbox1)

        hbox = QHBoxLayout()
        hbox.addWidget(self.camera, 3)
        hbox.addWidget(right_widget, 1)

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
                if self.load_model_thread.is_alive():
                    self.load_model_thread.join()
                self.camera.start_detect()  # 目标检测

    def load_yolo(self):
        """重新加载YOLO模型"""
        print(f'[{threading.get_native_id()}] 加载YOLO模型: {self.settings.line_weights.text()}')
        ret = True
        # 目标检测
        check = self.camera.yolo.set_config(
            weights=self.settings.line_weights.text(),
            device=self.settings.line_device.text(),
            img_size=int(self.settings.combo_size.currentText()),
            conf=round(self.settings.spin_conf.value(), 1),
            iou=round(self.settings.spin_iou.value(), 1),
            agnostic=self.settings.check_agnostic.isChecked(),
            augment=self.settings.check_augment.isChecked(),
            half=self.settings.check_half.isChecked()
        )
        if check:
            self.camera.yolo.load_model()
            self.btn_camera.setEnabled(True)
        else:
            YOLOGGER.warning('配置有误，放弃加载模型')
            self.btn_camera.setEnabled(False)
            self.camera.stop_detect()  # 关闭摄像头
            self.signal_config_error.emit()
            ret = False
        print(f'[{threading.get_native_id()}] 模型加载结束')
        return ret

    def reload(self):
        self.load_model_thread = threading.Thread(target=self.load_yolo)
        self.load_model_thread.start()

    def slot_config_error(self):
        msg = msg_box.MsgWarning()
        msg.setText('配置信息有误，无法正常加载YOLO模型！')
        msg.exec()

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
