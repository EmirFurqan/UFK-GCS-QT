import qtawesome as qta
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt

class MetricRow(QWidget):
    """
    İkon + Başlık + (Değer [+ Birim]) görünümü.
    QSS seçicileri:
      - #metric, #metricIcon, #metricTitle, #metricValue, #metricUnit
    """
    def __init__(self, icon_name: str, title: str, unit: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("metric")

        wrap = QHBoxLayout(self)
        wrap.setContentsMargins(8, 6, 8, 6)
        wrap.setSpacing(8)

        # ikon
        self.icon = QLabel()
        self.icon.setObjectName("metricIcon")
        self.icon.setFixedSize(28, 28)
        self.icon.setAlignment(Qt.AlignCenter)
        self.set_icon(icon_name)
        wrap.addWidget(self.icon)

        # metin alanı (başlık + değer satırı)
        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        text_box.setContentsMargins(0, 0, 0, 0)

        self.title = QLabel(title)
        self.title.setObjectName("metricTitle")

        val_row = QHBoxLayout()
        val_row.setSpacing(6)
        val_row.setContentsMargins(0, 0, 0, 0)

        self.value = QLabel("—")
        self.value.setObjectName("metricValue")

        self.unit = QLabel(unit)
        self.unit.setObjectName("metricUnit")

        val_row.addWidget(self.value)
        if unit:
            val_row.addWidget(self.unit)
        val_row.addStretch(1)

        text_box.addWidget(self.title)
        text_box.addLayout(val_row)

        wrap.addLayout(text_box, 1)

    def set_icon(self, icon_name: str):
        # qtawesome ikonu pixmap olarak yerleştir
        ico = qta.icon(icon_name, color="white")
        # 24px vektör, HiDPI ile keskin görünsün
        pm = ico.pixmap(24, 24)
        self.icon.setPixmap(pm)

    def set_value(self, text: str):
        self.value.setText(text)
