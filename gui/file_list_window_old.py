# -*- coding: utf-8 -*-
"""
文件列表窗口
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
from typing import List, TYPE_CHECKING

from ..core.file_comparator import FileChange, ChangeType

if TYPE_CHECKING:
    from .main_window import IncrementalPackerApp

class FileListWindow:
    """文件列表窗口"""
    
    def __init__(self, parent, app: 'IncrementalPackerApp'):
        """
        初始化文件列表窗口
        
        Args:
            parent: 父窗口
            app: 主应用实例
        """
        self.app = app
        self.changes: List[FileChange] = []
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("文件变更列表")
        self.window.geometry("800x600")
        self.window.transient(parent)
        
        self._setup_ui()
        self._setup_events()
    
    def _setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text="文件变更列表",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        # 统计信息
        self.stats_label = ctk.CTkLabel(main_frame, text="")
        self.stats_label.pack(pady=5)
        
        # 过滤框架
        filter_frame = ctk.CTkFrame(main_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(filter_frame, text="过滤:").pack(side="left", padx=5)
        
        self.filter_var = tk.StringVar(value="all")
        
        # 过滤按钮
        ctk.CTkRadioButton(
            filter_frame, text="全部", variable=self.filter_var, value="all",
            command=self._apply_filter
        ).pack(side="left", padx=5)
        
        ctk.CTkRadioButton(
            filter_frame, text="新增", variable=self.filter_var, value="added",
            command=self._apply_filter
        ).pack(side="left", padx=5)
        
        ctk.CTkRadioButton(
            filter_frame, text="修改", variable=self.filter_var, value="modified",
            command=self._apply_filter
        ).pack(side="left", padx=5)
        
        ctk.CTkRadioButton(
            filter_frame, text="删除", variable=self.filter_var, value="deleted",
            command=self._apply_filter
        ).pack(side="left", padx=5)
        
        # 文件列表框架
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 创建树状表格
        columns = ("状态", "文件路径", "大小变化", "修改时间")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 设置列标题
        self.tree.heading("状态", text="状态")
        self.tree.heading("文件路径", text="文件路径")
        self.tree.heading("大小变化", text="大小变化")
        self.tree.heading("修改时间", text="修改时间")
        
        # 设置列宽度
        self.tree.column("状态", width=80, anchor="center")
        self.tree.column("文件路径", width=400, anchor="w")
        self.tree.column("大小变化", width=120, anchor="center")
        self.tree.column("修改时间", width=150, anchor="center")
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # 操作按钮框架
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        self.view_diff_btn = ctk.CTkButton(
            button_frame,
            text="查看差异",
            command=self._view_selected_diff,
            state="disabled"
        )
        self.view_diff_btn.pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="关闭",
            command=self.window.destroy
        ).pack(side="right", padx=5)
    
    def _setup_events(self):
        """设置事件处理"""
        # 双击事件
        self.tree.bind("<Double-1>", self._on_double_click)
        
        # 选择事件
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)
    
    def show_changes(self, changes: List[FileChange]):
        """
        显示文件变更
        
        Args:
            changes: 文件变更列表
        """
        self.changes = changes
        self._update_stats()
        self._populate_tree()
        
        # 显示窗口
        self.window.deiconify()
        self.window.focus()
    
    def _update_stats(self):
        """更新统计信息"""
        added_count = len([c for c in self.changes if c.change_type == ChangeType.ADDED])
        modified_count = len([c for c in self.changes if c.change_type == ChangeType.MODIFIED])
        deleted_count = len([c for c in self.changes if c.change_type == ChangeType.DELETED])
        
        stats_text = f"总计: {len(self.changes)} 个变化 | "
        stats_text += f"新增: {added_count} | 修改: {modified_count} | 删除: {deleted_count}"
        
        self.stats_label.configure(text=stats_text)
    
    def _populate_tree(self):
        """填充树状表格"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 根据过滤条件获取数据
        filtered_changes = self._get_filtered_changes()
        
        # 添加数据
        for change in filtered_changes:
            status_text = self._get_status_text(change.change_type)
            size_change = self._get_size_change_text(change)
            mtime_text = self._get_mtime_text(change)
            
            item_id = self.tree.insert("", "end", values=(
                status_text,
                change.file_path,
                size_change,
                mtime_text
            ))
            
            # 设置项目标签（用于存储change对象）
            self.tree.set(item_id, "#0", "")
            self.tree.item(item_id, tags=(change.change_type.value,))
        
        # 设置行颜色
        self.tree.tag_configure("added", background="#e8f5e8")
        self.tree.tag_configure("modified", background="#fff8dc")
        self.tree.tag_configure("deleted", background="#ffe8e8")
    
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
        if change_type == ChangeType.ADDED:
            return "新增"
        elif change_type == ChangeType.MODIFIED:
            return "修改"
        elif change_type == ChangeType.DELETED:
            return "删除"
        else:
            return "未知"
    
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
    
    def _get_mtime_text(self, change: FileChange) -> str:
        """获取修改时间文本"""
        if change.change_type == ChangeType.ADDED and change.new_mtime:
            return self._format_time(change.new_mtime)
        elif change.change_type == ChangeType.MODIFIED and change.new_mtime:
            return self._format_time(change.new_mtime)
        elif change.change_type == ChangeType.DELETED and change.old_mtime:
            return self._format_time(change.old_mtime)
        return "-"
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes is None:
            return "-"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    def _format_time(self, timestamp: float) -> str:
        """格式化时间戳"""
        try:
            import datetime
            dt = datetime.datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return "-"
    
    def _apply_filter(self):
        """应用过滤"""
        self._populate_tree()
    
    def _on_selection_changed(self, event):
        """选择改变事件"""
        selection = self.tree.selection()
        if selection:
            self.view_diff_btn.configure(state="normal")
        else:
            self.view_diff_btn.configure(state="disabled")
    
    def _on_double_click(self, event):
        """双击事件"""
        self._view_selected_diff()
    
    def _view_selected_diff(self):
        """查看选中文件的差异"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # 获取选中项的信息
        item_id = selection[0]
        values = self.tree.item(item_id, "values")
        tags = self.tree.item(item_id, "tags")
        
        if not values or not tags:
            return
        
        file_path = values[1]
        change_type_str = tags[0]
        
        # 转换变更类型
        change_type = ChangeType(change_type_str)
        
        # 显示差异
        self.app.show_file_diff(file_path, change_type)
