# SMW And Trainer (converted from SMW.CT)

A standalone Python/Tkinter trainer built from Cheat Engine table.

## Setup (Windows only)

`pymem` uses Windows API calls (`OpenProcess`, `ReadProcessMemory`, etc.), so this
only runs on Windows — same as Snes9x itself.

```
pip install pymem
```

## Running

1. Start Snes9x and load your Super Mario World ROM.
2. Run the trainer:
   ```
   python smw_trainer.py
   ```
3. Click **Attach to Snes9x**.
4. Tabs: **General**, **Yoshi**, **Position**, **Switches** — matching the
   groups in your original cheat table.
5. Per cheat:
   - **Read** — pulls the current in-game value into the box.
   - **Set** — writes the value in the box once.
   - **Freeze** — keeps re-writing the value ~10x/second (good for
     Lives/Time/Coins style "infinite" cheats).

## Notes

- **State**: 0=Small, 1=Super/Big, 2=Cape, 3=Flower, 67=Small Fire Mario
  (other values = Small Mario with texture glitches)
- **Item Box**: 0=Empty, 1=Mushroom, 2=Flower, 3=Star, 4=Cape, 5=1-UP,
  6=Upward Vine, 10=P-Balloon, 11=Red Coin (5 Coin), 12=Flying 1-UP,
  13=Flying Harmful Key, 14=Random Item, 16-17=Flying Empty Kaizo,
  20=Cloud, 62=Unstoppable Snake Building, 70=Radio, 83=Lighten Entities,
  85=Red Kaizo, 92=Bugs Whole Program, 104=Direct Self Damage,
  118=Scroll Whole Level, 155=Key Hole, 188=Jumpad,
  194=Yoshi (despawns if already present), 215=Win Flag,
  226/228/230/236=Moving Platform variants, 247=Coins-Giving Cloud,
  248-249=Trampoline (left/right)
- **Position X** is a 4-byte value that wraps at ~4.29 billion. Rather than
  setting an absolute value, use small repeated **Set** clicks (or freeze +
  manual bumps) to move Mario incrementally, same logic as the original table.
- **Time**: 151587093 ≈ 999 in-game.
- **Lives**: 3014498 ≈ 99 in-game.

## Raw (non-module) addresses

`Is Riding Yoshi`, `Position X`, `Position Y`, `Blue Switch`, and `Red Switch`
were stored in your table as bare addresses rather than `snes9x.exe+offset`
or a resolved pointer path. They should work as long as Snes9x's memory
layout matches what it was when the table was made, but they're the most
likely entries to break after an emulator restart or version change. If one
stops working, re-scan it in Cheat Engine and update the `"address"` field
for that entry in `smw_trainer.py`.
