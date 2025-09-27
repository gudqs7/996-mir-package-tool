#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量打包工具主程序
作者: MiniMax Agent
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.main_window import IncrementalPackerApp

def main():
    """主程序入口"""
    try:
        app = IncrementalPackerApp()
        app.run()
    except Exception as e:
        print(f"程序启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
