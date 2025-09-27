import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import difflib
import os


class DiffViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Git Diff 模拟工具")
        self.root.geometry("1000x700")

        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 文件选择区域
        file_frame = ttk.Frame(main_frame)
        file_frame.pack(fill=tk.X, pady=5)

        ttk.Button(file_frame, text="选择文件1", command=self.select_file1).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="选择文件2", command=self.select_file2).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="比较", command=self.compare_files).pack(side=tk.LEFT, padx=5)

        self.file1_label = ttk.Label(file_frame, text="未选择文件")
        self.file1_label.pack(side=tk.LEFT, padx=10)
        self.file2_label = ttk.Label(file_frame, text="未选择文件")
        self.file2_label.pack(side=tk.LEFT, padx=10)

        # 差异显示区域
        diff_frame = ttk.Frame(main_frame)
        diff_frame.pack(fill=tk.BOTH, expand=True)

        # 创建文本区域用于显示差异
        self.text_area = scrolledtext.ScrolledText(
            diff_frame,
            wrap=tk.NONE,
            font=("Courier New", 10)
        )
        self.text_area.pack(fill=tk.BOTH, expand=True)

        self.file1_path = None
        self.file2_path = None

    def select_file1(self):
        self.file1_path = filedialog.askopenfilename(title="选择第一个文件")
        if self.file1_path:
            self.file1_label.config(text=os.path.basename(self.file1_path))

    def select_file2(self):
        self.file2_path = filedialog.askopenfilename(title="选择第二个文件")
        if self.file2_path:
            self.file2_label.config(text=os.path.basename(self.file2_path))

    def compare_files(self):
        if not self.file1_path or not self.file2_path:
            return

        with open(self.file1_path, 'r', encoding='gbk') as f1:
            file1_lines = f1.readlines()

        with open(self.file2_path, 'r', encoding='gbk') as f2:
            file2_lines = f2.readlines()

        # 使用difflib生成差异
        diff = difflib.unified_diff(
            file1_lines,
            file2_lines,
            fromfile=self.file1_path,
            tofile=self.file2_path,
            lineterm=''
        )

        # 清空文本区域
        self.text_area.delete(1.0, tk.END)

        # 添加差异内容
        for line in diff:
            self.text_area.insert(tk.END, line + '\n')

            # 根据差异类型设置颜色
            if line.startswith('+'):
                self.text_area.tag_add("added", "end-2l", "end-1l")
            elif line.startswith('-'):
                self.text_area.tag_add("removed", "end-2l", "end-1l")
            elif line.startswith('@'):
                self.text_area.tag_add("header", "end-2l", "end-1l")

        # 配置标签样式
        self.text_area.tag_config("added", foreground="green")
        self.text_area.tag_config("removed", foreground="red")
        self.text_area.tag_config("header", foreground="blue")


if __name__ == "__main__":
    root = tk.Tk()
    app = DiffViewer(root)
    root.mainloop()