#!/usr/bin/env python3
"""
idle_ore.py

Lightweight idle game loop using curses.

Controls:
  UP / DOWN : select worker
  SPACE     : manual mine with selected worker
  q         : quit
"""

import curses
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

# -------------------------
# Configuration / constants
# -------------------------
AUTO_TICK_SECONDS = 1.0
XP_BASE_THRESHOLD = 10  # XP needed for level 1, scales linearly: threshold = XP_BASE_THRESHOLD * (level + 1)
PROGRESS_BAR_WIDTH = 12

# Traits definitions - multipliers applied to XP gains and occasional bonuses
TRAITS = {
    "Overzealous": {"drive_xp_mult": 1.5, "str_xp_mult": 0.75},
    "Lazy":       {"drive_xp_mult": 0.75, "str_xp_mult": 1.5},
    "Efficient":  {"drive_xp_mult": 1.25, "str_xp_mult": 1.25},
    "Clumsy":     {"str_xp_mult": 0.75},
    "Lucky":      {"bonus_ore_chance": 0.05},  # small chance to produce bonus ore on actions
    "Stalwart":   {"str_xp_mult": 1.1, "drive_xp_mult": 1.1},
}

# Specializations unlocked at level >= SPECIALIZE_LEVEL
SPECIALIZE_LEVEL = 5

# -------------------------
# Utility: procedural names
# -------------------------
SYLLABLES = [
    "zor", "vik", "ka", "ron", "thu", "mar", "xel", "tri", "pha", "gon",
    "qua", "len", "shi", "bor", "nek", "vol", "dra", "ula", "syl", "orn"
]

def make_name():
    # 2-3 syllables, capitalize
    count = random.choice([2, 3])
    name = "".join(random.choice(SYLLABLES) for _ in range(count))
    return name.capitalize()

# -------------------------
# Core classes
# -------------------------
@dataclass
class Resource:
    name: str
    amount: int = 0

    def add(self, qty: int):
        if qty <= 0:
            return
        self.amount += int(qty)

    def spend(self, qty: int) -> bool:
        if self.amount >= qty:
            self.amount -= qty
            return True
        return False

@dataclass
class Entity:
    name: str = field(default_factory=make_name)
    strength: int = field(default_factory=lambda: random.randint(1, 3))  # manual mining power
    drive: int = field(default_factory=lambda: random.randint(0, 2))     # auto mining power
    trait_name: str = field(default_factory=lambda: random.choice(list(TRAITS.keys())))
    str_xp: float = 0.0
    dri_xp: float = 0.0
    str_level: int = 0
    dri_level: int = 0
    specialization: Optional[str] = None

    def trait(self) -> Dict:
        return TRAITS.get(self.trait_name, {})

    def xp_threshold(self, level: int) -> int:
        # Linear growth threshold. Could be made exponential later.
        return XP_BASE_THRESHOLD * (level + 1)

    def manual_mine(self, resource: Resource) -> int:
        """Manual mining done by player selecting this worker and pressing SPACE."""
        # Base ore = strength + specialization bonus
        bonus = 0
        if self.specialization == "Master Miner":
            bonus = 1  # flat bonus for Master Miner
        ore_gained = self.strength + bonus

        # Lucky trait can give a small bonus ore chance
        if "bonus_ore_chance" in self.trait():
            if random.random() < self.trait()["bonus_ore_chance"]:
                ore_gained += 1

        resource.add(ore_gained)

        # XP gain for STR
        mult = self.trait().get("str_xp_mult", 1.0)
        self.str_xp += 1.0 * mult

        self._check_levelups()
        return ore_gained

    def auto_mine(self, resource: Resource) -> int:
        """Idle mining that happens every tick for all workers."""
        bonus = 0
        if self.specialization == "Automation Expert":
            bonus = 1
        ore_gained = self.drive + bonus

        if "bonus_ore_chance" in self.trait():
            if random.random() < self.trait()["bonus_ore_chance"]:
                ore_gained += 1

        resource.add(ore_gained)

        # XP gain for DRIVE
        mult = self.trait().get("drive_xp_mult", 1.0)
        self.dri_xp += 1.0 * mult

        self._check_levelups()
        return ore_gained

    def _check_levelups(self):
        # Strength leveling
        while self.str_xp >= self.xp_threshold(self.str_level):
            thresh = self.xp_threshold(self.str_level)
            self.str_xp -= thresh
            self.str_level += 1
            self.strength += 1  # stat increases on level
            # Specialize if threshold reached
            if self.specialization is None and self.str_level >= SPECIALIZE_LEVEL:
                self.specialization = "Master Miner"

        # Drive leveling
        while self.dri_xp >= self.xp_threshold(self.dri_level):
            thresh = self.xp_threshold(self.dri_level)
            self.dri_xp -= thresh
            self.dri_level += 1
            self.drive += 1
            if self.specialization is None and self.dri_level >= SPECIALIZE_LEVEL:
                self.specialization = "Automation Expert"

