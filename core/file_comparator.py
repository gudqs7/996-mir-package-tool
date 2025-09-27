# -*- coding: utf-8 -*-
"""
文件对比模块
"""

import difflib
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class ChangeType(Enum):
    """变更类型"""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"

@dataclass
class FileChange:
    """文件变更信息"""
    file_path: str
    change_type: ChangeType
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    old_size: Optional[int] = None
    new_size: Optional[int] = None
    old_mtime: Optional[float] = None
    new_mtime: Optional[float] = None

class FileComparator:
    """文件对比器"""
    
    def __init__(self, max_file_size_for_diff: int = 1024 * 1024):  # 1MB
        """
        初始化文件对比器
        
        Args:
            max_file_size_for_diff: 进行内容对比的最大文件大小
        """
        self.max_file_size_for_diff = max_file_size_for_diff
    
    def compare_file_lists(self, old_files: Dict[str, dict], 
                          new_files: Dict[str, dict]) -> List[FileChange]:
        """
        比较文件列表
        
        Args:
            old_files: 旧文件信息
            new_files: 新文件信息
            
        Returns:
            文件变更列表
        """
        changes = []
        
        old_paths = set(old_files.keys())
        new_paths = set(new_files.keys())
        
        # 新增文件
        for path in new_paths - old_paths:
            file_info = new_files[path]
            changes.append(FileChange(
                file_path=path,
                change_type=ChangeType.ADDED,
                new_hash=file_info['hash'],
                new_size=file_info['size'],
                new_mtime=file_info['mtime']
            ))
        
        # 删除文件
        for path in old_paths - new_paths:
            file_info = old_files[path]
            changes.append(FileChange(
                file_path=path,
                change_type=ChangeType.DELETED,
                old_hash=file_info['hash'],
                old_size=file_info['size'],
                old_mtime=file_info['mtime']
            ))
        
        # 修改文件
        for path in old_paths & new_paths:
            old_info = old_files[path]
            new_info = new_files[path]
            
            if old_info['hash'] != new_info['hash']:
                changes.append(FileChange(
                    file_path=path,
                    change_type=ChangeType.MODIFIED,
                    old_hash=old_info['hash'],
                    new_hash=new_info['hash'],
                    old_size=old_info['size'],
                    new_size=new_info['size'],
                    old_mtime=old_info['mtime'],
                    new_mtime=new_info['mtime']
                ))
        
        return sorted(changes, key=lambda x: x.file_path)
    
    def get_file_diff(self, old_file_path: Path, new_file_path: Path, 
                     context_lines: int = 3) -> Optional[List[str]]:
        """
        获取文件内容差异
        
        Args:
            old_file_path: 旧文件路径
            new_file_path: 新文件路径
            context_lines: 上下文行数
            
        Returns:
            差异内容列表
        """
        try:
            # 检查文件大小
            if (old_file_path.exists() and old_file_path.stat().st_size > self.max_file_size_for_diff) or \
               (new_file_path.exists() and new_file_path.stat().st_size > self.max_file_size_for_diff):
                return [f"文件太大，不显示内容差异（限制: {self.max_file_size_for_diff // 1024}KB）"]
            
            # 读取文件内容
            old_content = []
            new_content = []
            
            if old_file_path.exists():
                try:
                    with open(old_file_path, 'r', encoding='utf-8') as f:
                        old_content = f.readlines()
                except UnicodeDecodeError:
                    # 尝试其他编码
                    try:
                        with open(old_file_path, 'r', encoding='gbk') as f:
                            old_content = f.readlines()
                    except UnicodeDecodeError:
                        return ["旧文件编码不支持，无法显示内容差异"]
            
            if new_file_path.exists():
                try:
                    with open(new_file_path, 'r', encoding='utf-8') as f:
                        new_content = f.readlines()
                except UnicodeDecodeError:
                    try:
                        with open(new_file_path, 'r', encoding='gbk') as f:
                            new_content = f.readlines()
                    except UnicodeDecodeError:
                        return ["新文件编码不支持，无法显示内容差异"]
            
            # 生成差异
            diff = list(difflib.unified_diff(
                old_content,
                new_content,
                fromfile=f"a/{old_file_path.name}",
                tofile=f"b/{new_file_path.name}",
                n=context_lines
            ))
            
            return diff
            
        except Exception as e:
            return [f"生成差异失败: {e}"]
    
    def is_text_file(self, file_path: Path) -> bool:
        """
        判断是否为文本文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否为文本文件
        """
        text_extensions = {
            '.txt', '.py', '.js', '.html', '.css', '.xml', '.json', '.yaml', '.yml',
            '.md', '.rst', '.ini', '.cfg', '.conf', '.sh', '.bat', '.ps1',
            '.c', '.cpp', '.h', '.hpp', '.java', '.cs', '.php', '.rb', '.go',
            '.sql', '.log', '.csv', '.tsv'
        }
        
        return file_path.suffix.lower() in text_extensions
    
    def format_size(self, size_bytes: int) -> str:
        """
        格式化文件大小
        
        Args:
            size_bytes: 字节数
            
        Returns:
            格式化后的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
