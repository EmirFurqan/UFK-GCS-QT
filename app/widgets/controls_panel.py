from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton


class ControlsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlsPanel")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        # Ortala
        self.centerBtn = QPushButton("Ortala")
        self.centerBtn.setObjectName("centerBtn")
        self.centerBtn.setFixedHeight(32)

        # Bölge
        self.regionBtn = QPushButton("Bölge")
        self.regionBtn.setObjectName("regionBtn")
        self.regionBtn.setFixedHeight(32)

        # MISSION
        self.missionBtn = QPushButton("Mission")
        self.missionBtn.setObjectName("missionBtn")
        self.missionBtn.setFixedHeight(32)

        # QR Noktası
        self.qrBtn = QPushButton("QR")
        self.qrBtn.setObjectName("qrBtn")
        self.qrBtn.setFixedHeight(32)

        # ÖN KONTROL (Pre-Check)
        self.preCheckBtn = QPushButton("Ön Kontrol")
        self.preCheckBtn.setObjectName("preCheckBtn")
        self.preCheckBtn.setFixedHeight(32)
        # Stil olarak biraz farklı yapabiliriz (opsiyonel)

        # Yerleştir
        lay.addWidget(self.centerBtn)
        lay.addWidget(self.regionBtn)
        lay.addWidget(self.missionBtn)
        lay.addWidget(self.qrBtn)
        lay.addWidget(self.preCheckBtn)
        lay.addStretch(1)
