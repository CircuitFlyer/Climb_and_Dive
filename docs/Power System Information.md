---
title: Power System Information
layout: default
nav_order: 5
---

## **Climb_and_Dive** ##
{: .text-blue-100}
{: .text-right}

## ESC Information ##

The details of how to program your ESC (electronic speed controller) is outside the scope of these instructions.  Please refer to your ESC instruction manual for information.  If you are completely new to how electric control line power systems work, a brief overview can be found [here][1].

As a reference guide, use the following table for suggested settings for ESC programming.

{: .highlight }
Note: The features described may or may *not* be present in the ESC you are using.

| ESC Programmable Feature | Recommended Setting |
| --- | :---: |
| RPM Governing | OFF |
| Brake setting | ON |
| Soft start | OFF |
| BEC Voltage Output | 5.0V or 5.5V Maximum |


The timer PWM signal covers a very wide throttle range and ESC throttle calibration is not likely required.  If you think your ESC requires throttle calibration and your instructions call for the RC transmitter stick to be at maximum throttle at power-up, use the following procedure:

**Step 1** - **Remove the propeller from the motor.**<br>
**Step 2** - Hold the timer touch pin while connecting the battery power.  The timer will start up and output a maximum throttle signal.<br>
**Step 3** - After the ESC is calibrated, release the timer touch pin.  The timer output will return to minimum throttle and the ESC should arm.<br>
**Step 4** - Disconnect the battery and re-install the propeller.

## Motor Information ##

In order for the timer to accurately determine the motor RPM you must know the number of magnetic poles used in your motor.  14 poles is the default choice but some motors use a different number.  The number of magnetic poles  can be found in you motor documentation or by counting the number of magnet segments glued around the inside of the rotating part of the motor.  Be sure ***not*** to count the number of stationary copper windings.

Please refer to the timer Bluetooth programming section for information on where to enter this information.

[1]: https://circuitflyer.com/electric%20power%20system%20101.html
