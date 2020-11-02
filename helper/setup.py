# -*- coding: utf-8 -*-

# cx_Freeze 打包脚本

import os
import shutil
import sys
from helper import clean

from cx_Freeze import setup, Executable


options = {
    'build_exe': {
        'build_exe': './setup',
        'optimize': 0,
        'excludes': ['caffe2', 'cairo', 'absl', 'certifi', 'chardet', 'colorama',
                     'curses', 'Cython', 'dbm', 'future', 'idna', 'lib2to3',
                     'msilib', 'past', 'pkg_resources', 'pydoc_data', 'pyximport',
                     'requests', 'setuptools', 'sqlite3', 'tensorboard', 'test',
                     'urllib3', 'win32com', 'xmlrpc'],  # 无用的包
        'includes': ['models.yolo'],
        'packages': ['PySide2', 'torch', 'torchvision', 'cv2', 'matplotlib'],
        'include_files': ['../img'],
        'zip_include_packages': [],
        'bin_excludes': [],
        'bin_path_excludes': [],
        'silent': True
    },
    'bdist_msi': {
        'add_to_path': True,
        'all_users': True,
        'install_icon': '../img/yologo64.ico',
        'summary_data': {
            'author': 'mxy493',
        },
        'target_name': 'YOLOv5-Qt'
    }
}

# 打包后仍然包含大量无用文件，可手动删除，以下文件经测试删除后不影响程序运行
# PySide2 包含大量无用文件:
#   *.exe、*WebEngine*、PySide2/translations、PySide2/qml、PySide2/*3D*、
#   PySide2/resources、PySide2/*quick*、PySide2/examples
# torch 包含无用的大体积文件:
#   dnnl.lib, mkldnn.lib

# 要删除文件的字符串列表
substrs = ['.exe', 'WebEngine', 'translations', '3D', 'resources',
           'dnnl.lib', 'mkldnn.lib']


def rm_build():
    """打包前删除旧的工作文件"""
    direc = 'build'
    if os.path.exists(direc):
        confirm = input('要先删除build文件夹吗(y/n): ').lower()
        if confirm == 'y':
            shutil.rmtree(direc)
            print('已删除')


def freeze():
    base = 'Console'
    if sys.platform == 'win32':
        base = 'Win32GUI'

    # 可执行程序列表，此处仅一个可执行程序
    executables = [
        Executable(
            '../main.py',
            base=base,  # 注释后可打开控制台窗口运行
            targetName='YOLOv5-Qt',
            icon='../img/yologo64.ico'
        )
    ]

    setup(
        name='YOLOv5-Qt',
        version='1.0.0',
        description='YOLOv5使用Qt实现的GUI程序',
        options=options,
        executables=executables
    )


if __name__ == '__main__':
    rm_build()
    freeze()
    c = input('清理无用文件(y/n): ').lower()
    if c == 'y':
        root_path = os.path.abspath('./setup/lib')
        clean.rm_useless_files(root_path, substrs)
