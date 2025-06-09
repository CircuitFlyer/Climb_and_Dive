---
title: Safety Features
layout: default
parent: Operation
nav_order: 6
---

{% include Header.html %}

## Built-in Safety Features ##

The timer is programmed to automatically shutdown the motor and jump to the Flight Complete mode if certain fault conditions are detected.  After the motor stops the onboard LED will flash a number of times every 3 seconds to indicate which fault occurred.

{: .warning }
SAFETY FIRST!  While the timer code does include some safety features to help protect the power system, these features do not cover *all* potential problems.  Always use extra caution whenever the battery is connected and something unexpected occurs.

**1 Red Flash**<br>
The motor RPM unexpectedly drops too low.  This can happen if the prop comes in contact with something, i.e. a crash or prop strike, or if the battery voltage drops very low.  This can also occur if there is a poor, or intermittent, electrical connection with the voltage sensing wires to the timer.

**2 Red Flashes**<br>
The motor fails to start properly and/or the timer cannot detect any RPM.  This can happen if there is a poor electrical connection to the ESC or with the voltage sensing wires to the timer. Make sure any ESC "soft start" is OFF.

**3 Red Flashes**<br>
The motor fails to reach the assigned governing RPM.  The motor will operate for a very short period of time but if it cannot attain the desired RPM it will shut down.  This can happen if the battery voltage is too low or if the motor/prop combination is not capable of reaching the set RPM.

{: .highlight}
It is very important to make sure your power system can achieve the desired RPM before programming the timer.

**4 Red Flashes**<br>
At motor start-up the RPM did not increase smoothly. This fault would likely occur because of a nose-over or due to a mechanical issue preventing the motor from rotating.
