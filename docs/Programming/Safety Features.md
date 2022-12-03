---
title: Safety Features
layout: default
parent: Operation
nav_order: 3
---

## **Climb_and_Dive** ##
{: .text-blue-100}
{: .text-right}

## Built-in Safety Features ##

The timer is programmed to automatically shutdown the motor and jump to the Flight Complete mode if certain fault conditions are detected.  After the motor stops the onboard LED will flash a number of times every 3 seconds to indicate which fault occurred.

{: .warning }
SAFETY FIRST!  While the timer code does include some safety features to help protect the power system, these features do not cover *all* potential problems.  Always use extra caution whenever the battery is connected and something unexpected occurs.

**1 Red Flash**<br>
The motor RPM unexpectedly drops too low.  This can happen if the prop comes in contact with something, i.e. a crash or nose-over, or if the battery voltage drops very low.

**2 Red Flashes**<br>
The motor fails to start properly.  This can happen if there is a poor electrical connection to the ESC or with the voltage sensing wires to the timer.  This could also happen due to a mechanical issue preventing the motor from rotating.

**3 Red Flashes**<br>
The motor fails to reach the assigned governing RPM.  The motor will operate for a very short period of time but if it cannot attain the desired RPM it will shut down.  This can happen if the battery voltage is too low or if the motor/prop combination is not capable of reaching the set RPM.

{: .highlight}
It is very important to make sure your power system can achieve the desired RPM before programming the timer.
