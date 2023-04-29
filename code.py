
#    **********************
#    *   Climb_and_Dive   *
#    **********************

#  An Open Source Electric Control Line Timer by CircuitFlyer (a.k.a. Paul Emmerson).  A CircuitPython program for a
#  microcontroller development board to create a timed PWM servo signal with accelerometer input, PID RPM control
#  and Bluetooth LE programming suitable to conduct a typical flight of an electric powered control line model aircraft.

# Timer Program Version: 1.1, April 2023
# Microcontroller Board: Seeed Studio Xiao BLE, https://wiki.seeedstudio.com/XIAO_BLE/
# Firmware: CircuitPython 7.3.3, https://circuitpython.org/board/Seeed_XIAO_nRF52840_Sense/
# Backpack Hardware Version: 3.2

"""
MIT License

Copyright (c) 2023 CircuitFlyer (aka - Paul Emmerson) - Climb_and_Dive

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

# Import required libraries and modules:

from board import LED_RED, LED_BLUE, LED_GREEN, D6, D7, D9, D10, A0, A1, A2, A3
from time import monotonic, sleep, monotonic_ns
import touchio
from pwmio import PWMOut
import digitalio
from analogio import AnalogIn
import math
from microcontroller import nvm
from pulseio import PulseIn
from struct import pack, unpack
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_debouncer import Debouncer


# Set some things up to get started:


# Built in RGB LED
red_led = digitalio.DigitalInOut(LED_RED)
red_led.direction = digitalio.Direction.OUTPUT
green_led = digitalio.DigitalInOut(LED_GREEN)
green_led.direction = digitalio.Direction.OUTPUT
blue_led = digitalio.DigitalInOut(LED_BLUE)
blue_led.direction = digitalio.Direction.OUTPUT

# Capacitive touch sensor input on pin RX/D7
touch_debounced = touchio.TouchIn(D7)
touch = Debouncer(touch_debounced, interval=0.02)  # add a debouncer to the touchio pin, default stabilization interval is .01 seconds

# Optional pushbutton input on pin MI/D9
button_debounced = digitalio.DigitalInOut(D9)
button_debounced.switch_to_input(pull=digitalio.Pull.UP)
pushbutton = Debouncer(button_debounced, interval=0.02)  # v1.1 added debounce to the pushbutton to match touch pin

# Servo signal output on pin TX/D6
esc_pwm = PWMOut(D6, frequency=50)

# Setup accelerometer analog inputs
x_axis = AnalogIn(A0)
y_axis = AnalogIn(A1)
z_axis = AnalogIn(A2)

# Setup bluetooth UART
ble = BLERadio()
ble.name = "Climb & Dive v1.1"  # name to display on Bluetooth app, max v1.1 26 (was 18) characters
uart_server = UARTService()
advertisement = ProvideServicesAdvertisement(uart_server)
ble.stop_advertising()


# Create some helper functions:


def neo_update():  # generator used to control the color and flash rate of the built in LED.  Sorry, the neo name is not accurate for all boards.  It's a carry over from Adafruits boards.

    # initialize stored data:
    show = True  # not needed for LED's
    flash_time = 0

    # initial value:
    flash_count = 0

    while True:
        color, flash_interval = yield flash_count  # first time through (.send(None)) generator stops here and waits for next "now, color, flash_interval and long_touch logic state"
        if not long_touch:
            flash_count = 0
        if (flash_interval == 0):  # if a solid color is required, turn it on
            dot(color)
            show = True
        if ((flash_interval > 0) and (now >= flash_time + flash_interval)):  # if the led is to flash, check to see if it's time to turn on or off
            if (show):  # if on, turn off
                dot(BLANK)
                show = False
            else:
                dot(color)  # if off, turn on
                if (long_touch):
                    flash_count += 1  # record the number of flashes only if it's during a long touch (programming modes)
                show = True
            flash_time = now

def dot(color):
    if color[0] > 0:
        red_led.value = False  # Xiao BLE LED's are active LOW
    else:
        red_led.value = True
    if color[1] >0:
        green_led.value = False
    else:
        green_led.value = True
    if color[2] > 0:
        blue_led.value = False
    else:
        blue_led.value = True

def flash(number_of_flashes):  # used to display auto-shutdown fault codes at end of flight
    for i in range(number_of_flashes):
        red_led.value = False  # turn on
        sleep(.3)
        red_led.value = True  # turn off
        sleep(.5)

def save_parameters():  # used to write any changed parameters to non-volatile memory for the next flight
    array = pack('10h', delay_time, flight_time, rpm_setpoint, climb_gain, dive_gain, number_of_poles, motor_acceleration_setting, last_lap_duration, wing_axis, fuse_axis)
    nvm[0:20] = array
    print("Parameters have been saved")

def program_select():  # used to select the various choices within the manual programming modes
    global mode
    global main_count
    if (main_count == 1):  # 1 touch - program the delay time
        mode = "program_delay"
        print("Now in", mode, "mode")
        print("Current delay time is set to", delay_time, "seconds")
    if (main_count == 2):  # 2 touches  - program the flight time
        mode = "program_flight"
        print("Now in", mode, "mode")
        print("Current flight time is set to", flight_time, "seconds")
    if (main_count == 3):  # 3 touches - program the RPM
        mode = "program_rpm"
        print("Now in", mode, "mode")
        print("Current RPM is set to", rpm_setpoint)
    if (main_count == 4):  # 4 touches - exits the programming mode and returns to standby ready to fly
        mode = "standby"
        print("Now in", mode, "mode")
    main_count = 0
    return mode

def servo_duty_cycle(pulse_us, frequency=50):  # used to convert from a servo microsecond value to duty cycle integer
    period_us = 1 / frequency * 1_000_000
    duty_cycle = int(pulse_us / (period_us / 65535))
    return duty_cycle

def servo_us(duty_cycle, frequency=50):  # used to convert from a duty cycle integer to a servo microsecond value
    period_us = 1 / frequency * 1_000_000
    pulse_us = int(duty_cycle * (period_us/65535))
    return pulse_us

def g_force(axis):
    gravities = round(((axis.value/(65535/2))-1.01) * 5.5, 5)  # input converted to g's and rounded off any useless noise, 1.01 & 5.5 are approximate range and offset calibration values for the ADXL335
    return gravities

def axis_orientation():
    for x in range(1,4):
        accel_out = g_force(axes[x-1])  # read g-force on each axis
        if abs(accel_out) > .8:  # choose the vertical axis
            signed_axis = int(math.copysign(x, accel_out))  # derive a signed integer variable used to identify axis chosen (easier than using an ascii character)
            return signed_axis

def active():  # construct a generator using the global parameters.

    # initialize stored data
    old_wing_filtered = 0  # these are local vaiables
    wing_slope_filtered = 0
    last_time = 0

    # initial value
    active_out = 0

    while True:
        now = yield active_out  # first time through (.send(None)) generator stops here and waits for next "now"
        period = (now - last_time)/1_000_000_000  # uses time monotonic_us for better accuracy
        if period > .018:  # slows down the sample period, can improve noise rejection
            wing_in = g_force(axes[abs(wing_axis)-1]) * (math.copysign(1, wing_axis)) * -1  # invert for correct slope calculation
            wing_in *= 2  # multiplier to increase sensitivity
            #print((wing_in,))  # for testing use - plot raw wing axis data
            #fuse_in = g_force(axes[abs(fuse_axis)-1]) * (math.copysign(1, fuse_axis)) * -1  # invert for correct positive value calculation
            #print((fuse_in,))  # for testing use - plot raw fuse axis data
            wing_filtered = round((old_wing_filtered * wing_coefficient)+((1-wing_coefficient)*wing_in), 5)  # input filtered and rounded
            rate_of_change = (wing_filtered-old_wing_filtered)/period
            wing_slope = math.degrees(math.atan(rate_of_change))
            wing_slope_filtered = (wing_slope_filtered * wing_slope_coefficient)+((1-wing_slope_coefficient) * wing_slope)  # output filtered again
            old_wing_filtered = wing_filtered
            last_time = now
            if wing_slope_filtered > climb_threshold:  # climb(and dive) treshold can be used to adjust sensitivity
                boost = wing_slope_filtered - climb_threshold
            elif wing_slope_filtered < (dive_threshold * -1):
                brake = wing_slope_filtered + dive_threshold
            else:
                boost = 0
                brake = 0
            active_out = ((boost * climb_gain) + (brake * dive_gain)) * active_ouput_multiplier  # application of gain
            #print((active_out,))  # for testing use - plot RPM change


def getRPM():
    global RPM, valid_samples, now
    global total
    global start_time
    if (now - start_time) > .02:  # set min sample time to collect all required samples at the desired resolution (5000RPM min). This is also used for a fixed time interval for PID calculations
        pulses.pause()
        if (len(pulses) >= 6):  # if there is the minimum number of samples
            for i in range(len(pulses)):  # used to ignore extrememly short pulses that get past the RPM signal conditioining circuit
                if pulses[i] < 40:
                    pass
                else:
                    total += pulses[i]  # only valid pulses are totaled up
                    valid_samples += 1  # only the number of valid samples to be used in RPM calculation to give true RPM numbers.
            try:
                RPM = (int(((1_000_000/total)*60)/(number_of_poles/valid_samples)/10))*10  # need to divide by number of motor poles here.  Sets minimum resolution at 10RPM
            except ZeroDivisionError:
                RPM = 0
            if (RPM > 60_000):  # needed to read 0 RPM
                RPM = 0
        if (len(pulses) < 6):  # minimum samples
            RPM = 0
        total = 0
        valid_samples = 0
        pulses.clear()
        start_time = now
        pulses.resume()
        return RPM
    else:
        return  # if minimum sample time has not finished yet then return None

def PID(base, current_setpoint):
    global error_sum, last_input
    RPMinput = getRPM()
    if RPMinput is not None:
        #print((RPMinput - current_setpoint,))  # for testing use - plot measured RPM
        if RPMinput < (.75 * current_setpoint):  # prop strike protection - if  there is a loss of voltage signal, 0 RPM, or if motor stalls or falls to less than a % of setpoint - shut it down.  75% of setpoint RPM works OK, can adjust here is needed
            pid_us = idle_us
            #print(RPMinput)  # for testing use - show the last RPM when prop strike protection kicked in
            return pid_us
        else:
            error = current_setpoint - RPMinput
            error_sum += error * dt
            error_sum = max(min(500, error_sum), -500)  # clamp the Ki portion to limit windup
            if last_input == 0:  # this prevents a large  negative derror first time through
                last_input = RPMinput
            derror = (last_input - RPMinput)
            derror = max(min(500, derror), -500)  # clamp Kd portion to limit spikes due to a sudden step change
            pid_us = int(base + (Kp * error) + (Ki * error_sum) + (Kd * derror))
            pid_us = max(min(max_throttle_us, pid_us), idle_us)  # clamp output so it never goes out of range.
            last_input = RPMinput
            return pid_us
    else:
        return

def spool_up():
    global mode, base_us, motor_status, sample_count
    global start_time, fault_code
    tach = getRPM()
    if tach is not None:
        #print((tach - rpm_setpoint,))  # for testing use - plot measured RPM
        if tach < (rpm_setpoint - 200):  # transfer point from spool-up to PID control
            new_duty_cycle = esc_pwm.duty_cycle + (motor_acceleration_setting * 2)  # value used for incrementing RPM
            new_duty_cycle = max(min(servo_duty_cycle(max_throttle_us), new_duty_cycle), servo_duty_cycle(idle_us))  # clamp it to stay within allowable range
            esc_pwm.duty_cycle = new_duty_cycle
        if tach < (rpm_setpoint - 200) and tach > 0 and sample_count < 5:  # at motor start-up the RPM readings are not accurate.  This is required to ignoring the first few RPM samples.
            sample_count += 1
        if tach >= (rpm_setpoint - 200) and sample_count >= 5:
            setpoint_duty_cycle = esc_pwm.duty_cycle
            print("output us = ", servo_us(setpoint_duty_cycle), "output duty cylce = ", esc_pwm.duty_cycle, "=", tach, "RPM")  # prints the transfer point details
            motor_status = "run"  # now under PID control
            sample_count = 0
            base_us = (servo_us(esc_pwm.duty_cycle))
            start_time = now
        if tach == 0 and now - last_time > (1.6 + (4/motor_acceleration_setting)):  # timeout limit if no RPM detected
            mode = "flight_complete"
            print("Failed to start")
            fault_code = 2
        if now - last_time > (5 + (20/motor_acceleration_setting)):  # timeout in case the RPM never reaches transition point
            mode = "flight_complete"
            print("Motor failed to reach full RPM")
            fault_code = 3

def check_ble():
    global mode
    if not ble.connected and not ble.advertising:  # advertise when not connected.
        print("Advertising...")
        ble.start_advertising(advertisement)
    if ble.connected and not mode == "ble_programming":
        ble.stop_advertising()
        print("Connected")
        mode = "ble_programming"  # change to ble program mode

def send_text(first_line, last_line):
    if last_line == -1:
        last_line = len(text_file)
        first_line = len(text_file) - 1
    for item in text_file[first_line:(last_line + 1)]:
        uart_server.write(item.encode())  # writes text items

def update_strings():
    global temp_file
    text0 = "**** Climb_and_Dive Timer Settings ****\n\n"  # list of all the strings to display
    text1 = " 1) Start Delay Time .... {} seconds\n".format(delay_time)
    text2 = " 2) Flight Time ......... {} seconds\n".format(flight_time)
    text3 = " 3) RPM Setting ......... {} RPM\n".format(rpm_setpoint)
    text4 = " 4) Climb Gain .......... {} \n".format(climb_gain)
    text5 = " 5) Dive Gain ........... {} \n".format(dive_gain)
    text6 = " 6) Number of Motor Poles {} \n".format(number_of_poles)
    text7 = " 7) Motor Acceleration .. {} \n".format(motor_acceleration_setting)
    text8 = " 8) Last Lap Time........ {} \n".format(last_lap_duration)
    text9 = " 9) Mounting Position ... {}, {}\n".format(axis_display_name[wing_axis], axis_display_name[fuse_axis])  # v1.1 added orientation detection
    text14 = " 0) Save and EXIT\n"
    text151 = "\nStep 1: Record wing to timer mounting orientation.  Point outboard wing down.\n"
    text152 = "\nEnter W when ready "
    text153 = "\nStep 2: Record fuselage to timer mounting orientation.  Point the nose of the fuselage down.\n"
    text154 = "\nEnter F when ready "
    text155 = "\n"
    text156 = "or X to return to Main Menu\n"
    text16 = " \nEnter item #:\n"
    text18 = " \nEnter new setting:\n"
    text20 = " \nParameters saved, OK to disconnect\n"
    temp_file = [text0, text1, text2, text3, text4, text5, text6, text7, text8, text9, text14, text151, text152, text153, text154, text155, text156, text16, text18, text20]  # make a list of all of the strings

def input_ble_settings(choice):
    global delay_time
    global flight_time
    global rpm_setpoint
    global climb_gain
    global dive_gain
    global number_of_poles
    global motor_acceleration_setting
    global last_lap_duration
    global temp_file
    global text_file
    global orientation_step_1
    global orientation_step_2
    global wing_axis
    global fuse_axis
    waiting_for_input = True  # flag to hold in new parameter input loop
    while waiting_for_input:
        if uart_server.in_waiting:  # incoming (RX) check for incoming text
            input_bytes = uart_server.read(uart_server.in_waiting)  # read text
            setting = input_bytes.decode().strip()  # strip linebreak
            print(setting)
            try:
                new_setting = int(setting)  # integers only
                if choice == 1:
                    new_setting = min(60, max(0, new_setting))  # constrain output, delay time 0-60 seconds
                    delay_time = new_setting
                if choice == 2:
                    new_setting = min(360, max(1, new_setting))  # constrain output, flight time 1 sec to 6 minutes
                    flight_time = int(new_setting)
                if choice == 3:
                    new_setting = min(15000, max(4000, new_setting))  # constrain output, RPM setpoint v1.1 reduced to 4000 (was 5000) to 15000 RPM
                    rpm_setpoint = new_setting
                if choice == 4:
                    new_setting = min(10, max(0, new_setting))  # constrain output, climb gain setting 0-10
                    climb_gain = new_setting
                if choice == 5:
                    new_setting = min(10, max(0, new_setting))  # constrain output, dive gain setting 0-10
                    dive_gain = new_setting
                if choice == 6:
                    new_setting = min(24, max(2, new_setting))  # constrain output, number of motor magnets 2 to 24
                    number_of_poles = new_setting
                if choice == 7:
                    new_setting = min(10, max(1, new_setting))  # constrain output, motor acceleration setting 1 to 10
                    motor_acceleration_setting = new_setting
                if choice == 8:
                    new_setting = min(10, max(0, new_setting))  # constrain output, last lap duration setting 0 to 10
                    last_lap_duration = new_setting
                if choice == 9:
                    if orientation_step_1:
                        send_text(12,12)
                        send_text(-4,-4)
                    if orientation_step_2:
                        send_text(14,14)
                        send_text(-4,-4)
                if not orientation_step_1 and not orientation_step_2:
                    update_strings()  # make sure text files contain new parameter
                    text_file = temp_file
                    send_text(-5,-5)  # line space
                    send_text(1,10)  # display new parameters
                    waiting_for_input = False  # exit loop, go back to parameter selection
            except ValueError:
                if choice == 9 and setting != "":
                    if orientation_step_1 and setting in "Ww":
                        temp_wing_axis = axis_orientation()
                        orientation_step_1 = False
                        send_text(13,14)
                        send_text(-4,-4)
                        orientation_step_2 = True
                    if orientation_step_2 and setting in "Ff":
                        fuse_axis = axis_orientation()
                        wing_axis = temp_wing_axis
                        orientation_step_2 = False
                        update_strings()  # make sure text files contain new parameter
                        text_file = temp_file
                        send_text(-5,-5)  # line space
                        send_text(1,10)  # display new parameters
                        waiting_for_input = False  # exit loop, go back to parameter selection
                    elif (orientation_step_1 or orientation_step_2) and setting in "Xx":
                        orientation_step_1 = False
                        orientation_step_2 = False
                        send_text(-5,-5)  # line space
                        send_text(1,10)  # display new parameters
                        waiting_for_input = False  # exit loop, go back to parameter selection
                if choice == 9 and (orientation_step_1 or orientation_step_2) and setting not in "WwFfXx":
                    print("valueError")  # non-integer was entered by mistake
                    if orientation_step_1:
                        send_text(12,12)
                        send_text(-4,-4)
                    if orientation_step_2:
                        send_text(14,14)
                        send_text(-4,-4)
                elif choice != 9:
                    send_text(-2,-2)  # re-enter value


# Define a bunch of variables:

previous_touch = False
counter = 0
touch_time = 0
long_touch = False
end_of_long_touch = False
RED = (255, 0, 0)
YELLOW = (200, 200, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
MAGENTA = (255, 0, 100)
WHITE = (255, 255, 255)
BLANK = (0, 0, 0)
done = False
mode = "standby"
flash_count = 0
last_time = 0
delay_time = 10  # default delay time (seconds)
flight_time = 180  # default flight time (seconds)
rpm_setpoint = 10000  # default rpm setting
wing_coefficient = .88  # active input filter
wing_slope_coefficient = .91  # active output filter
climb_threshold = 20
dive_threshold = 20
active_ouput_multiplier = 3
climb_gain = 5  # default gain
dive_gain = 5  # default gain
idle_us = 950
max_throttle_us = 2000
n = 0  # code loop counter
oldtime = 0  # code loop timer
number_of_poles = 14  # default number of magnetic poles in motor
last_update = 0
samples = 14  # number of RPM pulses to count
total = 0  # prevent divide by 0 error
RPM = 0
motor_acceleration_setting = 5  # default motor acceleration (spool up) or soft start
base_us = 0
error_sum = 0
Kp = .05
Ki = .5
Kd = .004
last_input = 0
dt = .02
rpm_last_time = 0
sample_count = 0
motor_status = None
valid_samples = 0
start_time = 0  # this is to supply an initial value to getRPM()
fault_code = 0
ESC_calibration = False
shutdown = False
start_blip = 1100  # throttle setting for indication of start-up, short duration throttle blip
axes = [x_axis, y_axis, z_axis]  # v1.1 build list of accelerometer axes
wing_axis = 3  # default value, +3 == +z axis, can asign any axis based on the timer mounting orientation
fuse_axis = -1  # default value, -1 == -x axis, can assign any axis based on the timer mounting orientation
axis_display_name = {1: '+X', -1: '-X', 2: '+Y', -2: '-Y', 3: '+Z', -3: '-Z'}  # create dictionary of axis variable names cross referenced to their display names
orientation_step_1 = False
orientation_step_2 = False
last_lap_duration = 0


# Read saved parameters from non-volatile memory:

if nvm[0:6] ==  nvm[20:26] :  # if the parameters have never been saved before (brand new microcontroller), write all of the default parameters to memory
    save_parameters()
if nvm[14:20] == nvm[20:26]:  # if updatingto latest revisions add memory items that have never been saved before, write only the new default values to memory
    array = pack('3h', last_lap_duration, wing_axis, fuse_axis)
    nvm[14:20] = array
else:  # otherwise assign the saved data for use as the new current parameters
    memory_read = nvm[0:20]
    data = unpack('10h', memory_read)
    delay_time = data[0]
    flight_time = data[1]
    rpm_setpoint = data[2]
    climb_gain = data[3]
    dive_gain = data[4]
    number_of_poles = data[5]
    motor_acceleration_setting = data[6]
    last_lap_duration = data[7]
    wing_axis = data[8]
    fuse_axis = data[9]


# Construct and initialize generators:

active1 = active()
active1.send(None)

neo_update1 = neo_update()
neo_update1.send(None)

# Set-up RPM signal input on pin MO/D10:

pulses = PulseIn(D10, maxlen=samples, idle_state=False)

# ESC throttle calibration routine:

if touch_debounced.raw_value > 500 or not button_debounced.value:  # if touch pin, or optional pushbutton is held at power-up
    esc_pwm.duty_cycle = servo_duty_cycle(max_throttle_us)  # set initial throttle to max throttle for ESC throttle Calibration
    ESC_calibration = True
    print("ESC Throttle Calibration - Maximum Trottle Output")
while touch_debounced.raw_value > 500 or not button_debounced.value:
    sleep(.05)  # wait here until touch pin or puchbutton released
if ESC_calibration == True:
    ESC_calibration = False
    touch_debounced.threshold = 250  # reset the touch pin threshold to a normal value
    print("ESC Throttle Calibration Complete - Minimum Throttle Output")

# Normal start-up at idle RPM:

esc_pwm.duty_cycle = servo_duty_cycle(idle_us)  # set initial throttle to idle
print("Now in", mode, "mode")


# Main Loop


while True:

    now = monotonic()  # update current time
    touch.update()  # checks the debounced input pin status
    pushbutton.update()  # checks the optional debounced pushbutton status
    button = not pushbutton.value  # invert the pull-up pushbutton logic to match the touch pin
    main_count = 0  # clear previous short touch count
    n += 1
    if n % 1000 == 0:
        #print((now - oldtime)/1000)  # for testing use - print the average loop time
        oldtime = now

# each time through the main loop, the following will test the touch pin for # of short touches or if a long touch has been entered

    if ((touch.value or button) and not previous_touch):  # at the start of any touch
        touch_time = now
        counter += 1
        previous_touch = True

    if (not (touch.value or button) and previous_touch):  # at the end of any touch
        previous_touch = False
        if (long_touch):  # except long touches, don't count long touches
            counter = 0
            long_touch = False
            end_of_long_touch = True  # set flag

    if (now - touch_time > 1 and counter > 0 and not (touch.value or button) and not long_touch):  # delay before updating short touch count
        main_count = counter  # indicator that short count is complete
        counter = 0

    if (now - touch_time > 3 and (touch.value or button) and previous_touch):  # after holding a touch for 3 seconds
        long_touch = True

# Timer program code

    if (mode == "standby"):  # entered at power-up, from programming modes or an aborted delay mode
        neo_update1.send((GREEN, 0))
        if ble.advertising:  # if ble_programming mode entered but never connected, stop advertising
            ble.stop_advertising()
            print("...Stop Advertising")
        if (long_touch):  # starts the timer for a typical flight
            mode = "delay"  # normal way to exit this mode
            esc_pwm.duty_cycle = servo_duty_cycle(start_blip)  # set throttle to a low RPM to indicate a start-up blip
            sleep(1.5)  # run motor for a very short period
            esc_pwm.duty_cycle = servo_duty_cycle(idle_us)  # return throttle to idle
            last_time = now  # start the timer for the start delay
            print("Now in", mode, "mode")
        if (main_count == 5):  # 5 short touches - enter the programming mode
            mode = "program_delay"  # alternate way to exit this mode
            print("Now in", mode, "mode")
            print("Current delay time is set to", delay_time, "seconds")

    if (mode == "program_delay"):  # manual programming only - entered from standby or any other program mode
        check_ble()
        if (long_touch):
            flash_count = neo_update1.send((YELLOW, 0.4))
        else:
            neo_update1.send((YELLOW, 0))
        if (end_of_long_touch):
            delay_time = flash_count  # count the number of flashes (1 flash = 1 second of delay) and
            save_parameters()  # save the parameters
            end_of_long_touch = False  # reset flag
            flash_count = 0  # reset count
            print('New delay time will be', delay_time, "seconds")
        mode = program_select()  # number of touches will determine where to go next

    if (mode == "program_flight"):  # manual programming only - entered from any other program mode
        check_ble()
        if (long_touch):
            flash_count = neo_update1.send((CYAN, 0.4))
        else:
            neo_update1.send((CYAN, 0))
        if (end_of_long_touch):
            flight_time = flash_count * 10 # count the number of flashes (1 flash = 10 seconds of flight) and
            save_parameters()  # save the parameters
            end_of_long_touch = False  # reset flag
            flash_count = 0  # reset count
            print('New flight time will be', flight_time, "seconds")
        mode = program_select()  # number of touches will determine where to go next

    if (mode == "program_rpm"):  # manual programming only - entered from any other program mode
        check_ble()
        if (now - touch_time > 0.2 and (touch.value or button)):  # at the start of the next long touch
            neo_update1.send((MAGENTA, 0.05))  # flash quickly to warn of impending motor stat-up
        else:
            neo_update1.send((MAGENTA, 0))
        if (long_touch):
            start_time = now
            mode = "set_rpm"  # switch to the rpm setting mode
            last_time = now
            print("Now in", mode, "mode")
        mode = program_select()  # number of short touches determine where to go next

    if (mode == "set_rpm"):  # manual programming only - mode to run motor at flight RPM and adjust as required
        neo_update1.send((MAGENTA, 0.2))
        if motor_status == None:
            spool_up()
        if motor_status == "run":
            pid_out = PID(base_us, rpm_setpoint)
            if pid_out == idle_us:  # main prop strike protection acts here
                mode = "flight_complete"
                print("Low RPM or Loss of RPM Signal Detected")
                fault_code = 1
            if pid_out is not None:
                esc_pwm.duty_cycle = servo_duty_cycle(pid_out)
        if (main_count == 1 and rpm_setpoint <= 14950):  # if a single touch and below  maximum value
            rpm_setpoint += 50  # speed it up a little
            print(rpm_setpoint)
        if (main_count == 2 and rpm_setpoint >= 4050):  # if a double touch and above  minimum value
            rpm_setpoint -= 50  # slow it down a little
            print(rpm_setpoint)
        if (counter == 3):   # three touches to stop motor and write new settings to memory
            save_parameters()  # save the parameters
            esc_pwm.duty_cycle = servo_duty_cycle(idle_us)  # set throttle to idle
            end_of_long_touch = False  # reset flag
            motor_status = None  # reset for the next time
            mode = "program_rpm"  # exit to the beginning of the program RPM mode

    if mode == "ble_programming":

        neo_update1.send((BLUE, 0))
        waiting = True
        finished = False
        update_strings()  # build the initial text strings
        text_file = temp_file  # create the initial list of stirngs
        while ble.connected and waiting:  # hold off on sending opening menu until user has UART window open and sends something
            if uart_server.in_waiting:  #  incomming (RX) waits for any incomming bytes
                send_text(0,10) # writes menu items
                send_text(-3,-3)  # asks to select menu item
                waiting = False  # exits the while loop
                uart_server.reset_input_buffer()  # discards the first bytes received
        while ble.connected and not finished:
            if uart_server.in_waiting:  # Incoming (RX) check for incoming text
                raw_bytes = uart_server.read(uart_server.in_waiting) # read text
                selection = raw_bytes.decode().strip() # strip linebreak
                try:
                    choice = int(selection)  # integers only
                    if (1 <= choice and choice <= 8):  # menu parameter selection
                        send_text(-5,-5)  # line space
                        send_text(choice,choice)  # show selection
                        send_text(-2,-2)   # ask for new input
                        input_ble_settings(choice)  # new input function
                    if (choice == 9):
                        print("Start Axis alignment routine")
                        send_text(-5,-5)  # line space
                        send_text(choice,choice)  # show selection
                        send_text(11,12)
                        send_text(-4,-4)  # ask for input
                        orientation_step_1 = True
                        input_ble_settings(choice)  # new input function
                    if choice == 0:  # menu EXIT selection
                        send_text(-1,-1)  # show exit text
                        save_parameters()  # save any changed parameters
                        mode = "standby"  # go back when finished with changes
                        finished = True  # exit ble programming loop
                    else:
                        send_text(-3,-3)  # re-enter index #
                except ValueError:
                    send_text(-3,-3)  # re-enter index #
        print("Disconnected")  # will automatically disconnect if app drops connection
        mode = "standby"  # go to safety if app drops connection
        print(mode)

    if (mode == "delay"):  # mode to count down the time of the delayed start
        if (end_of_long_touch and (touch.value or button)):  # after the long touch used to enter this mode is over, any touch while in delay mode will abort and return to standby
            mode = "standby"
            end_of_long_touch = False  # reset flag
            print("Now in", mode, "mode")
        if (now - last_time + 5 > delay_time):  # 5 seconds of warning flash before starting motor
            neo_update1.send((WHITE, 0.05))
        else:
            neo_update1.send((BLUE, 0.5))
        if (now - last_time > delay_time):  # after the programmed delay start the motor for take-off
            mode = "take-off"
            last_time = now
            start_time = now
            esc_pwm.duty_cycle = servo_duty_cycle(1090)  # jump throttle ahead to reduce delay before motor starts to turn
            print("Now in", mode, "mode")

    if (mode == "take-off"):  # mode to slowly ramp up the RPM for a smooth take-off
        neo_update1.send((RED, 1))
        if ((touch.value or button) and (end_of_long_touch or not previous_touch)):  # any touch will kill the motor and end the flight
            mode = "flight_complete"
            print("Now in", mode, "mode")
        spool_up()
        if motor_status == "run":
            mode = "flight"
            last_time = now
            motor_status = None
            print("Now in", mode, "mode")

    if (mode == "flight"):  # mode to time the lenght of flight
        neo_update1.send((RED, 1))
        if ((touch.value or button) and (end_of_long_touch or not previous_touch)):  # any touch will kill the motor and end the flight
            mode = "flight_complete"
            print("Now in", mode, "mode")
        if (now - last_time > 5):  # delay the implementation of the active output until after airplane has finished accelerating up to cruising speed.
            new_rpm_setpoint = rpm_setpoint + active1.send(monotonic_ns())  # add active accelerometer output
        else:
            new_rpm_setpoint = rpm_setpoint
            active1.send(monotonic_ns())  # keep the values up to date
        pid_out = PID(base_us, new_rpm_setpoint)
        if pid_out == idle_us:
            mode = "flight_complete"
            print("Low RPM or Loss of RPM Signal Detected")
            fault_code = 1
        if pid_out is not None:
            esc_pwm.duty_cycle = servo_duty_cycle(pid_out)
        if (now - last_time + 11) > (flight_time):  # flash the Neopixel for 10 seconds before landing mode
            neo_update1.send((WHITE, 0.05))
        if (now - last_time + 1) > (flight_time):  # time is up, prep for landing
            mode = "landing"
            last_time = now
            print("Now in", mode, "mode")

    if (mode == "landing"):  # used to boost the RPM for a short period to improve landing glide
        neo_update1.send((RED, 0.25))
        if (touch.value or button):  # any touch will kill the motor and end the flight
            mode = "flight_complete"
            print("Now in", mode, "mode")
        if (now - last_time) <= 3:  # start burst of higher RPM at end of flight
            new_rpm_setpoint = rpm_setpoint + 1000  # increase RPM by 1000
        if (now - last_time) > 3:  # end burst of higher RPM at end of flight
            new_rpm_setpoint = rpm_setpoint  # decrease the RPM back down to normal flight RPM
        pid_out = PID(base_us, new_rpm_setpoint)
        if pid_out == idle_us:
            mode = "flight_complete"
            print("Low RPM or Loss of RPM Signal Detected")
            fault_code = 1
        if pid_out is not None:
            esc_pwm.duty_cycle = servo_duty_cycle(pid_out)
        if (now - last_time) > (3 + last_lap_duration):  # end of flight after any last lap time
            esc_pwm.duty_cycle = servo_duty_cycle(idle_us)  # set throttle to idle
            mode = "flight_complete"
            last_time = now
            print("Now in", mode, "mode")

    if (mode == "flight_complete"):  # used to latch the program in an endless loop to conclude the flight and stop the motor
        esc_pwm.duty_cycle = servo_duty_cycle(idle_us)
        neo_update1.send((BLANK, 0))
        while True:
            sleep(3)  # flash codes for auto-shutdown events, 1 for prop strike, 2 for failed start, 3 for failure to reach governed RPM setpoint
            if fault_code > 0:
                flash(fault_code)
            pass
