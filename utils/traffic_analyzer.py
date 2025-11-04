"""
交通场景分析工具
"""

import cv2
import numpy as np


class TrafficLightAnalyzer:
    """红绿灯颜色识别"""
    
    @staticmethod
    def detect_color(img, bbox, debug=False):
        """
        检测红绿灯颜色
        
        Args:
            img: 原始图像
            bbox: 边界框 [x1, y1, x2, y2]
            debug: 是否输出调试信息
            
        Returns:
            str: 'red', 'yellow', 'green', 'unknown'
        """
        x1, y1, x2, y2 = map(int, bbox)
        
        # 确保坐标在图像范围内
        h, w = img.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 <= x1 or y2 <= y1:
            return 'unknown'
        
        # 裁剪红绿灯区域
        roi = img[y1:y2, x1:x2]
        
        if roi.size == 0:
            return 'unknown'
        
        # 转换到 HSV 颜色空间
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # 红色
        red_lower1 = np.array([0, 70, 70])
        red_upper1 = np.array([10, 255, 255])
        red_lower2 = np.array([160, 70, 70])
        red_upper2 = np.array([180, 255, 255])
        
        # 黄色
        yellow_lower = np.array([15, 70, 70])
        yellow_upper = np.array([40, 255, 255])
        
        # 绿色
        green_lower = np.array([35, 40, 40])
        green_upper = np.array([95, 255, 255])
        
        # 创建掩码
        red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
        red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
        red_mask = cv2.bitwise_or(red_mask1, red_mask2)
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        green_mask = cv2.inRange(hsv, green_lower, green_upper)
        
        # 计算每种颜色的像素数量
        red_pixels = cv2.countNonZero(red_mask)
        yellow_pixels = cv2.countNonZero(yellow_mask)
        green_pixels = cv2.countNonZero(green_mask)
        
        total_pixels = roi.shape[0] * roi.shape[1]
        
        # 调试信息
        if debug:
            print(f"[红绿灯检测] ROI尺寸: {roi.shape}, 总像素: {total_pixels}")
            print(f"[红绿灯检测] 红色像素: {red_pixels} ({red_pixels/total_pixels*100:.1f}%)")
            print(f"[红绿灯检测] 黄色像素: {yellow_pixels} ({yellow_pixels/total_pixels*100:.1f}%)")
            print(f"[红绿灯检测] 绿色像素: {green_pixels} ({green_pixels/total_pixels*100:.1f}%)")
        
        # 找出最多的颜色
        colors = {
            'red': red_pixels,
            'yellow': yellow_pixels,
            'green': green_pixels
        }
        
        max_color = max(colors.items(), key=lambda x: x[1])
        
        min_pixels_required = max(10, int(total_pixels * 0.01))
        
        if max_color[1] < min_pixels_required:
            if debug:
                print(f"[红绿灯检测] 像素数不足 ({max_color[1]} < {min_pixels_required})，返回 unknown")
            return 'unknown'
        
        if debug:
            print(f"[红绿灯检测] 检测结果: {max_color[0]}")
        
        return max_color[0]
    
    @staticmethod
    def get_color_name_chinese(color):
        """获取中文颜色名"""
        color_map = {
            'red': '红灯',
            'yellow': '黄灯',
            'green': '绿灯',
            'unknown': '未知'
        }
        return color_map.get(color, '未知')
    
    @staticmethod
    def get_color_bgr(color):
        """获取颜色对应的 BGR 值（用于显示）"""
        color_map = {
            'red': (0, 0, 255),
            'yellow': (0, 255, 255),
            'green': (0, 255, 0),
            'unknown': (128, 128, 128)
        }
        return color_map.get(color, (128, 128, 128))


class DrivableAreaAnalyzer:
    """可驾驶区域分析（基于 Real-time Multi-task Transformer 分割结果）"""
    
    def __init__(self, drivable_mask=None):
        """
        初始化
        
        Args:
            drivable_mask: Real-time Multi-task Transformer 分割出的可驾驶区域掩码 (numpy array)
        """
        self.drivable_mask = drivable_mask
    
    def set_drivable_mask(self, mask):
        """设置可驾驶区域掩码"""
        self.drivable_mask = mask
    
    def is_in_drivable_area(self, bbox):
        """
        判断边界框是否在可驾驶区域内（基于 Real-time Multi-task Transformer 分割掩码）
        
        Args:
            bbox: 边界框 [x1, y1, x2, y2]
            
        Returns:
            bool: 是否在可驾驶区域内
            float: 重叠比例 (0-1)
        """
        if self.drivable_mask is None:
            return False, 0.0
        
        x1, y1, x2, y2 = map(int, bbox)
        
        # 确保坐标在图像范围内
        h, w = self.drivable_mask.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        
        if x2 <= x1 or y2 <= y1:
            return False, 0.0
        
        # 获取边界框区域的掩码
        bbox_mask = self.drivable_mask[y1:y2, x1:x2]
        
        if bbox_mask.size == 0:
            return False, 0.0
        
        # 计算边界框内可驾驶区域的像素数
        if len(bbox_mask.shape) == 3:
            bbox_mask = cv2.cvtColor(bbox_mask, cv2.COLOR_BGR2GRAY)
        
        drivable_pixels = np.sum(bbox_mask > 0)
        total_pixels = bbox_mask.shape[0] * bbox_mask.shape[1]
        
        overlap_ratio = drivable_pixels / total_pixels if total_pixels > 0 else 0
        
        # 如果重叠比例超过30%，认为在可驾驶区域内
        is_in = overlap_ratio > 0.3
        
        return is_in, overlap_ratio
    
    def draw_drivable_zone(self, img, color=(0, 255, 255), alpha=0.3):
        """
        在图像上绘制可驾驶区域（基于分割掩码）
        
        Args:
            img: 图像
            color: 颜色 (BGR)
            alpha: 透明度
            
        Returns:
            绘制后的图像
        """
        if self.drivable_mask is None:
            return img
        
        overlay = img.copy()
        
        # 将掩码转换为灰度图
        if len(self.drivable_mask.shape) == 3:
            # 检查是否是 BGR 图像（3通道）
            if self.drivable_mask.shape[2] == 3:
                mask_gray = cv2.cvtColor(self.drivable_mask, cv2.COLOR_BGR2GRAY)
            else:
                # 如果是其他 3D 形状，取第一个通道
                mask_gray = self.drivable_mask[:, :, 0]
        elif len(self.drivable_mask.shape) == 2:
            # 已经是 2D 灰度图
            mask_gray = self.drivable_mask
        else:
            # 不支持的形状，返回原图
            return img
        
        # 创建彩色掩码
        colored_mask = np.zeros_like(img)
        colored_mask[mask_gray > 0] = color
        
        # 混合原图和掩码
        result = cv2.addWeighted(overlay, 1 - alpha, colored_mask, alpha, 0)
        
        # 绘制可驾驶区域轮廓
        contours, _ = cv2.findContours(mask_gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(result, contours, -1, color, 2)
        
        # 添加文字说明
        if len(contours) > 0:
            # 在最大轮廓上方添加文字
            largest_contour = max(contours, key=cv2.contourArea)
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(
                    result, "Drivable Area",
                    (cx - 80, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2
                )
        
        return result
