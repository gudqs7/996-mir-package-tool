# -*- coding: utf-8 -*-
"""
文件扫描和hash计算模块
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, Set, Optional, List
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class FileScanner:
    """文件扫描器，负责扫描目录和计算文件hash"""
    
    def __init__(self, 
                 target_paths: Optional[List[str]] = None,
                 exclude_files: Optional[List[str]] = None,
                 exclude_folders: Optional[List[str]] = None,
                 exclude_extensions: Optional[List[str]] = None):
        """
        初始化文件扫描器
        
        Args:
            target_paths: 目标扫描路径列表 (相对于输入目录)
            exclude_files: 需要排除的具体文件列表 (相对路径)
            exclude_folders: 需要排除的文件夹列表
            exclude_extensions: 需要排除的文件扩展名列表
        """
        # 只扫描指定的路径
        self.target_paths = target_paths or ["Mir200", "DBServer\\dbsrc.ini"]
        
        # 排除的具体文件
        self.exclude_files = set(exclude_files or ["Mir200\\M2Server.map", "Mir200\\GlobalVal.ini"])
        
        # 排除的文件夹
        self.exclude_folders = set(exclude_folders or ["Log"])
        
        # 排除的扩展名
        self.exclude_extensions = set(exclude_extensions or [".log", ".zip", ".dll", ".exe", ".json"])
        
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
    
    def should_exclude_file(self, file_path: Path, relative_path: str) -> bool:
        """
        判断文件是否应该被排除
        
        Args:
            file_path: 文件绝对路径
            relative_path: 文件相对路径
            
        Returns:
            是否排除该文件
        """
        # 检查扩展名
        if file_path.suffix.lower() in self.exclude_extensions:
            return True
        
        # 检查是否在排除文件列表中
        if relative_path in self.exclude_files:
            return True
        
        # 检查父目录是否在排除列表中
        for part in Path(relative_path).parts:
            if part in self.exclude_folders:
                return True
        
        return False
    
    def scan_directory(self, directory: Path, progress_callback=None) -> Dict[str, dict]:
        """
        扫描目录中的指定文件并计算hash
        
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
        
        # 收集目标路径下的文件
        all_files = []
        
        for target_path in self.target_paths:
            if self._stop_scan:
                break
                
            target_full_path = directory / target_path
            
            if not target_full_path.exists():
                print(f"目标路径不存在: {target_full_path}")
                continue
            
            if target_full_path.is_file():
                # 直接是文件
                relative_path = target_path
                if not self.should_exclude_file(target_full_path, relative_path):
                    all_files.append((target_full_path, relative_path))
            elif target_full_path.is_dir():
                # 是目录，遍历其中的文件
                for root, dirs, files in os.walk(target_full_path):
                    if self._stop_scan:
                        break
                    
                    # 检查当前目录是否在排除列表中
                    current_relative = Path(root).relative_to(directory)
                    if any(part in self.exclude_folders for part in current_relative.parts):
                        dirs.clear()  # 不再遍历子目录
                        continue
                    
                    for file in files:
                        file_path = Path(root) / file
                        relative_path = str(file_path.relative_to(directory))
                        
                        if not self.should_exclude_file(file_path, relative_path):
                            all_files.append((file_path, relative_path))
        
        total_files = len(all_files)
        processed = 0
        
        # 使用线程池并行处理
        max_workers = min(32, len(all_files)) if all_files else 1
        
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
