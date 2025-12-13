# widgets/video_widget.py
import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap
import threading

class VideoWidget(QWidget):
    connection_result = pyqtSignal(bool, object) # success, cap_object

    def __init__(self, parent=None, port=5000):
        super().__init__(parent)
        self.setObjectName("videoWidget")
        self._port = port
        self._cap = None
        self._is_connecting = False

        self.connection_result.connect(self._on_connection_result)

        # Ana layout
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)

        # 1) Video Label
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setMinimumSize(320, 240)
        self._label.setStyleSheet("background-color: black;")
        self._layout.addWidget(self._label)

        # 2) Error / Retry Widget (başlangıçta gizli)
        self._error_widget = QWidget(self)
        self._error_widget.setObjectName("videoErrorWidget")
        self._error_widget.hide()
        
        err_lay = QVBoxLayout(self._error_widget)
        err_lay.setAlignment(Qt.AlignCenter)
        err_lay.setSpacing(10)

        self._alert_lbl = QLabel("Kamera bağlantısı yok")
        self._alert_lbl.setObjectName("videoErrorLabel")
        self._alert_lbl.setAlignment(Qt.AlignCenter)

        self._retry_btn = QPushButton("Tekrar Dene")
        self._retry_btn.setObjectName("retryVideoBtn")
        self._retry_btn.setCursor(Qt.PointingHandCursor)
        self._retry_btn.clicked.connect(self.start)

        err_lay.addWidget(self._alert_lbl)
        err_lay.addWidget(self._retry_btn)

        self._layout.addWidget(self._error_widget)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._update_frame)

    def _open_capture_threaded(self):
        # GStreamer: appsink'e bloklamayı azaltan ayarlar ekledik
        gst_pipeline = (
            f'udpsrc port={self._port} '
            'caps="application/x-rtp, media=video, encoding-name=H264, payload=96" ! '
            'rtph264depay ! '
            'avdec_h264 ! '
            'videoconvert ! '
            'appsink sync=false max-buffers=1 drop=true'
        )

        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        if cap is not None and cap.isOpened():
            print("[VideoWidget] GStreamer pipeline ile açıldı.")
            self.connection_result.emit(True, cap)
        else:
            print("[VideoWidget] Uyarı: VideoCapture açılamadı.")
            self.connection_result.emit(False, None)

    def start(self):
        if self._is_connecting:
            return

        # UI hazırlık
        self._error_widget.hide()
        self._label.show()
        # Kullanıcıya bir şey olduğunu hissettirmek için label'a text yazabiliriz ama 
        # siyah ekran siyah kalacaksa sorun yok.
        self._label.setText("Bağlanıyor...")
        self._label.setStyleSheet("background-color: black; color: white;")
        
        self._is_connecting = True
        self._retry_btn.setEnabled(False) 
        
        # Thread başlat
        t = threading.Thread(target=self._open_capture_threaded, daemon=True)
        t.start()

    def _on_connection_result(self, success, cap):
        self._is_connecting = False
        self._retry_btn.setEnabled(True)

        if success:
            self._cap = cap
            self._label.setText("") # Texti temizle
            self._timer.start()
        else:
            self._cap = None
            self._label.hide()
            self._error_widget.show()
            self._alert_lbl.setText("Kamera bağlantısı başarısız")

    def stop(self):
        self._timer.stop()
        if self._cap is not None:
             # Release işlemi de bloklayabilir, thread'e almak iyi olur ama
             # kapanışta çok dert olmayabilir. Yine de try-except ekliyoruz.
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    def _update_frame(self):
        if self._cap is None:
            return

        ret, frame = self._cap.read()
        if not ret or frame is None:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pix = QPixmap.fromImage(qimg).scaled(
            self._label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self._label.setPixmap(pix)

    def resizeEvent(self, e):
        pm = self._label.pixmap()
        if pm is not None:
            self._label.setPixmap(pm.scaled(
                self._label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            ))
        super().resizeEvent(e)

    def closeEvent(self, e):
        self.stop()
        super().closeEvent(e)
