# -*- coding: utf-8 -*-
"""
配置管理模块
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理器，负责保存和加载用户设置"""

    def __init__(self, config_file: Optional[Path] = None):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径，如果为None则使用默认路径
        """
        if config_file is None:
            # 使用用户主目录下的配置文件
            home_dir = Path.home()
            self.config_dir = home_dir / ".incremental_packer"
            self.config_dir.mkdir(exist_ok=True)
            self.config_file = self.config_dir / "config.json"
        else:
            self.config_file = Path(config_file)
            self.config_dir = self.config_file.parent
            self.config_dir.mkdir(parents=True, exist_ok=True)

        self._config: Dict[str, Any] = {}
        self.current_version_index = 0  # 当前选中的版本索引 (0-9)

        # 版本配置模板
        self._version_config_template = {
            "input_directory": "",
            "output_directory": ""
        }

        self._default_config = {
            "current_version_index": 0,  # 当前版本索引
            "versions": {  # 10个版本的配置
                str(i): self._version_config_template.copy() for i in range(10)
            },
            "last_updated": "",
            "scan_filters": {
                "target_paths": ["Mir200", "DBServer/dbsrc.ini"],
                "exclude_files": ["Mir200\\M2Server.map", "Mir200\\GlobalVal.ini"],
                "exclude_folders": ["Log"],
                "exclude_extensions": [".log", ".zip", ".dll", ".exe", ".json"]
            },
            "ui_theme": {
                "appearance_mode": "light",  # 改为白色主题
                "color_theme": "blue"
            }
        }

        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    self._config = self._merge_config(self._default_config.copy(), loaded_config)
            else:
                self._config = self._default_config.copy()
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载配置文件失败: {e}")
            self._config = self._default_config.copy()

    def _merge_config(self, default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        """
        递归合并配置，保留默认配置的结构
        
        Args:
            default: 默认配置
            loaded: 加载的配置
            
        Returns:
            合并后的配置
        """
        result = default.copy()

        for key, value in loaded.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._merge_config(result[key], value)
                else:
                    result[key] = value
            else:
                result[key] = value

        return result

    def save_config(self):
        """保存配置文件"""
        try:
            # 更新最后修改时间
            self._config["last_updated"] = datetime.now().isoformat()

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"保存配置文件失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any, auto_save: bool = True):
        """
        设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
            auto_save: 是否自动保存
        """
        keys = key.split('.')
        config = self._config

        # 创建嵌套结构
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

        if auto_save:
            self.save_config()

    def get_current_version_index(self) -> int:
        """获取当前版本索引"""
        return self.get("current_version_index", 0)

    def set_current_version_index(self, index: int, auto_save: bool = True):
        """设置当前版本索引"""
        if 0 <= index <= 9:
            self.current_version_index = index
            self.set("current_version_index", index, auto_save)

    def get_input_directory(self, version_index: Optional[int] = None) -> str:
        """获取输入目录"""
        if version_index is None:
            version_index = self.current_version_index
        return self.get(f"versions.{version_index}.input_directory", "")

    def set_input_directory(self, directory: str, version_index: Optional[int] = None, auto_save: bool = True):
        """设置输入目录"""
        if version_index is None:
            version_index = self.current_version_index
        self.set(f"versions.{version_index}.input_directory", directory, auto_save)

    def get_output_directory(self, version_index: Optional[int] = None) -> str:
        """获取输出目录"""
        if version_index is None:
            version_index = self.current_version_index
        return self.get(f"versions.{version_index}.output_directory", "")

    def set_output_directory(self, directory: str, version_index: Optional[int] = None, auto_save: bool = True):
        """设置输出目录"""
        if version_index is None:
            version_index = self.current_version_index
        self.set(f"versions.{version_index}.output_directory", directory, auto_save)

    def get_version_config(self, version_index: int) -> Dict[str, str]:
        """获取指定版本的配置"""
        if 0 <= version_index <= 9:
            return {
                "input_directory": self.get(f"versions.{version_index}.input_directory", ""),
                "output_directory": self.get(f"versions.{version_index}.output_directory", "")
            }
        return self._version_config_template.copy()

    def set_version_config(self, version_index: int, input_dir: str, output_dir: str, auto_save: bool = True):
        """设置指定版本的配置"""
        if 0 <= version_index <= 9:
            self.set(f"versions.{version_index}.input_directory", input_dir, auto_save)
            self.set(f"versions.{version_index}.output_directory", output_dir, auto_save)

    def get_all_versions_info(self) -> Dict[int, Dict[str, str]]:
        """获取所有版本的信息概览"""
        versions_info = {}
        for i in range(10):
            config = self.get_version_config(i)
            versions_info[i] = {
                "input_directory": config["input_directory"],
                "output_directory": config["output_directory"],
                "has_config": bool(config["input_directory"] and config["output_directory"])
            }
        return versions_info

    def get_scan_filters(self) -> Dict[str, Any]:
        """获取扫描过滤器配置"""
        return self.get("scan_filters", self._default_config["scan_filters"])

    def get_ui_theme(self) -> Dict[str, str]:
        """获取UI主题配置"""
        return self.get("ui_theme", self._default_config["ui_theme"])

    def set_ui_theme(self, appearance_mode: str = None, color_theme: str = None, auto_save: bool = True):
        """设置UI主题"""
        if appearance_mode is not None:
            self.set("ui_theme.appearance_mode", appearance_mode, False)
        if color_theme is not None:
            self.set("ui_theme.color_theme", color_theme, False)

        if auto_save:
            self.save_config()
