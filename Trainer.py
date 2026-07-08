"""
SMW Trainer
===========
Converted from SMW.CT (Cheat Engine table) into a standalone Python trainer.

Requirements (Windows only — pymem uses WinAPI under the hood):
    pip install pymem

Run:
    python smw_trainer.py

Then start Snes9x + your SMW ROM, click "Attach", and use the trainer.

NOTE ON ADDRESSES
-----------------
Two address styles are used, exactly as they were in the original cheat table:

1. "snes9x.exe+OFFSET"  -> resolved relative to the Snes9x module base.
   These stay valid across restarts of the emulator.

2. Raw addresses (e.g. 00987511) -> used as-is, with NO module offset.
   These were captured directly in Cheat Engine without a module reference
   or a resolved pointer path. They MAY break if you restart Snes9x, use a
   different Snes9x version/build, or load a save state at a different
   point than when the table was made. If an entry using a raw address
   stops working, re-do a pointer scan on it in Cheat Engine and swap the
   address in CHEATS below.
"""

import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

import pymem
import pymem.process

PROCESS_NAME = "snes9x.exe"

# ---------------------------------------------------------------------------
# Cheat definitions (converted 1:1 from SMW.CT)
# ---------------------------------------------------------------------------
# type: "byte" (1 byte, 0-255) or "int" (4 bytes, CE's "4 Bytes")
CHEATS = [
    {
        "name": "State",
        "type": "byte",
        "address": "snes9x.exe+5874AD",
        "group": "General",
        "note": "0=Small 1=Super/Big 2=Cape 3=Flower 67=Small Fire Mario",
    },
    {
        "name": "Score",
        "type": "int",
        "address": "snes9x.exe+5883C8",
        "group": "General",
    },
    {
        "name": "Coins",
        "type": "byte",
        "address": "snes9x.exe+588253",
        "group": "General",
    },
    {
        "name": "Lives",
        "type": "int",
        "address": "snes9x.exe+588248",
        "group": "General",
        "note": "3014498 in the table maps to 99 lives",
    },
    {
        "name": "Yoshi Coins",
        "type": "byte",
        "address": "snes9x.exe+5888B6",
        "group": "General",
    },
    {
        "name": "Item Box",
        "type": "byte",
        "address": "snes9x.exe+588256",
        "group": "General",
        "note": "0=Empty 1=Mushroom 2=Flower 3=Star 4=Cape 5=1-UP ... see Item Box list",
    },
    {
        "name": "Time",
        "type": "int",
        "address": "009883C4",
        "group": "General",
        "note": "151587093 in the table maps to 999",
    },
    {
        "name": "Eaten Fruits By Yoshi",
        "type": "byte",
        "address": "snes9x.exe+588D79",
        "group": "Yoshi",
    },
    {
        "name": "Is Riding Yoshi",
        "type": "byte",
        "address": "0098755E",
        "group": "Yoshi",
        "note": "raw address, may need re-scanning after restart",
    },
    {
        "name": "Position X",
        "type": "int",
        "address": "00987525",
        "group": "Position",
        "note": "raw address; cycles at the 4-byte limit, use freeze/hotkey style increments",
    },
    {
        "name": "Position Y",
        "type": "byte",
        "address": "00987511",
        "group": "Position",
        "note": "raw address, may need re-scanning after restart",
    },
    {
        "name": "Yellow Switch",
        "type": "byte",
        "address": "snes9x.exe+5893BC",
        "group": "Switches",
    },
    {
        "name": "Green Switch",
        "type": "byte",
        "address": "snes9x.exe+5893BB",
        "group": "Switches",
    },
    {
        "name": "Blue Switch",
        "type": "byte",
        "address": "009893BD",
        "group": "Switches",
        "note": "raw address, may need re-scanning after restart",
    },
    {
        "name": "Red Switch",
        "type": "int",
        "address": "009893BE",
        "group": "Switches",
        "note": "raw address, may need re-scanning after restart",
    },
]


