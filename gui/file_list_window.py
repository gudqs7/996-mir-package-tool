# -*- coding: gbk -*-
"""
˫���ļ�����鿴����
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import customtkinter as ctk
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING, Dict
import difflib
import zipfile
from core.make_win_center import center_on_screen

from core.file_comparator import FileChange, ChangeType
from core.file_cache_manager import FileCacheManager

if TYPE_CHECKING:
    from .main_window import IncrementalPackerApp


class FileListWindow:
    """˫���ļ�����鿴����"""

    def __init__(self, parent, app: 'IncrementalPackerApp'):
        """
        ��ʼ���ļ��б���
        
        Args:
            parent: ������
            app: ��Ӧ��ʵ��
        """
        self.app = app
        self.changes: List[FileChange] = []
        self.selected_change: Optional[FileChange] = None
        self.item_to_change: Dict[str, FileChange] = {}  # �洢tree item��change�����ӳ��

        # ʹ�û������Ŀ¼�Ļ��������
        output_dir = app.output_dir.get()
        if output_dir:
            from pathlib import Path
            self.cache_manager = FileCacheManager.create_for_output_dir(Path(output_dir))
        else:
            # ���û�����Ŀ¼��ʹ��Ĭ�ϻ���
            self.cache_manager = FileCacheManager()

        # ��������
        self.window = ctk.CTkToplevel()
        self.window.title("�ļ��������")
        self.window.grab_set()

        # ���ô��ھ��кͺ����С
        self.window.geometry("1500x900")
        self.window.minsize(1200, 800)
        center_on_screen(self.window)

        self._setup_ui()
        self._setup_events()

    def _setup_ui(self):
        """����UI����"""
        # �����
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ��������
        title_frame = ctk.CTkFrame(main_frame)
        title_frame.pack(fill="x", padx=10, pady=(10, 5))

        title_label = ctk.CTkLabel(
            title_frame,
            text="�ļ��������",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(side="left", padx=10, pady=10)

        # ͳ����Ϣ
        self.stats_label = ctk.CTkLabel(title_frame, text="")
        self.stats_label.pack(side="right", padx=10, pady=10)

        # ����������˫�в��֣�
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # ����ļ��б�
        self._setup_file_list(content_frame)

        # �ָ���
        separator = ttk.Separator(content_frame, orient="vertical")
        separator.pack(side="left", fill="y", padx=5)

        # �Ҳ������ʾ
        self._setup_diff_view(content_frame)

        # �ײ���ť����
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(
            button_frame,
            text="ˢ��",
            command=self._refresh_diff,
            width=80
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            button_frame,
            text="�ر�",
            command=self.window.destroy,
            width=80
        ).pack(side="right", padx=5)

    def _setup_file_list(self, parent):
        """��������ļ��б�"""
        left_frame = ctk.CTkFrame(parent)
        left_frame.pack(side="left", fill="both", expand=False, padx=5, pady=5)
        left_frame.configure(width=320)

        # �б����
        list_title = ctk.CTkLabel(
            left_frame,
            text="����ļ��б�",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_title.pack(pady=(10, 5))

        # ���˿��
        filter_frame = ctk.CTkFrame(left_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(filter_frame, text="����:").pack(side="left", padx=5)

        self.filter_var = tk.StringVar(value="all")

        # ����ѡ��
        filter_options = [
            ("ȫ��", "all"),
            ("����", "added"),
            ("�޸�", "modified"),
            ("ɾ��", "deleted")
        ]

        for text, value in filter_options:
            ctk.CTkRadioButton(
                filter_frame,
                text=text,
                variable=self.filter_var,
                value=value,
                command=self._apply_filter
            ).pack(side="left", padx=0)

        # �ļ��б��
        list_frame = ctk.CTkFrame(left_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # ������״��� - �޸���������show="headings"����������ʹ�õ�0��
        columns = ("״̬")
        self.tree = ttk.Treeview(list_frame, columns=columns, height=20)

        # �����б���Ϳ��
        self.tree.heading("#0", text="·��", anchor="w")
        self.tree.heading("״̬", text="״̬")

        # �����п��
        self.tree.column("#0", width=330, anchor="w")
        self.tree.column("״̬", width=10, anchor="center")

        # ��ӹ�����
        scrollbar_y = ctk.CTkScrollbar(list_frame, orientation="vertical", command=self.tree.yview)
        scrollbar_x = ctk.CTkScrollbar(list_frame, orientation="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # ����
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")

        # ����gridȨ��
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # ��ֹ���������
        left_frame.pack_propagate(False)

    def _setup_diff_view(self, parent):
        """�����Ҳ������ʾ"""
        right_frame = ctk.CTkFrame(parent)
        right_frame.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # ������ʾ����
        diff_title_frame = ctk.CTkFrame(right_frame)
        diff_title_frame.pack(fill="x", padx=10, pady=(10, 5))

        self.diff_title_label = ctk.CTkLabel(
            diff_title_frame,
            text="���ݶԱ�",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.diff_title_label.pack(side="left", padx=10, pady=5)

        self.file_path_label = ctk.CTkLabel(
            diff_title_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.file_path_label.pack(side="left", padx=10, pady=5)

        # ������ʾ����
        diff_frame = ctk.CTkFrame(right_frame)
        diff_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # �����ı�����ʾ����
        self.diff_text = tk.Text(
            diff_frame,
            wrap="none",
            font=("΢���ź�", 12),
            bg="#ffffff",  # ��ɫ����
            fg="#000000",  # ��ɫ����
            insertbackground="white",  # �����ɫ
            selectbackground="#1f6aa5",  # ѡ���ı�����ɫ
        state="disabled",
        )
        self.diff_text.pack(fill="both", expand=True, padx=5, pady=5)

        # ������ֱ������
        self.v_scrollbar = ctk.CTkScrollbar(diff_frame, orientation="vertical")
        self.v_scrollbar.configure(command=self.diff_text.yview)

        # ����ˮƽ������
        self.h_scrollbar = ctk.CTkScrollbar(diff_frame, orientation="horizontal")
        self.h_scrollbar.configure(command=self.diff_text.xview)

        # �����ı�����Ĺ�������
        self.diff_text.configure(
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set
        )

        # ʹ��grid����ȷ����������ȷ����
        self.diff_text.grid(row=0, column=0, sticky="nsew")
        self.v_scrollbar.grid(row=0, column=1, sticky="ns")
        self.h_scrollbar.grid(row=1, column=0, sticky="ew")
        diff_frame.grid_rowconfigure(0, weight=1)
        diff_frame.grid_columnconfigure(0, weight=1)

        # �����ı���ǩ��ʽ������VSCode��git diff��
        self._setup_text_tags()

        # Ĭ����ʾ��ʾ��Ϣ
        self._show_default_message()

    def _setup_text_tags(self):
        """�����ı���ǩ��ʽ"""
        # ����б��
        self.diff_text.tag_configure("added", background="#e6ffed", foreground="#22863a",selectbackground="#1f6aa5")
        self.diff_text.tag_configure("removed", background="#ffeef0", foreground="#d73a49",selectbackground="#1f6aa5")
        self.diff_text.tag_configure("context", background="#ffffff", foreground="#333333",selectbackground="#1f6aa5")
        self.diff_text.tag_configure("header", background="#f1f8ff", foreground="#0366d6",selectbackground="#1f6aa5", font=("΢���ź�", 12, "bold"))
        self.diff_text.tag_configure("info", background="#fff5b4", foreground="#735c0f",selectbackground="#1f6aa5", font=("΢���ź�", 12, "bold"))

    def _setup_events(self):
        """�����¼�����"""
        # ѡ���¼�
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_changed)

        # ˫���¼�
        self.tree.bind("<Double-1>", self._on_double_click)

    def show_changes(self, changes: List[FileChange]):
        """
        ��ʾ�ļ����
        
        Args:
            changes: �ļ�����б�
        """
        self.changes = changes
        self._update_stats()
        self._populate_tree()
        self._show_default_message()

        # ��ʾ����
        self.window.deiconify()
        self.window.focus()

    def _update_stats(self):
        """����ͳ����Ϣ"""
        added_count = len([c for c in self.changes if c.change_type == ChangeType.ADDED])
        modified_count = len([c for c in self.changes if c.change_type == ChangeType.MODIFIED])
        deleted_count = len([c for c in self.changes if c.change_type == ChangeType.DELETED])

        stats_text = f"����: {added_count} | �޸�: {modified_count} | ɾ��: {deleted_count}"
        self.stats_label.configure(text=stats_text)

    def _populate_tree(self):
        """����ļ��б�"""
        # �����������
        for item in self.tree.get_children():
            self.tree.delete(item)

        # ���ӳ���ֵ�
        self.item_to_change.clear()

        # ���ݹ���������ȡ����
        filtered_changes = self._get_filtered_changes()

        # �������
        for change in filtered_changes:
            status_text = self._get_status_text(change.change_type)
            size_change = self._get_size_change_text(change)
            file_name = Path(change.file_path).name

            # ʹ���ļ�·����Ϊ��0�е���ʾ�ı�
            item_id = self.tree.insert("", "end",
                                       text=change.file_path,  # ��0����ʾ����·��
                                       values=(
                                           status_text,
                                           file_name,
                                           size_change
                                       ))

            # ��item_idӳ�䵽change����
            self.item_to_change[item_id] = change

        # �������Ŀ��Ĭ��ѡ���һ��
        items = self.tree.get_children()
        if items:
            self.tree.selection_set(items[0])
            self._on_selection_changed(None)

    def _get_filtered_changes(self) -> List[FileChange]:
        """��ȡ���˺�ı���б�"""
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
        """��ȡ״̬�ı�"""
        status_map = {
            ChangeType.ADDED: "����",
            ChangeType.MODIFIED: "�޸�",
            ChangeType.DELETED: "ɾ��"
        }
        return status_map.get(change_type, "δ֪")

    def _get_size_change_text(self, change: FileChange) -> str:
        """��ȡ��С�仯�ı�"""
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
                    return "�ޱ仯"
        return "-"

    def _format_size(self, size_bytes: int) -> str:
        """��ʽ���ļ���С"""
        if size_bytes is None:
            return "-"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"

    def _apply_filter(self):
        """Ӧ�ù���"""
        self._populate_tree()

    def _on_selection_changed(self, event):
        """ѡ��ı��¼�"""
        selection = self.tree.selection()
        if not selection:
            self._show_default_message()
            return

        # ��ӳ���ֵ��л�ȡ��Ӧ��FileChange����
        item_id = selection[0]
        selected_change = self.item_to_change.get(item_id)

        if selected_change:
            self.selected_change = selected_change
            self._show_file_diff(selected_change)

    def _on_double_click(self, event):
        """˫���¼�"""
        # ˫��ʱչ��/�۵����ڵ��ִ����������
        pass

    def _show_default_message(self):
        """��ʾĬ����ʾ��Ϣ"""
        self.diff_text.config(state="normal")
        self.diff_text.delete(1.0, tk.END)

        self.file_path_label.configure(text="")

        message = "�������ѡ��һ���ļ��鿴�������\n\n"
        message += "˵��:\n"
        message += "? ��ɫ����������������\n"
        message += "? ��ɫ������ɾ��������\n"
        message += "? ��ɫ�������ļ�ͷ��Ϣ\n"
        message += "? ��ɫ��������Ҫ��ʾ��Ϣ"

        self.diff_text.insert(1.0, message)
        self.diff_text.tag_add("info", 1.0, tk.END)
        self.diff_text.config(state="disabled")

    def _show_file_diff(self, change: FileChange):
        """��ʾ�ļ�����"""
        self.file_path_label.configure(text=f"�ļ�: {change.file_path}")

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
        """��ʾ�����ļ�"""
        current_file = Path(self.app.input_dir.get()) / change.file_path

        # �����ļ�ͷ
        header = f"=== �����ļ�: {change.file_path} ===\n"
        self.diff_text.insert(tk.END, header)
        self.diff_text.tag_add("header", "end-2l", "end-1l")

        if not current_file.exists():
            self.diff_text.insert(tk.END, "�ļ�������\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return

        if not self._is_text_file(current_file):
            self.diff_text.insert(tk.END, "�������ļ����޷���ʾ����\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return

        try:
            content = self._read_file_content(current_file)
            if content is None:
                return

            # ��ʾ���ݣ������ж����Ϊ��ӣ�
            for i, line in enumerate(content.splitlines(), 1):
                line_text = f"{i:4d}\t{line}\n"
                self.diff_text.insert(tk.END, line_text)
                self.diff_text.tag_add("added", "end-2l", "end-1l")

        except Exception as e:
            error_msg = f"��ȡ�ļ�ʧ��: {e}\n"
            self.diff_text.insert(tk.END, error_msg)
            self.diff_text.tag_add("info", "end-2l", "end-1l")

    def _show_deleted_file(self, change: FileChange):
        """��ʾɾ���ļ�"""
        # �����ļ�ͷ
        header = f"=== ɾ���ļ�: {change.file_path} ===\n"
        self.diff_text.insert(tk.END, header)
        self.diff_text.tag_add("header", "end-2l", "end-1l")

        # ���Դ�֮ǰ��zip���л�ȡ�ļ�����
        old_content = self._get_file_from_previous_version(change.file_path)
        if old_content is None:
            self.diff_text.insert(tk.END, "�޷���ȡ�ļ�����ʷ�汾����\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return

        # ��ʾɾ��������
        for i, line in enumerate(old_content.splitlines(), 1):
            line_text = f"{i:4d}\t{line}\n"
            self.diff_text.insert(tk.END, line_text)
            self.diff_text.tag_add("removed", "end-2l", "end-1l")

    def _show_modified_file(self, change: FileChange):
        """��ʾ�޸��ļ�"""
        current_file = Path(self.app.input_dir.get()) / change.file_path

        # �����ļ�ͷ
        header = f"=== ��ɫ����ɾ��,��ɫ��������;�޸ĵ���һ����ɾ��ԭ��+�����޸ĺ���� ===\n"
        self.diff_text.insert(tk.END, header)
        self.diff_text.tag_add("header", "end-2l", "end-1l")

        if not current_file.exists():
            self.diff_text.insert(tk.END, "��ǰ�ļ�������\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return

        if not self._is_text_file(current_file):
            self.diff_text.insert(tk.END, "�������ļ����޷���ʾ���ݲ���\n")
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return

        # ��ȡ��ǰ�ļ�����
        current_content = self._read_file_content(current_file)
        if current_content is None:
            return

        # ��ȡ��ʷ�汾����
        old_content = self._get_file_from_previous_version(change.file_path)
        if old_content is None:
            self.diff_text.insert(tk.END, "�޷���ȡ�ļ�����ʷ�汾����ʾ��ǰ���ݣ�\n\n")
            self.diff_text.tag_add("info", "end-3l", "end-1l")

            for i, line in enumerate(current_content.splitlines(), 1):
                line_text = f" {i:4d} | {line}\n"
                self.diff_text.insert(tk.END, line_text)
                self.diff_text.tag_add("context", "end-2l", "end-1l")
            return

        # ���ɲ���
        self._show_unified_diff(old_content, current_content, change.file_path)

    def _show_unified_diff(self, old_content: str, new_content: str, file_path: str):
        """��ʾͳһ��ʽ�Ĳ���"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"�ɰ汾\\{file_path}",
            tofile=f"�°汾\\{file_path}"
        )
        old_line_num = 0
        new_line_num = 0
        just_del = False
        for line in diff:
            if line.startswith("+++") or line.startswith("---"):
                self.diff_text.insert(tk.END, line)
                self.diff_text.tag_add("header", "end-2l", "end-1l")
            elif line.startswith("@@"):
                # �� @@ -x,y +z,w @@ �����к���Ϣ
                import re
                match = re.search(r'@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
                if match:
                    old_line_num = int(match.group(1)) - 1  # ��ָ���кſ�ʼ
                    old_lines = int(match.group(2) or 1)
                    new_line_num = int(match.group(3)) - 1
                    new_lines = int(match.group(4) or 1)

                read_line = f"\n��һ�����: ԭ�ļ���{old_line_num + 1}-{old_line_num + old_lines}�� �� ���ļ���{new_line_num + 1}-{new_line_num + new_lines}��\n"
                self.diff_text.insert(tk.END, read_line)
                self.diff_text.tag_add("info", "end-2l", "end-1l")
            elif line.startswith("+"):
                new_line_num += 1
                self.diff_text.insert(tk.END, f"{old_line_num:3d} {new_line_num:3d} {line}")
                self.diff_text.tag_add("added", "end-2l", "end-1l")
            elif line.startswith("-"):
                just_del = True
                old_line_num += 1
                self.diff_text.insert(tk.END, f"{old_line_num:3d} {new_line_num + 1:3d} {line}")
                self.diff_text.tag_add("removed", "end-2l", "end-1l")
            else:
                old_line_num += 1
                new_line_num += 1
                self.diff_text.insert(tk.END, f"{old_line_num:3d} {new_line_num:3d} {line}")
                self.diff_text.tag_add("context", "end-2l", "end-1l")

    def _get_file_from_previous_version(self, file_path: str) -> Optional[str]:
        """�ӻ����л�ȡ�ļ�����һ���汾����"""
        # ���ȴӻ����ȡ
        cached_content = self.cache_manager.get_cached_content(file_path)
        if cached_content is not None:
            return cached_content

        # ���������û�У����Դ�zip����ȡ�������ݣ�
        if not self.app.version_manager:
            return None

        # ��ȡ�汾��ʷ
        versions = self.app.version_manager.get_versions()
        if not versions:
            return None

        # �����Ŀ¼�в���zip�ļ�
        output_dir = Path(self.app.output_dir.get())

        for version_info in versions:
            zip_file_path = output_dir / f"{version_info.version}.zip"
            if zip_file_path.exists():
                try:
                    with zipfile.ZipFile(zip_file_path, 'r') as zf:
                        if file_path in zf.namelist():
                            content = zf.read(file_path).decode('gbk', errors='ignore')
                            return content
                except (zipfile.BadZipFile, UnicodeDecodeError, KeyError):
                    continue

        return None

    def _is_text_file(self, file_path: Path) -> bool:
        """�ж��Ƿ�Ϊ�ı��ļ�"""
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.html', '.css', '.xml', '.json',
            '.ini', '.cfg', '.conf', '.log', '.csv', '.sql', '.sh', '.bat',
            '.yml', '.yaml', '.toml', '.properties'
        }

        if file_path.suffix.lower() in text_extensions:
            return True

        # ���Զ�ȡ�ļ���ͷ�ж�
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(8192)
                # ����Ƿ����null�ֽ�
                if b'\\0' in sample:
                    return False
                # ���Խ���
                sample.decode('utf-8')
                return True
        except (UnicodeDecodeError, IOError):
            return False

    def _read_file_content(self, file_path: Path) -> Optional[str]:
        """��ȡ�ļ�����"""
        try:
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                return f.read()
        except IOError as e:
            error_msg = f"��ȡ�ļ�ʧ��: {e}\n"
            self.diff_text.insert(tk.END, error_msg)
            self.diff_text.tag_add("info", "end-2l", "end-1l")
            return None

    def _refresh_diff(self):
        """ˢ�²�����ʾ"""
        if self.selected_change:
            self._show_file_diff(self.selected_change)
