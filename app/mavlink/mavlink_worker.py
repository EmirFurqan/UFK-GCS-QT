import time
import math
import queue
from PyQt5.QtCore import QThread, pyqtSignal
from dataclasses import dataclass
from typing import Optional

# Pymavlink imports
from pymavlink import mavutil

SERIAL_DEVICE = "/dev/tty.usbmodem1101"
BAUD = 57600
CONNECTION_STRING = "udp://0.0.0.0:14554"

@dataclass
class Telemetry:
    heartbeat: bool = False
    iha_enlem: Optional[float] = 40.7128
    iha_boylam: Optional[float] = 29.6652
    baglanilan_gps_sayisi: Optional[int] = None
    iha_irtifa: Optional[float] = None
    iha_dikilme: Optional[float] = None
    iha_yonelme: Optional[float] = None
    iha_yatis: Optional[float] = None
    iha_hiz: Optional[float] = None
    iha_batarya0: Optional[float] = None
    iha_batarya1: Optional[float] = None
    gps_saati: Optional[int] = None

class MavsdkWorker(QThread):
    telemetry = pyqtSignal(object)   # Telemetry instance
    status    = pyqtSignal(str)
    error     = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._stop = False
        self._cmd_queue = queue.Queue() 
        self.master = None

    def stop(self):
        self._stop = True
    
    def start_mission(self):
        """
        ARM + TAKEOFF + araçta yüklü misyonu başlat.
        """
        self._cmd_queue.put(("start_mission", None))

    def send_manual_control(self, x, y, z, r):
        """
        Control Surfaces testi için.
        x: pitch | y: roll | z: throttle | r: yaw
        Değerler -1000 ile 1000 arasında olması gerekebilir pymavlink manuel_control için
        fakat mavlink standardı -1000..1000.
        Gelen x,y,z,r -> -1.0 .. 1.0 (float) varsayıyoruz.
        """
        self._cmd_queue.put(("manual_control", (x, y, z, r)))

    def test_motor(self, motor_id: int):
        self._cmd_queue.put(("motor_test", motor_id))

    def run(self):
        # Bağlantı kur
        connection_str = CONNECTION_STRING if CONNECTION_STRING else f"{SERIAL_DEVICE}:{BAUD}"
        self.status.emit(f"Bağlanıyor: {connection_str}")
        
        try:
            # udpin: dinleyici mod (GCS), udpout: gönderici
            # Eğer GCS isek genelde udpin kullanırız ancak kullanıcı connection string verdi.
            # pymavlink string formatı: "udpin:0.0.0.0:14550" veya device
            # Mevcut CONNECTION_STRING "udp://..." formatında, pymavlink için "udpin:..." gerekebilir.
            # Ancak mavutil.mavlink_connection akıllıdır, deneyeceğiz.
            if "udp://" in connection_str:
                # Düzeltme: udp:// -> udpin:
                connection_str = connection_str.replace("udp://", "udpin:")
            
            self.master = mavutil.mavlink_connection(connection_str)
            self.status.emit(f"Bağlandı: {connection_str}")
        except Exception as e:
            self.error.emit(f"Bağlantı hatası: {e}")
            return

        # Heartbeat bekle
        self.status.emit("Heartbeat bekleniyor...")
        self.master.wait_heartbeat()
        self.status.emit("MAVLink Heartbeat alındı!")

        # Veri akışını başlat (gerekirse)
        # self.master.mav.request_data_stream_send(...)

        state = Telemetry(heartbeat=True)
        
        while not self._stop:
            # 1. Gelen mesajları oku
            msg = self.master.recv_match(blocking=False)
            if msg:
                self._handle_message(msg, state)
            
            # 2. Komut kuyruğunu işle
            try:
                while not self._cmd_queue.empty():
                    cmd, payload = self._cmd_queue.get_nowait()
                    self._process_command(cmd, payload)
            except queue.Empty:
                pass

            # 3. Telemetri yayınla (rate limiti yapılabilirdi ama şimdilik her döngüde değil)
            # Sürekli emit etmek arayüzü yorabilir, basit bir zamanlayıcı ekleyelim.
            # Veya her veri geldiğinde emit ediyoruz fakat _handle_message içinde yapıyoruz.
            
            time.sleep(0.01) # CPU'yu boğmamak için kısa uyku

    def _handle_message(self, msg, state):
        msg_type = msg.get_type()
        updated = False

        if msg_type == 'HEARTBEAT':
            state.heartbeat = True
            # updated = True # Heartbeat her geldiğinde arayüz yenilemeye gerek yok belki

        elif msg_type == 'GLOBAL_POSITION_INT':
            state.iha_enlem = msg.lat / 1e7
            state.iha_boylam = msg.lon / 1e7
            state.iha_irtifa = msg.relative_alt / 1000.0 # mm -> m
            updated = True

        elif msg_type == 'ATTITUDE':
            state.iha_yatis = math.degrees(msg.roll)
            state.iha_dikilme = math.degrees(msg.pitch)
            state.iha_yonelme = (math.degrees(msg.yaw) + 360) % 360
            updated = True
        
        elif msg_type == 'GPS_RAW_INT':
            state.baglanilan_gps_sayisi = msg.satellites_visible
            # gps fix type vs de bakılabilir
            updated = True

        elif msg_type == 'VFR_HUD':
            state.iha_hiz = msg.groundspeed
            updated = True

        elif msg_type == 'SYS_STATUS':
            # voltage_battery: mV
            # current_battery: cA (10mA)
            if msg.voltage_battery > 0:
                 state.iha_batarya0 = msg.voltage_battery / 1000.0
            updated = True
        
        elif msg_type == 'BATTERY_STATUS':
            # Hangi batarya olduğuna id'den bakılabilir
            # msg.id
            if msg.id == 0:
                if msg.voltages[0] < 65535:
                   volts = sum(v for v in msg.voltages if v < 65535) / 1000.0
                   state.iha_batarya0 = volts
            elif msg.id == 1:
                if msg.voltages[0] < 65535:
                   volts = sum(v for v in msg.voltages if v < 65535) / 1000.0
                   state.iha_batarya1 = volts

            updated = True

        if updated:
            self.telemetry.emit(state)

    def _process_command(self, cmd, payload):
        if not self.master:
            return

        try:
            if cmd == "start_mission":
                self.status.emit("Komut: ARM")
                # ARM komutu
                self.master.arducopter_arm()
                self.master.motors_armed_wait()
                
                self.status.emit("Komut: MISSION START")
                # Waypoint moduna geç
                self.master.set_mode_auto() 
                # Alternatif: MAV_CMD_MISSION_START
                # self.master.mav.command_long_send(
                #    self.master.target_system, self.master.target_component,
                #    mavutil.mavlink.MAV_CMD_MISSION_START,
                #    0, 0, 0, 0, 0, 0, 0, 0)
                
            elif cmd == "manual_control":
                # payload = (x, y, z, r) -> float -1..1
                x, y, z, r = payload
                # MANUAL_CONTROL mesajı: x, y, z, r binler cinsinden -1000..1000
                ix = int(x * 1000)
                iy = int(y * 1000)
                iz = int(z * 1000) # throttle 0..1000 genelde
                ir = int(r * 1000)
                
                # Z (throttle) genelde 0-1000 arasıdır, ama gelen veri -1..1 ise maplemek lazım
                # Eğer gelen z zaten 0..1 ise:
                iz = int(z * 1000)
                
                self.master.mav.manual_control_send(
                    self.master.target_system,
                    ix, iy, iz, ir,
                    0) # buttons

            elif cmd == "motor_test":
                motor_id = payload
                # MAV_CMD_DO_MOTOR_TEST
                # param1: motor instance (1-based map to 0-based?)
                # param2: throttle type (0=percent, 1=pwm, 2=pilot pass-through, 3=thrust_pwm)
                # param3: throttle (0-100%)
                # param4: timeout (seconds)
                # param5: motor count
                
                self.status.emit(f"Komut: Motor Test {motor_id}")
                self.master.mav.command_long_send(
                    self.master.target_system, self.master.target_component,
                    mavutil.mavlink.MAV_CMD_DO_MOTOR_TEST,
                    0,
                    motor_id, # Motor instance
                    0, # Throttle type: percent
                    15, # Throttle 15%
                    3, # Timeout 3s
                    1, # Motor count
                    0, 0) # Unused
                
        except Exception as e:
            self.error.emit(f"Komut hatası ({cmd}): {e}")
