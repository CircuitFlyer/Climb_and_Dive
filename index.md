---
title: Home
layout: home
nav_order: 1
---

## **Climb_and_Dive** ##
{: .text-blue-100}
{: .text-right}

## Overview ##

Climb_and_Dive is an open source do-it-yourself project to create your own advanced timer for an electric powered control line model aircraft.  Utilizing a low cost popular microcontroller development board coupled to an add-on circuit board the timer is compact, simple to use and packed with features.

You may have heard of a governing timer.  You may have heard of an active timer.  The Climb_and_Dive timer is both, an active & governing timer.  On top of that, it can be wirelessly programmed via a Bluetooth connection on a smart phone!  No more opening hatches, fiddling with connectors or programming boxes.  Because it’s open source, you can customize the functionality to your liking or even add some new features.

The timer is available as a DIY kit that only requires soldering some header pins to assemble.  The kit consists of two major parts, the Seeed Studio Xiao NRF52840 development board and an additional circuit board, sometimes referred to as a backpack. The backpack contains the accelerometer and RPM signal conditioning circuitry that makes wiring and assembly fast and easy.

Programming the microcontroller is as easy as dragging and dropping a few files on your computer.  The program code also includes a few features that can add an additional layer of safety to protect your power system in case something doesn't go as expected.

<span class="fs-6">
[Click Here to order a **Climb_and_Dive** kit on Tindie](https://www.tindie.com/products/28568/){: .btn .btn-green}
</span>

## List of Features ##

- Dimensions: 27mm x 18mm x 9mm.  Weight: 5g

- Capacitive touch sensor for user input.  No additional switches or buttons to wire and mount.  Although, if desired, the program code does allow for use with an optional remote pushbutton.

- Onboard multicolour LED to indicate the status of the timer.

- Wireless programming in the field via a *free* Bluetooth app using a laptop, tablet or smart phone. The start-up delay, flight time and governed RPM settings plus a lot more more can be changed without any extra tools, cards or programming boxes.

- Programmable soft start.  The RPM increases over a programmable time period for smoother take-offs.

- A 3 second boost in RPM at the conclusion of a flight to improve the landing glide.

- An onboard accelerometer provides a programmable active boost in power during a climb as well as a decrease in power in a dive.  Accelerometer calibration is not required.

- Constant RPM throughout the flight is maintained by sensing the motor voltage using a PID feedback loop.  No need for a tachometer.  The RPM number you program is the RPM you get at the propeller.

- Works with lower cost ESC’s.  The governing function takes place in the timer so expensive governing ESC’s are not required.

- Power to the motor is cut off quickly and automatically if the propeller inadvertently strikes the ground.  No more burned out motors or ESC’s from a crash or nose-over on takeoff.

- Auto shutdown with a loss of power or a loss of motor RPM signal.

- Auto shutdown if motor fails to reach programmed RPM on takeoff.

- For added safety, a pilot initiated shutdown can be triggered at any time during the flight by repeatedly pulling on the handle.  (Note: This feature is considered experimental and still under development).

- Should an auto shutdown occur, the onboard LED will flash a sequence of fault codes to aid in troubleshooting.

- Built-in micro USB C port.  Plug it into your computer and it shows up as a small disk drive.   This makes it very easy to keep the software up to date with the latest revisions.

- The program code is written in Adafruit CircuitPython.  CircuitPython is an easy to read and easy to learn language well supported by comprehensive learning guides on the Adafruit website.

- Reprogrammable.  Have another project idea in mind?  The Xiao line of development boards have the same footprint and pinouts as the Adafruit QTPy size of boards.  The Climb_and_Dive hardware platform is also a great starting point to use in developing code for your own project.  It can also be programmed as an Arduino device if you prefer.
