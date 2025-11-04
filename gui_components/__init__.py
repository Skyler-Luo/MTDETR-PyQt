"""
GUI 组件包
包含所有图形界面组件

组件分类:
- 主窗口: MainWindow
- 基础类: BaseDetectionInterface 及混入类
- 功能界面: ImageInterface, VideoInterface, HistoryInterface, 
           AnalyticsInterface, PerformanceInterface, AboutInterface
- 自定义控件: ImagePreviewCard
- 后台线程: PredictThread
"""

# 主窗口
from .main_window import MainWindow

# 基础类和混入类
from .base_interface import (
    BaseDetectionInterface, LogMixin, ModelLoaderMixin, 
    UICardMixin, PredictMixin
)

# 功能界面
from .image_interface import ImageInterface
from .video_interface import VideoInterface
from .history_interface import HistoryInterface
from .analytics_interface import AnalyticsInterface
from .performance_interface import PerformanceInterface
from .about_interface import AboutInterface

# 自定义控件
from .image_preview import ImagePreviewCard

# 后台线程
from .predict_thread import PredictThread

__all__ = [
    # 主窗口
    'MainWindow',
    
    # 基础类和混入类
    'BaseDetectionInterface',
    'LogMixin',
    'ModelLoaderMixin',
    'UICardMixin',
    'PredictMixin',
    
    # 功能界面
    'ImageInterface',
    'VideoInterface',
    'HistoryInterface',
    'AnalyticsInterface',
    'PerformanceInterface',
    'AboutInterface',
    
    # 自定义控件
    'ImagePreviewCard',
    
    # 后台线程
    'PredictThread'
]
