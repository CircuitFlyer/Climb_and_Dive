
#    **********************
#    *   Climb_and_Dive   *
#    **********************

#  An Open Source Electric Control Line Timer by CircuitFlyer (a.k.a. Paul Emmerson).  A CircuitPython program for a
#  microcontroller development board to create a timed PWM servo signal with accelerometer input, PID RPM control
#  and Bluetooth LE programming suitable to conduct a typical flight of an electric powered control line model aircraft.

# Timer Program Version: X.X.X
# Microcontroller Board: Seeed Studio Xiao BLE, https://wiki.seeedstudio.com/XIAO_BLE/
# Firmware: CircuitPython 7.3.3, https://circuitpython.org/board/Seeed_XIAO_nRF52840_Sense/
# Backpack Hardware Version: 3.2

import board
import digitalio
import neopixel
from time import monotonic, sleep
from touchio import TouchIn
from pwmio import PWMOut
from analogio import AnalogIn
from math import copysign, degrees, atan
from pulseio import PulseIn
from struct import pack, unpack
from microcontroller import nvm
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_debouncer import Debouncer
from ulab import numpy as np

# =============================================================================
# CONSTANTS & CONFIGURATION
# =============================================================================

# Magic 4-byte signature for NVM (Change this if you want to force a re-format of all parameters)
NVM_HEADER = b"CD01"

class Colors:
    """Standard RGB color definitions for the status LED."""
    BLANK   = (  0,   0,   0)
    RED     = (255,   0,   0)
    GREEN   = (  0, 255,   0)
    YELLOW  = (255, 255,   0)
    BLUE    = (  0,   0, 255)
    MAGENTA = (255,   0, 255)
    CYAN    = (  0, 255, 255)
    WHITE   = (255, 255, 255)

class Pins:
    """Hardware pin mapping for the Seeed Studio Xiao BLE."""
    RED_LED      = board.LED_RED
    GREEN_LED    = board.LED_GREEN
    BLUE_LED     = board.LED_BLUE
    NEOPIXEL     = board.D3
    TOUCH        = board.D7
    BUTTON       = board.D9
    ESC_PWM      = board.D6
    X_AXIS       = board.A0
    Y_AXIS       = board.A1
    Z_AXIS       = board.A2
    RPM_INPUT    = board.D10
    LANDING_GEAR = board.D8

class Parameter:
    def __init__(self, id_num, key, name, default, min_val, max_val, scale=1.0, fmt="{}", options=None):
        self.id = id_num
        self.key = key
        self.name = name
        self.default = default
        self.min_val = min_val
        self.max_val = max_val
        self.scale = scale
        self.fmt = fmt
        self.options = options

    def parse_input(self, val_str):
        try:
            val = int(val_str)
            if self.options and val not in self.options:
                return False, "Invalid option"
            
            scaled_val = val / self.scale
            if not (self.min_val <= scaled_val <= self.max_val):
                return False, "Out of range"
            return True, scaled_val
        except ValueError:
            return False, "Invalid number"

    def format_value(self, val):
        if self.options:
            return self.options.get(int(val), str(val))
        if self.scale != 1.0:
            return self.fmt.format(val)
        return self.fmt.format(int(val))

PARAMETERS = [
    Parameter(1, "delay_time", "Start Delay Time", 10, 0, 60, fmt="{} seconds"),
    Parameter(2, "flight_time", "Flight Time", 180, 10, 360, fmt="{} seconds"),
    Parameter(3, "rpm_setpoint", "RPM Setting", 10000, 4000, 15000, fmt="{} RPM"),
    Parameter(4, "climb_gain", "Climb Gain", 5, 0, 100),
    Parameter(5, "dive_gain", "Dive Gain", 5, 0, 100),
    Parameter(6, "number_of_poles", "Number of Motor Poles", 14, 2, 24),
    Parameter(7, "motor_acceleration_setting", "Motor Acceleration", 2, 1, 10),
    Parameter(8, "last_lap_duration", "Last Lap Time", 0, 0, 20),
    # 9 is Calibration/Mounting - handled specially
    Parameter(10, "overhead_boost_setting", "Overhead Boost", 5, 0, 100),
    Parameter(11, "estop", "E-Stop", 0, 0, 2, options={0: "OFF", 1: "TEST", 2: "ON"}),
    Parameter(12, "corner_boost_gain", "Corner Boost Gain", 0, 0, 100),
    Parameter(13, "gear_closed_us", "Gear Closed", 1200, 500, 2500, fmt="{} us"),
    Parameter(14, "gear_open_us", "Gear Open", 1800, 500, 2500, fmt="{} us"),
    # 15 is Test Gear - handled specially
    Parameter(17, "pid_kp", "PID Kp", 0.05, 0.0, 10.0, scale=10000.0, fmt="{:.4f}"),
    Parameter(18, "pid_ki", "PID Ki", 0.5, 0.0, 10.0, scale=10000.0, fmt="{:.4f}"),
    Parameter(19, "pid_kd", "PID Kd", 0.004, 0.0, 10.0, scale=10000.0, fmt="{:.4f}"),
    Parameter(20, "logging", "Logging", 0, 0, 1, options={0: "OFF", 1: "ON"}),
]

HIDDEN_PARAMETERS = [
    Parameter(101, "wing_axis", "Wing Axis", 3, -3, 3),
    Parameter(102, "fuse_axis", "Fuse Axis", -1, -3, 3),
    Parameter(103, "vert_axis_scale_factor", "Vert Axis Scale", 0.0, -100.0, 100.0, scale=1000.0),
    Parameter(104, "vert_axis_offset", "Vert Axis Offset", 0.0, -100.0, 100.0, scale=1000.0),
]

