
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QStackedWidget, QGroupBox, QMessageBox, QFormLayout
)
from PyQt5.QtCore import Qt
from config.settings_manager import SettingsManager

class ConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bağlantı Ayarları")
        self.resize(400, 450)
        self.settings = SettingsManager.load_settings()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # --- Plane Connection Section ---
        plane_group = QGroupBox("Uçak Bağlantısı")
        plane_layout = QVBoxLayout(plane_group)

        # Connection Type Selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Bağlantı Tipi:"))
        self.conn_type_combo = QComboBox()
        self.conn_type_combo.addItems(["UDP", "Serial"])
        type_layout.addWidget(self.conn_type_combo)
        plane_layout.addLayout(type_layout)

        # Stacked Widget for changing inputs
        self.plane_stack = QStackedWidget()
        
        # Page 1: TCP
        page_tcp = QFormLayout()
        self.tcp_addr_input = QLineEdit()
        self.tcp_port_input = QLineEdit()
        page_tcp.addRow("IP Adresi:", self.tcp_addr_input)
        page_tcp.addRow("Port:", self.tcp_port_input)
        
        tcp_widget = QGroupBox("TCP Ayarları") # Optional: wrap in widget/group
        tcp_widget.setLayout(page_tcp) # Layout can't be set directly on layout, need widget
        
        w_tcp = QGroupBox("UDP Detayları")
        w_tcp.setLayout(page_tcp)
        
        self.plane_stack.addWidget(w_tcp)

        # Page 2: Serial
        page_serial = QFormLayout()
        self.serial_port_input = QLineEdit()
        self.serial_baud_input = QLineEdit()
        page_serial.addRow("Cihaz (Port):", self.serial_port_input)
        page_serial.addRow("Baud Rate:", self.serial_baud_input)
        
        w_serial = QGroupBox("Serial Detayları")
        w_serial.setLayout(page_serial)
        
        self.plane_stack.addWidget(w_serial)

        plane_layout.addWidget(self.plane_stack)
        layout.addWidget(plane_group)

        # --- Camera Connection Section ---
        cam_group = QGroupBox("Kamera Bağlantısı")
        cam_layout = QFormLayout(cam_group)
        self.cam_port_input = QLineEdit()
        cam_layout.addRow("Port:", self.cam_port_input)
        layout.addWidget(cam_group)

        # --- Server Connection Section ---
        server_group = QGroupBox("Yarışma Sunucusu")
        page_server_layout = QVBoxLayout(server_group) # Changed to QVBoxLayout
        
        # Adres
        page_server_layout.addWidget(QLabel("Sunucu Adresi:"))
        self.server_url_input = QLineEdit() # Renamed from server_addr_input
        page_server_layout.addWidget(self.server_url_input)
        
        # Kullanıcı Adı
        page_server_layout.addWidget(QLabel("Kullanıcı Adı:"))
        self.server_user_input = QLineEdit()
        page_server_layout.addWidget(self.server_user_input)
        
        # Şifre
        page_server_layout.addWidget(QLabel("Şifre:"))
        self.server_pass_input = QLineEdit()
        self.server_pass_input.setEchoMode(QLineEdit.Password)
        page_server_layout.addWidget(self.server_pass_input)
        
        page_server_layout.addStretch(1) # Added stretch to push content to top
        layout.addWidget(server_group)

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        
        self.btn_connect = QPushButton("Bağlan")
        self.btn_connect.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 6px;")
        self.btn_connect.clicked.connect(self.on_connect)
        
        self.btn_disconnect = QPushButton("Bağlantıyı Kes")
        self.btn_disconnect.setStyleSheet("background-color: #c62828; color: white; font-weight: bold; padding: 6px;")
        self.btn_disconnect.clicked.connect(self.on_disconnect)

        self.btn_save = QPushButton("Sadece Kaydet")
        self.btn_save.clicked.connect(self.on_save)
        
        btn_layout.addWidget(self.btn_disconnect)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_connect)
        layout.addLayout(btn_layout)

        # Logic
        self.conn_type_combo.currentIndexChanged.connect(self.on_type_changed)
        
        # Load initial values
        self.load_to_ui()

    def on_connect(self):
        if self.save_settings_internal():
            self.done(1) # 1: Connect

    def on_disconnect(self):
        # Ayarları kaydetmeye gerek var mı? Belki.
        self.done(2) # 2: Disconnect

    def on_save(self):
        if self.save_settings_internal():
            QMessageBox.information(self, "Başarılı", "Ayarlar kaydedildi.")
            self.done(0) # 0: Just save (or cancel action basically, but saved)

    def save_settings_internal(self):
        # Validate inputs if needed
        current_type = self.conn_type_combo.currentText().lower()
        
        u_name = self.server_user_input.text().strip()
        if len(u_name) > 0 and len(u_name) < 3:
             QMessageBox.warning(self, "Hata", "Kullanıcı adı en az 3 karakter olmalı.")
             return False
        
        new_settings = {
            "plane_connection_type": current_type,
            "plane_address": self.tcp_addr_input.text().strip(),
            "plane_port": self.tcp_port_input.text().strip(),
            "plane_serial_port": self.serial_port_input.text().strip(),
            "plane_baud": self.serial_baud_input.text().strip(),
            "camera_port": self.cam_port_input.text().strip(),
            "server_address": self.server_url_input.text().strip(),
            "server_username": self.server_user_input.text().strip(),
            "server_password": self.server_pass_input.text().strip()
        }
        
        return SettingsManager.save_settings(new_settings)

    def save_settings(self):
        # Legacy method kept if needed, but we use internal now
        pass

    def on_type_changed(self, index):
        self.plane_stack.setCurrentIndex(index)

    def load_to_ui(self):
        s = self.settings
        
        # Plane
        ctype = s.get("plane_connection_type", "udp")
        if ctype.lower() == "serial":
            self.conn_type_combo.setCurrentIndex(1)
        else:
            self.conn_type_combo.setCurrentIndex(0)
            
        self.tcp_addr_input.setText(s.get("plane_address", "0.0.0.0"))
        self.tcp_port_input.setText(str(s.get("plane_port", "14550")))
        self.serial_port_input.setText(s.get("plane_serial_port", "/dev/ttyUSB0"))
        self.serial_baud_input.setText(str(s.get("plane_baud", "57600")))
        
        # Camera
        self.cam_port_input.setText(str(s.get("camera_port", "5000")))
        
        # Server
        self.server_url_input.setText(s.get("server_address", "http://10.1.36.78:8000"))
        self.server_user_input.setText(s.get("server_username", ""))
        self.server_pass_input.setText(s.get("server_password", ""))

