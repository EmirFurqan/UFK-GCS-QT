import requests
import json
import time
import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QGroupBox, QGridLayout, QScrollArea, QWidget, QSpinBox
)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, Qt

# Arka planda request atacak thread
class SenderThread(QThread):
    response_signal = pyqtSignal(bool, str, str, object) # success, status_text, detail, json_data

    def __init__(self, url, data):
        super().__init__()
        self.url = url
        self.data_dict = data

    def run(self):
        try:
            # Timestamp güncelle (anlık gönderim zamanı)
            # Ama isterse dışarıdan gelen 'gps_saati' da kullanılabilir.
            # Biz burada yarışma isterine göre şu anki saati 
            # ya da eldeki gps verisini json'a koyup gönderiyoruz.
            # Kod içinde data_dict zaten hazırlanmış geliyor.
            
            headers = {'Content-Type': 'application/json'}
            resp = requests.post(self.url, json=self.data_dict, timeout=3)
            
            if resp.status_code == 200:
                try:
                    json_data = resp.json()
                except:
                    json_data = {}
                self.response_signal.emit(True, "Yüklendi (200)", resp.text, json_data)
            else:
                self.response_signal.emit(False, f"Hata: {resp.status_code}", resp.text, {})
                
        except Exception as e:
            self.response_signal.emit(False, "Bağlantı Hatası", str(e), {})

