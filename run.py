#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装和运行脚本
自动检查依赖并启动程序
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("❌ 错误: 需要 Python 3.7 或更高版本")
        print(f"当前版本: Python {sys.version}")
        return False
    
    print(f"✓ Python 版本检查通过: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = {
        'customtkinter': '5.2.0',
        'packaging': '21.0'
    }
    
    missing_packages = []
    
    for package, min_version in required_packages.items():
        try:
            __import__(package)
            print(f"✓ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} 未安装")
    
    return missing_packages

def install_dependencies(packages):
    """安装缺少的依赖包"""
    print(f"\n正在安装依赖包: {', '.join(packages)}")
    
    try:
        cmd = [sys.executable, '-m', 'pip', 'install'] + packages
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✓ 依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def run_tests():
    """运行功能测试"""
    print("\n正在运行功能测试...")
    
    try:
        result = subprocess.run([sys.executable, 'test.py'], 
                              capture_output=True, text=True, check=True)
        print("✓ 功能测试通过")
        return True
    except subprocess.CalledProcessError:
        print("⚠️  功能测试失败，但程序仍可尝试启动")
        return False
    except FileNotFoundError:
        print("⚠️  找不到测试文件，跳过测试")
        return True

def start_application():
    """启动主程序"""
    print("\n正在启动增量打包工具...")
    
    try:
        from main import main
        main()
    except ImportError as e:
        print(f"❌ 导入主程序失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 程序运行失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("=" * 60)
    print("增量文件打包工具 - 自动安装和启动")
    print("作者: MiniMax Agent")
    print("=" * 60)
    
    # 检查当前目录
    if not Path('main.py').exists():
        print("❌ 错误: 请在项目根目录下运行此脚本")
        sys.exit(1)
    
    # 检查Python版本
    if not check_python_version():
        sys.exit(1)
    
    # 检查依赖
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"\n发现缺少 {len(missing_packages)} 个依赖包")
        choice = input("是否自动安装? (y/n): ").lower().strip()
        
        if choice in ['y', 'yes', '是']:
            if not install_dependencies(missing_packages):
                print("依赖安装失败，请手动安装:")
                print(f"pip install {' '.join(missing_packages)}")
                sys.exit(1)
        else:
            print("请手动安装依赖后重试:")
            print(f"pip install {' '.join(missing_packages)}")
            sys.exit(1)
    
    # 运行测试
    run_tests()
    
    # 启动程序
    start_application()

if __name__ == '__main__':
    main()
