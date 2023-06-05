---
title: Software
layout: default
nav_order: 3
---

## **Climb_and_Dive** ##
{: .text-blue-100}
{: .text-right}

## Software Installation ##

If you purchased a **Climb_and_Dive kit** complete with both boards, then the Xiao microcontroller board will come preloaded with the program code already installed and tested.  You can skip ahead to the Bluetooth app installation.  Although, when it comes to installing future program updates, it is advisable to read through the following section so that you are familiar with the programming procedure.

If you sourced your Seeed Studio Xiao nRF52840 from another provider you will have to follow **Steps 1 through 3** to install CircuitPython first before installing the program code and libraries.  Dont' worry, it's easy.

{: .highlight}
Always be sure to check back here from time to time to make sure you are using the most up to date version of the program code.  **Latest Version: v1.2**

<span class="fs-6">
[Click Here to download the latest program code .zip file](https://github.com/CircuitFlyer/Climb_and_Dive/archive/v1.2.0.zip){: .btn .btn-blue }
</span>

Unzip the download and have a look inside.  You should find a CircuitPython .uf2 file, code.py and a lib(rary) folder.

{: .highlight }
A quick note about USB C cables: If you have trouble getting the disk drive to show up on your computer there is a possibility you are not using a data cable.  There may be some USB cables that are used for charging only and are not data transfer cables.  Be sure you have the right one.

### Installing CircuitPython on a New Xiao nRF52840: ###

Connect the timer's Xiao circuit board to your computer using a USB C data cable.  It may look like nothing happened. Don't worry.  Follow this simple procedure to install CircuitPython and get the `CIRCUITPY` drive to appear.

**Step 1** - Enter Bootloader mode<br>
Before we install CircuitPython to the Seeed Studio XIAO nRF52840, it needs to be in bootloader mode. Enter the bootloader mode by clicking the very tiny Reset Button **twice**:

![](assets/images/XiaoBle.png)

Give it a couple of seconds, then the `XAIO-SENSE` disk drive will show up:

![](assets/images/Xiao-sense.png)

**Step 2** - Drag the CircuitPython .uf2 file that you downloaded and drop it onto the `XAIO-SENSE` drive.<br>

![](assets/images/Xiao-circuitpython.png)

**Step 3** - After 15 seconds or so, the disk drive will automatically exit bootloader mode and the name will change to `CIRCUITPY`.

![](assets/images/Xiao-circuitpy.png)

Congratulations, you have successfully installed CircuitPython.

### Installing the Program Code and Library Files: ###

With the timer connected to your computer and the `CIRCUITPY` drive available:

**Step 4** - Drag the complete lib folder that you downloaded and drop it onto the `CIRCUITPY` drive.  Your computer may ask if you want to replace the folder on the drive. Click **Replace**, don't keep the old one.  

**Step 5** - Next, drag and drop the code.py file onto the `CIRCUITPY` drive.  Again, your computer may ask if you want to replace the file on the drive. Click **Replace**, don't keep the old one.

![](assets/images/Code-circuitpy.png)

Congratulations, you should now have a Climb_and_Drive timer.  The LED on the Xiao should illuminate green to indicate that it's currently in Standby mode.

### Updating the Software: ###

If there are future updates to the program code, you will only need to complete **Step 5** to overwrite and replace just the (1) file called code.py. Replace it with the latest version of the same file.  If there is a major update, perhaps because a newer version of CircuitPython is released, then you will need to repeat all of **Steps 1 through 5** to update CircuitPython and replace all of the files and libraries.
