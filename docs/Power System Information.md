---
title: Power System Information
layout: default
nav_order: 6
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

{: .highlight }
Note: Castle Creations Phoenix ESC's are more intricate and discussed in greater detail [below](Power%20System%20Information.html#castle-creations).


The timer PWM signal covers a very wide throttle range and ESC throttle calibration is not likely required.  If you think your ESC requires throttle calibration and your instructions call for the RC transmitter stick to be at maximum throttle at power-up, use the following procedure:

**Step 1** - **Remove the propeller from the motor.**<br>
**Step 2** - Hold the timer touch pin while connecting the battery power.  The timer will start up and output a maximum throttle signal.<br>
**Step 3** - After the ESC is calibrated, release the timer touch pin.  The timer output will return to minimum throttle and the ESC should arm.<br>
**Step 4** - Disconnect the battery and re-install the propeller.

## Motor Information ##

In order for the timer to accurately determine the motor RPM you must know the number of magnetic poles used in your motor.  14 poles is the default choice but some motors use a different number.  The number of magnetic poles  can be found in you motor documentation or by counting the number of magnet segments glued around the inside of the rotating part of the motor.  Be sure ***not*** to count the number of stationary copper windings.

Please refer to the timer Bluetooth programming section for information on where to enter this information.

## Castle Creations ##

The Castle Creations Phoenix line of ESC's have additional complexity and warrant a separate discussion.  A Castle Link USB device and the associated software is required to upload the necessary adjustments to the ESC to make it compatible for use with the Climb_and_Dive timer.

The Throttle must be setup to use **Multi-Rotor** as the Vehicle Type.  Do *not* use Control Line as a Vehicle Type.  The governor function of the Climb_and_Dive *timer* must be allowed complete control of the throttle; free from any output delay or input filtering within the ESC.  The Airplane Vehicle Type is also *not* a viable option.  Primarily due to the lack of a procedure to match the ESC throttle range to the timers fixed outputs.  Both Helicopter and External Governor types do *not* have braking enabled.

The Brake should be set to 100%.  The amount of Brake Delay and Brake Ramp can be adjusted to suit your requirements.

Cutoffs are another setting that are subject to personal preferences.  The Cutoff Voltage (and/or Auto-Lipo Volts/Cell) may be set to values suggested by your battery manufacturer.  (Low) Voltage Cutoff Type is debatable.  When using a control line timer, the obvious choice is an immediate Hard Cutoff.  The Climb_and_Dive timer in use with a Phoenix ESC does allow choosing the Soft Cutoff option.  When the low voltage limit is reached using a Soft Cutoff the RPM will slowly decrease.  When the RPM decreases to 75% of the programmed flight RPM the timer will automatically shutdown. Pulse Cutoff and RPM Reduction Cutoff are *not* viable choices.

The Current Limiting value is your choice.  For Current Cutoff Type, Hard Cutoff is strongly suggested.

Motor Start Power is not that important for most control line models.  It has no bearing on the operation of the timer and can be set to your liking.  The other Motor settings are motor dependent and have very little influence on the operation of the timer.

BEC Voltage must be set to 5.0V.


[1]: https://circuitflyer.com/electric%20power%20system%20101.html
