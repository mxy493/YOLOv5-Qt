import os
import re

import numpy as np
import torch

from deep_sort.deep_sort import DeepSort
from deep_sort.utils.parser import get_config
from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import (check_img_size, non_max_suppression, scale_coords, set_logging)
from utils.torch_utils import select_device, time_synchronized


def bbox_rel(image_width, image_height,  *xyxy):
    """" Calculates the relative bounding box from absolute pixel values. """
    bbox_left = min([xyxy[0].item(), xyxy[2].item()])
    bbox_top = min([xyxy[1].item(), xyxy[3].item()])
    bbox_w = abs(xyxy[0].item() - xyxy[2].item())
    bbox_h = abs(xyxy[1].item() - xyxy[3].item())
    x_c = (bbox_left + bbox_w / 2)
    y_c = (bbox_top + bbox_h / 2)
    w = bbox_w
    h = bbox_h
    return x_c, y_c, w, h


def compute_color_for_labels(label):
    """
    Simple function that adds fixed color depending on the class
    """
    color = [int((p * (label ** 2 - label + 1)) % 255) for p in palette]
    return tuple(color)


class YOLO5:
    def __init__(self):
        self.opt = dict()  # 配置信息
        self.model = None
        self.device = None
        self.names = []
        self.colors = []

        self.deepsort = None  # DeepSort

    def set_config(self, weights, device='cpu', img_size=480, conf=0.4, iou=0.5,
                   agnostic=True, augment=True) -> bool:
        """检查参数的正确性并设置参数，参数改变后需要重新设置"""
        # 判断weights文件是否以'pt'结尾且真实存在
        if not os.path.exists(weights) or '.pt' not in weights:
            return False

        # 判断device设置是否正确
        check_device = True
        if device in ['cpu', '0', '1', '2', '3']:
            check_device = True
        elif re.match(r'[0-3],[0-3](,[0-3])?(,[0-3])?', device):
            for c in ['0', '1', '2', '3']:
                if device.count(c) > 1:
                    check_device = False
                    break
        else:
            check_device = False
        if not check_device:
            return False

        # img_size是否32的整数倍
        if img_size % 32 != 0:
            return False

        if conf <= 0 or conf >= 1:
            return False

        if iou <= 0 or iou >= 1:
            return False

        # 初始化配置
        self.opt = {
            'weights': weights,
            'device': device,
            'img_size': img_size,
            'conf_thresh': conf,
            'iou_thresh': iou,
            'agnostic_nms': agnostic,
            'augment': augment
        }
        return True

    def load_model(self):
        """加载模型，参数改变后需要重新加载模型"""
        # Initialize
        set_logging()
        self.device = select_device(self.opt['device'])

        # Load model
        self.model = attempt_load(self.opt['weights'], map_location=self.device)  # load FP32 model
        self.opt['img_size'] = check_img_size(
            self.opt['img_size'], s=self.model.stride.max())  # check img_size

        # Get names and colors
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        self.colors = [[np.random.randint(0, 255) for _ in range(3)] for _ in range(len(self.names))]

        # initialize deepsort
        cfg = get_config()
        cfg.merge_from_file('deep_sort/configs/deep_sort.yaml')
        self.deepsort = DeepSort(cfg.DEEPSORT.REID_CKPT,
                                 max_dist=cfg.DEEPSORT.MAX_DIST,
                                 min_confidence=cfg.DEEPSORT.MIN_CONFIDENCE,
                                 nms_max_overlap=cfg.DEEPSORT.NMS_MAX_OVERLAP,
                                 max_iou_distance=cfg.DEEPSORT.MAX_IOU_DISTANCE,
                                 max_age=cfg.DEEPSORT.MAX_AGE,
                                 n_init=cfg.DEEPSORT.N_INIT,
                                 nn_budget=cfg.DEEPSORT.NN_BUDGET,
                                 use_cuda=True)
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
                                   classes=None, agnostic=self.opt['agnostic_nms'])

        # Process detections
        for i, det in enumerate(pred):  # detections per image
            gn = torch.tensor(image.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            if det is not None and len(det):
                # Rescale boxes from img_size to image size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], image.shape).round()

                xywh_list = []
                confidence_list = []

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    xywh_list.append(bbox_rel(img_w, img_h, *xyxy))
                    confidence_list.append([conf.item()])

                    # xyxy = [xy.item() for xy in xyxy]  # tensor列表转为一般列表
                    # xywh = [xyxy[0] / img_w, xyxy[1] / img_h,
                    #         (xyxy[2] - xyxy[0]) / img_w, (xyxy[3] - xyxy[1]) / img_h]  # 转相对于宽高的坐标
                    # objects.append({'class': self.names[int(cls)], 'color': self.colors[int(cls)],
                    #                 'confidence': conf.item(), 'x': xywh[0], 'y': xywh[1], 'w': xywh[2], 'h': xywh[3]})

                # print('识别到:', len(xywh_list))
                xywhs = torch.Tensor(xywh_list)
                confss = torch.Tensor(confidence_list)

                # Pass detections to deepsort
                outputs = self.deepsort.update(xywhs, confss, image)
                # 归一化
                objs = []
                if type(outputs) is np.ndarray:
                    outputs.tolist()
                    for obj in outputs:
                        x = obj[0] / img_w
                        y = obj[1] / img_h
                        w = (obj[2] - obj[0]) / img_w
                        h = (obj[3] - obj[1]) / img_h
                        objs.append([x, y, w, h, obj[-1]])

                # print('跟踪到:', len(objs))
                # 转字典
                for i, obj in enumerate(objs):
                    objects.append({'x': obj[0], 'y': obj[1], 'w': obj[2], 'h': obj[3], 'id': obj[-1]})
        return objects
