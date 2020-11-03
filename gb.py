# coding=utf-8
import json
import os
import threading

import msg_box


def thread_runner(func):
    """多线程"""

    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs).start()

    return wrapper


class Global:
    def __init__(self):
        # 保存的配置
        # @video: 视频文件
        # @weights: 权重文件
        # @img_size: 图像大小，32的倍数（320|416|480|640）
        # @conf_thresh: 置信度阈值（0.1-0.9）
        # @iou_thresh: IOU阈值（0.1-0.9）
        self.config = dict()

    def init_config(self):
        if not os.path.exists('config'):
            os.mkdir('config')  # make new config folder
            return
        try:
            with open('config/config.json', 'r') as file_settings:
                GLOBAL.config = json.loads(file_settings.read())
        except FileNotFoundError as err_file:
            print('配置文件不存在: ' + str(err_file))

    def record_config(self, _dict):
        """将设置参数写入到本地文件保存，传入字典"""
        # 更新配置
        for k, v in _dict.items():
            self.config[k] = v
        if not os.path.exists('config'):
            os.mkdir('config')  # 创建config文件夹
        try:
            # 写入文件
            with open('config/config.json', 'w') as file_config:
                file_config.write(json.dumps(self.config, indent=4))
        except FileNotFoundError as err_file:
            print(err_file)
            msg = msg_box.MsgWarning()
            msg.setText('参数保存失败！')
            msg.exec()


GLOBAL = Global()  # 全局变量调用该对象
