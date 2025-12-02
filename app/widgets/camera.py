# widgets/video_widget.py
import cv2
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


class VideoWidget(QWidget):
    """
    UDP üzerinden gelen H264 videoyu OpenCV ile okuyup Qt içinde gösterir.

    Denenecek iki yol:
      1) GStreamer backend ile:
         udpsrc port=5000 caps="application/x-rtp, media=video, encoding-name=H264, payload=96" !
         rtph264depay ! avdec_h264 ! videoconvert ! appsink

      2) FFMPEG backend ile:
         udp://0.0.0.0:5000  (OpenCV FFMPEG destekliyse)

    OpenCV derlemen neyi destekliyorsa onu kullanır.
    """

    def __init__(self, parent=None, port=5000):
        super().__init__(parent)
        self.setObjectName("videoWidget")
        self._port = port
        self._cap = None

        # görüntünün çizileceği label
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setMinimumSize(320, 240)
        self._label.setStyleSheet("background-color: black;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._label)

        # frame güncellemek için timer
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS
        self._timer.timeout.connect(self._update_frame)

        # capture açmayı burada dene
        self._open_capture()

    # ---------- OpenCV VideoCapture açma ----------

    def _open_capture(self):
        """Önce GStreamer pipeline dene, olmazsa udp:// ile dene."""
        # 1) GStreamer pipeline
        gst_pipeline = (
            f'udpsrc port={self._port} '
            'caps=application/x-rtp,media=video,encoding-name=H264,payload=96 ! '
            'rtph264depay ! '
            'avdec_h264 ! '
            'videoconvert ! '
            'appsink'
        )

        cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
        if cap is not None and cap.isOpened():
            print("[VideoWidget] GStreamer pipeline ile açıldı.")
            self._cap = cap
            return

        # 2) FFMPEG backend ile basit UDP dene
        ff_uri = f"udp://0.0.0.0:{self._port}"
        cap = cv2.VideoCapture(ff_uri, cv2.CAP_FFMPEG)
        if cap is not None and cap.isOpened():
            print("[VideoWidget] FFMPEG udp:// ile açıldı.")
            self._cap = cap
            return

        print("[VideoWidget] Uyarı: VideoCapture açılamadı.")
        self._cap = None

    # ---------- Public API ----------

    def start(self):
        if self._cap is None:
            self._open_capture()
        if self._cap is not None and self._cap.isOpened():
            self._timer.start()
        else:
            print("[VideoWidget] start(): capture yok / açılmamış.")

    def stop(self):
        self._timer.stop()
        if self._cap is not None:
            try:
                self._cap.release()
            except Exception:
                pass
            self._cap = None

    # ---------- Frame güncelleme ----------

    def _update_frame(self):
        if self._cap is None:
            return
        ret, frame = self._cap.read()
        if not ret or frame is None:
            return

        # BGR -> RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qimg = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pix = QPixmap.fromImage(qimg)
        # Label boyutuna göre ölçekle, oranı koru
        pix = pix.scaled(
            self._label.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self._label.setPixmap(pix)

    def resizeEvent(self, e):
        # Pencere büyüyünce mevcut kareyi de yeniden ölçeklemek için
        if self._label.pixmap() is not None:
            pix = self._label.pixmap().scaled(
                self._label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self._label.setPixmap(pix)
        super().resizeEvent(e)

    def closeEvent(self, e):
        self.stop()
        super().closeEvent(e)
