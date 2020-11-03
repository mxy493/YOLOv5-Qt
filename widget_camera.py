# -*- coding: utf-8 -*-

"""
Author: mxy
Email: mxy493@qq.com
Date: 2020/11/3
Desc: 摄像头界面
"""

import time

import cv2
from PySide2.QtCore import QRect
from PySide2.QtGui import QPainter, QColor, Qt, QPixmap, QImage, QFont, QBrush, QPen
from PySide2.QtWidgets import QWidget

import msg_box
from gb import thread_runner
from yolo import YOLO5


class WidgetCamera(QWidget):
    def __init__(self):
        super(WidgetCamera, self).__init__()

        self.yolo = YOLO5()

        self.opened = False  # 摄像头已打开
        self.detecting = False  # 目标检测中
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
        self.stop_detect()  # 停止目标检测线程
        time.sleep(0.1)  # 等待读取完最后一帧画面，读取一帧画面0.1s以内，一般0.02~0.03s
        self.cap.release()
        self.reset()  # 恢复初始状态

    @thread_runner
    def show_camera(self, fps=0):
        """传入参数帧率，摄像头使用默认值0，视频一般取30|60"""
        print('显示画面线程开始')
        wait = 1 / fps if fps else 0
        while self.opened:
            self.read_image()  # 0.1s以内，一般0.02~0.03s
            if fps:
                time.sleep(wait)  # 等待wait秒读取一帧画面并显示
            self.update()
        self.update()
        print('显示画面线程结束')

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
        self.detecting = True
        print('目标检测线程开始')
        while self.detecting:
            if self.image is None:
                continue
            # 检测
            t0 = time.time()
            self.objects = self.yolo.obj_detect(self.image)
            t1 = time.time()
            self.fps = 1 / (t1 - t0)
            self.update()
        self.update()
        print('目标检测线程结束')

    def stop_detect(self):
        """停止目标检测"""
        self.detecting = False

    def reset(self):
        """恢复初始状态"""
        self.opened = False  # 摄像头关闭
        self.pix_image = None  # 无QPixmap视频帧
        self.image = None  # 当前无读取到的图片
        self.scale = 1  # 比例无
        self.objects = []  # 无检测到的目标
        self.fps = 0  # 帧率无

    def resizeEvent(self, event):
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.draw(qp)
        qp.end()

    def draw(self, qp):
        qp.setWindow(0, 0, self.width(), self.height())  # 设置窗口
        qp.setRenderHint(QPainter.SmoothPixmapTransform)
        # 画框架背景
        qp.setBrush(QColor('#cecece'))  # 框架背景色
        qp.setPen(Qt.NoPen)
        rect = QRect(0, 0, self.width(), self.height())
        qp.drawRect(rect)

        sw, sh = self.width(), self.height()  # 图像窗口宽高

        if not self.opened:
            qp.drawPixmap(sw / 2 - 100, sh / 2 - 100, 200, 200, QPixmap('img/video.svg'))

        # 画图
        if self.opened and self.image is not None:
            ih, iw, _ = self.image.shape
            self.scale = sw / iw if sw / iw < sh / ih else sh / ih  # 缩放比例
            px = round((sw - iw * self.scale) / 2)
            py = round((sh - ih * self.scale) / 2)
            qimage = QImage(self.image.data, iw, ih, 3 * iw, QImage.Format_RGB888)  # 转QImage
            qpixmap = QPixmap.fromImage(qimage.scaled(sw, sh, Qt.KeepAspectRatio))  # 转QPixmap
            pw, ph = qpixmap.width(), qpixmap.height()  # 缩放后的QPixmap大小
            qp.drawPixmap(px, py, qpixmap)

            font = QFont()
            font.setFamily('Microsoft YaHei')
            if self.fps > 0:
                font.setPointSize(14)
                qp.setFont(font)
                pen = QPen()
                pen.setColor(Qt.white)
                qp.setPen(pen)
                qp.drawText(sw - px - 130, py + 40, 'FPS: ' + str(round(self.fps, 2)))

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
                ox, oy = px + round(pw * obj['x']), py + round(ph * obj['y'])
                ow, oh = round(pw * obj['w']), round(ph * obj['h'])
                obj_rect = QRect(ox, oy, ow, oh)
                qp.drawRect(obj_rect)  # 画矩形框

                # 画 类别 和 置信度
                qp.drawText(ox, oy - 5, str(obj['class']) + str(round(obj['confidence'], 2)))

