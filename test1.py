import cv2
import torch
import threading
import numpy as np
import pytesseract
from ultralytics import YOLO

# 📌 OpenCV Optimizasyonu Aç
cv2.setUseOptimized(True)
cv2.setNumThreads(12)  # Ryzen 5 4600H için 12 mantıksal işlem birimini kullan

# 📌 YOLOv8 Modelini CPU'da Optimize Et
model = YOLO("yolov8n.pt").to("cpu")  # En küçük model (Nano) kullan
model.fuse()  # Model optimizasyonu

# 📌 OCR için Tesseract Kurulumu (Eğer henüz kurulmadıysa yükle)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 📌 Kamera Aç ve Çözünürlüğü Küçük Tut (Hız İçin)
cap = cv2.VideoCapture(0)
cap.set(3, 320)  # Genişlik (FPS'yi artırmak için düşük tut)
cap.set(4, 240)  # Yükseklik

# 📌 Frame İşleme Fonksiyonu (Çoklu İş Parçacığı İçin)
def process_frame():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 🔹 Görüntü Boyutunu Küçült (Daha Hızlı İşleme İçin)
        frame = cv2.resize(frame, (320, 240))

        # 🔹 YOLO ile Nesne Algılama (FP16 KAPALI, CPU İÇİN GEREKSİZ)
        results = model(frame)  

        # 🔹 Algılanan Nesneleri Çiz
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Nesne Koordinatları
                label = result.names[int(box.cls)]  # Nesne Adı
                conf = box.conf.item()  # Güven Skoru

                # 🔹 Nesne Çizimi
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # 🔹 OCR için Sadece Metin Olabilecek Nesnelerde İşleme Yap
                if "text" in label.lower():  # Metin içeren nesneler için OCR
                    roi = frame[y1:y2, x1:x2]  
                    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)  # Siyah-Beyaz Dönüştürme
                    
                    # OCR ile Metin Okuma
                    text = pytesseract.image_to_string(gray, lang="eng+tur").strip()
                    if text:
                        cv2.putText(frame, text, (x1, y2 + 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # 🔹 Görüntüyü Göster
        cv2.imshow("Nesne ve Metin Algılama (CPU Optimize)", frame)

        # Çıkış için 'q' tuşuna bas
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

# 📌 Thread Başlat (Daha Hızlı İşleme İçin)
thread = threading.Thread(target=process_frame)
thread.start()

# 📌 Thread'in Bitmesini Bekle
thread.join()

# 📌 Kaynakları Serbest Bırak
cap.release()
cv2.destroyAllWindows()
