# -*- coding: utf-8 -*-

"""
Author: mxy
Email: mxy493@qq.com
Date: 2021/6/9
Desc: 
"""
from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import (QDialog, QGridLayout, QCheckBox, QLabel, QLineEdit, QPushButton, QGroupBox, QComboBox,
                               QListView, QDoubleSpinBox, QVBoxLayout, QHBoxLayout, QFileDialog)

import gb


class SettingsDialog(QDialog):
    def __init__(self):
        super(SettingsDialog, self).__init__()
        self.setWindowTitle('Settings')
        self.setWindowIcon(QIcon('img/yologo.png'))
        self.setWindowFlags(Qt.WindowCloseButtonHint)

        HEIGHT = 30

        grid = QGridLayout()

        # 选择权重文件
        label_weights = QLabel('Weights')
        self.line_weights = QLineEdit()
        self.line_weights.setFixedHeight(HEIGHT)

        self.btn_weights = QPushButton('...')
        self.btn_weights.setFixedWidth(40)
        self.btn_weights.setFixedHeight(HEIGHT)
        self.btn_weights.clicked.connect(self.choose_weights_file)

        grid.addWidget(label_weights, 2, 0)
        grid.addWidget(self.line_weights, 2, 1, 1, 2)
        grid.addWidget(self.btn_weights, 2, 3)

        # 是否使用GPU
        label_device = QLabel('CUDA device')
        self.line_device = QLineEdit('cpu')
        self.line_device.setToolTip('cuda device, i.e. 0 or 0,1,2,3 or cpu')
        self.line_device.setPlaceholderText('cpu or 0 or 0,1,2,3')
        self.line_device.setFixedHeight(HEIGHT)

        grid.addWidget(label_device, 3, 0)
        grid.addWidget(self.line_device, 3, 1, 1, 3)

        # 设置图像大小
        label_size = QLabel('Img Size')
        self.combo_size = QComboBox()
        self.combo_size.setToolTip('inference size (pixels)')
        self.combo_size.setFixedHeight(HEIGHT)
        self.combo_size.setStyleSheet(
            'QAbstractItemView::item {height: 40px;}')
        self.combo_size.setView(QListView())
        self.combo_size.addItem('320', 320)
        self.combo_size.addItem('384', 384)
        self.combo_size.addItem('448', 448)
        self.combo_size.addItem('512', 512)
        self.combo_size.addItem('576', 576)
        self.combo_size.addItem('640', 640)

        grid.addWidget(label_size, 4, 0)
        grid.addWidget(self.combo_size, 4, 1, 1, 3)

        # 设置置信度阈值
        label_conf = QLabel('Confidence')
        self.spin_conf = QDoubleSpinBox()
        self.spin_conf.setToolTip('confidence threshold')
        self.spin_conf.setFixedHeight(HEIGHT)
        self.spin_conf.setDecimals(1)
        self.spin_conf.setRange(0.1, 0.9)
        self.spin_conf.setSingleStep(0.1)

        grid.addWidget(label_conf, 5, 0)
        grid.addWidget(self.spin_conf, 5, 1, 1, 3)

        # 设置IOU阈值
        label_iou = QLabel('IOU')
        self.spin_iou = QDoubleSpinBox()
        self.spin_iou.setToolTip('NMS IoU threshold')
        self.spin_iou.setFixedHeight(HEIGHT)
        self.spin_iou.setDecimals(1)
        self.spin_iou.setRange(0.1, 0.9)
        self.spin_iou.setSingleStep(0.1)

        grid.addWidget(label_iou, 6, 0)
        grid.addWidget(self.spin_iou, 6, 1, 1, 3)

        # class-agnostic NMS
        self.check_agnostic = QCheckBox('Agnostic')
        self.check_agnostic.setToolTip('class-agnostic NMS')

        # augmented inference
        self.check_augment = QCheckBox('Augment')
        self.check_augment.setToolTip('augmented inference')

        # half
        self.check_half = QCheckBox('Half')
        self.check_half.setToolTip('use FP16 half-precision inference')

        grid.addWidget(self.check_agnostic, 7, 0)
        grid.addWidget(self.check_augment, 7, 1)
        grid.addWidget(self.check_half, 7, 2)

        box = QGroupBox()
        box.setLayout(grid)

        hbox = QHBoxLayout()
        self.btn_cancel = QPushButton('Cancel')
        self.btn_cancel.clicked.connect(self.restore)
        self.btn_ok = QPushButton('Ok')
        self.btn_ok.clicked.connect(self.save_settings)
        hbox.addStretch()
        hbox.addWidget(self.btn_cancel)
        hbox.addWidget(self.btn_ok)

        vbox = QVBoxLayout()
        vbox.addWidget(box)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        self.load_settings()

    def choose_weights_file(self):
        """从系统中选择权重文件"""
        file = QFileDialog.getOpenFileName(self, "Pre-trained YOLOv5 Weights", "./",
                                           "Weights Files (*.pt);;All Files (*)")
        if file[0] != '':
            self.line_weights.setText(file[0])

    def load_settings(self):
        self.line_weights.setText(gb.get_config('weights', ''))
        self.line_device.setText(gb.get_config('device', 'cpu'))
        self.combo_size.setCurrentText(gb.get_config('img_size', '640'))
        self.spin_conf.setValue(gb.get_config('conf_thresh', 0.5))
        self.spin_iou.setValue(gb.get_config('iou_thresh', 0.5))
        self.check_agnostic.setChecked(gb.get_config('agnostic', True))
        self.check_augment.setChecked(gb.get_config('augment', True))
        self.check_half.setChecked(gb.get_config('half', True))

    def save_settings(self):
        """更新配置"""
        config = {
            'weights': self.line_weights.text(),
            'device': self.line_device.text(),
            'img_size': self.combo_size.currentText(),
            'conf_thresh': round(self.spin_conf.value(), 1),
            'iou_thresh': round(self.spin_iou.value(), 1),
            'agnostic': self.check_agnostic.isChecked(),
            'augment': self.check_augment.isChecked(),
            'half': self.check_half.isChecked()
        }
        gb.record_config(config)
        self.accept()

    def restore(self):
        """恢复原配置"""
        self.load_settings()
        self.reject()

    def closeEvent(self, event):
        self.restore()
