import json
from pathlib import Path
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QDoubleSpinBox, QPushButton, QWidget, QLabel, QGridLayout
)


class RegionDialog(QDialog):
    def __init__(self, parent=None, config_path: Path = None):
        super().__init__(parent)
        self.setWindowTitle("Bölge Sınırları")
        self.setObjectName("regionDialog")

        self._config_path = config_path or (Path(__file__).resolve().parents[1] / "config" / "regions.json")
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(10)

        title = QLabel("Dört Köşe Bölge Tanımı")
        title.setObjectName("dialogTitle")
        subtitle = QLabel("Köşeleri saat yönünde veya saat yönünün tersinde giriniz.")
        subtitle.setObjectName("dialogSubtitle")
        lay.addWidget(title)
        lay.addWidget(subtitle)

        # 4 köşe (lat/lon x4) yatay satırlar
        self.lat1 = QDoubleSpinBox(); self.lat1.setRange(-90.0, 90.0); self.lat1.setDecimals(7); self.lat1.setSuffix("°")
        self.lon1 = QDoubleSpinBox(); self.lon1.setRange(-180.0, 180.0); self.lon1.setDecimals(7); self.lon1.setSuffix("°")
        self.lat2 = QDoubleSpinBox(); self.lat2.setRange(-90.0, 90.0); self.lat2.setDecimals(7); self.lat2.setSuffix("°")
        self.lon2 = QDoubleSpinBox(); self.lon2.setRange(-180.0, 180.0); self.lon2.setDecimals(7); self.lon2.setSuffix("°")
        self.lat3 = QDoubleSpinBox(); self.lat3.setRange(-90.0, 90.0); self.lat3.setDecimals(7); self.lat3.setSuffix("°")
        self.lon3 = QDoubleSpinBox(); self.lon3.setRange(-180.0, 180.0); self.lon3.setDecimals(7); self.lon3.setSuffix("°")
        self.lat4 = QDoubleSpinBox(); self.lat4.setRange(-90.0, 90.0); self.lat4.setDecimals(7); self.lat4.setSuffix("°")
        self.lon4 = QDoubleSpinBox(); self.lon4.setRange(-180.0, 180.0); self.lon4.setDecimals(7); self.lon4.setSuffix("°")

        def row(label_text, lat_box, lon_box):
            roww = QWidget()
            roww.setObjectName("cornerRow")
            hl = QHBoxLayout(roww); hl.setContentsMargins(0, 0, 0, 0); hl.setSpacing(8)
            lab = QLabel(label_text); lab.setObjectName("cornerLabel")
            comma = QLabel(",")
            hl.addWidget(lab)
            hl.addStretch(1)
            hl.addWidget(lat_box)
            hl.addWidget(comma)
            hl.addWidget(lon_box)
            return roww

        lay.addWidget(row("1. Köşe", self.lat1, self.lon1))
        lay.addWidget(row("2. Köşe", self.lat2, self.lon2))
        lay.addWidget(row("3. Köşe", self.lat3, self.lon3))
        lay.addWidget(row("4. Köşe", self.lat4, self.lon4))

        btnRow = QHBoxLayout()
        self.saveBtn = QPushButton("Kaydet")
        self.cancelBtn = QPushButton("İptal")
        btnRow.addStretch(1)
        btnRow.addWidget(self.cancelBtn)
        btnRow.addWidget(self.saveBtn)
        lay.addLayout(btnRow)

        self.cancelBtn.clicked.connect(self.reject)
        self.saveBtn.clicked.connect(self._on_save)

        self._load()

    def _load(self):
        try:
            if self._config_path.exists():
                data = json.loads(self._config_path.read_text(encoding="utf-8"))
                # Önce polygon formatını dene
                poly = data.get("polygon")
                if isinstance(poly, list) and len(poly) == 4:
                    (lat1, lon1), (lat2, lon2), (lat3, lon3), (lat4, lon4) = poly
                    self.lat1.setValue(float(lat1)); self.lon1.setValue(float(lon1))
                    self.lat2.setValue(float(lat2)); self.lon2.setValue(float(lon2))
                    self.lat3.setValue(float(lat3)); self.lon3.setValue(float(lon3))
                    self.lat4.setValue(float(lat4)); self.lon4.setValue(float(lon4))
                    return
                # Geriye dönük uyum: min/max varsa dikdörtgen köşelere dağıt
                region = data.get("region") or {}
                minLat = float(region.get("minLat", 0.0))
                minLon = float(region.get("minLon", 0.0))
                maxLat = float(region.get("maxLat", 0.0))
                maxLon = float(region.get("maxLon", 0.0))
                self.lat1.setValue(minLat); self.lon1.setValue(minLon)
                self.lat2.setValue(minLat); self.lon2.setValue(maxLon)
                self.lat3.setValue(maxLat); self.lon3.setValue(maxLon)
                self.lat4.setValue(maxLat); self.lon4.setValue(minLon)
                return
        except Exception:
            pass
        # Kayıt bulunamazsa verilen örnek koordinatlarla başlat
        try:
            self.lat1.setValue(41.0300); self.lon1.setValue(28.9500)
            self.lat2.setValue(41.0300); self.lon2.setValue(28.9700)
            self.lat3.setValue(41.0100); self.lon3.setValue(28.9700)
            self.lat4.setValue(41.0100); self.lon4.setValue(28.9500)
        except Exception:
            pass

    def _on_save(self):
        payload = {
            "polygon": [
                [self.lat1.value(), self.lon1.value()],
                [self.lat2.value(), self.lon2.value()],
                [self.lat3.value(), self.lon3.value()],
                [self.lat4.value(), self.lon4.value()],
            ]
        }
        try:
            self._config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass
        self.accept()

    def get_polygon(self):
        return [
            [self.lat1.value(), self.lon1.value()],
            [self.lat2.value(), self.lon2.value()],
            [self.lat3.value(), self.lon3.value()],
            [self.lat4.value(), self.lon4.value()],
        ]


