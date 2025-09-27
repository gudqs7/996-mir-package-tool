# -*- coding: utf-8 -*-
"""
双列文件变更查看窗口
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import customtkinter as ctk
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING
import difflib
import zipfile
from datetime import datetime

from core.file_comparator import FileChange, ChangeType

if TYPE_CHECKING:
    from .main_window import IncrementalPackerApp

class FileListWindow:
    """双列文件变更查看窗口"""
    
    def __init__(self, parent, app: 'IncrementalPackerApp'):
        """
        初始化文件列表窗口
        
        Args:
            parent: 父窗口
            app: 主应用实例
        """
        self.app = app
        self.changes: List[FileChange] = []
        self.selected_change: Optional[FileChange] = None
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("文件变更详情")
        self.window.geometry("1200x800")
        self.window.transient(parent)
        
        self._setup_ui()
        self._setup_events()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题区域
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="文件变更详情",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)
        
        # 统计信息
        self.stats_label = ctk.CTkLabel(title_frame, text="")
        self.stats_label.pack(side="right", padx=10, pady=10)
        
        # 主内容区域（双列布局）
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 左侧文件列表
        self._setup_file_list(content_frame)
        
        # 分隔符
        separator = ttk.Separator(content_frame, orient="vertical")
        separator.pack(side="left", fill="y", padx=5)
        
        # 右侧差异显示
        self._setup_diff_view(content_frame)
        
        # 底部按钮区域
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="刷新",
            command=self._refresh_diff,
            width=80
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="关闭",
            command=self.window.destroy,
            width=80
        ).pack(side="right", padx=5)
    
    def _setup_file_list(self, parent):
        """设置左侧文件列表"""
        left_frame = ctk.CTkFrame(parent)
        left_frame.pack(side="left", fill="both", expand=False, padx=5, pady=5)
        left_frame.configure(width=400)
        
        # 列表标题
        list_title = ctk.CTkLabel(
            left_frame,
            text="变更文件列表",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_title.pack(pady=(10, 5))
        
        # 过滤框架
        filter_frame = ctk.CTkFrame(left_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="过滤:").pack(side="left", padx=5)
        
        self.filter_var = tk.StringVar(value="all")
        
        # 过滤选项
        filter_options = [
            ("全部", "all"),
            ("新增", "added"),
            ("修改", "modified"),
            ("删除", "deleted")
        ]
        
        for text, value in filter_options:
            ctk.CTkRadioButton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                command=self._apply_filter
            ).pack(side="left", padx=5)
        
        # 文件列表框
        list_frame = ctk.CTkFrame(left_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建树状表格
        columns = ("状态", "文件名", "大小")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=20)
        
        # 设置列标题和宽度
        self.tree.heading("状态", text="状态")
        self.tree.heading("文件名", text="文件名")
        self.tree.heading("大小", text="大小变化")
        
        self.tree.column("状态", width=60, anchor="center")
        self.tree.column("文件名", width=250, anchor="w")
        self.tree.column("大小", width=80, anchor="center")
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar_y.set)
        
        # 布局
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar_y.pack(side="right", fill="y")
        
        # 阻止左侧框架收缩
        left_frame.pack_propagate(False)
    
    def _setup_diff_view(self, parent):
        """设置右侧差异显示"""
        right_frame = ctk.CTkFrame(parent)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)
        
        # 差异显示标题
        diff_title_frame = ctk.CTkFrame(right_frame)
        diff_title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.diff_title_label = ctk.CTkLabel(
            diff_title_frame,
            text="内容对比",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.diff_title_label.pack(side="left", padx=10, pady=5)
        
        self.file_path_label = ctk.CTkLabel(
            diff_title_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.file_path_label.pack(side="left", padx=10, pady=5)
        
        # 差异显示区域
        diff_frame = ctk.CTkFrame(right_frame)
        diff_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建文本框显示差异
        self.diff_text = scrolledtext.ScrolledText(
            diff_frame,
            wrap=tk.NONE,
            font=("Consolas", 10),
            bg="#ffffff",  # 白色背景
            fg="#000000",  # 黑色文字
            insertbackground="black",
            selectbackground="#0078d4",
            state="disabled",
            height=25
        )
        self.diff_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # 设置文本标签样式（类似VSCode的git diff）
        self._setup_text_tags()
        
        # 默认显示提示信息
        self._show_default_message()
    
    def _setup_text_tags(self):
        """设置文本标签样式"""
        # 添加行标记
        self.diff_text.tag_configure("added", background="#e6ffed", foreground="#22863a")
        self.diff_text.tag_configure("removed", background="#ffeef0", foreground="#d73a49")
        self.diff_text.tag_configure("context", background="#ffffff", foreground="#586069")
        self.diff_text.tag_configure("header", background="#f1f8ff", foreground="#0366d6", font=("Consolas", 10, "bold"))
        self.diff_text.tag_configure("info", background="#fff5b4", foreground="#735c0f")
        self.diff_text.tag_configure("line_number", background="#fafbfc", foreground="#586069", font=("Consolas", 9))
    
    def _setup_events(self):
        """设置事件处理"""
        # 选择事件
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
        
        # 双击事件
        self.tree.bind("<Double-1>", self._on_double_click)
    
    def show_changes(self, changes: List[FileChange]):
        """
        显示文件变更
        
        Args:
            changes: 文件变更列表
        """
        self.changes = changes
        self._update_stats()
        self._populate_tree()
        self._show_default_message()
        
        # 显示窗口
        self.window.deiconify()
        self.window.focus()
    
    def _update_stats(self):
        """更新统计信息"""
        added_count = len([c for c in self.changes if c.change_type == ChangeType.ADDED])
        modified_count = len([c for c in self.changes if c.change_type == ChangeType.MODIFIED])
        deleted_count = len([c for c in self.changes if c.change_type == ChangeType.DELETED])
        
        stats_text = f"新增: {added_count} | 修改: {modified_count} | 删除: {deleted_count}"
        self.stats_label.configure(text=stats_text)
    
    def _populate_tree(self):
        """填充文件列表"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 根据过滤条件获取数据
        filtered_changes = self._get_filtered_changes()
        
        # 添加数据
        for change in filtered_changes:
            status_text = self._get_status_text(change.change_type)
            size_change = self._get_size_change_text(change)
            file_name = Path(change.file_path).name
            
            item_id = self.tree.insert("", "end", values=(
                status_text,
                file_name,
                size_change
            ))
            
            # 存储完整的change对象
            self.tree.set(item_id, "#0", change.file_path)
        
        # 如果有项目，默认选择第一个
        items = self.tree.get_children()
        if items:
            self.tree.selection_set(items[0])
            self._on_selection_changed(None)
    
    def _get_filtered_changes(self) -> List[FileChange]:
        """获取过滤后的变更列表"""
        filter_type = self.filter_var.get()
        
        if filter_type == "all":
            return self.changes
        elif filter_type == "added":
            return [c for c in self.changes if c.change_type == ChangeType.ADDED]
        elif filter_type == "modified":
            return [c for c in self.changes if c.change_type == ChangeType.MODIFIED]
        elif filter_type == "deleted":
            return [c for c in self.changes if c.change_type == ChangeType.DELETED]
        else:
            return self.changes
    
    def _get_status_text(self, change_type: ChangeType) -> str:
        """获取状态文本"""
        status_map = {
            ChangeType.ADDED: "新增",
            ChangeType.MODIFIED: "修改",
            ChangeType.DELETED: "删除"
        }
        return status_map.get(change_type, "未知")
    
    def _get_size_change_text(self, change: FileChange) -> str:
        """获取大小变化文本"""
        if change.change_type == ChangeType.ADDED:
            return self._format_size(change.new_size) if change.new_size else "-"
        elif change.change_type == ChangeType.DELETED:
            return f"-{self._format_size(change.old_size)}" if change.old_size else "-"
        elif change.change_type == ChangeType.MODIFIED:
            if change.old_size is not None and change.new_size is not None:
                diff = change.new_size - change.old_size
                if diff > 0:
                    return f"+{self._format_size(diff)}"
                elif diff < 0:
                    return f"-{self._format_size(-diff)}"
                else:
                    return "无变化"
        return "-"
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes is None:
            return "-"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
    
    def _apply_filter(self):
        """应用过滤"""
        self._populate_tree()
    
    def _on_selection_changed(self, event):
        """选择改变事件"""
        selection = self.tree.selection()
        if not selection:
            self._show_default_message()
            return
        
        # 获取选中项的文件路径
        item_id = selection[0]
        file_path = self.tree.set(item_id, "#0")
        
        # 找到对应的FileChange对象
        selected_change = None
        for change in self.changes:
            if change.file_path == file_path:
                selected_change = change
                break
        
        if selected_change:
            self.selected_change = selected_change
            self._show_file_diff(selected_change)
    
    def _on_double_click(self, event):
        """双击事件"""
        # 双击时展开/折叠树节点或执行其他操作
        pass
    
    def _show_default_message(self):
        """显示默认提示信息"""
        self.diff_text.config(state="normal")
        self.diff_text.delete(1.0, tk.END)
        
        self.file_path_label.configure(text="")
        
        message = "请在左侧选择一个文件查看变更详情\\n\\n"
        message += "说明:\\n"
        message += "• 绿色背景：新增的内容\\n"
        message += "• 红色背景：删除的内容\\n"
        message += "• 蓝色背景：文件头信息\\n"
        message += "• 黄色背景：重要提示信息"
        
        self.diff_text.insert(1.0, message)
        self.diff_text.tag_add("info", 1.0, tk.END)
        self.diff_text.config(state="disabled")
    
    def _show_file_diff(self, change: FileChange):
        """显示文件差异"""
        self.file_path_label.configure(text=f"文件: {change.file_path}")
        
        self.diff_text.config(state="normal")
        self.diff_text.delete(1.0, tk.END)
        
        if change.change_type == ChangeType.ADDED:
            self._show_added_file(change)
        elif change.change_type == ChangeType.DELETED:
            self._show_deleted_file(change)
        elif change.change_type == ChangeType.MODIFIED:
            self._show_modified_file(change)
        
        self.diff_text.config(state="disabled")
    
    def _show_added_file(self, change: FileChange):
        """显示新增文件"""
        current_file = Path(self.app.input_dir.get()) / change.file_path
        
        # 插入文件头
        header = f"=== 新增文件: {change.file_path} ===\\n"
        self.diff_text.insert(tk.END, header)
        self.diff_text.tag_add("header", "end-2l", "end-1l")
        
        if not current_file.exists():
            self.diff_text.insert(tk.END, "文件不存在\\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return
        
        if not self._is_text_file(current_file):
            self.diff_text.insert(tk.END, "二进制文件，无法显示内容\\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return
        
        try:
            content = self._read_file_content(current_file)
            if content is None:
                return
            
            # 显示内容（所有行都标记为添加）
            for i, line in enumerate(content.splitlines(), 1):
                line_text = f"+{i:4d} | {line}\\n"
                self.diff_text.insert(tk.END, line_text)
                self.diff_text.tag_add("added", "end-2l", "end-1l")
                
        except Exception as e:
            error_msg = f"读取文件失败: {e}\\n"
            self.diff_text.insert(tk.END, error_msg)
            self.diff_text.tag_add("info", "end-2l", "end-1l")
    
    def _show_deleted_file(self, change: FileChange):
        """显示删除文件"""
        # 插入文件头
        header = f"=== 删除文件: {change.file_path} ===\\n"
        self.diff_text.insert(tk.END, header)
        self.diff_text.tag_add("header", "end-2l", "end-1l")
        
        # 尝试从之前的zip包中获取文件内容
        old_content = self._get_file_from_previous_version(change.file_path)
        
        if old_content is None:
            self.diff_text.insert(tk.END, "无法获取文件的历史版本内容\\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return
        
        # 显示删除的内容
        for i, line in enumerate(old_content.splitlines(), 1):
            line_text = f"-{i:4d} | {line}\\n"
            self.diff_text.insert(tk.END, line_text)
            self.diff_text.tag_add("removed", "end-2l", "end-1l")
    
    def _show_modified_file(self, change: FileChange):
        """显示修改文件"""
        current_file = Path(self.app.input_dir.get()) / change.file_path
        
        # 插入文件头
        header = f"=== 修改文件: {change.file_path} ===\\n"
        self.diff_text.insert(tk.END, header)
        self.diff_text.tag_add("header", "end-2l", "end-1l")
        
        if not current_file.exists():
            self.diff_text.insert(tk.END, "当前文件不存在\\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return
        
        if not self._is_text_file(current_file):
            self.diff_text.insert(tk.END, "二进制文件，无法显示内容差异\\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return
        
        # 获取当前文件内容
        current_content = self._read_file_content(current_file)
        if current_content is None:
            return
        
        # 获取历史版本内容
        old_content = self._get_file_from_previous_version(change.file_path)
        if old_content is None:
            self.diff_text.insert(tk.END, "无法获取文件的历史版本，显示当前内容：\\n\\n")
            self.diff_text.tag_add("info", "end-3l", "end-1l")
            
            for i, line in enumerate(current_content.splitlines(), 1):
                line_text = f" {i:4d} | {line}\\n"
                self.diff_text.insert(tk.END, line_text)
                self.diff_text.tag_add("context", "end-2l", "end-1l")
            return
        
        # 生成差异
        self._show_unified_diff(old_content, current_content, change.file_path)
    
    def _show_unified_diff(self, old_content: str, new_content: str, file_path: str):
        """显示统一格式的差异"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"旧版本/{file_path}",
            tofile=f"新版本/{file_path}",
            lineterm=""
        )
        
        for line in diff:
            if line.startswith("+++") or line.startswith("---"):
                self.diff_text.insert(tk.END, line + "\\n")
                self.diff_text.tag_add("header", "end-2l", "end-1l")
            elif line.startswith("@@"):
                self.diff_text.insert(tk.END, line + "\\n")
                self.diff_text.tag_add("info", "end-2l", "end-1l")
            elif line.startswith("+"):
                self.diff_text.insert(tk.END, line + "\\n")
                self.diff_text.tag_add("added", "end-2l", "end-1l")
            elif line.startswith("-"):
                self.diff_text.insert(tk.END, line + "\\n")
                self.diff_text.tag_add("removed", "end-2l", "end-1l")
            else:
                self.diff_text.insert(tk.END, line + "\\n")
                self.diff_text.tag_add("context", "end-2l", "end-1l")
    
    def _get_file_from_previous_version(self, file_path: str) -> Optional[str]:
        """从上个版本的zip包中获取文件内容"""
        if not self.app.version_manager:
            return None
        
        # 获取版本历史
        versions = self.app.version_manager.get_versions()
        if not versions:
            return None
        
        # 在输出目录中查找zip文件
        output_dir = Path(self.app.output_dir.get())
        
        for version_info in versions:
            zip_file_path = output_dir / f"{version_info.version}.zip"
            if zip_file_path.exists():
                try:
                    with zipfile.ZipFile(zip_file_path, 'r') as zf:
                        if file_path in zf.namelist():
                            content = zf.read(file_path).decode('utf-8', errors='ignore')
                            return content
                except (zipfile.BadZipFile, UnicodeDecodeError, KeyError):
                    continue
        
        return None
    
    def _is_text_file(self, file_path: Path) -> bool:
        """判断是否为文本文件"""
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.xml', '.json',
            '.ini', '.cfg', '.conf', '.log', '.csv', '.sql', '.sh', '.bat',
            '.yml', '.yaml', '.toml', '.properties'
        }
        
        if file_path.suffix.lower() in text_extensions:
            return True
        
        # 尝试读取文件开头判断
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(8192)
                # 检查是否包含null字节
                if b'\\0' in sample:
                    return False
                # 尝试解码
                sample.decode('utf-8')
                return True
        except (UnicodeDecodeError, IOError):
            return False
    
    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except IOError as e:
            error_msg = f"读取文件失败: {e}\\n"
            self.diff_text.insert(tk.END, error_msg)
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return None
    
    def _refresh_diff(self):
        """刷新差异显示"""
        if self.selected_change:
            self._show_file_diff(self.selected_change)