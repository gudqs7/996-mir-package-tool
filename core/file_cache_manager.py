# -*- coding: utf-8 -*-
"""
文件缓存管理模块
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime
import json

class FileCacheManager:
    """文件缓存管理器，负责缓存文件内容用于差异对比"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录路径，如果为None则使用默认路径
        """
        if cache_dir is None:
            # 默认使用用户主目录下的缓存目录（但推荐传入output_dir/cache）
            home_dir = Path.home()
            self.cache_dir = home_dir / ".incremental_packer" / "cache"
        else:
            self.cache_dir = Path(cache_dir)
            
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存索引文件
        self.index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
    
    @classmethod
    def create_for_output_dir(cls, output_dir: Path) -> 'FileCacheManager':
        """
        为指定输出目录创建缓存管理器
        
        Args:
            output_dir: 输出目录路径
            
        Returns:
            缓存管理器实例
        """
        cache_dir = output_dir / "cache"
        return cls(cache_dir)
    
    def _load_cache_index(self) -> Dict:
        """加载缓存索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"files": {}, "last_update": None}
    
    def _save_cache_index(self):
        """保存缓存索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存缓存索引失败: {e}")
    
    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """获取文件的SHA256哈希值"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                for chunk in iter(lambda: f.read(4096), b""):
                    file_hash.update(chunk)
                return file_hash.hexdigest()
        except IOError:
            return None
    
    def _get_cache_file_path(self, file_path: str, file_hash: str) -> Path:
        """获取缓存文件路径"""
        # 使用文件路径的哈希值作为目录结构，避免路径过长
        path_hash = hashlib.md5(file_path.encode('utf-8')).hexdigest()
        cache_subdir = self.cache_dir / path_hash[:2] / path_hash[2:4]
        cache_subdir.mkdir(parents=True, exist_ok=True)
        return cache_subdir / f"{file_hash}.cache"
    
    def cache_file(self, file_path: Path, relative_path: str) -> bool:
        """
        缓存文件内容
        
        Args:
            file_path: 实际文件路径
            relative_path: 相对路径（用作索引键）
            
        Returns:
            是否成功缓存
        """
        try:
            if not file_path.exists():
                return False
            
            # 获取文件哈希
            file_hash = self._get_file_hash(file_path)
            if not file_hash:
                return False
            
            # 检查是否已经缓存
            if relative_path in self.cache_index["files"]:
                cached_info = self.cache_index["files"][relative_path]
                if cached_info.get("hash") == file_hash:
                    # 文件没有变化，不需要重新缓存
                    return True
            
            # 获取缓存文件路径
            cache_file_path = self._get_cache_file_path(relative_path, file_hash)
            
            # 复制文件到缓存目录
            shutil.copy2(file_path, cache_file_path)
            
            # 更新缓存索引
            self.cache_index["files"][relative_path] = {
                "hash": file_hash,
                "cache_file": str(cache_file_path),
                "size": file_path.stat().st_size,
                "timestamp": datetime.now().isoformat(),
                "original_path": str(file_path)
            }
            
            self._save_cache_index()
            return True
            
        except Exception as e:
            print(f"缓存文件失败 {relative_path}: {e}")
            return False
    
    def get_cached_content(self, relative_path: str) -> Optional[str]:
        """
        获取缓存的文件内容
        
        Args:
            relative_path: 相对路径
            
        Returns:
            文件内容，如果不存在或读取失败则返回None
        """
        try:
            if relative_path not in self.cache_index["files"]:
                return None
            
            cached_info = self.cache_index["files"][relative_path]
            cache_file_path = Path(cached_info["cache_file"])
            
            if not cache_file_path.exists():
                # 缓存文件不存在，清理索引
                del self.cache_index["files"][relative_path]
                self._save_cache_index()
                return None
            
            # 检查是否为文本文件
            if not self._is_text_file(cache_file_path):
                return None
            
            # 读取文件内容
            with open(cache_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
                
        except Exception as e:
            print(f"读取缓存文件失败 {relative_path}: {e}")
            return None
    
    def _is_text_file(self, file_path: Path) -> bool:
        """判断是否为文本文件"""
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.xml', '.json',
            '.ini', '.cfg', '.conf', '.log', '.csv', '.sql', '.sh', '.bat',
            '.yml', '.yaml', '.toml', '.properties', '.c', '.cpp', '.h',
            '.java', '.cs', '.php', '.rb', '.go', '.rs', '.kt', '.swift'
        }
        
        if file_path.suffix.lower() in text_extensions:
            return True
        
        # 尝试读取文件开头判断
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(8192)
                # 检查是否包含null字节
                if b'\0' in sample:
                    return False
                # 尝试解码
                sample.decode('utf-8')
                return True
        except (UnicodeDecodeError, IOError):
            return False
    
    def cache_files_batch(self, files_dict: Dict[str, Path]) -> List[str]:
        """
        批量缓存文件
        
        Args:
            files_dict: {relative_path: actual_file_path} 的字典
            
        Returns:
            成功缓存的文件列表
        """
        cached_files = []
        for relative_path, file_path in files_dict.items():
            if self.cache_file(file_path, relative_path):
                cached_files.append(relative_path)
        
        # 更新最后更新时间
        self.cache_index["last_update"] = datetime.now().isoformat()
        self._save_cache_index()
        
        return cached_files
    
    def clear_cache(self) -> bool:
        """
        清理所有缓存
        
        Returns:
            是否成功清理
        """
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            self.cache_index = {"files": {}, "last_update": None}
            self._save_cache_index()
            return True
            
        except Exception as e:
            print(f"清理缓存失败: {e}")
            return False
    
    def get_cache_info(self) -> Dict:
        """获取缓存信息"""
        total_files = len(self.cache_index["files"])
        total_size = 0
        
        for file_info in self.cache_index["files"].values():
            total_size += file_info.get("size", 0)
        
        return {
            "total_files": total_files,
            "total_size": total_size,
            "last_update": self.cache_index.get("last_update"),
            "cache_dir": str(self.cache_dir)
        }
    
    def has_cached_version(self, relative_path: str) -> bool:
        """检查是否有缓存版本"""
        return relative_path in self.cache_index["files"]