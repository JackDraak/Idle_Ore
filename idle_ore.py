import curses
import time

class Resource:
    def __init__(self, name, amount=0):
        self.name = name
        self.amount = amount

    def add(self, qty):
        self.amount += qty

class Entity:
    def __init__(self, name, production_rate):
        self.name = name
        self.production_rate = production_rate  # ore per tick

    def produce(self, resource):
        resource.add(self.production_rate)


def game(stdscr):
    curses.curs_set(0)  # hide cursor
    stdscr.nodelay(True)  # make getch non-blocking
    stdscr.timeout(100)  # refresh every 100ms

    ore = Resource("Ore")
    worker = Entity("Worker", production_rate=1)

    last_update = time.time()
    running = True

    while running:
        now = time.time()

        # Handle input
        key = stdscr.getch()
        if key == ord('q'):
            running = False
        elif key == ord(' '):
            ore.add(1)

        # Update every second
        if now - last_update >= 1:
            worker.produce(ore)
            last_update = now

        # Draw UI
        stdscr.clear()
        stdscr.addstr(0, 0, "Idle Mining Game (q to quit)")
        stdscr.addstr(2, 0, f"{ore.name}: {ore.amount}")
        stdscr.addstr(4, 0, "Press SPACE to mine manually")
        stdscr.addstr(5, 0, f"Worker produces {worker.production_rate} ore/sec")
        stdscr.refresh()


if __name__ == "__main__":
    curses.wrapper(game)