class TelemetrySenderDialog(QDialog):
    competitors_update = pyqtSignal(list)
    
    def __init__(self, parent=None, telemetry_state=None, default_url=None):
        super().__init__(parent)
        self.setWindowTitle("Sunucuya Telemetri Gönder")
        self.resize(400, 500)
        self.telemetry_state = telemetry_state
        
        # Varsayılan URL
        self.default_url = default_url if default_url else "http://10.1.36.78:8000/api/telemetri_gonder"
        
        self.is_running = False
        
        # UI Kurulumu
        self.init_ui()
        
        # Otomatik gönderim için Timer
        self.timer = QTimer(self)
        self.timer.setInterval(1000) # 1 saniyede bir (1Hz)
        self.timer.timeout.connect(self.send_telemetry)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 1. URL Ayarı
        url_group = QGroupBox("Sunucu Adresi")
        ul = QVBoxLayout(url_group)
        self.url_input = QLineEdit(self.default_url)
        ul.addWidget(self.url_input)
        main_layout.addWidget(url_group)
        
        # 2. Manual Hedef Verileri (Telemetri akışında olmayanlar)
        target_group = QGroupBox("Hedef / Kilitlenme Verileri (Simüle)")
        g = QGridLayout(target_group)
        
        self.spin_kilit = QSpinBox(); self.spin_kilit.setRange(0, 1); self.spin_kilit.setValue(1)
        self.spin_otonom = QSpinBox(); self.spin_otonom.setRange(0, 1); self.spin_otonom.setValue(1)
        
        self.spin_hx = QSpinBox(); self.spin_hx.setRange(0, 2000); self.spin_hx.setValue(300)
        self.spin_hy = QSpinBox(); self.spin_hy.setRange(0, 2000); self.spin_hy.setValue(230)
        self.spin_hw = QSpinBox(); self.spin_hw.setRange(0, 500); self.spin_hw.setValue(30)
        self.spin_hh = QSpinBox(); self.spin_hh.setRange(0, 500); self.spin_hh.setValue(43)
        self.spin_takim = QSpinBox(); self.spin_takim.setRange(0, 999); self.spin_takim.setValue(1)
        
        g.addWidget(QLabel("Takım No:"), 0, 0); g.addWidget(self.spin_takim, 0, 1)
        g.addWidget(QLabel("Kilitlenme:"), 1, 0); g.addWidget(self.spin_kilit, 1, 1)
        g.addWidget(QLabel("Otonom:"), 2, 0); g.addWidget(self.spin_otonom, 2, 1)
        g.addWidget(QLabel("Hedef X:"), 3, 0); g.addWidget(self.spin_hx, 3, 1)
        g.addWidget(QLabel("Hedef Y:"), 4, 0); g.addWidget(self.spin_hy, 4, 1)
        g.addWidget(QLabel("Hedef G:"), 5, 0); g.addWidget(self.spin_hw, 5, 1)
        g.addWidget(QLabel("Hedef Yük:"), 6, 0); g.addWidget(self.spin_hh, 6, 1)
        
        main_layout.addWidget(target_group)
        
        # 3. Kontroller ve Durum
        ctrl_layout = QHBoxLayout()
        self.btn_send_once = QPushButton("Tek Gönder")
        self.btn_send_once.clicked.connect(self.send_telemetry)
        
        self.btn_toggle = QPushButton("Otomatik Başlat (1Hz)")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.clicked.connect(self.toggle_auto)
        
        ctrl_layout.addWidget(self.btn_send_once)
        ctrl_layout.addWidget(self.btn_toggle)
        main_layout.addLayout(ctrl_layout)
        
        self.status_lbl = QLabel("Hazır")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("font-weight: bold; color: gray;")
        main_layout.addWidget(self.status_lbl)

    def toggle_auto(self, checked):
        if checked:
            self.btn_toggle.setText("Durdur")
            self.timer.start()
            self.is_running = True
        else:
            self.btn_toggle.setText("Otomatik Başlat (1Hz)")
            self.timer.stop()
            self.is_running = False

    def get_current_data(self):
        t = self.telemetry_state
        if not t:
            return {}
            
        # UI'dan manuel değerler
        iha_otonom = self.spin_otonom.value()
        iha_kilitlenme = self.spin_kilit.value()
        hedef_merkez_X = self.spin_hx.value()
        hedef_merkez_Y = self.spin_hy.value()
        hedef_genislik = self.spin_hw.value()
        hedef_yukseklik = self.spin_hh.value()
        takim_numarasi = self.spin_takim.value()

        # Telemetri nesnesinden okunanlar (eğer None ise 0 varsayalım)
        # float dönüşümleri ve güvenli erişim
        iha_enlem = float(t.iha_enlem) if t.iha_enlem is not None else 0.0
        iha_boylam = float(t.iha_boylam) if t.iha_boylam is not None else 0.0
        iha_irtifa = float(t.iha_irtifa) if t.iha_irtifa is not None else 0.0
        iha_dikilme = float(t.iha_dikilme) if t.iha_dikilme is not None else 0.0
        iha_yonelme = float(t.iha_yonelme) if t.iha_yonelme is not None else 0.0
        iha_yatis = float(t.iha_yatis) if t.iha_yatis is not None else 0.0
        iha_hiz = float(t.iha_hiz) if t.iha_hiz is not None else 0.0
        
        # Batarya logic: batarya0 veya batarya1, yüzdeye çevir veya voltaj gönder?
        # Yarışma isterine göre "iha_batarya" yüzdelik (0-100) olabilir.
        # Basitçe voltajı alıp %'ye kabaca çevirelim veya direkt voltaj gidelim.
        # İsterde "iha_batarya": 50 diyor, demek ki yüzde.
        volts = 0.0
        if t.iha_batarya0: volts = float(t.iha_batarya0)
        elif t.iha_batarya1: volts = float(t.iha_batarya1)
        
        # 6S Lipo varsayımı (min 21V, max 25.2V)
        if volts > 0:
            pct = (volts - 21.0) / (25.2 - 21.0) * 100.0
            pct = max(0, min(100, pct))
        else:
            pct = 0
            
        # Zaman objesi
        now = datetime.datetime.now()
        gps_time = {
            "saat": now.hour,
            "dakika": now.minute,
            "saniye": now.second,
            "milisaniye": int(now.microsecond / 1000)
        }
        
        payload = {
            "takim_numarasi": takim_numarasi,
            "iha_enlem": iha_enlem,
            "iha_boylam": iha_boylam,
            "iha_irtifa": iha_irtifa,
            "iha_dikilme": iha_dikilme,
            "iha_yonelme": iha_yonelme,
            "iha_yatis": iha_yatis,
            "iha_hiz": iha_hiz,
            "iha_batarya": int(pct),
            "iha_otonom": iha_otonom,
            "iha_kilitlenme": iha_kilitlenme,
            "hedef_merkez_X": hedef_merkez_X,
            "hedef_merkez_Y": hedef_merkez_Y,
            "hedef_genislik": hedef_genislik,
            "hedef_yukseklik": hedef_yukseklik,
            "gps_saati": gps_time
        }
        return payload

    def send_telemetry(self):
        url = self.url_input.text().strip()
        data = self.get_current_data()
        
        self.status_lbl.setText("Gönderiliyor...")
        self.status_lbl.setStyleSheet("color: blue;")
        
        # Thread ile gönder
        self.sender_thread = SenderThread(url, data)
        self.sender_thread.response_signal.connect(self.on_response)
        self.sender_thread.start()
        
    def on_response(self, success, text, detail, json_data):
        if success:
            self.status_lbl.setText(f"{text} ({datetime.datetime.now().strftime('%H:%M:%S')})")
            self.status_lbl.setStyleSheet("color: green; font-weight: bold;")
            
            # Konum bilgilerini ayıkla ve sinyal gönder
            if isinstance(json_data, dict):
                competitors = json_data.get("konumBilgileri", [])
                if competitors:
                    self.competitors_update.emit(competitors)
        else:
            self.status_lbl.setText(text)
            self.status_lbl.setStyleSheet("color: red; font-weight: bold;")
            print("Sunucu Hatası Detay:", detail)
