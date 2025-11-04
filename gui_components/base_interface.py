"""
基础界面类和混入类
提取公共功能，减少代码重复
"""

import os
import time
from pathlib import Path
from typing import Optional
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog

from qfluentwidgets import (
    FluentIcon, PushButton, PrimaryPushButton, BodyLabel, SubtitleLabel,
    CardWidget, ProgressRing, InfoBar, InfoBarPosition, ComboBox, CheckBox, TextEdit
)

from ultralytics import MTDETR, YOLO
from config import (
    MODEL_DIR, DATASET_DIR, DEFAULT_MODEL_PATH, YOLOV10_MODEL_PATH,
    DEFAULT_PARAMS, DEVICE_OPTIONS, IMAGE_SIZE_PRESETS, DEFAULT_DEVICE
)
from utils import HistoryDB, UIComponentFactory, get_filename, parse_image_size, get_source_type


class LogMixin:
    """日志功能混入类"""
    
    def append_log(self, message):
        """添加日志消息"""
        if not hasattr(self, 'log_output'):
            return
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_output.append(f"[{timestamp}] {message}")
        # 自动滚动到底部
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )
    
    def clear_log(self):
        """清空日志"""
        if hasattr(self, 'log_output'):
            self.log_output.clear()
    
    def log_device_info(self):
        """记录设备信息到日志"""
        import torch
        self.append_log("=" * 50)
        self.append_log("系统设备信息")
        self.append_log("=" * 50)
        self.append_log(f"可用设备: {DEVICE_OPTIONS}")
        self.append_log(f"当前选择: {DEFAULT_DEVICE}")
        
        try:
            self.append_log(f"PyTorch 版本: {torch.__version__}")
            cuda_available = torch.cuda.is_available()
            self.append_log(f"CUDA 可用: {cuda_available}")
            
            if cuda_available:
                gpu_count = torch.cuda.device_count()
                self.append_log(f"GPU 数量: {gpu_count}")
                for i in range(gpu_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    self.append_log(f"  GPU {i}: {gpu_name}")
            else:
                self.append_log("⚠️  未检测到 CUDA 设备，将使用 CPU 模式")
        except Exception as e:
            self.append_log(f"[警告] 获取设备信息失败: {e}")
        
        self.append_log("=" * 50)


class ModelLoaderMixin:
    """模型加载功能混入类"""
    
    def load_model(self):
        """加载模型"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择模型文件", str(MODEL_DIR), "模型文件 (*.pt *.pth)"
        )
        
        if file_path:
            self._load_model_from_path(file_path)
    
    def load_default_model(self):
        """加载默认模型"""
        if DEFAULT_MODEL_PATH.exists():
            self._load_model_from_path(str(DEFAULT_MODEL_PATH))
        else:
            InfoBar.warning(
                title="警告",
                content=f"默认模型不存在: {DEFAULT_MODEL_PATH}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def _load_model_from_path(self, file_path):
        """从路径加载模型"""
        try:
            # 加载 MTDETR 模型
            self.model = MTDETR(file_path)
            
            # 打印模型信息
            self.append_log(f"[模型加载] 模型类型: {type(self.model)}")
            if hasattr(self.model, 'names'):
                self.append_log(f"[模型加载] 类别数量: {len(self.model.names)}")
                self.append_log(f"[模型加载] 类别名称: {self.model.names}")
            
            self.current_model_path = file_path
            self.model_path_label.setText(f"模型: {get_filename(file_path)}")
            self.model_status.setText("状态: 已加载 ✓")
            self.model_status.setStyleSheet("color: green; font-weight: bold;")
            self.check_ready_state()
            
            InfoBar.success(
                title="成功",
                content="模型加载成功！",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
        except Exception as e:
            self.model_status.setText(f"状态: 加载失败 ✗")
            self.model_status.setStyleSheet("color: red;")
            InfoBar.error(
                title="错误",
                content=f"模型加载失败: {str(e)}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
    
    def load_person_model(self):
        """加载 YOLOv10n 检测模型"""
        try:
            if YOLOV10_MODEL_PATH.exists():
                self.append_log(f"[YOLOv10n] 加载检测模型: {YOLOV10_MODEL_PATH}")
                self.person_model = YOLO(str(YOLOV10_MODEL_PATH))
                self.append_log("[YOLOv10n] 模型加载成功")
            else:
                self.append_log(f"[YOLOv10n] 未找到模型文件: {YOLOV10_MODEL_PATH}")
                self.person_model = None
        except Exception as e:
            self.append_log(f"[YOLOv10n] 加载模型失败: {e}")
            self.person_model = None
    
    def set_model(self, model, person_model=None):
        """设置模型（供外部调用）"""
        self.model = model
        if person_model:
            self.person_model = person_model
        
        # 更新UI显示
        if model and hasattr(model, 'ckpt_path'):
            self.current_model_path = str(model.ckpt_path)
            self.model_path_label.setText(f"模型: {get_filename(self.current_model_path)}")
            self.model_status.setText("状态: 已加载 ✓")
            self.model_status.setStyleSheet("color: green; font-weight: bold;")
            self.check_ready_state()


class UICardMixin:
    """UI卡片创建混入类"""
    
    def create_model_card(self):
        """创建模型加载卡片"""
        card = CardWidget(self)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # 标题
        title = BodyLabel("1. 模型加载", card)
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 模型路径显示
        self.model_path_label = BodyLabel("未加载模型", card)
        self.model_path_label.setWordWrap(True)
        layout.addWidget(self.model_path_label)
        
        # 按钮
        btn_layout = QHBoxLayout()
        self.load_model_btn = PrimaryPushButton(FluentIcon.FOLDER, "选择模型", card)
        self.load_model_btn.clicked.connect(self.load_model)
        btn_layout.addWidget(self.load_model_btn)
        
        self.load_default_btn = PushButton(FluentIcon.SYNC, "加载默认", card)
        self.load_default_btn.clicked.connect(self.load_default_model)
        btn_layout.addWidget(self.load_default_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # 模型状态
        self.model_status = BodyLabel("状态: 未加载", card)
        self.model_status.setStyleSheet("color: gray;")
        layout.addWidget(self.model_status)
        
        return card
    
    def create_param_card(self):
        """创建参数配置卡片"""
        card = CardWidget(self)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # 标题
        title = BodyLabel("3. 参数配置", card)
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 图像尺寸预设
        size_layout, self.img_size_combo = UIComponentFactory.create_labeled_combobox(
            "图像尺寸", [f"{w}×{h}" for w, h in IMAGE_SIZE_PRESETS], card
        )
        self.img_size_combo.setCurrentText("640×640")
        layout.addLayout(size_layout)
        
        # 置信度阈值
        from qfluentwidgets import DoubleSpinBox
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(BodyLabel("置信度阈值:", card))
        self.conf_threshold_spinbox = DoubleSpinBox(card)
        self.conf_threshold_spinbox.setRange(0.0, 1.0)
        self.conf_threshold_spinbox.setValue(0.5)
        self.conf_threshold_spinbox.setSingleStep(0.05)
        self.conf_threshold_spinbox.setDecimals(2)
        self.conf_threshold_spinbox.setToolTip("设置检测置信度阈值，只显示置信度高于此值的检测结果")
        conf_layout.addWidget(self.conf_threshold_spinbox)
        conf_layout.addStretch()
        layout.addLayout(conf_layout)
        
        # 掩码阈值
        threshold_layout, self.mask_threshold_low, self.mask_threshold_high = \
            UIComponentFactory.create_threshold_spinboxes("掩码阈值", 0.35, 0.95, card)
        layout.addLayout(threshold_layout)
        
        # 设备选择
        device_layout, self.device_combo = UIComponentFactory.create_labeled_combobox(
            "计算设备", DEVICE_OPTIONS, card
        )
        if DEFAULT_DEVICE in DEVICE_OPTIONS:
            self.device_combo.setCurrentText(DEFAULT_DEVICE)
        layout.addLayout(device_layout)
        
        # 显示选项
        display_label = BodyLabel("显示选项:", card)
        layout.addWidget(display_label)
        
        display_options = UIComponentFactory.create_display_options(card)
        self.show_boxes_check = display_options['boxes']
        self.show_labels_check = display_options['labels']
        self.show_conf_check = display_options['conf']
        layout.addLayout(display_options['layout'])
        
        # 行人检测选项
        person_detect_label = BodyLabel("额外检测:", card)
        layout.addWidget(person_detect_label)
        
        person_layout = QHBoxLayout()
        self.person_detect_check = CheckBox("启用 YOLOv10n 辅助检测（行人+红绿灯）", card)
        self.person_detect_check.setChecked(False)
        self.person_detect_check.setToolTip("使用 YOLOv10n 额外检测:\n• 行人 - 绿色框\n• 红绿灯 - 橙色框")
        person_layout.addWidget(self.person_detect_check)
        person_layout.addStretch()
        layout.addLayout(person_layout)
        
        return card
    
    def create_control_card(self):
        """创建执行控制卡片"""
        card = CardWidget(self)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # 标题
        title = BodyLabel("4. 执行控制", card)
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 按钮和进度
        control_layout = QHBoxLayout()
        self.predict_btn = PrimaryPushButton(FluentIcon.PLAY, "开始检测", card)
        self.predict_btn.clicked.connect(self.start_predict)
        self.predict_btn.setEnabled(False)
        control_layout.addWidget(self.predict_btn)
        
        self.open_result_btn = PushButton(FluentIcon.FOLDER, "打开结果", card)
        self.open_result_btn.clicked.connect(self.open_result_folder)
        self.open_result_btn.setEnabled(False)
        control_layout.addWidget(self.open_result_btn)
        
        control_layout.addStretch()
        
        # 进度环 - 缩小尺寸并支持进度显示
        self.progress_ring = ProgressRing(card)
        self.progress_ring.setFixedSize(32, 32)  # 设置固定大小（缩小）
        self.progress_ring.setStrokeWidth(3)  # 设置线条宽度
        self.progress_ring.setVisible(False)
        control_layout.addWidget(self.progress_ring)
        
        layout.addLayout(control_layout)
        
        # 状态显示
        self.status_label = BodyLabel("就绪", card)
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)
        
        return card


class PredictMixin:
    """预测功能混入类"""
    
    def count_detections_from_labels(self, result_dir):
        """从标签文件中统计检测数量"""
        try:
            labels_dir = Path(result_dir) / 'labels'
            
            if not labels_dir.exists():
                self.append_log(f"[检测统计] 标签目录不存在: {labels_dir}")
                return 0
            
            total_detections = 0
            label_files = list(labels_dir.glob('*.txt'))
            
            self.append_log(f"[检测统计] 找到 {len(label_files)} 个标签文件")
            
            for label_file in label_files:
                try:
                    with open(label_file, 'r') as f:
                        lines = f.readlines()
                        valid_lines = [line.strip() for line in lines if line.strip()]
                        total_detections += len(valid_lines)
                except Exception as e:
                    self.append_log(f"[检测统计] 读取标签文件失败 {label_file}: {e}")
                    continue
            
            self.append_log(f"[检测统计] 总检测数: {total_detections}")
            return total_detections
            
        except Exception as e:
            self.append_log(f"[检测统计] 统计失败: {e}")
            return 0
    
    def save_prediction_history(self, success, message, inference_time, num_detections):
        """保存预测历史记录"""
        source_type = get_source_type(self.source_path)
        
        record_data = {
            'timestamp': datetime.now().isoformat(),
            'model_path': self.current_model_path,
            'source_path': self.source_path,
            'source_type': source_type,
            'result_path': message if success else '',
            'parameters': self.current_params if hasattr(self, 'current_params') else {},
            'success': success,
            'error_message': message if not success else '',
            'inference_time': inference_time,
            'num_detections': num_detections
        }
        
        try:
            self.db.add_record(record_data)
        except Exception as e:
            self.append_log(f"[警告] 保存历史记录失败: {e}")
    
    def open_result_folder(self):
        """打开结果文件夹"""
        if hasattr(self, 'result_path') and os.path.exists(self.result_path):
            os.startfile(self.result_path)


class BaseDetectionInterface(QWidget, LogMixin, ModelLoaderMixin, UICardMixin, PredictMixin):
    """
    基础检测界面类
    整合所有混入类，提供通用功能
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model: Optional[MTDETR] = None
        self.person_model: Optional[YOLO] = None
        self.predict_thread = None
        self.source_path = ""
        self.result_path = ""
        self.current_model_path = ""
        self.db = HistoryDB()
        self.predict_start_time = 0
    
    def check_ready_state(self):
        """检查是否准备就绪（子类需要实现）"""
        pass
    
    def start_predict(self):
        """开始预测（子类需要实现）"""
        pass
