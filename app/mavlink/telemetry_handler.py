import math
from dataclasses import dataclass
from typing import Optional

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

class TelemetryHandler:
    def handle_message(self, msg, state: Telemetry) -> bool:
        """
        Parses a Mavlink message and updates the Telemetry state.
        Returns True if the state was updated, False otherwise.
        """
        msg_type = msg.get_type()
        updated = False

        if msg_type == 'HEARTBEAT':
            state.heartbeat = True
            # updated = True 

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
            updated = True

        elif msg_type == 'VFR_HUD':
            state.iha_hiz = msg.groundspeed
            updated = True

        elif msg_type == 'SYS_STATUS':
            if msg.voltage_battery > 0:
                 state.iha_batarya0 = msg.voltage_battery / 1000.0
            updated = True
        
        elif msg_type == 'BATTERY_STATUS':
            if msg.id == 0:
                if msg.voltages[0] < 65535:
                   volts = sum(v for v in msg.voltages if v < 65535) / 1000.0
                   state.iha_batarya0 = volts
            elif msg.id == 1:
                if msg.voltages[0] < 65535:
                   volts = sum(v for v in msg.voltages if v < 65535) / 1000.0
                   state.iha_batarya1 = volts
            updated = True

        return updated
