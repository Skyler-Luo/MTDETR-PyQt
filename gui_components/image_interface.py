"""
图片检测界面模块 - 专门用于图片和图片文件夹的检测
"""

import os
import time
from pathlib import Path
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QStackedWidget

from qfluentwidgets import (
    FluentIcon, PushButton, PrimaryPushButton, BodyLabel, SubtitleLabel,
    CardWidget, ScrollArea, InfoBar, InfoBarPosition, Pivot, TextEdit
)

from config import DATASET_DIR, DEFAULT_PARAMS
from .predict_thread import PredictThread
from .image_preview import ImagePreviewCard
from .base_interface import BaseDetectionInterface
from utils import get_filename, parse_image_size


class ImageInterface(BaseDetectionInterface):
    """图片检测界面 - 专门处理单张图片和图片文件夹"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        # 右侧：预览面板（宽度比例：4）
        right_panel = self.create_preview_panel()
        main_layout.addWidget(right_panel, 4)
        
    def create_control_panel(self):
        """创建控制面板"""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # 标题
        title = SubtitleLabel("图片检测", panel)
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
        
        # 2. 数据源选择卡片
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
    
    def create_preview_panel(self):
        """创建预览面板"""
        panel = QWidget(self)
        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        
        # 标题
        title = SubtitleLabel("预览窗口", panel)
        layout.addWidget(title)
        
        # 创建 Pivot 切换
        self.pivot = Pivot(panel)
        self.pivot.addItem(
            routeKey='input',
            text='输入图像',
            onClick=lambda: self.switch_preview('input')
        )
        self.pivot.addItem(
            routeKey='output',
            text='输出结果',
            onClick=lambda: self.switch_preview('output')
        )
        layout.addWidget(self.pivot)
        
        # 使用 QStackedWidget 管理预览卡片
        self.preview_stack = QStackedWidget(panel)
        
        # 输入预览
        self.input_preview = ImagePreviewCard(panel)
        self.preview_stack.addWidget(self.input_preview)
        
        # 输出预览
        self.output_preview = ImagePreviewCard(panel)
        self.preview_stack.addWidget(self.output_preview)
        
        layout.addWidget(self.preview_stack, 3)
        
        # 添加输出日志区域
        log_label = SubtitleLabel("输出日志", panel)
        layout.addWidget(log_label)
        
        # 创建日志输出文本框
        self.log_output = TextEdit(panel)
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("日志输出将显示在这里...")
        self.log_output.setMaximumHeight(200)
        self.log_output.setStyleSheet("""
            TextEdit {
                background-color: #ffffff;
                color: #333333;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.log_output, 1)
        
        # 添加清空日志按钮
        clear_log_btn = PushButton(FluentIcon.DELETE, "清空日志", panel)
        clear_log_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_log_btn)
        
        return panel
    
    def switch_preview(self, mode):
        """切换预览模式"""
        if mode == 'input':
            self.preview_stack.setCurrentWidget(self.input_preview)
        else:
            self.preview_stack.setCurrentWidget(self.output_preview)
    
    # 日志和模型卡片方法已从基类继承
    
    def create_source_card(self):
        """创建数据源选择卡片"""
        card = CardWidget(self)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # 标题
        title = BodyLabel("2. 数据源选择", card)
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title)
        
        # 路径显示
        self.source_path_label = BodyLabel("未选择数据源", card)
        self.source_path_label.setWordWrap(True)
        layout.addWidget(self.source_path_label)
        
        # 按钮组 - 只保留图片和文件夹
        btn_layout = QHBoxLayout()
        self.select_image_btn = PushButton(FluentIcon.PHOTO, "单张图片", card)
        self.select_image_btn.clicked.connect(self.select_image)
        btn_layout.addWidget(self.select_image_btn)
        
        self.select_folder_btn = PushButton(FluentIcon.FOLDER, "图片文件夹", card)
        self.select_folder_btn.clicked.connect(self.select_folder)
        btn_layout.addWidget(self.select_folder_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return card
    
    # 参数卡片和控制卡片方法已从基类继承
    # load_model, load_default_model, _load_model_from_path 已从基类继承
    
    def select_image(self):
        """选择图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", str(DATASET_DIR), 
            "图片文件 (*.jpg *.jpeg *.png *.bmp)"
        )
        if file_path:
            self.source_path = file_path
            self.source_path_label.setText(f"数据源: {get_filename(file_path)} (单张图片)")
            self.input_preview.set_image(file_path)
            self.append_log(f"[图片] 已选择图片: {get_filename(file_path)}")
            self.check_ready_state()
    
    def select_folder(self):
        """选择文件夹"""
        folder_path = QFileDialog.getExistingDirectory(
            self, "选择图片文件夹", str(DATASET_DIR)
        )
        if folder_path:
            self.source_path = folder_path
            
            # 查找文件夹中的图片数量
            from pathlib import Path
            folder = Path(folder_path)
            image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp']
            image_files = []
            for ext in image_extensions:
                image_files.extend(folder.glob(ext))
            
            # 更新数据源标签，显示图片数量
            if image_files:
                self.source_path_label.setText(
                    f"数据源: {get_filename(folder_path)} ({len(image_files)} 张图片)"
                )
                # 预览第一张图片
                self.input_preview.set_image(str(image_files[0]))
                self.append_log(f"[文件夹] 找到 {len(image_files)} 张图片，预览第一张")
            else:
                self.source_path_label.setText(f"数据源: {get_filename(folder_path)} (无图片)")
                self.input_preview.clear()
                self.append_log(f"[警告] 文件夹中未找到图片文件")
            
            self.check_ready_state()
    
    def check_ready_state(self):
        """检查是否准备就绪"""
        if self.model is not None and self.source_path:
            self.predict_btn.setEnabled(True)
            self.status_label.setText("就绪 - 可以开始检测")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.predict_btn.setEnabled(False)
    
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
        self.append_log("开始新的检测任务")
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
            
            # 加载第一张结果图片
            self.load_result_preview(message)
            
            InfoBar.success(
                title="成功",
                content=f"检测完成！耗时: {inference_time:.2f}s，检测到 {num_detections} 个目标",
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
    
    def load_result_preview(self, result_dir):
        """加载结果预览"""
        try:
            # 查找第一张结果图片
            for ext in ['*.jpg', '*.jpeg', '*.png']:
                result_files = list(Path(result_dir).glob(ext))
                if result_files:
                    self.output_preview.set_image(str(result_files[0]))
                    # 切换到输出预览
                    self.pivot.setCurrentItem('output')
                    self.switch_preview('output')
                    break
        except Exception as e:
            self.append_log(f"[警告] 加载结果预览失败: {e}")
    
    # open_result_folder, count_detections_from_labels 已从基类继承
    # load_person_model, log_device_info, set_model 已从基类继承

