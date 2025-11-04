"""
常量定义模块
统一管理所有常量，避免重复定义
"""

# Real-time Multi-task Transformer类别映射
MTDETR_CLASS_NAMES = {
    0: "Vehicle",     # 车辆
    1: "Drivable",    # 可驾驶区域
    2: "Lane"         # 车道线
}

# YOLOv10n特殊类别ID
YOLO_PERSON_CLASS_ID = 999
YOLO_TRAFFIC_LIGHT_CLASS_ID = 998
YOLO_OTHER_CLASS_ID = 997

# YOLOv10n原始类别ID
YOLO_PERSON_ORIGINAL_ID = 0
YOLO_TRAFFIC_LIGHT_ORIGINAL_ID = 9

# 类别ID到名称的映射
SPECIAL_CLASS_NAMES = {
    YOLO_PERSON_CLASS_ID: "Person",
    YOLO_TRAFFIC_LIGHT_CLASS_ID: "TrafficLight",
    YOLO_OTHER_CLASS_ID: "Other"
}

# 颜色定义
COLORS = {
    'person': (0, 255, 0),           # 绿色
    'person_on_road': (0, 0, 255),   # 红色
    'traffic_light': (0, 165, 255),  # 橙色
    'red_light': (0, 0, 255),        # 红色
    'yellow_light': (0, 255, 255),   # 黄色
    'green_light': (0, 255, 0),      # 绿色
    'unknown': (128, 128, 128)       # 灰色
}

# 默认渲染样式
DEFAULT_RENDER_STYLE = {
    'box_thickness': 2,
    'font_scale': 0.45,
    'font_thickness': 1,
    'label_padding': 2,
    'mask_alpha': 0.3,
}

def get_class_name(class_id):
    """
    获取类别名称
    
    Args:
        class_id: 类别ID
        
    Returns:
        类别名称字符串
    """
    # 优先查找特殊类别
    if class_id in SPECIAL_CLASS_NAMES:
        return SPECIAL_CLASS_NAMES[class_id]
    
    # 查找 Real-time Multi-task Transformer 类别
    if class_id in MTDETR_CLASS_NAMES:
        return MTDETR_CLASS_NAMES[class_id]
    
    # 未知类别
    return f"Unknown-{class_id}"
