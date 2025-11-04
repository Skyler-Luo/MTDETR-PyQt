"""
图像预览卡片模块
"""

import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QVBoxLayout, QLabel

from qfluentwidgets import CardWidget, BodyLabel


class ImagePreviewCard(CardWidget):
    """图像预览卡片"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title = BodyLabel("预览", self)
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # 图像显示
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet(
            "QLabel { background-color: #f0f0f0; border: 2px dashed #ccc; border-radius: 8px; }"
        )
        self.image_label.setMinimumSize(400, 300)
        self.image_label.setText("暂无预览")
        layout.addWidget(self.image_label)
        
    def set_image(self, image_path):
        """设置预览图像"""
        if not os.path.exists(image_path):
            return
            
        try:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                # 缩放图像以适应标签
                scaled_pixmap = pixmap.scaled(
                    self.image_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_label.setPixmap(scaled_pixmap)
        except Exception as e:
            # 静默处理预览加载失败
            pass
    
    def clear(self):
        """清除预览"""
        self.image_label.clear()
        self.image_label.setText("暂无预览")
