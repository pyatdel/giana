import re
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

VALID_GENRES = {'RPG', 'ACT', 'SIM', 'ADV', 'VOD', 'SHT', 'NOV', 'ANO'}
DEFAULT_EXTENSIONS = ['.zip', '.rar', '.7z', '']

class ModernUI:
    @staticmethod
    def setup_styles():
        colors = {
            'primary': '#2C3E50',
            'secondary': '#34495E',
            'accent': '#3498DB',
            'success': '#2ECC71',
            'warning': '#F1C40F',
            'error': '#E74C3C',
            'background': '#ECF0F1',
            'text': '#2C3E50'
        }

        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('modern.TFrame', background=colors['background'])
        style.configure('modern.TLabelframe', background=colors['background'])
        style.configure('modern.TLabelframe.Label', 
                       background=colors['background'],
                       font=('Malgun Gothic', 9, 'bold'))
        
        style.configure('modern.TButton',
                       padding=10,
                       font=('Malgun Gothic', 9))
        
        style.configure('modern.TEntry',
                       padding=5,
                       font=('Malgun Gothic', 9))
        
        style.configure('modern.Treeview',
                       font=('Malgun Gothic', 9),
                       rowheight=25)
        style.configure('modern.Treeview.Heading',
                       font=('Malgun Gothic', 9, 'bold'))

        style.configure('modern.TCheckbutton',
                       background=colors['background'],
                       font=('Malgun Gothic', 9))
        
        return colors

class ModernDraggableHeaderTreeview(ttk.Treeview):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.drag_data = None
        self.ghost_window = None
        self.ghost_label = None
        
        # Bind events to the header
        self.bind('<Button-1>', self.start_drag)
        self.bind('<B1-Motion>', self.drag)
        self.bind('<ButtonRelease-1>', self.stop_drag)
        
        # Keep track of column order
        self.column_order = list(self['columns'])

    def create_ghost_window(self, text):
        self.ghost_window = tk.Toplevel(self)
        self.ghost_window.overrideredirect(True)
        self.ghost_window.attributes('-alpha', 0.7)
        
        self.ghost_label = tk.Label(
            self.ghost_window,
            text=text,
            bg='#2C3E50',
            fg='white',
            relief='solid',
            borderwidth=1,
            pady=2,
            padx=5,
            font=('Malgun Gothic', 9)
        )
        self.ghost_label.pack()
        
        self.ghost_window.withdraw()
        self.ghost_label.update_idletasks()
        width = self.ghost_label.winfo_reqwidth()
        height = self.ghost_label.winfo_reqheight()
        self.ghost_window.geometry(f"{width}x{height}")

    def start_drag(self, event):
        region = self.identify_region(event.x, event.y)
        if region != "heading":
            return
            
        column = self.identify_column(event.x)
        if not column:
            return
            
        # Get column index
        column_index = int(column[1]) - 1
        if column_index < 0 or column_index >= len(self.column_order):
            return
            
        column_name = self.column_order[column_index]
        heading_text = self.heading(column_name)['text']
        
        self.drag_data = {
            'column': column_name,
            'text': heading_text,
            'x': event.x_root,
            'y': event.y_root,
            'index': column_index,
            'start_x': event.x
        }
        
        self.create_ghost_window(heading_text)
        self.ghost_window.geometry(f"+{event.x_root}+{event.y_root}")
        self.ghost_window.deiconify()

    def drag(self, event):
        if not self.drag_data:
            return
            
        x_offset = event.x_root - self.drag_data['x']
        y_offset = event.y_root - self.drag_data['y']
        
        new_x = self.drag_data['x'] + x_offset
        new_y = self.drag_data['y'] + y_offset
        
        if self.ghost_window:
            self.ghost_window.geometry(f"+{new_x}+{new_y}")
        
        target_column = self.identify_column(event.x)
        if target_column:
            target_index = int(target_column[1]) - 1
            if target_index >= 0 and target_index < len(self.column_order):
                current_index = self.drag_data['index']
                if target_index != current_index:
                    # 드래그 거리 계산
                    drag_distance = abs(event.x - self.drag_data['start_x'])
                    
                    # 컬럼 너비의 절반 이상 이동했을 때만 위치 변경
                    min_move = self.column(self.column_order[current_index], "width") // 2
                    
                    if drag_distance > min_move:
                        # 위치 전환
                        column = self.column_order.pop(current_index)
                        self.column_order.insert(target_index, column)
                        
                        # 컬럼 표시 순서 업데이트
                        self['displaycolumns'] = self.column_order
                        
                        # 드래그 시작 위치 업데이트
                        self.drag_data['index'] = target_index
                        self.drag_data['start_x'] = event.x
                        
                        self.event_generate('<<TreeviewColumnReordered>>')

    def stop_drag(self, event):
        if self.ghost_window:
            self.ghost_window.destroy()
            self.ghost_window = None
            self.ghost_label = None
        
        self.drag_data = None

    def get_column_order(self):
        return self.column_order

    def on_destroy(self):
        if self.ghost_window:
            self.ghost_window.destroy()

