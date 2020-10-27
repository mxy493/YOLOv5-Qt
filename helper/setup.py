# -*- coding: utf-8 -*-

"""
cx_Freeze 打包脚本
打包后仍然包含大量无用文件，可手动删除，以下文件经测试删除后不影响程序运行
PySide2 包含大量无用文件: *.exe、*WebEngine*、PySide2/translations、PySide2/qml、
    PySide2/*3D*、PySide2/resources、PySide2/*quick*、PySide2/examples
torch 包含无用的大体积文件: dnnl.lib, mkldnn.lib
"""

import sys

from cx_Freeze import setup, Executable

options = {
    'build_exe': {
        'build_exe': './helper/build/',
        'optimize': 0,
        'excludes': ['caffe2', 'cairo', 'absl', 'certifi', 'chardet', 'colorama',
                     'curses', 'Cython', 'dbm', 'future', 'idna', 'lib2to3',
                     'msilib', 'past', 'pkg_resources', 'pydoc_data', 'pyximport',
                     'requests', 'setuptools', 'sqlite3', 'tensorboard', 'test',
                     'urllib3', 'win32com', 'xmlrpc'],
        'includes': ['models.yolo'],
        'packages': ['PySide2', 'torch', 'torchvision', 'cv2', 'matplotlib'],
        'include_files': ['img'],
        'zip_include_packages': [],
        'bin_excludes': [],
        'bin_path_excludes': [],
        'silent': True
    },
    'bdist_msi': {
        'add_to_path': True,
        'all_users': True,
        'install_icon': 'img/yologo64.ico',
        'summary_data': {
            'author': 'mxy493',
        },
        'target_name': 'YOLOv5-Qt'
    }
}

base = 'Console'
if sys.platform == 'win32':
    base = 'Win32GUI'

executables = [
    Executable('main.py',
               base=base,  # 注释后可打开控制台窗口运行
               targetName='YOLOv5-Qt',
               icon='img/yologo64.ico'
               )
]

setup(
    name='YOLOv5-Qt',
    version='1.0.0',
    description='YOLOv5使用Qt实现的GUI程序',
    options=options,
    executables=executables
)
