import os
import re

import cv2
import numpy as np
import torch
import pkg_resources as pkg
from pathlib import Path

from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import (check_img_size, non_max_suppression, scale_coords)
from utils.torch_utils import select_device

from gb import YOLOGGER

SUPPORT_TENSORFLOW = False
try:
    pkg.require('tensorflow>=2.4.1')
    import tensorflow as tf
    SUPPORT_TENSORFLOW = True
except pkg.DistributionNotFound as error:
    YOLOGGER.error(error)


class YOLO5:
    def __init__(self):
        self.opt = dict()  # 配置信息

        self.model = None
        self.net = None
        self.session = None
        self.interpreter = None

        self.device = None
        self.names = []
        self.colors = []
        self.stride = 32

        self.is_pt = False
        self.is_onnx = False
        self.is_tflite = False
        self.is_pb = False
        self.is_saved_model = False
        self.is_int8 = False

        self.input_details = []
        self.output_details = []

    def set_config(self,
                   weights,  # model.pt path(s)
                   device='cpu',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
                   img_size=448,  # inference size (pixels)
                   conf=0.4,  # confidence threshold
                   iou=0.5,  # NMS IOU threshold
                   max_det=1000,  # maximum detections per image
                   agnostic=True,  # class-agnostic NMS
                   augment=True,  # augmented inference
                   half=True,  # use FP16 half-precision inference
                   dnn=False  # use OpenCV DNN for ONNX inference
                   ) -> (bool, str):
        """检查参数的正确性并设置参数，参数改变后需要重新设置"""
        # 判断weights文件是否真实存在
        if not os.path.exists(weights):
            return False, f'Weights文件不存在: {weights}'
        # 判断文件名后缀是否合法
        suffix = Path(weights).suffix.lower()
        suffixes = ['.pt', '.onnx', '.tflite', '.pb', '']
        if suffix not in suffixes:
            return False, f'不合法的文件后缀: \n{weights}'

        if suffix == '.pt':
            self.is_pt = True
        elif suffix == '.onnx':
            self.is_onnx = True
        elif suffix == '.tflite':
            self.is_tflite = True
        elif suffix == '.pb':
            self.is_pb = True
        elif suffix == '':
            self.is_saved_model = True

        # 判断device设置是否正确
        if re.match(r'^[0-3](,[0-3]){0,3}$', device):
            if not torch.cuda.is_available():
                return False, 'CUDA当前无法使用！请将CUDA device设置为"cpu"！'
            else:
                for c in ['0', '1', '2', '3']:
                    if device.count(c) > 1:
                        return False, 'CUDA device 配置错误！'
        elif device != 'cpu':
            return False, 'CUDA device 配置错误！'

        # img_size是否64的整数倍
        if img_size % 64 != 0:
            return False, 'Image Size应为64的倍数！'

        if conf <= 0 or conf >= 1:
            return False, 'Confidence阈值应处于(0, 1)之间！'

        if iou <= 0 or iou >= 1:
            return False, 'IOU阈值应处于(0, 1)之间！'

        if half and device == 'cpu':
            return False, '当前CUDA device配置为"cpu"，Half不可用！'

        # 初始化配置
        self.opt = {
            'weights': weights,
            'device': device,
            'img_size': img_size,
            'conf_thresh': conf,
            'iou_thresh': iou,
            'max_det': max_det,
            'agnostic_nms': agnostic,
            'augment': augment,
            'half': half,
            'dnn': dnn
        }
        return True, ''

    def load_model(self):
        """加载模型，参数改变后需要重新加载模型"""
        # Initialize
        self.device = select_device(self.opt['device'])
        half = self.opt.get('half') and self.device.type != 'cpu'  # half precision only supported on CUDA

        w = self.opt['weights']
        if self.is_pt:
            # Load model
            self.model = torch.jit.load(w) if 'torchscript' in w else attempt_load(w, map_location=self.device)
            self.stride = int(self.model.stride.max())  # model stride

            # Get names and colors
            self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
            self.colors = [[np.random.randint(0, 255) for _ in range(3)] for _ in range(len(self.names))]
            if half:
                self.model.half()  # to FP16
        elif self.is_onnx:
            if self.opt['dnn']:
                # check_requirements(('opencv-python>=4.5.4',))
                self.net = cv2.dnn.readNetFromONNX(w)
            else:
                try:
                    pkg.require(('onnx', 'onnxruntime'))
                except pkg.DistributionNotFound as error:
                    YOLOGGER.error(error)
                else:
                    import onnxruntime
                    self.session = onnxruntime.InferenceSession(w, None)
        else:  # TensorFlow models
            if SUPPORT_TENSORFLOW:
                if self.is_pb:  # https://www.tensorflow.org/guide/migrate#a_graphpb_or_graphpbtxt
                    def wrap_frozen_graph(gd, inputs, outputs):
                        x = tf.compat.v1.wrap_function(lambda: tf.compat.v1.import_graph_def(gd, name=""), [])  # wrapped import
                        return x.prune(tf.nest.map_structure(x.graph.as_graph_element, inputs),
                                       tf.nest.map_structure(x.graph.as_graph_element, outputs))

                    graph_def = tf.Graph().as_graph_def()
                    graph_def.ParseFromString(open(w, 'rb').read())
                    self.frozen_func = wrap_frozen_graph(gd=graph_def, inputs="x:0", outputs="Identity:0")
                elif self.is_saved_model:
                    self.model = tf.keras.models.load_model(w)
                elif self.is_tflite:
                    self.interpreter = tf.lite.Interpreter(model_path=w)  # load TFLite model
                    self.interpreter.allocate_tensors()  # allocate
                    self.input_details = self.interpreter.get_input_details()  # inputs
                    self.output_details = self.interpreter.get_output_details()  # outputs
                    self.is_int8 = self.input_details[0]['dtype'] == np.uint8  # is TFLite quantized uint8 model
        self.opt['img_size'] = check_img_size(self.opt['img_size'], s=self.stride)  # check img_size
        imgsz = self.opt['img_size']
        if self.is_pt and self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, imgsz, imgsz).to(self.device).type_as(next(self.model.parameters())))  # run once
        return True

    def obj_detect(self, image):
        objects = []  # 返回目标列表
        img_h, img_w, _ = image.shape

        # Padded resize
        img = letterbox(image, new_shape=self.opt['img_size'], stride=self.stride)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB
        img = np.ascontiguousarray(img)  # 转换为内存连续存储的数组
        if self.is_onnx:
            img = img.astype('float32')
        else:
            img = torch.from_numpy(img).to(self.device)
            img = img.half() if self.opt.get('half') else img.float()  # uint8 to fp16/32

        img = img / 255.0  # 0 - 255 to 0.0 - 1.0
        if len(img.shape) == 3:
            img = img[None]  # expand for batch dim

        if img.ndimension() == 3:
            img = img.unsqueeze(0)  # 添加一维

        # Inference
        if self.is_pt:
            pred = self.model(img, augment=self.opt['augment'])[0]
        elif self.is_onnx:
            if self.opt['dnn']:
                self.net.setInput(img)
                pred = torch.tensor(self.net.forward())
            else:
                result = self.session.run(
                    [self.session.get_outputs()[0].name], {self.session.get_inputs()[0].name: img})
                pred = torch.tensor(result)
        else:  # tensorflow model (tflite, pb, saved_model)
            imn = img.permute(0, 2, 3, 1).cpu().numpy()  # image in numpy
            if self.is_pb:
                pred = self.frozen_func(x=tf.constant(imn)).numpy()
            elif self.is_saved_model:
                pred = self.model(imn, training=False).numpy()
            elif self.is_tflite:
                if self.is_int8:
                    scale, zero_point = self.input_details[0]['quantization']
                    imn = (imn / scale + zero_point).astype(np.uint8)  # de-scale
                self.interpreter.set_tensor(self.input_details[0]['index'], imn)
                self.interpreter.invoke()
                pred = self.interpreter.get_tensor(self.output_details[0]['index'])
                if self.is_int8:
                    scale, zero_point = self.output_details[0]['quantization']
                    pred = (pred.astype(np.float32) - zero_point) * scale  # re-scale
            imgsz = self.opt['img_size']
            pred[..., 0] *= imgsz[1]  # x
            pred[..., 1] *= imgsz[0]  # y
            pred[..., 2] *= imgsz[1]  # w
            pred[..., 3] *= imgsz[0]  # h
            pred = torch.tensor(pred)

        # Apply NMS
        pred = non_max_suppression(pred, self.opt['conf_thresh'], self.opt['iou_thresh'], classes=None,
                                   agnostic=self.opt['agnostic_nms'], max_det=self.opt['max_det'])

        # # Second-stage classifier (optional)
        # if classify:
        #     pred = apply_classifier(pred, modelc, img, im0s)

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            gn = torch.tensor(image.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            if det is not None and len(det):
                # Rescale boxes from img_size to image size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], image.shape).round()

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    xyxy = [xy.item() for xy in xyxy]  # tensor列表转为一般列表
                    xywh = [xyxy[0] / img_w, xyxy[1] / img_h,
                            (xyxy[2] - xyxy[0]) / img_w, (xyxy[3] - xyxy[1]) / img_h]  # 转相对于宽高的坐标
                    objects.append({'class': self.names[int(cls)], 'color': self.colors[int(cls)],
                                    'confidence': conf.item(), 'x': xywh[0], 'y': xywh[1], 'w': xywh[2], 'h': xywh[3]})
        return objects
