from evdev import InputDevice, categorize, ecodes, list_devices
import threading
import queue
import time

class Event:

    def __init__(self):
        self.x = -1
        self.y = -1
        self.slot = -1
        self.id_ = -1
        self.event = None

    def __repr__(self):
        return f"<Event ID:{self.id_} x:{self.x} y:{self.y} Slot:{self.slot} Event: {self.event}>"

class Action:

    UP = 0
    DOWN = 1

    def __init__(self, event):
        self.x = event.x
        self.y = event.y
        self.action = event.event

    def __repr__(self):
        return f"<Action x:{self.x} y:{self.y}, T:{self.action}>"

class TouchProcessor(threading.Thread):

    RESOLUTON_CALC = 0.22

    def __init__(self, output_queue, device_name="Finger"):
        super().__init__()
        self.device = self.find_touch_device(device_name)
        abs_info = self.device.capabilities().get(ecodes.EV_ABS, [])
        self.max_x = None
        self.max_y = None
        for code, abs_data in abs_info:
            if code == ecodes.ABS_X:
                self.max_x = abs_data.max
            elif code == ecodes.ABS_Y:
                self.max_y = abs_data.max
        self.output_queue = output_queue
        self.running = True  # Flaga kontroli wątku
        
    def find_touch_device(self, name):
        """Znajduje urządzenie dotykowe po nazwie."""
        devices = [InputDevice(path) for path in list_devices()]
        for device in devices:
            if name.lower() in device.name.lower():
                return device
        raise FileNotFoundError(f"Nie znaleziono urządzenia o nazwie zawierającej: {device_name}")

    def run(self):
        while self.running:
            try:
                track = {}  # Przechowuje informacje o slotach
                current_slot = None  # Obecnie aktywny slot
                action = []

                for event in self.device.read_loop():
                    if not self.running:
                        return  # wyjście przy zamknięciu
                    if event.type == ecodes.EV_ABS:
                        if event.code == ecodes.ABS_MT_SLOT:  # Zmiana slotu
                            current_slot = event.value
                        elif event.code == ecodes.ABS_MT_TRACKING_ID:
                            id_ = event.value
                            if id_ > 0:
                                if current_slot is not None:
                                    track[current_slot] = Event()
                                    track[current_slot].id_ = id_
                                    track[current_slot].event = Action.DOWN
                                else:
                                    current_slot = 0
                                    track[current_slot] = Event()
                                    track[current_slot].id_ = id_
                                    track[current_slot].event = Action.DOWN
                                action.append(current_slot)
                            else:
                                if current_slot is not None:
                                    if current_slot in track:
                                        track[current_slot].event = Action.UP
                                        self.output_queue.put(Action(track[current_slot]))
                                current_slot = None
                        elif event.code == ecodes.ABS_MT_POSITION_X:  # Współrzędna X
                            if current_slot in track:
                                track[current_slot].x = int(event.value * self.RESOLUTON_CALC)
                        elif event.code == ecodes.ABS_MT_POSITION_Y:  # Współrzędna Y
                            if current_slot in track:
                                track[current_slot].y = int(event.value * self.RESOLUTON_CALC)
                    elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                        if current_slot is not None:
                            track[current_slot].event = event.value
                            if event.value == 0:
                                if current_slot in track:
                                    track[current_slot].event = Action.UP
                                    old.append(track.pop(current_slot))
                    elif event.type == ecodes.EV_SYN:
                        if action:
                            self.output_queue.put(Action(track[action.pop()]))
            except Exception as Err:
                # Brak eventów w kolejce
                print(Err)
                continue

    def stop(self):
        """Zatrzymaj wątek."""
        self.running = False

