# -*- coding: utf-8 -*-

"""
Author: mxy
Email: mxy493@qq.com
Date: 2020/11/3
Desc: 配置界面
"""

from PySide2.QtWidgets import (QGroupBox, QGridLayout, QCheckBox, QLabel, QLineEdit, QPushButton, QFileDialog, QWidget,
                               QVBoxLayout)

from gb import GLOBAL


class WidgetConfig(QWidget):
    def __init__(self):
        super(WidgetConfig, self).__init__()

        HEIGHT = 30

        grid1 = QGridLayout()

        # 使用默认摄像头复选框
        self.check_camera = QCheckBox('Use default camera')
        self.check_camera.setChecked(GLOBAL.config.get('use_camera', True))
        self.check_camera.stateChanged.connect(self.slot_check_camera)
        grid1.addWidget(self.check_camera, 0, 0, 1, 4)

        # 选择视频文件
        label_video = QLabel('Source')
        self.line_video = QLineEdit()
        self.line_video.setText(GLOBAL.config.get('video', ''))
        self.line_video.setFixedHeight(HEIGHT)
        self.line_video.setEnabled(False)
        self.line_video.editingFinished.connect(
            lambda: GLOBAL.record_config({'video': self.line_video.text()}))

        self.btn_video = QPushButton('...')
        self.btn_video.setFixedWidth(40)
        self.btn_video.setFixedHeight(HEIGHT)
        self.btn_video.setEnabled(False)
        self.btn_video.clicked.connect(self.choose_video_file)
        self.slot_check_camera()

        grid1.addWidget(label_video, 1, 0)
        grid1.addWidget(self.line_video, 1, 1, 1, 2)
        grid1.addWidget(self.btn_video, 1, 3)

        # 视频录制
        self.check_record = QCheckBox('Record video')
        self.check_record.setChecked(GLOBAL.config.get('record', True))
        self.check_record.stateChanged.connect(
            lambda: GLOBAL.record_config({'record': self.check_record.isChecked()}))
        grid1.addWidget(self.check_record, 2, 0, 1, 4)

        # Settings
        self.btn_settings = QPushButton('Settings')
        grid1.addWidget(self.btn_settings, 3, 0, 1, 4)

        box = QGroupBox()
        box.setLayout(grid1)

        vbox = QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.addWidget(box)

        self.setLayout(vbox)

    def slot_check_camera(self):
        check = self.check_camera.isChecked()
        GLOBAL.record_config({'use_camera': check})  # 保存配置
        if check:
            self.line_video.setEnabled(False)
            self.btn_video.setEnabled(False)
        else:
            self.line_video.setEnabled(True)
            self.btn_video.setEnabled(True)

    def choose_video_file(self):
        """从系统中选择视频文件"""
        file = QFileDialog.getOpenFileName(self, "Video Files", "./",
                                           "Video Files (*)")
        if file[0] != '':
            self.line_video.setText(file[0])
            GLOBAL.record_config({'video': file[0]})