def validate_name(name):
    patterns = [
        (r'^\[(.+?)\]-\[([RV]J\d+)\] (.+?) \(([A-Z]+)\)_DLsite.*$', 'DLsite'),
        (r'^\[(.+?)\]-\[(v\d+)\] (.+?) \(([A-Z]+)\)_VNdb.*$', 'VNdb'),
        (r'^\[(.+?)\]-\[(\d+)\] (.+?) \(([A-Z]+)\)_Getchu.*$', 'Getchu'),
        (r'^\[(.+?)\]-\[(.+?)\] (.+?) \(([A-Z]+)\)_Fanza.*$', 'Fanza'),
        (r'^\[(.+?)\]-\[(.+?)\] (.+?) \(([A-Z]+)\)_Steam.*$', 'Steam')
    ]

    for pattern, platform in patterns:
        match = re.match(pattern, name)
        if match:
            creator, unique_id, game_title, genre = match.groups()

            if genre not in VALID_GENRES:
                return False, None

            if platform == 'DLsite' and not unique_id.startswith(('RJ', 'VJ')):
                return False, None

            if platform == 'VNdb' and not unique_id.startswith('v'):
                return False, None

            if platform == 'Getchu' and not unique_id.isdigit():
                return False, None

            return True, {
                "creator": creator,
                "unique_id": unique_id,
                "game_title": game_title,
                "genre": genre,
                "platform": platform
            }

    return False, None

def get_items_in_path(path, extensions):
    items = []
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)):
            if os.path.splitext(item)[1].lower() in extensions or '' in extensions:
                items.append(item)
        elif os.path.isdir(os.path.join(path, item)) and '' in extensions:
            items.append(item)
    return items

def classify_items(items):
    valid_items = []
    invalid_items = []
    unique_ids = {}
    
    for item in items:
        is_valid, item_info = validate_name(item)
        if is_valid:
            unique_id = item_info['unique_id']
            if unique_id in unique_ids:
                unique_ids[unique_id].append(item)
            else:
                unique_ids[unique_id] = [item]
            valid_items.append((item, item_info))
        else:
            invalid_items.append(item)
    
    duplicate_items = [item for items in unique_ids.values() if len(items) > 1 for item in items]
    
    return valid_items, invalid_items, duplicate_items

