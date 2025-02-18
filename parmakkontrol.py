import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from threading import Thread
import time
import cv2
import mediapipe as mp
import pyautogui
from screeninfo import get_monitors
import math
from collections import deque

class TutorialOverlay:
    def __init__(self, root, screen_width, screen_height):
        self.window = tk.Toplevel(root)
        self.window.title("El Kontrollü Fare Eğitimi")
        
        # Pencere boyutunu ve konumunu ayarla
        window_width = 1000
        window_height = 600
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Modern görünüm için tema renkleri
        self.colors = {
            'bg': '#f0f0f0',
            'primary': '#2196F3',
            'text': '#333333',
            'button': '#1976D2',
            'button_text': 'white'
        }
        
        self.window.configure(bg=self.colors['bg'])
        
        self.steps = [
            {
                'title': 'El Kontrollü Fare - Eğitim',
                'text': 'Bu eğitim size el hareketleriyle fare kontrolünü öğretecek.\nDevam etmek için İleri butonuna tıklayın.',
                'image': 'images/welcome.png'
            },
            {
                'title': 'İşaretparmağı - Fare Hareketi',
                'text': 'Elinizi açık tutun ve hareket ettirin.\nParmağınızın hareketi fareyi kontrol edecek.',
                'image': 'images/left_click.png'
            },
            {
                'title': 'Baş Parmak + İşaret Parmağı - Sol Tık',
                'text': 'Baş parmak ve işaret parmağınızı birleştirin.\nBu hareket sol tıklamayı tetikler.',
                'image': 'images/pointer_move.png'
            },
            {
                'title': 'Baş Parmak + Orta Parmak - Sağ Tık',
                'text': 'Baş parmak ve orta parmağınızı birleştirin.\nBu hareket sağ tıklamayı tetikler.',
                'image': 'images/right_click.png'
            },
            {
                'title': 'İşaret Parmağı Yukarı/Aşağı - Kaydırma',
                'text': 'İşaret parmağınızı yukarı/aşağı hareket ettirin.\nBu hareket sayfayı kaydırır.',
                'image': 'images/scroll.png'
            }
        ]
        
        self.current_step = 0
        self.setup_ui()
        self.load_images()
        self.update_content()
        
    def setup_ui(self):
        # Ana container
        self.main_frame = tk.Frame(self.window, bg=self.colors['bg'])
        self.main_frame.pack(expand=True, fill='both', padx=40, pady=10)
        
        # Başlık
        self.title_label = tk.Label(self.main_frame, 
                                  font=('Helvetica', 24, 'bold'),
                                  bg=self.colors['bg'],
                                  fg=self.colors['text'])
        self.title_label.pack(pady=(0, 10))
        
        # Görsel container
        self.image_frame = tk.Frame(self.main_frame, 
                                  bg=self.colors['bg'],
                                  height=300)
        self.image_frame.pack(fill='x', pady=10)
        self.image_frame.pack_propagate(False)
        
        self.image_label = tk.Label(self.image_frame, bg=self.colors['bg'])
        self.image_label.pack(expand=True)
        
        # Açıklama metni
        self.text_label = tk.Label(self.main_frame,
                                 font=('Helvetica', 14),
                                 bg=self.colors['bg'],
                                 fg=self.colors['text'],
                                 wraplength=600)
        self.text_label.pack(pady=10)
        
        # İlerleme göstergesi
        self.progress_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.progress_frame.pack(fill='x', pady=10)
        
        self.progress_dots = []
        for i in range(len(self.steps)):
            dot = tk.Label(self.progress_frame, 
                         text='○', 
                         font=('Helvetica', 16),
                         bg=self.colors['bg'],
                         fg=self.colors['primary'])
            dot.pack(side='left', padx=5)
            self.progress_dots.append(dot)
        
        # Buton container
        self.button_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.button_frame.pack(pady=10)
        
        # Özel buton stili
        button_style = {
            'font': ('Helvetica', 12),
            'bg': self.colors['button'],
            'fg': self.colors['button_text'],
            'activebackground': self.colors['primary'],
            'activeforeground': self.colors['button_text'],
            'relief': 'flat',
            'padx': 20,
            'pady': 10
        }
        
        self.prev_button = tk.Button(self.button_frame,
                                   text='← Geri',
                                   command=self.prev_step,
                                   **button_style)
        
        self.next_button = tk.Button(self.button_frame,
                                   text='İleri →',
                                   command=self.next_step,
                                   **button_style)
        
        self.finish_button = tk.Button(self.button_frame,
                                     text='Başla',
                                     command=self.finish_tutorial,
                                     **button_style)
    
    def load_images(self):
        self.images = {}
        for step in self.steps:
            if step['image']:
                try:
                    # Görsel dosyasını yükle ve boyutlandır
                    image = Image.open(step['image'])
                    image = image.resize((300, 300), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(image)
                    self.images[step['image']] = photo
                except Exception as e:
                    print(f"Görsel yükleme hatası ({step['image']}): {e}")
                    # Hata durumunda varsayılan görsel
                    self.create_default_image(step['image'])
    
    def create_default_image(self, image_key):
        # Varsayılan görsel oluştur
        default_image = Image.new('RGB', (300, 300), color='#f5f5f5')
        draw = ImageDraw.Draw(default_image)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        draw.text((150, 150), "Görsel\nBulunamadı", 
                 font=font,
                 fill='#666666', 
                 anchor="mm")
        self.images[image_key] = ImageTk.PhotoImage(default_image)
    
    def update_content(self):
        step = self.steps[self.current_step]
        
        # İçeriği güncelle
        self.title_label.config(text=step['title'])
        self.text_label.config(text=step['text'])
        
        # Görseli güncelle
        if step['image'] and step['image'] in self.images:
            self.image_label.config(image=self.images[step['image']])
        else:
            self.image_label.config(image='')
        
        # İlerleme noktalarını güncelle
        for i, dot in enumerate(self.progress_dots):
            dot.config(text='●' if i == self.current_step else '○')
        
        # Butonları güncelle
        if self.current_step == 0:
            self.prev_button.pack_forget()
        else:
            self.prev_button.pack(side='left', padx=10)
            
        if self.current_step == len(self.steps) - 1:
            self.next_button.pack_forget()
            self.finish_button.pack(side='left', padx=10)
        else:
            self.finish_button.pack_forget()
            self.next_button.pack(side='left', padx=10)
    
    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.update_content()
    
    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_content()
    
    def finish_tutorial(self):
        self.window.destroy()

class SmoothMouseController:
    def __init__(self):
        self.pos_history = deque(maxlen=3)
        self.last_update = time.time()
        self.velocity = [0, 0]
        self.damping = 0.6
        self.spring = 0.4
        
    def update_target(self, target_x, target_y):
        current_time = time.time()
        dt = current_time - self.last_update
        self.last_update = current_time
        
        if not self.pos_history:
            self.pos_history.append((pyautogui.position()))
            return target_x, target_y
        
        current_pos = self.pos_history[-1]
        
        dist_x = target_x - current_pos[0]
        dist_y = target_y - current_pos[1]
        dist = math.sqrt(dist_x**2 + dist_y**2)
        
        acceleration = min(dist / 500, 2.0)
        
        force_x = dist_x * self.spring * acceleration
        force_y = dist_y * self.spring * acceleration
        
        self.velocity[0] = self.velocity[0] * self.damping + force_x
        self.velocity[1] = self.velocity[1] * self.damping + force_y
        
        new_x = int(current_pos[0] + self.velocity[0])
        new_y = int(current_pos[1] + self.velocity[1])
        
        self.pos_history.append((new_x, new_y))
        return new_x, new_y

class HandMouseController:
    def __init__(self, screen_width, screen_height):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=0
        )
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        pyautogui.FAILSAFE = False
        pyautogui.MINIMUM_DURATION = 0
        pyautogui.MINIMUM_SLEEP = 0
        pyautogui.PAUSE = 0
        
        self.mouse_controller = SmoothMouseController()
        self.movement_scale = 3.5
        
        self.click_cooldown = 0.03
        self.last_click_time = 0
        self.is_clicking = False
        self.is_dragging = False
        self.scroll_threshold = 0.008
        self.scroll_speed = 300
        self.prev_scroll_y = None
        
    def process_hand(self, frame):
        results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if not results.multi_hand_landmarks:
            return
            
        landmarks = results.multi_hand_landmarks[0].landmark
        
        raw_x = (1 - landmarks[8].x)
        raw_y = landmarks[8].y
        
        mapped_x = raw_x * (raw_x * raw_x) * self.screen_width * self.movement_scale
        mapped_y = raw_y * (raw_y * raw_y) * self.screen_height * self.movement_scale
        
        x, y = self.mouse_controller.update_target(mapped_x, mapped_y)
        x = max(0, min(self.screen_width - 1, x))
        y = max(0, min(self.screen_height - 1, y))
        
        try:
            pyautogui.moveTo(x, y, _pause=False)
        except:
            pass
        
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        
        thumb_index_dist = math.hypot(thumb_tip.x - index_tip.x, thumb_tip.y - index_tip.y)
        thumb_middle_dist = math.hypot(thumb_tip.x - middle_tip.x, thumb_tip.y - middle_tip.y)
        
        current_time = time.time()
        
        if thumb_index_dist < 0.03:
            if not self.is_clicking and current_time - self.last_click_time > self.click_cooldown:
                pyautogui.mouseDown(button='left', _pause=False)
                self.is_clicking = True
                self.last_click_time = current_time
        elif self.is_clicking:
            pyautogui.mouseUp(button='left', _pause=False)
            self.is_clicking = False
        
        if thumb_middle_dist < 0.03:
            if not self.is_dragging and current_time - self.last_click_time > self.click_cooldown:
                pyautogui.mouseDown(button='right', _pause=False)
                self.is_dragging = True
                self.last_click_time = current_time
        elif self.is_dragging:
            pyautogui.mouseUp(button='right', _pause=False)
            self.is_dragging = False
        
        if self.prev_scroll_y is None:
            self.prev_scroll_y = index_tip.y
        else:
            scroll_diff = index_tip.y - self.prev_scroll_y
            if abs(scroll_diff) > self.scroll_threshold:
                scroll_amount = int(scroll_diff * self.scroll_speed)
                try:
                    pyautogui.scroll(-scroll_amount, _pause=False)
                except:
                    pass
            self.prev_scroll_y = index_tip.y

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("El Kontrollü Fare")
        
        # Eğitim durumunu kontrol et
        self.tutorial_file = "tutorial_completed.txt"
        self.tutorial_shown = self.check_tutorial_status()
        
        # Ana pencere boyutu ve konumu
        window_width = 400
        window_height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Tema renkleri
        self.colors = {
            'bg': '#f0f0f0',
            'primary': '#2196F3',
            'secondary': '#FFC107',
            'text': '#333333',
            'success': '#4CAF50',
            'error': '#f44336'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Kamera ve kontrol değişkenleri
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.controller = HandMouseController(self.screen_width, self.screen_height)
        self.running = False
        self.mirror = tk.BooleanVar(value=True)
        
        self.setup_ui()
    
    def check_tutorial_status(self):
        try:
            with open(self.tutorial_file, 'r') as f:
                return f.read().strip() == 'completed'
        except FileNotFoundError:
            return False

    def mark_tutorial_completed(self):
        try:
            with open(self.tutorial_file, 'w') as f:
                f.write('completed')
            self.tutorial_shown = True
        except Exception as e:
            print(f"Eğitim durumu kaydedilemedi: {e}")
    
    def setup_ui(self):
        # Logo/başlık alanı
        self.header_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.header_frame.pack(fill='x', pady=10)
        
        self.title_label = tk.Label(self.header_frame,
                                  text="El Kontrollü Fare",
                                  font=('Helvetica', 24, 'bold'),
                                  bg=self.colors['bg'],
                                  fg=self.colors['text'])
        self.title_label.pack()
        
        # Durum göstergesi
        self.status_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.status_frame.pack(fill='x', pady=10)
        
        self.status_label = tk.Label(self.status_frame,
                                   text="Hazır",
                                   font=('Helvetica', 12),
                                   bg=self.colors['bg'],
                                   fg=self.colors['text'])
        self.status_label.pack()
        
        # Kamera önizleme (opsiyonel)
        self.preview_frame = tk.Frame(self.root, 
                                    bg='black',
                                    width=300,
                                    height=220)
        self.preview_frame.pack(pady=10)
        self.preview_frame.pack_propagate(False)
        
        # Kontrol butonları
        self.control_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.control_frame.pack(fill='x', pady=10, padx=20)
        
        button_style = {
            'font': ('Helvetica', 12, 'bold'),
            'relief': 'flat',
            'padx': 20,
            'pady': 10
        }
        
        self.start_button = tk.Button(self.control_frame,
                                    text="Başlat",
                                    bg=self.colors['success'],
                                    fg='white',
                                    command=self.start_app,
                                    **button_style)
        self.start_button.pack(fill='x', pady=5)
        
        self.tutorial_button = tk.Button(self.control_frame,
                                       text="Eğitimi Göster",
                                       bg=self.colors['primary'],
                                       fg='white',
                                       command=self.show_tutorial,
                                       **button_style)
        self.tutorial_button.pack(fill='x', pady=5)
        
        # Ayarlar
        self.settings_frame = tk.LabelFrame(self.root,
                                          text="Ayarlar",
                                          bg=self.colors['bg'],
                                          fg=self.colors['text'],
                                          font=('Helvetica', 12))
        self.settings_frame.pack(fill='x', padx=40, pady=10)
        
        self.mirror_check = tk.Checkbutton(self.settings_frame,
                                         text="Görüntüyü Aynala",
                                         variable=self.mirror,
                                         bg=self.colors['bg'],
                                         fg=self.colors['text'],
                                         selectcolor=self.colors['primary'],
                                         font=('Helvetica', 10))
        self.mirror_check.pack(pady=10)
        
        # Durum çubuğu
        self.statusbar = tk.Label(self.root,
                                text="Hazır",
                                bd=1,
                                relief=tk.SUNKEN,
                                anchor=tk.W,
                                bg=self.colors['bg'],
                                fg=self.colors['text'])
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def show_tutorial(self):
        tutorial = TutorialOverlay(self.root, 
                                 self.root.winfo_screenwidth(),
                                 self.root.winfo_screenheight())
        self.root.wait_window(tutorial.window)
        self.mark_tutorial_completed()
    
    def start_app(self):
        if not self.running:
            if not self.tutorial_shown:
                tutorial = TutorialOverlay(self.root, self.screen_width, self.screen_height)
                self.root.wait_window(tutorial.window)
                self.mark_tutorial_completed()
            
            self.running = True
            self.start_button.config(text="Durdur", bg=self.colors['error'])
            self.status_label.config(text="Çalışıyor")
            Thread(target=self.update, daemon=True).start()
        else:
            self.running = False
            self.start_button.config(text="Başlat", bg=self.colors['success'])
            self.status_label.config(text="Hazır")
    
    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                if self.mirror.get():
                    frame = cv2.flip(frame, 1)
                self.controller.process_hand(frame)
            time.sleep(0.001)
    
    def run(self):
        self.root.mainloop()
    
    def stop(self):
        self.running = False
        self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    app = App()
    try:
        app.run()
    finally:
        app.stop()