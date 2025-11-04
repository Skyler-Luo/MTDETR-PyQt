"""
UI组件工厂模块
"""

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout
from qfluentwidgets import CardWidget, BodyLabel, ComboBox, CheckBox, DoubleSpinBox


class UIComponentFactory:
    """UI组件工厂类"""
    
    @staticmethod
    def create_card_with_title(title, parent=None):
        """
        创建带标题的卡片
        
        Args:
            title: 标题文本
            parent: 父组件
            
        Returns:
            card, layout: 卡片和布局
        """
        card = CardWidget(parent)
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # 标题
        title_label = BodyLabel(title, card)
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)
        
        return card, layout
    
    @staticmethod
    def create_labeled_combobox(label_text, items, parent=None):
        """
        创建带标签的下拉框
        
        Args:
            label_text: 标签文本
            items: 选项列表
            parent: 父组件
            
        Returns:
            layout, combobox: 布局和下拉框
        """
        layout = QHBoxLayout()
        layout.addWidget(BodyLabel(f"{label_text}:", parent))
        
        combobox = ComboBox(parent)
        combobox.addItems(items)
        layout.addWidget(combobox)
        layout.addStretch()
        
        return layout, combobox
    
    @staticmethod
    def create_display_options(parent=None):
        """
        创建标准显示选项复选框组
        
        Returns:
            dict: {'layout': QHBoxLayout, 'boxes': checkbox, 'labels': checkbox, 'conf': checkbox}
        """
        layout = QHBoxLayout()
        
        boxes_check = CheckBox("显示框", parent)
        boxes_check.setChecked(True)
        layout.addWidget(boxes_check)
        
        labels_check = CheckBox("显示标签", parent)
        labels_check.setChecked(True)
        layout.addWidget(labels_check)
        
        conf_check = CheckBox("显示置信度", parent)
        conf_check.setChecked(True)
        layout.addWidget(conf_check)
        layout.addStretch()
        
        return {
            'layout': layout,
            'boxes': boxes_check,
            'labels': labels_check,
            'conf': conf_check
        }
    
    @staticmethod
    def create_threshold_spinboxes(label_text, default_low=0.45, default_high=0.9, parent=None):
        """
        创建阈值范围输入框
        
        Args:
            label_text: 标签文本
            default_low: 低阈值默认值
            default_high: 高阈值默认值
            parent: 父组件
            
        Returns:
            layout, spinbox_low, spinbox_high
        """
        layout = QHBoxLayout()
        layout.addWidget(BodyLabel(f"{label_text}:", parent))
        
        spinbox_low = DoubleSpinBox(parent)
        spinbox_low.setRange(0.0, 1.0)
        spinbox_low.setValue(default_low)
        spinbox_low.setSingleStep(0.05)
        layout.addWidget(spinbox_low)
        
        layout.addWidget(BodyLabel("-", parent))
        
        spinbox_high = DoubleSpinBox(parent)
        spinbox_high.setRange(0.0, 1.0)
        spinbox_high.setValue(default_high)
        spinbox_high.setSingleStep(0.05)
        layout.addWidget(spinbox_high)
        layout.addStretch()
        
        return layout, spinbox_low, spinbox_high