class ModernRenameWindow(tk.Toplevel):
    def __init__(self, parent, selected_items, path, callback):
        super().__init__(parent)
        self.title("이름 변경 및 순서 변경")
        
        window_width = 1400
        window_height = 800
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        self.minsize(1200, 700)
        
        self.configure(bg='#ECF0F1')
        
        self.selected_items = selected_items
        self.path = path
        self.callback = callback
        self.colors = ModernUI.setup_styles()

        self.name_parts = ['creator', 'unique_id', 'game_title', 'genre', 'platform']
        self.name_parts_korean = {
            'creator': '제작자',
            'unique_id': '고유 ID',
            'game_title': '게임 제목',
            'genre': '장르',
            'platform': '플랫폼'
        }
        self.edit_entries = {}
        
        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self, style='modern.TFrame')
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)

        left_frame = ttk.Frame(main_frame, style='modern.TFrame')
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 15))

        right_frame = ttk.Frame(main_frame, style='modern.TFrame')
        right_frame.pack(side="right", fill="both", expand=True)

        self.create_item_list(left_frame)
        self.create_edit_frame(right_frame)
        self.create_preview_list(right_frame)
        self.create_button_frame(right_frame)

    def create_item_list(self, parent):
        list_frame = ttk.LabelFrame(parent, text="파일/폴더 목록", style='modern.TLabelframe')
        list_frame.pack(fill="both", expand=True)

        self.item_tree = ttk.Treeview(list_frame, columns=("Item",), 
                                    show="headings", style='modern.Treeview')
        self.item_tree.heading("Item", text="이름")
        self.item_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", 
                                command=self.item_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.item_tree.configure(yscrollcommand=scrollbar.set)

        for item in self.selected_items:
            self.item_tree.insert("", "end", values=(item,))

        self.item_tree.bind("<<TreeviewSelect>>", self.on_item_select)

    def create_edit_frame(self, parent):
        edit_frame = ttk.LabelFrame(parent, text="항목 편집", style='modern.TLabelframe')
        edit_frame.pack(fill="x", pady=(0, 10))

        entry_frame = ttk.Frame(edit_frame, style='modern.TFrame')
        entry_frame.pack(fill="both", expand=True, padx=10, pady=10)

        for part in self.name_parts:
            ttk.Label(entry_frame, text=f"{self.name_parts_korean[part]}:",
                     background=self.colors['background'],
                     font=('Malgun Gothic', 9)).pack(anchor="w", pady=(5, 0))
            entry = ttk.Entry(entry_frame, style='modern.TEntry')
            entry.bind('<KeyRelease>', lambda e: self.update_preview_list())
            entry.pack(fill="x", pady=(0, 5))
            self.edit_entries[part] = entry

    def create_preview_list(self, parent):
        preview_frame = ttk.LabelFrame(parent, text="미리보기", style='modern.TLabelframe')
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.preview_tree = ModernDraggableHeaderTreeview(
            preview_frame,
            columns=("Creator", "ID", "Title", "Genre", "Platform"),
            show="headings",
            style='modern.Treeview'
        )

        # Set up headings with Korean text
        column_names = {
            "Creator": "제작자",
            "ID": "고유 ID",
            "Title": "게임 제목",
            "Genre": "장르",
            "Platform": "플랫폼"
        }

        for col, text in column_names.items():
            self.preview_tree.heading(col, text=text)
            self.preview_tree.column(col, width=100)
        
        self.preview_tree.column("Title", width=400)

        self.preview_tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical",
                               command=self.preview_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.preview_tree.configure(yscrollcommand=scrollbar.set)
        
        self.preview_tree.bind('<<TreeviewColumnReordered>>', self.on_column_reorder)

    def create_button_frame(self, parent):
        button_frame = ttk.Frame(parent, style='modern.TFrame')
        button_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(button_frame, text="변경 적용",
                 style='modern.TButton',
                 command=self.apply_changes).pack(side="left")

    def on_item_select(self, event):
        selected_items = self.item_tree.selection()
        if len(selected_items) == 1:
            item = self.item_tree.item(selected_items[0])['values'][0]
            is_valid, info = validate_name(item)
            if is_valid:
                for part in self.name_parts:
                    self.edit_entries[part].config(state="normal")
                    self.edit_entries[part].delete(0, tk.END)
                    self.edit_entries[part].insert(0, info[part])
        else:
            for entry in self.edit_entries.values():
                entry.delete(0, tk.END)
                entry.config(state="disabled")

        self.update_preview_list()

    def on_column_reorder(self, event):
        """Handle column reordering and update file names accordingly"""
        # Get the new column order
        new_order = self.preview_tree.get_column_order()
        
        # Create mapping between display columns and name parts
        column_to_part = {
            "Creator": "creator",
            "ID": "unique_id",
            "Title": "game_title",
            "Genre": "genre",
            "Platform": "platform"
        }
        
        # Update name_parts order based on column order
        self.name_parts = [column_to_part[col] for col in new_order]
        
        # Update preview list to reflect new order
        self.update_preview_list()

    def get_new_name(self, old_name):
        is_valid, info = validate_name(old_name)
        if is_valid:
            if len(self.item_tree.selection()) == 1:
                new_info = {part: self.edit_entries[part].get() for part in self.name_parts}
            else:
                new_info = info

            # Use the current column order to construct the file name
            ordered_parts = []
            for part in self.name_parts:
                ordered_parts.append(new_info[part])

            return f"[{ordered_parts[0]}]-[{ordered_parts[1]}] {ordered_parts[2]} ({ordered_parts[3]})_{ordered_parts[4]}"
        return old_name

    def update_preview_list(self):
        self.preview_tree.delete(*self.preview_tree.get_children())
        selected_items = self.item_tree.selection()
        for item in selected_items:
            old_name = self.item_tree.item(item)['values'][0]
            is_valid, info = validate_name(old_name)
            if is_valid:
                if len(selected_items) == 1:
                    # Use values from entry fields for single selection
                    self.preview_tree.insert("", "end", values=(
                        self.edit_entries['creator'].get(),
                        self.edit_entries['unique_id'].get(),
                        self.edit_entries['game_title'].get(),
                        self.edit_entries['genre'].get(),
                        self.edit_entries['platform'].get()
                    ))
                else:
                    # Use original values for multiple selection
                    self.preview_tree.insert("", "end", values=(
                        info['creator'],
                        info['unique_id'],
                        info['game_title'],
                        info['genre'],
                        info['platform']
                    ))
            else:
                self.preview_tree.insert("", "end", values=("-", "-", "-", "-", "-"))

    def apply_changes(self):
        selected_items = self.item_tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "변경할 항목을 선택해주세요.")
            return

        renamed_count = 0
        for item in selected_items:
            old_name = self.item_tree.item(item)['values'][0]
            new_name = self.get_new_name(old_name)
            if old_name != new_name:
                if self.perform_rename(old_name, new_name):
                    self.item_tree.item(item, values=(new_name,))
                    renamed_count += 1

        self.update_preview_list()
        messagebox.showinfo("완료", f"{renamed_count}개 항목의 이름을 변경했습니다.")
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
            messagebox.showerror("오류", f"{old_name} 변경 중 오류 발생:\n{str(e)}")
            return False

