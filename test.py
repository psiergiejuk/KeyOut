import os
import time
import struct
import queue
from touch import TouchProcessor
from keyboard import KeyboardManager




def main():
    """Główna funkcja programu."""
    try:
        SCALE = 0.2214
        event_queue = queue.Queue()
        touch = TouchProcessor(event_queue)
        touch.start()
        keyboard = KeyboardManager(event_queue)
        keyboard.show_keys()


        while True:
            time.sleep(1)
    except OSError as  e:
        print(f"Błąd: {e}")



if __name__ == "__main__":
    main()

