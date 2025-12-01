import asyncio, math, time
from PyQt5.QtCore import QThread, pyqtSignal
from dataclasses import dataclass
from typing import Optional
import queue 

SERIAL_DEVICE = "/dev/tty.usbmodem1101"
BAUD = 57600
CONNECTION_STRING = "udp://0.0.0.0:14554"  # e.g. "udpin:0.0.0.0:14550"

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

    def stop(self):
        self._stop = True
    def start_mission(self):
        """
        MainWindow burayı çağıracak:
        ARM + TAKEOFF + araçta yüklü misyonu başlat.
        """
        self._cmd_queue.put(("start_mission", None))

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._amain())
        finally:
            loop.close()

    async def _amain(self):
        try:
            from mavsdk import System
        except Exception as e:
            self.error.emit(f"mavsdk import hatası: {e}")
            return

        try:
            drone = System()
            addr = CONNECTION_STRING if CONNECTION_STRING else f"serial:///{SERIAL_DEVICE}:{BAUD}"
            await drone.connect(system_address=addr)
            self.status.emit(f"Bağlantı: {addr}")
        except Exception as e:
            self.error.emit(f"Bağlantı hatası: {e}")
            return

        # bağlantı bekle
        async for cs in drone.core.connection_state():
            if cs.is_connected:
                self.status.emit("MAVLink bağlı")
                break

        # Telemetri akış hızlarını ayarla
        try:
            await drone.telemetry.set_rate_battery(15.0)        # 5 Hz batarya ⚡️
        except Exception as e:
            self.status.emit(f"Rate ayarlanamadı: {e}")

        # Telemetry state objesi
        state = Telemetry(heartbeat=True)

        # === Telemetri görevleri ===
        async def pos_task():
            async for p in drone.telemetry.position():
                state.iha_enlem  = p.latitude_deg
                state.iha_boylam = p.longitude_deg
                state.iha_irtifa = p.relative_altitude_m
                self.telemetry.emit(state)

        async def att_task():
            async for e in drone.telemetry.attitude_euler():
                state.iha_yatis   = e.roll_deg
                state.iha_dikilme = e.pitch_deg
                state.iha_yonelme = (e.yaw_deg % 360.0)
                self.telemetry.emit(state)

        async def gps_task():
            async for g in drone.telemetry.gps_info():
                state.baglanilan_gps_sayisi = g.num_satellites
                self.telemetry.emit(state)

        async def speed_task():
            async for v in drone.telemetry.velocity_ned():
                state.iha_hiz = (v.north_m_s**2 + v.east_m_s**2) ** 0.5
                self.telemetry.emit(state)
        async def command_task():
            """
            Kuyruktan komut al, gerekirse ARM + TAKEOFF + MISSION START yap.
            """
            while not self._stop:
                try:
                    cmd, payload = self._cmd_queue.get_nowait()
                except queue.Empty:
                    await asyncio.sleep(0.1)
                    continue

                if cmd == "start_mission":
                    try:
                        self.status.emit("Mission: ARM...")
                        await drone.action.arm()

                        self.status.emit("Mission: TAKEOFF...")
                        await drone.action.takeoff()

                        # basit bekleme; is_in_air kontrolü ile iyileştirilebilir
                        await asyncio.sleep(5)

                        self.status.emit("Mission: START...")
                        await drone.mission.start_mission()

                        self.status.emit("Mission: running")
                    except Exception as e:
                        self.error.emit(f"Mission hata: {e}")


        # 🔋 Tek döngüde iki bataryayı birlikte işle
        import math, time
        async def battery_task():
            last_emit = 0.0
            EMIT_PERIOD = 0.2  # 5 Hz arayüz güncelleme
            async for b in drone.telemetry.battery():
                v = getattr(b, "voltage_v", None)
                if v is None or not math.isfinite(v):
                    continue

                if b.id == 0:
                    state.iha_batarya0 = float(v)
                elif b.id == 1:
                    state.iha_batarya1 = float(v)
                else:
                    continue

                now = time.time()
                if now - last_emit >= EMIT_PERIOD:
                    self.telemetry.emit(state)
                    last_emit = now

        # === tüm görevleri aynı anda çalıştır ===
        await asyncio.gather(
            pos_task(),
            att_task(),
            gps_task(),
            speed_task(),
            battery_task(),
            command_task(),
        )
