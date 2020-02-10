# FACSvatar-Blender add-on (FACSvatar)
Blender 2.8x companion add-on to the [FACSvatar project](https://github.com/NumesSanguis/FACSvatar).
This add-on allows streaming of facial configuration and head pose data (from another computer) into Blender over ZeroMQ sockets,
**without** freezing the interface (publisher-subscriber pattern).

**Code working - *README in progress***

Standalone Blender-outside data transfer - BlendZMQ: https://github.com/NumesSanguis/Blender-ZMQ-add-on

## Update
- FACSvatar v0.4.0 branch - 2020-02-10 - **Blender 2.81+ pip support**: In Blender 2.81 pip is enabled by default.
This update takes that behavior into account. If the `Enable pip & install pyzmq` button fails, it still executes
`ensurepip.bootstrap()`. Restart Blender and try again, it will work this time
(on Windows make sure you run with admin rights).

## Overview
Blender is very powerful software, but if you run your own code that's a bit heavy, you quickly make the interface
unresponsive. I.e freezing the interface.
This could be solved with Threading/Async, however, this is difficult due Blender's internal loop (which is more like a game engine).
Also, in case of threading, you can't manipulate objects in the main loop of Blender without using e.g. a queue system.

Why not take the program logic and manipulation of data outside Blender, and possibly run heavy code on another PC?
Enter ZeroMQ.

ZeroMQ (`pyzmq` - Python wrapper of ZMQ) is a communication protocol library that allows the sending of data packages
between programs (even when written in different languages) by using sockets.
Therefore, the data can be send over the network (e.g. TCP), meaning you can even run the software on different machines.

This add-on works by setting a timer function (Blender 2.80+) that checks if a ZeroMQ socket has received
a message from outside (using `zmq.Poller()`). If so, process that data to move selected objects.
This timer keeps being invoked until the socket has been disconnected.
See for a demonstration:

[![BlendZMQ demo](https://img.youtube.com/vi/wGDdDCS3E1g/0.jpg)](https://youtu.be/wGDdDCS3E1g)


## Prerequisite
- FACSvatar: https://github.com/NumesSanguis/FACSvatar

## How to use
1. Download this repository as a .zip by:
   - Go to https://github.com/NumesSanguis/Blender-ZMQ-add-on/releases and download the ZIP, or
   - Clicking the green "Clone or download" button and choose "Download ZIP"
1. Start Blender with Administrator right (at least on Windows) to allow enabling of `pip` and installing `pyzmq`
(does NOT work with a Snap package install of Blender on Linux, see troubleshooting)
1. In Blender, add this add-on by selecting Edit -> Preferences -> Add-ons ->
   1. Install... -> select downloaded ZIP from step 1 -> Install Add-on
   1. Search: `blendzmq` -> click checkbox to activate
1. Open side panel in 3D view by
   - Pressing `n` on your keyboard
   - Dragging `<` to the left
1. Click "FACSvatar" -> "Enable pip & install pyzmq" button
1. Create a [MB-Lab character](https://mblab.dev/download/) (Use EEVEE engine), finalize it and select the character.
1. In the settings panel, go to `Modifier Properties` (blue wrench icon) -> `mbastlab_subdvision` ->
   Set Subdivisions: Viewport to `0` (for performance reasons) 
1. Click "Connect socket" button. Now it's waiting for data message from outside.
1. Follow the instructions over at [FACSvatar](https://github.com/NumesSanguis/FACSvatar) and send data to port 5572
   (the Quickstart automatically has this correct).
    
    
## Troubleshooting
- If Step 5 (enable pip & install `pyzmq`) does not work (e.g. `Couldn't activate pip.`),
link Blender to e.g. your `bzmq` conda environment:
https://docs.blender.org/api/current/info_tips_and_tricks.html#bundled-python-extensions


# Notes
- Blender Artists: https://blenderartists.org/t/blendzmq-open-source-add-on-streaming-data-into-blender-2-8x-without-freezing-the-interface/
- Gumroad: https://gumroad.com/l/blendzmq
- Blender add-on file structure inspired by btrace: https://github.com/sobotka/blender-addons/tree/master/btrace
- More information about ZeroMQ: https://zeromq.org/
- Why not make your outside Blender software easy to deploy, independent of OS?
Take a look at ZeroMQ with Docker: https://github.com/NumesSanguis/pyzmq-docker
- When developing Blender Add-ons, reload all add-ons without restarting Blender by executing: `bpy.ops.script.reload()`


# Acknowledgement
- dr.sybren (bunch of small questions)
- joules (multi-selection of previously selected objects)
- Other people at blender.chat, blender.stackexchange.com and the documentation