class Config:
    """Manages flight parameters, NVM persistence, and default settings."""
    def __init__(self):
        self.values = {}
        for p in PARAMETERS + HIDDEN_PARAMETERS:
            self.values[p.key] = p.default

        # System constants not stored in configurable NVM
        self.blip_duration       = 0.5
        self.blip_PWM            = 1150
        self.touch_pin_sensitivity = 100
        self.timer_name          = "Climb and Dive Timer"
        self.glide_boost         = 3
        self.corner_boost_duration = 0.6
        self.climb_threshold     = 12
        self.dive_threshold      = 12
        self.idle_us             = 950
        self.max_throttle_us     = 2000
        self.overhead_threshold  = 1.2
        self.gear_safety_buffer  = 10.0
        
        self.load()

    def __getattr__(self, name):
        if name == "values":
            raise AttributeError()
        if name in self.values:
            return self.values[name]
        raise AttributeError(f"'Config' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if hasattr(self, "values") and name in self.values:
            self.values[name] = value
        else:
            super().__setattr__(name, value)

    @property
    def vert_axis(self):
        return 6 - (abs(self.wing_axis) + abs(self.fuse_axis))

    def load(self):
        """Load configuration from NVM. If NVM is empty or wrong version, save defaults."""
        if nvm[0:4] != NVM_HEADER:
            self.save()
            return

        idx = 4
        while idx + 3 <= len(nvm):
            param_id = nvm[idx]
            if param_id == 0xFF:
                break
            val_int = unpack('<h', nvm[idx+1:idx+3])[0]
            
            for p in PARAMETERS + HIDDEN_PARAMETERS:
                if p.id == param_id:
                    self.values[p.key] = val_int / p.scale
                    break
            idx += 3

    def save(self):
        """Serialize and save current configuration to NVM using dynamic KV layout."""
        nvm[0:4] = NVM_HEADER
        idx = 4
        for p in PARAMETERS + HIDDEN_PARAMETERS:
            if idx + 3 > len(nvm):
                break
            nvm[idx] = p.id
            val_int = int(self.values[p.key] * p.scale)
            nvm[idx+1:idx+3] = pack('<h', val_int)
            idx += 3
        if idx < len(nvm):
            nvm[idx] = 0xFF

# =============================================================================
# HARDWARE ABSTRACTION LAYER
# =============================================================================

class Hardware:
    """Low-level hardware abstraction layer for sensors, LEDs, and PWM."""
    def __init__(self, config):
        self.cfg        = config
        self.red_led    = digitalio.DigitalInOut(Pins.RED_LED)
        self.red_led.direction = digitalio.Direction.OUTPUT
        
        self.green_led  = digitalio.DigitalInOut(Pins.GREEN_LED)
        self.green_led.direction = digitalio.Direction.OUTPUT
        
        self.blue_led   = digitalio.DigitalInOut(Pins.BLUE_LED)
        self.blue_led.direction = digitalio.Direction.OUTPUT
        
        self.pixels     = neopixel.NeoPixel(Pins.NEOPIXEL, 1, brightness=1.0, auto_write=True)
        self.touch_in   = TouchIn(Pins.TOUCH)
        self.touch_in.threshold = self.touch_in.raw_value + self.cfg.touch_pin_sensitivity
        self.touch      = Debouncer(self.touch_in, interval=0.02)
        
        self.button_in  = digitalio.DigitalInOut(Pins.BUTTON)
        self.button_in.switch_to_input(pull=digitalio.Pull.UP)
        self.button     = Debouncer(self.button_in, interval=0.02)
        
        self.esc_pwm    = PWMOut(Pins.ESC_PWM, frequency=50)
        self.gear_pwm   = PWMOut(Pins.LANDING_GEAR, frequency=50)
        self.axes       = [AnalogIn(Pins.X_AXIS), AnalogIn(Pins.Y_AXIS), AnalogIn(Pins.Z_AXIS)]
        
        # LED state for flashing
        self.flash_time = 0
        self.flash_show = True
        self.flash_count = 0

    def update_leds(self, now, color, interval, long_touch):
        """Update LED state for flashing or solid color display."""
        if not long_touch:
            self.flash_count = 0
            
        if interval == 0:
            self.set_leds(color)
            return self.flash_count

        if now < self.flash_time + interval:
            return self.flash_count

        # Toggle LED state
        self.flash_show = not self.flash_show
        self.flash_time = now

        if self.flash_show:
            self.set_leds(color)
            if long_touch:
                self.flash_count += 1
        else:
            self.set_leds(Colors.BLANK)

        return self.flash_count

    def set_leds(self, color):
        self.red_led.value = not color[0]
        self.green_led.value = not color[1]
        self.blue_led.value = not color[2]
        self.pixels[0] = color

    def get_g_force(self, axis_idx):
        axis = self.axes[axis_idx]
        val = axis.value
        g = ((val / (65535 / 2)) - 1.01) * 5.5
        if g > 20: return 20.0
        if g < -20: return -20.0
        if g != g: return 0.0 # NaN check
        return g

    def set_throttle(self, us):
        """Set the ESC throttle pulse width in microseconds."""
        period_us = 1_000_000 / 50
        self.esc_pwm.duty_cycle = int(us / (period_us / 65535))

    def get_throttle_us(self):
        period_us = 1_000_000 / 50
        return int(self.esc_pwm.duty_cycle * (period_us / 65535))

    def set_gear(self, us):
        """Set the landing gear servo pulse width in microseconds."""
        period_us = 1_000_000 / 50
        self.gear_pwm.duty_cycle = int(us / (period_us / 65535))

# =============================================================================
# CONTROL ALGORITHMS
# =============================================================================

class PIDController:
    """Standard PID controller for motor RPM stabilization."""
    def __init__(self, kp=0.05, ki=0.5, kd=0.004):
        self.kp, self.ki, self.kd  = kp, ki, kd
        self.kff = 0
        self.error_sum = 0
        self.last_input = 0
        self.last_time = -1
        self.filtered_derror = 0

    def update(self, setpoint, current_input, min_us, max_us, now):
        """Calculate new PID output based on error and time delta."""
        error = setpoint - current_input
        if self.last_time == -1: self.last_time = now
        dt = now - self.last_time
        if dt < 0.001: dt = 0.001
        self.error_sum = max(min(2000, self.error_sum + error * dt), -2000)
        if self.last_input == 0: self.last_input = current_input
        
        raw_derror = (self.last_input - current_input) / dt
        self.filtered_derror = (self.filtered_derror * 0.7) + (raw_derror * 0.3) 
        derror = max(min(2000, self.filtered_derror), -2000)

        output = int(min_us + (self.kp * error) + (self.ki * self.error_sum) + (self.kd * derror) + (self.kff * setpoint))
        self.last_input = current_input
        self.last_time = now
        return max(min(max_us, output), min_us)

    def reset(self):
        self.error_sum  = 0
        self.last_input = 0

class FlightController:
    """Mathematical engine for pitch detection, G-force analysis, and E-Stop."""
    def __init__(self, hardware, config):
        self.hw, self.cfg = hardware, config
        self.pid = PIDController(config.pid_kp, config.pid_ki, config.pid_kd)
        self.rpm_pulses = PulseIn(Pins.RPM_INPUT, maxlen=14, idle_state=False)
        self.last_rpm_time = 0
        self.rpm = 0

        # Filters computed at https://fiiir.com
        # Filter Type: Low Pass, Windowed Sinc FIR
        # Window type: Kaiser
        # Sampling rate: 150Hz
        # Cutoff freqency: 1.5Hz
        # Transition bandwidth: 1.7Hz
        # Stopband attenuation: 21dB
        # Weighting Function: N/A
        self.taps1 = np.array([
            0.004107233826136629, 0.004568299107366780, 0.005035127545733832, 0.005506781542188349,
            0.005982302099982009, 0.006460711293076683, 0.006941014801796215, 0.007422204508355161,
            0.007903261144690013, 0.008383156984833282, 0.008860858573909787, 0.009335329485698457,
            0.009805533100592132, 0.010270435395702739, 0.010729007738800197, 0.011180229677740685,
            0.011623091717033547, 0.012056598073216263, 0.012479769400753626, 0.012891645480250251,
            0.013291287860864680, 0.013677782448938516, 0.014050242035004473, 0.014407808751512962,
            0.014749656453816961, 0.015074993017178927, 0.015383062542810877, 0.015673147466228377,
            0.015944570561490463, 0.016196696835209488, 0.016428935304546512, 0.016640740653757920,
            0.016831614764226909, 0.017001108113297247, 0.017148821037626043, 0.017274404857185066,
            0.017377562856465571, 0.017458051119878183, 0.017515679218785489, 0.017550310748059635,
            0.017561863710518360, 0.017550310748059635, 0.017515679218785489, 0.017458051119878183,
            0.017377562856465571, 0.017274404857185066, 0.017148821037626043, 0.017001108113297247,
            0.016831614764226909, 0.016640740653757920, 0.016428935304546512, 0.016196696835209488,
            0.015944570561490463, 0.015673147466228377, 0.015383062542810877, 0.015074993017178927,
            0.014749656453816961, 0.014407808751512962, 0.014050242035004473, 0.013677782448938516,
            0.013291287860864680, 0.012891645480250251, 0.012479769400753626, 0.012056598073216263,
            0.011623091717033547, 0.011180229677740685, 0.010729007738800197, 0.010270435395702739,
            0.009805533100592132, 0.009335329485698457, 0.008860858573909787, 0.008383156984833282,
            0.007903261144690013, 0.007422204508355161, 0.006941014801796215, 0.006460711293076683,
            0.005982302099982009, 0.005506781542188349, 0.005035127545733832, 0.004568299107366780,
            0.004107233826136629
        ])
        self.wing_data      = np.zeros(len(self.taps1) + 1)
        self.vert_history   = np.zeros(20)
        self.old_wing_accel = 0
        self.old_vert_accel = 0
        self.level_gforce   = 0
        self.wing_buffer    = []
        self.corner         = False
        self.corner_timer   = 0
        self.m_counter      = 0

        # E-Stop variables
        self.estop_submode = "normal"
        self.pull_count = 0
        self.pull_timer = 0
        self.estop_data = np.zeros(7)
        self.estop_idx = 0
        self.estop_reference = np.array([-0.88, -0.97, -0.45, 0.39, 0.93, 0.79, 0.18])
        self.estop_shutdown       = False
        self.estop_shutdown_timer = 0
        self.corner_boost         = 0
        self.boost                = 0
        self.brake                = 0
        self.last_boost_time      = 1e9

    def get_rpm(self, now):
        """Measure current motor RPM from pulse input."""
        if (now - self.last_rpm_time) < 0.02:
            return None

        self.rpm_pulses.pause()
        total, valid = 0, 0
        if len(self.rpm_pulses) >= 6:
            for i in range(len(self.rpm_pulses)):
                p = self.rpm_pulses[i]
                if p >= 40: 
                    total += p
                    valid += 1
            try:                 
                self.rpm = (int(((1_000_000 / total) * 60) / (self.cfg.number_of_poles / valid) / 10)) * 10
            except ZeroDivisionError: 
                self.rpm = 0
            if self.rpm > 60000: 
                self.rpm = 0
        else: 
            self.rpm = 0
        self.rpm_pulses.clear()
        self.last_rpm_time = now
        self.rpm_pulses.resume()
        return self.rpm        

    def calculate_active_boost(self, now, flight_start_time, data_collection=False):
        """Calculate RPM boost based on pitch, G-force, and maneuvers."""
        # 1. Calculate Accelerations
        wing_accel = self.hw.get_g_force(abs(self.cfg.wing_axis) - 1) * copysign(1, self.cfg.wing_axis) * -1
        wing_accel_avg = (self.old_wing_accel * 0.85) + (0.15 * wing_accel)
        self.old_wing_accel = wing_accel_avg

        vert_accel = (self.hw.get_g_force(self.cfg.vert_axis - 1) * self.cfg.vert_axis_scale_factor) - self.cfg.vert_axis_offset
        vert_accel_avg = (self.old_vert_accel * 0.9) + (0.1 * vert_accel)
        self.old_vert_accel = vert_accel_avg

        # 2. Update History and Filter
        self.vert_history = np.roll(self.vert_history, -1)
        self.vert_history[-1] = vert_accel_avg
        vert_rate = self.vert_history[-1] - self.vert_history[0]

        self.wing_data = np.roll(self.wing_data, -1)
        self.wing_data[-1] = wing_accel_avg
        diff = np.diff(self.wing_data, n = 1)
        wing_filtered = np.sum(diff * self.taps1)

        dt = now - self.last_boost_time
        if dt <= 0: dt = 1/150.0
        self.last_boost_time = now

        slope = degrees(atan(wing_filtered / dt))
        slope = min(40, max(-40, slope))

        if slope > self.cfg.climb_threshold:
            self.boost = slope - (self.cfg.climb_threshold / 2)
        elif slope < -self.cfg.dive_threshold:
            self.brake = slope + (self.cfg.dive_threshold / 2)
        else:
            self.boost = 0
            self.brake = 0

        # 3. Data Collection for Level G-Force
        if data_collection and (self.m_counter % 20 == 0):
            self.wing_buffer.append(wing_accel_avg)
            self.level_gforce = np.mean(np.array(self.wing_buffer))

        # 4. Corrected Wing Accel and Boosts
        wing_accel_corrected = wing_accel_avg - self.level_gforce
        overhead_boost = max(0, wing_accel_corrected - self.cfg.overhead_threshold) * self.cfg.overhead_boost_setting * 40

        # Corner Detection
        is_cornering = (vert_accel_avg > 3 and vert_rate > 1) or (vert_accel_avg < -3 and vert_rate < -1)
        if not self.corner and wing_accel_corrected < 0.5 and is_cornering:
            self.corner, self.corner_timer = True, now
            self.corner_boost = 40 * self.cfg.corner_boost_gain

        if (now - self.corner_timer) > self.cfg.corner_boost_duration:
            self.corner, self.corner_boost = False, 0

        # 5. E-Stop Check
        estop_action = self._check_estop(now, flight_start_time, wing_accel_corrected)

        self.m_counter = (self.m_counter + 1) % 60
        boost_val = int((self.boost * self.cfg.climb_gain) + (self.brake * self.cfg.dive_gain))
        return boost_val, overhead_boost, self.corner_boost, estop_action

    def _check_estop(self, now, flight_start_time, wing_accel_corrected):
        """Internal method to handle E-Stop logic."""
        if self.cfg.estop == 0 or (self.m_counter % 20 != 0):
            return None

        clock = now - flight_start_time
        
        if self.estop_submode == "normal":
            if (clock - self.pull_timer) > 0.6:
                self.pull_count = 0
            if wing_accel_corrected <= -0.5:
                self.estop_submode = "collect_data"
            return None

        if self.estop_submode == "collect_data":
            self.estop_data[self.estop_idx] = wing_accel_corrected
            self.estop_idx += 1
            if self.estop_idx == 7:
                self.estop_submode = "analyse_data"
                self.estop_idx = 0
            return None

        if self.estop_submode == "analyse_data":
            mean = np.mean(self.estop_data)
            data_centered = self.estop_data - mean

            dot_ref = np.dot(self.estop_reference, self.estop_reference)
            dot_data = np.dot(data_centered, data_centered)
            correlation = np.sqrt(max(0, dot_ref * dot_data))
            peak_value = np.max(data_centered)
            
            if correlation > 2.8 and peak_value > 0.7:
                self.pull_count += 1
                self.pull_timer = clock
            else:
                self.pull_count = 0
            self.estop_submode = "normal"

        if self.estop_shutdown and (clock - self.estop_shutdown_timer) >= 1.5:
            self.estop_shutdown = False
            return "reset_rpm"
        
        if self.pull_count >= 3:
            if self.cfg.estop == 1: # TEST mode
                self.estop_shutdown = True
                self.pull_count = 0
                self.estop_shutdown_timer = clock
                return "boost_rpm"
            if self.cfg.estop == 2: # ON mode
                return "shutdown"
        
        return None

# =============================================================================
# COMMUNICATION INTERFACE
# =============================================================================

class BLEInterface:
    """Handles Bluetooth Low Energy communication and the UART menu system."""
    def __init__(self, config):
        self.cfg = config
        self.ble = BLERadio()
        self.ble.name = self.cfg.timer_name
        self.uart = UARTService()
        self.advertisement = ProvideServicesAdvertisement(self.uart)
        self.ble.stop_advertising()
        
        self.prompts = {
            "wing_1": "\nStep 1: Record wing to timer mounting orientation.  Point outboard wing down.\n",
            "wing_2": "\nEnter W when ready ",
            "fuse_1": "\nStep 2: Record fuselage to timer mounting orientation.  Point the nose of the fuselage down.\n",
            "fuse_2": "\nEnter F when ready ",
            "cal_u_1": "\nStep 3: Calibrate upright. Orient the airframe in an upright level flying position.\n",
            "cal_u_2": "\nEnter U when ready ",
            "cal_i_1": "\nStep 4: Calibrate inverted. Orient the airframe in an inverted level flying position.\n",
            "cal_i_2": "\nEnter I when ready ",
            "main_menu_x": "\nEnter X to return to main menu\n",
            "invalid": "\nInvalid Input. Or X to return to Main Menu\n",
            "select_item": "\nEnter selection #:\n",
            "enter_value": " \nEnter new setting:\n",
            "saved": " \nParameters saved, OK to disconnect\n\n"
        }

    def send_prompt(self, key):
        self.uart.write(self.prompts[key].encode())

    def update(self):
        if not self.ble.connected and not self.ble.advertising:
            self.ble.start_advertising(self.advertisement)
        return self.ble.connected

    def send_menu(self):
        axis_names = {1: '+X', -1: '-X', 2: '+Y', -2: '-Y', 3: '+Z', -3: '-Z'}
        menu = ["**** Climb_and_Dive Timer Settings ****\n\n"]
        
        idx = 1
        for p in PARAMETERS:
            if idx == 9:
                menu.append(" 9) Mounting Position ... {}, {}\n    & Calibration ....... {:.2f}, {:.2f}\n".format(
                    axis_names.get(self.cfg.wing_axis, "??"), axis_names.get(self.cfg.fuse_axis, "??"),
                    self.cfg.vert_axis_scale_factor, self.cfg.vert_axis_offset))
                idx += 1
            if idx == 16:
                menu.append("16) Test Gear (Toggle)\n")
                idx += 1
                
            val = getattr(self.cfg, p.key)
            formatted_val = p.format_value(val)
            name_padded = (p.name + " ").ljust(22, ".")
            menu.append("{:2d}) {} {} \n".format(idx, name_padded, formatted_val))
            idx += 1
            
        menu.append(" 0) Save and EXIT\n")
        menu.append(self.prompts["select_item"])
        
        for line in menu:
            self.print(line)

    def handle_input(self):
        if self.uart.in_waiting:
            data = self.uart.read(self.uart.in_waiting).decode().strip()
            return data
        return None

    def print(self, *args):
        try:
            string = " ".join(map(str, args)) + "\n"
            self.uart.write(string.encode())
        except Exception:
            pass

# =============================================================================
# DATA LOGGING
# =============================================================================

from struct import calcsize, pack_into

class Logger:
    """Handles black-box logging of flight telemetry."""
    def __init__(self, ble):
        self.ble = ble
        self.file = None
        self.enabled = False
        
        self.filename = "/flight_log.bin" 
        
        self.fmt = "<fffffff"
        self.record_size = calcsize(self.fmt)
        
        self.max_buffer_records = 51
        self.buffer = bytearray(self.record_size * self.max_buffer_records)
        self.offset = 0

    def start(self):
        """Start logging session."""
        
        try:
            self.file = open(self.filename, "ab")
            self.enabled = True
            # Write a divider record (NaNs) to separate flights
            nan_record = pack(self.fmt, float('nan'), float('nan'), float('nan'), float('nan'), float('nan'), float('nan'), float('nan'))
            self.file.write(nan_record)
        except OSError as e:
            self.enabled = False
            self.ble.print("Log file open failed: " + str(e))

    def log(self, timestamp, rpm, wing_accel, vert_accel, climb_boost, overhead_boost, corner_boost):
        """Write a single telemetry record to buffer."""
        if not self.enabled: 
            return

        try:
            pack_into(
                self.fmt, 
                self.buffer, 
                self.offset,
                timestamp or 0.0, 
                float(rpm or 0), 
                wing_accel or 0.0, 
                vert_accel or 0.0, 
                float(climb_boost or 0),
                float(overhead_boost or 0),
                float(corner_boost or 0)
            )
            
            self.offset += self.record_size

            if self.offset >= len(self.buffer):
                self.flush()
        except Exception as e:
            self.ble.print("Log write failed: " + str(e))

    def flush(self):
        """Write buffer to disk."""
        if self.enabled and self.file and self.offset > 0:
            try:
                self.file.write(memoryview(self.buffer)[:self.offset])
                self.offset = 0
            except OSError:
                self.enabled = False

    def stop(self):
        """Stop logging and close file."""
        if self.file:
            self.flush()
            try:
                self.file.close()
            except OSError:
                pass
            self.file = None
            self.enabled = False

# =============================================================================
# MAIN APPLICATION LOGIC
# =============================================================================

class TimerApp:
    """Main state machine orchestrating the flight sequence and user interaction."""
    def __init__(self):
        self.cfg            = Config()
        self.hw             = Hardware(self.cfg)
        self.fc             = FlightController(self.hw, self.cfg)
        self.ble            = BLEInterface(self.cfg)
        self.logger         = Logger(self.ble)
        
        self.mode           = "standby"
        self.last_time      = 0
        self.touch_time     = 0
        self.counter        = 0
        self.long_touch     = False
        self.previous_touch = False
        self.motor_status   = None
        self.sample_count   = 0
        self.old_tach       = 0
        self.fault_code     = 0
        self.fault_color    = None
        self.submode        = None
        self.flash_timer    = 0
        self.flash_state    = 0
        self.ble_choice     = None
        self.end_of_long_touch = False
        self.ble_enable     = True
        
        self.state_map = {
            "standby": self._state_standby,
            "start_blip": self._state_start_blip,
            "delay": self._state_delay,
            "take-off": self._state_take_off,
            "flight": self._state_flight,
            "landing": self._state_landing,
            "flight_complete": self._state_flight_complete,
            "ble_programming": self._state_ble_programming,
            "manual_programming": self._state_manual_programming,
            "motor_tuning": self._state_motor_tuning
        }
    
    def _update_inputs(self):
        now = monotonic()
        self.hw.touch.update(); self.hw.button.update()
        return now, (self.hw.touch.value or not self.hw.button.value)

    def _process_touch(self, now, touching):
        self.end_of_long_touch = False
        
        if touching and not self.previous_touch:
            self.touch_time    = now
            self.counter      += 1
            self.previous_touch = True
            
        if self.previous_touch and not touching:
            self.previous_touch = False
            if self.long_touch:
                self.counter    = 0
                self.long_touch = False
                self.end_of_long_touch = True
        
        main_count = 0
        if now - self.touch_time > 1 and not touching and not self.long_touch and not self.end_of_long_touch:
            main_count, self.counter = self.counter, 0
        if now - self.touch_time > 3 and touching:
            self.long_touch = True
        return main_count

    def handle_ble_choice(self, choice, data):
        """Handle BLE menu choices in a non-blocking way."""
        if choice == 16:
            # Toggle gear for testing
            period_us = 20000
            current_us = int(self.hw.gear_pwm.duty_cycle * (period_us / 65535))
            target_gear = self.cfg.gear_open_us if abs(current_us - self.cfg.gear_closed_us) < 50 else self.cfg.gear_closed_us
            self.hw.set_gear(target_gear)
            return True

        # Find the parameter mapped to this choice
        target_param = None
        idx = 1
        for p in PARAMETERS:
            if idx == 9: idx += 1    # Skip calibration
            if idx == 16: idx += 1   # Skip gear test
            if idx == choice:
                target_param = p
                break
            idx += 1

        if not target_param:
            return False

        if data is None:
            # Ask for new input
            if target_param.options:
                opts = ", ".join(f"{k}={v}" for k, v in target_param.options.items())
                self.ble.print(f"\n{opts}\n")
            self.ble.send_prompt("enter_value")
            return False

        if data.upper() == 'X':
            return True

        success, result = target_param.parse_input(data)
        if success:
            setattr(self.cfg, target_param.key, result)
            return True
        else:
            self.ble.print(f"\nError: {result}")
            self.ble.send_prompt("enter_value")
            return False

    def _wait_for_ble_input(self, prompt_idx_1, prompt_idx_2, target_char):
        """Helper to wait for a specific BLE input character."""
        self.ble.send_prompt(prompt_idx_1)
        self.ble.send_prompt(prompt_idx_2)
        while self.ble.ble.connected:
            data = self.ble.handle_input()
            if not data:
                sleep(0.1)
                continue
            char = data.upper()
            if char == 'X': return 'X'
            if char == target_char: return char
            sleep(0.1)
        return None

    def run_calibration(self):
        # Step 1: Wing axis
        if self._wait_for_ble_input("wing_1", "wing_2", 'W') == 'X': return
        temp_wing = self.get_axis_orientation()
        
        # Step 2: Fuse axis
        if self._wait_for_ble_input("fuse_1", "fuse_2", 'F') == 'X': return
        self.cfg.fuse_axis = self.get_axis_orientation()
        self.cfg.wing_axis = temp_wing
            
        # Step 3: Calibrate Upright
        if self._wait_for_ble_input("cal_u_1", "cal_u_2", 'U') == 'X': return
        p1 = self.read_axis_oversampled(self.cfg.vert_axis - 1)
            
        # Step 4: Calibrate Inverted
        if self._wait_for_ble_input("cal_i_1", "cal_i_2", 'I') == 'X': return
        p2 = self.read_axis_oversampled(self.cfg.vert_axis - 1)
        
        raw_range = abs(p1 - p2)
        if raw_range > 0:
            self.cfg.vert_axis_scale_factor = 2.0 / raw_range
            self.cfg.vert_axis_offset = ((p1 + p2) / 2.0) * self.cfg.vert_axis_scale_factor
            
        self.cfg.save()
        self.ble.send_prompt("saved")

    def get_axis_orientation(self):
        for i in range(3):
            val = self.hw.get_g_force(i)
            if abs(val) > 0.8: return int(copysign(i + 1, val))
        return 1

    def read_axis_oversampled(self, axis_idx):
        total = 0
        for _ in range(100): total += self.hw.get_g_force(axis_idx)
        return total / 100.0

    def _state_manual_programming(self, now, touching, main_count):
        if not self.submode: self.submode = "program_delay"
        if self.end_of_long_touch:
            if self.submode == "program_delay": 
                self.cfg.delay_time = self.hw.flash_count
                self.cfg.save()
            elif self.submode == "program_flight": 
                self.cfg.flight_time = self.hw.flash_count * 10
                self.cfg.save()
        
        if self.submode == "program_delay":
            self.hw.update_leds(now, Colors.YELLOW, 0.4 if self.long_touch else 0, self.long_touch)
            if main_count == 2: self.submode = "program_flight"
            elif main_count == 4: self.mode, self.submode = "standby", None
        elif self.submode == "program_flight":
            self.hw.update_leds(now, Colors.CYAN, 0.4 if self.long_touch else 0, self.long_touch)
            if main_count == 1: self.submode = "program_delay"
            if main_count == 3: self.submode = "program_rpm"
            elif main_count == 4: self.mode, self.submode = "standby", None
        elif self.submode == "program_rpm":
            self.hw.update_leds(now, Colors.MAGENTA, 0.05 if touching and not self.long_touch else 0, False)
            if self.long_touch: 
                self.sample_count, self.old_tach = 0, 0
                self.mode, self.long_touch = "motor_tuning", False
            if main_count == 2: self.submode = "program_flight"
            elif main_count == 4: self.mode, self.submode = "standby", None

    def _state_motor_tuning(self, now, touching, main_count):
        self.hw.update_leds(now, Colors.MAGENTA, 0.2, True)
        if self.motor_status is None:
            self.spool_up(now, self.last_time)
        else:
            rpm = self.fc.get_rpm(now)
            if rpm is not None:
                if rpm < 0.75 * self.cfg.rpm_setpoint: 
                    self.hw.set_throttle(self.cfg.idle_us)
                    self.mode, self.motor_status = "standby", None
                    return
                throttle = self.fc.pid.update(self.cfg.rpm_setpoint, rpm, self.cfg.idle_us, self.cfg.max_throttle_us, now)
                self.hw.set_throttle(throttle)
            
            if main_count == 1: self.cfg.rpm_setpoint = min(15000, self.cfg.rpm_setpoint + 50)
            elif main_count == 2: self.cfg.rpm_setpoint = max(4000, self.cfg.rpm_setpoint - 50)
            elif main_count == 3: 
                self.cfg.save()
                self.hw.set_throttle(self.cfg.idle_us)
                self.mode, self.motor_status = "standby", None

    def spool_up(self, now, start_time):
        tach = self.fc.get_rpm(now)
        if tach is None:
            self._check_spool_up_timeout(now, start_time, 0)
            return

        if tach >= (self.cfg.rpm_setpoint - 200):
            self.motor_status = "run"
            self.fc.pid.kff = (self.hw.get_throttle_us() - self.cfg.idle_us) / self.cfg.rpm_setpoint
            self.fc.pid.reset()
            return

        # Increase throttle
        new_throttle = self.hw.get_throttle_us() + (self.cfg.motor_acceleration_setting * 2)
        self.hw.set_throttle(min(self.cfg.max_throttle_us, new_throttle))
        
        if tach > 0:
            self.sample_count += 1
            
        # Check for stall/fault
        if self.sample_count >= 8 and tach < self.old_tach - 1000 and self.old_tach > 2000:
            self.mode, self.fault_code = "flight_complete", 4
            
        self.old_tach = max(self.old_tach, tach)
        self._check_spool_up_timeout(now, start_time, tach)

    def _check_spool_up_timeout(self, now, start_time, tach):
        """Helper to check for spool-up timeouts."""
        if tach == 0 and now - start_time > (1.6 + (4.0 / self.cfg.motor_acceleration_setting)):
            self.mode, self.fault_code = "flight_complete", 2
        if now - start_time > (5.0 + (20.0 / self.cfg.motor_acceleration_setting)):
            self.mode, self.fault_code = "flight_complete", 3

    def run(self):
        """Main application entry point and state machine loop."""
        self._check_initial_safety()
        self.hw.set_throttle(self.cfg.idle_us)
        self.hw.set_gear(self.cfg.gear_open_us)

        loop_period = 1 / 150.0
        loop_target_time = monotonic()

        while True:
            try:
                now, touching = self._update_inputs()
                main_count = self._process_touch(now, touching)
                handler = self.state_map.get(self.mode)
                if handler:
                    handler(now, touching, main_count)
            except ZeroDivisionError:
                # Division by zero in PID or slope calculation
                self.fault_code = 5
                self.fault_color = Colors.CYAN
                self.mode = "flight_complete"
            except IndexError:
                # Array access out of bounds (buffer issue)
                self.fault_code = 5
                self.fault_color = Colors.MAGENTA
                self.mode = "flight_complete"
            except MemoryError:
                # Out of RAM during flight
                self.fault_code = 5
                self.fault_color = Colors.BLUE
                self.mode = "flight_complete"
            except Exception as e:
                # Unknown error - print full traceback for debugging
                import traceback
                try:
                    error_msg = "".join(traceback.format_exception(e))
                except Exception:
                    error_msg = f"Error: {e}"
                self.ble.print(error_msg)
                self.fault_code = 5
                self.fault_color = Colors.RED
                self.mode = "flight_complete"
            
            if self.mode == "flight_complete" and self.fault_color:
                self.hw.set_throttle(self.cfg.idle_us)
                
            loop_target_time += loop_period
            time_remaining = loop_target_time - monotonic()
            
            if time_remaining > 0:
                sleep(time_remaining)

    def _check_initial_safety(self):
        """Check for safety conditions at startup."""
        if self.hw.touch_in.raw_value > 500 or not self.hw.button_in.value:
            self.hw.set_throttle(self.cfg.idle_us)
            self.hw.set_gear(self.cfg.gear_open_us)
            self.hw.set_leds(Colors.WHITE)
            while self.hw.touch_in.raw_value > 500 or not self.hw.button_in.value:
                sleep(0.05)

    def _state_standby(self, now, touching, main_count):
        self.hw.update_leds(now, Colors.GREEN, 0, False)
        if self.long_touch: 
            self.mode, self.last_time = "start_blip", now
        elif main_count == 5: 
            self.mode, self.submode = "manual_programming", None
        elif self.ble.update() and self.ble_enable: 
            self.mode = "ble_programming"

    def _state_start_blip(self, now, touching, main_count):
        self.hw.update_leds(now, Colors.RED, 0, False)
        self.hw.set_throttle(self.cfg.blip_PWM)
        if not self.long_touch and touching:
            self.hw.set_throttle(self.cfg.idle_us)
            self.mode = "standby"
        elif now - self.last_time > self.cfg.blip_duration:
            self.hw.set_throttle(self.cfg.idle_us)
            self.mode, self.last_time = "delay", now

    def _state_delay(self, now, touching, main_count):
        color = Colors.WHITE if now - self.last_time + 5 > self.cfg.delay_time else Colors.BLUE
        interval = 0.05 if color == Colors.WHITE else 0.5
        self.hw.update_leds(now, color, interval, False)

        if now - self.last_time > self.cfg.delay_time:
            self.sample_count, self.old_tach = 0, 0
            self.mode, self.last_time = "take-off", now
            self.hw.set_throttle(self.cfg.idle_us)

    def _state_take_off(self, now, touching, main_count):
        self.hw.update_leds(now, Colors.RED, 1, False)
        if touching:
            self.mode = "flight_complete"
            return
        self.spool_up(now, self.last_time)
        if self.motor_status == "run":
            if self.cfg.logging:
                self.logger.start()
            self.mode, self.last_time, self.motor_status = "flight", now, None

    def _state_flight(self, now, touching, main_count):
        if touching:
            self.mode = "flight_complete"
            return
        
        flight_elapsed = now - self.last_time
        self._update_gear_state(flight_elapsed)

        climb_boost, overhead_boost, corner_boost, estop_action = self.fc.calculate_active_boost(now, self.last_time, data_collection=(5 < flight_elapsed < 10))
        boost = climb_boost + overhead_boost + corner_boost if now - self.last_time > 5 else 0
        if self._handle_estop_action(estop_action): return

        self._update_flight_rpm(now, boost)
        
        self.logger.log(
            timestamp=now,
            rpm=self.fc.rpm - self.cfg.rpm_setpoint,
            wing_accel=self.fc.wing_data[-1],
            vert_accel=self.fc.vert_history[-1],
            climb_boost=climb_boost,
            overhead_boost=overhead_boost,
            corner_boost=corner_boost
        )
        if flight_elapsed <= 10:
            self.hw.update_leds(now, Colors.RED, 1, False)
        elif (self.cfg.flight_time - flight_elapsed) <= 1:
            self.mode, self.last_time = "landing", now
            self.hw.set_gear(self.cfg.gear_open_us)
        elif (self.cfg.flight_time - flight_elapsed) <= 11:
            self.hw.update_leds(now, Colors.WHITE, 0.05, False)
        else:
            self.hw.update_leds(now, Colors.BLANK, 0, False)

    def _update_gear_state(self, flight_elapsed):
        if flight_elapsed < self.cfg.gear_safety_buffer or flight_elapsed > self.cfg.flight_time - self.cfg.gear_safety_buffer:
            self.hw.set_gear(self.cfg.gear_open_us)
        else:
            self.hw.set_gear(self.cfg.gear_closed_us)

    def _handle_estop_action(self, estop_action):
        if estop_action == "shutdown":
            self.mode = "flight_complete"
            return True
        if estop_action == "boost_rpm":
            self.cfg.rpm_setpoint += 800
        elif estop_action == "reset_rpm":
            self.cfg.rpm_setpoint -= 800
        return False

    def _update_flight_rpm(self, now, boost):
        rpm_target = self.cfg.rpm_setpoint + boost
        rpm = self.fc.get_rpm(now)
        if rpm is not None:
            if rpm_target > 0 and rpm < 0.75 * rpm_target:
                self.mode, self.fault_code = "flight_complete", 1
            else:
                if abs(rpm - rpm_target) < 100 and rpm_target == self.cfg.rpm_setpoint:
                    active_throttle = self.hw.get_throttle_us() - self.cfg.idle_us
                    self.fc.pid.kff = (self.fc.pid.kff * 0.999) + (active_throttle / rpm) * 0.001
                throttle = self.fc.pid.update(rpm_target, rpm, self.cfg.idle_us, self.cfg.max_throttle_us, now)
                self.hw.set_throttle(throttle)

    def _state_landing(self, now, touching, main_count):
        self.hw.update_leds(now, Colors.RED, 0.25, False)
        if touching: 
            self.mode = "flight_complete"
            return
            
        rpm_target = self.cfg.rpm_setpoint + (1000 if now - self.last_time <= self.cfg.glide_boost else 0)
        rpm = self.fc.get_rpm(now)
        if rpm is not None:
            throttle = self.fc.pid.update(rpm_target, rpm, self.cfg.idle_us, self.cfg.max_throttle_us, now)
            self.hw.set_throttle(throttle)
            
            # Log telemetry
            self.logger.log(
                timestamp=now,
                rpm=rpm - self.cfg.rpm_setpoint,
                wing_accel=self.fc.wing_data[-1],
                vert_accel=self.fc.vert_history[-1],                
                climb_boost=(1000 if now - self.last_time <= self.cfg.glide_boost else 0),
                overhead_boost=0,
                corner_boost=0
            )
            
        if now - self.last_time > self.cfg.glide_boost + self.cfg.last_lap_duration:
            self.mode = "flight_complete"

    def _state_flight_complete(self, now, touching, main_count):
        self.logger.stop()
        self.ble_enable = True
        self.hw.set_throttle(self.cfg.idle_us)
        self.hw.set_gear(self.cfg.gear_open_us)
        
        # Exit condition
        if main_count == 1:
            self.hw.update_leds(now, Colors.BLANK, 0, False)
            self.mode, self.fault_code, self.flash_state, self.fault_color = "standby", 0, 0, None
            return

        if self.fault_code == 0:
            self.hw.update_leds(now, Colors.BLANK, 0, False)
            return

        # Determine blink color (Red for standard faults, specific color for System Error 5)
        blink_color = self.fault_color if self.fault_color is not None else Colors.RED
        limit = self.fault_code * 2

        # Pause phase
        if self.flash_state > limit:
            if now - self.flash_timer > 3.0:
                self.flash_state = 0
                self.flash_timer = now
            else:
                self.hw.set_leds(Colors.BLANK)
            return

        # Blinking phase
        duration = 0.3 if self.flash_state % 2 == 1 else 0.5
        
        if now - self.flash_timer > duration:
            self.flash_timer = now
            self.flash_state += 1
            
            if self.flash_state > limit:
                self.hw.set_leds(Colors.BLANK)
            else:
                is_on = (self.flash_state % 2 == 1)
                self.hw.set_leds(blink_color if is_on else Colors.BLANK)

    def _state_ble_programming(self, now, touching, main_count):
        if not self.ble.ble.connected:
            self.mode, self.submode, self.ble_choice = "standby", None, None
            return
            
        self.hw.update_leds(now, Colors.BLUE, 0, False)
        
        if not self.submode:
            if self.ble.uart.in_waiting:
                self.ble.uart.reset_input_buffer()
                self.ble.send_menu()
                self.submode = "menu"
            return

        data = self.ble.handle_input()
        if self.submode == "menu":
            if data is not None:
                try:
                    choice = int(data)
                    if choice == 0: 
                        self.cfg.save()
                        self.ble.send_prompt("saved")
                        self.mode, self.submode, self.ble_enable = "standby", None, False
                    elif choice == 9:
                        self.run_calibration()
                        self.ble.send_menu()
                    else: 
                        self.ble_choice = choice
                        if self.handle_ble_choice(choice, None):
                            self.ble.send_menu()
                            self.ble_choice = None
                        else:
                            self.submode = "input"
                except ValueError:
                    pass
        elif self.submode == "input":
            if data is not None:
                if self.handle_ble_choice(self.ble_choice, data):
                    self.ble.send_menu()
                    self.submode, self.ble_choice = "menu", None

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("Starting app...")
    app = TimerApp()
    app.run()
