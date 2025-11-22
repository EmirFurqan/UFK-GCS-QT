from PyQt5.QtWidgets import QWidget, QFrame, QGridLayout, QSizePolicy
from PyQt5.QtCore import Qt
from .metric_row import MetricRow


class TelemetryPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setMaximumSize(1100, 200)

        self._layout = QGridLayout(self)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setHorizontalSpacing(3)
        self._layout.setVerticalSpacing(10)
        # Grid'i sabitle: 5 sütun için sabit min genişlik ve stretch kapalı
        for c in range(5):
            self._layout.setColumnMinimumWidth(c, 150)
            self._layout.setColumnStretch(c, 0)
        for r in range(2):
            self._layout.setRowMinimumHeight(r, 44)
            # fazla yükseklik olursa satırlara eşit dağıt ve içerikleri ortala
            self._layout.setRowStretch(r, 1)

        self._icon_map = {
            "iha_enlem":             "fa5s.map-marker-alt",
            "iha_boylam":            "fa5s.map-marker-alt",
            "baglanilan_gps_sayisi": "fa5s.satellite-dish",
            "iha_irtifa":            "fa5s.arrow-up",
            "iha_yatis":             "fa5s.sync-alt",
            "iha_dikilme":           "fa5s.exchange-alt",
            "iha_yonelme":           "fa5s.compass",
            "iha_hiz":               "fa5s.tachometer-alt",
            "iha_batarya0":          "fa5s.bolt",
            "iha_batarya1":          "fa5s.bolt",
        }

        self.metrics = {}

        keys = [
            ("iha_enlem", "Enlem", ""),
            ("iha_boylam", "Boylam", ""),
            ("baglanilan_gps_sayisi", "GPS Sats", ""),
            ("iha_irtifa", "İrtifa", "m"),
            ("iha_hiz", "Hız", "m/s"),
            ("iha_yatis", "Yatış", "°"),
            ("iha_dikilme", "Dikilme", "°"),
            ("iha_yonelme", "Yönelme", "°"),
            ("iha_batarya0", "Batarya 0", "V"),
            ("iha_batarya1", "Batarya 1", "V"),
        ]

        for idx, (k, t, u) in enumerate(keys):
            self._add_metric(idx, k, t, u)

    def _add_metric(self, idx: int, key: str, title: str, unit: str = ""):
        row = MetricRow(self._icon_map.get(key, "fa5s.circle"), title, unit, parent=self)
        # Hücre sabit boyut ve Fixed policy
        row.setFixedHeight(44)
        row.setFixedWidth(150)
        row.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        r = idx // 5
        c = idx % 5
        self._layout.addWidget(row, r, c, alignment=Qt.AlignVCenter)
        self.metrics[key] = row

    def update_telemetry(self, t):
        if not self.isVisible():
            return

        def S(x, fmt=None):
            if x is None:
                return "—"
            return fmt(x) if fmt else str(x)

        self.metrics["iha_enlem"].set_value(   S(t.iha_enlem,  lambda x: f"{x:.7f}"))
        self.metrics["iha_boylam"].set_value(  S(t.iha_boylam, lambda x: f"{x:.7f}"))
        self.metrics["baglanilan_gps_sayisi"].set_value(S(t.baglanilan_gps_sayisi))
        self.metrics["iha_irtifa"].set_value(  S(t.iha_irtifa, lambda x: f"{x:.1f}"))
        self.metrics["iha_yatis"].set_value(   S(t.iha_yatis,  lambda x: f"{x:.1f}"))
        self.metrics["iha_dikilme"].set_value( S(t.iha_dikilme,lambda x: f"{x:.1f}"))
        self.metrics["iha_yonelme"].set_value( S(t.iha_yonelme,lambda x: f"{x:.1f}"))
        self.metrics["iha_hiz"].set_value(     S(t.iha_hiz,    lambda x: f"{x:.1f}"))
        self.metrics["iha_batarya0"].set_value(S(t.iha_batarya0,lambda x: f"{x:.2f}"))
        self.metrics["iha_batarya1"].set_value(S(t.iha_batarya1,lambda x: f"{x:.2f}"))


