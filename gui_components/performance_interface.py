"""
性能监控界面
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout

from qfluentwidgets import (
    CardWidget, BodyLabel, SubtitleLabel, ProgressBar, FluentIcon
)

try:
    import pyqtgraph as pg
    PYQTGRAPH_AVAILABLE = True
except:
    PYQTGRAPH_AVAILABLE = False

from utils.performance_monitor import PerformanceMonitor


class MetricCard(CardWidget):
    """指标卡片 - 美化版"""
    
    def __init__(self, title, icon, color_scheme=None, parent=None):
        super().__init__(parent)
        self.color_scheme = color_scheme or {
            'gradient': ['#667eea', '#764ba2'],
            'text': '#2c3e50',
            'bar_low': '#43e97b',
            'bar_mid': '#f5af19',
            'bar_high': '#e74c3c'
        }
        self.init_ui(title, icon)
    
    def init_ui(self, title, icon):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 美化卡片样式
        self.setStyleSheet(f"""
            MetricCard {{
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }}
        """)
        self.setFixedHeight(170)  # 固定高度，确保内容完整显示
        
        # 标题
        header_layout = QHBoxLayout()
        title_label = SubtitleLabel(title, self)
        title_label.setStyleSheet(f"""
            font-weight: 600;
            font-size: 14px;
            color: {self.color_scheme['text']};
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # 数值显示
        self.value_label = SubtitleLabel("0%", self)
        self.value_label.setStyleSheet(f"""
            color: {self.color_scheme['gradient'][0]};
            font-size: 28px;
            font-weight: bold;
        """)
        layout.addWidget(self.value_label)
        
        # 进度条
        self.progress_bar = ProgressBar(self)
        self.progress_bar.setMinimumHeight(8)
        layout.addWidget(self.progress_bar)
        
        # 详细信息
        self.detail_label = BodyLabel("", self)
        self.detail_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 11px;
            margin-top: 5px;
        """)
        layout.addWidget(self.detail_label)
    
    def update_value(self, value, detail=""):
        """更新值"""
        self.value_label.setText(f"{value:.1f}%")
        self.progress_bar.setValue(int(value))
        
        # 根据使用率动态改变颜色
        if value < 50:
            color = self.color_scheme['bar_low']
        elif value < 80:
            color = self.color_scheme['bar_mid']
        else:
            color = self.color_scheme['bar_high']
        
        self.value_label.setStyleSheet(f"""
            color: {color};
            font-size: 28px;
            font-weight: bold;
        """)
        
        if detail:
            self.detail_label.setText(detail)


class PerformanceInterface(QWidget):
    """性能监控界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.monitor = PerformanceMonitor(interval=1000)
        self.monitor.data_updated.connect(self.update_metrics)
        
        self.init_ui()
        self.monitor.start()
    
    def init_ui(self):
        """初始化界面"""
        from PyQt5.QtWidgets import QScrollArea
        
        # 创建滚动区域
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        
        # 创建内容容器
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 将滚动区域添加到主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll_area)
        
        # 标题
        title = SubtitleLabel("性能监控", content_widget)
        layout.addWidget(title)
        
        # 指标卡片网格 - 使用不同的配色方案
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(15)
        
        # CPU卡片
        self.cpu_card = MetricCard(
            "CPU 使用率", None, 
            color_scheme={
                'gradient': ['#667eea', '#764ba2'],
                'text': '#2c3e50',
                'bar_low': '#43e97b',
                'bar_mid': '#f5af19',
                'bar_high': '#e74c3c'
            },
            parent=content_widget
        )
        metrics_layout.addWidget(self.cpu_card, 0, 0)
        
        # 内存卡片
        self.memory_card = MetricCard(
            "内存使用率", None,
            color_scheme={
                'gradient': ['#4facfe', '#00f2fe'],
                'text': '#2c3e50',
                'bar_low': '#43e97b',
                'bar_mid': '#f5af19',
                'bar_high': '#e74c3c'
            },
            parent=content_widget
        )
        metrics_layout.addWidget(self.memory_card, 0, 1)
        
        # GPU卡片
        self.gpu_card = MetricCard(
            "GPU 使用率", None,
            color_scheme={
                'gradient': ['#fa709a', '#fee140'],
                'text': '#2c3e50',
                'bar_low': '#43e97b',
                'bar_mid': '#f5af19',
                'bar_high': '#e74c3c'
            },
            parent=content_widget
        )
        metrics_layout.addWidget(self.gpu_card, 1, 0)
        
        # GPU内存卡片
        self.gpu_memory_card = MetricCard(
            "GPU 内存", None,
            color_scheme={
                'gradient': ['#f093fb', '#f5576c'],
                'text': '#2c3e50',
                'bar_low': '#43e97b',
                'bar_mid': '#f5af19',
                'bar_high': '#e74c3c'
            },
            parent=content_widget
        )
        metrics_layout.addWidget(self.gpu_memory_card, 1, 1)
        
        layout.addLayout(metrics_layout)
        
        # GPU温度和功率 - 美化版
        gpu_info_card = CardWidget(content_widget)
        gpu_info_card.setStyleSheet("""
            CardWidget {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
                padding: 15px;
            }
        """)
        gpu_info_layout = QHBoxLayout(gpu_info_card)
        gpu_info_layout.setContentsMargins(20, 15, 20, 15)
        
        # 温度标签
        temp_container = QVBoxLayout()
        temp_title = BodyLabel("GPU 温度", gpu_info_card)
        temp_title.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: 500;")
        temp_container.addWidget(temp_title)
        
        self.gpu_temp_label = SubtitleLabel("-- °C", gpu_info_card)
        self.gpu_temp_label.setStyleSheet("color: #e74c3c; font-size: 18px; font-weight: bold;")
        temp_container.addWidget(self.gpu_temp_label)
        gpu_info_layout.addLayout(temp_container)
        
        gpu_info_layout.addSpacing(40)
        
        # 功率标签
        power_container = QVBoxLayout()
        power_title = BodyLabel("GPU 功率", gpu_info_card)
        power_title.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: 500;")
        power_container.addWidget(power_title)
        
        self.gpu_power_label = SubtitleLabel("-- W", gpu_info_card)
        self.gpu_power_label.setStyleSheet("color: #f39c12; font-size: 18px; font-weight: bold;")
        power_container.addWidget(self.gpu_power_label)
        gpu_info_layout.addLayout(power_container)
        
        gpu_info_layout.addStretch()
        
        layout.addWidget(gpu_info_card)
        
        # 图表（如果可用）
        if PYQTGRAPH_AVAILABLE:
            self.create_charts(layout)
        
        # 系统信息 - 美化版
        system_card = CardWidget(content_widget)
        system_card.setStyleSheet("""
            CardWidget {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        system_layout = QVBoxLayout(system_card)
        system_layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = SubtitleLabel("系统 I/O 信息", system_card)
        title_label.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        system_layout.addWidget(title_label)
        
        self.system_info_label = BodyLabel("", system_card)
        self.system_info_label.setWordWrap(True)
        self.system_info_label.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
            line-height: 1.6;
        """)
        system_layout.addWidget(self.system_info_label)
        
        layout.addWidget(system_card)
        layout.addStretch()
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
    
    def create_charts(self, parent_layout):
        """创建图表 - 美化版"""
        # 获取内容widget（从parent_layout）
        content_widget = parent_layout.parentWidget()
        chart_card = CardWidget(content_widget)
        chart_card.setStyleSheet("""
            CardWidget {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_label = SubtitleLabel("性能历史趋势", chart_card)
        title_label.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #2c3e50;
            margin-bottom: 10px;
        """)
        chart_layout.addWidget(title_label)
        
        # 创建图表
        pg.setConfigOption('background', '#f8f9fa')
        pg.setConfigOption('foreground', '#2c3e50')
        pg.setConfigOption('antialias', True)
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', '使用率 (%)', 
                                  color='#2c3e50', size='11pt', **{'font-weight': 'bold'})
        self.plot_widget.setLabel('bottom', '时间 (秒)', 
                                  color='#2c3e50', size='11pt', **{'font-weight': 'bold'})
        self.plot_widget.setYRange(0, 100)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setBackground('#f8f9fa')
        self.plot_widget.setMinimumHeight(350)  # 确保图表有足够高度
        
        # 美化曲线 - 使用更粗的线条和更鲜艳的颜色
        self.cpu_curve = self.plot_widget.plot(
            pen=pg.mkPen(color='#667eea', width=3), name='CPU',
            symbol='o', symbolSize=6, symbolBrush='#667eea'
        )
        self.memory_curve = self.plot_widget.plot(
            pen=pg.mkPen(color='#4facfe', width=3), name='Memory',
            symbol='s', symbolSize=6, symbolBrush='#4facfe'
        )
        self.gpu_curve = self.plot_widget.plot(
            pen=pg.mkPen(color='#fa709a', width=3), name='GPU',
            symbol='t', symbolSize=6, symbolBrush='#fa709a'
        )
        
        # 图例
        legend = self.plot_widget.addLegend(offset=(10, 10))
        legend.setLabelTextColor('#2c3e50')
        
        chart_layout.addWidget(self.plot_widget)
        parent_layout.addWidget(chart_card)
    
    def update_metrics(self, data):
        """更新指标"""
        # CPU
        cpu_percent = data.get('cpu_percent', 0)
        cpu_freq = data.get('cpu_freq', 0)
        self.cpu_card.update_value(
            cpu_percent,
            f"频率: {cpu_freq:.0f} MHz" if cpu_freq > 0 else ""
        )
        
        # 内存
        memory_percent = data.get('memory_percent', 0)
        memory_used = data.get('memory_used', 0)
        memory_total = data.get('memory_total', 0)
        self.memory_card.update_value(
            memory_percent,
            f"{memory_used:.1f} GB / {memory_total:.1f} GB"
        )
        
        # GPU
        if data.get('gpu_available', False):
            gpu_percent = data.get('gpu_percent', 0)
            self.gpu_card.update_value(gpu_percent)
            
            # GPU内存
            gpu_memory_percent = data.get('gpu_memory_percent', 0)
            gpu_memory_used = data.get('gpu_memory_used', 0)
            gpu_memory_total = data.get('gpu_memory_total', 0)
            self.gpu_memory_card.update_value(
                gpu_memory_percent,
                f"{gpu_memory_used:.1f} GB / {gpu_memory_total:.1f} GB"
            )
            
            # 温度和功率
            gpu_temp = data.get('gpu_temp', 0)
            gpu_power = data.get('gpu_power', 0)
            self.gpu_temp_label.setText(f"{gpu_temp}°C")
            self.gpu_power_label.setText(f"{gpu_power:.1f} W")
        else:
            self.gpu_card.update_value(0, "GPU不可用")
            self.gpu_memory_card.update_value(0, "GPU不可用")
            self.gpu_temp_label.setText("N/A")
            self.gpu_power_label.setText("N/A")
        
        # 更新图表
        if PYQTGRAPH_AVAILABLE and hasattr(self, 'cpu_curve'):
            cpu_history = data.get('cpu_history', [])
            memory_history = data.get('memory_history', [])
            gpu_history = data.get('gpu_history', [])
            
            self.cpu_curve.setData(cpu_history)
            self.memory_curve.setData(memory_history)
            if gpu_history:
                self.gpu_curve.setData(gpu_history)
        
        # 系统信息
        disk_read = data.get('disk_read', 0)
        disk_write = data.get('disk_write', 0)
        net_sent = data.get('net_sent', 0)
        net_recv = data.get('net_recv', 0)
        
        info_text = (
            f"💾 磁盘 I/O: 读取 {disk_read:.0f} MB  |  写入 {disk_write:.0f} MB\n"
            f"🌐 网络流量: 发送 {net_sent:.0f} MB  |  接收 {net_recv:.0f} MB"
        )
        self.system_info_label.setText(info_text)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.monitor.stop()
        event.accept()
