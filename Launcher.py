"""
SMW Launcher
============
Double-click this (or its compiled .exe) to launch:
    data/snes9x.exe  data/ROM.smc

Folder layout expected next to this launcher:
    SMW Launcher.exe   (this program, once compiled)
    data/
        snes9x.exe
        ROM.smc
        snes9x.conf   <- created by Snes9x itself once you've configured
                          "Hide Menubar" and cleared hotkeys inside it

Build into a standalone .exe with PyInstaller:
    pip install pyinstaller
    pyinstaller --onefile --noconsole --name "SMW Launcher" launcher.py

Then take the resulting dist/SMW Launcher.exe and place it as a SIBLING
of the "data" folder (NOT inside it):

    MyGame/
        SMW Launcher.exe
        data/
            snes9x.exe
            ROM.smc
"""

import os
import subprocess
import sys


def get_base_dir() -> str:
    """Directory the launcher itself lives in, whether run as .py or frozen .exe."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def fail(message: str):
    """Show a message box (Windows) instead of a console window, then exit."""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "SMW Launcher", 0x10)
    except Exception:
        print(message)
    sys.exit(1)


def main():
    base_dir = get_base_dir()
    data_dir = os.path.join(base_dir, "data")
    snes9x_path = os.path.join(data_dir, "snes9x.exe")
    rom_path = os.path.join(data_dir, "ROM.smc")

    if not os.path.isdir(data_dir):
        fail(f"Could not find the 'data' folder next to this launcher:\n{data_dir}")
    if not os.path.isfile(snes9x_path):
        fail(f"Could not find snes9x.exe at:\n{snes9x_path}")
    if not os.path.isfile(rom_path):
        fail(f"Could not find ROM.smc at:\n{rom_path}")

    # cwd=data_dir is important: Snes9x reads/writes snes9x.conf (menu bar +
    # hotkey settings, save dirs, etc.) relative to its working directory.
    subprocess.Popen([snes9x_path, rom_path], cwd=data_dir)


if __name__ == "__main__":
    main()
