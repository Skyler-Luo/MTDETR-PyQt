"""
主窗口模块
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import FluentIcon, NavigationItemPosition, MSFluentWindow

from config import APP_NAME, WINDOW_SIZE
from .image_interface import ImageInterface
from .video_interface import VideoInterface
from .history_interface import HistoryInterface
from .analytics_interface import AnalyticsInterface
from .performance_interface import PerformanceInterface
from .about_interface import AboutInterface


class MainWindow(MSFluentWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_window()
        self.init_navigation()
        
    def init_window(self):
        """初始化窗口"""
        self.setWindowTitle(APP_NAME)
        
        # 设置图标 - 使用 FluentIcon
        self.setWindowIcon(FluentIcon.CAR.icon())
        
        # 设置窗口大小
        self.resize(*WINDOW_SIZE)
        
        # 居中显示
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)
        
    def init_navigation(self):
        """初始化导航"""
        # 添加子界面
        self.image_interface = ImageInterface(self)
        self.image_interface.setObjectName("imageInterface")
        
        self.video_interface = VideoInterface(self)
        self.video_interface.setObjectName("videoInterface")
        
        self.history_interface = HistoryInterface(self)
        self.history_interface.setObjectName("historyInterface")
        
        self.analytics_interface = AnalyticsInterface(self)
        self.analytics_interface.setObjectName("analyticsInterface")
        
        self.performance_interface = PerformanceInterface(self)
        self.performance_interface.setObjectName("performanceInterface")
        
        self.about_interface = AboutInterface(self)
        self.about_interface.setObjectName("aboutInterface")
        
        # 添加导航项 - 功能分组
        self.addSubInterface(
            self.image_interface,
            FluentIcon.PHOTO,
            "图片检测",
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.video_interface,
            FluentIcon.VIDEO,
            "视频检测",
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.history_interface,
            FluentIcon.HISTORY,
            "历史记录",
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.analytics_interface,
            FluentIcon.PIE_SINGLE,
            "结果分析",
            position=NavigationItemPosition.TOP
        )
        
        self.addSubInterface(
            self.performance_interface,
            FluentIcon.DEVELOPER_TOOLS,
            "性能监控",
            position=NavigationItemPosition.TOP
        )
        
        # 底部项
        self.addSubInterface(
            self.about_interface,
            FluentIcon.INFO,
            "关于",
            position=NavigationItemPosition.BOTTOM
        )
        
        # 设置默认界面
        self.stackedWidget.setCurrentWidget(self.image_interface)
        
        # 共享模型实例
        self._setup_model_sharing()
    
    def _setup_model_sharing(self):
        """设置模型共享"""
        # 当任一界面加载模型后，共享到其他界面
        
        # 图片界面模型共享
        original_image_load = self.image_interface._load_model_from_path
        def image_load_and_share(file_path):
            original_image_load(file_path)
            if hasattr(self.image_interface, 'model') and self.image_interface.model:
                person_model = getattr(self.image_interface, 'person_model', None)
                # 共享到视频界面
                self.video_interface.set_model(self.image_interface.model, person_model=person_model)
        self.image_interface._load_model_from_path = image_load_and_share
        
        # 视频界面模型共享
        original_video_load = self.video_interface._load_model_from_path
        def video_load_and_share(file_path):
            original_video_load(file_path)
            if hasattr(self.video_interface, 'model') and self.video_interface.model:
                person_model = getattr(self.video_interface, 'person_model', None)
                # 共享到图片界面
                self.image_interface.set_model(self.video_interface.model, person_model=person_model)
        self.video_interface._load_model_from_path = video_load_and_share
