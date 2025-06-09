---
title: Emergency Stop
layout: default
parent: Operation
nav_order: 5
---

{% include Header.html %}

## Emergency Stop ##
This is an entirely new concept introduced in v1.5 and I hope users find it helpful.

The traditional control line flight profile ignores the glaring safety concern of the lack of ability to stop the flight at any time when the situation is warranted.  This new E-stop feature allows the pilot to initiate a stop signal to the timer by simply pulling on the control handle three times.  No awkward radio control transmitters or receiver installations are required.

During a “pull” on the control handle the aircraft moves sideways toward the centre of the circle.  During this time the accelerometer reading increases well beyond any reading that occurs during normal acrobatic maneuvers.  Taking advantage of this fact, the timer is programmed to use a form of gesture recognition to identify 3 consecutive pulls on the handle.  When the timer successfully identifies the third pull it will immediately stop the motor.

This is an optional feature and by default is turned **OFF** in the settings.  When turned **OFF** any lateral acceleration of the airplane is ignored.

The physical requirements of the three consecutive pulls are somewhat specific.  Too slow or too fast and the pull may not register and be counted.  To that end, the settings allow for a testing mode.  With the E-stop feature set to **TEST**, the timer will initiate a short *increase* in RPM when it successfully identifies the stop command.  This allows the pilot to learn how the system works and get a feel for the proper timing of the 3 consecutive pulls without having to land, restart and takeoff again.  In this mode the E-stop feature will *not* stop the motor.

When the E-stop feature is fully active in the **ON** position it will stop the motor and terminate the flight when the timer successfully identifies the 3 consecutive pulls.

While primarily intended for emergency use, it can be used to shorten the flight and land at any time.  This could be helpful when training, trimming a new airplane or setting up for a spot landing.

**Helpfull hints:**<br>
The successful activation of the shutdown is very dependent on the pilot movement of the handle.  Some practice may be required to get a feel for the correct timing of the pull sequence.   10-12 inches of travel at the handle should suffice.  All three pulls should occur within 2 to 2 1/2 seconds (approximately 1/3 a circle flying distance).   Most airplanes will yaw back a forth a small amount as it moves inward and then flies back outward.  Initiating the pull sequence downwind is ideal and can aid in helping the airplane fly outward between pulls. **Note:** the E-stop feature is dependent on the timer active output therefore E-stop is not available until 5 seconds after take-off.
