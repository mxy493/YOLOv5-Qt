import os
import shutil

import numpy as np
import torch
from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import (check_img_size, non_max_suppression, scale_coords, xyxy2xywh, set_logging)
from utils.torch_utils import select_device, time_synchronized


class Yolo5:
    def __init__(self):
        self.opt = {
            'img_size': 480,
            'conf_thresh': 0.4,
            'iou_thresh': 0.5,
            'agnostic_nms': True,
            'output': 'inference/output'
        }
        self.model = None
        self.device = None
        self.names = []
        self.colors = []

    def init_opt(self, opt):
        for k, v in opt.items():
            self.opt[k] = v
        # Initialize
        set_logging()
        self.device = select_device(self.opt['device'])
        # 确保输出文件夹存在
        if os.path.exists(self.opt['output']):
            shutil.rmtree(self.opt['output'])  # delete output folder
        os.makedirs(self.opt['output'])  # make new output folder

        # Load model
        self.model = attempt_load(self.opt['weights'], map_location=self.device)  # load FP32 model
        self.opt['img_size'] = check_img_size(self.opt['img_size'], s=self.model.stride.max())  # check img_size

        # Get names and colors
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        self.colors = [[np.random.randint(0, 255) for _ in range(3)] for _ in range(len(self.names))]
        return True

    def obj_detect(self, image):
        objects = []  # 返回目标列表
        img_h, img_w, _ = image.shape

        # Padded resize
        img = letterbox(image, new_shape=self.opt['img_size'])[0]

        # Convert
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB
        img = np.ascontiguousarray(img)  # 转换为内存连续存储的数组

        # Run inference
        img = torch.from_numpy(img).to(self.device)
        img = img.float()  # uint8 to fp16/32
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
                                   classes=self.opt['classes'], agnostic=self.opt['agnostic_nms'])

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