# -------------------------
# UI helpers
# -------------------------
def progress_bar(curr: float, threshold: float, width: int) -> str:
    if threshold <= 0:
        return "[" + " " * width + "]"
    ratio = max(0.0, min(1.0, curr / threshold))
    filled = int(round(ratio * width))
    bar = "[" + ("#" * filled).ljust(width) + "]"
    return bar

# -------------------------
# Game loop (curses)
# -------------------------
def game(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)  # 100 ms

    ore = Resource("Ore", amount=0)

    # Start with 4 procedural workers
    workers = [Entity() for _ in range(4)]
    selected = 0
    last_tick = time.monotonic()
    running = True

    while running:
        now = time.monotonic()
        key = stdscr.getch()

        # Input handling
        if key != -1:
            if key in (ord("q"), ord("Q")):
                running = False
            elif key == curses.KEY_UP:
                selected = max(0, selected - 1)
            elif key == curses.KEY_DOWN:
                selected = min(len(workers) - 1, selected + 1)
            elif key == ord(" "):
                # manual mine with selected worker
                gained = workers[selected].manual_mine(ore)
                # show a tiny flash line - we'll rely on UI refresh to display change
            # future keys: hire, upgrades, etc.

        # Auto tick
        if now - last_tick >= AUTO_TICK_SECONDS:
            for w in workers:
                w.auto_mine(ore)
            last_tick = now

        # Draw UI
        stdscr.erase()
        stdscr.addstr(0, 0, "Idle Workers - Procedural Growth (q to quit)")
        stdscr.addstr(1, 0, f"Ore: {ore.amount}")
        stdscr.addstr(2, 0, "Controls: UP/DOWN select worker, SPACE manual mine")

        base_row = 4
        for idx, w in enumerate(workers):
            row = base_row + idx * 4
            sel_marker = ">" if idx == selected else " "
            stdscr.addstr(row, 0, f"{sel_marker} {w.name}  Trait: {w.trait_name}  Spec: {w.specialization or '-'}")
            stdscr.addstr(row + 1, 2, f"STR Lv:{w.str_level}  STR:{w.strength}  XP: {int(w.str_xp)}/{w.xp_threshold(w.str_level)} {progress_bar(w.str_xp, w.xp_threshold(w.str_level), PROGRESS_BAR_WIDTH)}")
            stdscr.addstr(row + 2, 2, f"DRI Lv:{w.dri_level}  DRI:{w.drive}  XP: {int(w.dri_xp)}/{w.xp_threshold(w.dri_level)} {progress_bar(w.dri_xp, w.xp_threshold(w.dri_level), PROGRESS_BAR_WIDTH)}")

        stdscr.refresh()
        time.sleep(0.02)  # small sleep so loop does not eat CPU

def main():
    curses.wrapper(game)

if __name__ == "__main__":
    main()

