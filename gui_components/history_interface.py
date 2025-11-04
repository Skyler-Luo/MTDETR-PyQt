"""
历史记录管理界面
"""

import os
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)

from qfluentwidgets import (
    CardWidget, BodyLabel, SubtitleLabel, PushButton, TitleLabel,
    LineEdit, FluentIcon, InfoBar, InfoBarPosition, MessageBox, TextEdit
)

from utils import HistoryDB, format_timestamp, format_duration, get_filename


class HistoryInterface(QWidget):
    """历史记录界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = HistoryDB()
        self.init_ui()
        self.load_records()
    
    def _create_stat_card(self, title, value, color1, color2):
        """创建统计卡片"""
        card = CardWidget(self)
        card.setFixedHeight(100)
        
        # 设置渐变背景
        card.setStyleSheet(f"""
            CardWidget {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color1},
                    stop:1 {color2}
                );
                border-radius: 10px;
                border: none;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)
        card_layout.setSpacing(5)
        
        # 标题
        title_label = BodyLabel(title, card)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 12px;
            font-weight: 500;
        """)
        card_layout.addWidget(title_label)
        
        # 数值
        value_label = TitleLabel(value, card)
        value_label.setStyleSheet("""
            color: white;
            font-size: 28px;
            font-weight: bold;
        """)
        card_layout.addWidget(value_label)
        
        # 保存值标签的引用以便更新
        card.value_label = value_label
        
        return card
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = SubtitleLabel("📋 预测历史", self)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        layout.addWidget(title)
        
        # 统计卡片组
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        # 总计卡片
        self.total_card = self._create_stat_card("总记录数", "0", "#667eea", "#764ba2")
        stats_layout.addWidget(self.total_card)
        
        # 成功卡片
        self.success_card = self._create_stat_card("成功", "0", "#43e97b", "#38f9d7")
        stats_layout.addWidget(self.success_card)
        
        # 失败卡片
        self.failed_card = self._create_stat_card("失败", "0", "#fa709a", "#fee140")
        stats_layout.addWidget(self.failed_card)
        
        # 平均耗时卡片
        self.avg_time_card = self._create_stat_card("平均耗时", "0s", "#4facfe", "#00f2fe")
        stats_layout.addWidget(self.avg_time_card)
        
        layout.addLayout(stats_layout)
        
        # 搜索和操作栏
        control_card = CardWidget(self)
        control_card.setStyleSheet("""
            CardWidget {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        control_layout = QHBoxLayout(control_card)
        control_layout.setContentsMargins(15, 10, 15, 10)
        
        # 搜索框（更大更显眼）
        self.search_box = LineEdit(control_card)
        self.search_box.setPlaceholderText("🔍 搜索记录（模型、数据源等）...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.search_records)
        self.search_box.setFixedHeight(36)
        control_layout.addWidget(self.search_box, 2)
        
        control_layout.addSpacing(10)
        
        # 操作按钮
        self.refresh_btn = PushButton(FluentIcon.SYNC, "刷新", control_card)
        self.refresh_btn.clicked.connect(self.load_records)
        self.refresh_btn.setFixedHeight(36)
        control_layout.addWidget(self.refresh_btn)
        
        self.open_btn = PushButton(FluentIcon.FOLDER, "打开结果", control_card)
        self.open_btn.clicked.connect(self.open_result)
        self.open_btn.setEnabled(False)
        self.open_btn.setFixedHeight(36)
        control_layout.addWidget(self.open_btn)
        
        self.delete_btn = PushButton(FluentIcon.DELETE, "删除", control_card)
        self.delete_btn.clicked.connect(self.delete_selected)
        self.delete_btn.setEnabled(False)
        self.delete_btn.setFixedHeight(36)
        control_layout.addWidget(self.delete_btn)
        
        self.clear_btn = PushButton(FluentIcon.CLOSE, "清空全部", control_card)
        self.clear_btn.clicked.connect(self.clear_all)
        self.clear_btn.setFixedHeight(36)
        control_layout.addWidget(self.clear_btn)
        
        layout.addWidget(control_card)
        
        # 历史记录表格
        table_card = CardWidget(self)
        table_card.setStyleSheet("""
            CardWidget {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(15, 15, 15, 15)
        
        # 表格标题
        table_title = BodyLabel("📊 检测记录", table_card)
        table_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 5px 0;")
        table_layout.addWidget(table_title)
        
        self.history_table = QTableWidget(table_card)
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "⏰ 时间", "🤖 模型", "📁 数据源", "📋 类型", "✓ 状态", 
            "🎯 检测数", "⏱️ 耗时"
        ])
        
        # 美化表格样式
        self.history_table.setStyleSheet("""
            QTableWidget {
                background-color: #fafafa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                gridline-color: #e8e8e8;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QTableWidget::item:hover {
                background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                color: #495057;
            }
        """)
        
        # 设置列宽
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        # 设置选择模式
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.history_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.history_table.cellDoubleClicked.connect(self.on_double_click)
        
        table_layout.addWidget(self.history_table)
        layout.addWidget(table_card)
        
        # 详细信息卡片
        detail_card = CardWidget(self)
        detail_card.setStyleSheet("""
            CardWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e0f7fa,
                    stop:1 #f3e5f5
                );
                border-radius: 10px;
                border: 1px solid #e0e0e0;
            }
        """)
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(15, 15, 15, 15)
        
        detail_title = BodyLabel("📝 详细信息", detail_card)
        detail_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2c3e50; padding: 5px 0;")
        detail_layout.addWidget(detail_title)
        
        # 使用TextEdit代替BodyLabel，支持滚动
        self.detail_label = TextEdit(detail_card)
        self.detail_label.setReadOnly(True)
        self.detail_label.setPlaceholderText("💡 请选择一条记录查看详细信息...")
        self.detail_label.setMinimumHeight(150)
        self.detail_label.setMaximumHeight(180)
        self.detail_label.setStyleSheet("""
            TextEdit {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 8px;
                padding: 12px;
                font-size: 12px;
                line-height: 1.6;
                color: #2c3e50;
            }
        """)
        detail_layout.addWidget(self.detail_label)
        
        layout.addWidget(detail_card)
        layout.addStretch()
    
    def load_records(self):
        """加载记录"""
        records = self.db.get_all_records(limit=1000)
        self._populate_table(records)
    
    def update_statistics(self):
        """更新统计信息"""
        stats = self.db.get_statistics()
        
        # 使用统一的时长格式化函数
        avg_time_str = format_duration(stats['avg_inference_time'])
        
        # 更新统计卡片
        self.total_card.value_label.setText(str(stats['total']))
        self.success_card.value_label.setText(str(stats['success']))
        self.failed_card.value_label.setText(str(stats['failed']))
        self.avg_time_card.value_label.setText(avg_time_str)
    
    def search_records(self, keyword):
        """搜索记录"""
        if not keyword:
            self.load_records()
            return
        
        records = self.db.search_records(keyword)
        self._populate_table(records)
    
    def _populate_table(self, records):
        """
        填充表格
        
        Args:
            records: 记录列表
        """
        self.history_table.setRowCount(0)
        
        for record in records:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            # ID
            self.history_table.setItem(row, 0, QTableWidgetItem(str(record['id'])))
            
            # 时间
            time_str = format_timestamp(record['timestamp'])
            self.history_table.setItem(row, 1, QTableWidgetItem(time_str))
            
            # 模型
            model_name = get_filename(record['model_path'])
            self.history_table.setItem(row, 2, QTableWidgetItem(model_name))
            
            # 数据源
            source_name = get_filename(record['source_path'])
            self.history_table.setItem(row, 3, QTableWidgetItem(source_name))
            
            # 类型
            self.history_table.setItem(row, 4, QTableWidgetItem(record['source_type']))
            
            # 状态（带颜色）
            status_item = QTableWidgetItem("✓ 成功" if record['success'] else "✗ 失败")
            if record['success']:
                status_item.setForeground(Qt.darkGreen)
            else:
                status_item.setForeground(Qt.red)
            self.history_table.setItem(row, 5, status_item)
            
            # 检测数
            self.history_table.setItem(row, 6, QTableWidgetItem(str(record['num_detections'])))
            
            # 耗时
            time_str = format_duration(record['inference_time'])
            self.history_table.setItem(row, 7, QTableWidgetItem(time_str))
        
        # 更新统计
        self.update_statistics()
    
    def on_selection_changed(self):
        """选择变化"""
        selected_rows = self.history_table.selectedItems()
        
        if selected_rows:
            self.open_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
            
            # 显示详细信息
            row = selected_rows[0].row()
            record_id = int(self.history_table.item(row, 0).text())
            
            record = self.db.get_record(record_id)
            if record:
                details = []
                details.append(f"ID: {record['id']}")
                details.append(f"时间: {record['timestamp']}")
                details.append(f"模型: {record['model_path']}")
                details.append(f"数据源: {record['source_path']}")
                details.append(f"结果路径: {record['result_path']}")
                details.append(f"状态: {'成功' if record['success'] else '失败'}")
                
                if not record['success'] and record['error_message']:
                    details.append(f"错误: {record['error_message']}")
                
                if record['parameters']:
                    params = record['parameters']
                    details.append(f"\n参数:")
                    for key, value in params.items():
                        details.append(f"  {key}: {value}")
                
                self.detail_label.setPlainText("\n".join(details))
        else:
            self.open_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.detail_label.setPlainText("请选择一条记录查看详情")
    
    def on_double_click(self, row, col):
        """双击打开结果"""
        self.open_result()
    
    def open_result(self):
        """打开结果文件夹"""
        selected_rows = self.history_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        record_id = int(self.history_table.item(row, 0).text())
        
        record = self.db.get_record(record_id)
        if record and record['result_path']:
            if os.path.exists(record['result_path']):
                os.startfile(record['result_path'])
            else:
                InfoBar.warning(
                    title="警告",
                    content="结果文件不存在",
                    position=InfoBarPosition.TOP,
                    parent=self
                )
    
    def delete_selected(self):
        """删除选中记录"""
        selected_rows = self.history_table.selectedItems()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        record_id = int(self.history_table.item(row, 0).text())
        
        # 确认对话框
        msg_box = MessageBox(
            "确认删除",
            "确定要删除这条记录吗？",
            self
        )
        
        if msg_box.exec():
            self.db.delete_record(record_id)
            self.load_records()
            
            InfoBar.success(
                title="成功",
                content="记录已删除",
                position=InfoBarPosition.TOP,
                parent=self
            )
    
    def clear_all(self):
        """清空所有记录"""
        # 确认对话框
        msg_box = MessageBox(
            "确认清空",
            "确定要清空所有历史记录吗？此操作不可恢复！",
            self
        )
        
        if msg_box.exec():
            self.db.clear_all()
            self.load_records()
            
            InfoBar.success(
                title="成功",
                content="所有记录已清空",
                position=InfoBarPosition.TOP,
                parent=self
            )
    
    def add_record(self, record_data):
        """添加记录（供外部调用）"""
        self.db.add_record(record_data)
        self.load_records()
