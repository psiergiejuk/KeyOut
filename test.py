import os
import time
import struct
import queue
from KeyOut.touch import TouchProcessor
from KeyOut.keyboard import KeyboardManager



def main():
    """Główna funkcja programu."""
    try:
        SCALE = 0.2214
        event_queue = queue.Queue()
        touch = TouchProcessor(event_queue)
        touch.start()
        keyboard = KeyboardManager(event_queue)
        keyboard.show_keys()
        keyboard.main()


    except IndexError as  e:
        print(f"Błąd: {e}")



if __name__ == "__main__":
    main()

