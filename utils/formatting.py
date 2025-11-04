"""
数据格式化工具模块
统一处理日期、时间、文件路径等格式化
"""

import os
from datetime import datetime
from pathlib import Path


def format_timestamp(timestamp_str, format='%m-%d %H:%M'):
    """
    格式化时间戳字符串
    
    Args:
        timestamp_str: ISO格式时间戳字符串
        format: 输出格式
        
    Returns:
        格式化后的字符串
    """
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime(format)
    except:
        return timestamp_str[:16] if len(timestamp_str) > 16 else timestamp_str


def format_duration(seconds):
    """
    格式化时长
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化字符串 (如 "1.23s" 或 "N/A")
    """
    if seconds is None or seconds <= 0:
        return "N/A"
    return f"{seconds:.2f}s"


def format_file_size(bytes_size):
    """
    格式化文件大小
    
    Args:
        bytes_size: 字节数
        
    Returns:
        格式化字符串 (如 "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def get_filename(path):
    """
    从路径获取文件名
    
    Args:
        path: 文件路径
        
    Returns:
        文件名
    """
    return os.path.basename(path) if path else ""


def parse_image_size(size_text):
    """
    解析图像尺寸字符串
    
    Args:
        size_text: 尺寸字符串，格式如 "640×640" 或 "640x640"
        
    Returns:
        (width, height) 元组
    """
    separator = '×' if '×' in size_text else 'x'
    w, h = map(int, size_text.split(separator))
    return (w, h)


def format_confidence(confidence):
    """
    格式化置信度
    
    Args:
        confidence: 置信度值 (0-1)
        
    Returns:
        百分比字符串 (如 "85.2%")
    """
    if confidence is None:
        return "N/A"
    return f"{confidence * 100:.1f}%"


def get_source_type(file_path):
    """
    判断数据源类型
    
    Args:
        file_path: 文件路径
        
    Returns:
        'image', 'video', 'folder' 或 'unknown'
    """
    if not file_path:
        return 'unknown'
    
    if os.path.isdir(file_path):
        return 'folder'
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']:
        return 'image'
    elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm']:
        return 'video'
    else:
        return 'unknown'