# ---------------------------------------------------------------------------
# Memory backend
# ---------------------------------------------------------------------------
class TrainerBackend:
    def __init__(self):
        self.pm = None
        self.module_base = None

    def attach(self):
        self.pm = pymem.Pymem(PROCESS_NAME)
        module = pymem.process.module_from_name(self.pm.process_handle, PROCESS_NAME)
        if module is None:
            raise RuntimeError(f"Could not find module {PROCESS_NAME}")
        self.module_base = module.lpBaseOfDll

    def resolve_address(self, address_str: str) -> int:
        if address_str.lower().startswith(PROCESS_NAME.lower() + "+"):
            offset = int(address_str.split("+", 1)[1], 16)
            return self.module_base + offset
        return int(address_str, 16)

    def read(self, cheat) -> int:
        addr = self.resolve_address(cheat["address"])
        if cheat["type"] == "byte":
            return self.pm.read_uchar(addr)
        return self.pm.read_int(addr)

    def write(self, cheat, value: int):
        addr = self.resolve_address(cheat["address"])
        if cheat["type"] == "byte":
            self.pm.write_uchar(addr, value & 0xFF)
        else:
            self.pm.write_int(addr, value)


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
class TrainerApp:
    POLL_INTERVAL = 0.1  # seconds, for frozen values

    def __init__(self, root):
        self.root = root
        self.root.title("SMW Trainer")
        self.backend = TrainerBackend()
        self.attached = False
        self.rows = {}  # name -> {entry, freeze_var}
        self._stop_event = threading.Event()

        self._build_ui()
        self._start_freeze_loop()

    # -- UI construction ----------------------------------------------------
    def _build_ui(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        self.status_var = tk.StringVar(value="Not attached")
        ttk.Label(top, textvariable=self.status_var).pack(side="left")

        ttk.Button(top, text="Attach to Snes9x", command=self.attach).pack(side="right")

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        groups = {}
        for cheat in CHEATS:
            groups.setdefault(cheat["group"], []).append(cheat)

        for group_name, cheats in groups.items():
            frame = ttk.Frame(notebook, padding=10)
            notebook.add(frame, text=group_name)
            self._build_group(frame, cheats)

    def _build_group(self, frame, cheats):
        for r, cheat in enumerate(cheats):
            name = cheat["name"]

            ttk.Label(frame, text=name, width=20).grid(row=r, column=0, sticky="w", pady=3)

            entry = ttk.Entry(frame, width=12)
            entry.insert(0, "0")
            entry.grid(row=r, column=1, padx=5)

            set_btn = ttk.Button(
                frame, text="Set", width=6,
                command=lambda c=cheat, e=entry: self.set_value(c, e)
            )
            set_btn.grid(row=r, column=2, padx=3)

            freeze_var = tk.BooleanVar(value=False)
            freeze_chk = ttk.Checkbutton(frame, text="Freeze", variable=freeze_var)
            freeze_chk.grid(row=r, column=3, padx=3)

            read_btn = ttk.Button(
                frame, text="Read", width=6,
                command=lambda c=cheat, e=entry: self.read_value(c, e)
            )
            read_btn.grid(row=r, column=4, padx=3)

            if "note" in cheat:
                ttk.Label(
                    frame, text=cheat["note"], foreground="gray", font=("", 8)
                ).grid(row=r, column=5, sticky="w", padx=8)

            self.rows[name] = {"entry": entry, "freeze_var": freeze_var, "cheat": cheat}

    # -- actions --------------------------------------------------------
    def attach(self):
        try:
            self.backend.attach()
            self.attached = True
            self.status_var.set(f"Attached to {PROCESS_NAME}")
        except Exception as exc:
            self.attached = False
            self.status_var.set("Not attached")
            messagebox.showerror(
                "Attach failed",
                f"Could not attach to {PROCESS_NAME}.\n\n"
                f"Make sure Snes9x is running with the ROM loaded.\n\nDetails: {exc}",
            )

    def _require_attached(self):
        if not self.attached:
            messagebox.showwarning("Not attached", "Click 'Attach to Snes9x' first.")
            return False
        return True

    def set_value(self, cheat, entry):
        if not self._require_attached():
            return
        try:
            value = int(entry.get())
            self.backend.write(cheat, value)
        except Exception as exc:
            messagebox.showerror("Write failed", str(exc))

    def read_value(self, cheat, entry):
        if not self._require_attached():
            return
        try:
            value = self.backend.read(cheat)
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
        except Exception as exc:
            messagebox.showerror("Read failed", str(exc))

    # -- freeze loop ------------------------------------------------------
    def _start_freeze_loop(self):
        def loop():
            while not self._stop_event.is_set():
                if self.attached:
                    for row in self.rows.values():
                        if row["freeze_var"].get():
                            try:
                                value = int(row["entry"].get())
                                self.backend.write(row["cheat"], value)
                            except Exception:
                                pass  # bad input or lost handle; skip this tick
                time.sleep(self.POLL_INTERVAL)

        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def on_close(self):
        self._stop_event.set()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = TrainerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
