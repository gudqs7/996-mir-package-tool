#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量打包工具功能改进测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.main_window import IncrementalPackerApp

def main():
    """主函数"""
    # 清理测试环境
    import shutil
    cache_dirs = [
        Path.home() / ".incremental_packer" / "cache",
        Path("test_output") / "cache"
    ]
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"清理缓存目录: {cache_dir}")
            except Exception as e:
                print(f"清理缓存目录失败: {e}")
    
    # 创建并运行应用
    app = IncrementalPackerApp()
    
    print("增量打包工具功能改进版已启动")
    print("新功能包括:")
    print("1. 版本配置下拉框 (支持版本1-10)")
    print("2. 缓存路径优化 (使用输出目录/cache)")
    print("3. 配置自动保存 (扫描、打包、退出时)")
    print("4. 版本独立缓存")
    
    app.run()

if __name__ == "__main__":
    main()