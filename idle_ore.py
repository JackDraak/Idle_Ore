#!/usr/bin/env python3
"""
idle_ore.py with death and reproduction.

Controls:
  UP / DOWN : select worker
  SPACE     : manual mine with selected worker
  s         : save game
  q         : quit (autosaves)
"""

import curses
import json
import random
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

# --- Config ---
SAVE_FILENAME = "savegame.json"
AUTO_TICK_SECONDS = 1.0
XP_BASE_THRESHOLD = 10
PROGRESS_BAR_WIDTH = 12

TRAITS = {
    "Overzealous": {"drive_xp_mult": 1.5, "str_xp_mult": 0.75},
    "Lazy":       {"drive_xp_mult": 0.75, "str_xp_mult": 1.5},
    "Efficient":  {"drive_xp_mult": 1.25, "str_xp_mult": 1.25},
    "Clumsy":     {"str_xp_mult": 0.75},
    "Lucky":      {"bonus_ore_chance": 0.05},
    "Stalwart":   {"str_xp_mult": 1.1, "drive_xp_mult": 1.1},
}

SPECIALIZE_LEVEL = 5
MAX_WORKERS = 10
REPRODUCTION_TICKS = 30
REPRODUCTION_ORE_COST = 10
DEATH_RATE_CONSTANT = 0.02
MINING_SAFETY = 0.5  # base safety factor of mining job

SYLLABLES = [
    "zor", "vik", "ka", "ron", "thu", "mar", "xel", "tri", "pha", "gon",
    "qua", "len", "shi", "bor", "nek", "vol", "dra", "ula", "syl", "orn"
]

def make_name():
    count = random.choice([2, 3])
    name = "".join(random.choice(SYLLABLES) for _ in range(count))
    return name.capitalize()

# --- Classes ---
@dataclass
class Resource:
    name: str
    amount: int = 0

    def add(self, qty: int):
        if qty > 0:
            self.amount += int(qty)

    def spend(self, qty: int) -> bool:
        if self.amount >= qty:
            self.amount -= qty
            return True
        return False

    def to_dict(self):
        return {"name": self.name, "amount": int(self.amount)}

    @staticmethod
    def from_dict(d):
        return Resource(name=d.get("name", "Ore"), amount=int(d.get("amount", 0)))

