"""
性能监控工具
"""

import psutil
import time
import pynvml
NVIDIA_AVAILABLE = True

from collections import deque
from PyQt5.QtCore import QObject, QTimer, pyqtSignal



class PerformanceMonitor(QObject):
    """性能监控器"""
    
    data_updated = pyqtSignal(dict)
    
    def __init__(self, interval=1000):
        """
        Args:
            interval: 更新间隔(毫秒)
        """
        super().__init__()
        
        self.interval = interval
        self.is_running = False
        
        # 数据历史(最多保存100个数据点)
        self.cpu_history = deque(maxlen=100)
        self.memory_history = deque(maxlen=100)
        self.gpu_history = deque(maxlen=100)
        self.gpu_memory_history = deque(maxlen=100)
        
        # GPU初始化
        self.gpu_available = False
        print(f"[性能监控] NVIDIA库可用: {NVIDIA_AVAILABLE}")
        if NVIDIA_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_count = pynvml.nvmlDeviceGetCount()
                if self.gpu_count > 0:
                    self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    self.gpu_available = True
                    print(f"[性能监控] GPU初始化成功，检测到 {self.gpu_count} 个GPU设备")
                else:
                    print("[性能监控] 未检测到GPU设备")
            except Exception as e:
                print(f"[性能监控] GPU初始化失败: {e}")
                self.gpu_available = False
        
        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_metrics)
    
    def start(self):
        """开始监控"""
        if not self.is_running:
            self.is_running = True
            self.timer.start(self.interval)
    
    def stop(self):
        """停止监控"""
        if self.is_running:
            self.is_running = False
            self.timer.stop()
    
    def update_metrics(self):
        """更新指标"""
        data = {}
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=0.1)
        self.cpu_history.append(cpu_percent)
        data['cpu_percent'] = cpu_percent
        data['cpu_history'] = list(self.cpu_history)
        
        # CPU频率
        try:
            cpu_freq = psutil.cpu_freq()
            data['cpu_freq'] = cpu_freq.current if cpu_freq else 0
        except:
            data['cpu_freq'] = 0
        
        # 内存使用
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        self.memory_history.append(memory_percent)
        data['memory_percent'] = memory_percent
        data['memory_used'] = memory.used / (1024**3)  # GB
        data['memory_total'] = memory.total / (1024**3)  # GB
        data['memory_history'] = list(self.memory_history)
        
        # GPU信息
        if self.gpu_available:
            try:
                data['gpu_available'] = True
                
                # GPU使用率
                gpu_util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
                gpu_percent = gpu_util.gpu
                self.gpu_history.append(gpu_percent)
                data['gpu_percent'] = gpu_percent
                data['gpu_history'] = list(self.gpu_history)
                
                # GPU内存
                gpu_mem = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
                gpu_memory_percent = (gpu_mem.used / gpu_mem.total) * 100
                self.gpu_memory_history.append(gpu_memory_percent)
                data['gpu_memory_percent'] = gpu_memory_percent
                data['gpu_memory_used'] = gpu_mem.used / (1024**3)  # GB
                data['gpu_memory_total'] = gpu_mem.total / (1024**3)  # GB
                data['gpu_memory_history'] = list(self.gpu_memory_history)
                
                # GPU温度
                try:
                    gpu_temp = pynvml.nvmlDeviceGetTemperature(
                        self.gpu_handle, 
                        pynvml.NVML_TEMPERATURE_GPU
                    )
                    data['gpu_temp'] = gpu_temp
                except:
                    data['gpu_temp'] = 0
                
                # GPU功率
                try:
                    gpu_power = pynvml.nvmlDeviceGetPowerUsage(self.gpu_handle) / 1000  # W
                    data['gpu_power'] = gpu_power
                except:
                    data['gpu_power'] = 0
                
            except Exception as e:
                # 处理GPU监控错误
                print(f"[性能监控] GPU数据获取错误: {e}")
                data['gpu_available'] = False
        else:
            data['gpu_available'] = False
        
        # 磁盘IO
        try:
            disk_io = psutil.disk_io_counters()
            data['disk_read'] = disk_io.read_bytes / (1024**2)  # MB
            data['disk_write'] = disk_io.write_bytes / (1024**2)  # MB
        except:
            data['disk_read'] = 0
            data['disk_write'] = 0
        
        # 网络IO
        try:
            net_io = psutil.net_io_counters()
            data['net_sent'] = net_io.bytes_sent / (1024**2)  # MB
            data['net_recv'] = net_io.bytes_recv / (1024**2)  # MB
        except:
            data['net_sent'] = 0
            data['net_recv'] = 0
        
        self.data_updated.emit(data)
    
    def __del__(self):
        """析构函数"""
        if self.gpu_available and NVIDIA_AVAILABLE:
            try:
                pynvml.nvmlShutdown()
            except:
                pass
