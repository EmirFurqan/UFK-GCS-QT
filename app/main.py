import sys, qtawesome as qta, signal, traceback, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFrame, QSizePolicy,QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QSize, QCoreApplication
from widgets import MetricRow
from widgets.Map.map import MapWidget
from widgets.telemetry_panel import TelemetryPanel
from widgets.controls_panel import ControlsPanel
from widgets.region_dialog import RegionDialog
from pathlib import Path
import json
from mavlink.mavsdk_worker import MavsdkWorker 
import dotenv

dotenv.load_dotenv()

IMAGE_PATH = os.getenv("IMAGE_PATH", "styles/ufkefsun.png")

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

        root = QWidget(); self.setCentralWidget(root)
        root_layout = QHBoxLayout(root); root_layout.setContentsMargins(0,0,0,0); root_layout.setSpacing(0)
       
        # ===== Main Area =====
        center = QWidget()
        center_layout = QVBoxLayout(center); center_layout.setContentsMargins(16,16,16,16); center_layout.setSpacing(14)
        root_layout.addWidget(center, 1)

        # Sadece telemetri başlığı ve durum etiketi
        header = QFrame(); header.setObjectName("header")
        hl = QHBoxLayout(header); hl.setContentsMargins(12,10,12,10); hl.setSpacing(10)
        title = QLabel("Telemetry"); title.setObjectName("title")
        self.statusLbl = QLabel("Bağlantı bekleniyor…"); self.statusLbl.setObjectName("statusLbl")
        hl.addWidget(title); hl.addStretch(1); hl.addWidget(self.statusLbl)

        # ===== Telemetry panel =====
        self.panel = TelemetryPanel(parent=center)

        # ===== Map =====
        self.map = MapWidget(parent=center)

        # ===== Kontrol paneli (butonlar) =====
        self.controls = ControlsPanel(parent=center)
        # Araç ikonu (ufkefsun.png) ayarla
        try:
            self.map.set_vehicle_icon(
                r"C:\Users\yuste\Desktop\UFK-GCS-QT\styles\ufkefsun.png"
            )
        except Exception:
            pass

        # Assemble
        center_layout.addWidget(header)
        center_layout.addWidget(self.panel, 0)
        center_layout.addWidget(self.controls, 0)
        center_layout.addWidget(self.map, 1)

        # Ortala butonu: son bilinen araca odaklan
        self.controls.centerBtn.clicked.connect(lambda: self.map.center_on_last(15))

        # Bölge butonu: dialog aç, kaydedip çiz
        self.controls.regionBtn.clicked.connect(self.on_region_clicked)
        # Mission butonu: waypoint / görev ekleme
        self.controls.missionBtn.clicked.connect(self.on_mission_clicked)

        # Açılışta kayıtlı bölgeyi yükle ve çiz (harita hazır olduğunda)
        self._regions_path = Path(__file__).resolve().parent / "config" / "regions.json"
        self.map.on_ready(lambda: self._load_and_draw_region())

        # Worker
        self.w = MavsdkWorker()
        self.w.status.connect(self.statusLbl.setText)
        self.w.error.connect(self.statusLbl.setText)
        self.w.telemetry.connect(self.on_telemetry)
        self.w.start()

    def on_telemetry(self, t):
        if not self.isVisible():
            return
        # panel üzerinden güncelle
        self.panel.update_telemetry(t)
        # harita üzerinden güncelle
        try:
            lat = getattr(t, "iha_enlem", None)
            lon = getattr(t, "iha_boylam", None)
            hdg = getattr(t, "iha_yonelme", None)
            if lat is not None and lon is not None:
                self.map.update_vehicle(lat, lon, hdg)
        except Exception:
            pass

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
                if data.get("polygon"):
                    self._draw_polygon(data.get("polygon"))
                elif data.get("region"):
                    # eski format desteği
                    self._draw_region(data.get("region"))
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

    def closeEvent(self, e):
        if hasattr(self, "w") and self.w:
            try:
                self.w.telemetry.disconnect(self.on_telemetry)
            except Exception:
                pass
            self.w.stop(); self.w.wait(1500)
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
