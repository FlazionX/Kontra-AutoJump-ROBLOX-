# Kontra AutoJump

A compact Windows helper for Roblox that repeatedly taps Space while the user physically holds Space.

## Features

- Click **Start**, focus Roblox, then hold Space to trigger repeated short Space taps.
- Releasing Space stops the repeated taps.
- Adjustable interval from 100 to 1500 ms (default: 450 ms).
- Saves the selected interval in the user's AppData settings folder.
- Uses ordinary Windows keyboard input; it does not inject code into Roblox or modify game files.

## Run from source

1. Install Python 3.10 or newer.
2. Run `py -m pip install -r requirements.txt`.
3. Run `py main.py`.

## Build a Windows EXE

Double-click `build.bat`. The executable will be created at `dist\Kontra AutoJump.exe`.

## Roblox timing note

Roblox does not define one universal jump interval. Each experience can implement its own jump cooldown. The default 450 ms is a starting point, not a guaranteed game-wide timing. Adjust it in the app if the experience needs a slower or faster cadence. The app cannot read the character's actual grounded/jump-ready state from outside the game.
