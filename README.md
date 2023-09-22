#dbus-serialbattery-gui

This is a graphical user interface (GUI) for configuring and managing dbus-serialbattery https://louisvdw.github.io/dbus-serialbattery/

Currently for linux only tested on *buntu 20.10 using python3

In progress:

Will eventually release as AppImage if desired. Mostly created so I can edit the config file quicker. 


Features

- Load and edit local configuration files.
- Pull configuration files from a remote host.
- Push local configuration files to a remote host.
- Configure SSH settings for remote file operations.
- Restart dbus-serialbattery remotely.

Prerequisites

- Python 3.x installed on your system.
- PyQt5 library installed (pip install PyQt5).
- Paramiko library installed (pip install paramiko).
