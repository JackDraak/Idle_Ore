import curses
from game.core import game_loop

def main():
    curses.wrapper(game_loop)

if __name__ == "__main__":
    main()

