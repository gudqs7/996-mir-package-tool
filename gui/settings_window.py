# -*- coding: utf-8 -*-
"""
设置窗口
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from typing import TYPE_CHECKING, Set

if TYPE_CHECKING:
    from .main_window import IncrementalPackerApp

class SettingsWindow:
    """设置窗口"""
    
    def __init__(self, parent, app: 'IncrementalPackerApp'):
        """
        初始化设置窗口
        
        Args:
            parent: 父窗口
            app: 主应用实例
        """
        self.app = app
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.window.geometry("500x400")
        self.window.transient(parent)
        
        # 设置变量
        self.exclude_extensions = tk.StringVar()
        self.max_file_size = tk.StringVar()
        self.thread_count = tk.StringVar()
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text="设置",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 20))
        
        # 排除文件类型设置
        self._create_exclude_section(main_frame)
        
        # 性能设置
        self._create_performance_section(main_frame)
        
        # 其他设置
        self._create_other_section(main_frame)
        
        # 按钮区域
        self._create_button_section(main_frame)
    
    def _create_exclude_section(self, parent):
        """创建排除文件设置区域"""
        exclude_frame = ctk.CTkFrame(parent)
        exclude_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            exclude_frame,
            text="排除文件类型",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            exclude_frame,
            text="输入需要排除的文件扩展名，用逗号分隔（如: .dll,.exe,.json）",
            anchor="w"
        ).pack(anchor="w", padx=10, pady=2)
        
        self.exclude_entry = ctk.CTkEntry(
            exclude_frame,
            textvariable=self.exclude_extensions,
            height=35,
            placeholder_text=".dll,.exe,.json"
        )
        self.exclude_entry.pack(fill="x", padx=10, pady=(5, 10))
    
    def _create_performance_section(self, parent):
        """创建性能设置区域"""
        perf_frame = ctk.CTkFrame(parent)
        perf_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            perf_frame,
            text="性能设置",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 最大文件大小
        size_frame = ctk.CTkFrame(perf_frame)
        size_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            size_frame,
            text="显示差异的最大文件大小 (MB):",
            width=200
        ).pack(side="left", padx=5)
        
        self.size_entry = ctk.CTkEntry(
            size_frame,
            textvariable=self.max_file_size,
            width=100,
            placeholder_text="1"
        )
        self.size_entry.pack(side="left", padx=5)
        
        # 线程数
        thread_frame = ctk.CTkFrame(perf_frame)
        thread_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkLabel(
            thread_frame,
            text="最大线程数:",
            width=200
        ).pack(side="left", padx=5)
        
        self.thread_entry = ctk.CTkEntry(
            thread_frame,
            textvariable=self.thread_count,
            width=100,
            placeholder_text="8"
        )
        self.thread_entry.pack(side="left", padx=5)
    
    def _create_other_section(self, parent):
        """创建其他设置区域"""
        other_frame = ctk.CTkFrame(parent)
        other_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            other_frame,
            text="其他设置",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # 主题设置
        theme_frame = ctk.CTkFrame(other_frame)
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(
            theme_frame,
            text="主题模式:",
            width=200
        ).pack(side="left", padx=5)
        
        self.theme_var = tk.StringVar(value="system")
        self.theme_option = ctk.CTkOptionMenu(
            theme_frame,
            variable=self.theme_var,
            values=["system", "light", "dark"],
            command=self._change_theme
        )
        self.theme_option.pack(side="left", padx=5)
        
        # 缓存管理
        cache_frame = ctk.CTkFrame(other_frame)
        cache_frame.pack(fill="x", padx=10, pady=(5, 10))
        
        ctk.CTkButton(
            cache_frame,
            text="清理缓存",
            command=self._clear_cache,
            fg_color="orange",
            hover_color="dark orange"
        ).pack(side="left", padx=10, pady=5)
        
        ctk.CTkLabel(
            cache_frame,
            text="清理所有版本缓存数据",
            anchor="w"
        ).pack(side="left", padx=10)
    
    def _create_button_section(self, parent):
        """创建按钮区域"""
        button_frame = ctk.CTkFrame(parent)
        button_frame.pack(fill="x", side="bottom", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame,
            text="保存",
            command=self._save_settings
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="取消",
            command=self.window.destroy
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="重置默认值",
            command=self._reset_defaults,
            fg_color="gray",
            hover_color="dark gray"
        ).pack(side="right", padx=5)
    
    def _load_settings(self):
        """加载设置"""
        # 从文件扫描器获取当前设置
        exclude_exts = ",".join(sorted(self.app.file_scanner.exclude_extensions))
        self.exclude_extensions.set(exclude_exts)
        
        # 设置默认值
        max_size_mb = self.app.file_comparator.max_file_size_for_diff / (1024 * 1024)
        self.max_file_size.set(str(int(max_size_mb)))
        
        self.thread_count.set("8")
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 解析排除文件类型
            exclude_text = self.exclude_extensions.get().strip()
            if exclude_text:
                exclude_set = set()
                for ext in exclude_text.split(","):
                    ext = ext.strip()
                    if ext and not ext.startswith("."):
                        ext = "." + ext
                    if ext:
                        exclude_set.add(ext.lower())
                self.app.file_scanner.exclude_extensions = exclude_set
            
            # 解析最大文件大小
            max_size_text = self.max_file_size.get().strip()
            if max_size_text:
                max_size_mb = float(max_size_text)
                if max_size_mb > 0:
                    self.app.file_comparator.max_file_size_for_diff = int(max_size_mb * 1024 * 1024)
            
            messagebox.showinfo("成功", "设置已保存")
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("错误", f"设置值无效: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}")
    
    def _reset_defaults(self):
        """重置默认值"""
        if messagebox.askyesno("确认", "是否重置为默认设置？"):
            self.exclude_extensions.set(".dll,.exe,.json")
            self.max_file_size.set("1")
            self.thread_count.set("8")
            self.theme_var.set("system")
    
    def _change_theme(self, theme: str):
        """改变主题"""
        ctk.set_appearance_mode(theme)
    
    def _clear_cache(self):
        """清理缓存"""
        if messagebox.askyesno("确认", "是否清理所有缓存数据？\n这将删除所有版本历史和扫描结果。"):
            try:
                if self.app.version_manager:
                    self.app.version_manager.clear_cache()
                    # 重置应用状态
                    self.app.current_version.set("v1.0.0")
                    self.app.file_changes = []
                    self.app.current_file_info = {}
                    self.app.view_changes_btn.configure(state="disabled")
                    self.app.package_btn.configure(state="disabled")
                    self.app.full_btn.configure(state="disabled")
                    self.app.status_text.set("缓存已清理，请重新扫描文件")
                
                messagebox.showinfo("成功", "缓存已清理")
                
            except Exception as e:
                messagebox.showerror("错误", f"清理缓存失败: {e}")
