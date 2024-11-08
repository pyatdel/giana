import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from constants import DEFAULT_EXTENSIONS
from utils import classify_items, get_items_in_path
from rename_window import RenameWindow

class GameItemValidatorApp:
    def __init__(self, master):
        self.master = master
        master.title("게임 파일/폴더명 검증 및 수정 프로그램")
        master.geometry("1200x700")

        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(master, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=0, padx=10, pady=10)

        self.browse_button = ttk.Button(master, text="폴더 선택", command=self.browse_folder)
        self.browse_button.grid(row=0, column=1, padx=10, pady=10)

        self.validate_button = ttk.Button(master, text="검증", command=self.validate_items)
        self.validate_button.grid(row=0, column=2, padx=10, pady=10)

        # 확장자 선택 프레임
        self.extensions_frame = ttk.LabelFrame(master, text="확장자 선택 (빈칸은 폴더 포함)")
        self.extensions_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")

        self.extension_vars = {}
        for i, ext in enumerate(DEFAULT_EXTENSIONS):
            var = tk.BooleanVar(value=True)
            self.extension_vars[ext] = var
            ttk.Checkbutton(self.extensions_frame, text=ext if ext else "폴더/무확장자", variable=var).grid(row=i//4, column=i%4, padx=5, pady=5, sticky="w")

        self.custom_ext_var = tk.StringVar()
        self.custom_ext_entry = ttk.Entry(self.extensions_frame, textvariable=self.custom_ext_var, width=10)
        self.custom_ext_entry.grid(row=len(DEFAULT_EXTENSIONS)//4, column=len(DEFAULT_EXTENSIONS)%4, padx=5, pady=5)
        ttk.Button(self.extensions_frame, text="추가", command=self.add_custom_extension).grid(row=len(DEFAULT_EXTENSIONS)//4, column=(len(DEFAULT_EXTENSIONS)%4)+1, padx=5, pady=5)

        self.result_tree = ttk.Treeview(master, columns=("Item", "Status", "Platform", "Genre", "ID"), show="headings")
        self.result_tree.heading("Item", text="파일/폴더명", command=lambda: self.treeview_sort_column("Item", False))
        self.result_tree.heading("Status", text="상태", command=lambda: self.treeview_sort_column("Status", False))
        self.result_tree.heading("Platform", text="플랫폼", command=lambda: self.treeview_sort_column("Platform", False))
        self.result_tree.heading("Genre", text="장르", command=lambda: self.treeview_sort_column("Genre", False))
        self.result_tree.heading("ID", text="고유 ID", command=lambda: self.treeview_sort_column("ID", False))
        self.result_tree.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.scrollbar = ttk.Scrollbar(master, orient="vertical", command=self.result_tree.yview)
        self.scrollbar.grid(row=2, column=3, sticky="ns")
        self.result_tree.configure(yscrollcommand=self.scrollbar.set)

        self.rename_button = ttk.Button(master, text="선택 항목 이름 변경", command=self.open_rename_window)
        self.rename_button.grid(row=3, column=0, padx=10, pady=10)

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(2, weight=1)

        self.result_tree.tag_configure("valid", background="lightgreen")
        self.result_tree.tag_configure("invalid", background="lightpink")
        self.result_tree.tag_configure("duplicate", background="lightyellow")

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.path_var.set(folder_path)

    def add_custom_extension(self):
        custom_ext = self.custom_ext_var.get().strip()
        if custom_ext and not custom_ext.startswith('.'):
            custom_ext = '.' + custom_ext
        if custom_ext and custom_ext not in self.extension_vars:
            var = tk.BooleanVar(value=True)
            self.extension_vars[custom_ext] = var
            row = (len(self.extension_vars) - 1) // 4
            col = (len(self.extension_vars) - 1) % 4
            ttk.Checkbutton(self.extensions_frame, text=custom_ext, variable=var).grid(row=row, column=col, padx=5, pady=5, sticky="w")
            self.custom_ext_var.set('')

    def get_selected_extensions(self):
        return [ext for ext, var in self.extension_vars.items() if var.get()]

    def validate_items(self):
        path = self.path_var.get()
        if not path:
            return

        extensions = self.get_selected_extensions()
        items = get_items_in_path(path, extensions)
        valid, invalid, duplicate = classify_items(items)

        self.result_tree.delete(*self.result_tree.get_children())

        for item, info in valid:
            status = "유효"
            tag = "valid"
            if item in duplicate:
                status = "중복"
                tag = "duplicate"
            self.result_tree.insert("", "end", values=(item, status, info['platform'], info['genre'], info['unique_id']), tags=(tag,))

        for item in invalid:
            self.result_tree.insert("", "end", values=(item, "유효하지 않음", "-", "-", "-"), tags=("invalid",))

        messagebox.showinfo("검증 완료", 
                            f"총 항목 수: {len(items)}\n"
                            f"유효한 항목 수: {len(valid)}\n"
                            f"유효하지 않은 항목 수: {len(invalid)}\n"
                            f"중복된 고유 번호 항목 수: {len(duplicate)}")

    def treeview_sort_column(self, col, reverse):
        l = [(self.result_tree.set(k, col), k) for k in self.result_tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.result_tree.move(k, '', index)

        self.result_tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))

    def open_rename_window(self):
        selected_items = self.result_tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "변경할 항목을 선택해주세요.")
            return

        selected_names = [self.result_tree.item(item, "values")[0] for item in selected_items]
        RenameWindow(self.master, selected_names, self.path_var.get(), self.validate_items)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameItemValidatorApp(root)
    root.mainloop()