@dataclass
class Entity:
    name: str = field(default_factory=make_name)
    strength: int = field(default_factory=lambda: random.randint(1, 3))
    drive: int = field(default_factory=lambda: random.randint(0, 2))
    trait_name: str = field(default_factory=lambda: random.choice(list(TRAITS.keys())))
    risk_aversion: float = field(default_factory=lambda: random.uniform(0.3, 0.9))  # 0=reckless,1=cautious
    str_xp: float = 0.0
    dri_xp: float = 0.0
    str_level: int = 0
    dri_level: int = 0
    specialization: Optional[str] = None
    ticks_survived: int = 0

    def trait(self) -> Dict:
        return TRAITS.get(self.trait_name, {})

    def xp_threshold(self, level: int) -> int:
        return XP_BASE_THRESHOLD * (level + 1)

    def manual_mine(self, resource: Resource) -> int:
        bonus = 0
        if self.specialization == "Master Miner":
            bonus = 1
        ore_gained = self.strength + bonus
        if "bonus_ore_chance" in self.trait() and random.random() < self.trait()["bonus_ore_chance"]:
            ore_gained += 1
        resource.add(ore_gained)
        mult = self.trait().get("str_xp_mult", 1.0)
        self.str_xp += 1.0 * mult
        self._check_levelups()
        return ore_gained

    def auto_mine(self, resource: Resource) -> int:
        bonus = 0
        if self.specialization == "Automation Expert":
            bonus = 1
        ore_gained = self.drive + bonus
        if "bonus_ore_chance" in self.trait() and random.random() < self.trait()["bonus_ore_chance"]:
            ore_gained += 1
        resource.add(ore_gained)
        mult = self.trait().get("drive_xp_mult", 1.0)
        self.dri_xp += 1.0 * mult
        self._check_levelups()
        return ore_gained

    def _check_levelups(self):
        while self.str_xp >= self.xp_threshold(self.str_level):
            thresh = self.xp_threshold(self.str_level)
            self.str_xp -= thresh
            self.str_level += 1
            self.strength += 1
            if self.specialization is None and self.str_level >= SPECIALIZE_LEVEL:
                self.specialization = "Master Miner"
        while self.dri_xp >= self.xp_threshold(self.dri_level):
            thresh = self.xp_threshold(self.dri_level)
            self.dri_xp -= thresh
            self.dri_level += 1
            self.drive += 1
            if self.specialization is None and self.dri_level >= SPECIALIZE_LEVEL:
                self.specialization = "Automation Expert"

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "strength": int(self.strength),
            "drive": int(self.drive),
            "trait_name": self.trait_name,
            "risk_aversion": float(self.risk_aversion),
            "str_xp": float(self.str_xp),
            "dri_xp": float(self.dri_xp),
            "str_level": int(self.str_level),
            "dri_level": int(self.dri_level),
            "specialization": self.specialization,
            "ticks_survived": int(self.ticks_survived),
        }

    @staticmethod
    def from_dict(d: Dict):
        return Entity(
            name=d.get("name", make_name()),
            strength=int(d.get("strength", 1)),
            drive=int(d.get("drive", 0)),
            trait_name=d.get("trait_name", random.choice(list(TRAITS.keys()))),
            risk_aversion=float(d.get("risk_aversion", random.uniform(0.3, 0.9))),
            str_xp=float(d.get("str_xp", 0.0)),
            dri_xp=float(d.get("dri_xp", 0.0)),
            str_level=int(d.get("str_level", 0)),
            dri_level=int(d.get("dri_level", 0)),
            specialization=d.get("specialization"),
            ticks_survived=int(d.get("ticks_survived", 0)),
        )

# --- Save / Load ---
def make_save_state(resource: Resource, workers: list) -> Dict:
    return {
        "version": 1,
        "resource": resource.to_dict(),
        "workers": [w.to_dict() for w in workers],
        "timestamp": time.time(),
    }

def save_game(filename: str, resource: Resource, workers: list) -> None:
    state = make_save_state(resource, workers)
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

def load_game(filename: str):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        resource = Resource.from_dict(data.get("resource", {}))
        workers_data = data.get("workers", [])
        workers = [Entity.from_dict(wd) for wd in workers_data]
        return resource, workers
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# --- UI helpers ---
def progress_bar(curr: float, threshold: float, width: int) -> str:
    if threshold <= 0:
        return "[" + " " * width + "]"
    ratio = max(0.0, min(1.0, curr / threshold))
    filled = int(round(ratio * width))
    return "[" + ("#" * filled).ljust(width) + "]"

