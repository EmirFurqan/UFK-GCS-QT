from pymavlink import mavutil

class CommandHandler:
    def __init__(self, master):
        self.master = master

    def start_mission(self, status_signal=None):
        if not self.master: return

        if status_signal: status_signal.emit("Komut: ARM")
        self.master.arducopter_arm()
        self.master.motors_armed_wait()
        
        if status_signal: status_signal.emit("Komut: MISSION START")
        self.master.set_mode_auto() 

    def send_manual_control(self, x, y, z, r):
        if not self.master: return
        
        # payload = (x, y, z, r) -> float -1..1
        # MANUAL_CONTROL mesajı: x, y, z, r binler cinsinden -1000..1000
        ix = int(x * 1000)
        iy = int(y * 1000)
        iz = int(z * 1000) 
        ir = int(r * 1000)
        
        self.master.mav.manual_control_send(
            self.master.target_system,
            ix, iy, iz, ir,
            0) # buttons

    def test_motor(self, motor_id, status_signal=None):
        if not self.master: return

        if status_signal: status_signal.emit(f"Komut: Motor Test {motor_id}")
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
