# -*- coding: utf-8 -*-
"""
文件扫描和hash计算模块
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, Set, Optional
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class FileScanner:
    """文件扫描器，负责扫描目录和计算文件hash"""
    
    def __init__(self, exclude_extensions: Optional[Set[str]] = None):
        """
        初始化文件扫描器
        
        Args:
            exclude_extensions: 需要排除的文件扩展名集合
        """
        self.exclude_extensions = exclude_extensions or {'.dll', '.exe', '.json'}
        self._stop_scan = False
        self._lock = threading.Lock()
    
    def calculate_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        计算文件hash值
        
        Args:
            file_path: 文件路径
            algorithm: hash算法，默认sha256
            
        Returns:
            文件的hash值
        """
        hasher = hashlib.new(algorithm)
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    if self._stop_scan:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, IOError) as e:
            print(f"读取文件失败 {file_path}: {e}")
            return ""
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """
        判断文件是否应该被排除
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否排除该文件
        """
        return file_path.suffix.lower() in self.exclude_extensions
    
    def scan_directory(self, directory: Path, progress_callback=None) -> Dict[str, dict]:
        """
        扫描目录中的所有文件并计算hash
        
        Args:
            directory: 要扫描的目录
            progress_callback: 进度回调函数
            
        Returns:
            文件信息字典，键为相对路径，值包含文件信息
        """
        self._stop_scan = False
        file_info = {}
        
        if not directory.exists() or not directory.is_dir():
            return file_info
        
        # 收集所有文件
        all_files = []
        for root, dirs, files in os.walk(directory):
            if self._stop_scan:
                break
            for file in files:
                file_path = Path(root) / file
                if not self.should_exclude_file(file_path):
                    relative_path = file_path.relative_to(directory)
                    all_files.append((file_path, str(relative_path)))
        
        total_files = len(all_files)
        processed = 0
        
        # 使用线程池并行处理
        max_workers = min(8, len(all_files)) if all_files else 1
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_file = {
                executor.submit(self._process_single_file, file_path, relative_path): relative_path
                for file_path, relative_path in all_files
            }
            
            # 处理结果
            for future in as_completed(future_to_file):
                if self._stop_scan:
                    break
                    
                relative_path = future_to_file[future]
                try:
                    result = future.result()
                    if result:
                        file_info[relative_path] = result
                except Exception as e:
                    print(f"处理文件失败 {relative_path}: {e}")
                
                processed += 1
                if progress_callback:
                    progress_callback(processed, total_files)
        
        return file_info
    
    def _process_single_file(self, file_path: Path, relative_path: str) -> Optional[dict]:
        """
        处理单个文件
        
        Args:
            file_path: 绝对文件路径
            relative_path: 相对路径
            
        Returns:
            文件信息字典
        """
        try:
            stat = file_path.stat()
            hash_value = self.calculate_file_hash(file_path)
            
            if not hash_value:  # hash计算失败
                return None
                
            return {
                'size': stat.st_size,
                'mtime': stat.st_mtime,
                'hash': hash_value,
                'relative_path': relative_path
            }
        except (OSError, IOError) as e:
            print(f"访问文件失败 {file_path}: {e}")
            return None
    
    def stop_scan(self):
        """停止扫描"""
        with self._lock:
            self._stop_scan = True
