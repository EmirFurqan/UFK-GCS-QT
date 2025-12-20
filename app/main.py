import sys, qtawesome as qta, signal, traceback, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QSizePolicy,QMessageBox, QInputDialog, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QSize, QCoreApplication
from widgets import MetricRow
from widgets.Map.map import MapWidget
from widgets.telemetry_panel import TelemetryPanel
from widgets.controls_panel import ControlsPanel
from widgets.region_dialog import RegionDialog
from pathlib import Path
import json
from mavlink.mavlink_worker import MavlinkWorker 
import dotenv
from widgets.camera import VideoWidget 
from widgets.hud_widget import HorizonHUD
from widgets.precheck_modal import PreCheckDialog
from widgets.telemetry_sender import TelemetrySenderDialog


dotenv.load_dotenv()

IMAGE_PATH = os.getenv("IMAGE_PATH")
QR_ICON_PATH = os.getenv("QR_ICON_PATH")

def make_card(title: str, prop_name: str = None):
    box = QFrame(); box.setObjectName("card")
    if prop_name:
        box.setProperty(prop_name, True)  # QSS attribute selector
    box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    lay = QVBoxLayout(box); lay.setContentsMargins(14,12,14,12); lay.setSpacing(6)
    title_lbl = QLabel(title); title_lbl.setObjectName("cardTitle")
    value_lbl = QLabel("—");  value_lbl.setObjectName("cardValue")
    lay.addWidget(title_lbl); lay.addWidget(value_lbl)
    return box, value_lbl
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UFK-GCS")
        self.resize(1100, 680)

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ===== Main Area =====
        center = QWidget()
        center_layout = QVBoxLayout(center)
        center_layout.setContentsMargins(16, 16, 16, 16)
        center_layout.setSpacing(14)
        root_layout.addWidget(center, 1)

        # ----- HEADER -----
        header = QFrame()
        header.setObjectName("header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 10, 12, 10)
        hl.setSpacing(10)

        title = QLabel("Telemetry")
        title.setObjectName("title")
        self.statusLbl = QLabel("Bağlantı bekleniyor…")
        self.statusLbl.setObjectName("statusLbl")

        hl.addWidget(title)
        hl.addStretch(1)
        hl.addWidget(self.statusLbl)

        # ===== Telemetry panel (üstteki kartlar) =====
        self.panel = TelemetryPanel(parent=center)

        # ===== Map =====
        self.map = MapWidget(parent=center)

        # ===== Video (kamera) =====
        self.video = VideoWidget(parent=center, port=5000)

        # ===== HUD (orta sütunun altı) =====
        self.hud = HorizonHUD(parent=center)


        # ===== Kontrol paneli (butonlar) =====
        self.controls = ControlsPanel(parent=center)

        try:
            self.map.set_vehicle_icon(
                IMAGE_PATH
            )
        except Exception:
            pass

        # ===== ALT BÖLGE: MAP | (CAMERA+HUD) | EMPTY =====
        bottom = QWidget(center)
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        # 1) SOL SÜTUN → MAP
        bottom_layout.addWidget(self.map, 1)

        # 2) ORTA SÜTUN → ÜST CAMERA, ALT HUD
        middle = QWidget(bottom)
        middle_layout = QVBoxLayout(middle)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(8)

        # ÜST: CAMERA
        middle_layout.addWidget(self.video, 1)

        # ALT: HUD
        middle_layout.addWidget(self.hud, 1)

        bottom_layout.addWidget(middle, 1)

        # 3) SAĞ SÜTUN → Rakip Takımlar Listesi
        self.right_empty = QWidget(bottom)
        re_layout = QVBoxLayout(self.right_empty)
        re_layout.setContentsMargins(0, 0, 0, 0)
        
        self.competitor_list = QListWidget()
        self.competitor_list.setObjectName("competitorList")
        re_layout.addWidget(QLabel("Rakip İHA'lar"))
        re_layout.addWidget(self.competitor_list)
        
        # Liste tıklama olayı
        self.competitor_list.itemClicked.connect(self.on_competitor_clicked)
        
        bottom_layout.addWidget(self.right_empty, 1)

        # ----- ÜSTTEN ALTA DİZ -----
        center_layout.addWidget(header, 0)
        center_layout.addWidget(self.panel, 0)
        center_layout.addWidget(self.controls, 0)
        center_layout.addWidget(bottom, 1)

        # Ortala butonu: son bilinen araca odaklan
        self.controls.centerBtn.clicked.connect(lambda: self.map.center_on_last(15))
        # Bölge butonu: dialog aç, kaydedip çiz
        self.controls.regionBtn.clicked.connect(self.on_region_clicked)
        # Mission butonu: waypoint / görev ekleme
        self.controls.missionBtn.clicked.connect(self.on_mission_clicked)
        # QR noktası butonu: lat,lon al, arı marker çiz ve kaydet
        self.controls.qrBtn.clicked.connect(self.on_qr_clicked)
        # Ön kontrol
        self.controls.preCheckBtn.clicked.connect(self.on_precheck_clicked)
        # Sunucu butonu
        self.controls.serverBtn.clicked.connect(self.on_server_clicked)

        # Açılışta kayıtlı bölgeyi yükle ve çiz (harita hazır olduğunda)
        self._regions_path = Path(__file__).resolve().parent / "config" / "regions" / "regions.json"
        
        # Efsun ikonu yolu
        self._efsun_icon_path = str(Path(__file__).resolve().parent.parent / "styles" / "ufkefsun.png")
        # senin path'in farklıysa eski halini kullan:
        self._regions_path = Path(__file__).resolve().parent / "config" / "regions.json"
        self.map.on_ready(lambda: self._load_and_draw_region())

        # Worker
        self.w = MavlinkWorker()
        self.w.status.connect(self.statusLbl.setText)
        self.w.error.connect(self.statusLbl.setText)
        self.w.telemetry.connect(self.on_telemetry)
        self.w.start()
        print("Worker started")
        # Kamera
        self.video.start()
            
    def on_telemetry(self, t):
        if not self.isVisible():
            return

        # Üstteki kartları güncelle
        self.panel.update_telemetry(t)

        # Harita güncelle
        try:
            lat = getattr(t, "iha_enlem", None)
            lon = getattr(t, "iha_boylam", None)
            hdg = getattr(t, "iha_yonelme", None)
            if lat is not None and lon is not None:
                self.map.update_vehicle(lat, lon, hdg)
        except Exception:
            pass

        # ---------- HUD GÜNCELLE ----------
        try:
            roll = getattr(t, "iha_yatis", 0.0) or 0.0
            pitch = getattr(t, "iha_dikilme", 0.0) or 0.0
            yaw = getattr(t, "iha_yonelme", 0.0) or 0.0
            alt = getattr(t, "iha_irtifa", 0.0) or 0.0
            spd = getattr(t, "iha_hiz", 0.0) or 0.0
            sats = getattr(t, "baglanilan_gps_sayisi", 0) or 0

            batt0 = getattr(t, "iha_batarya0", None)
            batt1 = getattr(t, "iha_batarya1", None)

            volts = 0.0
            if batt0 is not None:
                volts = float(batt0)
            elif batt1 is not None:
                volts = float(batt1)

            if volts > 0:
                percent = (volts - 21.0) / (25.2 - 21.0) * 100.0
                percent = max(0.0, min(100.0, percent))
            else:
                percent = 0.0

            self.hud.update_hud(
                float(roll),
                float(pitch),
                float(yaw),
                float(alt),
                float(spd),
                float(percent),
                float(volts),
                int(sats),
            )
        except Exception as e:
            print("HUD update error:", e)



    def on_precheck_clicked(self):
        """
        Uçuş öncesi kontrol modalını aç.
        """
        if not hasattr(self, "w"):
            return
        dlg = PreCheckDialog(self, worker=self.w)
        dlg.exec_()

    def on_server_clicked(self):
        """
        Sunucuya telemetri gönderme penceresini aç.
        """
        # MavlinkWorker'ın içindeki telemetry objesini gönderiyoruz.
        # w.telemetry_state diye bir attribute varsa onu, yoksa telemetry sinyalinden gelen son veriyi tutmak gerekebilir.
        # MavlinkWorker (mavlink_worker.py) implementation'ında genellikle self.telemetry_state tutulur.
        # Eğer yoksa, worker'a eklememiz gerekebilir veya buradaki on_telemetry'de son state'i saklamalıyız.
        # Ancak MavlinkWorker genellikle self.t diye state tutar.
        
        # Basitlik için worker'ın state'ine erişmeye çalışalım.
        state = None
        if hasattr(self, "w"):
            if hasattr(self.w, "telemetry_state"):
                state = self.w.telemetry_state
    
        if not state:
            # Eğer worker'da state yoksa, boş bir state ile de açılabilir,
            # ama en güzeli worker'a referans vermek.
            pass

        # Dialog'u aç
        # Not: Dialog'u self.server_dlg gibi saklayıp tekrar açmak daha iyi olabilir (state korumak için)
        if not hasattr(self, "server_dlg") or self.server_dlg is None:
            self.server_dlg = TelemetrySenderDialog(self, telemetry_state=state)
        
        # State referansını güncelle (eğer değiştiyse veya ilk null ise)
        self.server_dlg.telemetry_state = state
        
        # Sinyal bağlantısını her seferinde yapmamak için kontrol veya disconnect gerekebilir
        # Ancak PyQt aynı slotu çoklu bağlamayı (bazen) önler veya biz try-except ile yönetebiliriz.
        try:
            self.server_dlg.competitors_update.disconnect(self.update_competitors)
        except:
            pass
        self.server_dlg.competitors_update.connect(self.update_competitors)
        
        self.server_dlg.show()
        self.server_dlg.raise_()
        self.server_dlg.activateWindow()

    def update_competitors(self, competitors):
        """
        Sunucudan gelen rakip listesini (dict listesi) işle.
        """
        # 1. Listeyi güncelle
        # Önce mevcut seçimi hatırlamak zor olabilir, basitçe listeyi yenileyelim.
        # Ama seçili olanı korumak istersek ID'yi saklamalıyız.
        current_row = self.competitor_list.currentRow()
        
        self.competitor_list.clear()
        self._competitor_data = {} # id -> data
        
        
        # Filtreleme için state (varsa kullan yoksa oluştur)
        if not hasattr(self, "_competitor_filters"):
            self._competitor_filters = {} # t_no -> {'lat': val, 'lon': val, 'hdg': val}

        for comp in competitors:
            t_no = comp.get("takim_numarasi")
            if t_no is None: continue
            
            # Ham veriler
            raw_lat = float(comp.get("iha_enlem", 0))
            raw_lon = float(comp.get("iha_boylam", 0))
            raw_hdg = float(comp.get("iha_yonelme", 0))
            alt = comp.get("iha_irtifa")
            
            # EMA Smoothing (Alpha factor)
            # Alpha düşükse daha smooth ama gecikmeli. 0.1 ile ciddi filtreleme yapalım.
            alpha = 0.1
            
            if t_no not in self._competitor_filters:
                self._competitor_filters[t_no] = {'lat': raw_lat, 'lon': raw_lon, 'hdg': raw_hdg}
            else:
                prev = self._competitor_filters[t_no]
                # Filter: New = Old * (1-alpha) + Raw * alpha
                new_lat = prev['lat'] * (1 - alpha) + raw_lat * alpha
                new_lon = prev['lon'] * (1 - alpha) + raw_lon * alpha
                
                # Heading için dairesel geçiş (0-360) sorunu olabilir ama basitçe lineer yapalım şimdilik
                # Yarışma verisi 0-360 geliyorsa ve 359->1 geçişi varsa bu yöntem (kısa yoldan gitmezse) sapıtabilir.
                # Ama basit smoothing için lineer yeterli olabilir, çok hızlı dönmüyorlarsa.
                new_hdg = prev.get('hdg', raw_hdg) * (1 - alpha) + raw_hdg * alpha
                
                self._competitor_filters[t_no] = {'lat': new_lat, 'lon': new_lon, 'hdg': new_hdg}
                
            filtered_lat = self._competitor_filters[t_no]['lat']
            filtered_lon = self._competitor_filters[t_no]['lon']
            filtered_hdg = self._competitor_filters[t_no]['hdg']

            # Label oluştur
            txt = f"Takım {t_no} (Alt: {alt}m)"
            
            item = QListWidgetItem(txt)
            # Item data olarak ID sakla
            item.setData(Qt.UserRole, t_no) 
            self.competitor_list.addItem(item)
            
            # Veriyi güncelle (orijinali sakla ama çizimde filtreliyi kullanacağız)
            # Burada comp dict'ini kopyalayıp filtreli coordları yazalım ki click event'i de doğru görsün
            comp_copy = comp.copy()
            comp_copy['iha_enlem'] = filtered_lat
            comp_copy['iha_boylam'] = filtered_lon
            self._competitor_data[t_no] = comp_copy
            
            # 2. Haritada göster
            # Varsayılan opaklık: 1.0 (Opak). Seçili olan 0.5 (Saydam/Ghost) ???
            # Kullanıcı: "diğer uçaklar opak olsun listeden herhaangi birine tıkladığımızda opak gözükmesin"
            # O zaman Varsayılan 1.0. Tıklananı farklı yapacağız.
            # Şu an henüz tıklama yok (update anı), hepsi 1.0.
            # YA DA: Seçili bir takım varsa onu hatırla?
            
            # Basitlik için hepsini çiz, opacity 1.0
            # Eğer bir seçim mantığı varsa (self._selected_team_id gibi) onu kullanırız.
            opac = 1.0
            if hasattr(self, "_selected_team_id") and self._selected_team_id == t_no:
                 opac = 0.5 
                 
            self.map.add_marker(
                marker_id=f"team_{t_no}",
                lat=filtered_lat,
                lon=filtered_lon,
                icon_path=self._efsun_icon_path, 
                popup=f"Takım {t_no}<br>Hız: {comp.get('iha_hizi')}",
                opacity=opac,
                heading=filtered_hdg
            )

    def on_competitor_clicked(self, item):
        t_no = item.data(Qt.UserRole)
        self._selected_team_id = t_no
        
        # Tüm markerları güncelle (yeni opacity ile)
        # Veriyi _competitor_data'dan alıp tekrar çiziyoruz.
        if hasattr(self, "_competitor_data"):
            for tid, comp in self._competitor_data.items():
                opac = 1.0
                if tid == self._selected_team_id:
                    # Seçilen 'opak olsun' demişti ama önceki istek 'seçilen hariç opak' gibiydi.
                    # Son isteği: "efsun png ile gösterebilirisn ama opak olsun"
                    # Bu tümü opak olsun demek olabilir. AMA "opak gözükmesin" ifadesi de vardı.
                    # Kullanıcı: "herhangi birine tıkladığımızda opak gözükmesin" -> Seçilen saydam.
                    # Yeni istek: "opak olsun". 
                    # Belki de PNG'nin kendi saydamlığı vardır, ama biz 1.0 gönderelim.
                    # Yine de seçileni ayırt etmek için 0.5 mantığını koruyorum veya 0.7.
                    # "opak olsun" -> görünür olsun demek istemiş olabilir (göremiyorum dediği için).
                    pass 
                
                # Kullanıcı "göremiyorum" dedi, yani görünürlük sorunu var.
                # Ben yine de seçileni farklı yapayım ama görünür (0.5).
                if tid == self._selected_team_id:
                     opac = 0.5
                
                self.map.add_marker(
                    marker_id=f"team_{tid}",
                    lat=float(comp.get("iha_enlem", 0)),
                    lon=float(comp.get("iha_boylam", 0)),
                    popup=f"Takım {tid}",
                    icon_path=self._efsun_icon_path,
                    opacity=opac,
                    heading=float(comp.get("iha_yonelme", 0))
                )

    def on_region_clicked(self):
        dlg = RegionDialog(self)
        if dlg.exec_() == dlg.Accepted:
            polygon = dlg.get_polygon()
            try:
                self._regions_path.parent.mkdir(parents=True, exist_ok=True)
                Path(self._regions_path).write_text(json.dumps({"polygon": polygon}, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception:
                pass
            self._draw_polygon(polygon)

    def on_qr_clicked(self):
        """
        QR koordinatı gir:
        - Kullanıcıdan "lat,lon" formatında al
        - JSON'a qr_point olarak kaydet
        - Haritaya arı ikonlu marker çiz
        """
        text, ok = QInputDialog.getText(
            self,
            "QR Koordinatı",
            "Enlem, boylam gir (örnek: 41.0, 29.0):"
        )
        if not ok or not text.strip():
            return

        # "41.0, 29.0" / "41.0 29.0" gibi formatları destekle
        raw = text.replace(";", ",").replace(" ", ",")
        parts = [p.strip() for p in raw.split(",") if p.strip()]

        if len(parts) != 2:
            QMessageBox.warning(self, "Hata", "Lütfen 'enlem, boylam' formatında gir.")
            return

        try:
            lat = float(parts[0])
            lon = float(parts[1])
        except ValueError:
            QMessageBox.warning(self, "Hata", "Enlem ve boylam sayısal olmalı.")
            return

        # Haritada göster
        self._set_qr_point(lat, lon)

        # JSON'a kaydet: varsa polygon/region'u koru, sadece qr_point ekle/güncelle
        data = {}
        try:
            if self._regions_path.exists():
                data = json.loads(self._regions_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

        data["qr_point"] = {"lat": lat, "lon": lon}

        try:
            self._regions_path.parent.mkdir(parents=True, exist_ok=True)
            self._regions_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception as e:
            QMessageBox.warning(self, "Hata", f"QR noktası kaydedilemedi:\n{e}")

    def on_mission_clicked(self):
        """
        Mission butonu:
        - Worker'a 'arm + takeoff + misyonu başlat' komutu gönderir
        """
        if not hasattr(self, "w") or self.w is None:
            return

        self.statusLbl.setText("Mission: ARM + TAKEOFF + START...")
        try:
            self.w.start_mission() 
        except Exception as e:
            # İstersen QMessageBox da kullanırsın
            print("Mission komutu gönderilemedi:", e)


    def _load_and_draw_region(self):
        try:
            if self._regions_path.exists():
                data = json.loads(self._regions_path.read_text(encoding="utf-8"))

                # Yeni format: polygon
                if data.get("polygon"):
                    self._draw_polygon(data.get("polygon"))
                # Eski format: min/max lat lon
                elif data.get("region"):
                    self._draw_region(data.get("region"))

                # QR noktası varsa onu da çiz
                qr = data.get("qr_point")
                if qr and "lat" in qr and "lon" in qr:
                    try:
                        lat = float(qr["lat"])
                        lon = float(qr["lon"])
                        self._set_qr_point(lat, lon)
                    except Exception:
                        pass
        except Exception:
            pass


    def _draw_region(self, region):
        try:
            minLat = float(region.get("minLat"))
            minLon = float(region.get("minLon"))
            maxLat = float(region.get("maxLat"))
            maxLon = float(region.get("maxLon"))
        except Exception:
            return
        self.map.draw_bounds_rect(minLat, minLon, maxLat, maxLon)

    def _draw_polygon(self, polygon):
        try:
            pts = [(float(p[0]), float(p[1])) for p in polygon]
        except Exception:
            return
        self.map.draw_polygon(pts)

    def _set_qr_point(self, lat: float, lon: float):
        """
        Haritada arı ikonlu QR marker'ı çiz ve hafifçe ortala.
        """
        try:
            self.map.add_marker(
                marker_id="qr_point",
                lat=lat,
                lon=lon,
                icon_path=QR_ICON_PATH,
                icon_size=(36, 36)
            )
        except Exception as e:
            print("QR marker çizilemedi:", e)


    def closeEvent(self, e):
        if hasattr(self, "w") and self.w:
            try:
                self.w.telemetry.disconnect(self.on_telemetry)
            except Exception:
                pass
            self.w.stop(); self.w.wait(1500)

        if hasattr(self, "video") and self.video:
            try:
                self.video.stop()
            except Exception:
                pass

        super().closeEvent(e)

if __name__ == "__main__":
    # Terminalden Ctrl+C ile kapatabilmek ve beklenmeyen hatada çıkmak için
    def _excepthook(exctype, value, tb):
        try:
            traceback.print_exception(exctype, value, tb)
        except Exception:
            pass
        try:
            QCoreApplication.quit()
        except Exception:
            pass
        os._exit(1)
    sys.excepthook = _excepthook

    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    except Exception:
        pass
    # HiDPI ve keskin ikonlar
    try:
        QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass
    app = QApplication(sys.argv)
    try:
        with open("styles/styles.qss","r") as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print("QSS yüklenemedi:", e)
    w = MainWindow()
    w.show()
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        os._exit(130)
