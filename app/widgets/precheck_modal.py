from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QWidget, QGridLayout, QFrame
)
from PyQt5.QtCore import Qt, QTimer

class PreCheckDialog(QDialog):
    def __init__(self, parent=None, worker=None):
        super().__init__(parent)
        self.setWindowTitle("Uçuş Öncesi Kontroller")
        self.resize(600, 400)
        self.worker = worker
        
        # Styles for this dialog specifically
        self.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                font-size: 14px;
                color: #eeeeee;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 8px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            #stepTitle {
                font-size: 18px;
                font-weight: bold;
                color: #4CAF50;
                margin-bottom: 10px;
            }
            #infoLabel {
                font-style: italic;
                color: #aaaaaa;
            }
        """)

        layout = QVBoxLayout(self)

        # Header
        self.titleLbl = QLabel("Adım 1: Motor Kontrolü")
        self.titleLbl.setObjectName("stepTitle")
        self.titleLbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.titleLbl)

        # Stacked Widget for pages
        self.pages = QStackedWidget()
        layout.addWidget(self.pages)

        # --- PAGE 1: ENGINE ---
        page1 = QWidget()
        p1_layout = QVBoxLayout(page1)
        
        info1 = QLabel("Motor butonuna basıldığında motora %10-15 güç verilir.\nPervane dönüşünü ve sesini kontrol edin.")
        info1.setAlignment(Qt.AlignCenter)
        info1.setObjectName("infoLabel")
        p1_layout.addWidget(info1)

        # Tek Motor (Uçak)
        self.btnMotor = QPushButton("Ana Motor (Throttle) Testi")
        self.btnMotor.setFixedSize(250, 60)
        self.btnMotor.clicked.connect(lambda: self.run_motor_test(1))
        
        p1_layout.addStretch(1)
        p1_layout.addWidget(self.btnMotor, 0, Qt.AlignCenter)
        p1_layout.addStretch(1)
        
        self.pages.addWidget(page1)

        # --- PAGE 2: SURFACES ---
        page2 = QWidget()
        p2_layout = QVBoxLayout(page2)

        info2 = QLabel("Kontrol Yüzeyleri (Aileron, Elevator, Rudder).\nButona basınca yüzey hareket eder, sonra merkeze döner.")
        info2.setAlignment(Qt.AlignCenter)
        info2.setObjectName("infoLabel")
        p2_layout.addWidget(info2)

        surf_grid = QGridLayout()
        
        # Uçak Terminolojisi
        btnRollL = QPushButton("Sol Aileron (Sola Yatış)")
        btnRollR = QPushButton("Sağ Aileron (Sağa Yatış)")
        btnPitchU = QPushButton("Elevator Yukarı (Tırmanış)")
        btnPitchD = QPushButton("Elevator Aşağı (Dalış)")
        btnYawL = QPushButton("Rudder Sol (Sola Sapma)")
        btnYawR = QPushButton("Rudder Sağ (Sağa Sapma)")

        btnRollL.clicked.connect(lambda: self.test_surface(0, -0.5, 0, 0)) # Roll -
        btnRollR.clicked.connect(lambda: self.test_surface(0, 0.5, 0, 0))  # Roll +
        
        btnPitchU.clicked.connect(lambda: self.test_surface(0.5, 0, 0, 0)) # Pitch +
        btnPitchD.clicked.connect(lambda: self.test_surface(-0.5, 0, 0, 0))# Pitch -

        btnYawL.clicked.connect(lambda: self.test_surface(0, 0, 0, -0.5))  # Yaw -
        btnYawR.clicked.connect(lambda: self.test_surface(0, 0, 0, 0.5))   # Yaw +
        
        # Grid yerleşimi
        #      PitchU (Elevator Up)
        # RollL      RollR (Ailerons)
        #      PitchD (Elevator Down)
        # ----------------
        # YawL       YawR (Rudder)
        
        surf_grid.addWidget(btnPitchD, 0, 1) # Pitch Stick Forward -> Down -> Elevator Down in simulation? 
                                             # Usually 'Push' stick -> Pitch Down -> Elevator goes DOWN visually? 
                                             # Wait, Pitch UP means Nose UP. Stick BACK.
                                             # Let's keep logic simple: Up btn -> Pitch +
        
        surf_grid.addWidget(btnPitchU, 0, 1) # Tırmanış
        surf_grid.addWidget(btnRollL, 1, 0)
        surf_grid.addWidget(btnRollR, 1, 2)
        surf_grid.addWidget(btnPitchD, 2, 1) # Dalış

        surf_grid.addWidget(QLabel("--- Kuyruk (Rudder) ---"), 3, 1, alignment=Qt.AlignCenter) # Spacer/Title
        
        surf_grid.addWidget(btnYawL, 4, 0)
        surf_grid.addWidget(btnYawR, 4, 2)

        p2_layout.addLayout(surf_grid)
        p2_layout.addStretch(1)
        self.pages.addWidget(page2)

        # Footer Buttons
        btn_layout = QHBoxLayout()
        self.btnCancel = QPushButton("Kapat")
        self.btnCancel.clicked.connect(self.reject)
        self.btnNext = QPushButton("İleri >")
        self.btnNext.clicked.connect(self.go_next)
        
        btn_layout.addStretch(1)
        btn_layout.addWidget(self.btnCancel)
        btn_layout.addWidget(self.btnNext)
        layout.addLayout(btn_layout)

        self.current_step = 0

    def go_next(self):
        if self.current_step == 0:
            self.current_step = 1
            self.pages.setCurrentIndex(1)
            self.titleLbl.setText("Adım 2: Kontrol Yüzeyleri")
            self.btnNext.setText("Bitir")
            # Style update for 'finish' maybe?
        else:
            self.accept()

    def run_motor_test(self, motor_id):
        if self.worker:
            self.worker.test_motor(motor_id)

    def test_surface(self, x, y, z, r):
        """
        x=pitch, y=roll, z=throttle, r=yaw
        1. Komutu gönder
        2. 1 sn sonra sıfırla
        """
        if self.worker:
            self.worker.send_manual_control(x, y, z, r)
            QTimer.singleShot(1000, lambda: self.worker.send_manual_control(0, 0, 0, 0))

