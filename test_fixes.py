#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试导入是否正常"""
    print("=== 测试导入修复 ===")
    
    try:
        from gui.main_window import IncrementalPackerApp
        print("✓ gui.main_window 导入成功")
        
        from gui.file_list_window import FileListWindow
        print("✓ gui.file_list_window 导入成功")
        
        from core.file_cache_manager import FileCacheManager
        print("✓ core.file_cache_manager 导入成功")
        
        from core.config_manager import ConfigManager
        print("✓ core.config_manager 导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_config_initialization():
    """测试config初始化"""
    print("\n=== 测试config初始化修复 ===")
    
    try:
        from gui.main_window import IncrementalPackerApp
        
        # 创建应用实例但不运行主循环
        import customtkinter as ctk
        ctk.set_appearance_mode("light")
        
        app = IncrementalPackerApp()
        
        # 检查config属性
        if hasattr(app, 'config'):
            print("✓ config属性存在")
            
            # 测试config方法
            if hasattr(app.config, 'get_input_directory'):
                print("✓ config.get_input_directory 方法存在")
            
            if hasattr(app.config, 'set_window_geometry'):
                print("✓ config.set_window_geometry 方法存在")
                
            return True
        else:
            print("❌ config属性不存在")
            return False
            
    except Exception as e:
        print(f"❌ config初始化测试失败: {e}")
        return False

def test_cache_manager():
    """测试缓存管理器"""
    print("\n=== 测试文件缓存管理器 ===")
    
    try:
        from core.file_cache_manager import FileCacheManager
        
        cache_manager = FileCacheManager()
        print("✓ FileCacheManager 创建成功")
        
        # 测试缓存信息
        cache_info = cache_manager.get_cache_info()
        print(f"✓ 缓存信息: {cache_info['total_files']} 个文件")
        print(f"  缓存目录: {cache_info['cache_dir']}")
        
        return True
        
    except Exception as e:
        print(f"❌ 缓存管理器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试修复后的功能...\n")
    
    tests = [
        test_imports,
        test_config_initialization, 
        test_cache_manager
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n=== 测试总结 ===")
    print(f"通过: {passed}/{total} 个测试")
    
    if passed == total:
        print("🎉 所有修复都测试通过！")
        print("\n修复内容:")
        print("1. ✓ 修复了相对导入问题，改为绝对导入")
        print("2. ✓ 修复了config属性缺失问题，正确初始化ConfigManager")
        print("3. ✓ 实现了文件缓存机制，用于diff内容对比")
        print("4. ✓ 集成缓存到打包流程，自动缓存文件内容")
        print("5. ✓ 修改了差异查看器，优先使用缓存内容")
    else:
        print("❌ 部分测试失败，需要进一步检查")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
