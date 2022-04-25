# 简述
本项目为基于[yolov5](https://github.com/ultralytics/yolov5)的GUI目标识别程序，支持选择要使用的权重文件，设置是否使用GPU、置信度阈值等参数。

注：该Demo为早期版本录制的动画，与新版存在部分差异！

![Demo](demo.gif)

# 环境
- Python 3.8

# 安装和使用

**注意：该程序由我个人开发，存在bug在所难免，但程序迭代了多个版本并一直在优化，因此强烈建议使用最新版代码！**

安装依赖：

```shell
pip install -r requirements.txt
```

所有依赖安装成功后，程序即可正常运行！

初次使用需要对软件进行简单的配置，必不可少的是配置目标识别模型文件，模型文件可以从网络上下载，或者自己训练生成。这里为了简单说明本程序的使用方式，使用yolov5官方仓库提供的模型文件为例介绍，yolov5的每一个release都附带了训练好的模型文件可以对常见物体进行目标识别，请自行下载备用！

yolov5官方模型文件下载：https://github.com/ultralytics/yolov5/releases

模型文件准备好后，运行程序并点击主界面Settings按钮，在弹出的Settings对话框中配置Weights配置项，即模型文件的路径，然后点击Ok按钮保存设置，程序会自动加载对应模型文件，主界面有模型加载是否成功的提示。

模型加载成功后就可以点击主界面右下角Open/Close Camera按钮使用电脑的默认摄像头进行实时目标识别，或者你可以取消Use default camera的勾选，并在Source配置项中配置图片路径、视频路径或实时视频流地址后使用！
