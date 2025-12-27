
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

class ConnectionStatusWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(15)

        # Style helpers
        self.style_base = "font-weight: bold; padding: 4px 8px; border-radius: 4px;"
        self.color_gray = "background-color: #555; color: #aaa;"
        self.color_green = "background-color: #2e7d32; color: white;"
        self.color_red = "background-color: #c62828; color: white;"
        self.color_yellow = "background-color: #f9a825; color: black;"

        # Indicators
        self.plane_lbl = self._create_indicator("Uçak: Bağlı Değil", self.color_gray)
        self.cam_lbl = self._create_indicator("Kamera: Kapalı", self.color_gray)
        self.server_lbl = self._create_indicator("Sunucu: Beklemede", self.color_gray)

        self.layout.addWidget(self.plane_lbl)
        self.layout.addWidget(self.cam_lbl)
        self.layout.addWidget(self.server_lbl)

    def _create_indicator(self, text, initial_style):
        lbl = QLabel(text)
        lbl.setStyleSheet(self.style_base + initial_style)
        lbl.setAlignment(Qt.AlignCenter)
        return lbl

    def set_plane_status(self, connected: bool, text=None):
        if connected:
            self.plane_lbl.setStyleSheet(self.style_base + self.color_green)
            self.plane_lbl.setText(text if text else "Uçak: Bağlı")
        else:
            self.plane_lbl.setStyleSheet(self.style_base + self.color_red)
            self.plane_lbl.setText(text if text else "Uçak: Koptu")

    def set_plane_text(self, text, color="gray"):
        style = self.color_gray
        if color == "green": style = self.color_green
        elif color == "red": style = self.color_red
        elif color == "yellow": style = self.color_yellow
        
        self.plane_lbl.setStyleSheet(self.style_base + style)
        self.plane_lbl.setText(text)

    def set_camera_status(self, active: bool):
        if active:
            self.cam_lbl.setStyleSheet(self.style_base + self.color_green)
            self.cam_lbl.setText("Kamera: Açık")
        else:
            self.cam_lbl.setStyleSheet(self.style_base + self.color_gray)
            self.cam_lbl.setText("Kamera: Kapalı")

    def set_server_text(self, text, color="gray"):
        style = self.color_gray
        if color == "green": style = self.color_green
        elif color == "red": style = self.color_red
        elif color == "yellow": style = self.color_yellow
        
        self.server_lbl.setStyleSheet(self.style_base + style)
        self.server_lbl.setText(f"Sunucu: {text}")

    def set_server_status(self, success: bool, code=None):
        if success:
            self.server_lbl.setStyleSheet(self.style_base + self.color_green)
            self.server_lbl.setText(f"Sunucu: OK ({code})")
        else:
            self.server_lbl.setStyleSheet(self.style_base + self.color_red)
            txt = f"Sunucu: Hata"
            if code: txt += f" ({code})"
            self.server_lbl.setText(txt)
