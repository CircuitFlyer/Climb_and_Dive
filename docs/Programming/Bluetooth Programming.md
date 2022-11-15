---
title: Bluetooth Programming
layout: default
parent: Operation
nav_order: 1
---

## **Climb_and_Dive** ##
{: .text-blue-000}
{: .text-right}

## Bluetooth Programming Instructions ##

There are several features of the the timer that you can customize based on a user programmable setting.

**Start Delay Time**<br>
The start delay is programmable from 0 to 60 seconds in 1 second intervals.  This is the delay time between starting the timer and when the motor starts.

**Flight Time**<br>
The flight time can be set from 1 second to 360 seconds (6 minutes) in 1 second intervals.  This time begins when the motor reaches full flight RPM and lasts until the 3 second period of increased RPM just before the motor stops at the end of the flight.

**Motor RPM**<br>
The governed RPM can be set from 5000 RPM to 15000 RPM in 10 RPM increments.  This setting is the base RPM (or setpoint) that the PID control loop inside the timer will use to control the ESC. This control loop will work to maintain a constant RPM throughout the flight even as the battery voltage decreases.

**Climb Gain**<br>
The climb gain is an arbitrary multiplier with a value from 0 through 10 (integer values only).  This number is used to multiply the output of the accelerometer reading and adds the results to the setpoint to increase the RPM slightly when the model is in a climb.  0 turns off the accelerometer input and a setting of 10 would be the maximum RPM boost possible.  Most pilots will likely use a setting between 4 and 6.

**Dive Gain**<br>
The climb gain is an arbitrary multiplier with a value from 0 through 10 (integer values only).  This number is used to multiply the output of the accelerometer reading and subtracts the results from the setpoint to decrease the RPM slightly when the model is in a dive.  0 turns off the accelerometer input and a setting of 10 would be the maximum braking effect possible.  Most pilots will likely use a setting between 4 and 6.

**Motor Acceleration**<br>
The motor acceleration is an arbitrary multiplier with a value from 1 through 10 (integer values only).  This number is used to adjust the amount of time that the motor takes to startup at take-of; from 0 RPM to the programmed setpoint RPM.   A setting of 1 is a very slow acceleration of the motor RPM and a setting of 10 is a very quick startup.

**Number of Motor Poles**<br>
Enter the number of magnetic poles used in your motor.  The timer needs this information in order to accurately calculate the RPM.  The number of magnetic poles  can be found in you motor documentation or by counting the number of magnet segments glued around the inside of the rotating part of the motor.

The table below summarizes the programmable settings available and the default values:

| Programmable Setting | Allowable Range | Default Setting |
| --- | :---: | :---: |
| Start Delay Time | 0 to 60 | 10 Seconds |
| Flight Time | 1 to 360 | 180 Seconds |
| Motor RPM | 5000 to 15000 | 10000 |
| Climb Gain | 0 to 10 | 5 |
| Dive Gain | 0 to 10 | 5 |
| Motor Acceleration | 1 to 10 | 5 |
| Number of Motor Poles | 2 to 24 | 14 |

Connect the battery and boot up the timer. Tap your finger on the touch pin 5 times. The LED should turn a steady YELLOW (Programming mode, or more specifically Program Start Delay mode).

Open the Bluefruit Connect app on your phone. Give it a second to search for the timer and the Climb & Dive timer should show up.

![](assets/images/Bluefruit 1.png)

![](assets/images/Bluefruit 2.png)

![](assets/images/Bluefruit 3.png)
