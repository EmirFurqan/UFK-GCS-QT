        # ----- ALT BÖLGE: 3 DİKEY PARÇA -----
        bottom = QWidget(center)
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        # solda map, ortada kamera, sağda HUD
        bottom_layout.addWidget(self.map, 2)    # sol
        bottom_layout.addWidget(self.video, 3)  # orta
        bottom_layout.addWidget(self.hud, 2)    # sağ

        # ----- ÜSTTEN ALTA DİZ -----
        center_layout.addWidget(header, 0)
        center_layout.addWidget(self.panel, 0)
        center_layout.addWidget(self.controls, 0)
        center_layout.addWidget(bottom, 1)