class ModernGameItemValidatorApp:
    def __init__(self, master):
        self.master = master
        self.master.title("게임 파일/폴더명 검증 및 수정 프로그램")
        
        window_width = 1400
        window_height = 800
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.master.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        self.master.minsize(1200, 700)
        
        self.colors = ModernUI.setup_styles()
        
        self.path_var = tk.StringVar()
        self.create_widgets()

    def create_widgets(self):
        main_container = ttk.Frame(self.master, style='modern.TFrame')
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.create_header_frame(main_container)
        
        content_frame = ttk.Frame(main_container, style='modern.TFrame')
        content_frame.pack(fill="both", expand=True, pady=(20, 0))
        
        self.create_extension_frame(content_frame)
        self.create_result_tree(content_frame)
        self.create_action_buttons(content_frame)

    def create_header_frame(self, parent):
        header_frame = ttk.Frame(parent, style='modern.TFrame')
        header_frame.pack(fill="x", pady=(0, 10))

        title_label = ttk.Label(header_frame, 
                            text="게임 파일/폴더명 검증 및 수정 프로그램",
                            font=('Malgun Gothic', 16, 'bold'),
                            background=self.colors['background'])
        title_label.pack(side="top", anchor="w", pady=(0, 10))

        path_frame = ttk.Frame(header_frame, style='modern.TFrame')
        path_frame.pack(fill="x")

        path_label = ttk.Label(path_frame, 
                           text="폴더 경로:",
                           font=('Malgun Gothic', 9, 'bold'),
                           background=self.colors['background'])
        path_label.pack(side="left", padx=(0, 10))

        path_entry = ttk.Entry(path_frame,
                           textvariable=self.path_var,
                           style='modern.TEntry')
        path_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))

        browse_button = ttk.Button(path_frame,
                               text="폴더 선택",
                               style='modern.TButton',
                               command=self.browse_folder)
        browse_button.pack(side="left", padx=(0, 10))

        validate_button = ttk.Button(path_frame,
                                 text="검증",
                                 style='modern.TButton',
                                 command=self.validate_items)
        validate_button.pack(side="left")

    def create_extension_frame(self, parent):
        extensions_frame = ttk.LabelFrame(parent,
                                      text="파일 확장자",
                                      style='modern.TLabelframe')
        extensions_frame.pack(fill="x", pady=(0, 20))

        extension_container = ttk.Frame(extensions_frame, style='modern.TFrame')
        extension_container.pack(fill="x", padx=10, pady=10)

        self.extension_vars = {}
        for i, ext in enumerate(DEFAULT_EXTENSIONS):
            var = tk.BooleanVar(value=True)
            self.extension_vars[ext] = var
            
            cb = ttk.Checkbutton(extension_container,
                             text=ext if ext else "폴더/무확장자",
                             variable=var,
                             style='modern.TCheckbutton')
            cb.grid(row=i//4, column=i%4, padx=10, pady=5, sticky="w")

    def create_result_tree(self, parent):
        tree_frame = ttk.Frame(parent, style='modern.TFrame')
        tree_frame.pack(fill="both", expand=True, pady=(0, 10))

        self.result_tree = ttk.Treeview(tree_frame,
                                    columns=("Item", "Status", "Platform", "Genre", "ID"),
                                    show="headings",
                                    style='modern.Treeview')

        self.result_tree.heading("Item", text="파일/폴더명",
                             command=lambda: self.treeview_sort_column("Item", False))
        self.result_tree.heading("Status", text="상태",
                             command=lambda: self.treeview_sort_column("Status", False))
        self.result_tree.heading("Platform", text="플랫폼",
                             command=lambda: self.treeview_sort_column("Platform", False))
        self.result_tree.heading("Genre", text="장르",
                             command=lambda: self.treeview_sort_column("Genre", False))
        self.result_tree.heading("ID", text="고유 ID",
                             command=lambda: self.treeview_sort_column("ID", False))

        self.result_tree.column("Item", width=500)
        self.result_tree.column("Status", width=100)
        self.result_tree.column("Platform", width=100)
        self.result_tree.column("Genre", width=100)
        self.result_tree.column("ID", width=100)

        self.result_tree.tag_configure("valid", background=self.colors['success'])
        self.result_tree.tag_configure("invalid", background=self.colors['error'])
        self.result_tree.tag_configure("duplicate", background=self.colors['warning'])

        scrollbar = ttk.Scrollbar(tree_frame,
                              orient="vertical",
                              command=self.result_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        self.result_tree.pack(side="left", fill="both", expand=True)

    def create_action_buttons(self, parent):
        button_frame = ttk.Frame(parent, style='modern.TFrame')
        button_frame.pack(fill="x", pady=(0, 10))

        rename_button = ttk.Button(button_frame,
                               text="선택 항목 이름 변경",
                               style='modern.TButton',
                               command=self.open_rename_window)
        rename_button.pack(side="left")

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.path_var.set(folder_path)

    def validate_items(self):
        path = self.path_var.get()
        if not path:
            messagebox.showwarning("경고", "폴더를 선택해주세요.")
            return

        extensions = [ext for ext, var in self.extension_vars.items() if var.get()]
        items = get_items_in_path(path, extensions)
        valid, invalid, duplicate = classify_items(items)

        self.result_tree.delete(*self.result_tree.get_children())

        for item, info in valid:
            status = "유효"
            tag = "valid"
            if item in duplicate:
                status = "중복"
                tag = "duplicate"
            self.result_tree.insert("", "end",
                                values=(item, status, info['platform'],
                                       info['genre'], info['unique_id']),
                                tags=(tag,))

        for item in invalid:
            self.result_tree.insert("", "end",
                                values=(item, "유효하지 않음", "-", "-", "-"),
                                tags=("invalid",))

        messagebox.showinfo("검증 완료",
                        f"총 항목 수: {len(items)}\n"
                        f"유효한 항목 수: {len(valid)}\n"
                        f"유효하지 않은 항목 수: {len(invalid)}\n"
                        f"중복된 항목 수: {len(duplicate)}")

    def treeview_sort_column(self, col, reverse):
        l = [(self.result_tree.set(k, col), k) for k in self.result_tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.result_tree.move(k, '', index)

        self.result_tree.heading(col,
                             command=lambda: self.treeview_sort_column(col, not reverse))

    def open_rename_window(self):
        selected_items = self.result_tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "변경할 항목을 선택해주세요.")
            return

        selected_names = [self.result_tree.item(item)["values"][0] 
                       for item in selected_items]
        ModernRenameWindow(self.master, selected_names, 
                        self.path_var.get(), self.validate_items)

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernGameItemValidatorApp(root)
    root.mainloop()