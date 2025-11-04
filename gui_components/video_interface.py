"""
视频文件检测界面模块 - 包含视频离线检测和实时预览功能
"""

import os
import time
import cv2
from pathlib import Path
from datetime import datetime

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QLabel

from qfluentwidgets import (
    FluentIcon, PushButton, PrimaryPushButton, BodyLabel, SubtitleLabel,
    CardWidget, ScrollArea, ProgressRing, InfoBar, InfoBarPosition, TextEdit
)

from config import DATASET_DIR, DEFAULT_PARAMS
from .predict_thread import PredictThread
from .base_interface import BaseDetectionInterface
from utils import get_filename, parse_image_size


class StreamThread(QThread):
    """视频流处理线程（用于实时预览）"""
    frame_ready = pyqtSignal(object, object, float, object)  # 原始帧, 处理后帧, FPS, 检测结果
    error = pyqtSignal(str)
    log = pyqtSignal(str)  # 日志信号
    
    def __init__(self, model, source, params, person_model=None):
        super().__init__()
        self.model = model
        self.person_model = person_model  # YOLOv10n行人检测模型
        self.source = source
        self.params = params
        self.is_running = False
        self.is_paused = False  # 暂停状态
        self.is_recording = False
        self.video_writer = None
        self.current_result = None  # 保存当前帧的检测结果
        self.recording_output_path = None  # 录制输出路径
        
    def run(self):
        self.is_running = True
        
        try:
            # 导入所需模块
            import time
            import torch
            import numpy as np
            import traceback
            
            # 打开视频源
            if isinstance(self.source, int):
                cap = cv2.VideoCapture(self.source)
            else:
                cap = cv2.VideoCapture(self.source)
            
            if not cap.isOpened():
                self.error.emit("无法打开视频源")
                return
            
            fps_time = time.time()
            fps_counter = 0
            current_fps = 0
            
            # 初始化predictor并设置hook捕获分割掩码
            from ultralytics.models.mtdetr.predict import MTDETRPredictor
            
            if not hasattr(self.model, 'predictor') or self.model.predictor is None:
                self.model.predictor = MTDETRPredictor(overrides={
                    'imgsz': self.params.get('imgsz', (640, 640)),
                    'device': self.params.get('device', 'cpu'),
                    'mask_threshold': self.params.get('mask_threshold', [0.45, 0.9])
                })
                self.model.predictor.setup_model(model=self.model.model)
            
            # 保存原始postprocess
            original_postprocess = self.model.predictor.postprocess
            current_seg_mask = None
            
            def custom_postprocess(preds, img, orig_imgs):
                nonlocal current_seg_mask
                results, seg_mask = original_postprocess(preds, img, orig_imgs)
                current_seg_mask = seg_mask
                return results, seg_mask
            
            # 替换postprocess
            self.model.predictor.postprocess = custom_postprocess
            
            try:
                while self.is_running:
                    # 暂停检查
                    if self.is_paused:
                        time.sleep(0.1)  # 暂停时降低CPU占用
                        continue
                    
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # 原始帧
                    orig_frame = frame.copy()
                    processed_frame = frame.copy()  # 初始化处理后的帧
                    
                    # 重置当前分割掩码
                    current_seg_mask = None
                    
                    # 模型推理
                    try:
                        # 使用正确的参数调用predict
                        results = self.model.predict(
                            source=frame,
                            imgsz=self.params.get('imgsz', (640, 640)),
                            device=self.params.get('device', 'cpu'),
                            conf=self.params.get('conf', 0.25),  # 置信度阈值
                            mask_threshold=self.params.get('mask_threshold', [0.45, 0.9]),
                            verbose=False,
                            stream=False,
                            save=False
                        )
                        
                        # 获取处理后的帧
                        if results and len(results) > 0:
                            result = results[0]
                            self.current_result = result  # 保存当前结果，供截图使用
                            
                            # 调试：输出检测信息（仅第一帧）
                            if fps_counter == 0:
                                num_boxes = len(result.boxes) if hasattr(result, 'boxes') and result.boxes is not None else 0
                                has_seg_mask = current_seg_mask is not None
                                self.log.emit(f"[检测] 检测框: {num_boxes}, 分割掩码: {'是' if has_seg_mask else '否'}")
                                if has_seg_mask:
                                    if isinstance(current_seg_mask, torch.Tensor):
                                        self.log.emit(f"[检测] 掩码形状: {current_seg_mask.shape}")
                            
                            # 使用plot()绘制基础检测结果
                            processed_frame = result.plot()
                            
                            # 手动叠加分割掩码
                            if current_seg_mask is not None:
                                # 转换掩码为numpy数组
                                if isinstance(current_seg_mask, torch.Tensor):
                                    seg_mask_np = current_seg_mask.cpu().numpy()
                                else:
                                    seg_mask_np = current_seg_mask
                                
                                # 使用DetectionRenderer绘制分割掩码
                                from utils import DetectionRenderer
                                renderer = DetectionRenderer()
                                processed_frame = renderer.draw_all_segmentation_masks(
                                    processed_frame, seg_mask_np
                                )
                            
                            # 如果启用了行人检测，使用YOLOv10n进行额外检测
                            if self.person_model is not None:
                                try:
                                    # 重置YOLOv10n的predictor
                                    if hasattr(self.person_model, 'predictor'):
                                        self.person_model.predictor = None
                                    
                                    # YOLOv10n推理（使用用户设置的置信度阈值）
                                    from utils import YOLO_PERSON_ORIGINAL_ID, YOLO_TRAFFIC_LIGHT_ORIGINAL_ID
                                    person_results = self.person_model.predict(
                                        source=frame,
                                        imgsz=self.params.get('imgsz', (640, 640)),
                                        device=self.params.get('device', 'cpu'),
                                        classes=[YOLO_PERSON_ORIGINAL_ID, YOLO_TRAFFIC_LIGHT_ORIGINAL_ID],
                                        conf=self.params.get('conf', 0.25),  # 使用用户设置的置信度阈值
                                        verbose=False,
                                        stream=False,
                                        save=False
                                    )
                                    
                                    # 绘制YOLO检测结果
                                    if person_results and len(person_results) > 0:
                                        person_result = person_results[0]
                                        if hasattr(person_result, 'boxes') and person_result.boxes is not None:
                                            boxes = person_result.boxes
                                            num_yolo_detections = len(boxes)
                                            
                                            if fps_counter == 0:
                                                self.log.emit(f"[YOLO] 检测到 {num_yolo_detections} 个对象")
                                            
                                            # 手动绘制YOLO检测结果
                                            from utils import DetectionRenderer, YOLO_PERSON_CLASS_ID, YOLO_TRAFFIC_LIGHT_CLASS_ID
                                            renderer = DetectionRenderer()
                                            
                                            for box in boxes:
                                                cls_id = int(box.cls[0].item())
                                                conf = box.conf[0].item()
                                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                                bbox = [int(x1), int(y1), int(x2), int(y2)]
                                                
                                                # 映射类别ID
                                                if cls_id == 0:  # person in YOLO
                                                    mapped_cls_id = YOLO_PERSON_CLASS_ID
                                                    class_name = "Person"
                                                elif cls_id == 9:  # traffic light in YOLO
                                                    mapped_cls_id = YOLO_TRAFFIC_LIGHT_CLASS_ID
                                                    class_name = "TrafficLight"
                                                else:
                                                    mapped_cls_id = cls_id
                                                    class_name = f"Class-{cls_id}"
                                                
                                                # 绘制检测结果
                                                processed_frame = renderer.draw_detection(
                                                    processed_frame,
                                                    bbox,
                                                    mapped_cls_id,
                                                    conf,
                                                    class_name,
                                                    show_box=True,
                                                    show_label=True,
                                                    show_conf=True
                                                )
                                except Exception as yolo_e:
                                    if fps_counter == 0:
                                        self.log.emit(f"[YOLO错误] {yolo_e}")
                        else:
                            # 无检测结果，processed_frame已经初始化为frame.copy()
                            self.current_result = None
                        
                    except Exception as e:
                        self.log.emit(f"[推理错误] {e}")
                        self.log.emit(f"[错误详情] {traceback.format_exc()}")
                        # processed_frame已经初始化为frame.copy()
                        self.current_result = None
                    
                    # 计算FPS
                    fps_counter += 1
                    if time.time() - fps_time >= 1.0:
                        current_fps = fps_counter / (time.time() - fps_time)
                        fps_counter = 0
                        fps_time = time.time()
                    
                    # 录制
                    if self.is_recording and self.video_writer is not None:
                        if self.video_writer.isOpened():
                            self.video_writer.write(processed_frame)
                        else:
                            if fps_counter % 30 == 0:  # 每30帧提示一次
                                self.log.emit("[录制错误] 视频写入器未正常打开")
                    
                    # 发送帧（包含检测结果）
                    self.frame_ready.emit(orig_frame, processed_frame, current_fps, self.current_result)
            finally:
                # 恢复原始postprocess
                self.model.predictor.postprocess = original_postprocess
                
            cap.release()
            if self.video_writer:
                self.video_writer.release()
                
        except Exception as e:
            self.error.emit(f"处理错误: {str(e)}")
    
    def stop(self):
        """停止处理"""
        self.is_running = False
        self.wait()
    
    def pause(self):
        """暂停处理"""
        self.is_paused = True
        self.log.emit("[暂停] 视频流已暂停")
    
    def resume(self):
        """恢复处理"""
        self.is_paused = False
        self.log.emit("[继续] 视频流已恢复")
    
    def start_recording(self, output_path, frame_size):
        """开始录制"""
        import os
        from pathlib import Path
        
        # 确保输出目录存在
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建视频写入器（使用实际帧尺寸）
        # 尝试多种编解码器，以提高兼容性
        codecs = [
            ('mp4v', '.mp4'),  # MPEG-4
            ('XVID', '.avi'),  # Xvid
            ('MJPG', '.avi'),  # Motion JPEG
        ]
        
        for codec, ext in codecs:
            try:
                # 如果需要，修改输出路径扩展名
                if not output_path.endswith(ext):
                    output_path = str(Path(output_path).with_suffix(ext))
                
                fourcc = cv2.VideoWriter_fourcc(*codec)
                self.video_writer = cv2.VideoWriter(
                    output_path, fourcc, 20.0, frame_size
                )
                
                if self.video_writer.isOpened():
                    self.is_recording = True
                    self.recording_output_path = output_path  # 保存输出路径
                    self.log.emit(f"[录制] 开始录制，编解码器: {codec}, 分辨率: {frame_size}")
                    self.log.emit(f"[录制] 输出: {output_path}")
                    return
            except Exception as e:
                self.log.emit(f"[录制] 编解码器 {codec} 失败: {e}")
                continue
        
        # 所有编解码器都失败
        self.log.emit(f"[录制错误] 无法创建视频写入器，所有编解码器都失败")
        self.is_recording = False
    
    def stop_recording(self):
        """停止录制"""
        self.is_recording = False
        output_path = self.recording_output_path
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            self.log.emit(f"[录制] 视频已保存: {output_path}")
        self.recording_output_path = None
        return output_path


