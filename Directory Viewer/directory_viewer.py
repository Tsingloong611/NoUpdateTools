import os
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import ttkbootstrap as ttkb


class DirectoryViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("目录结构查看器")
        self.root.geometry("900x600")
        self.selected_dir = None
        self.check_vars = {}  # 存储每个文件夹是否显示文件的选项

        # 设置主题
        style = ttkb.Style("cosmo")

        # 顶部框架：选择目录和保存
        frame_top = ttkb.Frame(self.root, padding=10)
        frame_top.pack(fill=tk.X)

        self.directory_label = ttkb.Label(frame_top, text="未选择目录", bootstyle="primary", anchor="w")
        self.directory_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        select_button = ttkb.Button(frame_top, text="选择目录", bootstyle="success", command=self.select_directory)
        select_button.pack(side=tk.LEFT, padx=5)

        save_txt_button = ttkb.Button(frame_top, text="保存为文本", bootstyle="info", command=self.save_as_text)
        save_txt_button.pack(side=tk.LEFT, padx=5)

        save_json_button = ttkb.Button(frame_top, text="保存为 JSON", bootstyle="warning", command=self.save_as_json)
        save_json_button.pack(side=tk.LEFT, padx=5)

        # 中间框架：显示目录结构（Treeview + 滚动条）
        frame_middle = ttkb.Frame(self.root)
        frame_middle.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.tree = ttkb.Treeview(frame_middle, selectmode="browse")
        self.tree.heading("#0", text="目录结构", anchor="w")

        # 垂直滚动条
        y_scrollbar = ttkb.Scrollbar(frame_middle, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scrollbar.set)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 绑定滚轮事件到 Treeview
        self.tree.bind("<Enter>", self.bind_tree_scroll)
        self.tree.bind("<Leave>", self.unbind_tree_scroll)

        # 底部框架：复选框区域（添加滚动条支持）
        frame_bottom = ttkb.Frame(self.root, padding=10)
        frame_bottom.pack(fill=tk.BOTH, expand=True)

        self.checkbox_canvas = tk.Canvas(frame_bottom)
        self.checkbox_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttkb.Scrollbar(frame_bottom, orient=tk.VERTICAL, command=self.checkbox_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.checkbox_canvas.configure(yscrollcommand=scrollbar.set)
        self.checkbox_frame = ttkb.Frame(self.checkbox_canvas)

        self.checkbox_window = self.checkbox_canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")

        # 绑定滚动事件到 Canvas
        self.checkbox_canvas.bind("<Enter>", self.bind_canvas_scroll)
        self.checkbox_canvas.bind("<Leave>", self.unbind_canvas_scroll)

        # 动态调整 Canvas 的滚动区域
        self.checkbox_frame.bind("<Configure>", self.on_checkbox_frame_configure)
        self.checkbox_canvas.bind("<Configure>", self.on_canvas_configure)

    def bind_tree_scroll(self, event):
        """绑定 Treeview 的滚轮事件"""
        self.root.bind_all("<MouseWheel>", self.on_tree_scroll)

    def unbind_tree_scroll(self, event):
        """解绑 Treeview 的滚轮事件"""
        self.root.unbind_all("<MouseWheel>")

    def on_tree_scroll(self, event):
        """处理 Treeview 的滚轮事件"""
        self.tree.yview_scroll(-1 * int(event.delta / 120), "units")

    def bind_canvas_scroll(self, event):
        """绑定 Canvas 的滚轮事件"""
        self.root.bind_all("<MouseWheel>", self.on_canvas_scroll)

    def unbind_canvas_scroll(self, event):
        """解绑 Canvas 的滚轮事件"""
        self.root.unbind_all("<MouseWheel>")

    def on_canvas_scroll(self, event):
        """处理 Canvas 的滚轮事件"""
        self.checkbox_canvas.yview_scroll(-1 * int(event.delta / 120), "units")

    def on_checkbox_frame_configure(self, event):
        """更新 Canvas 的滚动区域"""
        self.checkbox_canvas.configure(scrollregion=self.checkbox_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """当 Canvas 尺寸改变时调整窗口大小"""
        canvas_width = event.width
        self.checkbox_canvas.itemconfig(self.checkbox_window, width=canvas_width)

    def select_directory(self):
        """通过文件对话框选择目录"""
        self.selected_dir = filedialog.askdirectory()
        if self.selected_dir:
            self.directory_label.config(text=self.selected_dir)
            self.show_directory_structure()

    def show_directory_structure(self):
        """递归显示目录结构，并生成复选框"""
        if not self.selected_dir:
            messagebox.showerror("错误", "请先选择一个目录！")
            return

        # 清空 Treeview 和复选框区域
        self.tree.delete(*self.tree.get_children())
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.check_vars.clear()

        def add_tree_item(parent, path):
            """添加树形控件的节点"""
            folder_name = os.path.basename(path)
            folder_id = self.tree.insert(parent, "end", text=folder_name, open=True)

            # 添加复选框变量
            if path not in self.check_vars:
                self.check_vars[path] = tk.BooleanVar(value=True)

            # 在复选框区域添加复选框
            cb = ttkb.Checkbutton(
                self.checkbox_frame,
                text=f"{folder_name} 显示文件",
                variable=self.check_vars[path],
                bootstyle="round-toggle",
                command=self.update_view
            )
            cb.pack(anchor="w", padx=5, pady=2)

            # 遍历子文件夹和文件
            try:
                items = sorted(os.listdir(path))
            except PermissionError:
                items = []

            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    add_tree_item(folder_id, item_path)
                elif self.check_vars[path].get():  # 仅当复选框选中时，显示文件
                    self.tree.insert(folder_id, "end", text=item)

        # 添加顶层目录
        add_tree_item("", self.selected_dir)

    def update_view(self):
        """根据复选框状态更新 Treeview 显示"""
        if not self.selected_dir:
            return

        # 清空 Treeview
        self.tree.delete(*self.tree.get_children())

        def add_tree_item(parent, path):
            """动态更新 Treeview 节点"""
            folder_name = os.path.basename(path)
            folder_id = self.tree.insert(parent, "end", text=folder_name, open=True)

            # 遍历子文件夹和文件
            try:
                items = sorted(os.listdir(path))
            except PermissionError:
                items = []

            for item in items:
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    add_tree_item(folder_id, item_path)
                elif self.check_vars[path].get():  # 仅当复选框选中时，显示文件
                    self.tree.insert(folder_id, "end", text=item)

        # 重新加载目录结构
        add_tree_item("", self.selected_dir)

    def save_as_text(self):
        """保存目录结构到文本文件"""
        if not self.selected_dir:
            messagebox.showerror("错误", "请先选择一个目录！")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                self.write_treeview_to_file(f, "")
            messagebox.showinfo("成功", f"目录结构已保存到 {save_path}")

    def save_as_json(self):
        """保存目录结构到 JSON 文件"""
        if not self.selected_dir:
            messagebox.showerror("错误", "请先选择一个目录！")
            return

        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")]
        )
        if save_path:
            directory_json = self.generate_treeview_json("")
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(directory_json, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("成功", f"目录结构已保存到 {save_path}")

    def write_treeview_to_file(self, file, parent, indent=""):
        """递归写入 Treeview 的内容到文件"""
        for child in self.tree.get_children(parent):
            text = self.tree.item(child, "text")
            file.write(f"{indent}{text}/\n")
            self.write_treeview_to_file(file, child, indent + "    ")

    def generate_treeview_json(self, parent):
        """递归生成 Treeview 的 JSON 表示"""
        result = {}
        for child in self.tree.get_children(parent):
            text = self.tree.item(child, "text")
            result[text] = self.generate_treeview_json(child)
        return result


# 创建主窗口
root = ttkb.Window(themename="cosmo")
app = DirectoryViewerApp(root)
root.mainloop()
