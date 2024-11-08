import tkinter as tk
from tkinter import ttk, messagebox
import os
from utils import validate_name

class RenameWindow(tk.Toplevel):
    def __init__(self, parent, selected_items, path, callback):
        super().__init__(parent)
        self.title("이름 변경")
        self.geometry("1200x700")
        self.selected_items = selected_items
        self.path = path
        self.callback = callback

        self.name_parts = ['creator', 'unique_id', 'game_title', 'genre', 'platform']
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True)

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        self.create_item_list(left_frame)
        self.create_edit_frame(right_frame)
        self.create_preview_frame(right_frame)
        self.create_button_frame(right_frame)

    def create_item_list(self, parent):
        list_frame = ttk.LabelFrame(parent, text="파일/폴더 목록")
        list_frame.pack(fill="both", expand=True)

        self.item_tree = ttk.Treeview(list_frame, columns=("Item",), show="headings")
        self.item_tree.heading("Item", text="파일/폴더명")
        self.item_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.item_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.item_tree.configure(yscrollcommand=scrollbar.set)

        for item in self.selected_items:
            self.item_tree.insert("", "end", values=(item,))

        self.item_tree.bind("<<TreeviewSelect>>", self.on_item_select)

    def create_edit_frame(self, parent):
        edit_frame = ttk.LabelFrame(parent, text="항목 편집")
        edit_frame.pack(fill="x", pady=(0, 10))

        order_frame = ttk.Frame(edit_frame)
        order_frame.pack(side="left", fill="y", padx=(0, 10))

        self.order_listbox = tk.Listbox(order_frame, height=10)
        self.order_listbox.pack(side="left", fill="both", expand=True)

        button_frame = ttk.Frame(order_frame)
        button_frame.pack(side="left", fill="y", padx=(5, 0))

        ttk.Button(button_frame, text="↑", command=self.move_up).pack(fill="x", pady=(0, 5))
        ttk.Button(button_frame, text="↓", command=self.move_down).pack(fill="x")

        for part in self.name_parts:
            self.order_listbox.insert(tk.END, part)

        entry_frame = ttk.Frame(edit_frame)
        entry_frame.pack(side="left", fill="both", expand=True)

        self.edit_entries = {}
        for part in self.name_parts:
            ttk.Label(entry_frame, text=part).pack(anchor="w")
            entry = ttk.Entry(entry_frame)
            entry.pack(fill="x", padx=5, pady=2)
            self.edit_entries[part] = entry

    def create_preview_frame(self, parent):
        preview_frame = ttk.LabelFrame(parent, text="미리보기")
        preview_frame.pack(fill="x", pady=(0, 10))

        self.preview_var = tk.StringVar()
        ttk.Label(preview_frame, textvariable=self.preview_var, wraplength=400).pack(fill="x", padx=5, pady=5)

    def create_button_frame(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(button_frame, text="미리보기 업데이트", command=self.update_preview).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="선택 항목 이름 변경", command=self.rename_item).pack(side="left", padx=(0, 5))
        ttk.Button(button_frame, text="모든 항목 이름 변경", command=self.rename_all_items).pack(side="left")

    def on_item_select(self, event):
        selected_items = self.item_tree.selection()
        if selected_items:
            item = self.item_tree.item(selected_items[0])['values'][0]
            is_valid, info = validate_name(item)
            if is_valid:
                for part in self.name_parts:
                    self.edit_entries[part].delete(0, tk.END)
                    self.edit_entries[part].insert(0, info[part])
            self.update_preview()

    def move_up(self):
        selected = self.order_listbox.curselection()
        if selected and selected[0] > 0:
            text = self.order_listbox.get(selected[0])
            self.order_listbox.delete(selected[0])
            self.order_listbox.insert(selected[0]-1, text)
            self.order_listbox.selection_set(selected[0]-1)
            self.update_preview()

    def move_down(self):
        selected = self.order_listbox.curselection()
        if selected and selected[0] < self.order_listbox.size()-1:
            text = self.order_listbox.get(selected[0])
            self.order_listbox.delete(selected[0])
            self.order_listbox.insert(selected[0]+1, text)
            self.order_listbox.selection_set(selected[0]+1)
            self.update_preview()

    def update_preview(self):
        new_name_parts = {part: self.edit_entries[part].get() for part in self.name_parts}
        ordered_parts = [new_name_parts[self.order_listbox.get(i)] for i in range(self.order_listbox.size())]
        new_name = f"[{ordered_parts[0]}]-[{ordered_parts[1]}] {ordered_parts[2]} ({ordered_parts[3]})_{ordered_parts[4]}"
        self.preview_var.set(new_name)

    def rename_item(self):
        selected_items = self.item_tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "변경할 항목을 선택해주세요.")
            return

        old_name = self.item_tree.item(selected_items[0])['values'][0]
        new_name = self.preview_var.get()

        if self.perform_rename(old_name, new_name):
            self.item_tree.item(selected_items[0], values=(new_name,))
            messagebox.showinfo("이름 변경 완료", "항목의 이름을 변경했습니다.")

    def rename_all_items(self):
        renamed_count = 0
        for item in self.item_tree.get_children():
            old_name = self.item_tree.item(item)['values'][0]
            is_valid, info = validate_name(old_name)
            if is_valid:
                new_name_parts = {part: info[part] for part in self.name_parts}
                ordered_parts = [new_name_parts[self.order_listbox.get(i)] for i in range(self.order_listbox.size())]
                new_name = f"[{ordered_parts[0]}]-[{ordered_parts[1]}] {ordered_parts[2]} ({ordered_parts[3]})_{ordered_parts[4]}"
                if self.perform_rename(old_name, new_name):
                    self.item_tree.item(item, values=(new_name,))
                    renamed_count += 1

        messagebox.showinfo("이름 변경 완료", f"{renamed_count}개 항목의 이름을 변경했습니다.")
        self.callback()

    def perform_rename(self, old_name, new_name):
        old_path = os.path.join(self.path, old_name)
        new_path = os.path.join(self.path, new_name)

        if os.path.isfile(old_path):
            _, ext = os.path.splitext(old_name)
            new_path += ext

        try:
            os.rename(old_path, new_path)
            return True
        except Exception as e:
            messagebox.showerror("오류", f"{old_name} 변경 중 오류 발생: {str(e)}")
            return False