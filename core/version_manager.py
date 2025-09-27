# -*- coding: utf-8 -*-
"""
版本管理模块
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from packaging import version

@dataclass
class VersionInfo:
    """版本信息"""
    version: str
    timestamp: str
    file_count: int
    total_size: int
    is_full_package: bool
    description: str = ""

class VersionManager:
    """版本管理器"""
    
    def __init__(self, cache_dir: Path):
        """
        初始化版本管理器
        
        Args:
            cache_dir: 缓存目录
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.versions_file = self.cache_dir / "versions.json"
        self.latest_scan_file = self.cache_dir / "latest_scan.json"
        
        self._versions: List[VersionInfo] = []
        self._latest_file_info: Dict[str, dict] = {}
        
        self._load_data()
    
    def _load_data(self):
        """加载数据"""
        # 加载版本信息
        if self.versions_file.exists():
            try:
                with open(self.versions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._versions = [VersionInfo(**item) for item in data]
            except (json.JSONDecodeError, TypeError) as e:
                print(f"加载版本信息失败: {e}")
                self._versions = []
        
        # 加载最新扫描信息
        if self.latest_scan_file.exists():
            try:
                with open(self.latest_scan_file, 'r', encoding='utf-8') as f:
                    self._latest_file_info = json.load(f)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"加载扫描信息失败: {e}")
                self._latest_file_info = {}
    
    def _save_data(self):
        """保存数据"""
        try:
            # 保存版本信息
            with open(self.versions_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(v) for v in self._versions], f, 
                         ensure_ascii=False, indent=2)
            
            # 保存最新扫描信息
            with open(self.latest_scan_file, 'w', encoding='utf-8') as f:
                json.dump(self._latest_file_info, f, 
                         ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存数据失败: {e}")
    
    def get_next_version(self, is_full_package: bool = False) -> str:
        """
        获取下一个版本号
        
        Args:
            is_full_package: 是否为全量包
            
        Returns:
            下一个版本号
        """
        if not self._versions:
            return "v1.0.0"
        
        # 获取最新版本
        latest_version = max(self._versions, key=lambda v: version.parse(v.version.lstrip('v')))
        current = version.parse(latest_version.version.lstrip('v'))
        
        if is_full_package:
            # 全量包：主版本号+1
            next_version = version.Version(f"{current.major + 1}.0.0")
        else:
            # 增量包：次版本号+1
            next_version = version.Version(f"{current.major}.{current.minor + 1}.0")
        
        return f"v{next_version}"
    
    def add_version(self, version_str: str, file_info: Dict[str, dict], 
                   is_full_package: bool = False, description: str = "") -> VersionInfo:
        """
        添加新版本
        
        Args:
            version_str: 版本号
            file_info: 文件信息
            is_full_package: 是否为全量包
            description: 版本描述
            
        Returns:
            版本信息对象
        """
        total_size = sum(info['size'] for info in file_info.values())
        
        version_info = VersionInfo(
            version=version_str,
            timestamp=datetime.now().isoformat(),
            file_count=len(file_info),
            total_size=total_size,
            is_full_package=is_full_package,
            description=description
        )
        
        self._versions.append(version_info)
        self._latest_file_info = file_info.copy()
        self._save_data()
        
        return version_info
    
    def get_versions(self) -> List[VersionInfo]:
        """获取所有版本"""
        return sorted(self._versions, key=lambda v: version.parse(v.version.lstrip('v')), reverse=True)
    
    def get_latest_file_info(self) -> Dict[str, dict]:
        """获取最新的文件信息"""
        return self._latest_file_info.copy()
    
    def compare_files(self, current_files: Dict[str, dict]) -> Tuple[List[str], List[str], List[str]]:
        """
        比较文件变化
        
        Args:
            current_files: 当前文件信息
            
        Returns:
            (new_files, modified_files, deleted_files)
        """
        if not self._latest_file_info:
            # 没有之前的记录，所有文件都是新文件
            return list(current_files.keys()), [], []
        
        old_files = set(self._latest_file_info.keys())
        new_files_set = set(current_files.keys())
        
        # 新增文件
        added = new_files_set - old_files
        
        # 删除文件
        deleted = old_files - new_files_set
        
        # 修改文件（hash值不同）
        modified = []
        for file_path in new_files_set & old_files:
            if current_files[file_path]['hash'] != self._latest_file_info[file_path]['hash']:
                modified.append(file_path)
        
        return list(added), modified, list(deleted)
    
    def reset_to_full_package(self):
        """重置为全量包模式（清除所有版本信息）"""
        self._versions.clear()
        self._latest_file_info.clear()
        
        # 删除缓存文件
        if self.versions_file.exists():
            self.versions_file.unlink()
        if self.latest_scan_file.exists():
            self.latest_scan_file.unlink()
    
    def clear_cache(self):
        """清理缓存目录"""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._versions.clear()
        self._latest_file_info.clear()
