---
title: Timer Mounting Position
layout: default
parent: Operation
nav_order: 3
---

## **Climb_and_Dive** ##
{: .text-blue-100}
{: .text-right}

## Programming the Timer Mounting Position ##

### Description ###

The following instructions apply if you would like to install the timer on your airplane in an orientation other than the **default** mounting position described in the [assembly instructions](../Assembly#installation).  If you are using the default mounting position, the timer is already programmed with the default settings and is ready to use.

The programming procedure for this feature is slightly different than the other items in the Bluetooth programming menu so therefore warrant more detailed instructions.  This procedure only needs to be done once after mounting the timer in the airplane, or if you change the timer orientation for any reason.

**Overview**<br>
First, a brief explanation of why this is necessary.  The accelerometer used by the timer actually has (3) separate accelerometers inside.  Each measurement axis is orientated 90 degrees to each other.  In addition, each measurement axis has a positive and negative direction.

![](assets/images/Accelerometer Axes.png)

It is imperative that the timer uses the correct measurement axis and direction for the active output calculations.  If the timer is installed in a different orientation with respect to the wings and fuselage of the airplane, the timer will need to be reprogrammed to tell it which measurement axes to use.

The timer can be installed in any position.  Although, it still must be installed so that the sides and edges of the timer are aligned with the major axes of the airplane.  The timer *cannot* be mounted askew, tilted or at an angle to the wing and fuselage axes.

**Programming**<br>
Programming the timer to tell it which accelerometer axes to use is a two step process.  

{: .highlight }
Safety first: You are about to connect the battery to power-up the airplane.  Although you will only enter the Bluetooth programming mode, for maximum safety remove the propeller or get someone to securely hold the airplane at all times.

With the timer installed in the airplane, power it up and enter the Bluetooth programming mode.  From the menu selections choose the Mounting Position option.

![](assets/images/Bluefruit 7.png)

**Step 1**<br>
Follow the onscreen prompt and hold the airplane with the outboard wing pointing down (leadouts pointing up to the sky).  When you are ready, enter the letter "W" to tell the timer this is the accelerometer axis you want to use for the wing axis.  There is also an option to enter "X" if you want to exit the procedure and return to the main menu without making and changes.

![](assets/images/Bluefruit 8.png)

**Step 2**<br>
Next, the prompt will ask you to rotate the airplane so that the fuselage is vertical with the nose pointed down and the rudder pointing up to the sky.  When you are ready, enter the letter "F" to tell the timer this is the accelerometer axis you want to use for the fuselage axis.  Again, there is also an option to enter "X" if you want to exit the procedure and return to the main menu without making any changes.

![](assets/images/Bluefruit 9.png)

**Results**<br>
The menu will reappear showing the new accelerometer axes assigned to the airplanes wing and fuselage axes.  The **default orientation** of the timer uses the +Z axis assigned to the wing axis and the -X axis assigned to the fuselage axis.  All other mounting orientations will use a different combination of axes and signs.

Be sure to **save** the new programming settings when you disconnect and exit the Bluetooth programming mode.
