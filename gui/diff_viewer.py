# -*- coding: utf-8 -*-
"""
文件差异查看器
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import customtkinter as ctk
from pathlib import Path
from typing import List, Optional
import difflib
from datetime import datetime

from ..core.file_comparator import ChangeType

class DiffViewer:
    """文件差异查看器"""
    
    def __init__(self, parent):
        """
        初始化差异查看器
        
        Args:
            parent: 父窗口
        """
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("文件差异查看")
        self.window.geometry("1000x700")
        self.window.transient(parent)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题区域
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="文件差异查看",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.pack(side="left", padx=10, pady=10)
        
        # 文件信息区域
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="x", padx=10, pady=5)
        
        self.file_info_label = ctk.CTkLabel(info_frame, text="", anchor="w")
        self.file_info_label.pack(fill="x", padx=10, pady=5)
        
        # 差异显示区域
        diff_frame = ctk.CTkFrame(main_frame)
        diff_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建文本框
        self.text_widget = scrolledtext.ScrolledText(
            diff_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="white",
            selectbackground="#264f78",
            state="disabled"
        )
        self.text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 设置文本颜色标签
        self._setup_text_tags()
        
        # 按钮区域
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="关闭",
            command=self.window.destroy
        ).pack(side="right", padx=10, pady=5)
    
    def _setup_text_tags(self):
        """设置文本标签样式"""
        # 添加行样式
        self.text_widget.tag_configure("added", background="#1e4f1e", foreground="#4dff4d")
        self.text_widget.tag_configure("removed", background="#4f1e1e", foreground="#ff4d4d")
        self.text_widget.tag_configure("context", background="#1e1e1e", foreground="#d4d4d4")
        self.text_widget.tag_configure("info", background="#1e1e1e", foreground="#9cdcfe")
        self.text_widget.tag_configure("header", background="#264f78", foreground="#ffffff", font=("Consolas", 10, "bold"))
    
    def show_diff(self, file_path: str, change_type: ChangeType, base_dir: str):
        """
        显示文件差异
        
        Args:
            file_path: 文件相对路径
            change_type: 变更类型
            base_dir: 基础目录
        """
        self.window.title(f"文件差异查看 - {file_path}")
        
        # 更新文件信息
        self._update_file_info(file_path, change_type)
        
        # 清空文本内容
        self.text_widget.config(state="normal")
        self.text_widget.delete(1.0, tk.END)
        
        if change_type == ChangeType.ADDED:
            self._show_added_file(file_path, base_dir)
        elif change_type == ChangeType.DELETED:
            self._show_deleted_file(file_path)
        elif change_type == ChangeType.MODIFIED:
            self._show_modified_file(file_path, base_dir)
        
        self.text_widget.config(state="disabled")
        
        # 显示窗口
        self.window.deiconify()
        self.window.focus()
    
    def _update_file_info(self, file_path: str, change_type: ChangeType):
        """更新文件信息"""
        change_text = {
            ChangeType.ADDED: "新增文件",
            ChangeType.MODIFIED: "修改文件",
            ChangeType.DELETED: "删除文件"
        }.get(change_type, "未知操作")
        
        info_text = f"文件: {file_path} | 状态: {change_text}"
        self.file_info_label.configure(text=info_text)
    
    def _show_added_file(self, file_path: str, base_dir: str):
        """显示新增文件内容"""
        current_file = Path(base_dir) / file_path
        
        if not current_file.exists():
            self._insert_text("文件不存在", "info")
            return
        
        if not self._is_text_file(current_file):
            self._insert_text("二进制文件，无法显示内容", "info")
            return
        
        try:
            content = self._read_file_content(current_file)
            if content is None:
                return
            
            # 显示文件头
            self._insert_text(f"=== 新增文件: {file_path} ===\n", "header")
            
            # 显示内容（所有行都标记为添加）
            for i, line in enumerate(content.splitlines(), 1):
                self._insert_text(f"+{i:4d}: {line}\n", "added")
                
        except Exception as e:
            self._insert_text(f"读取文件失败: {e}", "info")
    
    def _show_deleted_file(self, file_path: str):
        """显示删除文件信息"""
        self._insert_text(f"=== 删除文件: {file_path} ===\n", "header")
        self._insert_text("文件已被删除，无法显示内容", "info")
    
    def _show_modified_file(self, file_path: str, base_dir: str):
        """显示修改文件的差异"""
        current_file = Path(base_dir) / file_path
        
        if not current_file.exists():
            self._insert_text("当前文件不存在", "info")
            return
        
        if not self._is_text_file(current_file):
            self._insert_text("二进制文件，无法显示内容差异", "info")
            return
        
        # 读取当前文件内容
        current_content = self._read_file_content(current_file)
        if current_content is None:
            return
        
        # 由于没有保存原始文件内容，只能显示当前内容
        self._insert_text(f"=== 修改文件: {file_path} ===\n", "header")
        self._insert_text("注意: 由于未保存原始文件内容，只能显示当前文件内容\n\n", "info")
        
        # 显示当前内容
        for i, line in enumerate(current_content.splitlines(), 1):
            self._insert_text(f"{i:4d}: {line}\n", "context")
    
    def _is_text_file(self, file_path: Path) -> bool:
        """判断是否为文本文件"""
        text_extensions = {
            '.txt', '.py', '.js', '.html', '.css', '.xml', '.json', '.yaml', '.yml',
            '.md', '.rst', '.ini', '.cfg', '.conf', '.sh', '.bat', '.ps1',
            '.c', '.cpp', '.h', '.hpp', '.java', '.cs', '.php', '.rb', '.go',
            '.sql', '.log', '.csv', '.tsv', '.jsx', '.tsx', '.vue', '.scss', '.less'
        }
        
        return file_path.suffix.lower() in text_extensions
    
    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """读取文件内容"""
        # 检查文件大小（限制为1MB）
        if file_path.stat().st_size > 1024 * 1024:
            self._insert_text("文件太大（>1MB），无法显示内容", "info")
            return None
        
        try:
            # 尝试UTF-8编码
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                # 尝试GBK编码
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except UnicodeDecodeError:
                self._insert_text("文件编码不支持，无法显示内容", "info")
                return None
        except Exception as e:
            self._insert_text(f"读取文件失败: {e}", "info")
            return None
    
    def _insert_text(self, text: str, tag: str):
        """插入文本并应用标签"""
        start_pos = self.text_widget.index(tk.INSERT)
        self.text_widget.insert(tk.INSERT, text)
        end_pos = self.text_widget.index(tk.INSERT)
        self.text_widget.tag_add(tag, start_pos, end_pos)
