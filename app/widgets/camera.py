# widgets/video_widget.py
import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


class VideoWidget(QWidget):
    def __init__(self, parent=None, port=5000):
        super().__init__(parent)
        self.setObjectName("videoWidget")
        self._port = port
        self._cap = None

        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setMinimumSize(320, 240)
        self._label.setStyleSheet("background-color: black;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._update_frame)

        # ÖNEMLİ: init'te capture açma yok.
        # self._open_capture()  <-- BUNU SİLDİK

    def _open_capture(self):
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
            self._cap = cap
            return True

        print("[VideoWidget] Uyarı: VideoCapture açılamadı.")
        self._cap = None
        return False

    def start(self):
        # Event loop başladıktan sonra capture aç
        def _start_impl():
            if self._cap is None:
                ok = self._open_capture()
                if not ok:
                    return
            self._timer.start()

        QTimer.singleShot(0, _start_impl)

    def stop(self):
        self._timer.stop()
        if self._cap is not None:
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
