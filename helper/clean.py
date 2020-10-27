import os
import shutil

# 要遍历删除的根目录
root = os.path.abspath(os.path.join(os.getcwd(), 'build', 'lib'))
# 要删除文件的字符串列表
strs = ['.exe', 'WebEngine', 'translations', '3D', 'resources',
        'dnnl.lib', 'mkldnn.lib']


def cleaner(substr):
    substr = substr.lower()
    for curpath, dirs, files in os.walk(root):
        for d in dirs:
            if substr in d.lower():
                full_path = os.path.join(root, curpath, d)
                p = os.path.normpath(os.path.abspath(full_path))
                print(f'RemoveDir: {p}')
                shutil.rmtree(p)
        for f in files:
            if substr in f.lower():
                full_path = os.path.join(root, curpath, f)
                p = os.path.normpath(os.path.abspath(full_path))
                print(f'RemoveFile: {p}')
                os.remove(p)


if __name__ == '__main__':
    for s in strs:
        cleaner(s)
