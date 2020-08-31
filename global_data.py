# coding=utf-8
import json
import os

import msg_box


class GlobalData:
    def __init__(self):
        self.config = {}

    def record_config(self, key, value):
        """将设置参数写入到本地文件保存，传入键值对"""
        # 更新配置
        self.config[key] = value
        if not os.path.exists('config'):
            os.mkdir('config')  # 创建log文件夹
        try:
            # 写入文件
            with open('config/config.json', 'w') as file_config:
                file_config.write(json.dumps(self.config))
        except FileNotFoundError as err_file:
            print(err_file)
            msg = msg_box.MsgWarning()
            msg.setText('参数保存失败！')
            msg.exec()


GLOBAL = GlobalData()  # 全局变量调用该对象
