# Kontra AutoJump

A compact Windows desktop helper that holds a selected keyboard key until you turn it off.

## Features

- Toggle key holding with a configurable global hotkey (F6 by default).
- Configure the held key and hotkey in the app.
- Saves settings between launches.
- Releases the held key when disabled or when the app closes.
- Sends ordinary keyboard input; it does not inject code into a game or modify game files.

## Run from source

1. Install Python 3.10 or newer.
2. Open a terminal in this folder.
3. Run `py -m pip install -r requirements.txt`.
4. Run `py main.py`.

## Build a Windows EXE

Double-click `build.bat`. The executable will be created at `dist\Kontra AutoJump.exe`.

## Controls

- F6 by default: toggle holding the selected key.
- SPACE is the default held key.
- Close the app to release the held key.

Windows may show a security prompt for an unsigned executable. Only run builds you trust.