# --- Game loop ---
def game(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    loaded = load_game(SAVE_FILENAME)
    if loaded:
        ore, workers = loaded
        if not workers:
            workers = [Entity() for _ in range(4)]
    else:
        ore = Resource("Ore", amount=0)
        workers = [Entity() for _ in range(4)]

    selected = 0
    last_tick = time.monotonic()
    death_messages = []
    death_message_duration = 3  # seconds
    running = True

    while running:
        now = time.monotonic()
        key = stdscr.getch()

        # Sanity checks on workers
        if not workers:
            workers = [Entity() for _ in range(4)]
            selected = 0
        elif selected >= len(workers):
            selected = len(workers) - 1

        if key != -1:
            if key in (ord("q"), ord("Q")):
                save_game(SAVE_FILENAME, ore, workers)
                running = False
            elif key in (ord("s"), ord("S")):
                save_game(SAVE_FILENAME, ore, workers)
            elif key == curses.KEY_UP:
                selected = max(0, selected - 1)
            elif key == curses.KEY_DOWN:
                selected = min(len(workers) - 1, selected + 1)
            elif key == ord(" "):
                workers[selected].manual_mine(ore)

        # Auto tick
        if now - last_tick >= AUTO_TICK_SECONDS:
            new_workers = []
            for w in workers:
                # Death chance calculation
                death_chance = (1.0 - w.risk_aversion) * (1.0 - MINING_SAFETY) * DEATH_RATE_CONSTANT
                if random.random() < death_chance:
                    death_messages.append((f"{w.name} died due to risky mining.", now))
                    continue  # skip adding to new_workers -> worker dies
                else:
                    # survived this tick, increment ticks_survived
                    w.ticks_survived += 1

                    # reproduction if enough ticks survived and ore available, and below max workers
                    if (w.ticks_survived >= REPRODUCTION_TICKS and
                        ore.amount >= REPRODUCTION_ORE_COST and
                        len(workers) + len(new_workers) < MAX_WORKERS):
                        ore.spend(REPRODUCTION_ORE_COST)
                        child = reproduce_worker(w)
                        new_workers.append(child)
                        w.ticks_survived = 0  # reset survival counter

                    # normal auto mining
                    w.auto_mine(ore)
                    new_workers.append(w)

            workers = new_workers
            last_tick = now

        # Draw UI
        stdscr.erase()
        stdscr.addstr(0, 0, f"idle_ore with death/reproduction (s=save, q=quit)  Workers: {len(workers)}/{MAX_WORKERS}")
        stdscr.addstr(1, 0, f"Ore: {ore.amount}")
        stdscr.addstr(2, 0, "Controls: UP/DOWN select worker, SPACE manual mine, s save")

        base_row = 4
        for idx, w in enumerate(workers):
            row = base_row + idx * 5
            sel_marker = ">" if idx == selected else " "
            risk_pct = int(w.risk_aversion * 100)
            stdscr.addstr(row, 0, f"{sel_marker} {w.name}  Trait: {w.trait_name}  Spec: {w.specialization or '-'}")
            stdscr.addstr(row + 1, 2, f"Risk Aversion: {risk_pct}%  Ticks Survived: {w.ticks_survived}")
            stdscr.addstr(row + 2, 2, f"STR Lv:{w.str_level}  STR:{w.strength}  XP: {int(w.str_xp)}/{w.xp_threshold(w.str_level)} {progress_bar(w.str_xp, w.xp_threshold(w.str_level), PROGRESS_BAR_WIDTH)}")
            stdscr.addstr(row + 3, 2, f"DRI Lv:{w.dri_level}  DRI:{w.drive}  XP: {int(w.dri_xp)}/{w.xp_threshold(w.dri_level)} {progress_bar(w.dri_xp, w.xp_threshold(w.dri_level), PROGRESS_BAR_WIDTH)}")

        # Show recent death messages (last 3 seconds)
        now_sec = time.monotonic()
        death_messages = [(msg, t) for (msg, t) in death_messages if now_sec - t < death_message_duration]
        for i, (msg, t) in enumerate(death_messages[-3:]):
            stdscr.addstr(base_row + len(workers)*5 + i, 0, msg)

        stdscr.refresh()
        time.sleep(0.02)

def reproduce_worker(parent: Entity) -> Entity:
    """Create a new Entity resembling the parent with some variation."""
    # Inherit risk_aversion with random small mutation
    new_risk = min(max(parent.risk_aversion + random.uniform(-0.1, 0.1), 0.0), 1.0)
    # Trait can be inherited or random
    new_trait = parent.trait_name if random.random() < 0.8 else random.choice(list(TRAITS.keys()))
    child = Entity(
        name=make_name(),
        strength=max(1, parent.strength + random.choice([-1, 0, 1])),
        drive=max(0, parent.drive + random.choice([-1, 0, 1])),
        trait_name=new_trait,
        risk_aversion=new_risk,
    )
    return child

def main():
    curses.wrapper(game)

if __name__ == "__main__":
    main()

