"""
预测线程模块（重构版）
职责：管理异步预测任务，避免UI冻结
"""

import os
import cv2
import numpy as np
from pathlib import Path
from PyQt5.QtCore import QThread, pyqtSignal

from utils import (
    DetectionRenderer, BannerRenderer, TrafficLightAnalyzer, DrivableAreaAnalyzer,
    YOLO_PERSON_CLASS_ID, YOLO_TRAFFIC_LIGHT_CLASS_ID, YOLO_OTHER_CLASS_ID,
    YOLO_PERSON_ORIGINAL_ID, YOLO_TRAFFIC_LIGHT_ORIGINAL_ID
)


class PredictThread(QThread):
    """
    预测线程 - 异步执行模型推理
    
    Signals:
        finished: (success: bool, message: str) - 预测完成信号
        progress: (message: str) - 进度更新信号
        progress_percent: (percent: int) - 进度百分比信号 (0-100)
        log: (message: str) - 日志输出信号
    """
    
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    progress_percent = pyqtSignal(int)  # 新增：进度百分比信号
    log = pyqtSignal(str)
    
    def __init__(self, model, source, params, person_model=None):
        """
        初始化预测线程
        
        Args:
            model: 主模型（MTDETR）
            source: 数据源路径
            params: 预测参数字典
            person_model: 可选的行人检测模型（YOLOv10n）
        """
        super().__init__()
        self.model = model
        self.person_model = person_model
        self.source = source
        self.params = params
        
        # 创建渲染器
        self.renderer = DetectionRenderer()
    
    def reset_model_config(self):
        """重置模型配置，确保新参数生效"""
        if hasattr(self.model, 'predictor') and self.model.predictor is not None:
            self.model.predictor = None
        
        # 清理 overrides 中的显示相关配置
        if hasattr(self.model, 'overrides'):
            display_keys = ['show_boxes', 'show_labels', 'show_conf', 
                          'show', 'save', 'line_width']
            for key in display_keys:
                self.model.overrides.pop(key, None)
    
    def run(self):
        """执行预测任务"""
        try:
            self.progress.emit("正在进行预测...")
            
            # 打印参数以便调试
            self.log.emit(f"[预测参数] show_boxes={self.params['show_boxes']}, "
                         f"show_labels={self.params['show_labels']}, "
                         f"show_conf={self.params['show_conf']}, "
                         f"enable_person_detection={self.params.get('enable_person_detection', False)}")
            
            # 重置模型配置
            self.reset_model_config()
            
            # 根据是否启用行人检测选择预测模式
            if self.person_model and self.params.get('enable_person_detection', False):
                self._dual_model_predict()
            else:
                self._single_model_predict()
            
            # 完成
            self.progress.emit("预测完成！")
            output_path = os.path.join(self.params['project'], self.params['name'])
            self.finished.emit(True, output_path)
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.log.emit(f"[错误] {error_msg}")
            self.finished.emit(False, str(e))
    
    def _single_model_predict(self):
        """单模型预测流程"""
        # 使用 hook 捕获分割掩码
        from ultralytics.models.mtdetr.predict import MTDETRPredictor
        
        # 创建 predictor
        if not hasattr(self.model, 'predictor') or self.model.predictor is None:
            self.model.predictor = MTDETRPredictor(overrides={
                'imgsz': self.params['imgsz'],
                'device': self.params['device'],
                'mask_threshold': self.params['mask_threshold']
            })
            self.model.predictor.setup_model(model=self.model.model)
        
        # 设置参数
        self.model.predictor.args.imgsz = self.params['imgsz']
        self.model.predictor.args.device = self.params['device']
        self.model.predictor.args.mask_threshold = self.params['mask_threshold']
        
        # 捕获分割掩码 - 使用列表收集所有图片的掩码
        seg_masks_list = []
        original_postprocess = self.model.predictor.postprocess
        
        def custom_postprocess(preds, img, orig_imgs):
            nonlocal seg_masks_list
            results, seg_mask = original_postprocess(preds, img, orig_imgs)
            # 收集每次的掩码
            if seg_mask is not None:
                # 检查是否是批处理（多张图片一次处理）
                if hasattr(seg_mask, 'shape') and len(seg_mask.shape) > 0:
                    # 如果是批处理，seg_mask 包含多张图片的掩码
                    seg_masks_list.append(seg_mask)
                else:
                    seg_masks_list.append(seg_mask)
            return results, seg_mask
        
        self.model.predictor.postprocess = custom_postprocess
        
        try:
            results = self.model.predict(
                source=self.source,
                imgsz=self.params['imgsz'],
                device=self.params['device'],
                conf=self.params.get('conf', 0.25),  # 置信度阈值
                mask_threshold=self.params['mask_threshold'],
                show_boxes=self.params['show_boxes'],
                show_labels=self.params['show_labels'],
                show_conf=self.params['show_conf'],
                save=False,  # 先不保存，手动绘制后再保存
                save_txt=False,  # 禁用ultralytics的标签保存，使用自定义保存
                save_conf=False,
                project=self.params['project'],
                name=self.params['name'],
                exist_ok=True
            )
        finally:
            self.model.predictor.postprocess = original_postprocess
        
        self.log.emit(f"[单模型] 预测完成，结果数量: {len(results)}")
        
        # 打印调试信息
        if seg_masks_list:
            # 检查掩码批次信息
            if len(seg_masks_list) > 0 and hasattr(seg_masks_list[0], 'shape'):
                self.log.emit(f"[单模型] ✓ 成功获取 {len(seg_masks_list)} 批掩码，第一批形状: {seg_masks_list[0].shape}")
            else:
                self.log.emit(f"[单模型] ✓ 成功获取 {len(seg_masks_list)} 个分割掩码")
        else:
            self.log.emit(f"[单模型] ✗ 未获取到分割掩码")
        
        # 手动绘制并保存结果
        if self.params['save']:
            self._save_single_model_results(results, seg_masks_list)
    
    def _save_single_model_results(self, results, seg_masks_list=None):
        """保存单模型预测结果"""
        output_dir = Path(self.params['project']) / self.params['name']
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建labels目录用于保存标签文件
        labels_dir = output_dir / "labels"
        labels_dir.mkdir(exist_ok=True)
        
        # 处理掩码：可能是列表形式（每次调用一张图）或批处理形式（一次多张图）
        seg_masks = None
        if seg_masks_list:
            if len(seg_masks_list) == 1:
                # 可能是批处理，一次返回所有图片的掩码
                seg_masks = seg_masks_list[0]
            elif len(seg_masks_list) == len(results):
                # 每张图片单独返回的掩码列表
                seg_masks = seg_masks_list
            else:
                self.log.emit(f"[警告] 掩码数量({len(seg_masks_list)})与结果数量({len(results)})不匹配")
        
        total_images = len(results)
        for i, result in enumerate(results):
            # 发送进度百分比
            progress_percent = int((i + 1) / total_images * 100)
            self.progress_percent.emit(progress_percent)
            self.progress.emit(f"正在保存: {i+1}/{total_images}")
            img = result.orig_img.copy()
            
            # 1. 绘制分割掩码
            if seg_masks is not None:
                try:
                    # 构建类别名称字典
                    class_names = {}
                    if hasattr(self.model, 'names') and isinstance(self.model.names, dict):
                        class_names = self.model.names
                    
                    # 根据掩码类型提取当前图片的掩码
                    if isinstance(seg_masks, list) and i < len(seg_masks):
                        current_mask = seg_masks[i]
                    else:
                        # 假设是批处理格式，直接传入整个掩码
                        current_mask = seg_masks
                    
                    # 绘制所有掩码
                    img = self.renderer.draw_all_segmentation_masks(
                        img, current_mask, class_names
                    )
                    self.log.emit(f"[单模型] 图片 {i+1}/{len(results)} - ✓ 绘制分割掩码成功")
                except Exception as e:
                    self.log.emit(f"[单模型] 图片 {i+1}/{len(results)} - ✗ 绘制掩码失败: {e}")
                    import traceback
                    self.log.emit(traceback.format_exc())
            
            # 2. 绘制检测框和标签
            if result.boxes is not None:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    # 获取类别名称
                    class_name = self.renderer.get_class_name(cls_id, result, self.model)
                    self.log.emit(f"[单模型] 检测: 类别ID={cls_id}, 类别名称='{class_name}', 置信度={conf:.2f}")
                    
                    # 绘制检测结果
                    img = self.renderer.draw_detection(
                        img, [x1, y1, x2, y2], cls_id, conf, class_name,
                        show_box=self.params['show_boxes'],
                        show_label=self.params['show_labels'],
                        show_conf=self.params['show_conf']
                    )
            
            # 3. 保存图像
            if hasattr(result, 'path'):
                filename = Path(result.path).name
            else:
                filename = f"image_{i}.jpg"
            
            output_path = output_dir / filename
            cv2.imwrite(str(output_path), img)
            self.log.emit(f"[单模型] 保存: {output_path}")
            
            # 4. 保存标签文件（包含置信度）
            if self.params.get('save_txt', True) and result.boxes is not None:
                label_filename = Path(filename).stem + '.txt'
                label_path = labels_dir / label_filename
                
                with open(label_path, 'w') as f:
                    for box in result.boxes:
                        xywhn = box.xywhn[0]
                        cls = int(box.cls[0])
                        conf = float(box.conf[0])
                        # 保存格式: class_id x_center y_center width height confidence
                        f.write(f"{cls} {xywhn[0]} {xywhn[1]} {xywhn[2]} {xywhn[3]} {conf}\n")
                
                self.log.emit(f"[单模型] 保存标签: {label_path}")
    
    def _dual_model_predict(self):
        """双模型预测流程：MTDETR + YOLOv10n"""
        self.progress.emit("双模型检测中...")
        
        # 运行 MTDETR 预测并捕获分割掩码
        self.log.emit("[双模型] 运行 MTDETR...")
        mtdetr_seg_masks_list = []
        
        from ultralytics.models.mtdetr.predict import MTDETRPredictor
        
        if not hasattr(self.model, 'predictor') or self.model.predictor is None:
            self.model.predictor = MTDETRPredictor(overrides={
                'imgsz': self.params['imgsz'],
                'device': self.params['device'],
                'mask_threshold': self.params['mask_threshold']
            })
            self.model.predictor.setup_model(model=self.model.model)
        
        # Hook postprocess to capture seg_masks
        original_postprocess = self.model.predictor.postprocess
        
        def custom_postprocess(preds, img, orig_imgs):
            nonlocal mtdetr_seg_masks_list
            results, seg_mask = original_postprocess(preds, img, orig_imgs)
            # 收集每次的掩码
            if seg_mask is not None:
                mtdetr_seg_masks_list.append(seg_mask)
            return results, seg_mask
        
        self.model.predictor.postprocess = custom_postprocess
        
        try:
            mtdetr_output = self.model.predict(
                source=self.source,
                imgsz=self.params['imgsz'],
                device=self.params['device'],
                conf=self.params.get('conf', 0.25),  # 置信度阈值
                mask_threshold=self.params['mask_threshold'],
                show_labels=self.params['show_labels'],
                save=False,
                verbose=False
            )
        finally:
            self.model.predictor.postprocess = original_postprocess
        
        mtdetr_results = mtdetr_output if isinstance(mtdetr_output, list) else [mtdetr_output]
        
        # 2. 运行 YOLOv10n 行人和红绿灯检测
        self.log.emit("[双模型] 运行 YOLOv10n...")
        # 使用统一的类别ID常量
        person_results = self.person_model.predict(
            source=self.source,
            imgsz=self.params['imgsz'],
            device=self.params['device'],
            classes=[YOLO_PERSON_ORIGINAL_ID, YOLO_TRAFFIC_LIGHT_ORIGINAL_ID],
            conf=self.params.get('conf', 0.25),  # 使用用户设置的置信度阈值
            save=False,
            verbose=False
        )
        
        # 3. 合并并保存结果
        self.progress.emit("合并检测结果...")
        if mtdetr_seg_masks_list:
            self.log.emit(f"[双模型] ✓ 成功获取 {len(mtdetr_seg_masks_list)} 个分割掩码")
        self._merge_and_save_dual_results(mtdetr_results, person_results, mtdetr_seg_masks_list)
    
    def _merge_and_save_dual_results(self, mtdetr_results, person_results, seg_masks_list=None):
        """合并双模型结果并保存"""
        output_dir = Path(self.params['project']) / self.params['name']
        output_dir.mkdir(parents=True, exist_ok=True)
        labels_dir = output_dir / "labels"
        labels_dir.mkdir(exist_ok=True)
        
        # 处理掩码：可能是列表形式或批处理形式
        seg_masks = None
        if seg_masks_list:
            if len(seg_masks_list) == 1:
                # 可能是批处理，一次返回所有图片的掩码
                seg_masks = seg_masks_list[0]
            elif len(seg_masks_list) == len(mtdetr_results):
                # 每张图片单独返回的掩码列表
                seg_masks = seg_masks_list
            else:
                self.log.emit(f"[警告] 掩码数量({len(seg_masks_list)})与结果数量({len(mtdetr_results)})不匹配")
        
        total_images = len(mtdetr_results)
        for i, (mtdetr_result, person_result) in enumerate(zip(mtdetr_results, person_results)):
            # 发送进度百分比
            progress_percent = int((i + 1) / total_images * 100)
            self.progress_percent.emit(progress_percent)
            self.progress.emit(f"正在保存: {i+1}/{total_images}")
            img = mtdetr_result.orig_img.copy()
            img_h, img_w = img.shape[:2]
            
            # 初始化分析器
            traffic_light_analyzer = TrafficLightAnalyzer()
            
            # 提取可驾驶区域掩码
            drivable_mask = self._extract_drivable_mask(seg_masks, i, img.shape)
            drivable_area_analyzer = DrivableAreaAnalyzer(drivable_mask)
            
            warnings = []
            traffic_lights_detected = []
            pedestrians_in_drivable = []
            
            # 1. 绘制 MTDETR 分割掩码
            if seg_masks is not None and i < len(seg_masks):
                try:
                    class_names = {}
                    if hasattr(self.model, 'names') and isinstance(self.model.names, dict):
                        class_names = self.model.names
                    
                    img = self.renderer.draw_all_segmentation_masks(
                        img, seg_masks[i], class_names
                    )
                except Exception as e:
                    self.log.emit(f"[双模型] 绘制掩码失败: {e}")
            
            # 2. 绘制 MTDETR 检测框
            if mtdetr_result.boxes is not None:
                for box in mtdetr_result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    class_name = self.renderer.get_class_name(cls_id, mtdetr_result, self.model)
                    self.log.emit(f"[双模型-MTDETR] 检测: 类别ID={cls_id}, 类别名称='{class_name}', 置信度={conf:.2f}")
                    
                    img = self.renderer.draw_detection(
                        img, [x1, y1, x2, y2], cls_id, conf, class_name,
                        show_box=self.params['show_boxes'],
                        show_label=self.params['show_labels'],
                        show_conf=self.params['show_conf']
                    )
            
            # 3. 绘制可驾驶区域
            if drivable_mask is not None and np.sum(drivable_mask) > 0:
                img = drivable_area_analyzer.draw_drivable_zone(img)
            
            # 4. 绘制 YOLOv10n 检测结果（行人+红绿灯）
            if person_result.boxes is not None and len(person_result.boxes) > 0:
                for box in person_result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    bbox = [x1, y1, x2, y2]
                    
                    # 使用统一的类别ID常量
                    if cls_id == YOLO_PERSON_ORIGINAL_ID:  # Person
                        # 改进的判断逻辑：使用行人底部中心点和扩展的可驾驶区域
                        # 因为分割掩码本身会排除行人，所以需要扩展掩码来判断行人是否靠近道路
                        is_in_road = self._is_pedestrian_on_road(bbox, drivable_mask, img_h, img_w)
                        
                        if is_in_road:
                            color = (0, 0, 255)
                            label_text = "Person-OnRoad"  # 英文标签
                            pedestrians_in_drivable.append({
                                'bbox': bbox, 'conf': conf, 'in_road': is_in_road
                            })
                            warnings.append(f"警告: 行人出现在道路区域内!")
                        else:
                            color = (0, 255, 0)
                            label_text = "Person"  # 英文标签
                        
                        self.log.emit(f"[双模型-YOLOv10n] 检测: 行人, 置信度={conf:.2f}, 在道路上={is_in_road}")
                    
                    elif cls_id == YOLO_TRAFFIC_LIGHT_ORIGINAL_ID:  # Traffic Light
                        # 检测红绿灯颜色
                        light_color = traffic_light_analyzer.detect_color(img, bbox, debug=False)
                        color_name_cn = traffic_light_analyzer.get_color_name_chinese(light_color)
                        color = traffic_light_analyzer.get_color_bgr(light_color)
                        # 使用英文标签
                        color_name_en = light_color.capitalize()  # red->Red, green->Green, yellow->Yellow
                        label_text = f"Light-{color_name_en}"
                        
                        traffic_lights_detected.append({
                            'bbox': bbox, 'color': light_color, 'conf': conf
                        })
                        
                        if light_color == 'red':
                            warnings.append(f"提示: 检测到红灯")
                        
                        self.log.emit(f"[双模型-YOLOv10n] 检测: 红绿灯={color_name_cn}, 置信度={conf:.2f}")
                    else:
                        color = (255, 0, 255)
                        label_text = f"Unknown-{cls_id}"  # 英文标签
                        self.log.emit(f"[双模型-YOLOv10n] 检测: 未知类别ID={cls_id}, 置信度={conf:.2f}")
                    
                    # 绘制
                    if self.params['show_labels']:
                        label = label_text
                        if self.params['show_conf']:
                            label += f" {conf:.2f}"
                    else:
                        label = ""
                    
                    if self.params['show_boxes']:
                        self.renderer.draw_box(img, bbox, color)
                    
                    if label and self.params['show_labels']:
                        self.renderer.draw_label(img, bbox, label, color)
            
            # 5. 添加警告横幅
            if warnings:
                img = BannerRenderer.draw_warning_banner(img, warnings)
            
            # 6. 添加信息横幅
            info_items = []
            if traffic_lights_detected:
                light_info = [f"{item['color']}" for item in traffic_lights_detected]
                info_items.append(f"红绿灯: {', '.join(light_info)}")
            if pedestrians_in_drivable:
                info_items.append(f"道路上行人: {len(pedestrians_in_drivable)} 人")
            
            if info_items:
                img = BannerRenderer.draw_info_banner(img, info_items)
            
            # 7. 保存图像
            if self.params['save']:
                filename = Path(mtdetr_result.path).name if hasattr(mtdetr_result, 'path') else f"image_{i}.jpg"
                output_path = output_dir / filename
                cv2.imwrite(str(output_path), img)
                self.log.emit(f"[双模型] 保存: {output_path}")
                
                # 打印检测摘要
                if warnings:
                    for warning in warnings:
                        self.log.emit(f"  ⚠️  {warning}")
                if traffic_lights_detected:
                    for tl in traffic_lights_detected:
                        self.log.emit(f"  🚦 红绿灯: {tl['color']} (置信度: {tl['conf']:.2f})")
                if pedestrians_in_drivable:
                    self.log.emit(f"  ⚠️  道路上检测到 {len(pedestrians_in_drivable)} 名行人!")
            
            # 8. 保存标签文件
            if self.params.get('save_txt', True):
                self._save_labels(filename, mtdetr_result, person_result, labels_dir)
    
    def _extract_drivable_mask(self, seg_masks, index, img_shape):
        """提取可驾驶区域掩码"""
        if seg_masks is None:
            return None
        
        # 根据掩码类型提取当前图片的掩码
        if isinstance(seg_masks, list):
            # 列表形式，每个元素是一张图片的掩码
            if index >= len(seg_masks):
                return None
            seg_mask = seg_masks[index]
        else:
            # 批处理形式，直接使用（假设包含所有图片）
            seg_mask = seg_masks
        
        if hasattr(seg_mask, 'cpu'):
            seg_mask_np = seg_mask.cpu().numpy()
        else:
            seg_mask_np = np.array(seg_mask)
        
        # 合并所有分割通道作为可驾驶区域
        # 处理多种可能的形状: (C, H, W), (1, C, H, W), (H, W)
        while len(seg_mask_np.shape) > 2:
            # 沿第一个维度取最大值，直到变成 2D
            seg_mask_np = seg_mask_np.max(axis=0)
        
        # 确保是 2D 灰度图
        if len(seg_mask_np.shape) == 2:
            drivable_mask = (seg_mask_np * 255).astype(np.uint8)
        else:
            # 如果还不是 2D，使用第一个通道
            drivable_mask = (seg_mask_np[0] * 255).astype(np.uint8)
        
        self.log.emit(f"[可驾驶区域] 提取成功，形状: {drivable_mask.shape}")
        
        return drivable_mask
    
    def _is_pedestrian_on_road(self, bbox, drivable_mask, img_h, img_w):
        """
        判断行人是否在道路上（改进版）
        
        策略：
        1. 计算行人底部中心点（脚的位置）
        2. 扩展可驾驶区域掩码（因为掩码会排除行人）
        3. 检查该点是否在扩展后的掩码附近
        4. 结合位置启发式规则（图像下半部分更可能是道路）
        
        Args:
            bbox: 行人边界框 [x1, y1, x2, y2]
            drivable_mask: 可驾驶区域掩码
            img_h: 图像高度
            img_w: 图像宽度
            
        Returns:
            bool: 是否在道路上
        """
        x1, y1, x2, y2 = bbox
        
        # 计算行人底部中心点（脚的位置）
        foot_x = int((x1 + x2) / 2)
        foot_y = int(y2)
        
        # 策略1: 基于位置的启发式规则
        # 如果行人在图像下半部分（通常是道路），更可能在路上
        in_lower_half = foot_y > img_h * 0.5
        
        # 策略2: 如果有可驾驶区域掩码，扩展掩码并检查
        if drivable_mask is not None and np.sum(drivable_mask) > 0:
            # 扩展可驾驶区域掩码（膨胀操作）
            # 这样可以包含行人周围的区域
            kernel_size = max(30, int(min(img_h, img_w) * 0.05))  # 动态核大小
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            expanded_mask = cv2.dilate(drivable_mask, kernel, iterations=1)
            
            # 检查脚部位置是否在扩展后的掩码内
            if 0 <= foot_y < expanded_mask.shape[0] and 0 <= foot_x < expanded_mask.shape[1]:
                on_expanded_road = expanded_mask[foot_y, foot_x] > 0
                
                # 综合判断：在扩展掩码内 且 在图像下半部分
                is_on_road = on_expanded_road and in_lower_half
                
                self.log.emit(f"[行人判断] 位置=({foot_x}, {foot_y}), 扩展掩码={on_expanded_road}, "
                             f"下半部={in_lower_half}, 最终判断={is_on_road}")
                
                return is_on_road
        
        # 策略3: 如果没有掩码，仅使用位置规则
        # 在图像下2/3区域且水平居中区域的行人更可能在路上
        in_road_vertical = foot_y > img_h * 0.4
        in_road_horizontal = img_w * 0.2 < foot_x < img_w * 0.8
        
        is_on_road = in_road_vertical and in_road_horizontal
        
        self.log.emit(f"[行人判断-无掩码] 位置=({foot_x}, {foot_y}), "
                     f"垂直={in_road_vertical}, 水平={in_road_horizontal}, 结果={is_on_road}")
        
        return is_on_road
    
    def _save_labels(self, filename, mtdetr_result, person_result, labels_dir):
        """保存标签文件"""
        label_filename = Path(filename).stem + '.txt'
        label_path = labels_dir / label_filename
        
        with open(label_path, 'w') as f:
            # 写入 MTDETR 的检测
            if mtdetr_result.boxes is not None:
                for box in mtdetr_result.boxes:
                    xywhn = box.xywhn[0]
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    f.write(f"{cls} {xywhn[0]} {xywhn[1]} {xywhn[2]} {xywhn[3]} {conf}\n")
            
            # 写入 YOLOv10n 的检测（使用特殊类别ID）
            if person_result.boxes is not None:
                for box in person_result.boxes:
                    xywhn = box.xywhn[0]
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])
                    
                    # 使用统一的类别ID常量
                    if cls_id == YOLO_PERSON_ORIGINAL_ID:
                        special_id = YOLO_PERSON_CLASS_ID
                    elif cls_id == YOLO_TRAFFIC_LIGHT_ORIGINAL_ID:
                        special_id = YOLO_TRAFFIC_LIGHT_CLASS_ID
                    else:
                        special_id = YOLO_OTHER_CLASS_ID
                    
                    f.write(f"{special_id} {xywhn[0]} {xywhn[1]} {xywhn[2]} {xywhn[3]} {conf}\n")
