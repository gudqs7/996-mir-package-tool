import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
from typing import List, Tuple, Optional, Dict, Any


class CTkTreeview(ctk.CTkFrame):
    def __init__(self, master, columns: List[str] = None, show: str = "tree headings", height: int = 200,
                 selectmode: str = "browse", **kwargs):
        super().__init__(master, **kwargs)

        self.columns = columns or []
        self.show = show
        self.selectmode = selectmode
        self.data = []  # 存储树形数据
        self.selected_items = []  # 多选模式支持
        self._heading_commands = {}  # 存储列标题命令
        self._column_config = {}  # 存储列配置

        # 初始化列配置
        for i, col in enumerate(self.columns):
            self._column_config[col] = {"width": 120, "minwidth": 50, "anchor": "w"}

        # 创建标题行（如果显示标题）
        if "headings" in show:
            self.header_frame = ctk.CTkFrame(self, fg_color="#2b2b2b", height=30)
            self.header_frame.pack(fill="x", padx=1, pady=(1, 0))
            self.header_frame.pack_propagate(False)

            # 创建列标题
            self.header_labels = {}
            x_position = 0

            # 树列（第一列）
            if "tree" in show:
                tree_header = ctk.CTkLabel(
                    self.header_frame,
                    text="#0",  # 树列的默认标识
                    width=150,
                    anchor="w"
                )
                tree_header.place(x=x_position, y=0, width=150, height=30)
                self.header_labels["#0"] = tree_header
                x_position += 150

            # 数据列
            for i, col in enumerate(self.columns):
                col_id = f"#{i + 1}"
                header = ctk.CTkLabel(
                    self.header_frame,
                    text=col,
                    width=self._column_config[col]["width"],
                    anchor=self._column_config[col]["anchor"]
                )
                header.place(x=x_position, y=0, width=self._column_config[col]["width"], height=30)
                self.header_labels[col_id] = header
                x_position += self._column_config[col]["width"]

                # 绑定点击事件用于排序
                header.bind("<Button-1>", lambda e, c=col_id: self._on_heading_click(c))
        else:
            self.header_frame = None

        # 创建滚动条和内容区域
        self.scrollable_frame = ctk.CTkScrollableFrame(self, height=height)
        self.scrollable_frame.pack(fill="both", expand=True, padx=1, pady=(0, 1))

        # 存储树节点
        self.tree_nodes = {}  # id -> node_data
        self.next_id = 0

        # 排序状态
        self.sort_column = None
        self.sort_reverse = False

    def _generate_id(self) -> str:
        """生成唯一ID"""
        self.next_id += 1
        return f"I{self.next_id:03d}"

    def insert(self, parent: str = "", index: str = "end", iid: str = None,
               text: str = "", values: tuple = (), open: bool = True, tags: tuple = ()) -> str:
        """插入新节点"""
        if iid is None:
            iid = self._generate_id()

        # 验证parent是否存在
        if parent and parent not in self.tree_nodes:
            raise ValueError(f"Parent '{parent}' does not exist")

        # 存储节点数据
        node_data = {
            "iid": iid,
            "parent": parent,
            "text": text,
            "values": values or (),
            "open": open,
            "tags": tags,
            "children": []
        }

        # 如果存在父节点，添加到父节点的children中
        if parent:
            parent_node = self.tree_nodes[parent]
            if index == "end":
                parent_node["children"].append(node_data)
            else:
                parent_node["children"].insert(index, node_data)
        else:
            if index == "end":
                self.data.append(node_data)
            else:
                self.data.insert(index, node_data)

        self.tree_nodes[iid] = node_data

        # 重新渲染树
        self._render_tree()

        return iid

    def delete(self, *items: str) -> None:
        """删除一个或多个项目"""
        for item_id in items:
            if item_id not in self.tree_nodes:
                continue

            # 递归删除所有子节点
            node = self.tree_nodes[item_id]
            children_copy = node["children"][:]
            for child in children_copy:
                self.delete(child["iid"])

            # 从父节点中移除
            if node["parent"]:
                parent_node = self.tree_nodes[node["parent"]]
                parent_node["children"] = [child for child in parent_node["children"] if child["iid"] != item_id]
            else:
                self.data = [item for item in self.data if item["iid"] != item_id]

            # 从选中项中移除
            if item_id in self.selected_items:
                self.selected_items.remove(item_id)

            # 从节点字典中移除
            del self.tree_nodes[item_id]

        self._render_tree()

    def get_children(self, item: str = "") -> Tuple[str, ...]:
        """获取指定项目的子项目"""
        if not item:
            return tuple(node["iid"] for node in self.data)

        if item not in self.tree_nodes:
            return ()

        node = self.tree_nodes[item]
        return tuple(child["iid"] for child in node["children"])

    def selection_set(self, *items: str) -> None:
        """设置选中项"""
        if self.selectmode == "browse" and len(items) > 1:
            items = (items[0],)  # browse模式只允许单选

        # 清除当前选择
        for item_id in self.selected_items:
            if item_id in self.tree_nodes:
                self._update_item_appearance(item_id, selected=False)

        self.selected_items = []

        # 设置新选择
        for item_id in items:
            if item_id in self.tree_nodes:
                self.selected_items.append(item_id)
                self._update_item_appearance(item_id, selected=True)

    def selection_add(self, *items: str) -> None:
        """添加选中项"""
        if self.selectmode == "browse":
            return self.selection_set(*items)

        for item_id in items:
            if item_id in self.tree_nodes and item_id not in self.selected_items:
                self.selected_items.append(item_id)
                self._update_item_appearance(item_id, selected=True)

    def selection_remove(self, *items: str) -> None:
        """移除选中项"""
        for item_id in items:
            if item_id in self.selected_items:
                self.selected_items.remove(item_id)
                self._update_item_appearance(item_id, selected=False)

    def selection_toggle(self, *items: str) -> None:
        """切换选中状态"""
        for item_id in items:
            if item_id in self.selected_items:
                self.selection_remove(item_id)
            else:
                self.selection_add(item_id)

    def selection(self) -> Tuple[str, ...]:
        """获取当前选中项"""
        return tuple(self.selected_items)

    def heading(self, column: str, **kwargs) -> None:
        """配置列标题"""
        if column not in self.header_labels:
            raise ValueError(f"Column '{column}' does not exist")

        if "text" in kwargs:
            self.header_labels[column].configure(text=kwargs["text"])

        if "command" in kwargs:
            self._heading_commands[column] = kwargs["command"]

    def column(self, column: str, **kwargs) -> None:
        """配置列属性"""
        if column == "#0":  # 树列
            if "width" in kwargs:
                new_width = kwargs["width"]
                self.header_labels[column].place(width=new_width)
                # 更新所有节点的树列宽度
                for node_data in self.tree_nodes.values():
                    if "text_label" in node_data:
                        node_data["text_label"].place(width=new_width - 20)

        elif column in self._column_config:
            if "width" in kwargs:
                self._column_config[column]["width"] = kwargs["width"]
                if column in self.header_labels:
                    self.header_labels[column].place(width=kwargs["width"])

            if "minwidth" in kwargs:
                self._column_config[column]["minwidth"] = kwargs["minwidth"]

            if "anchor" in kwargs:
                self._column_config[column]["anchor"] = kwargs["anchor"]
                if column in self.header_labels:
                    self.header_labels[column].configure(anchor=kwargs["anchor"])

        self._render_tree()

    def _on_heading_click(self, column: str) -> None:
        """列标题点击事件"""
        if column in self._heading_commands:
            self._heading_commands[column]()
        else:
            # 默认排序行为
            self._sort_by_column(column)

    def _sort_by_column(self, column: str) -> None:
        """按列排序"""
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        # 排序逻辑（这里需要实现具体的排序算法）
        # 由于树形结构复杂，实际排序需要递归处理
        self._render_tree()

    def _render_tree(self) -> None:
        """渲染整个树形结构"""
        # 清空当前显示
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # 递归渲染节点
        for item in self.data:
            self._render_node(item, 0)

    def _render_node(self, node: Dict[str, Any], level: int) -> None:
        """渲染单个节点及其子节点"""
        # 创建节点框架
        node_frame = ctk.CTkFrame(self.scrollable_frame, height=30)
        node_frame.pack(fill="x", pady=1)

        # 存储UI组件引用
        node["frame"] = node_frame
        node["text_label"] = None
        node["value_labels"] = []

        indent = level * 20
        x_position = 0

        # 树列（如果显示）
        if "tree" in self.show:
            # 展开/折叠按钮（如果有子节点）
            if node["children"]:
                btn_text = "−" if node["open"] else "+"
                toggle_btn = ctk.CTkButton(
                    node_frame,
                    text=btn_text,
                    width=20,
                    height=20,
                    command=lambda n=node: self._toggle_node(n)
                )
                toggle_btn.place(x=indent, y=5)
                indent += 25
            else:
                # 无子节点，添加空白占位
                indent_label = ctk.CTkLabel(node_frame, text="", width=20)
                indent_label.place(x=indent, y=5)
                indent += 25

            # 节点文本
            text_label = ctk.CTkLabel(
                node_frame,
                text=node["text"],
                width=150 - indent if indent < 150 else 130,
                anchor="w"
            )
            text_label.place(x=indent, y=5)
            node["text_label"] = text_label
            x_position = 150

        # 数据列
        for i, value in enumerate(node["values"]):
            if i >= len(self.columns):
                break

            col_id = f"#{i + 1}"
            col_config = self._column_config[self.columns[i]]

            value_label = ctk.CTkLabel(
                node_frame,
                text=str(value),
                width=col_config["width"],
                anchor=col_config["anchor"]
            )
            value_label.place(x=x_position, y=5, width=col_config["width"])
            node["value_labels"].append(value_label)
            x_position += col_config["width"]

        # 设置选中状态
        is_selected = node["iid"] in self.selected_items
        self._update_node_appearance(node, is_selected)

        # 绑定点击事件
        node_frame.bind("<Button-1>", lambda e, n=node: self._on_item_click(n))
        if node["text_label"]:
            node["text_label"].bind("<Button-1>", lambda e, n=node: self._on_item_click(n))
        for label in node["value_labels"]:
            label.bind("<Button-1>", lambda e, n=node: self._on_item_click(n))

        # 如果节点是展开的，渲染子节点
        if node["open"] and node["children"]:
            for child in node["children"]:
                self._render_node(child, level + 1)

    def _on_item_click(self, node: Dict[str, Any]) -> None:
        """处理项目点击事件"""
        if self.selectmode == "browse":
            self.selection_set(node["iid"])
        else:  # extended 模式
            if node["iid"] in self.selected_items:
                self.selection_remove(node["iid"])
            else:
                self.selection_add(node["iid"])

    def _toggle_node(self, node: Dict[str, Any]) -> None:
        """切换节点的展开/折叠状态"""
        node["open"] = not node["open"]
        self._render_tree()

    def _update_node_appearance(self, node: Dict[str, Any], selected: bool) -> None:
        """更新节点外观"""
        bg_color = "#1f6aa5" if selected else ["#f0f0f0", "#2b2b2b"]
        node["frame"].configure(fg_color=bg_color)

    def _update_item_appearance(self, item_id: str, selected: bool) -> None:
        """更新指定项目的外观"""
        if item_id in self.tree_nodes:
            node = self.tree_nodes[item_id]
            self._update_node_appearance(node, selected)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("增强版 CTkTreeview 示例")
        self.geometry("900x600")

        # 创建现代风格树形视图
        self.tree = CTkTreeview(
            self,
            columns=["大小", "类型", "修改日期"],
            show="tree headings",
            height=400,
            selectmode="extended"  # 支持多选
        )
        self.tree.pack(fill="both", expand=True, padx=20, pady=20)

        # 配置列
        self.tree.column("#0", width=200)  # 树列
        self.tree.column("大小", width=100)
        self.tree.column("类型", width=100)
        self.tree.column("修改日期", width=150)

        # 配置标题
        self.tree.heading("#0", text="名称")
        self.tree.heading("大小", text="大小")
        self.tree.heading("类型", text="类型")
        self.tree.heading("修改日期", text="修改日期")

        # 添加示例数据
        self.populate_tree()

        # 添加控制面板
        self.create_control_panel()

    def populate_tree(self):
        """填充示例数据"""
        # 添加根节点
        root1 = self.tree.insert("", "end", text="项目", values=("1.2 MB", "文件夹", "2023-10-01"))
        self.tree.insert(root1, "end", text="子项目1", values=("450 KB", "文件", "2023-10-02"))
        self.tree.insert(root1, "end", text="子项目2", values=("780 KB", "文件", "2023-10-03"))

        root2 = self.tree.insert("", "end", text="文档", values=("2.5 MB", "文件夹", "2023-09-15"))
        self.tree.insert(root2, "end", text="报告.pdf", values=("1.1 MB", "PDF", "2023-09-20"))
        self.tree.insert(root2, "end", text="数据.xlsx", values=("1.4 MB", "Excel", "2023-09-18"))

        root3 = self.tree.insert("", "end", text="图片", values=("5.7 MB", "文件夹", "2023-10-05"))
        self.tree.insert(root3, "end", text="photo1.jpg", values=("2.1 MB", "JPEG", "2023-10-06"))
        self.tree.insert(root3, "end", text="photo2.png", values=("3.6 MB", "PNG", "2023-10-07"))

        # 设置默认选中项
        self.tree.selection_set(root1)

    def create_control_panel(self):
        """创建控制面板"""
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(pady=10)

        # 操作按钮
        ctk.CTkButton(control_frame, text="添加项目", command=self.add_item).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="删除选中", command=self.delete_selected).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="获取选中", command=self.get_selected).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="获取子项", command=self.get_children).pack(side="left", padx=5)
        ctk.CTkButton(control_frame, text="切换主题", command=self.toggle_theme).pack(side="left", padx=5)

        # 信息显示
        self.info_label = ctk.CTkLabel(self, text="选中项目: 无")
        self.info_label.pack(pady=5)

    def add_item(self):
        """添加新项目"""
        import random
        sizes = ["120 KB", "850 KB", "2.1 MB", "350 KB"]
        types = ["文件", "图片", "文档", "视频"]
        dates = ["2023-10-12", "2023-10-11", "2023-10-10", "2023-10-09"]

        new_item = f"新项目{random.randint(1, 100)}"
        size = random.choice(sizes)
        file_type = random.choice(types)
        date = random.choice(dates)

        # 如果有选中项，添加到选中项下面
        selected = self.tree.selection()
        if selected:
            parent = selected[0]
        else:
            parent = ""

        self.tree.insert(parent, "end", text=new_item, values=(size, file_type, date))

    def delete_selected(self):
        """删除选中项目"""
        selected = self.tree.selection()
        if selected:
            self.tree.delete(*selected)
            self.info_label.configure(text=f"已删除 {len(selected)} 个项目")

    def get_selected(self):
        """获取选中项目信息"""
        selected = self.tree.selection()
        if selected:
            self.info_label.configure(text=f"选中项目: {', '.join(selected)}")
        else:
            self.info_label.configure(text="选中项目: 无")

    def get_children(self):
        """获取子项目"""
        selected = self.tree.selection()
        if selected:
            parent = selected[0]
            children = self.tree.get_children(parent)
            self.info_label.configure(text=f"{parent} 的子项目: {', '.join(children)}")
        else:
            children = self.tree.get_children("")
            self.info_label.configure(text=f"根项目: {', '.join(children)}")

    def toggle_theme(self):
        """切换主题"""
        current_theme = ctk.get_appearance_mode()
        new_theme = "Dark" if current_theme == "Light" else "Light"
        ctk.set_appearance_mode(new_theme)


if __name__ == "__main__":
    app = App()
    app.mainloop()