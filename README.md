# dbus-serialbattery-gui

![dbus-serialbattery-gui](images/screenshots/gui.png)

This is a graphical user interface (GUI) for configuring and managing dbus-serialbattery https://louisvdw.github.io/dbus-serialbattery/

Linux only for now, tested on *buntu 20.10.

Features

- Load and edit local configuration files.
- Pull configuration files from a remote host.
- Push local configuration files to a remote host.
- Configure SSH settings for remote file operations.
- Restart dbus-serialbattery remotely.

Requires

- Python 3.x installed on your system.
- PyQt5 library installed (pip install PyQt5).
- Paramiko library installed (pip install paramiko).

Steps

1. Clone the repository to your local machine:

   git clone https://github.com/yourusername/dbus-serialbattery-gui.git

2. Navigate to the project directory:

   cd dbus-serialbattery-gui

3. Install requirments

   Using apt-get:
   sudo apt-get update
   sudo apt-get install python3 python3-pyqt5 python3-paramiko

   Using pip3:
   pip3 install -r requirements.txt

4. Run the application:

   python3 dbus-serialbattery-gui.py
