from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton


class ControlsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("controlsPanel")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        self.centerBtn = QPushButton("Ortala")
        self.centerBtn.setObjectName("centerBtn")
        self.centerBtn.setFixedHeight(32)

        self.regionBtn = QPushButton("Bölge")
        self.regionBtn.setObjectName("regionBtn")
        self.regionBtn.setFixedHeight(32)

        lay.addWidget(self.centerBtn)
        lay.addWidget(self.regionBtn)
        lay.addStretch(1)


