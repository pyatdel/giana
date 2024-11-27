import re
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import time
from PIL import Image, ImageTk
import io

VALID_GENRES = {'RPG', 'ACT', 'SIM', 'ADV', 'VOD', 'SHT', 'NOV', 'ANO'}
DEFAULT_EXTENSIONS = ['.zip', '.rar', '.7z', '']

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
               rowheight=25,
               fieldbackground="white",  
               background="white")      
        style.configure('modern.Treeview.Heading',
                       font=('Malgun Gothic', 9, 'bold'))

        style.configure('modern.TCheckbutton',
                       background=colors['background'],
                       font=('Malgun Gothic', 9))
        
        style.configure('modern.TNotebook', 
                       background=colors['background'])
        style.configure('modern.TNotebook.Tab',
                       padding=[10, 5],
                       font=('Malgun Gothic', 9))
        
        style.map('modern.TNotebook.Tab',
                 background=[('selected', colors['accent']),
                            ('!selected', colors['secondary'])],
                 foreground=[('selected', 'white'),
                            ('!selected', 'white')])
        
        return colors

class ModernDraggableHeaderTreeview(ttk.Treeview):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        
        self.drag_data = None
        self.ghost_window = None
        self.ghost_label = None
        
        self.bind('<Button-1>', self.start_drag)
        self.bind('<B1-Motion>', self.drag)
        self.bind('<ButtonRelease-1>', self.stop_drag)
        
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
                    drag_distance = abs(event.x - self.drag_data['start_x'])
                    min_move = self.column(self.column_order[target_index], "width") // 2
                    
                    if drag_distance > min_move:
                        column = self.column_order.pop(current_index)
                        self.column_order.insert(target_index, column)
                        self['displaycolumns'] = self.column_order
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
        self.is_crawled = False
        self.image_urls = {}  # 이미지 URL을 저장할 딕셔너리 추가

        self.valid_genres = sorted(list(VALID_GENRES))
        self.valid_platforms = ['DLsite', 'VNdb', 'Getchu', 'Fanza', 'Steam']

        self.name_parts = ['creator', 'unique_id', 'game_title', 'genre', 'platform']
        self.name_parts_korean = {
            'creator': '제작자',
            'unique_id': '고유 ID',
            'game_title': '게임 제목',
            'genre': '장르',
            'platform': '플랫폼'
        }
        self.edit_entries = {}
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.create_widgets()

    def fetch_product_info(self, product_id):
        base_url = "https://www.dlsite.com/maniax/work/=/product_id/"
        locale = "/?locale=ko_KR"
        url = f"{base_url}{product_id}{locale}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        def get_tag_text(tag, default='N/A'):
            return tag.get_text(strip=True) if tag else default
        
        # 메인 이미지 URL 가져오기 (수정된 부분)
        try:
            # 방법 1: 작품 이미지 메타 태그
            img_tag = soup.find('meta', {'property': 'og:image'})
            if img_tag and 'content' in img_tag.attrs:
                image_url = img_tag['content']
            else:
                # 방법 2: 메인 이미지 태그
                img_tag = soup.find('img', {'class': 'slider_item'}) or \
                         soup.find('img', {'id': 'work_main_img'}) or \
                         soup.find('img', {'class': 'product-slider-data'}) or \
                         soup.find('div', {'class': 'product-slider-data'})
                
                if img_tag:
                    image_url = img_tag.get('src') or img_tag.get('data-src')
                else:
                    image_url = None
            
            # URL이 상대 경로인 경우 절대 경로로 변환
            if image_url and not image_url.startswith('http'):
                image_url = 'https:' + image_url
        except:
            image_url = None

        print(f"Found image URL: {image_url}")  # 디버깅용 출력

        # 게임 제목
        title_tag = soup.find('h1', itemprop='name', id='work_name')
        title = get_tag_text(title_tag)
        
        # 서클명
        try:
            circle_tag = soup.find('span', itemprop='brand', class_='maker_name').find('a')
            circle_name = get_tag_text(circle_tag)
        except:
            circle_name = 'N/A'

        # 장르
        genre_tags = soup.find('th', string='장르')
        if genre_tags:
            genre_tags = genre_tags.find_next_sibling('td').find_all('a')
        genres = [get_tag_text(genre) for genre in genre_tags] if genre_tags else []

        # 판매일
        sales_date_tag = soup.find('th', string='판매일')
        if sales_date_tag:
            sales_date_tag = sales_date_tag.find_next_sibling('td').find('a')
        sales_date = get_tag_text(sales_date_tag)

        # 파일 용량
        file_size_tag = soup.find('th', string='파일 용량')
        if file_size_tag:
            file_size_tag = file_size_tag.find_next_sibling('td').find('div', class_='main_genre')
        file_size = get_tag_text(file_size_tag)
        
        # 파일 용량 변환
        try:
            size_str = re.sub(r'[^\d.]', '', file_size)
            size_num = float(size_str)
            if 'MB' in file_size:
                file_size = size_num
            elif 'GB' in file_size:
                file_size = size_num * 1024
            else:
                file_size = 'Unknown'
        except:
            file_size = 'Unknown'

        # 버전 정보
        btn_ver_up_tag = soup.find('div', class_='btn_ver_up')

        # 일치도 계산
        confidence = 0
        if title != 'N/A':
            confidence += 40
        if circle_name != 'N/A':
            confidence += 30
        if genres:
            confidence += 30
            
        # DLsite의 장르를 프로그램의 장르로 매핑
        genre_mapping = {
            'アドベンチャー': 'ADV',
            'ロールプレイング': 'RPG',
            'シミュレーション': 'SIM',
            'アクション': 'ACT',
            '音声作品': 'VOD',
            'シューティング': 'SHT',
            'ノベル': 'NOV',
            'その他ゲーム': 'ANO'
        }
        
        mapped_genres = []
        for genre in genres:
            if genre in genre_mapping:
                mapped_genres.append(genre_mapping[genre])
        
        primary_genre = mapped_genres[0] if mapped_genres else 'ANO'

        return {
            'Platform': 'DLsite',
            'Title': title,
            'Creator': circle_name,
            'ID': product_id,
            'Genre': primary_genre,
            'ReleaseDate': sales_date,
            'FileSize': f"{file_size:,.0f}MB" if isinstance(file_size, (int, float)) else file_size,
            'Version': '업데이트 있음' if btn_ver_up_tag else '최신 버전',
            'Tags': ", ".join(genres),
            'Confidence': f"{confidence}%",
            'ImageURL': image_url
        }

    def download_image(self, url, product_id):
        if not url:
            messagebox.showerror("오류", "이미지 URL을 찾을 수 없습니다.")
            return None
            
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # 다운로드 폴더 생성
            download_dir = os.path.join(self.path, "downloaded_images")
            os.makedirs(download_dir, exist_ok=True)
            
            # 이미지 저장
            file_path = os.path.join(download_dir, f"{product_id}_main.jpg")
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            messagebox.showinfo("완료", f"이미지가 다음 경로에 저장되었습니다:\n{file_path}")
            return file_path
        except Exception as e:
            messagebox.showerror("오류", f"이미지 다운로드 중 오류 발생:\n{str(e)}")
            return None

    def show_image_preview(self, image_url, product_id):
        if not image_url:
            messagebox.showwarning("경고", "이미지를 찾을 수 없습니다.")
            return
            
        # 이미지 프리뷰 창 생성
        preview_window = tk.Toplevel(self)
        preview_window.title(f"이미지 프리뷰 - {product_id}")
        
        # 창 크기 및 위치 설정
        window_width = 800
        window_height = 600
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        preview_window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # 프레임 생성
        frame = ttk.Frame(preview_window, style='modern.TFrame')
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 이미지 다운로드 및 표시
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            
            # PIL Image로 변환
            image_data = Image.open(io.BytesIO(response.content))
            
            # 창 크기에 맞게 이미지 리사이즈
            display_size = (700, 500)  # 여백 고려
            image_data.thumbnail(display_size, Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(image_data)
            
            # 이미지 라벨
            image_label = ttk.Label(frame)
            image_label.configure(image=photo)
            image_label.image = photo  # 참조 유지
            image_label.pack(pady=(0, 10))
            
            # 다운로드 버튼
            download_button = ttk.Button(
                frame,
                text="이미지 다운로드",
                style='modern.TButton',
                command=lambda: self.download_image(image_url, product_id)
            )
            download_button.pack()
            
        except Exception as e:
            error_label = ttk.Label(
                frame,
                text=f"이미지 로드 중 오류 발생:\n{str(e)}",
                style='modern.TLabel'
            )
            error_label.pack()

    def create_widgets(self):
        main_frame = ttk.Frame(self, style='modern.TFrame')
        main_frame.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        
        main_frame.grid_columnconfigure(1, weight=3)
        main_frame.grid_rowconfigure(0, weight=1)

        left_frame = ttk.Frame(main_frame, style='modern.TFrame')
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        
        right_frame = ttk.Frame(main_frame, style='modern.TFrame')
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        self.create_item_list(left_frame)
        self.create_edit_frame(right_frame)
        self.create_preview_list(right_frame)
        self.create_button_frame(right_frame)

    def create_item_list(self, parent):
        list_frame = ttk.LabelFrame(parent, text="파일/폴더 목록", style='modern.TLabelframe')
        list_frame.grid(sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        container = ttk.Frame(list_frame)
        container.grid(sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        y_scroll = ttk.Scrollbar(container, orient="vertical")
        x_scroll = ttk.Scrollbar(container, orient="horizontal")

        self.item_tree = ttk.Treeview(
            container,
            columns=("Item",),
            show="headings",
            style='modern.Treeview',
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )

        y_scroll.config(command=self.item_tree.yview)
        x_scroll.config(command=self.item_tree.xview)

        self.item_tree.heading("Item", text="이름")
        self.item_tree.column("Item", width=300)

        self.item_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        for item in self.selected_items:
            self.item_tree.insert("", "end", values=(item,))

        self.item_tree.bind("<<TreeviewSelect>>", self.on_item_select)

    def create_edit_frame(self, parent):
        edit_frame = ttk.Frame(parent, style='modern.TFrame', padding=10)
        edit_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        title_label = ttk.Label(edit_frame, 
                            text="항목 편집",
                            font=('Malgun Gothic', 10, 'bold'),
                            background=self.colors['background'])
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        content_frame = ttk.Frame(edit_frame, style='modern.TFrame')
        content_frame.grid(row=1, column=0, sticky="ew")
        content_frame.grid_columnconfigure(1, weight=1)
        
        for i, part in enumerate(self.name_parts):
            row_frame = ttk.Frame(content_frame, style='modern.TFrame')
            row_frame.grid(row=i, column=0, columnspan=2, sticky="ew", pady=5)
            
            label = ttk.Label(
                row_frame, 
                text=f"{self.name_parts_korean[part]}:",
                background=self.colors['background'],
                font=('Malgun Gothic', 9)
            )
            label.grid(row=0, column=0, sticky="w", padx=(0, 10))
            
            if part == 'genre':
                entry = ttk.Combobox(row_frame, 
                                   values=self.valid_genres,
                                   font=('Malgun Gothic', 9),
                                   state="readonly")
                entry.bind('<<ComboboxSelected>>', lambda e: self.update_preview_list())
            elif part == 'platform':
                entry = ttk.Combobox(row_frame, 
                                   values=self.valid_platforms,
                                   font=('Malgun Gothic', 9),
                                   state="readonly")
                entry.bind('<<ComboboxSelected>>', lambda e: self.update_preview_list())
            else:
                entry = tk.Entry(row_frame, font=('Malgun Gothic', 9))
                entry.configure(background='white')
                entry.bind('<KeyRelease>', lambda e: self.update_preview_list())
            
            entry.grid(row=0, column=1, sticky="ew")
            self.edit_entries[part] = entry
            
            row_frame.grid_columnconfigure(1, weight=1)
            
    def update_preview_list(self):
        self.current_tree.delete(*self.current_tree.get_children())
        self.new_tree.delete(*self.new_tree.get_children())
        
        selected_items = self.item_tree.selection()
        
        for item in selected_items:
            old_name = self.item_tree.item(item)['values'][0]
            is_valid, info = validate_name(old_name)
            
            if is_valid:
                self.current_tree.insert("", "end", values=(
                    info['creator'],
                    info['unique_id'],
                    info['game_title'],
                    info['genre'],
                    info['platform']
                ))

                display_info = info.copy()
                if len(selected_items) > 1:
                    for part in self.name_parts:
                        current_value = self.edit_entries[part].get()
                        if current_value and current_value != "(다중 선택)":
                            display_info[part] = current_value
                else:
                    for part in self.name_parts:
                        display_info[part] = self.edit_entries[part].get()
                
                self.new_tree.insert("", "end", values=(
                    display_info['creator'],
                    display_info['unique_id'],
                    display_info['game_title'],
                    display_info['genre'],
                    display_info['platform']
                ))
            else:
                empty_values = ("-", "-", "-", "-", "-")
                self.current_tree.insert("", "end", values=empty_values)
                self.new_tree.insert("", "end", values=empty_values)

    def create_preview_list(self, parent):
        preview_frame = ttk.LabelFrame(parent, text="미리보기", style='modern.TLabelframe')
        preview_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)

        self.preview_notebook = ttk.Notebook(preview_frame, style='modern.TNotebook')
        self.preview_notebook.grid(row=0, column=0, sticky="nsew")

        # 현재 이름 탭
        current_tab = ttk.Frame(self.preview_notebook, style='modern.TFrame')
        self.preview_notebook.add(current_tab, text="현재 이름")

        # 새 이름 탭
        new_name_tab = ttk.Frame(self.preview_notebook, style='modern.TFrame')
        self.preview_notebook.add(new_name_tab, text="새 이름")

        # 크롤링 결과 탭
        crawling_tab = ttk.Frame(self.preview_notebook, style='modern.TFrame')
        self.preview_notebook.add(crawling_tab, text="크롤링 결과")

        # Current name tab
        current_container = ttk.Frame(current_tab)
        current_container.grid(row=0, column=0, sticky="nsew")
        current_container.grid_rowconfigure(0, weight=1)
        current_container.grid_columnconfigure(0, weight=1)

        current_y_scroll = ttk.Scrollbar(current_container, orient="vertical")
        current_x_scroll = ttk.Scrollbar(current_container, orient="horizontal")

        self.current_tree = ModernDraggableHeaderTreeview(
            current_container,
            columns=("Creator", "ID", "Title", "Genre", "Platform"),
            show="headings",
            style='modern.Treeview',
            yscrollcommand=current_y_scroll.set,
            xscrollcommand=current_x_scroll.set
        )

        current_y_scroll.config(command=self.current_tree.yview)
        current_x_scroll.config(command=self.current_tree.xview)

        column_names = {
            "Creator": ("제작자", 150),
            "ID": ("고유 ID", 100),
            "Title": ("게임 제목", 400),
            "Genre": ("장르", 100),
            "Platform": ("플랫폼", 100)
        }

        for col, (text, width) in column_names.items():
            self.current_tree.heading(col, text=text)
            self.current_tree.column(col, width=width, minwidth=50)

        self.current_tree.grid(row=0, column=0, sticky="nsew")
        current_y_scroll.grid(row=0, column=1, sticky="ns")
        current_x_scroll.grid(row=1, column=0, sticky="ew")

        # New name tab
        new_container = ttk.Frame(new_name_tab)
        new_container.grid(row=0, column=0, sticky="nsew")
        new_container.grid_rowconfigure(0, weight=1)
        new_container.grid_columnconfigure(0, weight=1)

        new_y_scroll = ttk.Scrollbar(new_container, orient="vertical")
        new_x_scroll = ttk.Scrollbar(new_container, orient="horizontal")

        self.new_tree = ModernDraggableHeaderTreeview(
            new_container,
            columns=("Creator", "ID", "Title", "Genre", "Platform"),
            show="headings",
            style='modern.Treeview',
            yscrollcommand=new_y_scroll.set,
            xscrollcommand=new_x_scroll.set,
        )

        new_y_scroll.config(command=self.new_tree.yview)
        new_x_scroll.config(command=self.new_tree.xview)

        for col, (text, width) in column_names.items():
            self.new_tree.heading(col, text=text)
            self.new_tree.column(col, width=width, minwidth=50)

        self.new_tree.grid(row=0, column=0, sticky="nsew")
        new_y_scroll.grid(row=0, column=1, sticky="ns")
        new_x_scroll.grid(row=1, column=0, sticky="ew")

        # Crawling results tab
        crawling_container = ttk.Frame(crawling_tab)
        crawling_container.grid(row=0, column=0, sticky="nsew")
        crawling_container.grid_rowconfigure(0, weight=1)
        crawling_container.grid_columnconfigure(0, weight=1)

        crawl_y_scroll = ttk.Scrollbar(crawling_container, orient="vertical")
        crawl_x_scroll = ttk.Scrollbar(crawling_container, orient="horizontal")

        self.crawl_tree = ModernDraggableHeaderTreeview(
            crawling_container,
            columns=("Platform", "Title", "Creator", "ID", "Genre", "ReleaseDate", "FileSize", "Version", "Tags", "Confidence", "Image"),
            show="headings",
            style='modern.Treeview',
            yscrollcommand=crawl_y_scroll.set,
            xscrollcommand=crawl_x_scroll.set
        )

        crawl_y_scroll.config(command=self.crawl_tree.yview)
        crawl_x_scroll.config(command=self.crawl_tree.xview)

        crawl_columns = {
            "Platform": ("플랫폼", 100),
            "Title": ("게임 제목", 300),
            "Creator": ("제작자", 150),
            "ID": ("고유 ID", 100),
            "Genre": ("장르", 100),
            "ReleaseDate": ("발매일", 100),
            "FileSize": ("용량", 100),
            "Version": ("버전", 100),
            "Tags": ("태그", 300),
            "Confidence": ("일치도", 100),
            "Image": ("이미지", 100)
        }

        for col, (text, width) in crawl_columns.items():
            self.crawl_tree.heading(col, text=text)
            self.crawl_tree.column(col, width=width, minwidth=50)

        self.crawl_tree.grid(row=0, column=0, sticky="nsew")
        crawl_y_scroll.grid(row=0, column=1, sticky="ns")
        crawl_x_scroll.grid(row=1, column=0, sticky="ew")

        # 이미지 프리뷰 버튼 바인딩
        self.crawl_tree.bind('<Double-1>', self.on_tree_double_click)

        for tab in [current_tab, new_name_tab, crawling_tab]:
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)

    def create_button_frame(self, parent):
        button_frame = ttk.Frame(parent, style='modern.TFrame')
        button_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        ttk.Button(button_frame, 
                  text="변경 적용",
                  style='modern.TButton',
                  command=self.apply_changes).grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        ttk.Button(button_frame,
                  text="웹 정보 가져오기",
                  style='modern.TButton',
                  command=self.crawl_info).grid(row=0, column=1, sticky="w")

    def on_tree_double_click(self, event):
        selection = self.crawl_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        item_id = self.crawl_tree.item(item)['values'][3]  # ID 컬럼
        
        # 이미지 URL을 딕셔너리에서 가져오기
        image_url = self.image_urls.get(item)
        
        if image_url:
            self.show_image_preview(image_url, item_id)
        else:
            messagebox.showwarning("경고", "이미지를 찾을 수 없습니다.")

    def crawl_info(self):
        selected_items = self.item_tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "크롤링할 항목을 선택해주세요.")
            return
        
        # 진행 상황을 보여주는 프로그레스 창 생성
        progress_window = tk.Toplevel(self)
        progress_window.title("크롤링 진행 중")
        
        # 화면 중앙에 위치
        window_width = 300
        window_height = 100
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        progress_window.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # 진행 상황 라벨
        progress_label = ttk.Label(
            progress_window, 
            text="크롤링 진행 중...", 
            font=('Malgun Gothic', 9),
            background=self.colors['background']
        )
        progress_label.pack(pady=10)
        
        # 프로그레스 바
        progress_bar = ttk.Progressbar(
            progress_window, 
            mode='determinate',
            length=200
        )
        progress_bar.pack(pady=10)
        
        # 크롤링 결과 트리 초기화
        self.crawl_tree.delete(*self.crawl_tree.get_children())
        
        total_items = len(selected_items)
        progress_bar['maximum'] = total_items
        
        def process_items():
            self.is_crawled = False  # 크롤링 시작 시 False로 설정
            for i, item in enumerate(selected_items, 1):
                old_name = self.item_tree.item(item)['values'][0]
                is_valid, info = validate_name(old_name)
                
                # 진행 상황 업데이트
                progress_label['text'] = f"크롤링 진행 중... ({i}/{total_items})"
                progress_bar['value'] = i
                
                if is_valid and info['platform'] == 'DLsite':
                    crawled_info = self.fetch_product_info(info['unique_id'])
                    if crawled_info:
                        tree_item = self.crawl_tree.insert("", "end", values=(
                            crawled_info['Platform'],
                            crawled_info['Title'],
                            crawled_info['Creator'],
                            crawled_info['ID'],
                            crawled_info['Genre'],
                            crawled_info['ReleaseDate'],
                            crawled_info['FileSize'],
                            crawled_info['Version'],
                            crawled_info['Tags'],
                            crawled_info['Confidence'],
                            "보기" if crawled_info['ImageURL'] else "없음"
                        ))
                        # 이미지 URL을 딕셔너리에 저장
                        self.image_urls[tree_item] = crawled_info['ImageURL']
                    else:
                        self.crawl_tree.insert("", "end", values=(
                            'DLsite', '조회 실패', '-', info['unique_id'], '-', '-', '-', '-', '-', '0%', '-'
                        ))
                else:
                    self.crawl_tree.insert("", "end", values=(
                        'DLsite', '유효하지 않은 이름', '-', '-', '-', '-', '-', '-', '-', '0%', '-'
                    ))
                
                # 각 아이템 처리 후 1초 대기
                time.sleep(1)
                
                # GUI 업데이트
                self.update()
            
            # 크롤링 완료 후
            self.is_crawled = True  # 크롤링 완료 표시
            progress_window.destroy()
            self.preview_notebook.select(2)  # 크롤링 결과 탭으로 전환
            messagebox.showinfo("완료", "크롤링이 완료되었습니다.")
        
        # 별도 스레드에서 실행하지 않고 메인 스레드에서 처리
        self.after(100, process_items)

    def on_item_select(self, event):
        selected_items = self.item_tree.selection()
        if len(selected_items) > 1:
            # 다중 선택 시
            for part in self.name_parts:
                if part in ['genre', 'platform']:
                    self.edit_entries[part].set('')  
                else:
                    self.edit_entries[part].delete(0, tk.END)
                    self.edit_entries[part].insert(0, "(다중 선택)")
        elif len(selected_items) == 1:
            # 단일 선택 시 
            item = self.item_tree.item(selected_items[0])['values'][0]
            is_valid, info = validate_name(item)
            if is_valid:
                for part in self.name_parts:
                    if part in ['genre', 'platform']:
                        self.edit_entries[part].set(info[part])
                    else:
                        self.edit_entries[part].delete(0, tk.END)
                        self.edit_entries[part].insert(0, info[part])
        else:
            # 선택 없음update_preview_list
            for part in self.name_parts:
                if part in ['genre', 'platform']:
                    self.edit_entries[part].set('')
                else:
                    self.edit_entries[part].delete(0, tk.END)

        self.update_preview_list()

    def get_new_name(self, old_name):
        is_valid, info = validate_name(old_name)
        if is_valid:
            if len(self.item_tree.selection()) == 1:
                new_info = {part: self.edit_entries[part].get() for part in self.name_parts}
            else:
                new_info = info.copy()
                for part in self.name_parts:
                    current_value = self.edit_entries[part].get()
                    if current_value and current_value != "(다중 선택)":
                        new_info[part] = current_value

            ordered_parts = [new_info[part] for part in self.name_parts]
            return f"[{ordered_parts[0]}]-[{ordered_parts[1]}] {ordered_parts[2]} ({ordered_parts[3]})_{ordered_parts[4]}"
        return old_name

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

        if not self.is_crawled:
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

        # 트리뷰 컨테이너 생성
        container = ttk.Frame(tree_frame)
        container.pack(fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # 스크롤바 생성
        y_scroll = ttk.Scrollbar(container, orient="vertical")
        x_scroll = ttk.Scrollbar(container, orient="horizontal")

        # 트리뷰 생성 및 스크롤바 연결
        self.result_tree = ttk.Treeview(
            container,
            columns=("Item", "Status", "Platform", "Genre", "ID"),
            show="headings",
            style='modern.Treeview',
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )

        # 스크롤바 설정
        y_scroll.config(command=self.result_tree.yview)
        x_scroll.config(command=self.result_tree.xview)

        # 컬럼 설정
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

        # 컬럼 너비 설정
        self.result_tree.column("Item", width=500, minwidth=200)
        self.result_tree.column("Status", width=100, minwidth=80)
        self.result_tree.column("Platform", width=100, minwidth=80)
        self.result_tree.column("Genre", width=100, minwidth=80)
        self.result_tree.column("ID", width=100, minwidth=80)

        # 태그 설정
        self.result_tree.tag_configure("valid", background=self.colors['success'])
        self.result_tree.tag_configure("invalid", background=self.colors['error'])
        self.result_tree.tag_configure("duplicate", background=self.colors['warning'])

        # 그리드 배치
        self.result_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def create_action_buttons(self, parent):
        button_frame = ttk.Frame(parent, style='modern.TFrame')
        button_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(button_frame,
                  text="선택 항목 이름 변경",
                  style='modern.TButton',
                  command=self.open_rename_window).pack(side="left")

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