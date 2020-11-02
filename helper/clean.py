# -*- coding: utf-8 -*-

"""
Author: mxy
Email: mxy493@qq.com
Date: 2020/11/2
Desc: 
    打包后的非必要文件，占用空间较多可删除
    torch/dnnl.lib, torch/mkldnn.lib, libprotobuf.lib, libproto.lib
"""

# 工作路径
import os
import shutil


# 要删除文件的字符串列表
substrs = ['libprotobuf.lib', 'libprotoc.lib', 'dnnl.lib', 'mkldnn.lib']


def rm_useless_files(root_path, strings):
    """接受一个字符串列表，清理所有包含这些字符串的文件夹"""
    if not os.path.exists(root_path):
        return
    for s in strings:
        s = s.lower()
        for root, dirs, files in os.walk(root_path):
            for d in dirs:
                if s in d.lower():
                    full_path = os.path.join(root_path, root, d)
                    p = os.path.normpath(os.path.abspath(full_path))
                    print(f'RemoveDir: {p}')
                    shutil.rmtree(p)
            for f in files:
                if s in f.lower():
                    full_path = os.path.join(root_path, root, f)
                    p = os.path.normpath(os.path.abspath(full_path))
                    print(f'RemoveFile: {p}')
                    os.remove(p)


if __name__ == '__main__':
    root_path = os.path.abspath('./dist/YOLOv5-Qt')
    rm_useless_files(root_path, substrs)
