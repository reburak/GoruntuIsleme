import cv2
import webbrowser
import os
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time
from collections import deque

class EyeTracker:
    def __init__(self, screen_width, screen_height):
        # Ekran boyutuna göre kalibrasyon noktaları
        padding = 50  # Kenarlardan uzaklık
        self.calibration_points = [
            (padding, padding),                    # Sol üst
            (screen_width - padding, padding),     # Sağ üst
            (screen_width // 2, screen_height // 2),  # Orta
            (padding, screen_height - padding),    # Sol alt
            (screen_width - padding, screen_height - padding)  # Sağ alt
        ]
        self.current_point = 0
        self.samples_per_point = 30
        self.current_samples = []
        self.calibration_data = [[] for _ in range(len(self.calibration_points))]
        self.is_calibrated = False
        self.point_start_time = None
        self.point_duration = 3
        
    def calculate_eye_ratio(self, eye_points):
        try:
            # Göz köşe noktaları
            left = eye_points[0]
            right = eye_points[8]
            top = eye_points[4]
            bottom = eye_points[12]
            
            # Göz merkezi
            center_x = (left[0] + right[0]) / 2
            center_y = (top[1] + bottom[1]) / 2
            
            # Mesafeler
            eye_width = max(abs(right[0] - left[0]), 1)  # Sıfıra bölünmeyi önle
            eye_height = max(abs(bottom[1] - top[1]), 1)
            
            # Oranları hesapla
            x_ratio = (center_x - left[0]) / eye_width
            y_ratio = (center_y - top[1]) / eye_height
            
            return x_ratio, y_ratio
        except (IndexError, ZeroDivisionError):
            return None, None
    
    def calibrate(self, frame, face_landmarks):
        if not self.is_calibrated:
            current_point = self.calibration_points[self.current_point]
            
            # Noktayı göster
            cv2.circle(frame, current_point, 10, (0, 255, 0), -1)
            
            # Başlangıç zamanını ayarla
            if self.point_start_time is None:
                self.point_start_time = time.time()
                return frame, False
            
            # Süre kontrolü
            elapsed_time = time.time() - self.point_start_time
            remaining_time = max(0, self.point_duration - elapsed_time)
            
            # Kalan süreyi göster
            cv2.putText(frame, f"Noktaya {int(remaining_time)} saniye bakın", 
                       (50, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            if elapsed_time < self.point_duration:
                try:
                    # Göz verilerini topla
                    left_eye = face_landmarks[33:46]
                    right_eye = face_landmarks[263:276]
                    
                    left_ratio = self.calculate_eye_ratio(left_eye)
                    right_ratio = self.calculate_eye_ratio(right_eye)
                    
                    if left_ratio[0] is not None and right_ratio[0] is not None:
                        self.current_samples.append({
                            'left': left_ratio,
                            'right': right_ratio
                        })
                except (IndexError, TypeError):
                    pass
                
                return frame, False
            else:
                # Yeterli örnek toplandı mı kontrol et
                if len(self.current_samples) > self.samples_per_point // 2:
                    self.calibration_data[self.current_point] = self.current_samples
                    self.current_point += 1
                    self.current_samples = []
                
                # Tüm noktalar tamamlandı mı?
                if self.current_point >= len(self.calibration_points):
                    self.process_calibration()
                    return frame, True
                
                self.point_start_time = None
                return frame, False
        
        return frame, True
    
    def process_calibration(self):
        try:
            x_ratios_left = []
            y_ratios_left = []
            x_ratios_right = []
            y_ratios_right = []
            
            # Her kalibrasyon noktası için ortalama değerleri hesapla
            for point_samples in self.calibration_data:
                if point_samples:  # Boş olmayan örnekler için
                    point_x_left = []
                    point_y_left = []
                    point_x_right = []
                    point_y_right = []
                    
                    for sample in point_samples:
                        left = sample['left']
                        right = sample['right']
                        if left[0] is not None and right[0] is not None:
                            point_x_left.append(left[0])
                            point_y_left.append(left[1])
                            point_x_right.append(right[0])
                            point_y_right.append(right[1])
                    
                    if point_x_left:  # Boş değilse ortalamaları al
                        x_ratios_left.append(np.mean(point_x_left))
                        y_ratios_left.append(np.mean(point_y_left))
                        x_ratios_right.append(np.mean(point_x_right))
                        y_ratios_right.append(np.mean(point_y_right))
            
            # Min-max değerlerini hesapla
            if x_ratios_left:
                self.x_min_left = min(x_ratios_left)
                self.x_max_left = max(x_ratios_left)
                self.y_min_left = min(y_ratios_left)
                self.y_max_left = max(y_ratios_left)
                
                self.x_min_right = min(x_ratios_right)
                self.x_max_right = max(x_ratios_right)
                self.y_min_right = min(y_ratios_right)
                self.y_max_right = max(y_ratios_right)
                
                self.is_calibrated = True
        except (ValueError, AttributeError) as e:
            print(f"Kalibrasyon işleme hatası: {e}")
            self.is_calibrated = False
    
    def get_gaze_point(self, frame, face_landmarks):
        try:
            if not self.is_calibrated or face_landmarks is None:
               return None
               
            left_eye = face_landmarks[33:46]
            right_eye = face_landmarks[263:276]
           
            left_ratio = self.calculate_eye_ratio(left_eye)
            right_ratio = self.calculate_eye_ratio(right_eye)
           
            if None in (left_ratio[0], left_ratio[1], right_ratio[0], right_ratio[1]):
                return None

            denominator_x_left = self.x_max_left - self.x_min_left
            denominator_y_left = self.y_max_left - self.y_min_left
            denominator_x_right = self.x_max_right - self.x_min_right
            denominator_y_right = self.y_max_right - self.y_min_right
    
            if min(denominator_x_left, denominator_y_left, denominator_x_right, denominator_y_right) < 1e-6:
                return None

            x_left = (left_ratio[0] - self.x_min_left) / denominator_x_left
            y_left = (left_ratio[1] - self.y_min_left) / denominator_y_left
            x_right = (right_ratio[0] - self.x_min_right) / denominator_x_right
            y_right = (right_ratio[1] - self.y_min_right) / denominator_y_right

            x = (x_left + x_right) / 2
            y = (y_left + y_right) / 2
           
            x = max(0, min(1, x))
            y = max(0, min(1, y))
           
            return (int(x * frame.shape[1]), int(y * frame.shape[0]))
        except Exception as e:
            print(f"Göz takibi hatası: {e}")
            return None

class YouTubePlayer(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        
        # Pencere özellikleri
        self.attributes('-alpha', 0.7)  # 70% saydamlık
        self.overrideredirect(True)  # Pencere dekorasyonlarını kaldır
        self.attributes('-topmost', True)  # Her zaman üstte
        
        # Video frame
        self.video_frame = tk.Frame(self)
        self.video_frame.pack(expand=True, fill='both')
        
        # Kontrol çerçevesi
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(fill='x', pady=5)
        
        self.url_entry = tk.Entry(self.control_frame)
        self.url_entry.pack(side='left', fill='x', expand=True, padx=5)
        
        self.load_button = tk.Button(self.control_frame, text="Yükle",
                                   command=self.load_video)
        self.load_button.pack(side='right', padx=5)
        
        # Sürükleme değişkenleri
        self.drag_data = {'x': 0, 'y': 0, 'dragging': False}
        
    def start_drag(self, x, y):
        self.drag_data['x'] = x
        self.drag_data['y'] = y
        self.drag_data['dragging'] = True
    
    def on_drag(self, x, y):
       if self.drag_data['dragging']:
           dx = (x - self.drag_data['x']) * 2.5  # Hassasiyet artışı
           dy = (y - self.drag_data['y']) * 2.5
           new_x = self.winfo_x() + dx
           new_y = self.winfo_y() + dy
           self.geometry(f"+{int(new_x)}+{int(new_y)}")
           self.drag_data['x'] = x
           self.drag_data['y'] = y
    
    def stop_drag(self):
        self.drag_data['dragging'] = False
    
    def load_video(self):
        video_id = self.url_entry.get()
        if video_id:
            html = f"""
            <html>
                <body style="margin:0;background:transparent;">
                    <iframe 
                        width="100%" 
                        height="100%" 
                        src="https://www.youtube.com/embed/{video_id}?autoplay=1" 
                        frameborder="0" 
                        allowfullscreen>
                    </iframe>
                </body>
            </html>
            """
            with open('temp.html', 'w', encoding='utf-8') as f:
                f.write(html)
            self.after(100, lambda: webbrowser.open('file://' + os.path.abspath('temp.html')))

class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Göz Takip Sistemi")
        
        # Tam ekran ve boyutları al
        self.root.attributes('-fullscreen', True)
        self.root.update()  # Pencere boyutlarının güncellenmesini bekle
        self.screen_width = self.root.winfo_width()
        self.screen_height = self.root.winfo_height()
        
        # MediaPipe başlatma
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        
        # Göz takip sistemi - ekran boyutlarını ilet
        self.eye_tracker = EyeTracker(self.screen_width, self.screen_height)
        
        # Kamera ayarları
        self.cap = cv2.VideoCapture(0)
        # Kamerayı mümkün olan en yüksek çözünürlüğe ayarla
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Video gösterimi için canvas - tam ekran boyutunda
        self.canvas = tk.Canvas(self.root, 
                              width=self.screen_width, 
                              height=self.screen_height,
                              highlightthickness=0)
        self.canvas.pack(expand=True, fill='both')
        
        # YouTube penceresi
        self.youtube_window = YouTubePlayer(self.root)
        initial_yt_width = min(800, self.screen_width - 100)
        initial_yt_height = min(600, self.screen_height - 100)
        self.youtube_window.geometry(f"{initial_yt_width}x{initial_yt_height}+50+50")
        
        # FPS sayacı
        self.fps_queue = deque(maxlen=30)
        self.last_frame_time = time.time()
        self.fps_label = tk.Label(self.root, text="FPS: 0",
                                bg='black', fg='green')
        self.fps_label.place(x=10, y=10)
        
        # Durum değişkenleri
        self.running = True
        self.show_gaze = True
        
        # Tuş dinleyicileri
        self.root.bind('<Escape>', lambda e: self.stop())
        self.root.bind('c', lambda e: self.toggle_calibration())
        self.root.bind('g', lambda e: self.toggle_gaze())
        
        # Ana döngü
        self.update_thread = threading.Thread(target=self.update_frame)
        self.update_thread.daemon = True
        self.update_thread.start()

    def detect_hand_gestures(self, frame):
        results = self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # İşaret ve orta parmak pozisyonları
                index_tip = hand_landmarks.landmark[8]
                middle_tip = hand_landmarks.landmark[12]
                index_pip = hand_landmarks.landmark[6]
                middle_pip = hand_landmarks.landmark[10]
                
                h, w, _ = frame.shape
                pos = (int((index_tip.x + middle_tip.x) * w / 2),
                      int((index_tip.y + middle_tip.y) * h / 2))
                
                # İki parmak kalkık mı kontrol et
                if (index_tip.y < index_pip.y and 
                    middle_tip.y < middle_pip.y):
                    
                    # Görselleştirme
                    cv2.circle(frame, pos, 10, (0, 255, 0), -1)
                    cv2.line(frame, 
                            (int(index_tip.x * w), int(index_tip.y * h)),
                            (int(middle_tip.x * w), int(middle_tip.y * h)),
                            (0, 255, 0), 2)
                    
                    return True, pos
                
                # El landmarkları görselleştirme
                mp.solutions.drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                    mp.solutions.drawing_styles.get_default_hand_connections_style())
        
        return False, None

    def update_frame(self):
        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    continue
                
                # Frame'i ekran boyutuna ölçekle
                frame = cv2.flip(frame, 1)  # Ayna görüntüsü
                frame = cv2.resize(frame, (self.screen_width, self.screen_height))
                
                # FPS hesaplama
                current_time = time.time()
                fps = 1 / (current_time - self.last_frame_time)
                self.last_frame_time = current_time
                self.fps_queue.append(fps)
                avg_fps = sum(self.fps_queue) / len(self.fps_queue)
                self.fps_label.config(text=f"FPS: {int(avg_fps)}")
                
                # Yüz landmark tespiti
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_results = self.face_mesh.process(rgb_frame)
                
                if face_results.multi_face_landmarks:
                    face_landmarks = [(int(l.x * frame.shape[1]), int(l.y * frame.shape[0])) 
                                    for l in face_results.multi_face_landmarks[0].landmark]
                    
                    # Kalibrasyon veya göz takibi
                    if not self.eye_tracker.is_calibrated:
                        frame, is_complete = self.eye_tracker.calibrate(frame, face_landmarks)
                    elif self.show_gaze:
                        gaze_point = self.eye_tracker.get_gaze_point(frame, face_landmarks)
                        if gaze_point:
                            cv2.circle(frame, gaze_point, 10, (0, 0, 255), -1)
                            cv2.putText(frame, f"Gaze: {gaze_point}", 
                                      (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                                      0.7, (0, 255, 0), 2)
                
                # El hareketleri
                drag_detected, hand_pos = self.detect_hand_gestures(frame)
                if drag_detected and hand_pos:
                    if not self.youtube_window.drag_data['dragging']:
                        self.youtube_window.start_drag(hand_pos[0], hand_pos[1])
                    else:
                        self.youtube_window.on_drag(hand_pos[0], hand_pos[1])
                else:
                    self.youtube_window.stop_drag()
                
                # Frame gösterimi - tam ekran boyutunda
                image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                photo = ImageTk.PhotoImage(image=image)
                self.canvas.create_image(0, 0, image=photo, anchor='nw')
                self.canvas.image = photo
                
            except Exception as e:
                print(f"Hata oluştu: {e}")
                continue
                
                
    def toggle_calibration(self):
        """Kalibrasyon modunu başlat/durdur"""
        if self.eye_tracker.is_calibrated:
            self.eye_tracker = EyeTracker()
        else:
            print("Kalibrasyon zaten devam ediyor...")
    
    def toggle_gaze(self):
        """Göz takibini aç/kapat"""
        self.show_gaze = not self.show_gaze
    
    def run(self):
        self.root.mainloop()
    
    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
        self.root.destroy()

if __name__ == "__main__":
    app = MainApp()
    try:
        app.run()
    except Exception as e:
        print(f"Ana uygulama hatası: {e}")
    finally:
        app.stop()