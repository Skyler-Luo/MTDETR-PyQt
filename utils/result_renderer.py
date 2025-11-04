"""
结果渲染工具模块
统一处理检测结果的可视化绘制，避免重复代码
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os

from .constants import MTDETR_CLASS_NAMES, get_class_name as get_class_name_from_constants


class DetectionRenderer:
    """检测结果渲染器 - 负责绘制检测框、标签和掩码"""
    
    # 默认样式配置
    DEFAULT_STYLE = {
        'box_thickness': 2,
        'font_scale': 0.45,
        'font_thickness': 1,
        'label_padding': 2,
        'mask_alpha': 0.3,
    }
    
    # 颜色方案（20种不同颜色）
    COLOR_PALETTE = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
        (255, 0, 255), (0, 255, 255), (128, 0, 0), (0, 128, 0),
        (0, 0, 128), (128, 128, 0), (128, 0, 128), (0, 128, 128),
        (192, 192, 192), (255, 128, 0), (255, 0, 128), (128, 255, 0),
        (0, 255, 128), (128, 0, 255), (0, 128, 255), (255, 192, 0)
    ]
    
    def __init__(self, style=None):
        """
        初始化渲染器
        
        Args:
            style: 自定义样式配置，会与默认样式合并
        """
        self.style = {**self.DEFAULT_STYLE, **(style or {})}
        
        # 加载中文字体（支持多个备选路径）
        self.font = self._load_chinese_font()
    
    def _load_chinese_font(self, size=20):
        """加载中文字体"""
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
            "/System/Library/Fonts/PingFang.ttc",  # macOS
            "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        
        # 如果找不到字体，使用默认字体
        print("[渲染器] 警告: 未找到中文字体，文本显示可能异常")
        return ImageFont.load_default()
    
    @staticmethod
    def get_color(class_id):
        """
        根据类别ID获取颜色
        
        Args:
            class_id: 类别ID
            
        Returns:
            BGR颜色元组
        """
        return DetectionRenderer.COLOR_PALETTE[class_id % len(DetectionRenderer.COLOR_PALETTE)]
    
    def draw_box(self, img, box, color):
        """
        绘制检测框
        
        Args:
            img: 图像
            box: 边界框 [x1, y1, x2, y2]
            color: BGR颜色
            
        Returns:
            绘制后的图像
        """
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(
            img, (x1, y1), (x2, y2), 
            color, self.style['box_thickness']
        )
        return img
    
    def draw_label(self, img, box, label, color, show_conf=True):
        """
        绘制标签（使用OpenCV绘制英文，更稳定）
        
        Args:
            img: 图像
            box: 边界框 [x1, y1, x2, y2]
            label: 标签文本
            color: 背景颜色
            show_conf: 是否显示置信度
            
        Returns:
            绘制后的图像
        """
        x1, y1 = int(box[0]), int(box[1])
        
        # 使用OpenCV绘制英文文本（稳定可靠）
        # 计算文本尺寸
        (label_w, label_h), _ = cv2.getTextSize(
            label, 
            cv2.FONT_HERSHEY_SIMPLEX, 
            self.style['font_scale'], 
            self.style['font_thickness']
        )
        
        padding = self.style['label_padding']
        
        # 绘制标签背景
        cv2.rectangle(
            img,
            (x1, y1 - label_h - 2 * padding),
            (x1 + label_w + 2 * padding, y1),
            color, -1
        )
        
        # 绘制标签文字
        cv2.putText(
            img, label,
            (x1 + padding, y1 - padding),
            cv2.FONT_HERSHEY_SIMPLEX, 
            self.style['font_scale'],
            (255, 255, 255), 
            self.style['font_thickness']
        )
        
        return img
    
    def draw_detection(self, img, box, class_id, confidence, class_name, show_box=True, show_label=True, show_conf=True, color=None):
        """
        绘制单个检测结果（框+标签）
        
        Args:
            img: 图像
            box: 边界框 [x1, y1, x2, y2]
            class_id: 类别ID
            confidence: 置信度
            class_name: 类别名称
            show_box: 是否显示边界框
            show_label: 是否显示标签
            show_conf: 是否显示置信度
            color: 自定义颜色，如果为None则使用默认调色板
            
        Returns:
            绘制后的图像
        """
        # 确定颜色
        if color is None:
            color = self.get_color(class_id)
        
        # 绘制边界框
        if show_box:
            self.draw_box(img, box, color)
        
        # 绘制标签
        if show_label:
            label = class_name
            if show_conf:
                label += f' {confidence:.2f}'
            self.draw_label(img, box, label, color, show_conf)
        
        return img
    
    def draw_segmentation_mask(self, img, mask, class_id, class_name="", alpha=None, color=None, draw_contours=True):
        """
        绘制分割掩码
        
        Args:
            img: 图像
            mask: 掩码数组（2D或3D）
            class_id: 类别ID
            class_name: 类别名称（可选）
            alpha: 透明度，如果为None则使用默认值
            color: 自定义颜色，如果为None则使用默认调色板
            draw_contours: 是否绘制轮廓
            
        Returns:
            绘制后的图像
        """
        if alpha is None:
            alpha = self.style['mask_alpha']
        
        if color is None:
            color = self.get_color(class_id)
        
        # 处理掩码格式
        if len(mask.shape) == 3:
            mask_binary = (mask.max(axis=0) > 0.5).astype(np.uint8)
        else:
            mask_binary = (mask > 0.5).astype(np.uint8)
        
        # 检查掩码是否有内容
        if np.sum(mask_binary) == 0:
            return img
        
        # 创建彩色掩码
        colored_mask = np.zeros_like(img)
        colored_mask[mask_binary > 0] = color
        
        # 半透明叠加
        img = cv2.addWeighted(img, 1, colored_mask, alpha, 0)
        
        # 绘制轮廓
        if draw_contours:
            contours, _ = cv2.findContours(
                mask_binary, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            cv2.drawContours(img, contours, -1, color, 2)
        
        return img
    
    def draw_all_segmentation_masks(self, img, seg_masks, class_names=None):
        """
        绘制所有分割掩码
        
        Args:
            img: 图像
            seg_masks: 分割掩码数组，形状为 (num_classes, H, W)
            class_names: 类别名称字典 {class_id: class_name}
            
        Returns:
            绘制后的图像
        """
        if seg_masks is None:
            return img
        
        # 转换为numpy数组
        if hasattr(seg_masks, 'cpu'):
            seg_masks_np = seg_masks.cpu().numpy()
        else:
            seg_masks_np = np.array(seg_masks)
        
        # 处理掩码维度: 支持 2D, 3D, 4D
        # 2D: (H, W) - 单类别单图
        # 3D: (C, H, W) - 多类别单图
        # 4D: (1, C, H, W) or (N, C, H, W) - 批处理格式
        if len(seg_masks_np.shape) == 4:
            # 批处理格式，取第一张图片的掩码
            if seg_masks_np.shape[0] == 1:
                seg_masks_np = seg_masks_np[0]  # 变成 (C, H, W)
                num_classes = seg_masks_np.shape[0]
            else:
                # 多张图片，只使用第一张
                seg_masks_np = seg_masks_np[0]
                num_classes = seg_masks_np.shape[0]
        elif len(seg_masks_np.shape) == 3:
            num_classes = seg_masks_np.shape[0]
        elif len(seg_masks_np.shape) == 2:
            num_classes = 1
            seg_masks_np = seg_masks_np[np.newaxis, ...]
        else:
            # 不支持的形状，静默返回原图
            return img
        
        # 绘制每个类别的掩码
        for cls_idx in range(num_classes):
            mask_layer = seg_masks_np[cls_idx]
            
            # 获取类别名称
            class_name = ""
            if class_names and cls_idx in class_names:
                class_name = class_names[cls_idx]
            
            # 绘制掩码
            img = self.draw_segmentation_mask(
                img, mask_layer, cls_idx, class_name
            )
        
        return img
    
    def get_class_name(self, class_id, result=None, model=None):
        """
        获取类别名称
        
        Args:
            class_id: 类别ID
            result: 预测结果对象（可能包含names属性）
            model: 模型对象（可能包含names属性）
            
        Returns:
            类别名称字符串
        """
        # 优先使用统一的类别名称函数
        class_name = get_class_name_from_constants(class_id)
        
        # 如果是未知类别，尝试从result或model获取
        if class_name.startswith('Unknown-'):
            # 方法1: 从 result.names 获取
            if result and hasattr(result, 'names') and result.names:
                if isinstance(result.names, dict):
                    result_name = result.names.get(class_id)
                    if result_name:
                        return result_name
                elif isinstance(result.names, list) and class_id < len(result.names):
                    return result.names[class_id]
            
            # 方法2: 从 model.names 获取
            if model and hasattr(model, 'names'):
                if isinstance(model.names, dict):
                    model_name = model.names.get(class_id)
                    if model_name:
                        return model_name
                elif isinstance(model.names, list) and class_id < len(model.names):
                    return model.names[class_id]
        
        return class_name


class BannerRenderer:
    """横幅渲染器 - 用于绘制警告、信息等横幅（支持中文）"""
    
    @staticmethod
    def _get_chinese_font(size=24):
        """获取中文字体"""
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",    # 黑体
            "C:/Windows/Fonts/simsun.ttc",    # 宋体
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        
        return ImageFont.load_default()
    
    @staticmethod
    def draw_warning_banner(img, warnings, bg_color=(0, 0, 139)):
        """
        在图像顶部绘制警告横幅（支持中文）
        
        Args:
            img: 图像
            warnings: 警告信息列表
            bg_color: 背景颜色（默认深红色）
            
        Returns:
            绘制后的图像
        """
        if not warnings:
            return img
        
        # 创建横幅
        banner_height = 40 * len(warnings)
        banner = np.zeros((banner_height, img.shape[1], 3), dtype=np.uint8)
        banner[:] = bg_color
        
        # 使用PIL绘制中文文字
        banner_pil = Image.fromarray(cv2.cvtColor(banner, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(banner_pil)
        font = BannerRenderer._get_chinese_font(size=24)
        
        for idx, warning in enumerate(warnings):
            draw.text(
                (10, 8 + idx * 40),
                warning,
                font=font,
                fill=(255, 255, 255)
            )
        
        # 转换回OpenCV格式
        banner = cv2.cvtColor(np.array(banner_pil), cv2.COLOR_RGB2BGR)
        
        # 拼接到图像顶部
        result = np.vstack([banner, img])
        return result
    
    @staticmethod
    def draw_info_banner(img, info_items, bg_color=(60, 60, 60)):
        """
        在图像底部绘制信息横幅（支持中文）
        
        Args:
            img: 图像
            info_items: 信息项列表
            bg_color: 背景颜色（默认深灰色）
            
        Returns:
            绘制后的图像
        """
        if not info_items:
            return img
        
        # 创建信息横幅
        info_banner_height = 40
        info_banner = np.zeros((info_banner_height, img.shape[1], 3), dtype=np.uint8)
        info_banner[:] = bg_color
        
        # 使用PIL绘制中文文字
        info_banner_pil = Image.fromarray(cv2.cvtColor(info_banner, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(info_banner_pil)
        font = BannerRenderer._get_chinese_font(size=20)
        
        # 合并信息
        info_combined = " | ".join(info_items)
        draw.text(
            (10, 10),
            info_combined,
            font=font,
            fill=(255, 255, 255)
        )
        
        # 转换回OpenCV格式
        info_banner = cv2.cvtColor(np.array(info_banner_pil), cv2.COLOR_RGB2BGR)
        
        # 拼接到图像底部
        result = np.vstack([img, info_banner])
        return result


def create_detection_renderer(style=None):
    """
    工厂函数：创建检测渲染器
    
    Args:
        style: 自定义样式配置
        
    Returns:
        DetectionRenderer实例
    """
    return DetectionRenderer(style)

