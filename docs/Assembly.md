---
title: Assembly
layout: default
nav_order: 2
---

## **Climb_and_Dive** ##
{: .text-blue-000}
{: .text-right}

## Bill of Materials ##

Complete project kits can be purchased on Tindie.  Each kit comes complete with the program code already installed and  the circuitboards fully tested.

If you prefer to purchase items separately here are some suggested sources:

| Qty | Description | Online Sources |
| :---: | ----------- | ------------- |
| 1 | Seed Studio Xiao nRF52840<br>(The cheaper one, not the 'Sense' version) | [Digikey][9]<br>[Mouser][10]<br>[Seeed Studio][11]  |
| 1 | Climb_and_Dive Backpack |  |
| 1 | Right Angle Header Strip, Single Row, 5 Position | [Mouser][5]<br>[Digikey][6]<br>[Sparkfun][3]<br>[Adafruit][4] |
| 1 | JST Battery Connector (Optional) | [HobbyTown][7]<br>[Amazon][8] |

## Tools Required ##

Electronic soldering equipment; soldering iron, flux and solder.  These are available from numerous sources online.  If you need to brush-up on your electronics soldering skills there are some good tutorials on [Adafruit][1] and [Sparkfun][2].

## Assembly ##

The boards as supplied include strips of breakaway header pins.  Solder as shown in the photos below.  Be careful to orient the boards correctly as shown.  The USB C port must be on the end opposite the ESC/Motor connection pins.


When connecting the ESC be sure the connector ground wire (brown or black) is attached to the ground pin on the board, labeled **GND**.  Connect the backpack motor pins to any two of the three motor wires.  For convenience I use a JST battery style connector (for reference: the correct manufacturers name is a JST-RYC connector).

![](assets/images/Climb_and_Dive Connection Diagram.png)

Solder

Solder

Now you can cut off the long header pins that you don't need.  Do *not* cut the touch pin, leave it sticking out.

{: .highlight }
Note: If you prefer, the program code does include provisions to use an *optional* push-button switch instead of the touch pin.  If you want to use a push-button switch it will connect to the timer using the 2 pins as shown below.  Depending how you want to connect your switch, you may want to leave those two pins sticking out as well.  The push-button switch will function exactly the same as the touch pin.

Installation

The flat bottom of the timer must be installed on a vertical part of the aircraft with the ESC/Motor connection pins pointing forward and the component side of the timer facing the pilot.  Although not super-critical, the long side of the timer should be installed so that it is horizontal when the aircraft is flying straight and level.  Calibration of the accelerometer is not required.

A couple of pieces of adhesive backed hook and loop fastener make quick work of mounting the timer in position.

[1]: https://learn.adafruit.com/adafruit-guide-excellent-soldering
[2]: https://learn.sparkfun.com/tutorials/how-to-solder-through-hole-soldering?_ga=2.264399628.2047829894.1668554338-987389297.1656854053
[3]: https://www.sparkfun.com/products/553
[4]: https://www.adafruit.com/product/1540
[5]: https://www.mouser.com/ProductDetail/Harwin/M20-9754046?qs=Jph8NoUxIfUFQh%2F79tzPcQ%3D%3D
[6]: https://www.digikey.com/en/products/detail/amphenol-cs-fci/68015-436HLF/1487576?s=N4IgTCBcDaIGwAYCcBaAzAFiQDhQOQBEACEAXQF8g
[7]: https://www.hobbytown.com/protek-rc-jst-male-connector-leads-2-ptk-5218/p23432
[8]: https://www.amazon.com/Silicone-Connector-SIM-NAT-Connectors/dp/B071XN7C43/ref=sr_1_16?crid=231ACQ422NRUB&keywords=jst+ryc&qid=1668614414&sprefix=jst+ryc%2Caps%2C89&sr=8-16
[9]: https://www.digikey.com/en/products/detail/seeed-technology-co-ltd/102010448/16652893?s=N4IgTCBcDaIIwFYCcB2AtHADGTWAseAHGgHIAiIAugL5A
[10]: https://www.mouser.com/ProductDetail/Seeed-Studio/102010448?qs=Znm5pLBrcAJ5g%252BWAkitg4w%3D%3D
[11]: https://www.seeedstudio.com/Seeed-XIAO-BLE-nRF52840-p-5201.html
