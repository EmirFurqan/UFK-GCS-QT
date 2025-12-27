
import time
import json
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from api.client import CompetitionClient

class ServerWorker(QThread):
    # Signals
    login_result = pyqtSignal(bool, str)     # success, msg
    telemetry_result = pyqtSignal(bool, object) # success, data (list of competitors or error)
    data_fetched = pyqtSignal(str, object)   # type (qr/hss), data
    error = pyqtSignal(str)

    def __init__(self, base_url, username, password):
        super().__init__()
        self.client = CompetitionClient(base_url)
        self.username = username
        self.password = password
        
        self._running = False
        self._telemetry_data = None
        self._mutex = QMutex()
        self._start_telemetry_event = False

    def update_telemetry_data(self, data):
        """
        Main thread calls this to update data sent to server
        """
        self._mutex.lock()
        self._telemetry_data = data
        self._mutex.unlock()

    def stop(self):
        self._running = False
        self.wait()

    def run(self):
        self._running = True
        
        # 1. Automatic Login
        self.login_result.emit(False, "Giriş yapılıyor...") # Info
        success, resp = self.client.login(self.username, self.password)
        if not success:
            self.login_result.emit(False, f"Giriş Başarısız: {resp}")
            self._running = False
            return
        
        self.login_result.emit(True, "Giriş Başarılı")
        
        # 2. Fetch Initial Data
        # QR
        s, r = self.client.get_qr_coord()
        if s: self.data_fetched.emit("qr", r)
        
        # HSS
        s, r = self.client.get_hss_coords()
        if s: self.data_fetched.emit("hss", r)
        
        # 3. Telemetry Loop
        while self._running:
            start_time = time.time()
            
            # Get current data safely
            self._mutex.lock()
            current_data = self._telemetry_data
            self._mutex.unlock()
            
            if current_data:
                # Send
                s, r = self.client.send_telemetry(current_data)
                if s:
                    # r usually contains competitor info
                    self.telemetry_result.emit(True, r)
                else:
                    self.telemetry_result.emit(False, r)
            
            # Rate limit (e.g. 2Hz = 0.5s)
            elapsed = time.time() - start_time
            sleep_time = max(0.0, 0.5 - elapsed)
            time.sleep(sleep_time)

