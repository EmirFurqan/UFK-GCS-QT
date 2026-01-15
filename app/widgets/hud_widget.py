from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QRectF


class HorizonHUD(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.altitude = 0.0
        self.speed = 0.0
        self.battery = 0.0
        self.battery_voltage = 0.0
        self.gps_sats = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ---------- SOL: HORIZON ----------
        self.horizon = HorizonCanvas()
        layout.addWidget(self.horizon, 4)

        # ---------- SAĞ: TELEMETRİ ----------
        right = QVBoxLayout()
        right.setContentsMargins(10, 10, 10, 10)
        right.setSpacing(6)

        def make_label(title, color):
            # Başlık
            title_lbl = QLabel(title)
            title_lbl.setObjectName("hudTitle")
            
            # Değer label'ı (ÖNCE oluşturuyoruz)
            value_lbl = QLabel("0.0")
            value_lbl.setObjectName("hudValue")

            box = QVBoxLayout()
            box.setSpacing(0)
            box.addWidget(title_lbl)
            box.addWidget(value_lbl)
            return box, value_lbl

        self.alt_box, self.alt_lbl = make_label("Altitude", "#75B7E5")
        self.speed_box, self.speed_lbl = make_label("Ground Speed", "#00C07A")
        self.batt_box, self.batt_lbl = make_label("Battery", "#FFCC33")
        self.gps_box, self.gps_lbl = make_label("GPS", "#B066FF")
        self.head_box, self.head_lbl = make_label("Heading", "#FF6666")

        for box, _ in [
            (self.alt_box, self.alt_lbl),
            (self.speed_box, self.speed_lbl),
            (self.batt_box, self.batt_lbl),
            (self.gps_box, self.gps_lbl),
            (self.head_box, self.head_lbl),
        ]:
            w = QWidget()
            w.setLayout(box)
            right.addWidget(w)

        right.addStretch(1)
        layout.addLayout(right, 2)

        self.setMinimumHeight(160)

    def update_hud(self, roll, pitch, yaw, alt, spd, batt, batt_v, sats):
        self.roll = roll or 0.0
        self.pitch = pitch or 0.0
        self.yaw = yaw or 0.0
        self.altitude = alt or 0.0
        self.speed = spd or 0.0
        self.battery = batt or 0.0
        self.battery_voltage = batt_v or 0.0
        self.gps_sats = sats or 0

        self.alt_lbl.setText(f"{self.altitude:.1f} m")
        self.speed_lbl.setText(f"{self.speed:.1f} m/s")
        self.batt_lbl.setText(f"{self.battery:.1f}% ({self.battery_voltage:.1f}V)")
        self.gps_lbl.setText(f"{self.gps_sats} sats")
        self.head_lbl.setText(f"{self.yaw:.1f}°")

        self.horizon.set_attitude(self.roll, self.pitch)


class HorizonCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.roll = 0.0
        self.pitch = 0.0
        self.setMinimumHeight(120)

    def set_attitude(self, roll, pitch):
        self.roll = roll or 0.0
        self.pitch = pitch or 0.0
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)

        w = float(self.width())
        h = float(self.height())

        sky_color = QColor("#75B7E5")    # mavi
        ground_color = QColor("#5A0E27") # kırmızı

        # çizimi merkeze al
        p.translate(w / 2.0, h / 2.0)
        # roll kadar döndür (sola yatma pozitifse - ile terslersin)
        p.rotate(-self.roll)

        # pitch'e göre ufuk çizgisinin y konumu
        # ölçeği istersen artır / azalt
        horizon_y = self.pitch * 2.0

        # büyük dikdörtgenler (widget'tan biraz büyük çiziyoruz ki boşluk kalmasın)
        half_h = h
        half_w = w

        sky_rect = QRectF(-half_w, -half_h, 2 * half_w, half_h + horizon_y)
        ground_rect = QRectF(-half_w, horizon_y, 2 * half_w, half_h - horizon_y)

        p.fillRect(sky_rect, sky_color)
        p.fillRect(ground_rect, ground_color)

        # ufuk çizgisi
        p.setPen(QPen(Qt.white, 2))
        p.drawLine(int(-half_w), int(horizon_y), int(half_w), int(horizon_y))

        # Text drawing removed as requested
        p.resetTransform()