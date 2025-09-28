# -*- coding: utf-8 -*-
"""
主窗口
"""
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from core.config_manager import ConfigManager
from core.file_comparator import FileComparator, ChangeType
from core.file_scanner import FileScanner
from core.make_win_center import center_on_screen, set_win_icon, get_windows_scaling_simple
from core.package_builder import PackageBuilder
from core.version_manager import VersionManager
from gui.file_list_window import FileListWindow

# 在CustomTkinter中使用
scaling = get_windows_scaling_simple()

# 设置CustomTkinter缩放
# ctk.set_widget_scaling(scaling)  # 控件缩放
# ctk.set_window_scaling(scaling)  # 窗口缩放

# 设置主题
ctk.set_appearance_mode("Dark")  # 系统模式
ctk.set_default_color_theme("blue")  # 蓝色主题


class IncrementalPackerApp:
    """增量打包工具主窗口"""

    def __init__(self):
        """初始化应用"""
        self.root = ctk.CTk()
        set_win_icon(self.root)
        self.root.title("996三端母包和增量包工具 by 心累 工具群: 820247699")
        self.root.geometry("600x500")
        # 绑定事件，在窗口显示后自动居中
        center_on_screen(self.root)

        # 设置表格内容的字体
        style = ttk.Style()
        style.configure("Treeview",
                        font=("微软雅黑", 12),
                        rowheight=30)
        # 设置表头的字体
        style.configure("Treeview.Heading",
                        font=("微软雅黑", 14, "bold"),
                        rowheight=35)

        # 配置管理器（先初始化）
        self.config = ConfigManager()

        # 应用状态
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.current_version = tk.StringVar(value="v1.0.0")
        self.status_text = tk.StringVar(value="就绪")
        self.version_choice = tk.StringVar()  # 版本选择下拉框的值

        # 核心组件
        self.file_scanner = FileScanner()
        self.version_manager: Optional[VersionManager] = None
        self.package_builder = PackageBuilder()
        self.file_comparator = FileComparator()

        # 工作状态
        self.is_scanning = False
        self.is_building = False
        self.current_file_info = {}
        self.file_changes = []

        # 子窗口
        self.file_list_window: Optional[FileListWindow] = None
        self._setup_ui()

        # 加载保存的目录配置
        self._load_saved_directories()

        self._setup_events()

    def _setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 标题
        title_label = ctk.CTkLabel(
            main_frame,
            text="996服务端打包工具",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(10, 20))

        # 目录选择区域
        self._create_directory_section(main_frame)

        # 版本信息区域
        self._create_version_section(main_frame)

        # 操作按钮区域
        self._create_action_section(main_frame)

        # 进度区域
        self._create_progress_section(main_frame)

        # 状态栏
        self._create_status_section(main_frame)

    def _create_directory_section(self, parent):
        """创建目录选择区域"""
        dir_frame = ctk.CTkFrame(parent)
        dir_frame.pack(fill="x", padx=10, pady=5)

        # 版本选择区域
        version_select_frame = ctk.CTkFrame(dir_frame)
        version_select_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(version_select_frame, text="版本配置:", width=80).pack(side="left", padx=5)

        # 版本下拉框
        version_options = [f"版本 {i + 1}" for i in range(10)]
        self.version_combobox = ctk.CTkComboBox(
            version_select_frame,
            values=version_options,
            variable=self.version_choice,
            width=120,
            command=self._on_version_changed
        )
        self.version_combobox.pack(side="left", padx=5)

        # 输入目录
        input_frame = ctk.CTkFrame(dir_frame)
        input_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(input_frame, text="输入目录:", width=80).pack(side="left", padx=5)

        self.input_entry = ctk.CTkEntry(input_frame, textvariable=self.input_dir, height=35)
        self.input_entry.pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(
            input_frame,
            text="选择",
            width=80,
            command=self._select_input_dir
        ).pack(side="right", padx=5)

        # 输出目录
        output_frame = ctk.CTkFrame(dir_frame)
        output_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(output_frame, text="输出目录:", width=80).pack(side="left", padx=5)

        self.output_entry = ctk.CTkEntry(output_frame, textvariable=self.output_dir, height=35)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(
            output_frame,
            text="选择",
            width=80,
            command=self._select_output_dir
        ).pack(side="right", padx=5)

    def _create_version_section(self, parent):
        """创建版本信息区域"""
        version_frame = ctk.CTkFrame(parent)
        version_frame.pack(fill="x", padx=10, pady=5)

        # 当前版本
        current_frame = ctk.CTkFrame(version_frame)
        current_frame.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        ctk.CTkLabel(current_frame, text="打包版本号:").pack(side="left", padx=5)
        self.version_label = ctk.CTkLabel(
            current_frame,
            textvariable=self.current_version,
            font=ctk.CTkFont(weight="bold")
        )
        self.version_label.pack(side="left", padx=5)

        # 版本历史按钮
        ctk.CTkButton(
            version_frame,
            text="版本历史",
            width=100,
            command=self._show_version_history
        ).pack(side="right", padx=5, pady=5)

    def _create_action_section(self, parent):
        """创建操作按钮区域"""
        action_frame = ctk.CTkFrame(parent)
        action_frame.pack(fill="x", padx=10, pady=10)

        # 第一行按钮
        row1_frame = ctk.CTkFrame(action_frame)
        row1_frame.pack(fill="x", padx=5, pady=5)

        self.scan_btn = ctk.CTkButton(
            row1_frame,
            text="扫描文件",
            width=120,
            command=self._start_scan
        )
        self.scan_btn.pack(side="left", padx=5)

        self.view_changes_btn = ctk.CTkButton(
            row1_frame,
            text="查看变更",
            width=120,
            command=self._view_file_changes,
            state="disabled"
        )
        self.view_changes_btn.pack(side="left", padx=5)

        # 第二行按钮
        row2_frame = ctk.CTkFrame(action_frame)
        row2_frame.pack(fill="x", padx=5, pady=5)

        self.package_btn = ctk.CTkButton(
            row2_frame,
            text="开始打包",
            width=120,
            command=self._start_package_auto,
            state="disabled"
        )
        self.package_btn.pack(side="left", padx=5)

        self.reset_btn = ctk.CTkButton(
            row2_frame,
            text="重置版本",
            width=120,
            command=self._reset_version,
            fg_color="orange",
            hover_color="dark orange"
        )
        self.reset_btn.pack(side="left", padx=5)

    def _create_progress_section(self, parent):
        """创建进度区域"""
        progress_frame = ctk.CTkFrame(parent)
        progress_frame.pack(fill="x", padx=10, pady=5)

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)

        # 进度文本
        self.progress_label = ctk.CTkLabel(progress_frame, text="")
        self.progress_label.pack(pady=5)

    def _create_status_section(self, parent):
        """创建状态区域"""
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", side="bottom", padx=10, pady=5)

        ctk.CTkLabel(
            status_frame,
            textvariable=self.status_text,
            anchor="w"
        ).pack(side="left", padx=10, pady=5)

    def _setup_events(self):
        """设置事件处理"""
        # 目录变更事件
        self.input_dir.trace('w', self._on_directory_changed)
        self.output_dir.trace('w', self._on_directory_changed)

        # 版本选择变更事件
        self.version_choice.trace('w', self._on_version_choice_changed)

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _select_input_dir(self):
        """选择输入目录"""
        directory = filedialog.askdirectory(title="选择输入目录")
        if directory:
            self.input_dir.set(directory)
            # 立即保存配置
            self._save_current_config()

    def _select_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir.set(directory)
            # 立即保存配置
            self._save_current_config()

    def _on_version_changed(self, selection):
        """版本下拉框选择变更处理"""
        # 获取选中的版本索引
        try:
            version_text = selection
            if "版本 " in version_text:
                version_index = int(version_text.split("版本 ")[1]) - 1
                if 0 <= version_index <= 9:
                    self._switch_to_version(version_index)
        except (ValueError, IndexError) as e:
            print(f"版本切换错误: {e}")

    def _on_version_choice_changed(self, *args):
        """版本选择变量变更处理"""
        choice = self.version_choice.get()
        if choice:
            self._on_version_changed(choice)

    def _switch_to_version(self, version_index: int):
        """切换到指定版本"""
        try:
            # 保存前一个版本的配置
            self._save_current_config()

            # 更新配置管理器的当前版本索引
            self.config.set_current_version_index(version_index)

            # 加载新版本的配置
            version_config = self.config.get_version_config(version_index)

            # 更新UI显示
            self.input_dir.set(version_config["input_directory"])
            self.output_dir.set(version_config["output_directory"])

            # 触发目录变更事件来更新其他组件
            self._on_directory_changed()
        except Exception as e:
            print(f"切换版本失败: {e}")
            self.status_text.set(f"切换版本失败: {e}")

    def _save_current_config(self):
        """保存当前版本的配置"""
        try:
            current_index = self.config.get_current_version_index()
            input_dir = self.input_dir.get()
            output_dir = self.output_dir.get()

            # 保存当前版本的配置
            self.config.set_version_config(current_index, input_dir, output_dir)

        except Exception as e:
            print(f"保存配置失败: {e}")

    def _on_directory_changed(self, *args):
        """目录变更事件处理"""
        # 保存配置
        self._save_current_config()
        self.view_changes_btn.configure(state="disabled")
        self.package_btn.configure(state="disabled")

        if self.input_dir.get() and self.output_dir.get():
            # 初始化版本管理器（使用输出目录下的cache）
            cache_dir = Path(self.output_dir.get()) / "cache"
            self.version_manager = VersionManager(cache_dir)

            # 初始化文件缓存管理器（使用输出目录下的cache）
            from core.file_cache_manager import FileCacheManager
            cache_manager = FileCacheManager.create_for_output_dir(Path(self.output_dir.get()))

            # 重新初始化打包构建器，传入新的缓存管理器
            self.package_builder = PackageBuilder(cache_manager)

            # 更新版本显示
            next_version = self.version_manager.get_next_version()
            self.current_version.set(next_version)

            # 启用扫描按钮
            self.scan_btn.configure(state="normal")
            self.reset_btn.configure(state="normal")
            self.status_text.set("就绪，请点击'扫描文件'开始")
        else:
            self.current_version.set("v1.0.0")
            self.scan_btn.configure(state="disabled")
            self.reset_btn.configure(state="disabled")
            self.status_text.set("请选择输入和输出目录")

    def _start_scan(self):
        """开始扫描文件"""
        if self.is_scanning:
            return

        input_path = Path(self.input_dir.get())
        if not input_path.exists():
            messagebox.showerror("错误", "输入目录不存在")
            return

        # 在扫描前保存配置
        self._save_current_config()

        self.is_scanning = True
        self.scan_btn.configure(text="停止扫描", command=self._stop_scan)
        self._disable_actions()

        # 在新线程中扫描
        threading.Thread(target=self._scan_files, daemon=True).start()

    def _stop_scan(self):
        """停止扫描"""
        self.file_scanner.stop_scan()
        self.status_text.set("正在停止扫描...")

    def _scan_files(self):
        """扫描文件（在子线程中执行）"""
        try:
            input_path = Path(self.input_dir.get())

            def progress_callback(current, total):
                progress = current / total if total > 0 else 0
                self.root.after(0, lambda: self.progress_bar.set(progress))
                self.root.after(0, lambda: self.progress_label.configure(
                    text=f"正在扫描: {current}/{total} 个文件"
                ))

            self.root.after(0, lambda: self.status_text.set("正在扫描文件..."))

            # 扫描文件
            file_info = self.file_scanner.scan_directory(input_path, progress_callback)

            if not file_info:  # 扫描被取消或失败
                self.root.after(0, self._on_scan_cancelled)
                return

            # 对比文件变化
            old_files = self.version_manager.get_latest_file_info()
            changes = self.file_comparator.compare_file_lists(old_files, file_info)

            # 更新UI
            self.root.after(0, lambda: self._on_scan_completed(file_info, changes))

        except Exception as e:
            self.root.after(0, lambda: self._on_scan_error(str(e)))

    def _on_scan_completed(self, file_info, changes):
        """扫描完成回调"""
        self.current_file_info = file_info
        self.file_changes = changes

        self.is_scanning = False
        self.scan_btn.configure(text="扫描文件", command=self._start_scan)
        self._enable_actions()

        # 更新进度
        self.progress_bar.set(1.0)

        # 更新状态
        change_count = len(changes)
        if change_count == 0:
            self.status_text.set("扫描完成，没有发现文件变化")
            self.progress_label.configure(text=f"扫描完成: 总计 {len(file_info)} 个文件，无变化")
        else:
            self.status_text.set(f"扫描完成，发现 {change_count} 个文件变化")
            self.progress_label.configure(text=f"扫描完成: 总计 {len(file_info)} 个文件，{change_count} 个变化")
            self.view_changes_btn.configure(state="normal")

    def _on_scan_cancelled(self):
        """扫描取消回调"""
        self.is_scanning = False
        self.scan_btn.configure(text="扫描文件", command=self._start_scan)
        self._enable_actions()

        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.status_text.set("扫描已取消")

    def _on_scan_error(self, error_msg):
        """扫描错误回调"""
        self.is_scanning = False
        self.scan_btn.configure(text="扫描文件", command=self._start_scan)
        self._enable_actions()

        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.status_text.set(f"扫描失败: {error_msg}")
        messagebox.showerror("扫描失败", f"扫描文件时发生错误:\n{error_msg}")

    def _disable_actions(self):
        """禁用操作按钮"""
        self.view_changes_btn.configure(state="disabled")
        self.package_btn.configure(state="disabled")
        self.reset_btn.configure(state="disabled")

    def _enable_actions(self):
        """启用操作按钮"""
        self.package_btn.configure(state="normal")
        self.reset_btn.configure(state="normal")

    def _view_file_changes(self):
        """查看文件变化"""
        if not self.file_changes:
            messagebox.showinfo("信息", "没有文件变化")
            return

        if self.file_list_window is None or not self.file_list_window.window.winfo_exists():
            self.file_list_window = FileListWindow(self.root, self)

        self.file_list_window.show_changes(self.file_changes)
        self.file_list_window.window.lift()

    def _start_package_auto(self):
        version = self.current_version.get()
        if version=='v1.0.0':
            self._start_full_package()
        else:
            self._start_incremental_package()

    def _start_incremental_package(self):
        """开始增量打包"""
        if not self.file_changes:
            messagebox.showinfo("信息", "没有文件变化，无需打包")
            return

        # 在打包前保存配置
        self._save_current_config()

        # 过滤出需要打包的文件（排除删除的文件）
        files_to_package = [
            change.file_path for change in self.file_changes
            if change.change_type != ChangeType.DELETED
        ]

        if not files_to_package:
            messagebox.showinfo("信息", "只有文件删除，无需创建增量包")
            return

        version = self.current_version.get()
        self._start_package(files_to_package, version, is_full=False)

    def _start_full_package(self):
        """开始全量打包"""
        if not self.current_file_info:
            messagebox.showerror("错误", "请先扫描文件")
            return

        # 在打包前保存配置
        self._save_current_config()

        files_to_package = list(self.current_file_info.keys())
        version = self.version_manager.get_next_version(is_full_package=True)
        self._start_package(files_to_package, version, is_full=True)

    def _start_package(self, files_to_package, version, is_full=False):
        """开始打包"""
        if self.is_building:
            return

        self.is_building = True
        self._disable_actions()

        package_type = "全量" if is_full else "增量"
        self.scan_btn.configure(state="disabled")

        # 在新线程中打包
        threading.Thread(
            target=self._build_package,
            args=(files_to_package, version, is_full, package_type),
            daemon=True
        ).start()

    def _build_package(self, files_to_package, version, is_full, package_type):
        """构建包（在子线程中执行）"""
        try:
            input_path = Path(self.input_dir.get())
            output_path = Path(self.output_dir.get())
            package_file = output_path / f"{version}.zip"

            def progress_callback(current, total):
                progress = current / total if total > 0 else 0
                self.root.after(0, lambda: self.progress_bar.set(progress))
                self.root.after(0, lambda: self.progress_label.configure(
                    text=f"正在打包: {current}/{total} 个文件"
                ))

            self.root.after(0, lambda: self.status_text.set(f"正在创建{package_type}包..."))

            # 创建包
            success = self.package_builder.create_package(
                input_path, package_file, files_to_package, progress_callback
            )

            if success:
                new_file_info = {}
                for key in self.current_file_info:
                    if key in files_to_package:
                        new_file_info[key] = self.current_file_info[key]
                # 保存版本信息
                self.version_manager.add_version(
                    version, self.current_file_info, new_file_info,is_full,
                    f"{package_type}包"
                )

                # 更新UI
                self.root.after(0, lambda: self._on_package_completed(package_file, package_type))
            else:
                self.root.after(0, lambda: self._on_package_cancelled(package_type))

        except Exception as e:
            self.root.after(0, lambda: self._on_package_error(str(e), package_type))

    def _on_package_completed(self, package_file, package_type):
        """打包完成回调"""
        self.is_building = False
        self._enable_actions()
        self.scan_btn.configure(state="normal")

        # 更新版本显示
        next_version = self.version_manager.get_next_version()
        self.current_version.set(next_version)

        # 清理变化列表
        self.file_changes = []
        self.view_changes_btn.configure(state="disabled")

        # 更新进度
        self.progress_bar.set(1.0)
        self.progress_label.configure(text="")

        # 显示结果
        package_info = self.package_builder.get_package_info(package_file)
        if package_info:
            size_kb = package_info['compressed_size'] / 1024
            size_info = f'{size_kb:.2f} KB'
            if size_kb > 1024:
                size_mb = size_kb / 1024
                size_info = f'{size_mb:.2f} MB'

            message = f"{package_type}包创建成功!\n" \
                      f"文件: {package_file.name}\n" \
                      f"大小: {size_info}\n" \
                      f"文件数: {package_info['file_count']}"
            messagebox.showinfo("成功", message)
            self.status_text.set(f"{package_type}包创建成功: {package_file.name}")
        else:
            self.status_text.set(f"{package_type}包创建成功")

    def _on_package_cancelled(self, package_type):
        """打包取消回调"""
        self.is_building = False
        self._enable_actions()
        self.scan_btn.configure(state="normal")

        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.status_text.set(f"{package_type}包创建已取消")

    def _on_package_error(self, error_msg, package_type):
        """打包错误回调"""
        self.is_building = False
        self._enable_actions()
        self.scan_btn.configure(state="normal")

        self.progress_bar.set(0)
        self.progress_label.configure(text="")
        self.status_text.set(f"{package_type}包创建失败")
        messagebox.showerror("打包失败", f"创建{package_type}包时发生错误:\n{error_msg}")

    def _reset_version(self):
        """重置版本"""
        if messagebox.askyesno("确认", "是否重置所有版本信息？\n这将清除所有版本历史和缓存数据。"):
            if self.version_manager:
                self.version_manager.reset_to_full_package()
                self.package_builder.cache_manager.clear_cache()
                self.current_version.set("v1.0.0")
                self.file_changes = []
                self.current_file_info = {}
                self.view_changes_btn.configure(state="disabled")
                self.package_btn.configure(state="disabled")
                self.status_text.set("版本已重置，请重新扫描文件")

    def _show_version_history(self):
        """显示版本历史"""
        if not self.version_manager:
            messagebox.showinfo("信息", "请先选择输出目录")
            return

        versions = self.version_manager.get_versions()
        if not versions:
            messagebox.showinfo("信息", "没有版本历史")
            return

        # 创建版本历史窗口
        history_window = ctk.CTkToplevel()
        history_window.title("版本历史")
        history_window.geometry("600x450")
        history_window.grab_set()
        center_on_screen(history_window)

        # 创建树状表格
        columns = ("版本", "时间", "类型", "文件数", "大小")
        tree = ttk.Treeview(history_window, columns=columns, show="headings")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=60, anchor="center")

        tree.column("时间", width=160)

        # 添加数据
        for version in versions:
            size_kb = version.total_size / 1024
            size_info = f'{size_kb:.2f} KB'
            if size_kb > 1024:
                size_mb = size_kb / 1024
                size_info = f'{size_mb:.2f} MB'
            package_type = "全量" if version.is_full_package else "增量"
            tree.insert("", "end", values=(
                version.version,
                version.timestamp[:19].replace("T", " "),
                package_type,
                version.file_count,
                f"{size_info}"
            ))

        tree.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_window_close(self):
        """窗口关闭事件"""
        # 在退出前保存配置
        self._save_current_config()

        # 停止所有正在进行的操作
        if self.is_scanning:
            self.file_scanner.stop_scan()
        if self.is_building:
            self.package_builder.stop_build()

        # 关闭子窗口
        if self.file_list_window and self.file_list_window.window.winfo_exists():
            self.file_list_window.window.destroy()

        self.root.destroy()

    def _load_saved_directories(self):
        """加载保存的目录配置"""
        try:
            # 获取当前版本索引
            current_index = self.config.get_current_version_index()

            # 设置版本下拉框的选中值
            self.version_choice.set(f"版本 {current_index + 1}")

            # 从配置中加载保存的目录
            saved_input = self.config.get_input_directory(current_index)
            saved_output = self.config.get_output_directory(current_index)

            if saved_input and Path(saved_input).exists():
                self.input_dir.set(saved_input)

            if saved_output:
                self.output_dir.set(saved_output)

            # 如果有保存的目录，触发目录变更事件
            if saved_input or saved_output:
                self._on_directory_changed()

            self.status_text.set(f"已加载版本 {current_index + 1} 配置")

        except Exception as e:
            print(f"加载保存的目录配置失败: {e}")
            # 设置默认版本
            self.version_choice.set("版本 1")

    def run(self):
        """运行应用"""
        self.root.mainloop()
