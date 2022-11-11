---
title: Power System Information
layout: default
nav_order: 5
---

## **Climb_and_Dive** ##
{: .text-blue-000}
{: .text-right}

## ESC Information ##

The details of how to program the your ESC is outside the scope of these instructions.  Please refer to your ESC instruction manual for information.

As a reference guide, use the following table for suggested settings for ESC programming.

{: .highlight }
Note: The features described may or may *not* be present in the ESC you are using.

| ESC Programmable Feature | Recommended Setting |
| --- | :---: |
| RPM Governing | OFF |
| Brake setting | ON |
| Soft start | OFF |
| BEC Voltage Output | 5.0V or 5.5V Maximum |


The timer PWM signal covers a very wide throttle range and ESC throttle calibration is not likely required.  If you think your ESC requires throttle calibration and your instructions call for the RC transmitter stick to be at maximum throttle at power-up:

1. **For maximum safety**, remove the propeller from the motor.
2. Hold the timer touch pin and connect the battery power.  The timer will then output a maximum throttle signal.
3. After the ESC is calibrated, release the timer touch pin.  The timer output will return to minimum throttle and the ESC should arm.
4. Disconnect the battery and re-install the propeller.

## Motor Information ##

In order for the timer to accurately determine the motor RPM you must know the number of magnetic poles used in your motor.  14 poles if the default choice but some motors use a different number.  You can find the number of magnet poles used in you motor documentation or by counting the number of magnet segments glued around the inside of the rotating part of the motor.  Be sure *not* to count the number of stationary copper windings.

Please refer to the timer Bluetooth programming section for where to enter this information.
