import cv2
import mediapipe as mp
import pyautogui
import numpy as np
from screeninfo import get_monitors
import math
import time
import tkinter as tk
from threading import Thread
from collections import deque

class CalibrationScreen:
    def __init__(self, screen_width, screen_height, cap, controller):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.cap = cap
        self.controller = controller
        
        self.calibration_points = [
            (50, 50),  # Sol üst
            (screen_width - 50, 50),  # Sağ üst
            (screen_width//2, screen_height//2),  # Orta
            (50, screen_height - 50),  # Sol alt
            (screen_width - 50, screen_height - 50)  # Sağ alt
        ]
        self.current_point = 0
        self.calibration_data = []
        self.is_complete = False
        self.tracking = False
        
        self.canvas = tk.Canvas(self.root, width=screen_width, height=screen_height, 
                              bg='black', highlightthickness=0)
        self.canvas.pack()
        
        self.text = self.canvas.create_text(screen_width//2, screen_height//2 - 50,
                                          text="Kalibrasyon başlıyor...",
                                          fill="white", font=("Arial", 24))
        self.point = None
        self.timer_text = None
        # Cursor boyutunu 2 katına çıkar
        self.cursor = self.canvas.create_oval(0, 0, 60, 60, fill="blue", outline="white", width=2)
        self.canvas.itemconfigure(self.cursor, state='hidden')
        
        self.root.after(1000, self.start_calibration)
        
    def start_calibration(self):
        self.tracking = True
        self.update_tracking()
        self.show_next_point()
    
    def update_tracking(self):
        if not self.tracking:
            return
            
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            results = self.controller.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            if results.multi_hand_landmarks:
                landmarks = results.multi_hand_landmarks[0].landmark
                index_tip = landmarks[8]
                
                # El pozisyonunu al ve aynı dönüşümleri kullan
                raw_x = (1 - index_tip.x)
                raw_y = index_tip.y
                
                # Mouse için koordinat dönüşümü
                mapped_x = raw_x * (raw_x * raw_x) * self.screen_width * self.controller.movement_scale
                mapped_y = raw_y * (raw_y * raw_y) * self.screen_height * self.controller.movement_scale
                
                mouse_x, mouse_y = self.controller.mouse_controller.update_target(mapped_x, mapped_y)
                mouse_x = max(0, min(self.screen_width - 1, mouse_x))
                mouse_y = max(0, min(self.screen_height - 1, mouse_y))
                
                # Mouse'u hareket ettir
                try:
                    pyautogui.moveTo(mouse_x, mouse_y, _pause=False)
                except:
                    pass
                
                # Görsel cursor'ı mouse pozisyonuna göre güncelle
                self.canvas.itemconfigure(self.cursor, state='normal')
                self.canvas.coords(self.cursor, mouse_x-15, mouse_y-15, mouse_x+15, mouse_y+15)
                
                if self.point and self.countdown_time > 0:
                    # Hedef noktayla mouse pozisyonu arasındaki mesafeyi kontrol et
                    target_x, target_y = self.calibration_points[self.current_point]
                    distance = math.sqrt((mouse_x - target_x)**2 + (mouse_y - target_y)**2)
                    
                    # Eğer mouse hedeften uzaksa sayacı sıfırla
                    if distance > 100:  # 100 piksel eşik değeri
                        self.countdown_time = 3
                        self.canvas.itemconfig(self.timer_text, text="3")
            else:
                self.canvas.itemconfigure(self.cursor, state='hidden')
        
        self.root.after(10, self.update_tracking)
        
    def show_next_point(self):
        if self.current_point >= len(self.calibration_points):
            self.finish_calibration()
            return
            
        if self.point:
            self.canvas.delete(self.point)
        if self.timer_text:
            self.canvas.delete(self.timer_text)
            
        x, y = self.calibration_points[self.current_point]
        self.point = self.canvas.create_oval(x-15, y-15, x+15, y+15, fill="red")
        self.canvas.itemconfig(self.text, text=f"Hedefi 3 saniye boyunca işaret edin")
        
        self.countdown_time = 3
        self.update_timer()
        
    def update_timer(self):
        if not self.point:
            return
            
        if self.timer_text:
            self.canvas.delete(self.timer_text)
            
        x, y = self.calibration_points[self.current_point]
        self.timer_text = self.canvas.create_text(x, y+40,
                                                text=str(self.countdown_time),
                                                fill="white", font=("Arial", 20))
                                                
        if self.countdown_time > 0:
            self.countdown_time -= 1
            self.root.after(1000, self.update_timer)
        else:
            # Kalibrasyon noktasının koordinatlarını kaydet
            self.calibration_data.append((x, y))
            self.current_point += 1
            self.root.after(100, self.show_next_point)
            
    def finish_calibration(self):
        self.canvas.itemconfig(self.text, text="Kalibrasyon tamamlandı!")
        self.is_complete = True
        self.tracking = False
        
        # Kalibrasyon tamamlandığında pencereyi kapat
        self.root.after(1000, self.cleanup_and_close)
    
    def cleanup_and_close(self):
        self.tracking = False
        if self.root:
            self.root.quit()
            self.root.destroy()
        
    def run(self):
        self.root.mainloop()

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
        self.movement_scale = 2.0  # Azaltıldı daha hassas kontrol için
        
        self.click_cooldown = 0.03
        self.last_click_time = 0
        self.is_clicking = False
        self.is_dragging = False
        
        # Scroll ayarları
        self.scroll_accumulator = 0
        self.scroll_threshold = 0.05
        self.scroll_speed = 120
        self.prev_scroll_y = None
        self.scroll_cooldown = 0.1
        self.last_scroll_time = 0
    
    def update_calibration(self, calibration_data):
        self.calibration_points = calibration_data
        self.is_calibrated = True
        
        # Kalibrasyon matrisini hesapla
        if len(calibration_data) >= 5:
            self.calculate_calibration_matrix()
    
    def calculate_calibration_matrix(self):
        # Basit bir ölçekleme matrisi hesapla
        screen_points = np.array(self.calibration_points)
        min_x = np.min(screen_points[:, 0])
        max_x = np.max(screen_points[:, 0])
        min_y = np.min(screen_points[:, 1])
        max_y = np.max(screen_points[:, 1])
        
        self.calibration_matrix = {
            'x_scale': (max_x - min_x) / self.screen_width,
            'y_scale': (max_y - min_y) / self.screen_height,
            'x_offset': min_x,
            'y_offset': min_y
        }
    
    def apply_calibration(self, x, y):
        if not self.is_calibrated or not self.calibration_matrix:
            return x, y
            
        # Kalibrasyon matrisini uygula
        cal_x = (x * self.calibration_matrix['x_scale']) + self.calibration_matrix['x_offset']
        cal_y = (y * self.calibration_matrix['y_scale']) + self.calibration_matrix['y_offset']
        
        return cal_x, cal_y
        
    def process_hand(self, frame):
        results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if not results.multi_hand_landmarks:
            return
            
        landmarks = results.multi_hand_landmarks[0].landmark
        
        raw_x = (1 - landmarks[8].x)
        raw_y = landmarks[8].y
        
        # Temel haritalama
        mapped_x = raw_x * self.screen_width * self.movement_scale
        mapped_y = raw_y * self.screen_height * self.movement_scale
        
        # Mouse pozisyonunu güncelle
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
        
        # Click işlemleri
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
        
        # Scroll işlemi
        if self.prev_scroll_y is None:
            self.prev_scroll_y = index_tip.y
        else:
            current_time = time.time()
            if current_time - self.last_scroll_time > self.scroll_cooldown:
                scroll_diff = index_tip.y - self.prev_scroll_y
                self.scroll_accumulator += scroll_diff
                
                if abs(self.scroll_accumulator) > self.scroll_threshold:
                    scroll_amount = int(self.scroll_accumulator * self.scroll_speed)
                    try:
                        pyautogui.scroll(-scroll_amount, _pause=False)
                        self.last_scroll_time = current_time
                        self.scroll_accumulator = 0
                    except:
                        pass
                        
            self.prev_scroll_y = index_tip.y
        
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
        
        # Click işlemleri
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
        
        # Geliştirilmiş scroll işlemi
        if self.prev_scroll_y is None:
            self.prev_scroll_y = index_tip.y
        else:
            current_time = time.time()
            if current_time - self.last_scroll_time > self.scroll_cooldown:
                scroll_diff = index_tip.y - self.prev_scroll_y
                self.scroll_accumulator += scroll_diff
                
                if abs(self.scroll_accumulator) > self.scroll_threshold:
                    scroll_amount = int(self.scroll_accumulator * self.scroll_speed)
                    try:
                        pyautogui.scroll(-scroll_amount, _pause=False)
                        self.last_scroll_time = current_time
                        self.scroll_accumulator = 0
                    except:
                        pass
                        
            self.prev_scroll_y = index_tip.y

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("El Kontrollü Fare")
        self.root.geometry("200x150")
        self.root.attributes('-topmost', True)
        
        monitor = get_monitors()[0]
        self.screen_width = monitor.width
        self.screen_height = monitor.height
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FPS, 60)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        self.controller = HandMouseController(self.screen_width, self.screen_height)
        
        self.running = False
        self.mirror = tk.BooleanVar(value=True)
        
        self.setup_ui()
    
    def setup_ui(self):
        self.start_button = tk.Button(self.root, text="Başlat", command=self.start_calibration)
        self.start_button.pack(pady=20)
        
        self.mirror_check = tk.Checkbutton(self.root, text="Görüntüyü Aynala",
                                         variable=self.mirror)
        self.mirror_check.pack(pady=10)
    
    def start_calibration(self):
        # Kalibrasyon ekranını başlat
        calibration = CalibrationScreen(self.screen_width, self.screen_height, 
                                      self.cap, self.controller)
        self.root.withdraw()  # Ana pencereyi gizle
        calibration.run()
        self.root.deiconify()  # Ana pencereyi göster
        
        # Kalibrasyon tamamlandıktan sonra tracking'i başlat
        if calibration.is_complete:
            self.toggle_tracking()
    
    def toggle_tracking(self):
        if self.running:
            self.running = False
            self.start_button.config(text="Başlat")
        else:
            self.running = True
            self.start_button.config(text="Durdur")
            Thread(target=self.update, daemon=True).start()
    
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