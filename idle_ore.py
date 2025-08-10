import curses
import time
import random

# === Name parts for procedural generation ===
ENTITY_NAMES_PREFIX = [
    "Iron", "Stone", "Steel", "Copper", "Silver", "Golden",
    "Shadow", "Void", "Crystal", "Obsidian", "Jade", "Rusty"
]
ENTITY_NAMES_SUFFIX = [
    "Miner", "Digger", "Prospector", "Gatherer", "Harvester",
    "Excavator", "Delver", "Scraper", "Shoveler"
]


class Resource:
    def __init__(self, name, amount=0):
        self.name = name
        self.amount = amount

    def add(self, qty):
        self.amount += qty

    def spend(self, qty):
        if self.amount >= qty:
            self.amount -= qty
            return True
        return False


class Entity:
    def __init__(self):
        self.name = f"{random.choice(ENTITY_NAMES_PREFIX)} {random.choice(ENTITY_NAMES_SUFFIX)}"
        self.strength = random.randint(1, 3)   # manual mining power
        self.drive = random.randint(0, 2)      # idle mining power

    def mine_manual(self, resource):
        resource.add(self.strength)

    def mine_auto(self, resource):
        resource.add(self.drive)


def game(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)

    ore = Resource("Ore")
    # Start with 3 procedurally generated workers
    workers = [Entity() for _ in range(3)]

    last_update = time.time()
    running = True

    while running:
        now = time.time()

        # Handle input
        key = stdscr.getch()
        if key == ord('q'):
            running = False
        elif key == ord(' '):
            # Manual mining: all workers mine
            for worker in workers:
                worker.mine_manual(ore)

        # Auto mining every second
        if now - last_update >= 1:
            for worker in workers:
                worker.mine_auto(ore)
            last_update = now

        # Draw UI
        stdscr.clear()
        stdscr.addstr(0, 0, "Idle Mining Game - Procedural Edition (q to quit)")
        stdscr.addstr(2, 0, f"{ore.name}: {ore.amount}")

        stdscr.addstr(4, 0, "Workers:")
        for i, w in enumerate(workers, start=1):
            stdscr.addstr(4 + i, 2, f"{w.name} | STR: {w.strength}  DRIVE: {w.drive}")

        stdscr.addstr(8 + len(workers), 0, "SPACE = All workers mine manually")
        stdscr.refresh()


if __name__ == "__main__":
    curses.wrapper(game)

