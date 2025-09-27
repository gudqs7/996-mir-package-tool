#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本 - 一键打包成 exe 文件
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖环境"""
    print("正在检查依赖...")
    
    # 检查 Python 版本
    if sys.version_info < (3, 7):
        print("错误: 需要 Python 3.7 或更高版本")
        return False
    
    # 检查必要的包
    required_packages = ['customtkinter', 'packaging', 'pyinstaller']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"错误: 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    print("依赖检查通过✓")
    return True

def build_exe():
    """构建 exe 文件"""
    print("正在构建 exe 文件...")
    
    try:
        # 清理之前的构建文件
        if Path("build").exists():
            import shutil
            shutil.rmtree("build")
            print("已清理旧的构建文件")
        
        # 运行 PyInstaller
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",  # 清理缓存
            "build_exe.spec"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("构建成功! ✓")
            
            # 检查输出文件
            exe_file = Path("dist/IncrementalPacker.exe")
            if exe_file.exists():
                size_mb = exe_file.stat().st_size / (1024 * 1024)
                print(f"exe 文件位置: {exe_file.absolute()}")
                print(f"exe 文件大小: {size_mb:.1f} MB")
                return True
            else:
                print("错误: 找不到生成的 exe 文件")
                return False
        else:
            print("构建失败:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"构建过程中发生错误: {e}")
        return False

def install_dependencies():
    """安装依赖"""
    print("正在安装依赖...")
    
    try:
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("依赖安装成功! ✓")
            return True
        else:
            print("依赖安装失败:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"安装依赖时发生错误: {e}")
        return False

def main():
    """主函数"""
    print("===== 增量打包工具 - 一键构建脚本 =====")
    print()
    
    # 检查当前目录
    if not Path("main.py").exists():
        print("错误: 请在项目根目录下运行此脚本")
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        print()
        choice = input("是否自动安装依赖? (y/n): ")
        if choice.lower() in ['y', 'yes', '是']:
            if not install_dependencies():
                print("依赖安装失败，请手动安装")
                sys.exit(1)
        else:
            print("请手动安装依赖后重试")
            sys.exit(1)
    
    print()
    
    # 构建 exe
    if build_exe():
        print()
        print("✓ 构建完成! 现在您可以运行 dist/IncrementalPacker.exe")
        print()
        print("提示:")
        print("1. exe 文件是独立的，不需要安装 Python 环境")
        print("2. 首次运行可能较慢，请耐心等待")
        print("3. 如果杀毒软件误报，请添加到白名单")
    else:
        print("构建失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
