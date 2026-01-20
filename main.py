import sys
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QScrollArea
)
from PyQt5.QtWidgets import QGraphicsDropShadowEffect

COLOR_VARS = {
    "--background": "#000000",
    "--foreground": "#f2f3f7",
    "--card": "#0b0f18",
    "--border": "#111829",
    "--muted": "#121724",
    "--muted-foreground": "#9aa7bf",
    "--primary": "#6b7280",
    "--primary-foreground": "#f6f8ff",
    "--secondary": "#4b5563",
    "--secondary-foreground": "#f6f8ff",
    "--accent": "#7e8696",
    "--destructive": "#ff7048",
    "--destructive-foreground": "#0d0d14",
    "--input": "#0f1320",
    "--ring": "#6b7280",
}


def build_qss(c):
    return f"""
    * {{
        font-family: 'Segoe UI';
        color: {c["--foreground"]};
        background: transparent;
    }}
    QMainWindow, QWidget#central {{
        background: {c["--background"]};
    }}
    /* Panels */
    QFrame.panel {{
        background: {c["--card"]};
        border: 1px solid {c["--border"]};
        border-radius: 10px;
    }}
    /* Header */
    QWidget#topbar {{
        background: {c["--card"]};
        border-bottom: 1px solid {c["--border"]};
        padding: 16px 24px;
    }}
    QLabel#title {{
        font-size: 24px;
        font-weight: 700;
    }}
    QLabel#subtitle {{
        color: {c["--muted-foreground"]};
        font-size: 12px;
    }}
    /* Buttons */
    QPushButton.primary {{
        background: {c["--primary"]};
        border: 1px solid {c["--primary"]};
        color: {c["--primary-foreground"]};
        border-radius: 10px;
        padding: 12px 16px;
        font-weight: 700;
    }}
    QPushButton.primary:hover {{
        background: #4f82ff;
    }}
    QPushButton.primary:disabled {{
        background: {c["--muted"]};
        color: {c["--muted-foreground"]};
        border-color: {c["--border"]};
    }}
    QPushButton.ghost {{
        background: {c["--muted"]};
        border: 1px solid {c["--border"]};
        color: {c["--foreground"]};
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: 600;
    }}
    QPushButton.ghost:hover {{
        background: #252c3c;
    }}
    QPushButton.danger {{
        background: {c["--destructive"]};
        color: {c["--destructive-foreground"]};
        border: none;
        border-radius: 12px;
        padding: 12px 16px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }}
    /* Inputs */
    QLineEdit {{
        background: {c["--input"]};
        border: 1px solid {c["--border"]};
        border-radius: 10px;
        padding: 8px 10px;
        color: {c["--foreground"]};
    }}
    /* Terminal */
    QTabWidget::pane {{
        border: 1px solid {c["--border"]};
        background: #000;
        border-radius: 10px;
    }}
    QTabBar::tab {{
        background: {c["--card"]};
        border: 1px solid {c["--border"]};
        border-bottom: none;
        padding: 6px 12px;
        color: {c["--muted-foreground"]};
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: #000;
        color: #36d399;
        border-color: {c["--border"]};
    }}
    QTextEdit#terminalArea {{
        background: #000;
        color: #36d399;
        border: none;
    }}
    /* Sliders / progress */
    QSlider::groove:horizontal {{
        background: {c["--border"]};
        height: 6px;
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {c["--primary"]};
        width: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}
    QProgressBar {{
        background: {c["--muted"]};
        border: 1px solid {c["--border"]};
        border-radius: 8px;
        text-align: center;
        color: {c["--foreground"]};
    }}
    QProgressBar::chunk {{
        background: {c["--primary"]};
        border-radius: 8px;
    }}
    QLabel.small-label {{
        color: {c["--muted-foreground"]};
        font-size: 12px;
    }}
    QLabel.value-label {{
        font-family: 'Consolas';
        font-weight: 700;
    }}
    """


