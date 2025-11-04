"""
应用配置文件
集中管理应用的所有配置项，包括路径、模型、参数、UI等

配置分类:
- 应用信息: APP_NAME, APP_VERSION, APP_AUTHOR
- 路径配置: BASE_DIR, MODEL_DIR, RUNS_DIR, DATASET_DIR, DATABASE_DIR
- 模型配置: DEFAULT_MODEL_PATH, YOLOV10_MODEL_PATH, DEFAULT_PARAMS
- 文件格式: SUPPORTED_IMAGE_FORMATS, SUPPORTED_VIDEO_FORMATS
- UI配置: WINDOW_SIZE, THEME_*, IMAGE_SIZE_PRESETS
- 设备配置: DEVICE_OPTIONS
"""

import os
from pathlib import Path

# 尝试导入 torch 进行设备检测
try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


# 应用信息
APP_NAME = "基于 Transformer 的多任务交通视觉感知系统"
APP_VERSION = "1.0.0"
APP_AUTHOR = "宇翊"

# 路径配置
BASE_DIR = Path(__file__).parent
MODEL_DIR = BASE_DIR
RUNS_DIR = BASE_DIR / "runs"  # 运行结果目录
DATASET_DIR = BASE_DIR / "dataset"  # 数据集目录
DATABASE_DIR = BASE_DIR / "database"  # 历史记录数据库目录

# 模型配置
DEFAULT_MODEL_PATH = BASE_DIR / "best.pt"  # Real-time Multi-task Transformer
YOLOV10_MODEL_PATH = BASE_DIR / "yolov10n.pt"  # YOLOv10n

# 设备检测和配置
def get_available_devices():
    """
    自动检测可用的计算设备
    返回可用设备列表，优先显示可用的 GPU
    """
    devices = ['cpu']  # CPU 总是可用
    
    if _TORCH_AVAILABLE and torch.cuda.is_available():
        # 添加所有可用的 CUDA 设备
        gpu_count = torch.cuda.device_count()
        for i in range(gpu_count):
            devices.append(f'cuda:{i}')
    
    return devices

def get_default_device():
    """
    获取默认设备
    如果 CUDA 可用则使用 cuda:0，否则使用 cpu
    """
    if _TORCH_AVAILABLE and torch.cuda.is_available():
        return 'cuda:0'
    return 'cpu'

# 设备配置
DEVICE_OPTIONS = get_available_devices()
DEFAULT_DEVICE = get_default_device()

# 预测参数默认值
DEFAULT_PARAMS = {
    'imgsz': (640, 640),           # 输入图像尺寸
    'device': DEFAULT_DEVICE,      # 计算设备（自动检测）
    'mask_threshold': [0.45, 0.9], # 分割掩码阈值范围
    'show_labels': True,           # 显示标签
    'show_boxes': True,            # 显示边界框
    'show_conf': True,             # 显示置信度
    'save': True,                  # 保存结果
    'project': 'runs',             # 输出项目目录
    'name': 'predict'              # 输出子目录名称
}

# 支持的文件格式
SUPPORTED_IMAGE_FORMATS = [
    '*.jpg', '*.jpeg', '*.png', '*.bmp', '*.gif', '*.tiff', '*.webp'
]

SUPPORTED_VIDEO_FORMATS = [
    '*.mp4', '*.avi', '*.mov', '*.mkv', '*.flv', '*.wmv', '*.webm'
]

# UI 配置
WINDOW_SIZE = (1200, 800)  # 主窗口默认尺寸
CARD_SPACING = 15          # 卡片间距
LAYOUT_MARGIN = 20         # 布局边距

# 主题配置
THEME_AUTO = "auto"
THEME_LIGHT = "light"
THEME_DARK = "dark"

# 图像尺寸预设
IMAGE_SIZE_PRESETS = [
    (320, 320),
    (512, 512),
    (640, 640),
    (800, 800),
    (1024, 1024)
]

# 初始化函数
def ensure_dirs():
    """
    确保必要的目录存在
    在应用启动时自动创建所需的目录结构
    """
    RUNS_DIR.mkdir(exist_ok=True)
    DATASET_DIR.mkdir(exist_ok=True)
    DATABASE_DIR.mkdir(exist_ok=True)

def print_device_info():
    """
    打印设备信息（用于调试）
    """
    print("=" * 60)
    print("设备配置信息")
    print("=" * 60)
    print(f"可用设备: {DEVICE_OPTIONS}")
    print(f"默认设备: {DEFAULT_DEVICE}")
    
    if _TORCH_AVAILABLE:
        print(f"PyTorch 版本: {torch.__version__}")
        print(f"CUDA 可用: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"GPU 数量: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
    else:
        print("⚠️  PyTorch 未安装，无法使用 GPU 加速")
    print("=" * 60)

# 自动初始化目录
ensure_dirs()

# 如果是直接运行此文件，打印设备信息
if __name__ == '__main__':
    print_device_info()
