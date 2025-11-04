"""
关于界面模块
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5.QtGui import QFont

from qfluentwidgets import (
    CardWidget, BodyLabel, TitleLabel, SubtitleLabel, CaptionLabel,
    IconWidget, FluentIcon, ScrollArea
)

from config import APP_NAME, APP_VERSION, APP_AUTHOR


class AboutInterface(QWidget):
    """关于界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建滚动区域
        scroll_area = ScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea{border: none; background: transparent;}")
        
        # 创建内容容器
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        content_layout.setSpacing(30)
        content_layout.setContentsMargins(80, 60, 80, 60)
        
        # 顶部Logo和标题区域
        self._create_header(content_layout)
        
        # 基本信息和描述
        self._create_info_section(content_layout)
        
        # 核心特性网格
        self._create_features_section(content_layout)
        
        # 技术栈
        self._create_tech_section(content_layout)
        
        content_layout.addStretch()
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def _create_header(self, parent_layout):
        """创建顶部标题区域"""
        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)
        header_layout.setAlignment(Qt.AlignCenter)
        
        # Logo图标
        icon = IconWidget(FluentIcon.ROBOT, self)
        icon.setFixedSize(72, 72)
        header_layout.addWidget(icon, 0, Qt.AlignCenter)
        
        # 应用名称
        title = TitleLabel(APP_NAME, self)
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        # 副标题
        subtitle = SubtitleLabel("多任务交通视觉感知系统", self)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray; font-size: 15px;")
        header_layout.addWidget(subtitle)
        
        # 版本号
        version = BodyLabel(f"Version {APP_VERSION}", self)
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #999; font-size: 13px; margin-top: 3px;")
        header_layout.addWidget(version)
        
        parent_layout.addLayout(header_layout)
    
    def _create_info_section(self, parent_layout):
        """创建信息区域"""
        card = CardWidget(self)
        card.setMaximumWidth(1400)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(25)
        card_layout.setContentsMargins(40, 35, 40, 35)
        
        # 系统描述
        desc = BodyLabel(
            "这是一个基于 Transformer 架构的先进多任务交通视觉感知系统。\n"
            "系统支持实时目标检测、车道线识别、可行驶区域分割等多种任务，\n"
            "提供图片、视频和批量文件处理功能，配备直观的可视化界面。",
            card
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 15px; line-height: 2.0; color: #555;")
        card_layout.addWidget(desc)
        
        # 分隔线
        separator = QWidget(card)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: rgba(128, 128, 128, 0.15);")
        card_layout.addWidget(separator)
        
        # 基本信息网格
        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(80)
        info_grid.setVerticalSpacing(20)
        
        info_items = [
            (FluentIcon.COMMAND_PROMPT, "框架", "Ultralytics YOLOv10"),
            (FluentIcon.PALETTE, "界面", "PyQt5 + Fluent"),
            (FluentIcon.PEOPLE, "开发者", APP_AUTHOR),
            (FluentIcon.DOCUMENT, "许可证", "AGPL-3.0")
        ]
        
        row, col = 0, 0
        for icon, label, value in info_items:
            item_layout = QVBoxLayout()
            item_layout.setSpacing(8)
            item_layout.setAlignment(Qt.AlignCenter)
            
            # 图标
            icon_widget = IconWidget(icon, card)
            icon_widget.setFixedSize(32, 32)
            item_layout.addWidget(icon_widget, 0, Qt.AlignCenter)
            
            # 标签
            label_widget = CaptionLabel(label, card)
            label_widget.setAlignment(Qt.AlignCenter)
            label_widget.setStyleSheet("color: gray; font-size: 13px;")
            item_layout.addWidget(label_widget)
            
            # 值
            value_widget = BodyLabel(value, card)
            value_widget.setAlignment(Qt.AlignCenter)
            value_widget.setStyleSheet("font-weight: bold; font-size: 14px;")
            item_layout.addWidget(value_widget)
            
            info_grid.addLayout(item_layout, row, col)
            col += 1
            if col >= 4:
                col = 0
                row += 1
        
        card_layout.addLayout(info_grid)
        parent_layout.addWidget(card, 0, Qt.AlignCenter)
    
    def _create_features_section(self, parent_layout):
        """创建功能特性区域"""
        # 标题
        title = SubtitleLabel("✨ 核心特性", self)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 19px; margin-bottom: 10px;")
        parent_layout.addWidget(title)
        
        # 特性网格容器
        grid_container = QWidget()
        grid_container.setMaximumWidth(1000)
        grid_layout = QGridLayout(grid_container)
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        features = [
            (FluentIcon.PHOTO, "多格式图片处理", "支持 JPG、PNG、BMP 等常见图片格式"),
            (FluentIcon.VIDEO, "视频实时分析", "支持多种视频格式的实时检测与分析"),
            (FluentIcon.FOLDER, "批量文件处理", "高效处理大量文件，自动保存结果"),
            (FluentIcon.CAMERA, "摄像头实时检测", "支持本地摄像头和网络摄像头实时监控"),
            (FluentIcon.HISTORY, "历史记录管理", "完整的检测历史记录和结果追溯"),
            (FluentIcon.SPEED_HIGH, "性能统计分析", "详细的性能指标和统计数据展示")
        ]
        
        row, col = 0, 0
        for icon, title, desc in features:
            feature_card = self._create_feature_card(icon, title, desc)
            grid_layout.addWidget(feature_card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        parent_layout.addWidget(grid_container, 0, Qt.AlignCenter)
    
    def _create_feature_card(self, icon, title, desc):
        """创建单个特性卡片"""
        card = CardWidget(self)
        card.setFixedSize(310, 140)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(25, 25, 25, 25)
        
        # 图标
        icon_widget = IconWidget(icon, card)
        icon_widget.setFixedSize(40, 40)
        card_layout.addWidget(icon_widget)
        
        # 标题
        title_label = SubtitleLabel(title, card)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        card_layout.addWidget(title_label)
        
        # 描述
        desc_label = CaptionLabel(desc, card)
        desc_label.setStyleSheet("color: gray; font-size: 13px;")
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)
        
        card_layout.addStretch()
        
        return card
    
    def _create_tech_section(self, parent_layout):
        """创建技术栈区域"""
        # 标题
        title = SubtitleLabel("🔧 技术栈", self)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 19px; margin-bottom: 10px;")
        parent_layout.addWidget(title)
        
        # 技术栈容器
        tech_container = QWidget()
        tech_container.setMaximumWidth(1000)
        tech_layout = QGridLayout(tech_container)
        tech_layout.setHorizontalSpacing(25)
        tech_layout.setVerticalSpacing(20)
        tech_layout.setContentsMargins(0, 0, 0, 0)
        
        technologies = [
            ("Python 3.8+", FluentIcon.CODE),
            ("PyTorch", FluentIcon.COMMAND_PROMPT),
            ("Ultralytics", FluentIcon.ROBOT),
            ("OpenCV", FluentIcon.CAMERA),
            ("PyQt5", FluentIcon.APPLICATION),
            ("SQLite", FluentIcon.SAVE)
        ]
        
        row, col = 0, 0
        for tech_name, icon in technologies:
            tech_badge = self._create_tech_badge(tech_name, icon)
            tech_layout.addWidget(tech_badge, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1
        
        parent_layout.addWidget(tech_container, 0, Qt.AlignCenter)
        
        # 版权信息
        copyright = CaptionLabel(f"© 2024 {APP_AUTHOR}. All rights reserved.", self)
        copyright.setAlignment(Qt.AlignCenter)
        copyright.setStyleSheet("color: #999; margin-top: 30px; font-size: 12px;")
        parent_layout.addWidget(copyright)
    
    def _create_tech_badge(self, text, icon):
        """创建技术徽章"""
        badge = CardWidget(self)
        badge.setFixedHeight(70)
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(30, 18, 30, 18)
        badge_layout.setSpacing(18)
        
        # 图标
        icon_widget = IconWidget(icon, badge)
        icon_widget.setFixedSize(32, 32)
        badge_layout.addWidget(icon_widget)
        
        # 文本
        label = BodyLabel(text, badge)
        label.setStyleSheet("font-weight: 600; font-size: 16px;")
        badge_layout.addWidget(label)
        
        badge_layout.addStretch()
        
        return badge
