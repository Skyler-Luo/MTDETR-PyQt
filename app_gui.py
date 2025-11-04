"""
基于 Transformer 的多任务交通视觉感知系统 - 主程序入口
"""

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from qfluentwidgets import setTheme, Theme

from gui_components import MainWindow


def main():
    """主函数"""
    # 启用高 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 设置主题
    setTheme(Theme.AUTO)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
