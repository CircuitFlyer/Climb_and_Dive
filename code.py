
#    **********************
#    *   Climb_and_Dive   *
#    **********************

#  An Open Source Electric Control Line Timer by CircuitFlyer (a.k.a. Paul Emmerson).  A CircuitPython program for a
#  microcontroller development board to create a timed PWM servo signal with accelerometer input, PID RPM control
#  and Bluetooth LE programming suitable to conduct a typical flight of an electric powered control line model aircraft.

# Timer Program Version: 1.5.2, June 2025
# Microcontroller Board: Seeed Studio Xiao BLE, https://wiki.seeedstudio.com/XIAO_BLE/
# Firmware: CircuitPython 7.3.3, https://circuitpython.org/board/Seeed_XIAO_nRF52840_Sense/
# Backpack Hardware Version: 3.2

"""
MIT License

Copyright (c) 2025 CircuitFlyer (aka - Paul Emmerson) - Climb_and_Dive

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

from board import LED_RED, LED_BLUE, LED_GREEN, D3, D6, D7, D9, D10, A0, A1, A2
from time import monotonic, sleep, monotonic_ns
from touchio import TouchIn
from pwmio import PWMOut
import digitalio
from analogio import AnalogIn
from math import copysign, degrees, atan, isnan, sin, pi
from microcontroller import nvm
from pulseio import PulseIn
from struct import pack, unpack
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_debouncer import Debouncer
from ulab import numpy as np
import neopixel

##############################################################################
"""
Here are a few variables that you can change to customise your own timer.
Do not change the names of the variables; only the values assigned to them.
Please read the instructions "Advanced Modifications" for more information.
"""


blip_duration = 0.5  # time in seconds for the duration of the start-up throttle blip
blip_PWM = 1150  # throttle setting used for the short duration throttle blip
touch_pin_sensitivity = 100  # threshold value to trigger the touch pin
timer_name = "Climb & Dive v1.5.2"  # name displayed on the Bluetooth app screen, max 26 characters
pixel_colour = "RGB"  # order of the colours used in your Neopixel
glide_boost = 3  # time in seconds for the duration of higher RPM at the end of the flight
corner_boost_duration = 0.6  # time in seconds for the duration of the higher RPM boost in bottom corners

##############################################################################

# Set some things up to get started:

# Built in RGB LED
red_led = digitalio.DigitalInOut(LED_RED)
red_led.direction = digitalio.Direction.OUTPUT
green_led = digitalio.DigitalInOut(LED_GREEN)
green_led.direction = digitalio.Direction.OUTPUT
blue_led = digitalio.DigitalInOut(LED_BLUE)
blue_led.direction = digitalio.Direction.OUTPUT

# Optional Remote Neopixel LED on pin D3
pixels = neopixel.NeoPixel(D3, 1, brightness=1.0, auto_write=True, pixel_order= pixel_colour)

# Capacitive touch sensor input on pin RX/D7
touch_debounced = TouchIn(D7)
touch_debounced.threshold = touch_debounced.raw_value + touch_pin_sensitivity
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
ble.name = timer_name  # name to display on Bluetooth app
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
            pixels[0] = color
            show = True
        if ((flash_interval > 0) and (now >= flash_time + flash_interval)):  # if the led is to flash, check to see if it's time to turn on or off
            if (show):  # if on, turn off
                dot(BLANK)
                pixels[0] = BLANK
                show = False
            else:
                dot(color)  # if off, turn on
                pixels[0] = color
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
        pixels[0] = RED
        sleep(.3)
        red_led.value = True  # turn off
        pixels[0] = BLANK
        sleep(.5)

def save_parameters():  # used to write any changed parameters to non-volatile memory for the next flight
    array = pack('10h', delay_time, flight_time, rpm_setpoint, climb_gain, dive_gain, number_of_poles, motor_acceleration_setting, last_lap_duration, wing_axis, fuse_axis)
    nvm[0:20] = array
    array = pack('5h', overhead_boost_setting, estop, corner_boost_gain, int(vert_axis_scale_factor * 1000), int(vert_axis_offset * 1000))
    nvm[30:40] = array
    print("Parameters have been saved")

def read_memory():  # used to read all of the parameter values previously saved to memory
    global delay_time, flight_time, rpm_setpoint, climb_gain, dive_gain, number_of_poles, motor_acceleration_setting, last_lap_duration, wing_axis, fuse_axis, overhead_boost_setting
    global estop, corner_boost_gain, vert_axis_scale_factor, vert_axis_offset, vert_axis
    memory_read = nvm[0:40]
    data = unpack('20h', memory_read)
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
    overhead_boost_setting = data[15]
    estop = data[16]
    corner_boost_gain = data[17]
    vert_axis_scale_factor = data[18]/1000  # convert to float
    vert_axis_offset = data[19]/1000  # convert to float
    vert_axis = 6 - (abs(wing_axis) + abs(fuse_axis))  # determine vertical axis

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
            signed_axis = int(copysign(x, accel_out))  # derive a signed integer variable used to identify axis chosen (easier than using an ascii character)
            return signed_axis

def read_axis(axis):
    data = 0
    for y in range(100):  # oversample the accelerometer readings to reduce noise and improve accuracy
        data += g_force(axis)
    point = data/100
    return point

def calibrate(point1, point2):  # 2-point calibration routine
    ref_range = 2
    raw_range = abs(point1-point2)
    correction_factor = ref_range/raw_range
    offset = ((point1 + point2)/2) * correction_factor
    return correction_factor, offset

def active():  # Construct a generator to determine the accelerometer based active output.

    global mode, rpm_setpoint

    # Initialize some locally used data

    m = 0
    data1 = np.zeros(len(taps1) + 1)  # wing output digital filter buffer
    wing_buffer = []  # wing offset calibration buffer
    boost = 0
    brake = 0
    level_gforce = 0
    old_wing_accelerometer = 0
    wing_coefficient = .85  # IIR filter for smoothing of the wing input accelerometer
    data2 = np.zeros(7)  # number of samples to record for pull testing
    reference_data = np.array([-0.88, -0.97, -0.45, 0.39, 0.93, 0.79, 0.18])
    submode = "normal"
    pull_count = 0
    #timer1 = 0
    timer2 = 0
    timer3 = 0
    i=0
    shutdown = False
    corner = False
    history = np.ones(20)  # buffer to hold vert_accelerometer history
    old_vert_accelerometer = 0
    vert_coefficient = .9  # IIR filter for smoothing of the vertical input accelerometer
    corner_boost = 0

    # Initial value
    active_out = 0

    while True:
        now = yield active_out  # first time through (.send(None)) generator stops here and waits for next "now"
        # Measure accelerometer values and calculate output:
        wing_accelerometer = g_force(axes[abs(wing_axis)-1]) * (copysign(1, wing_axis)) * -1  # invert for correct slope calculation
        wing_accelerometer_average = round((old_wing_accelerometer * wing_coefficient)+((1-wing_coefficient)*wing_accelerometer), 5)  # input IIR filtered and rounded
        old_wing_accelerometer = wing_accelerometer_average
        vert_accelerometer = (g_force(axes[vert_axis-1]) * vert_axis_scale_factor) - vert_axis_offset  # raw vertical axis accelerometer data with calibration
        vert_accelerometer_average = round((old_vert_accelerometer * vert_coefficient)+((1-vert_coefficient)*vert_accelerometer), 5)  # input IIR filterd and rounded
        old_vert_accelerometer = vert_accelerometer_average
        history = np.roll(history,-1)
        history[-1] = (vert_accelerometer_average)  # load history buffer with filtered data
        vert_rate = np.sum(np.diff(history,n=1))
        if m % 2 == 0:  # reduce the sample frequency to allow a decrease in the filter cutoff frequency
            data1 = np.roll(data1,1)
            data1[-1] = wing_accelerometer_average
            first_derivative = np.diff(data1, n=1)  # determine the derivative of the wing input data
            wing_filtered_output = (np.sum(first_derivative * taps1)) * -1  # Apply FIR filter and invert for correct action
            calculated_slope = degrees(atan(wing_filtered_output/.006667))  # use average period to match sampling rate of filter
            slope = min(40, max(-40,calculated_slope))  # clip off the maximum/minimum slope, peak values not required
            if slope > climb_threshold:  # climb (and dive) treshold can be used to adjust sensitivity
                boost = slope - (climb_threshold / 2)  # only subtract 1/2 the threshold to augment the output slightly
            elif slope < (dive_threshold * -1):
                brake = slope + (dive_threshold / 2)
            else:
                boost = 0
                brake = 0
        # Measure and calculate level flight normal g-force offset:
        if data_collection and (m % 20 == 0):  # collect a sample of g-force readings for a short period after take-off
            wing_buffer.append(wing_accelerometer_average)  # stream the sampled data into a buffer
            wing_buffer_data = np.array(wing_buffer)  # convert the buffer to an array
            level_gforce = np.mean(wing_buffer_data)  # determine the average reading for level laps
        wing_accelerometer_corrected = wing_accelerometer_average - level_gforce  # offset the wing input data
        # Calculate overhead boost:
        if (wing_accelerometer_average - level_gforce) > overhead_threshold:
            overhead = (wing_accelerometer_average - level_gforce) - overhead_threshold  # determine when flying overhead
        else:
            overhead = 0
        overhead_boost = (overhead * overhead_boost_setting) * 40  # calculate the amount of additional overhead RPM desired
        # Determine and calculate for a lower altitude, sharp turn condition, used to add a boost in square corners:
        if not corner and wing_accelerometer_corrected < 0.5 and ((vert_accelerometer_average > 3 and vert_rate > 1) or (vert_accelerometer_average < -3 and vert_rate < -1)):  # minimum thresholds
            corner = True  # sharp turn detected
            timer4 = now
            corner_boost = 40 * corner_boost_gain  # calculate RPM increase for sharp corner
        if corner and ((now - timer4)/1_000_000_000) > corner_boost_duration :  # end corner boost
            corner = False
            corner_boost = 0
        # Calculate  active output:
        active_out = (int((boost * (climb_gain)) + (brake * dive_gain)) * active_ouput_multiplier) + overhead_boost + corner_boost # calculate output
        # For testing purposes only:
        if m % 5 == 0:  # approx 50/sec
            #print((active_out, ))  # for testing use - enter any variables of your choice to plot the output in real time
            pass
        if estop != 0 and (m % 20 == 0):  # approx 15 samples/sec
            clock = round((now/1_000_000_000)-last_time, 2)  # record the time since the start of the flight mode
            if submode == "normal":
                if pull_count > 0 and (clock - timer2) > .6:  # maximum time between valid pulls
                    pull_count = 0
                if wing_accelerometer_corrected <= -.5:
                    submode = "collect_data"
            if submode == "collect_data":
                data2[i] = wing_accelerometer_corrected  # record accelerometer output
                i += 1
                if i == 7:  # maximum number of samples collected
                    submode = "analyse_data"
                    i = 0
            if submode == "analyse_data":
                mean = np.mean(data2)
                data2_centered = data2 - mean
                correlation = np.sqrt(np.sum(reference_data ** 2) * np.sum(data2_centered ** 2)) # compare the input data to the reference data
                peak_value = np.max(data2_centered)  # find max value
                if correlation > 2.8 and peak_value > .7:  # confirm a valid pull
                    pull_count += 1
                    timer2 = clock
                    submode = "normal"
                else:
                    pull_count = 0  # if not a valid pull then reset and wait for start of next pull
                    submode = "normal"
                #print("correlation: ", correlation, " peak value: ", peak_value, " pull count: ", pull_count)  # for testing purposes
            if shutdown and (clock - timer3) >= 1.5:
                rpm_setpoint -= 800  # test mode only; reset RPM back to normal
                shutdown = False
            if not shutdown and pull_count >= 3:  # triggers on the third confirmed pull
                print("Pilot initiated shutdown detected")
                if estop == 1:  # enables test mode instead of hard cutoff
                    shutdown = True  # test mode only; gives high RPM for 1.5 seconds
                    pull_count = 0
                    timer3 = clock
                    rpm_setpoint += 800  # test mode only; RPM boost
                if estop == 2:  # hard cutoff enabled
                    mode = "flight_complete"  # this is official emergency shutdown procedure
                    print("Now in", mode, "mode")
        m += 1


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
                    valid_samples += 1  # only the number of valid samples to be used in RPM calculation to give true RPM numbers
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
        #print((RPMinput - current_setpoint,))  # for testing use - plot RPM variables
        if RPMinput < (.75 * current_setpoint):  # prop strike protection - if  there is a loss of voltage signal, 0 RPM, or if motor stalls or falls to less than a % of setpoint - shut it down.  75% of setpoint RPM works OK, can adjust here is needed
            pid_us = idle_us
            print(RPMinput)  # for testing use - show the last RPM when prop strike protection kicked in
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
    global start_time, fault_code, old_tach
    tach = getRPM()
    if tach is not None:
        #print((tach - rpm_setpoint,))  # for testing use - plot measured RPM
        if tach < (rpm_setpoint - 200):  # bump the throttle if RPM is valid but has not yet reached the transfer point to PID control
            new_duty_cycle = esc_pwm.duty_cycle + (motor_acceleration_setting * 2)  # value used for incrementing RPM
            new_duty_cycle = max(min(servo_duty_cycle(max_throttle_us), new_duty_cycle), servo_duty_cycle(idle_us))  # clamp it to stay within allowable range
            esc_pwm.duty_cycle = new_duty_cycle
        if tach < (rpm_setpoint - 200) and tach > 0 and sample_count < 8:  # at motor start-up the RPM readings are not accurate.  This is required to ignoring the first few RPM samples.
            sample_count += 1
        if tach < (rpm_setpoint - 200) and sample_count >= 8:  # shutdown if there is a decrease in RPM
            if tach < (old_tach - 1000) and old_tach > 2000:  # added minimum RPM due to less reliable readings at extremely low RPM's
                print("Most recent RPM", tach, "less than previous RPM", old_tach, ", a difference of", old_tach - tach)
                mode = "flight_complete"
                print("Failed to accelerate properly")
                fault_code = 4
            if tach > old_tach:
                old_tach = tach
        if tach >= (rpm_setpoint - 200) and sample_count >= 5:  # PID transfer point
            setpoint_duty_cycle = esc_pwm.duty_cycle
            print("output us = ", servo_us(setpoint_duty_cycle), "output duty cylce = ", esc_pwm.duty_cycle, "=", tach, "RPM")  # prints the transfer point details
            motor_status = "run"  # now under PID control
            sample_count = 0
            old_tach = 0
            base_us = (servo_us(esc_pwm.duty_cycle))
            start_time = now
        if tach == 0 and now - last_time > (1.6 + (4/motor_acceleration_setting)):  # timeout limit if no RPM detected
            mode = "flight_complete"
            print("Failed to start")
            fault_code = 2
        if now - last_time > (5 + (20/motor_acceleration_setting)):  # timeout in case the RPM never reaches the transfer point
            mode = "flight_complete"
            print("Motor failed to reach full RPM")
            fault_code = 3

def check_ble():
    global mode
    if not ble.connected and not ble.advertising:  # advertise when not connected
        print("Advertising...")
        ble.start_advertising(advertisement)
    if ble.connected and not mode == "ble_programming":
        ble.stop_advertising()
        print("Connected")
        mode = "ble_programming"  # change to ble program mode

def send_text(file,first_line, last_line):
    if last_line == -1:
        last_line = len(file)
        first_line = len(file) - 1
    for item in file[first_line:(last_line + 1)]:
        uart_server.write(item.encode())  # writes text items

def update_strings():
    global menu_file
    # list of all the menu selection strings to display
    menu_file = list((
    "**** Climb_and_Dive Timer Settings ****\n\n",
    " 1) Start Delay Time .... {} seconds\n".format(delay_time),
    " 2) Flight Time ......... {} seconds\n".format(flight_time),
    " 3) RPM Setting ......... {} RPM\n".format(rpm_setpoint),
    " 4) Climb Gain .......... {} \n".format(climb_gain),
    " 5) Dive Gain ........... {} \n".format(dive_gain),
    " 6) Number of Motor Poles {} \n".format(number_of_poles),
    " 7) Motor Acceleration .. {} \n".format(motor_acceleration_setting),
    " 8) Last Lap Time ....... {} \n".format(last_lap_duration),
    " 9) Mounting Position ... {}, {}\n    & Calibration ....... {:.2f}, {:.2f}\n".format(axis_display_name[wing_axis], axis_display_name[fuse_axis], vert_axis_scale_factor, vert_axis_offset),  # v1.5 added calibration
    "10) Overhead Boost ...... {} \n".format(overhead_boost_setting),  # v1.3 added overhead boost
    "11) E-Stop .............. {} \n".format(estop_text[estop]),  # v1.5 added E-stop, display selection as text
    "12) Corner Boost Gain ... {} \n".format(corner_boost_gain),  # v1.5 added corner boost
    " 0) Save and EXIT\n",
    ))


def input_ble_settings(choice):
    global delay_time
    global flight_time
    global rpm_setpoint
    global climb_gain
    global dive_gain
    global number_of_poles
    global motor_acceleration_setting
    global last_lap_duration
    global orientation_step_1, orientation_step_2
    global calibration_step_1, calibration_step_2
    global wing_axis, fuse_axis, vert_axis, vert_axis_scale_factor, vert_axis_offset
    global overhead_boost_setting
    global estop
    global corner_boost_gain


    waiting_for_input = True  # flag to hold in new parameter input loop
    while waiting_for_input:
        if uart_server.in_waiting:  # incoming (RX) check for incoming text
            input_bytes = uart_server.read(uart_server.in_waiting)  # read text
            setting = input_bytes.decode().strip()  # strip linebreak
            print(setting)
            try_again = False
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
                if choice == 10:
                    new_setting = min(10, max(0, new_setting))  # constrain output, overhead boost setting 0 to 10
                    overhead_boost_setting = new_setting
                if choice == 11:
                    if new_setting in [0,1,2]:
                        new_setting = min(2, max(0, new_setting))  # constrain output, estop setting 0, 1 or 2
                        estop = new_setting
                        try_again = False
                    else:
                        send_text(prompt_file,-5,-4)
                        try_again = True
                if choice == 12:
                    if vert_axis_scale_factor == 0:
                        send_text(prompt_file,-7,-7)  # line space
                        waiting_for_input = False  # exit loop, go back to parameter selection
                    else:
                        new_setting = min(10, max(0, new_setting))  # contrain output, corner boost setting 0 to 10
                        corner_boost_gain = new_setting
                if choice == 9:
                    if orientation_step_1:
                        send_text(prompt_file,0,1)  # step 1
                        send_text(prompt_file,-6,-6)  # option to exit
                    if orientation_step_2:
                        send_text(prompt_file,2,3)  # step 2
                        send_text(prompt_file,-6,-6)  # option to exit
                    if calibration_step_1:
                        send_text(prompt_file,4,5)  # step 3
                        send_text(prompt_file,-6,-6)  # option to exit
                    if calibration_step_2:
                        send_text(prompt_file,6,7)  # step 4
                        send_text(prompt_file,-6,-6)  # option to exit
                if not orientation_step_1 and not orientation_step_2 and not calibration_step_1 and not calibration_step_2 and not try_again:
                    update_strings()  # make sure text files contain new parameter
                    send_text(prompt_file,-7,-7)  # line space
                    send_text(menu_file,1,len(menu_file))  # display new parameters
                    waiting_for_input = False  # exit loop, go back to parameter selection
            except ValueError:
                if choice == 9 and setting != "":
                    if orientation_step_1 and setting in "Ww":
                        temp_wing_axis = axis_orientation()
                        orientation_step_1 = False
                        send_text(prompt_file,2,3)  # move to step 2
                        send_text(prompt_file,-6,-6)
                        orientation_step_2 = True
                    if orientation_step_2 and setting in "Ff":
                        fuse_axis = axis_orientation()
                        wing_axis = temp_wing_axis
                        vert_axis = 6 - (abs(wing_axis) + abs(fuse_axis))  # determine vertical axis
                        orientation_step_2 = False
                        update_strings()  # make sure text files contain new parameters
                        calibration_step_1 = True
                        send_text(prompt_file,4,5)  # move to calibratiion step 1
                        send_text(prompt_file,-6,-6)
                    if calibration_step_1 and setting in "Uu":
                        point_1 = read_axis(axes[vert_axis-1])
                        print(point_1)
                        calibration_step_1 = False
                        send_text(prompt_file,6,7)  # move to calibration step 2
                        send_text(prompt_file,-6,-6)
                        calibration_step_2 = True
                    if calibration_step_2 and setting in "Ii":
                        point_2 = read_axis(axes[vert_axis-1])
                        print(point_2)
                        vert_axis_scale_factor, vert_axis_offset = calibrate(point_1, point_2)
                        calibration_step_2 = False
                        update_strings()  # make sure text files contain new parameters
                        send_text(prompt_file,-7,-7)  # line space
                        send_text(menu_file,1,len(menu_file))  # display new parameters
                        waiting_for_input = False  # exit loop, go back to parameter selection
                    elif (orientation_step_1 or orientation_step_2 or calibration_step_1 or calibration_step_2) and setting in "Xx":
                        orientation_step_1 = False
                        orientation_step_2 = False
                        calibration_step_1 = False
                        calibration_step_2 = False
                        send_text(prompt_file,-7,-7)  # line space
                        send_text(menu_file,1,len(menu_file))  # display new parameters
                        waiting_for_input = False  # exit loop, go back to parameter selection
                elif choice == 9 and (orientation_step_1 or orientation_step_2) and setting not in "WwFfXx":
                    print("orientation valueError")  # incorrect setting was entered by mistake
                    if orientation_step_1:
                        send_text(prompt_file,1,1)  # resend step 1
                        send_text(prompt_file,-6,-6)  # option to exit
                    if orientation_step_2:
                        send_text(prompt_file,3,3)  # resend step 2
                        send_text(prompt_file,-6,-6)  # option to exit
                elif choice == 9 and (calibration_step_1 or calibration_step_2) and setting not in "UuIiXx":
                    print("calibration valueError")  # incorrect setting was entered by mistake
                    if calibration_step_1:
                        send_text(prompt_file,5,5)  # resend step 3
                        send_text(prompt_file,-6,-6)  # option to exit
                    if calibration_step_2:
                        send_text(prompt_file,7,7)  # resend step 4
                        send_text(prompt_file,-6,-6)  # option to exit
                elif choice == 11:
                    send_text(prompt_file,-4,-4)  # re-enter selection
                elif choice == 12:
                    if vert_axis_scale_factor == 0:
                        send_text(prompt_file,-7,-7)  # line space
                        send_text(menu_file,1,len(menu_file))  # display new parameters
                        waiting_for_input = False  # exit loop, go back to parameter selection
                    else:
                        send_text(prompt_file,-2,-2)  # re-enter value
                else:  # all other cases
                    send_text(prompt_file,-2,-2)  # re-enter value


# Define digital filter:

# Filters computed at https://fiiir.com

# Filter Type: Low Pass, Windowed Sinc FIR
# Window type: Kaiser
# Sampling rate: 150Hz
# Cutoff freqency: 1.5Hz
# Transition bandwidth: 1.7Hz
# Stopband attenuation: 21dB
# Weighting Function: N/A
# Number of coefficients: 81

taps1 = np.array([
    0.004107233826136629,
    0.004568299107366780,
    0.005035127545733832,
    0.005506781542188349,
    0.005982302099982009,
    0.006460711293076683,
    0.006941014801796215,
    0.007422204508355161,
    0.007903261144690013,
    0.008383156984833282,
    0.008860858573909787,
    0.009335329485698457,
    0.009805533100592132,
    0.010270435395702739,
    0.010729007738800197,
    0.011180229677740685,
    0.011623091717033547,
    0.012056598073216263,
    0.012479769400753626,
    0.012891645480250251,
    0.013291287860864680,
    0.013677782448938516,
    0.014050242035004473,
    0.014407808751512962,
    0.014749656453816961,
    0.015074993017178927,
    0.015383062542810877,
    0.015673147466228377,
    0.015944570561490463,
    0.016196696835209488,
    0.016428935304546512,
    0.016640740653757920,
    0.016831614764226909,
    0.017001108113297247,
    0.017148821037626043,
    0.017274404857185066,
    0.017377562856465571,
    0.017458051119878183,
    0.017515679218785489,
    0.017550310748059635,
    0.017561863710518360,
    0.017550310748059635,
    0.017515679218785489,
    0.017458051119878183,
    0.017377562856465571,
    0.017274404857185066,
    0.017148821037626043,
    0.017001108113297247,
    0.016831614764226909,
    0.016640740653757920,
    0.016428935304546512,
    0.016196696835209488,
    0.015944570561490463,
    0.015673147466228377,
    0.015383062542810877,
    0.015074993017178927,
    0.014749656453816961,
    0.014407808751512962,
    0.014050242035004473,
    0.013677782448938516,
    0.013291287860864680,
    0.012891645480250251,
    0.012479769400753626,
    0.012056598073216263,
    0.011623091717033547,
    0.011180229677740685,
    0.010729007738800197,
    0.010270435395702739,
    0.009805533100592132,
    0.009335329485698457,
    0.008860858573909787,
    0.008383156984833282,
    0.007903261144690013,
    0.007422204508355161,
    0.006941014801796215,
    0.006460711293076683,
    0.005982302099982009,
    0.005506781542188349,
    0.005035127545733832,
    0.004568299107366780,
    0.004107233826136629,
])

# Create some text strings for menu inputs:

prompt_file = list((
"\nStep 1: Record wing to timer mounting orientation.  Point outboard wing down.\n",
"\nEnter W when ready ",
"\nStep 2: Record fuselage to timer mounting orientation.  Point the nose of the fuselage down.\n",
"\nEnter F when ready ",
"\nStep 3: Calibrate upright. Orient the airframe in an upright level flying position.\n",
"\nEnter U when ready ",
"\nStep 4: Calibrate inverted. Orient the airframe in an inverted level flying position.\n",
"\nEnter I when ready ",
"\nNOTICE: Timer Mounting Position & Calibration must be completed before Corner Boost can be used.\n\nEnter X to return to main menu\n",
"\n",
"or X to return to Main Menu\n",
"\n0 = OFF, 1 = TEST, 2 = ON\n",
"\nEnter selection #:\n",
" \nEnter item #:\n",
" \nEnter new setting:\n",
" \nParameters saved, OK to disconnect\n\n"
))

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
climb_threshold = 13
dive_threshold = 13
active_ouput_multiplier = 1.5
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
axes = [x_axis, y_axis, z_axis]  # v1.1 build list of accelerometer axes
wing_axis = 3  # default value, +3 == +z axis, can asign any axis based on the timer mounting orientation
fuse_axis = -1  # default value, -1 == -x axis, can assign any axis based on the timer mounting orientation
axis_display_name = {1: '+X', -1: '-X', 2: '+Y', -2: '-Y', 3: '+Z', -3: '-Z'}  # create dictionary of axis variable names cross referenced to their display names
orientation_step_1 = False
orientation_step_2 = False
calibration_step_1 = False
calibration_step_2 = False
last_lap_duration = 0  # default value
data_collection = False
overhead_boost_setting = 5  # default overhead boost setting
overhead_threshold = 1.2  # default threshold value for overhead boost
estop = 0
estop_text = ("OFF", "TEST", "ON")
old_tach = 0
corner_boost_gain = 0
vert_axis_scale_factor = 0.0  # default initial value prior to calibration
vert_axis_offset = 0.0  # default initial value prior to calibration


# Read saved parameters from non-volatile memory:

if nvm[0:6] ==  nvm[20:26] :  # if the parameters have never been saved before (brand new microcontroller), write all of the default parameters to memory
    save_parameters()
    print("New microcontroller, all default parameters saved")
if nvm[14:20] == nvm[20:26]:  # if updating to revision V1.2 (or higher) add memory items that have never been saved before, write only the new default values to memory
    array = pack('3h', last_lap_duration, wing_axis, fuse_axis)
    nvm[14:20] = array
    read_memory()
    print("Upgrade to v1.2, new default parameters saved")
if nvm[30:32] == nvm[20:22]:  # if updating to revision V1.3 (or higher) add memory items that have never been saved before, write only the new default values to memory
    array = pack('1h', overhead_boost_setting)
    nvm[30:32] = array
    read_memory()
    print("Upgrade to v1.3, new default parameters saved")
if nvm[32:40] == nvm[20:28]:  # if updating to revision V1.5 (or higher) add memory items that have never been saved before, write only the new default values to memory
    array = pack('4h', estop, corner_boost_gain, int(vert_axis_scale_factor * 1000), int(vert_axis_offset * 1000))  # note: only integers makes life easier
    nvm[32:40] = array
    read_memory()
    print("Upgrade to v1.5, new default parameters saved")
else:  # otherwise assign the saved data for use as the new current parameters
    read_memory()
    print("All parameters read from memory")


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
    neo_update1.send((WHITE, 0))
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

    try:
        now = monotonic()  # update current time
        touch.update()  # checks the debounced input pin status
        pushbutton.update()  # checks the optional debounced pushbutton status
        button = not pushbutton.value  # invert the pull-up pushbutton logic to match the touch pin
        main_count = 0  # clear previous short touch count
        n += 1
        # For testing use only - to print the average code loop time and frequency:
        #if n % 100 == 0:
            #loop_period = (1000/(now - oldtime))
            #loop_frequency = 1 / loop_period
            #print(loop_period, loop_frequency)
            #oldtime = now
            #print((touch_debounced.raw_value,))

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
                mode = "start_blip"  # normal way to exit this mode
                last_time = now  # start the timer for the start delay
                print("Now in", mode, "mode")
            if (main_count == 5):  # 5 short touches - enter the programming mode
                mode = "program_delay"  # alternate way to exit this mode
                print("Now in", mode, "mode")
                print("Current delay time is set to", delay_time, "seconds")

        if (mode == "start_blip"):
            neo_update1.send((RED, 0))
            esc_pwm.duty_cycle = servo_duty_cycle(blip_PWM)  # set throttle to a low RPM to indicate a start-up blip
            if (end_of_long_touch and (touch.value or button)):  # after the long touch used to enter this mode is over, any touch while in this mode will abort and return to standby
                esc_pwm.duty_cycle = servo_duty_cycle(idle_us)  # return throttle to idle
                mode = "standby"
                end_of_long_touch = False  # reset flag
                print("Now in", mode, "mode")
            if (now - last_time > blip_duration):  # after the programmed duration advance to the delay mode
                esc_pwm.duty_cycle = servo_duty_cycle(idle_us)  # return throttle to idle
                mode = "delay"
                last_time = now
                print("Now in", mode, "mode")


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
            update_strings()  # build the initial menu text strings
            while ble.connected and waiting:  # hold off on sending opening menu until user has UART window open and sends something
                if uart_server.in_waiting:  #  incomming (RX) waits for any incomming bytes
                    send_text(menu_file,0,len(menu_file)) # writes menu items
                    send_text(prompt_file,-3,-3)  # asks to select menu item
                    waiting = False  # exits the while loop
                    uart_server.reset_input_buffer()  # discards the first bytes received
            while ble.connected and not finished:
                if uart_server.in_waiting:  # Incoming (RX) check for incoming text
                    raw_bytes = uart_server.read(uart_server.in_waiting) # read text
                    selection = raw_bytes.decode().strip() # strip linebreak
                    try:
                        choice = int(selection)  # integers only
                        if (1 <= choice and choice <= 8):  # menu parameter selection
                            send_text(prompt_file,-7,-7)  # line space
                            send_text(menu_file,choice,choice)  # show selection
                            send_text(prompt_file,-2,-2)   # ask for new input
                            input_ble_settings(choice)  # new input function
                        if (choice ==10):  # menu parameter selection
                            send_text(prompt_file,-7,-7)  # line space
                            send_text(menu_file,choice,choice)  # show selection
                            send_text(prompt_file,-2,-2)   # ask for new input
                            input_ble_settings(choice)  # new input function
                        if (choice == 11):  # menu parameter selection
                            send_text(prompt_file,-7,-7)  # line space
                            send_text(menu_file,choice,choice)  # show selection
                            send_text(prompt_file,-5,-4)   # ask for new input
                            input_ble_settings(choice)  # new input function
                        if (choice == 12):  # menu parameter selection
                            if vert_axis_scale_factor == 0:
                                send_text(prompt_file,8,8)  # calibration must be completed before corner boost can be used
                                input_ble_settings(choice)  # new input function
                            else:
                                send_text(prompt_file,-7,-7)  # line space
                                send_text(menu_file,choice,choice)  # show selection
                                send_text(prompt_file,-2,-2)   # ask for new input
                                input_ble_settings(choice)  # new input function
                        if (choice == 9):
                            print("Start axis alignment & vertical axis calibration routine")
                            send_text(prompt_file,-7,-7)  # line space
                            send_text(menu_file,choice,choice)  # show selection
                            send_text(prompt_file,0,1)  # send instructions
                            send_text(prompt_file,-6,-6)  # option to exit
                            orientation_step_1 = True
                            input_ble_settings(choice)  # new input function
                        if choice == 0:  # menu EXIT selection
                            send_text(prompt_file,-1,-1)  # show exit text
                            save_parameters()  # save any changed parameters
                            mode = "standby"  # go back when finished with changes
                            finished = True  # exit ble programming loop
                        else:
                            send_text(prompt_file,-3,-3)  # re-enter index #
                    except ValueError:
                        send_text(prompt_file,-3,-3)  # re-enter index #
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
                esc_pwm.duty_cycle = servo_duty_cycle(1130)  # jump throttle ahead to reduce delay before motor starts to turn
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
            if (now - last_time >= 5) and (now - last_time < 10.5):  # trun on level lap data collection only between 5 and 10.5 seconds after take-off
                data_collection = True
            else:
                data_collection = False
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
            if (now - last_time) <= glide_boost:  # start burst of higher RPM at end of flight
                new_rpm_setpoint = rpm_setpoint + 1000  # increase RPM by 1000
            if (now - last_time) > glide_boost:  # end burst of higher RPM at end of flight
                new_rpm_setpoint = rpm_setpoint  # decrease the RPM back down to normal flight RPM
            pid_out = PID(base_us, new_rpm_setpoint)
            if pid_out == idle_us:
                mode = "flight_complete"
                print("Low RPM or Loss of RPM Signal Detected")
                fault_code = 1
            if pid_out is not None:
                esc_pwm.duty_cycle = servo_duty_cycle(pid_out)
            if (now - last_time) > (glide_boost + last_lap_duration):  # end of flight after any last lap time
                esc_pwm.duty_cycle = servo_duty_cycle(idle_us)  # set throttle to idle
                mode = "flight_complete"
                last_time = now
                print("Now in", mode, "mode")

        if (mode == "flight_complete"):  # used to latch the program in an endless loop to conclude the flight and stop the motor
            esc_pwm.duty_cycle = servo_duty_cycle(idle_us)
            neo_update1.send((BLANK, 0))
            while True:
                sleep(3)  # flash codes for auto-shutdown events, 1 for prop strike or loss of signal, 2 for failed start, 3 for failure to reach governed RPM setpoint
                if fault_code > 0:
                    flash(fault_code)
                pass
    except Exception as error:
        esc_pwm.duty_cycle = servo_duty_cycle(idle_us)
        neo_update1.send((MAGENTA, 0))
        print(error)
        while True:
            pass
