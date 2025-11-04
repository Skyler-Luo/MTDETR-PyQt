"""
结果统计分析界面
"""

from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFileDialog,
    QGraphicsOpacityEffect
)

from qfluentwidgets import (
    CardWidget, BodyLabel, SubtitleLabel, TitleLabel, PushButton,
    FluentIcon, InfoBar, InfoBarPosition, TextEdit
)

from utils import get_class_name


try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib import font_manager
    
    # 配置中文字体 - 尝试多种字体
    chinese_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong', 'STSong', 'Arial Unicode MS']
    font_found = False
    
    for font_name in chinese_fonts:
        try:
            # 检查字体是否可用
            available_fonts = [f.name for f in font_manager.fontManager.ttflist]
            if font_name in available_fonts:
                plt.rcParams['font.sans-serif'] = [font_name]
                font_found = True
                break
        except:
            continue
    
    if not font_found:
        # 如果没有找到中文字体，使用默认字体但不报错
        plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
    
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
    
    MATPLOTLIB_AVAILABLE = True
except:
    MATPLOTLIB_AVAILABLE = False


class StatCard(CardWidget):
    """统计卡片 - 美化版"""
    
    def __init__(self, title, value, icon=None, color_gradient=None, parent=None):
        super().__init__(parent)
        self.color_gradient = color_gradient or ["#667eea", "#764ba2"]
        self.init_ui(title, value, icon)
    
    def init_ui(self, title, value, icon):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加渐变背景样式
        gradient_style = f"""
            StatCard {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {self.color_gradient[0]},
                    stop:1 {self.color_gradient[1]}
                );
                border-radius: 12px;
                border: none;
            }}
        """
        self.setStyleSheet(gradient_style)
        
        # 标题
        title_label = BodyLabel(title, self)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(title_label)
        
        # 数值
        self.value_label = TitleLabel(str(value), self)
        self.value_label.setStyleSheet("""
            color: white;
            font-size: 32px;
            font-weight: bold;
        """)
        layout.addWidget(self.value_label)
        
        # 设置固定高度，避免内容被遮挡
        self.setFixedHeight(140)
    
    def update_value(self, value):
        """更新值 - 带动画效果"""
        self.value_label.setText(str(value))
        
        # 添加淡入动画效果
        if not hasattr(self, 'opacity_effect'):
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.value_label.setGraphicsEffect(self.opacity_effect)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0.3)
        self.animation.setEndValue(1.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.start()


class ChartWidget(CardWidget):
    """图表控件 - 美化版"""
    
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.init_ui(title)
    
    def init_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 美化卡片样式
        self.setStyleSheet("""
            ChartWidget {
                background-color: white;
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # 标题
        title_label = SubtitleLabel(title, self)
        title_label.setStyleSheet("""
            font-weight: 600;
            font-size: 15px;
            color: #2c3e50;
            padding-bottom: 5px;
        """)
        layout.addWidget(title_label)
        
        if MATPLOTLIB_AVAILABLE:
            # 创建画布 - 稍微缩小尺寸，优化显示
            self.figure = Figure(figsize=(5.8, 3.8), dpi=100, facecolor='white')
            self.canvas = FigureCanvas(self.figure)
            self.canvas.setStyleSheet("background-color: white;")
            self.canvas.setMinimumHeight(350)  # 调整最小高度
            layout.addWidget(self.canvas)
            
            self.ax = self.figure.add_subplot(111)
            # 设置图表样式
            self.ax.set_facecolor('#f8f9fa')
            # 不在初始化时调用 tight_layout，等绘制数据后再调用
            # self.figure.tight_layout(pad=1.2)
        else:
            no_chart_label = BodyLabel("未安装 matplotlib", self)
            no_chart_label.setStyleSheet("color: #e74c3c; padding: 20px;")
            layout.addWidget(no_chart_label)


class AnalyticsInterface(QWidget):
    """统计分析界面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results_data = None
        self.init_ui()
    
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
        
        # 标题和控制
        header_layout = QHBoxLayout()
        
        title = SubtitleLabel("结果分析", content_widget)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self.load_btn = PushButton(FluentIcon.FOLDER, "加载结果", content_widget)
        self.load_btn.clicked.connect(self.load_results)
        header_layout.addWidget(self.load_btn)
        
        self.export_btn = PushButton(FluentIcon.SAVE, "导出报告", content_widget)
        self.export_btn.clicked.connect(self.export_report)
        self.export_btn.setEnabled(False)
        header_layout.addWidget(self.export_btn)
        
        layout.addLayout(header_layout)
        
        # 统计卡片 - 使用不同的渐变配色
        stats_layout = QGridLayout()
        stats_layout.setSpacing(15)
        
        self.total_detections_card = StatCard(
            "总检测数", "0", None, 
            color_gradient=["#667eea", "#764ba2"],
            parent=content_widget
        )
        stats_layout.addWidget(self.total_detections_card, 0, 0)
        
        self.avg_confidence_card = StatCard(
            "平均置信度", "0%", None,
            color_gradient=["#f093fb", "#f5576c"],
            parent=content_widget
        )
        stats_layout.addWidget(self.avg_confidence_card, 0, 1)
        
        self.num_classes_card = StatCard(
            "类别数量", "0", None,
            color_gradient=["#4facfe", "#00f2fe"],
            parent=content_widget
        )
        stats_layout.addWidget(self.num_classes_card, 0, 2)
        
        self.num_images_card = StatCard(
            "图片数量", "0", None,
            color_gradient=["#43e97b", "#38f9d7"],
            parent=content_widget
        )
        stats_layout.addWidget(self.num_images_card, 0, 3)
        
        layout.addLayout(stats_layout)
        
        # 添加统计摘要信息卡片
        self.summary_card = CardWidget(content_widget)
        self.summary_card.setStyleSheet("""
            CardWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e0f7fa,
                    stop:1 #f3e5f5
                );
                border-radius: 12px;
                border: 1px solid #e0e0e0;
            }
        """)
        summary_layout = QHBoxLayout(self.summary_card)
        summary_layout.setContentsMargins(20, 15, 20, 15)
        
        self.summary_label = BodyLabel("📊 等待加载数据...", self.summary_card)
        self.summary_label.setStyleSheet("""
            color: #2c3e50;
            font-size: 12px;
            font-weight: 500;
        """)
        summary_layout.addWidget(self.summary_label)
        
        layout.addWidget(self.summary_card)
        
        # 图表区域
        if MATPLOTLIB_AVAILABLE:
            charts_layout = QGridLayout()
            charts_layout.setSpacing(12)
            
            # 类别分布饼图
            self.class_pie_chart = ChartWidget("类别分布", content_widget)
            charts_layout.addWidget(self.class_pie_chart, 0, 0)
            
            # 置信度分布直方图
            self.conf_hist_chart = ChartWidget("置信度分布", content_widget)
            charts_layout.addWidget(self.conf_hist_chart, 0, 1)
            
            # 每张图片检测数柱状图
            self.detections_bar_chart = ChartWidget("每张图片检测数", content_widget)
            charts_layout.addWidget(self.detections_bar_chart, 1, 0, 1, 2)
            
            layout.addLayout(charts_layout)
        
        # 添加日志输出区域
        log_label = SubtitleLabel("分析日志", content_widget)
        layout.addWidget(log_label)
        
        self.log_output = TextEdit(content_widget)
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("分析日志将显示在这里...")
        self.log_output.setMaximumHeight(150)
        self.log_output.setStyleSheet("""
            TextEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout.addWidget(self.log_output)
        
        layout.addStretch()
        
        # 设置滚动区域的内容
        scroll_area.setWidget(content_widget)
    
    def load_results(self):
        """加载结果"""
        result_dir = QFileDialog.getExistingDirectory(
            self, "选择结果文件夹", "runs"
        )
        
        if result_dir:
            # 清空日志
            self.clear_log()
            self.append_log("=" * 50)
            self.append_log(f"开始分析结果: {result_dir}")
            self.append_log("=" * 50)
            self.analyze_results(result_dir)
    
    def analyze_results(self, result_dir):
        """分析结果"""
        try:
            # 查找结果图片
            result_path = Path(result_dir)
            image_files = list(result_path.glob('*.jpg')) + list(result_path.glob('*.png'))
            
            if not image_files:
                InfoBar.warning(
                    title="警告",
                    content="未找到结果图片",
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                return
            
            # 读取标签文件（YOLO格式）
            labels_dir = result_path / "labels"
            
            total_detections = 0
            class_counts = {}
            confidences = []
            detections_per_image = []
            
            if labels_dir.exists():
                # 从标签文件读取真实数据
                self.append_log(f"[分析] 找到标签文件夹: {labels_dir}")
                for img_file in image_files:
                    label_file = labels_dir / (img_file.stem + '.txt')
                    
                    if label_file.exists():
                        try:
                            with open(label_file, 'r') as f:
                                lines = f.readlines()
                                image_detections = 0
                                
                                for line in lines:
                                    parts = line.strip().split()
                                    # 标准YOLO格式: class_id x_center y_center width height [confidence]
                                    if len(parts) >= 5:
                                        try:
                                            class_id = int(parts[0])
                                            image_detections += 1
                                            
                                            # 使用统一的类别名称获取函数
                                            class_name = get_class_name(class_id)
                                            class_counts[class_name] = class_counts.get(class_name, 0) + 1
                                            
                                            # 尝试读取置信度
                                            if len(parts) >= 6:
                                                try:
                                                    conf = float(parts[5])
                                                    # 置信度范围检查
                                                    if 0.0 <= conf <= 1.0:
                                                        confidences.append(conf)
                                                except (ValueError, IndexError):
                                                    pass
                                        except (ValueError, IndexError) as e:
                                            self.append_log(f"[分析] 解析标签行失败: {line.strip()}, 错误: {e}")
                                            continue
                                
                                detections_per_image.append(image_detections)
                                total_detections += image_detections
                                
                        except Exception as e:
                            self.append_log(f"[分析] 读取标签文件失败 {label_file}: {e}")
                            detections_per_image.append(0)
                    else:
                        self.append_log(f"[分析] 标签文件不存在: {label_file}")
                        detections_per_image.append(0)
            else:
                # 如果没有标签文件，尝试从历史记录读取
                self.append_log(f"[分析] 未找到标签文件夹: {labels_dir}")
                InfoBar.warning(
                    title="警告",
                    content="未找到标签文件夹，无法进行详细分析",
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                
                # 使用默认值
                total_detections = 0
                class_counts = {}
                confidences = []
                detections_per_image = [0] * len(image_files)
            
            # 打印统计摘要
            self.append_log(f"[分析结果] 总检测数: {total_detections}")
            self.append_log(f"[分析结果] 类别统计: {class_counts}")
            self.append_log(f"[分析结果] 置信度数量: {len(confidences)}")
            self.append_log(f"[分析结果] 图片数量: {len(image_files)}")
            
            # 如果没有置信度数据，使用空列表（不显示默认值）
            # 修复：之前使用[0.85]会导致置信度显示不准确
            if not confidences and total_detections > 0:
                # 如果有检测但没有置信度，说明标签文件没有保存置信度
                self.append_log("[分析] 警告: 标签文件中未包含置信度信息")
            
            # 更新统计卡片 - 带动画效果
            from PyQt5.QtCore import QTimer
            
            # 延迟更新以创建连续动画效果
            QTimer.singleShot(0, lambda: self.total_detections_card.update_value(total_detections))
            
            # 计算平均置信度
            if confidences:
                avg_conf = sum(confidences) / len(confidences)
                QTimer.singleShot(100, lambda: self.avg_confidence_card.update_value(f"{avg_conf*100:.1f}%"))
            else:
                QTimer.singleShot(100, lambda: self.avg_confidence_card.update_value("N/A"))
            
            QTimer.singleShot(200, lambda: self.num_classes_card.update_value(len(class_counts) if class_counts else 0))
            QTimer.singleShot(300, lambda: self.num_images_card.update_value(len(image_files)))
            
            # 更新摘要信息
            self.update_summary(total_detections, class_counts, confidences, len(image_files))
            
            # 绘制图表
            if MATPLOTLIB_AVAILABLE:
                try:
                    # 类别分布图 - 只在有类别数据时绘制
                    if class_counts:
                        self.plot_class_distribution(class_counts)
                        self.append_log(f"[分析] ✓ 绘制类别分布图")
                    else:
                        self.append_log(f"[分析] ✗ 无类别数据，跳过类别分布图")
                except Exception as e:
                    self.append_log(f"[错误] 绘制类别分布图失败: {str(e)}")
                
                try:
                    # 置信度分布图 - 只在有置信度数据时绘制
                    if confidences and len(confidences) > 1:
                        self.plot_confidence_histogram(confidences)
                        self.append_log(f"[分析] ✓ 绘制置信度分布图")
                    else:
                        self.append_log(f"[分析] ✗ 置信度数据不足，跳过置信度分布图")
                except Exception as e:
                    self.append_log(f"[错误] 绘制置信度分布图失败: {str(e)}")
                
                try:
                    # 每张图片检测数图 - 只在有检测数据时绘制
                    if detections_per_image and sum(detections_per_image) > 0:
                        self.plot_detections_per_image(detections_per_image)
                        self.append_log(f"[分析] ✓ 绘制检测数分布图")
                    else:
                        self.append_log(f"[分析] ✗ 无检测数据，跳过检测数分布图")
                except Exception as e:
                    self.append_log(f"[错误] 绘制检测数分布图失败: {str(e)}")
            
            # 启用导出功能
            self.export_btn.setEnabled(True)
            
            # 保存数据用于导出
            avg_confidence_value = (sum(confidences) / len(confidences) * 100) if confidences else 0
            self.current_analysis = {
                'total_detections': total_detections,
                'avg_confidence': avg_confidence_value,
                'num_classes': len(class_counts),
                'num_images': len(image_files),
                'class_counts': class_counts,
                'result_dir': result_dir
            }
            
            InfoBar.success(
                title="成功",
                content=f"已分析 {len(image_files)} 张图片，检测到 {total_detections} 个目标",
                position=InfoBarPosition.TOP,
                parent=self
            )
            
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            self.append_log(f"[错误] {error_msg}")
            InfoBar.error(
                title="错误",
                content=f"分析失败: {str(e)}",
                position=InfoBarPosition.TOP,
                parent=self
            )
    
    def update_summary(self, total_detections, class_counts, confidences, num_images):
        """更新统计摘要信息"""
        try:
            # 计算平均每张图片的检测数
            avg_per_image = total_detections / num_images if num_images > 0 else 0
            
            # 找出最常见的类别
            most_common_class = ""
            if class_counts:
                most_common_class = max(class_counts.items(), key=lambda x: x[1])[0]
            
            # 置信度统计
            conf_info = ""
            if confidences:
                min_conf = min(confidences)
                max_conf = max(confidences)
                conf_info = f"置信度范围: {min_conf:.2f} ~ {max_conf:.2f}"
            else:
                conf_info = "置信度: N/A"
            
            # 构建摘要文本
            summary_text = (
                f"📊 检测摘要: 平均每张图片检测 {avg_per_image:.1f} 个目标  |  "
                f"🏆 最常见类别: {most_common_class}  |  {conf_info}"
            )
            
            self.summary_label.setText(summary_text)
        except Exception as e:
            self.summary_label.setText(f"📊 统计摘要生成失败: {str(e)}")
    
    def plot_class_distribution(self, class_counts):
        """绘制类别分布饼图 - 美化版"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        self.class_pie_chart.ax.clear()
        
        labels = list(class_counts.keys())
        sizes = list(class_counts.values())
        
        # 使用更现代的配色方案
        colors = ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a', 
                  '#fee140', '#30cfd0', '#a8edea', '#ff9a9e', '#fbc2eb']
        colors = colors[:len(labels)]
        
        # 自定义百分比显示函数 - 只在占比大于5%的扇区显示百分比
        def autopct_format(pct):
            return f'{pct:.1f}%' if pct > 5 else ''
        
        # 绘制饼图 - 不显示标签，百分比显示在内部
        wedges, texts, autotexts = self.class_pie_chart.ax.pie(
            sizes, 
            labels=None,  # 不在饼图上显示标签
            colors=colors,
            autopct=autopct_format,
            startangle=90,
            pctdistance=0.75,  # 将百分比显示在饼图内部
            explode=[0.03] * len(labels),  # 轻微分离效果
            shadow=True,
            textprops={'fontsize': 9, 'weight': 'bold'}
        )
        
        # 美化百分比文字 - 设置为白色以便在彩色背景上显示
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(9)
            autotext.set_weight('bold')
        
        # 添加图例到旁边，显示类别名称和数量
        legend_labels = [f'{label} ({count})' for label, count in zip(labels, sizes)]
        self.class_pie_chart.ax.legend(
            wedges, 
            legend_labels,
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            fontsize=9,
            frameon=True,
            fancybox=True,
            shadow=True
        )
        
        self.class_pie_chart.ax.axis('equal')
        self.class_pie_chart.figure.tight_layout(pad=1.0)
        self.class_pie_chart.canvas.draw()
        self.class_pie_chart.canvas.flush_events()  # 强制刷新
    
    def plot_confidence_histogram(self, confidences):
        """绘制置信度分布直方图 - 美化版"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        self.conf_hist_chart.ax.clear()
        
        # 绘制渐变色直方图
        n, bins, patches = self.conf_hist_chart.ax.hist(
            confidences, 
            bins=20, 
            edgecolor='white',
            alpha=0.85,
            linewidth=1.2
        )
        
        # 为每个柱子设置渐变色
        import matplotlib.cm as cm
        colors = cm.viridis(bins[:-1] / bins[-1])
        for patch, color in zip(patches, colors):
            patch.set_facecolor(color)
        
        # 设置标签和标题 - 使用英文避免字体问题
        self.conf_hist_chart.ax.set_xlabel('Confidence', fontsize=10, weight='bold', color='#2c3e50')
        self.conf_hist_chart.ax.set_ylabel('Count', fontsize=10, weight='bold', color='#2c3e50')
        self.conf_hist_chart.ax.set_xlim(0, 1)
        
        # 美化网格
        self.conf_hist_chart.ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.8)
        self.conf_hist_chart.ax.set_axisbelow(True)
        
        # 设置刻度样式
        self.conf_hist_chart.ax.tick_params(colors='#2c3e50', labelsize=8)
        
        # 添加均值线
        mean_conf = sum(confidences) / len(confidences)
        self.conf_hist_chart.ax.axvline(
            mean_conf, 
            color='#e74c3c', 
            linestyle='--', 
            linewidth=2.0, 
            label=f'Mean: {mean_conf:.2f}',
            alpha=0.8
        )
        self.conf_hist_chart.ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
        
        self.conf_hist_chart.figure.tight_layout(pad=1.0)
        self.conf_hist_chart.canvas.draw()
        self.conf_hist_chart.canvas.flush_events()  # 强制刷新
    
    def plot_detections_per_image(self, detections):
        """绘制每张图片检测数柱状图 - 美化版"""
        if not MATPLOTLIB_AVAILABLE:
            return
        
        self.detections_bar_chart.ax.clear()
        
        # 只显示前20张图片
        display_count = min(len(detections), 20)
        x = range(display_count)
        y = detections[:display_count]
        
        # 创建渐变色柱状图
        import matplotlib.cm as cm
        import numpy as np
        colors = cm.plasma(np.linspace(0.2, 0.8, display_count))
        
        bars = self.detections_bar_chart.ax.bar(
            x, y, 
            color=colors,
            edgecolor='white',
            alpha=0.85,
            linewidth=1.2
        )
        
        # 在柱子顶部添加数值标签
        for i, (bar, value) in enumerate(zip(bars, y)):
            if value > 0:
                height = bar.get_height()
                self.detections_bar_chart.ax.text(
                    bar.get_x() + bar.get_width()/2., height,
                    f'{int(value)}',
                    ha='center', va='bottom',
                    fontsize=7, weight='bold', color='#2c3e50'
                )
        
        # 设置标签 - 使用英文避免字体问题
        self.detections_bar_chart.ax.set_xlabel('Image Index', fontsize=10, weight='bold', color='#2c3e50')
        self.detections_bar_chart.ax.set_ylabel('Detection Count', fontsize=10, weight='bold', color='#2c3e50')
        
        # 美化网格
        self.detections_bar_chart.ax.grid(True, alpha=0.2, axis='y', linestyle='--', linewidth=0.8)
        self.detections_bar_chart.ax.set_axisbelow(True)
        
        # 设置刻度样式
        self.detections_bar_chart.ax.tick_params(colors='#2c3e50', labelsize=8)
        
        # 添加平均线
        if y:
            avg_detections = sum(y) / len(y)
            self.detections_bar_chart.ax.axhline(
                avg_detections, 
                color='#e74c3c', 
                linestyle='--', 
                linewidth=1.8, 
                label=f'Avg: {avg_detections:.1f}',
                alpha=0.7
            )
            self.detections_bar_chart.ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
        
        self.detections_bar_chart.figure.tight_layout(pad=1.0)
        self.detections_bar_chart.canvas.draw()
        self.detections_bar_chart.canvas.flush_events()  # 强制刷新
    
    def export_report(self):
        """导出报告"""
        if not hasattr(self, 'current_analysis'):
            InfoBar.warning(
                title="警告",
                content="请先加载并分析结果",
                position=InfoBarPosition.TOP,
                parent=self
            )
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存报告", "report.html", "HTML文件 (*.html)"
        )
        
        if file_path:
            try:
                data = self.current_analysis
                
                # 生成类别统计表格
                class_table = ""
                for cls, count in data.get('class_counts', {}).items():
                    percentage = (count / data['total_detections'] * 100) if data['total_detections'] > 0 else 0
                    class_table += f"""
                    <tr>
                        <td>{cls}</td>
                        <td>{count}</td>
                        <td>{percentage:.1f}%</td>
                    </tr>
                    """
                
                # 生成HTML报告
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>多任务交通感知系统检测结果报告</title>
                    <style>
                        body {{ 
                            font-family: 'Microsoft YaHei', Arial, sans-serif; 
                            margin: 20px; 
                            background: #f5f5f5;
                        }}
                        .container {{ 
                            max-width: 1200px; 
                            margin: 0 auto; 
                            background: white; 
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        }}
                        h1 {{ 
                            color: #2c3e50; 
                            border-bottom: 3px solid #3498db;
                            padding-bottom: 10px;
                        }}
                        .stats {{ 
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                            gap: 20px;
                            margin: 30px 0;
                        }}
                        .stat {{ 
                            padding: 20px; 
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            color: white;
                            border-radius: 10px;
                            text-align: center;
                        }}
                        .stat-label {{ 
                            font-size: 14px; 
                            opacity: 0.9;
                            margin-bottom: 10px;
                        }}
                        .stat-value {{ 
                            font-size: 32px; 
                            font-weight: bold; 
                        }}
                        table {{
                            width: 100%;
                            border-collapse: collapse;
                            margin: 20px 0;
                        }}
                        th, td {{
                            padding: 12px;
                            text-align: left;
                            border-bottom: 1px solid #ddd;
                        }}
                        th {{
                            background-color: #3498db;
                            color: white;
                        }}
                        tr:hover {{
                            background-color: #f5f5f5;
                        }}
                        .footer {{
                            margin-top: 30px;
                            padding-top: 20px;
                            border-top: 1px solid #ddd;
                            color: #7f8c8d;
                            font-size: 12px;
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🎯 多任务交通感知系统检测结果分析报告</h1>
                        
                        <div class="stats">
                            <div class="stat">
                                <div class="stat-label">总检测数</div>
                                <div class="stat-value">{data['total_detections']}</div>
                            </div>
                            <div class="stat">
                                <div class="stat-label">平均置信度</div>
                                <div class="stat-value">{data['avg_confidence']:.1f}%</div>
                            </div>
                            <div class="stat">
                                <div class="stat-label">类别数量</div>
                                <div class="stat-value">{data['num_classes']}</div>
                            </div>
                            <div class="stat">
                                <div class="stat-label">图片数量</div>
                                <div class="stat-value">{data['num_images']}</div>
                            </div>
                        </div>
                        
                        <h2>📊 类别分布统计</h2>
                        <table>
                            <thead>
                                <tr>
                                    <th>类别</th>
                                    <th>数量</th>
                                    <th>占比</th>
                                </tr>
                            </thead>
                            <tbody>
                                {class_table}
                            </tbody>
                        </table>
                        
                        <div class="footer">
                            <p>📁 结果路径: {data.get('result_dir', 'N/A')}</p>
                            <p>📅 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p>🔧 多任务交通视觉感知系统</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                InfoBar.success(
                    title="成功",
                    content=f"报告已保存: {file_path}",
                    position=InfoBarPosition.TOP,
                    parent=self
                )
                
            except Exception as e:
                import traceback
                error_msg = traceback.format_exc()
                self.append_log(f"[错误] {error_msg}")
                InfoBar.error(
                    title="错误",
                    content=f"导出失败: {str(e)}",
                    position=InfoBarPosition.TOP,
                    parent=self
                )
