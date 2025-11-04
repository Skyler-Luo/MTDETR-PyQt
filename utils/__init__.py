"""
工具模块包
集中管理数据库、性能监控、交通分析、结果渲染、UI组件工厂、格式化工具等功能
"""

from .database import HistoryDB
from .performance_monitor import PerformanceMonitor
from .traffic_analyzer import TrafficLightAnalyzer, DrivableAreaAnalyzer
from .result_renderer import DetectionRenderer, BannerRenderer, create_detection_renderer
from .ui_factory import UIComponentFactory
from .formatting import (
    format_timestamp, format_duration, format_file_size,
    get_filename, parse_image_size, format_confidence, get_source_type
)
from .constants import (
    MTDETR_CLASS_NAMES, YOLO_PERSON_CLASS_ID, YOLO_TRAFFIC_LIGHT_CLASS_ID,
    YOLO_OTHER_CLASS_ID, YOLO_PERSON_ORIGINAL_ID, YOLO_TRAFFIC_LIGHT_ORIGINAL_ID,
    SPECIAL_CLASS_NAMES, COLORS, DEFAULT_RENDER_STYLE, get_class_name
)

__all__ = [
    'HistoryDB',
    'PerformanceMonitor',
    'TrafficLightAnalyzer',
    'DrivableAreaAnalyzer',
    'DetectionRenderer',
    'BannerRenderer',
    'create_detection_renderer',
    'UIComponentFactory',
    'format_timestamp',
    'format_duration',
    'format_file_size',
    'get_filename',
    'parse_image_size',
    'format_confidence',
    'get_source_type',
    'MTDETR_CLASS_NAMES',
    'YOLO_PERSON_CLASS_ID',
    'YOLO_TRAFFIC_LIGHT_CLASS_ID',
    'YOLO_OTHER_CLASS_ID',
    'YOLO_PERSON_ORIGINAL_ID',
    'YOLO_TRAFFIC_LIGHT_ORIGINAL_ID',
    'SPECIAL_CLASS_NAMES',
    'COLORS',
    'DEFAULT_RENDER_STYLE',
    'get_class_name',
]