class VideoInterface(BaseDetectionInterface):
    """视频文件检测界面 - 包含离线检测和实时预览功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stream_thread = None  # 视频预览线程
        
        # 预览模式相关变量
        self.is_streaming = False
        self.current_frame = None
        self.current_result = None
        self.video_file_path = ""
        
        self.init_ui()
        self.load_person_model()
        self.log_device_info()
        
    def init_ui(self):
        """初始化界面"""
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧：控制面板（宽度比例：3）
        left_panel = self.create_control_panel()
        main_layout.addWidget(left_panel, 3)
        
        # 右侧：预览/信息面板（宽度比例：4）
        right_panel = self.create_combined_panel()
        main_layout.addWidget(right_panel, 4)
        
    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # 标题
        title = SubtitleLabel("视频文件检测", panel)
        layout.addWidget(title)
        
        # 创建滚动区域
        scroll_area = ScrollArea(panel)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        
        # 1. 模型加载卡片
        self.model_card = self.create_model_card()
        scroll_layout.addWidget(self.model_card)
        
        # 2. 视频源选择卡片
        self.source_card = self.create_source_card()
        scroll_layout.addWidget(self.source_card)
        
        # 3. 参数配置卡片
        self.param_card = self.create_param_card()
        scroll_layout.addWidget(self.param_card)
        
        # 4. 执行控制卡片
        self.control_card = self.create_control_card()
        scroll_layout.addWidget(self.control_card)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
        
        return panel
    
    def create_combined_panel(self):
        """创建合并面板 - 包含预览和信息（带滚动条）"""
        panel = QWidget(self)
        main_layout = QVBoxLayout(panel)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建滚动区域
        scroll_area = ScrollArea(panel)
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        layout = QVBoxLayout(scroll_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 视频预览区域
        preview_label = SubtitleLabel("视频预览", scroll_widget)
        layout.addWidget(preview_label)
        
        # 视频显示标签（更大的显示区域）
        self.video_label = QLabel(scroll_widget)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet(
            "QLabel { background-color: #000; border: 2px solid #ccc; }"
        )
        self.video_label.setMinimumSize(640, 360)
        self.video_label.setMaximumSize(960, 540)
        self.video_label.setText("等待视频...")
        layout.addWidget(self.video_label)
        
        # 预览控制按钮
        preview_control_card = CardWidget(scroll_widget)
        preview_control_layout = QHBoxLayout(preview_control_card)
        
        self.start_preview_btn = PrimaryPushButton(FluentIcon.PLAY, "启动预览", preview_control_card)
        self.start_preview_btn.clicked.connect(self.start_preview)
        self.start_preview_btn.setEnabled(False)
        preview_control_layout.addWidget(self.start_preview_btn)
        
        self.pause_preview_btn = PushButton(FluentIcon.PAUSE, "暂停", preview_control_card)
        self.pause_preview_btn.clicked.connect(self.toggle_pause_preview)
        self.pause_preview_btn.setEnabled(False)
        preview_control_layout.addWidget(self.pause_preview_btn)
        
        self.stop_preview_btn = PushButton(FluentIcon.CLOSE, "停止", preview_control_card)
        self.stop_preview_btn.clicked.connect(self.stop_preview)
        self.stop_preview_btn.setEnabled(False)
        preview_control_layout.addWidget(self.stop_preview_btn)
        
        # 录制按钮
        self.record_btn = PushButton(FluentIcon.SAVE, "录制", preview_control_card)
        self.record_btn.clicked.connect(self.toggle_recording)
        self.record_btn.setEnabled(False)
        preview_control_layout.addWidget(self.record_btn)
        
        self.recording_indicator = ProgressRing(preview_control_card)
        self.recording_indicator.setVisible(False)
        preview_control_layout.addWidget(self.recording_indicator)
        
        # 截图按钮
        self.screenshot_btn = PushButton(FluentIcon.CAMERA, "截图", preview_control_card)
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        self.screenshot_btn.setEnabled(False)
        preview_control_layout.addWidget(self.screenshot_btn)
        
        preview_control_layout.addStretch()
        layout.addWidget(preview_control_card)
        
        # FPS 显示
        self.fps_label = BodyLabel("FPS: 0", scroll_widget)
        layout.addWidget(self.fps_label)
        
        # 视频信息卡片
        info_card = CardWidget(scroll_widget)
        info_layout = QVBoxLayout(info_card)
        
        self.video_info_label = BodyLabel("未选择视频", info_card)
        self.video_info_label.setWordWrap(True)
        info_layout.addWidget(self.video_info_label)
        
        layout.addWidget(info_card)
        
        # 添加输出日志区域
        log_label = SubtitleLabel("输出日志", scroll_widget)
        layout.addWidget(log_label)
        
        # 创建日志输出文本框
        self.log_output = TextEdit(scroll_widget)
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("日志输出将显示在这里...")
        self.log_output.setStyleSheet("""
            TextEdit {
                background-color: #ffffff;
                color: #333333;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self.log_output.setMinimumHeight(100)
        self.log_output.setMaximumHeight(200)
        layout.addWidget(self.log_output)
        
        # 添加清空日志按钮
        clear_log_btn = PushButton(FluentIcon.DELETE, "清空日志", scroll_widget)
        clear_log_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_log_btn)
        
        # 添加底部间距
        layout.addStretch()
        
        # 设置滚动区域
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        return panel
    
    # append_log, clear_log, create_model_card 已从基类继承
    
    def create_source_card(self):
        """创建数据源选择卡片"""
        card = CardWidget(self)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # 标题
        title = BodyLabel("2. 视频文件选择", card)
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 路径显示
        self.source_path_label = BodyLabel("未选择视频文件", card)
        self.source_path_label.setWordWrap(True)
        layout.addWidget(self.source_path_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.select_video_btn = PrimaryPushButton(FluentIcon.VIDEO, "选择视频", card)
        self.select_video_btn.clicked.connect(self.select_video)
        btn_layout.addWidget(self.select_video_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return card
    
    # create_param_card, create_control_card 已从基类继承
    # load_model, load_default_model, _load_model_from_path 已从基类继承
    
    def select_video(self):
        """选择视频"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择视频", str(DATASET_DIR),
            "视频文件 (*.mp4 *.avi *.mov *.mkv)"
        )
        if file_path:
            self.source_path = file_path
            self.source_path_label.setText(f"视频: {get_filename(file_path)}")
            
            # 获取视频信息
            self.update_video_info(file_path)
            
            self.append_log(f"[视频] 已选择视频文件: {get_filename(file_path)}")
            self.check_ready_state()
    
    def update_video_info(self, video_path):
        """更新视频信息显示"""
        try:
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                duration = frame_count / fps if fps > 0 else 0
                
                info_text = (
                    f"文件名: {get_filename(video_path)}\n"
                    f"分辨率: {width}×{height}\n"
                    f"帧率: {fps:.2f} FPS\n"
                    f"总帧数: {frame_count}\n"
                    f"时长: {duration:.2f} 秒"
                )
                
                self.video_info_label.setText(info_text)
                cap.release()
                
                self.append_log(f"[视频信息] 分辨率={width}×{height}, 帧率={fps:.2f}, 总帧数={frame_count}")
            else:
                self.video_info_label.setText("无法读取视频信息")
                self.append_log("[错误] 无法打开视频文件")
        except Exception as e:
            self.video_info_label.setText(f"读取视频信息失败: {e}")
            self.append_log(f"[错误] 读取视频信息失败: {e}")
    
    def check_ready_state(self):
        """检查是否准备就绪"""
        if self.model is not None and self.source_path:
            self.predict_btn.setEnabled(True)
            self.start_preview_btn.setEnabled(True)  # 同时启用预览按钮
            self.status_label.setText("就绪 - 可以开始检测或预览")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.predict_btn.setEnabled(False)
            self.start_preview_btn.setEnabled(False)
    
    def start_predict(self):
        """开始预测"""
        if self.predict_thread and self.predict_thread.isRunning():
            InfoBar.warning(
                title="警告",
                content="检测任务正在进行中...",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        # 解析图像尺寸 - 使用统一的解析函数
        size_text = self.img_size_combo.currentText()
        w, h = parse_image_size(size_text)
        
        # 使用时间戳作为输出名称，确保每次都是新的预测
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_name = f"predict_{timestamp}"
        
        # 获取参数
        params = {
            'imgsz': (w, h),
            'device': self.device_combo.currentText(),
            'conf': self.conf_threshold_spinbox.value(),  # 置信度阈值
            'mask_threshold': [
                self.mask_threshold_low.value(),
                self.mask_threshold_high.value()
            ],
            'show_boxes': self.show_boxes_check.isChecked(),
            'show_labels': self.show_labels_check.isChecked(),
            'show_conf': self.show_conf_check.isChecked(),
            'enable_person_detection': self.person_detect_check.isChecked(),  # 行人检测
            'save': True,  # 默认总是保存结果
            'project': DEFAULT_PARAMS['project'],
            'name': output_name
        }
        
        # 创建并启动预测线程
        self.predict_thread = PredictThread(
            self.model, 
            self.source_path, 
            params,
            person_model=self.person_model if self.person_detect_check.isChecked() else None
        )
        self.predict_thread.progress.connect(self.update_progress)
        self.predict_thread.progress_percent.connect(self.update_progress_percent)  # 连接进度百分比
        self.predict_thread.finished.connect(self.on_predict_finished)
        self.predict_thread.log.connect(self.append_log)
        
        # 更新 UI 状态
        self.predict_btn.setEnabled(False)
        self.progress_ring.setVisible(True)
        self.progress_ring.setValue(0)  # 重置进度为0
        self.status_label.setText("正在检测中...")
        self.status_label.setStyleSheet("color: orange;")
        
        # 清空之前的日志
        self.clear_log()
        self.append_log("=" * 50)
        self.append_log("开始新的视频检测任务")
        self.append_log("=" * 50)
        
        # 记录开始时间
        self.predict_start_time = time.time()
        self.current_params = params
        
        self.predict_thread.start()
    
    def update_progress(self, message):
        """更新进度"""
        self.status_label.setText(message)
    
    def update_progress_percent(self, percent):
        """更新进度百分比"""
        self.progress_ring.setValue(percent)
    
    def on_predict_finished(self, success, message):
        """预测完成回调"""
        self.progress_ring.setVisible(False)
        self.predict_btn.setEnabled(True)
        
        # 计算推理时间
        inference_time = time.time() - self.predict_start_time if self.predict_start_time > 0 else 0
        
        # 获取检测数量
        num_detections = 0
        if success:
            num_detections = self.count_detections_from_labels(message)
        
        # 使用基类方法保存历史记录
        self.save_prediction_history(success, message, inference_time, num_detections)
        
        if success:
            self.status_label.setText(f"检测完成！检测到 {num_detections} 个目标")
            self.status_label.setStyleSheet("color: green;")
            self.open_result_btn.setEnabled(True)
            self.result_path = message
            
            InfoBar.success(
                title="成功",
                content=f"视频检测完成！耗时: {inference_time:.2f}s，检测到 {num_detections} 个目标",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            self.status_label.setText(f"检测失败")
            self.status_label.setStyleSheet("color: red;")
            
            InfoBar.error(
                title="错误",
                content=f"检测失败: {message}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    # open_result_folder, count_detections_from_labels 已从基类继承
    # load_person_model, log_device_info, set_model 已从基类继承
    
    def set_video_file(self, file_path):
        """设置视频文件（供外部调用）"""
        self.source_path = file_path
        self.video_file_path = file_path  # 同时设置预览用的路径
        self.source_path_label.setText(f"视频: {get_filename(file_path)}")
        self.update_video_info(file_path)
        self.append_log(f"[自动设置] 视频文件: {file_path}")
        self.check_ready_state()
    
    # ==================== 视频预览相关方法 ====================
    
    def start_preview(self):
        """启动视频预览"""
        if not self.model:
            InfoBar.warning(
                title="警告",
                content="请先加载模型",
                position=InfoBarPosition.TOP,
                parent=self
            )
            return
        
        # 确定视频源（使用source_path）
        if not self.source_path:
            InfoBar.warning(
                title="警告",
                content="请先选择视频文件",
                position=InfoBarPosition.TOP,
                parent=self
            )
            return
        
        source = self.source_path
        
        # 解析图像尺寸
        size_text = self.img_size_combo.currentText()
        w, h = parse_image_size(size_text)
        
        # 参数
        params = {
            'imgsz': (w, h),
            'device': self.device_combo.currentText(),
            'conf': self.conf_threshold_spinbox.value(),  # 置信度阈值
            'mask_threshold': [
                self.mask_threshold_low.value(),
                self.mask_threshold_high.value()
            ],
            'show_boxes': self.show_boxes_check.isChecked(),
            'show_labels': self.show_labels_check.isChecked(),
            'show_conf': self.show_conf_check.isChecked(),
        }
        
        # 创建线程（传递person_model以支持双模型检测）
        self.stream_thread = StreamThread(
            self.model, 
            source, 
            params, 
            person_model=self.person_model if self.person_detect_check.isChecked() else None
        )
        self.stream_thread.frame_ready.connect(self.update_preview_frame)
        self.stream_thread.error.connect(self.on_preview_error)
        self.stream_thread.log.connect(self.append_log)
        
        # 更新UI
        self.start_preview_btn.setEnabled(False)
        self.pause_preview_btn.setEnabled(True)
        self.stop_preview_btn.setEnabled(True)
        self.record_btn.setEnabled(True)
        self.screenshot_btn.setEnabled(True)
        self.status_label.setText("状态: 预览中")
        
        self.stream_thread.start()
        self.is_streaming = True
        self.append_log("[预览] 视频预览已启动")
    
    def stop_preview(self):
        """停止视频预览"""
        if self.stream_thread:
            self.stream_thread.stop()
            self.stream_thread = None
        
        self.start_preview_btn.setEnabled(True)
        self.pause_preview_btn.setEnabled(False)
        self.pause_preview_btn.setText("暂停")
        self.pause_preview_btn.setIcon(FluentIcon.PAUSE)
        self.stop_preview_btn.setEnabled(False)
        self.record_btn.setEnabled(False)
        self.screenshot_btn.setEnabled(False)
        self.status_label.setText("状态: 预览已停止")
        self.is_streaming = False
        
        if self.recording_indicator.isVisible():
            self.recording_indicator.setVisible(False)
        
        self.video_label.setText("等待视频...")
        self.fps_label.setText("FPS: 0")
        self.append_log("[预览] 视频预览已停止")
    
    def toggle_pause_preview(self):
        """切换暂停状态"""
        if not self.stream_thread:
            return
        
        if not self.stream_thread.is_paused:
            # 暂停
            self.stream_thread.pause()
            self.pause_preview_btn.setText("继续")
            self.pause_preview_btn.setIcon(FluentIcon.PLAY)
            self.status_label.setText("状态: 已暂停")
            
            # 暂停时禁用录制和截图
            self.record_btn.setEnabled(False)
            self.screenshot_btn.setEnabled(False)
            
            InfoBar.info(
                title="暂停",
                content="视频预览已暂停",
                position=InfoBarPosition.TOP,
                parent=self
            )
        else:
            # 继续
            self.stream_thread.resume()
            self.pause_preview_btn.setText("暂停")
            self.pause_preview_btn.setIcon(FluentIcon.PAUSE)
            self.status_label.setText("状态: 预览中")
            
            # 恢复时启用录制和截图
            self.record_btn.setEnabled(True)
            self.screenshot_btn.setEnabled(True)
            
            InfoBar.success(
                title="继续",
                content="视频预览已恢复",
                position=InfoBarPosition.TOP,
                parent=self
            )
    
    def toggle_recording(self):
        """切换录制状态"""
        if not self.stream_thread:
            return
        
        if not self.stream_thread.is_recording:
            # 检查是否有当前帧
            if not hasattr(self, 'current_frame') or self.current_frame is None:
                InfoBar.warning(
                    title="警告",
                    content="请等待视频预览启动后再开始录制",
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                return
            
            # 获取当前帧尺寸
            height, width = self.current_frame.shape[:2]
            frame_size = (width, height)
            
            # 开始录制
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"runs/stream_{timestamp}.mp4"
            self.stream_thread.start_recording(output_path, frame_size)
            self.record_btn.setText("停止录制")
            self.recording_indicator.setVisible(True)
            
            self.append_log(f"[录制] 开始录制到: {output_path}")
            InfoBar.success(
                title="录制",
                content="开始录制",
                position=InfoBarPosition.TOP,
                parent=self
            )
        else:
            # 停止录制
            saved_path = self.stream_thread.stop_recording()
            self.record_btn.setText("录制")
            self.recording_indicator.setVisible(False)
            
            self.append_log(f"[录制] 录制已停止并保存到: {saved_path}")
            InfoBar.success(
                title="录制完成",
                content=f"已保存到: {saved_path}",
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def take_screenshot(self):
        """截图"""
        if not hasattr(self, 'current_frame') or self.current_frame is None:
            return
        
        import os
        from pathlib import Path
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = Path(f"runs/screenshot_{timestamp}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存图片
        image_filename = "screenshot.jpg"
        image_path = output_dir / image_filename
        cv2.imwrite(str(image_path), self.current_frame)
        
        # 保存检测标签（YOLO格式）
        if self.current_result is not None and hasattr(self.current_result, 'boxes'):
            labels_dir = output_dir / "labels"
            labels_dir.mkdir(exist_ok=True)
            
            label_path = labels_dir / "screenshot.txt"
            
            try:
                with open(label_path, 'w') as f:
                    boxes = self.current_result.boxes
                    
                    if boxes is not None and len(boxes) > 0:
                        # 获取图像尺寸
                        img_height, img_width = self.current_frame.shape[:2]
                        
                        for box in boxes:
                            # 获取类别ID
                            cls_id = int(box.cls[0].item()) if hasattr(box, 'cls') else 0
                            
                            # 获取边界框坐标 (xyxy格式)
                            if hasattr(box, 'xyxy'):
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                
                                # 转换为YOLO格式 (归一化的中心点坐标和宽高)
                                x_center = ((x1 + x2) / 2) / img_width
                                y_center = ((y1 + y2) / 2) / img_height
                                width = (x2 - x1) / img_width
                                height = (y2 - y1) / img_height
                                
                                # 获取置信度
                                conf = box.conf[0].item() if hasattr(box, 'conf') else 0.0
                                
                                # 写入标签文件：class_id x_center y_center width height confidence
                                f.write(f"{cls_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f} {conf:.6f}\n")
                        
                        self.append_log(f"[截图] 保存了 {len(boxes)} 个检测标签")
                    else:
                        self.append_log(f"[截图] 当前帧无检测结果")
                        
            except Exception as e:
                self.append_log(f"[截图] 保存标签失败: {e}")
        else:
            self.append_log(f"[截图] 无检测结果可保存")
        
        InfoBar.success(
            title="截图成功",
            content=f"图片和标签已保存到: {output_dir}",
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )
    
    def update_preview_frame(self, orig_frame, processed_frame, fps, result):
        """更新预览帧显示"""
        self.current_frame = processed_frame
        self.current_result = result  # 保存检测结果用于截图
        
        # 更新FPS
        self.fps_label.setText(f"FPS: {fps:.1f}")
        
        # 转换为QImage
        height, width, channel = processed_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(
            processed_frame.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_RGB888
        ).rgbSwapped()
        
        # 显示
        pixmap = QPixmap.fromImage(q_image)
        scaled_pixmap = pixmap.scaled(
            self.video_label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
    
    def on_preview_error(self, message):
        """预览错误处理"""
        InfoBar.error(
            title="错误",
            content=message,
            position=InfoBarPosition.TOP,
            parent=self
        )
        self.stop_preview()