def add_shadow(widget, radius=18, opacity=0.28, dx=0, dy=6):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(radius)
    effect.setOffset(dx, dy)
    effect.setColor(QColor(0, 0, 0, int(opacity * 255)))
    effect.setEnabled(True)
    widget.setGraphicsEffect(effect)


class TopBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("topbar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        title = QLabel("UFK Takımı İstasyon")
        title.setObjectName("title")
        layout.addWidget(title)

        layout.addStretch()

        time_col = QVBoxLayout()
        tlabel = QLabel("Sistem Zamanı")
        tlabel.setStyleSheet("color:#9aa7bf; font-size:12px;")
        self.time_value = QLabel("--:--:--")
        self.time_value.setStyleSheet("font-family:'Consolas'; font-size:16px; font-weight:700;")
        time_col.addWidget(tlabel, alignment=Qt.AlignRight)
        time_col.addWidget(self.time_value, alignment=Qt.AlignRight)
        layout.addLayout(time_col)

    def set_time(self, text: str):
        self.time_value.setText(text)


class ControlPanel(QFrame):
    toggledConnect = pyqtSignal(bool)
    toggledStart = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setProperty("class", "panel")
        add_shadow(self)
        self.is_connected = False
        self.is_active = False

        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(14)

        # Connection status
        header = QHBoxLayout()
        dot = QLabel("●")
        dot.setStyleSheet("color:#ff5c5c; font-size:16px;")
        self.conn_dot = dot
        header.addWidget(dot)
        header.addWidget(QLabel("Bağlantı"), 1)
        self.conn_label = QLabel("ÇEVRİMDIŞI")
        header.addWidget(self.conn_label, 0, Qt.AlignRight)
        v.addLayout(header)

        # Connect button
        self.connect_btn = QPushButton("BAGLAN")
        self.connect_btn.setProperty("class", "primary")
        self.connect_btn.clicked.connect(self._toggle_connect)
        v.addWidget(self.connect_btn)

        # Start button
        self.start_btn = QPushButton("BAŞLAT")
        self.start_btn.setProperty("class", "primary")
        self.start_btn.clicked.connect(self._toggle_start)
        v.addWidget(self.start_btn)

        # Mode button
        self.mode_btn = QPushButton("MOD DEĞİŞTİR")
        self.mode_btn.setProperty("class", "ghost")
        v.addWidget(self.mode_btn)

    def _toggle_connect(self):
        self.is_connected = not self.is_connected
        self.refresh()
        self.toggledConnect.emit(self.is_connected)

    def _toggle_start(self):
        if not self.is_connected:
            return
        self.is_active = not self.is_active
        self.refresh()
        self.toggledStart.emit(self.is_active)

    def refresh(self):
        if self.is_connected:
            self.conn_dot.setStyleSheet("color:#36d399; font-size:16px;")
            self.conn_label.setText("BAĞLI")
            self.connect_btn.setText("KES")
            self.start_btn.setEnabled(True)
        else:
            self.conn_dot.setStyleSheet("color:#ff5c5c; font-size:16px;")
            self.conn_label.setText("ÇEVRİMDIŞI")
            self.connect_btn.setText("BAGLAN")
            self.start_btn.setEnabled(False)
            self.is_active = False
        self.start_btn.setText("DURDUR" if self.is_active else "BAŞLAT")


class MainMenuPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setProperty("class", "panel")
        add_shadow(self)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        title = QLabel("Ana Menü")
        title.setStyleSheet("font-weight:700;")
        v.addWidget(title)

        actions = ["QR Koordinatı", "Sunucu Bağlantısı", "Ayarlar", "Git"]
        for act in actions:
            btn = QPushButton(act)
            btn.setProperty("class", "ghost")
            btn.setFixedHeight(34)
            v.addWidget(btn)

        # Password section (always visible for simplicity)
        password = QLineEdit()
        password.setPlaceholderText("Görev Emri Şifresi")
        v.addWidget(password)


class MapPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setProperty("class", "panel")
        add_shadow(self)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        bg = QFrame()
        bg.setStyleSheet(
            "border-radius:10px; background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #0f1f3a, stop:1 #152a4d);"
        )
        bg_layout = QVBoxLayout(bg)
        bg_layout.setContentsMargins(16, 16, 16, 16)

        # HUD overlay imitation
        top_row = QHBoxLayout()
        top_row.addStretch()
        conn = QLabel("BAĞLANTI")
        conn.setFixedHeight(32)
        conn.setAlignment(Qt.AlignCenter)
        conn.setStyleSheet("padding:6px 12px; border-radius:8px; background:rgba(52,211,153,0.75); color:white; font-weight:700;")
        top_row.addWidget(conn, 0, Qt.AlignRight | Qt.AlignTop)
        bg_layout.addLayout(top_row)

        bg_layout.addStretch()
        center = QLabel("HARİTA")
        center.setAlignment(Qt.AlignCenter)
        center.setStyleSheet("color: rgba(255,255,255,0.8); font-size:48px; font-weight:800;")
        bg_layout.addWidget(center)
        bg_layout.addStretch()

        bottom = QFrame()
        bottom.setFixedHeight(64)
        bottom.setStyleSheet("background:qlineargradient(spread:pad, x1:0, y1:1, x2:0, y2:0, stop:0 rgba(0,0,0,0.55), stop:1 transparent);")
        bg_layout.addWidget(bottom)

        v.addWidget(bg)


class VideoPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setProperty("class", "panel")
        add_shadow(self)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        bg = QFrame()
        bg.setStyleSheet(
            "border-radius:10px; background:black;"
            "background-image: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(63,115,255,0.18), stop:1 rgba(132,102,255,0.18));"
        )
        layout = QVBoxLayout(bg)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        center = QLabel("Canlı Video")
        center.setStyleSheet("color:#9aa7bf; font-size:14px;")
        center.setAlignment(Qt.AlignCenter)
        layout.addWidget(center)
        layout.addStretch()

        badge = QLabel("● ÇEVRİMDIŞI")
        badge.setStyleSheet(
            "color:#ff5c5c; font-weight:700; background:rgba(0,0,0,0.6); padding:6px 10px; border-radius:12px;"
        )
        badge.setAlignment(Qt.AlignRight | Qt.AlignTop)
        layout.addWidget(badge, alignment=Qt.AlignRight | Qt.AlignTop)

        v.addWidget(bg)


class TerminalPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setProperty("class", "panel")
        add_shadow(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.North)
        for name in ["Makine", "Jetson", "Sunucu (Servo)"]:
            area = QTextEdit()
            area.setReadOnly(True)
            area.setObjectName("terminalArea")
            area.setText(
                f"[{name}] Terminal başlatıldı...\n[{name}] Sistem hazır\n[{name}] Komut bekleniyor...\n> _"
            )
            tabs.addTab(area, name)
        layout.addWidget(tabs)


class SystemStatusPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setProperty("class", "panel")
        add_shadow(self, opacity=0.15, dy=3)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        title = QLabel("Sistem Durumu")
        title.setStyleSheet("font-weight:700;")
        v.addWidget(title)

        items = [
            ("GPS", "37.7749, -122.4194"),
            ("Yükseklik", "245 m"),
            ("Hız", "12.5 m/s"),
            ("Batarya", "87 %"),
            ("Sinyal Şiddeti", "Güçlü"),
            ("Sistem Zamanı", "--:--:--"),
            ("Hata Kodu", "--"),
        ]
        self.time_label = None
        for label, value in items:
            row = QHBoxLayout()
            key = QLabel(label)
            key.setObjectName("small")
            key.setStyleSheet("color:#9aa7bf; font-size:12px;")
            val = QLabel(value)
            val.setStyleSheet("font-family:'Consolas'; font-weight:700;")
            if label == "Sistem Zamanı":
                self.time_label = val
            row.addWidget(key)
            row.addStretch()
            row.addWidget(val)
            v.addLayout(row)

    def set_time(self, text: str):
        if self.time_label:
            self.time_label.setText(text)


class RankingPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setProperty("class", "panel")
        add_shadow(self, opacity=0.15, dy=3)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(10)

        title = QLabel("Rakip Takım Uçakları Sıralaması")
        title.setStyleSheet("font-weight:700;")
        v.addWidget(title)

        teams = [("Takım A", 245), ("Takım B", 198), ("Takım C", 176), ("Takım D", 152)]
        for i, (name, score) in enumerate(teams, 1):
            box = QFrame()
            box.setStyleSheet(
                f"background:{COLOR_VARS['--muted']}; border:1px solid {COLOR_VARS['--border']}; border-radius:8px;"
            )
            row_layout = QHBoxLayout(box)
            row_layout.setContentsMargins(10, 6, 10, 6)
            row_layout.setSpacing(6)
            rank = QLabel(f"#{i}")
            rank.setStyleSheet("color:#3f73ff; font-weight:700;")
            row_layout.addWidget(rank)
            row_layout.addWidget(QLabel(name), 1)
            val = QLabel(str(score))
            val.setStyleSheet("font-family:'Consolas'; font-weight:700;")
            row_layout.addWidget(val)
            v.addWidget(box)


class FlightControlPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setProperty("class", "panel")
        add_shadow(self, opacity=0.15, dy=3)
        v = QVBoxLayout(self)
        v.setContentsMargins(16, 16, 16, 16)
        v.setSpacing(12)

        title = QLabel("Uçuş Kontrol Sistemi")
        title.setStyleSheet("font-weight:700;")
        v.addWidget(title)

        # Motor tests
        v.addWidget(self._section_label("Motor Testleri"))
        grid1 = QGridLayout()
        grid1.setHorizontalSpacing(8)
        grid1.setVerticalSpacing(8)
        for idx, text in enumerate(["Motor 1 Test", "Motor 2 Test"]):
            btn = QPushButton(text)
            btn.setProperty("class", "ghost")
            btn.setFixedHeight(34)
            grid1.addWidget(btn, idx // 2, idx % 2)
        v.addLayout(grid1)

        # Roll
        v.addWidget(self._section_label("Roll Kontrolü"))
        grid2 = QGridLayout()
        grid2.setHorizontalSpacing(8)
        grid2.setVerticalSpacing(8)
        for idx, text in enumerate(["Tam Sağ Roll", "Tam Sol Roll"]):
            btn = QPushButton(text)
            btn.setProperty("class", "ghost")
            btn.setFixedHeight(34)
            grid2.addWidget(btn, idx // 2, idx % 2)
        v.addLayout(grid2)

        # Pitch
        v.addWidget(self._section_label("Pitch Kontrolü"))
        grid3 = QGridLayout()
        grid3.setHorizontalSpacing(8)
        grid3.setVerticalSpacing(8)
        for idx, text in enumerate(["Tam Yukarı Pitch", "Tam Aşağı Pitch"]):
            btn = QPushButton(text)
            btn.setProperty("class", "ghost")
            btn.setFixedHeight(34)
            grid3.addWidget(btn, idx // 2, idx % 2)
        v.addLayout(grid3)

        # Yaw
        v.addWidget(self._section_label("Yaw (Dümen) Kontrolü"))
        grid4 = QGridLayout()
        grid4.setHorizontalSpacing(8)
        grid4.setVerticalSpacing(8)
        for idx, text in enumerate(["Tam Sağ Yaw", "Tam Sol Yaw"]):
            btn = QPushButton(text)
            btn.setProperty("class", "ghost")
            btn.setFixedHeight(34)
            grid4.addWidget(btn, idx // 2, idx % 2)
        v.addLayout(grid4)

        # Failsafe
        btn = QPushButton("Failsafe Test")
        btn.setProperty("class", "ghost")
        v.addWidget(btn)

        # Auto test
        auto = QPushButton("Oto Test")
        auto.setProperty("class", "primary")
        auto.setFixedHeight(40)
        v.addWidget(auto)

    @staticmethod
    def _section_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color:#9aa7bf; font-size:11px; font-weight:700; letter-spacing:0.6px;")
        return lbl


class HudPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("panel")
        self.setProperty("class", "panel")
        add_shadow(self, opacity=0.18, dy=4)
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 12, 12, 12)
        v.setSpacing(8)

        title = QLabel("HUD")
        title.setStyleSheet("font-weight:700;")
        v.addWidget(title)

        body = QFrame()
        body.setStyleSheet(
            "border-radius:10px; border:1px solid rgba(255,255,255,0.08);"
            "background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1f3a5f, stop:0.5 #0b0f18, stop:1 #352114);"
        )
        body.setMinimumHeight(220)
        b = QVBoxLayout(body)
        b.setContentsMargins(12, 12, 12, 12)
        b.setSpacing(6)

        # Top chips
        top = QHBoxLayout()
        for text, color in [
            ("BAĞLANTI", "rgba(54,211,153,0.9)"),
            ("GPS FIX", "rgba(110,231,183,0.9)"),
            ("MODE AUTO", "rgba(126,134,150,0.65)"),
        ]:
            chip = QLabel(text)
            chip.setStyleSheet(
                f"padding:6px 10px; border-radius:10px; background:{color}; color:black; font-weight:700; font-size:11px;"
            )
            top.addWidget(chip)
        top.addStretch()
        b.addLayout(top)

        # Horizon-style center
        horizon_wrap = QVBoxLayout()
        horizon_wrap.setContentsMargins(0, 0, 0, 0)
        horizon_wrap.setSpacing(6)

        horizon = QFrame()
        horizon.setFixedHeight(140)
        horizon.setStyleSheet(
            "border-radius:8px;"
            "background: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #1f3a5f, stop:0.48 #1b2738, stop:0.52 #3a2415, stop:1 #3a2415);"
        )
        h_layout = QVBoxLayout(horizon)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        # Horizon line
        line = QFrame()
        line.setFixedHeight(2)
        line.setStyleSheet(f"background:{COLOR_VARS['--primary']};")
        h_layout.addStretch()
        h_layout.addWidget(line)
        h_layout.addStretch()

        # Center reticle
        ret = QLabel("+")
        ret.setAlignment(Qt.AlignCenter)
        ret.setStyleSheet(f"color:{COLOR_VARS['--primary']}; font-size:20px; font-weight:800;")
        h_layout.addWidget(ret, 0, Qt.AlignCenter)

        horizon_wrap.addWidget(horizon)
        b.addLayout(horizon_wrap)

        # Bottom telemetry row
        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        telem = [
            ("ALT", "245 m"),
            ("SPD", "12.5 m/s"),
            ("BAT", "87%"),
            ("SİNYAL", "Güçlü"),
        ]
        for key, val in telem:
            box = QFrame()
            box.setStyleSheet(
                f"background:rgba(18,23,36,0.8); border:1px solid {COLOR_VARS['--border']}; border-radius:8px;"
            )
            bl = QVBoxLayout(box)
            bl.setContentsMargins(8, 6, 8, 6)
            bl.setSpacing(2)
            k = QLabel(key)
            k.setStyleSheet("color:#9aa7bf; font-size:11px; font-weight:700;")
            vlabel = QLabel(val)
            vlabel.setStyleSheet("font-family:'Consolas'; font-weight:700;")
            bl.addWidget(k)
            bl.addWidget(vlabel)
            bottom.addWidget(box)
        bottom.addStretch()
        b.addLayout(bottom)
        v.addWidget(body)


class FlightControlWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Uçuş Kontrol Sistemi")
        self.resize(480, 640)
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        panel = FlightControlPanel()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(panel)
        layout.addWidget(scroll)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ground Control Station - Teknofest")
        self.resize(1366, 768)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # Top bar
        self.topbar = TopBar()
        root.addWidget(self.topbar)

        # Main grid: 12 columns equivalent -> 3 buckets 2/7/3
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        # Left column (col-span 2)
        left_col = QVBoxLayout()
        left_col.setSpacing(10)
        self.control_panel = ControlPanel()
        self.main_menu = MainMenuPanel()
        left_col.addWidget(self.control_panel)
        left_col.addWidget(self.main_menu)
        left_col.addStretch()
        grid.addLayout(left_col, 0, 0, 2, 1)

        # Center column (col-span 7)
        center_col = QVBoxLayout()
        center_col.setSpacing(10)
        self.map_panel = MapPanel()
        self.map_panel.setMinimumHeight(460)
        self.ranking = RankingPanel()
        self.terminal_panel = TerminalPanel()
        center_col.addWidget(self.map_panel)
        center_col.addWidget(self.ranking)
        center_col.addWidget(self.terminal_panel)
        grid.addLayout(center_col, 0, 1, 2, 1)

        # Right column (col-span 3)
        right_col_widget = QWidget()
        right_col = QVBoxLayout(right_col_widget)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(10)
        self.video_panel = VideoPanel()
        self.video_panel.setMinimumHeight(320)
        self.system_status = SystemStatusPanel()
        self.hud_panel = HudPanel()
        self.flight_btn = QPushButton("Uçuş Kontrol Penceresi")
        self.flight_btn.setProperty("class", "primary")
        self.flight_btn.setFixedHeight(44)
        self.flight_btn.clicked.connect(self.open_flight_window)
        self.emergency = QPushButton("ACİL DURMA")
        self.emergency.setProperty("class", "danger")
        self.emergency.setFixedHeight(52)
        right_col.addWidget(self.video_panel)
        right_col.addWidget(self.system_status)
        right_col.addWidget(self.hud_panel)
        right_col.addWidget(self.flight_btn)
        right_col.addWidget(self.emergency)
        right_col.addStretch()

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.NoFrame)
        right_scroll.setWidget(right_col_widget)
        grid.addWidget(right_scroll, 0, 2, 2, 1)

        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 7)
        grid.setColumnStretch(2, 3)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)

        root.addWidget(grid_container)

        # Apply style
        self.setStyleSheet(build_qss(COLOR_VARS))

        # Size policies
        self.map_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.terminal_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # Signals
        self.control_panel.toggledConnect.connect(self.on_connect_changed)
        self.control_panel.toggledStart.connect(self.on_start_changed)

        # Timer for clock
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick_time)
        self.timer.start(1000)
        self.tick_time()

        self.control_panel.refresh()
        self.flight_window = None

    def tick_time(self):
        from datetime import datetime

        now = datetime.now().strftime("%H:%M:%S")
        self.topbar.set_time(now)
        self.system_status.set_time(now)

    def on_connect_changed(self, connected: bool):
        status = "BAĞLANTI" if connected else "ÇEVRİMDIŞI"
        color = "#36d399" if connected else "#ff5c5c"
        # Update video badge
        for child in self.video_panel.findChildren(QLabel):
            if "●" in child.text() or "ÇEVRİMDIŞI" in child.text() or "BAĞLANTI" in child.text():
                child.setText(f"● {status}")
                child.setStyleSheet(
                    f"color:{color}; font-weight:700; background:rgba(0,0,0,0.6); padding:6px 10px; border-radius:12px;"
                )

    def on_start_changed(self, active: bool):
        # No-op placeholder for future state-based UI changes
        _ = active

    def open_flight_window(self):
        if self.flight_window is None:
            self.flight_window = FlightControlWindow(self)
            # inherit style
            self.flight_window.setStyleSheet(self.styleSheet())
        self.flight_window.show()
        self.flight_window.raise_()
        self.flight_window.activateWindow()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

