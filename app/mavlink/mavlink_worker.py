import time
import queue
from PyQt5.QtCore import QThread, pyqtSignal
from pymavlink import mavutil

from mavlink.telemetry_handler import Telemetry, TelemetryHandler
from mavlink.command_handler import CommandHandler

SERIAL_DEVICE = "/dev/tty.usbmodem1101"
BAUD = 57600
CONNECTION_STRING = "udp://0.0.0.0:14554"

class MavlinkWorker(QThread):
    telemetry = pyqtSignal(object)   # Telemetry instance
    status    = pyqtSignal(str)
    error     = pyqtSignal(str)

    def __init__(self, connection_string=None):
        super().__init__()
        self._stop = False
        self._cmd_queue = queue.Queue() 
        self.master = None
        self.cmd_handler = None
        self.cmd_handler = None
        self.telem_handler = TelemetryHandler()
        self.telemetry_state = Telemetry()
        self.connection_string = connection_string

    def stop(self):
        self._stop = True
    
    def start_mission(self):
        self._cmd_queue.put(("start_mission", None))

    def send_manual_control(self, x, y, z, r):
        self._cmd_queue.put(("manual_control", (x, y, z, r)))

    def test_motor(self, motor_id: int):
        self._cmd_queue.put(("motor_test", motor_id))

    def run(self):
        connection_str = self.connection_string if self.connection_string else (CONNECTION_STRING if CONNECTION_STRING else f"{SERIAL_DEVICE}:{BAUD}")
        self.status.emit(f"Bağlanıyor: {connection_str}")
        
        try:
            if "udp://" in connection_str:
                connection_str = connection_str.replace("udp://", "udpin:")
            
            self.master = mavutil.mavlink_connection(connection_str)
            self.cmd_handler = CommandHandler(self.master)
            self.status.emit(f"Bağlandı: {connection_str}")
        except Exception as e:
            self.error.emit(f"Bağlantı hatası: {e}")
            return

        self.status.emit("Heartbeat bekleniyor...")
        self.master.wait_heartbeat()
        self.status.emit("MAVLink Heartbeat alındı!")

        self.telemetry_state.heartbeat = True
        
        while not self._stop:
            # 1. Gelen mesajları oku
            msg = self.master.recv_match(blocking=False)
            if msg:
                if self.telem_handler.handle_message(msg, self.telemetry_state):
                    self.telemetry.emit(self.telemetry_state)
            
            # 2. Komut kuyruğunu işle
            try:
                while not self._cmd_queue.empty():
                    cmd, payload = self._cmd_queue.get_nowait()
                    self._process_command(cmd, payload)
            except queue.Empty:
                pass

            time.sleep(0.01)

    def _process_command(self, cmd, payload):
        if not self.cmd_handler:
            return

        try:
            if cmd == "start_mission":
                self.cmd_handler.start_mission(self.status)
                
            elif cmd == "manual_control":
                x, y, z, r = payload
                self.cmd_handler.send_manual_control(x, y, z, r)

            elif cmd == "motor_test":
                motor_id = payload
                self.cmd_handler.test_motor(motor_id, self.status)
                
        except Exception as e:
            self.error.emit(f"Komut hatası ({cmd}): {e}")
