---
title: Operation
layout: default
nav_order: 6
---

## **Climb_and_Dive** ##
{: .text-blue-000}
{: .text-right}

## Operating Instructions ##

Note, leave sone head room on RPM
Lack of blip? see ESC throttle calibration


Install and connect the ESC as discussed in the assembly instructions.

The tri-colour LED is used to communicate the different modes of operation.  The capacitive touch pin is used for operator input.  This is similar to the touch sensitive screen on a smart-phone.  (Hint: As the conductivity of the average fingertip can vary, adding a bit of moisture to your fingertip will greatly improve the touch response.)

A long touch is a sustained touch for a minimum of 3 seconds.  A tap, or series of taps, is a single or multiple quick taps on the pin.  You will notice a 1 second delay after the last tap before the desired action takes place.  This short waiting period is needed to make sure all of the taps are complete.

When you connect the battery to the ESC the timer will boot-up and the tri-colour LED will turn green (Standby Mode).  At this point the board will output an “idle” signal to the ESC.  The ESC should complete its initialization and arming sequence.
The very first time the board is powered up it will load the default settings.

| Programmable Setting | Allowable Range | Default Setting |
| --- | :---: | :---: |
| Start Delay Time | 0 to x | 10 Seconds |
| Flight Time | 1 to 300 | 180 Seconds |
| Motor RPM | 3500 to 15000 | 10000 |
| Climb Gain | 0 to 10 | 5 |
| Dive Gain | 0 to 10 | 5 |
| Motor Acceleration | 1 to 10 | 5 |
| Number of Motor Poles | 2 to 20 | 14 |

{: .warning }
SAFETY FIRST!  Any time the battery is connected stay clear of the prop.  The aircraft should always be held or secured until the pilot is ready.  When the flight ends the pilot should wait until his/her helper disconnects the battery before putting the handle down.

When ready, touch and hold the pin (a long touch of a minimum of 3 seconds), the motor will spin up at a low RPM for a second and then stop.  The timer will now be in the Start Delay mode (flashing blue).  This indicates the start of the countdown timer before the motor starts.  During the last 5 seconds of the countdown the LED will change to white and flash quickly to warn of the impending startup of the motor.  Any touch of the pin during the Start Delay mode will stop the countdown and return to the Standby mode.

After the Start Delay the Flight mode will start (flashing red) and the motor RPM will slowly increase to the desired flight RPM at the programmed rate.  This will assist with a smooth take-off.  After the motor starts any touch of the pin will stop the motor and jump to the Flight Complete mode (LED off). 10 seconds before the Flight mode is complete the LED will quickly flash white to indicate the end of the flight.  The motor RPM will then increase for 3 seconds before stopping to aid in a smooth approach and landing.  Once the motor stops the program enters the Flight Complete mode (LED off).  The power must be reset in order to exit the Flight Complete mode.

Disconnect the battery, replace it with a fully charge one and repeat the process for the next flight
