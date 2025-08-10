import curses
import time
import random

from .entities import Entity, make_name, TRAITS
from .resources import Resource
from .save_load import save_game, load_game
from .ui import progress_bar

SAVE_FILENAME = "data/savegame.json"
AUTO_TICK_SECONDS = 1.0
MAX_WORKERS = 10
REPRODUCTION_TICKS = 30
REPRODUCTION_ORE_COST = 10
DEATH_RATE_CONSTANT = 0.02
MINING_SAFETY = 0.5

def reproduce_worker(parent: Entity) -> Entity:
    new_risk = min(max(parent.risk_aversion + random.uniform(-0.1, 0.1), 0.0), 1.0)
    new_trait = parent.trait_name if random.random() < 0.8 else random.choice(list(TRAITS.keys()))
    return Entity(
        name=make_name(),
        strength=max(1, parent.strength + random.choice([-1, 0, 1])),
        drive=max(0, parent.drive + random.choice([-1, 0, 1])),
        trait_name=new_trait,
        risk_aversion=new_risk,
    )

def game_loop(stdscr):
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
    death_message_duration = 3
    running = True

    while running:
        now = time.monotonic()
        key = stdscr.getch()

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

        if now - last_tick >= AUTO_TICK_SECONDS:
            new_workers = []
            for w in workers:
                death_chance = (1.0 - w.risk_aversion) * (1.0 - MINING_SAFETY) * DEATH_RATE_CONSTANT
                if random.random() < death_chance:
                    death_messages.append((f"{w.name} died due to risky mining.", now))
                    continue
                w.ticks_survived += 1
                if (w.ticks_survived >= REPRODUCTION_TICKS and
                    ore.amount >= REPRODUCTION_ORE_COST and
                    len(workers) + len(new_workers) < MAX_WORKERS):
                    ore.spend(REPRODUCTION_ORE_COST)
                    child = reproduce_worker(w)
                    new_workers.append(child)
                    w.ticks_survived = 0
                w.auto_mine(ore)
                new_workers.append(w)
            workers = new_workers
            last_tick = now

        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        stdscr.addstr(0, 0, f"idle_ore (s=save, q=quit)  Workers: {len(workers)}/{MAX_WORKERS}")
        stdscr.addstr(1, 0, f"Ore: {ore.amount}")
        stdscr.addstr(2, 0, "Controls: UP/DOWN select worker, SPACE manual mine, s save")

        base_row = 4
        for idx, w in enumerate(workers):
            row = base_row + idx * 5
            if row + 4 >= max_y:
                break
            sel_marker = ">" if idx == selected else " "
            stdscr.addstr(row, 0, f"{sel_marker} {w.name}  Trait: {w.trait_name}  Spec: {w.specialization or '-'}")
            stdscr.addstr(row + 1, 2, f"Risk Aversion: {int(w.risk_aversion * 100)}%  Ticks Survived: {w.ticks_survived}")
            stdscr.addstr(row + 2, 2, f"STR Lv:{w.str_level}  STR:{w.strength}  XP: {int(w.str_xp)}/{w.xp_threshold(w.str_level)} {progress_bar(w.str_xp, w.xp_threshold(w.str_level))}")
            stdscr.addstr(row + 3, 2, f"DRI Lv:{w.dri_level}  DRI:{w.drive}  XP: {int(w.dri_xp)}/{w.xp_threshold(w.dri_level)} {progress_bar(w.dri_xp, w.xp_threshold(w.dri_level))}")

        # Clean out old death messages
        now = time.monotonic()
        death_messages = [(msg, t) for msg, t in death_messages if now - t < death_message_duration]

        # Display death messages at bottom
        for i, (msg, _) in enumerate(death_messages):
            if max_y - 1 - i < 0:
                break
            stdscr.addstr(max_y - 1 - i, 0, msg[:max_x - 1])

        stdscr.refresh()
        time.sleep(0.02)

