# coding=utf-8
import json
import os
import sys
import threading
import datetime
import logging

import msg_box

CONFIG = dict()
YOLOGGER = logging.getLogger('yologger')


def thread_runner(func):
    """多线程"""

    def wrapper(*args, **kwargs):
        threading.Thread(target=func, args=args, kwargs=kwargs).start()

    return wrapper


def init_logger():
    if not os.path.exists('log'):
        os.mkdir('log')
    YOLOGGER.setLevel(logging.DEBUG)

    formatter = logging.Formatter(fmt='[%(asctime)s] [%(thread)d] %(message)s')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    YOLOGGER.addHandler(console_handler)

    file_handler = logging.FileHandler(filename=f'log/{datetime.date.today().isoformat()}.log')
    file_handler.setFormatter(formatter)
    YOLOGGER.addHandler(file_handler)


def init_config():
    global CONFIG
    if not os.path.exists('config'):
        os.mkdir('config')  # make new config folder
        return
    try:
        with open('config/config.json', 'r') as file_settings:
            CONFIG = json.loads(file_settings.read())
    except FileNotFoundError as err_file:
        print('配置文件不存在: ' + str(err_file))


def record_config(_dict):
    """将设置参数写入到本地文件保存，传入字典"""
    global CONFIG
    # 更新配置
    for k, v in _dict.items():
        CONFIG[k] = v
    if not os.path.exists('config'):
        os.mkdir('config')  # 创建config文件夹
    try:
        # 写入文件
        with open('config/config.json', 'w') as file_config:
            file_config.write(json.dumps(CONFIG, indent=4))
    except FileNotFoundError as err_file:
        print(err_file)
        msg = msg_box.MsgWarning()
        msg.setText('参数保存失败！')
        msg.exec()


def get_config(key, _default=None):
    global CONFIG
    return CONFIG.get(key, _default)
