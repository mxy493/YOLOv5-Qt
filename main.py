import sys
import threading
import platform
import time

import pkg_resources as pkg

from PySide2.QtCore import QSize, Signal
from PySide2.QtGui import (Qt, QIcon)
from PySide2.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                               QWidget, QApplication, QDesktopWidget, QStyle, QLabel)

import msg_box
import gb
from gb import YOLOGGER, thread_runner
from info import APP_NAME, APP_VERSION
from settings_dialog import SettingsDialog
from widget_camera import WidgetCamera
from widget_info import WidgetInfo
from widget_config import WidgetConfig


class MainWindow(QMainWindow):
    signal_config_error = Signal(str)

    def __init__(self):
        super().__init__()

        # 检查python版本是否满足要求
        minimum = '3.6.2'
        current = platform.python_version()
        current, minimum = (pkg.parse_version(x) for x in (current, minimum))
        if current < minimum:
            msg = msg_box.MsgWarning()
            msg.setText(f'当前Python版本({current})过低，请升级到{minimum}以上！')
            msg.exec()
            sys.exit()

        self.setWindowTitle(f'{APP_NAME} {APP_VERSION}')
        self.setWindowIcon(QIcon('img/yologo.png'))

        gb.init_logger()
        gb.clean_log()
        gb.init_config()

        self.camera = WidgetCamera()  # 摄像头
        self.info = WidgetInfo()  # 信息面板
        self.config = WidgetConfig()  # Yolo配置界面
        self.settings = SettingsDialog()

        self.signal_config_error.connect(self.slot_msg_dialog)

        # 模型加载线程
        self.load_model_thread = threading.Thread(target=self.load_yolo)
        self.load_model_thread.start()

        self.config.btn_settings.clicked.connect(self.settings.exec)
        self.settings.accepted.connect(self.reload)

        self.status_icon = QLabel()
        self.status_text = QLabel()
        self.update_status('Loading model...', False)
        hbox = QHBoxLayout()
        hbox.addWidget(self.status_icon)
        hbox.addWidget(self.status_text)

        self.btn_camera = QPushButton('Open/Close Camera')  # 开启或关闭摄像头
        self.btn_camera.setEnabled(False)
        self.btn_camera.clicked.connect(self.oc_camera)
        self.btn_camera.setFixedHeight(60)

        vbox1 = QVBoxLayout()
        vbox1.setContentsMargins(0, 0, 0, 0)
        vbox1.addWidget(self.info)
        vbox1.addWidget(self.config)
        vbox1.addStretch()
        vbox1.addLayout(hbox)
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
                self.update_info()

    def load_yolo(self):
        """重新加载YOLO模型"""
        YOLOGGER.info(f'加载YOLO模型: {self.settings.line_weights.text()}')
        # 目标检测
        check, msg = self.camera.yolo.set_config(
            weights=self.settings.line_weights.text(),
            device=self.settings.line_device.text(),
            img_size=int(self.settings.combo_size.currentText()),
            conf=round(self.settings.spin_conf.value(), 1),
            iou=round(self.settings.spin_iou.value(), 1),
            max_det=int(self.settings.spin_max_det.value()),
            agnostic=self.settings.check_agnostic.isChecked(),
            augment=self.settings.check_augment.isChecked(),
            half=self.settings.check_half.isChecked(),
            dnn=self.settings.check_dnn.isChecked()
        )
        if check:
            if not self.camera.yolo.load_model():
                return False
            self.update_status('Model loaded.', True)
            self.btn_camera.setEnabled(True)
            YOLOGGER.info('模型已成功加载')
        else:
            YOLOGGER.warning('配置有误，放弃加载模型')
            self.update_status('Model loading failed.', False)
            self.btn_camera.setEnabled(False)
            self.camera.stop_detect()  # 关闭摄像头
            self.signal_config_error.emit(msg)
            return False
        return True

    def reload(self):
        self.update_status('Reloading model...', False)
        self.load_model_thread = threading.Thread(target=self.load_yolo)
        self.load_model_thread.start()

    def slot_msg_dialog(self, text):
        msg = msg_box.MsgWarning()
        msg.setText(text)
        msg.exec()

    def update_status(self, text, ok=False):
        sz = 15
        min_width = f'min-width: {sz}px;'  # 最小宽度：size
        min_height = f'min-height: {sz}px;'  # 最小高度：size
        max_width = f'max-width: {sz}px;'  # 最小宽度：size
        max_height = f'max-height: {sz}px;'  # 最小高度：size
        # 再设置边界形状及边框
        border_radius = f'border-radius: {sz / 2}px;'  # 边框是圆角，半径为size / 2
        border = 'border:1px solid black;'  # 边框为1px黑色
        # 最后设置背景颜色
        background = "background-color:"
        if ok:
            background += "rgb(0,255,0)"
        else:
            background += "rgb(255,0,0)"
        style = min_width + min_height + max_width + max_height + border_radius + border + background
        self.status_icon.setStyleSheet(style)

        self.status_text.setText(text)

    @thread_runner
    def update_info(self):
        YOLOGGER.info('start update and print fps')
        while self.camera.detecting:
            self.info.update_fps(self.camera.fps)
            time.sleep(0.2)
        self.info.update_fps(self.camera.fps)
        YOLOGGER.info('stop update and print fps')

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
