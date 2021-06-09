# -*- coding: utf-8 -*-

"""
Author: mxy
Email: mxy493@qq.com
Date: 2020/11/3
Desc: 配置界面
"""

from PySide2.QtWidgets import QGroupBox, QGridLayout, QCheckBox, QLabel, QLineEdit, QPushButton, \
    QComboBox, QListView, QDoubleSpinBox, QFileDialog

from gb import GLOBAL


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
        self.line_video.setFixedHeight(HEIGHT)
        self.line_video.setEnabled(False)
        self.line_video.setText(GLOBAL.config.get('video', ''))
        self.line_video.editingFinished.connect(
            lambda: GLOBAL.record_config({'video': self.line_video.text()}))

        self.btn_video = QPushButton('...')
        self.btn_video.setFixedWidth(40)
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
        self.line_weights.setFixedHeight(HEIGHT)
        self.line_weights.setText(GLOBAL.config.get('weights', ''))
        self.line_weights.editingFinished.connect(lambda: GLOBAL.record_config(
            {'weights': self.line_weights.text()}
        ))

        self.btn_weights = QPushButton('...')
        self.btn_weights.setFixedWidth(40)
        self.btn_weights.setFixedHeight(HEIGHT)
        self.btn_weights.clicked.connect(self.choose_weights_file)

        grid.addWidget(label_weights, 2, 0)
        grid.addWidget(self.line_weights, 2, 1)
        grid.addWidget(self.btn_weights, 2, 2)

        # 是否使用GPU
        label_device = QLabel('CUDA device')
        self.line_device = QLineEdit('cpu')
        self.line_device.setToolTip('cuda device, i.e. 0 or 0,1,2,3 or cpu')
        self.line_device.setText(GLOBAL.config.get('device', 'cpu'))
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
        self.combo_size.setToolTip('inference size (pixels)')
        self.combo_size.setFixedHeight(HEIGHT)
        self.combo_size.setStyleSheet(
            'QAbstractItemView::item {height: 40px;}')
        self.combo_size.setView(QListView())
        self.combo_size.addItem('320', 320)
        self.combo_size.addItem('416', 416)
        self.combo_size.addItem('480', 480)
        self.combo_size.addItem('544', 544)
        self.combo_size.addItem('640', 640)
        self.combo_size.setCurrentIndex(
            self.combo_size.findData(GLOBAL.config.get('img_size', 480)))
        self.combo_size.currentIndexChanged.connect(lambda: GLOBAL.record_config(
            {'img_size': self.combo_size.currentData()}))

        grid.addWidget(label_size, 4, 0)
        grid.addWidget(self.combo_size, 4, 1, 1, 2)

        # 设置置信度阈值
        label_conf = QLabel('Confidence')
        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setToolTip('object confidence threshold')
        self.spin_conf.setFixedHeight(HEIGHT)
        self.spin_conf.setDecimals(1)
        self.spin_conf.setRange(0.1, 0.9)
        self.spin_conf.setSingleStep(0.1)
        self.spin_conf.setValue(GLOBAL.config.get('conf_thresh', 0.5))
        self.spin_conf.valueChanged.connect(lambda: GLOBAL.record_config(
            {'conf_thresh': round(self.spin_conf.value(), 1)}
        ))

        grid.addWidget(label_conf, 5, 0)
        grid.addWidget(self.spin_conf, 5, 1, 1, 2)

        # 设置IOU阈值
        label_iou = QLabel('IOU')
        self.spin_iou = QDoubleSpinBox()
        self.spin_iou.setToolTip('IOU threshold for NMS')
        self.spin_iou.setFixedHeight(HEIGHT)
        self.spin_iou.setDecimals(1)
        self.spin_iou.setRange(0.1, 0.9)
        self.spin_iou.setSingleStep(0.1)
        self.spin_iou.setValue(GLOBAL.config.get('iou_thresh', 0.5))
        self.spin_iou.valueChanged.connect(lambda: GLOBAL.record_config(
            {'iou_thresh': round(self.spin_iou.value(), 1)}
        ))

        grid.addWidget(label_iou, 6, 0)
        grid.addWidget(self.spin_iou, 6, 1, 1, 2)

        # class-agnostic NMS
        self.check_agnostic = QCheckBox('Agnostic')
        self.check_agnostic.setToolTip('class-agnostic NMS')
        self.check_agnostic.setChecked(GLOBAL.config.get('agnostic', True))
        self.check_agnostic.stateChanged.connect(lambda: GLOBAL.record_config(
            {'agnostic': self.check_agnostic.isChecked()}
        ))

        grid.addWidget(self.check_agnostic, 7, 0, 1, 3)  # 一行三列

        # augmented inference
        self.check_augment = QCheckBox('Augment')
        self.check_augment.setToolTip('augmented inference')
        self.check_augment.setChecked(GLOBAL.config.get('augment', True))
        self.check_augment.stateChanged.connect(lambda: GLOBAL.record_config(
            {'augment': self.check_augment.isChecked()}
        ))

        grid.addWidget(self.check_augment, 8, 0, 1, 3)  # 一行三列

        # half
        self.check_half = QCheckBox('Half')
        self.check_half.setToolTip('use FP16 half-precision inference')
        grid.addWidget(self.check_half, 9, 0, 1, 3)  # 一行三列

        # 视频录制
        self.check_record = QCheckBox('Record video')
        grid.addWidget(self.check_record, 10, 0, 1, 3)  # 一行三列

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
            'augment': self.check_augment.isChecked(),
            'half': self.check_half.isChecked()
        }
        GLOBAL.record_config(config)
