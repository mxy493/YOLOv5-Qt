import os
import re

import numpy as np
import torch

from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import (check_img_size, non_max_suppression, scale_coords, set_logging)
from utils.torch_utils import select_device, time_synchronized


class YOLO5:
    def __init__(self):
        self.opt = dict()  # 配置信息
        self.model = None
        self.device = None
        self.names = []
        self.colors = []
        self.stride = 32

    def set_config(self, weights, device='cpu', img_size=448, conf=0.4, iou=0.5,
                   agnostic=True, augment=True, half=True) -> (bool, str):
        """检查参数的正确性并设置参数，参数改变后需要重新设置"""
        # 判断weights文件是否以'pt'结尾且真实存在
        if not os.path.exists(weights) or '.pt' not in weights:
            return False, '找不到配置文件！'

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
            return False, '置信度阈值应处于(0, 1)之间！'

        if iou <= 0 or iou >= 1:
            return False, 'IOU阈值应处于(0, 1)之间！'

        # 初始化配置
        self.opt = {
            'weights': weights,
            'device': device,
            'img_size': img_size,
            'conf_thresh': conf,
            'iou_thresh': iou,
            'agnostic_nms': agnostic,
            'augment': augment,
            'half': half
        }
        return True, ''

    def load_model(self):
        """加载模型，参数改变后需要重新加载模型"""
        # Initialize
        set_logging()
        self.device = select_device(self.opt['device'])
        half = self.opt.get('half') and self.device.type != 'cpu'  # half precision only supported on CUDA

        # Load model
        self.model = attempt_load(self.opt['weights'], map_location=self.device)  # load FP32 model
        self.stride = int(self.model.stride.max())  # model stride
        imgsz = self.opt['img_size']
        self.opt['img_size'] = check_img_size(imgsz, s=self.stride)  # check img_size

        # Get names and colors
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        self.colors = [[np.random.randint(0, 255) for _ in range(3)] for _ in range(len(self.names))]
        if half:
            self.model.half()  # to FP16

        # Run inference
        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, imgsz, imgsz).to(self.device).type_as(next(self.model.parameters())))  # run once

        return True

    def obj_detect(self, image):
        objects = []  # 返回目标列表
        img_h, img_w, _ = image.shape

        # Padded resize
        img = letterbox(image, new_shape=self.opt['img_size'], stride=self.stride)[0]

        # Convert
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB
        img = np.ascontiguousarray(img)  # 转换为内存连续存储的数组

        # Run inference
        img = torch.from_numpy(img).to(self.device)
        img = img.half() if self.opt.get('half') else img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)  # 添加一维

        # Inference
        t1 = time_synchronized()
        pred = self.model(img, augment=self.opt['augment'])[0]
        t2 = time_synchronized()
        print('Time:', t2 - t1)

        # Apply NMS
        pred = non_max_suppression(pred, self.opt['conf_thresh'], self.opt['iou_thresh'],
                                   classes=None, agnostic=self.opt['agnostic_nms'])

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
