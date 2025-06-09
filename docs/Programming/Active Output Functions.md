---
title: Active Output Functions
layout: default
parent: Operation
nav_order: 4
---

{% include Header.html %}

## Active Output Functions ##

The use of an electronic aid to actively control the motor RPM during flight can be a very useful feature. The general idea behind the active function is to assist the aircraft to try and maintain a more constant velocity throughout the entire flight.  The timer can boost the motor RPM in a climb and reduce it in a dive. It can also add RPM when flying high overhead to get a little more line tension when needed.  The design intent of the Climb_and_Dive timer is to keep the integration of the active function simple to use and easy to understand.

{: .highlight}
**Note:** An important requirement of the Climb_and_Dive timer is to avoid starting any stunt maneuvers until after the completion of 2-3 laps of normal level flight after take-off. There are a couple of reasons for this requirement:<br><br>
**1)** The active output is suppressed for the first 5 seconds after take-off. This is necessary in order to allow the aircraft unhindered acceleration to reach a stable cruising speed. Therefore, **do not hold the running airplane for extended periods before releasing for take-off.**<br><br>
**2)** For the time period between 5 seconds and 10 seconds after take-off, the timer is collecting accelerometer readings for use in a self correction procedure. Approximately one full lap of data collection is needed to account for different wind conditions. This self correction takes place each flight and allows changing lap times (different propellers, motor RPM or line length) without having to go back and alter any active function settings.

A good practice to follow is to turn off all active output aids while test flying and trimming a brand new airplane. Set the Climb Gain, Dive Gain, Overhead Boost and Corner Boost values to 0.  In this configuration the timer acts as a governing timer only.  The RPM will be held constant at the programmed setpoint throughout the entire flight.  After following the standard trimming procedures to achieve the best flying airplane, then it’s time to start to experiment and incrementally add the active outputs as desired.

Climb Gain is used to boost the RPM when the airplane is increasing in altitude.  The output of the active function is proportional to the rate of change in altitude.  For example, in a wingover the boost comes on gradually and the maximum RPM due to the Climb Gain will occur around 45º and then taper off as it reaches the top of the hemisphere.

Dive Gain works in a similar manner with the RPM starting to decrease from the setpoint as it goes over the top and then reaches the maximum decrease in RPM at the exit of the maneuver.

The Overhead Boost function is used to add extra RPM when flying overhead.  It will gradually come on above 45º in altitude and reach its maximum boost directly overhead.  It works best in conjunction with some Climb Gain and can help give a more confident increase in line tension for maneuvers like the overhead figure eight.

The corner boost function is used to add extra RPM when the airplane experiences high g loads in sharp corners.  The altitude that the corner boost is active is restricted to the lower bottom corners of maneuvers only.  It is active when pulling up into a climb and pulling out of a dive for both inside and outside turns.  This boost aids in keeping a more constant velocity throughout the maneuver.

The optimal settings for each parameter are largely a matter of personal preference. That said, there is also a reasonable consensus that the active output could be overused so be careful not to overdo it. Adjustment of the parameters is an experimental process that takes place over several test flights tailored to your particular aircraft and flying style.

One suggested strategy to find your preferred settings is to start with all active functions set to 0.  Adjust the governed RPM setting to yield a lap time that you find the most comfortable.  After that, the next step is to incrementally add Overhead Boost.  When satisfied, then add Climb gain and Dive gain in equal amounts to help maintain a more constant velocity in the maneuvers.  Lastly, add in some corner boost to help reduce the loss of speed in sharp corners.  Finally, go back and re-adjust each parameter, including the governed RPM setting if necessary, to best suit your airplane and flying style.
