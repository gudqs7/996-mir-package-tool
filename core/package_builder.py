# -*- coding: utf-8 -*-
"""
打包模块
"""

import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Callable
import threading
from concurrent.futures import ThreadPoolExecutor

class PackageBuilder:
    """打包构建器"""
    
    def __init__(self):
        self._stop_build = False
        self._lock = threading.Lock()
    
    def create_package(self, source_dir: Path, output_file: Path, 
                      files_to_include: List[str], 
                      progress_callback: Optional[Callable] = None) -> bool:
        """
        创建打包文件
        
        Args:
            source_dir: 源目录
            output_file: 输出文件路径
            files_to_include: 要包含的文件列表（相对路径）
            progress_callback: 进度回调函数
            
        Returns:
            打包是否成功
        """
        self._stop_build = False
        
        try:
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            total_files = len(files_to_include)
            processed = 0
            
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                for relative_path in files_to_include:
                    if self._stop_build:
                        return False
                    
                    source_file = source_dir / relative_path
                    if source_file.exists() and source_file.is_file():
                        try:
                            # 使用相对路径保持目录结构
                            zf.write(source_file, relative_path)
                            processed += 1
                            
                            if progress_callback:
                                progress_callback(processed, total_files)
                        except Exception as e:
                            print(f"添加文件到压缩包失败 {relative_path}: {e}")
                            continue
            
            return not self._stop_build
            
        except Exception as e:
            print(f"创建打包失败: {e}")
            # 删除部分创建的文件
            if output_file.exists():
                try:
                    output_file.unlink()
                except:
                    pass
            return False
    
    def create_full_package(self, source_dir: Path, output_file: Path,
                           file_info: Dict[str, dict],
                           progress_callback: Optional[Callable] = None) -> bool:
        """
        创建全量包
        
        Args:
            source_dir: 源目录
            output_file: 输出文件路径
            file_info: 文件信息字典
            progress_callback: 进度回调函数
            
        Returns:
            打包是否成功
        """
        files_to_include = list(file_info.keys())
        return self.create_package(source_dir, output_file, files_to_include, progress_callback)
    
    def create_incremental_package(self, source_dir: Path, output_file: Path,
                                  changed_files: List[str],
                                  progress_callback: Optional[Callable] = None) -> bool:
        """
        创建增量包
        
        Args:
            source_dir: 源目录
            output_file: 输出文件路径
            changed_files: 变更的文件列表
            progress_callback: 进度回调函数
            
        Returns:
            打包是否成功
        """
        return self.create_package(source_dir, output_file, changed_files, progress_callback)
    
    def stop_build(self):
        """停止构建"""
        with self._lock:
            self._stop_build = True
    
    def get_package_info(self, package_file: Path) -> Optional[Dict]:
        """
        获取包文件信息
        
        Args:
            package_file: 包文件路径
            
        Returns:
            包信息字典
        """
        try:
            with zipfile.ZipFile(package_file, 'r') as zf:
                file_list = zf.namelist()
                total_size = sum(zf.getinfo(name).file_size for name in file_list)
                compressed_size = sum(zf.getinfo(name).compress_size for name in file_list)
                
                return {
                    'file_count': len(file_list),
                    'total_size': total_size,
                    'compressed_size': compressed_size,
                    'compression_ratio': (1 - compressed_size / total_size) * 100 if total_size > 0 else 0,
                    'files': file_list
                }
        except Exception as e:
            print(f"读取包信息失败: {e}")
            return None
