import struct
import mmap
import freetype
import time
import json
import numpy as np
import threading
import queue
import time
from evdev import UInput, InputDevice, categorize, ecodes, list_devices

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



class FB_Manger:
    
    BYTE_PER_PIXEL = 4
    FONT = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"

    def __init__(self, device="/dev/fb0", width=1920, height=1200, font_path=None):
        if font_path is None:
            font_path = self.FONT
        self.height = height
        self.width = width
        self.fb = open(device, "r+b")
        self.stride = self.width * self.BYTE_PER_PIXEL
        self.fb_map = mmap.mmap(self.fb.fileno(), self.stride * self.height, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ)
        self.face = freetype.Face(font_path)


class VirtualKeyboard:

    ACTION_MAP = {
            #(FN Shift Alt)
            (0, 0, 0): 0,
            (1, 0, 0): 4,
            (1, 0, 1): 4,
            (1, 1, 0): 5,
            (1, 1, 1): 5,
            (0, 1, 0): 1,
            (0, 1, 1): 3,
            (0, 0, 1): 2,
            }


    def __init__(self, parent):
        self.parent = parent
        self.shift = 0
        self.alt = 0
        self.spec = 0
        self.last = []
        self.fn = 0
        all_keys = [code for value, code in ecodes.ecodes.items() if value.startswith("KEY_")]
        all_keys = list(set(all_keys))
        print(len(all_keys))
        self.keyboard = UInput(
            {
                ecodes.EV_KEY: all_keys[:400],
                #ecodes.EV_SYN: [],
                #ecodes.EV_MSC: [ecodes.MSC_SCAN],
            },
            name="Virtual Keyboard",
        )

    def input(self, data):
        key = self.map_touch_to_key(data.x, data.y)

        if key is None:
            return 0,0
        if key["label"] == "\u21EB":
            self.shift = data.action 
        if key["label"] == "Alt":
            self.alt = data.action 
        if key["label"] == "Fn":
            self.fn = data.action 
        if key["label"] in ("Fn", "Alt", "\u21EB"):
            self.parent.index = self.ACTION_MAP[(self.fn, self.shift, self.alt)]
            self.parent.show_keys()
        print(key['label'], data.action)
        if "code" in key:

            print
            #self.keyboard.write(ecodes.EV_MSC, ecodes.MSC_SCAN, key["code"])  # MSC_SCAN dla kompatybilności
            self.keyboard.write(ecodes.EV_KEY, key["code"], data.action)
            self.keyboard.syn()
        return 0,0

    def map_touch_to_key(self, x, y):
        """Mapuje współrzędne dotyku na klawisz."""
        id_ = self.parent.map[y,x]
        if id_ == 0:
            return None
        return self.parent.keys[self.parent.index][id_ - 1][4]



class KeyboardManager:

    LAYOUT = {
            "EN": "/home/siergiej/soft/KeyOut/EN.json",
            "PL": "/home/siergiej/soft/KeyOut/EN.json",
            }
    ROWS_LEN = 13
    START_Y = 650
    BYTE_PER_PIXEL = 4
    MAIN_COLOR = (100, 100, 120, 0)
    SEC_COLOR = (255, 0,  255, 0)
    FONT = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
    KEYS = 6

    def __init__(self, queue, layout=None):
        if layout is None:
            layout = "EN"
        self.index = 0
        self.max_ascent = 0
        self.max_descent = 0
        self.queue = queue
        self.fbm = FB_Manger(font_path=self.FONT)
        self.layout = layout
        self.vkey = VirtualKeyboard(self)
        self.face = freetype.Face(self.FONT)
        self.buffer = np.zeros((self.KEYS, self.fbm.height, self.fbm.width, 4), dtype=np.uint8)  # 4 for RGBA
        self.map = np.zeros((self.fbm.height, self.fbm.width), dtype=np.uint8)
        buffer_size = self.buffer.nbytes  # Size of the buffer in bytes
        self.row_height = int((self.fbm.height - self.START_Y) / 5 )-1  # Wysokość jednego rzędu
        self.col_widths = int(self.fbm.width / self.ROWS_LEN) -1  # Szerokość kolumn w każdym wierszu
        self.start_offset = self.START_Y * self.fbm.stride
        self.end_offset = self.start_offset + (self.fbm.height - self.START_Y) * self.fbm.stride
        self.keys = {}

        # Wczytanie JSON-a
        with open(self.LAYOUT[self.layout], "r") as file:
            keyboard_config = json.load(file)
            for index in range(self.KEYS):
                self.keys[index] = []
                keyboard = keyboard_config["keyboard"][f"AD{index}"]
                for row_index, row in enumerate(keyboard):
                    y_start = row_index * self.row_height + self.START_Y
                    y_end = y_start + self.row_height
                    x_start = 0
                    for col_index, key in enumerate(row):
                        x_end = x_start + int(self.col_widths * key["width"])
                        self.keys[index].append((x_start, y_start, x_end, y_end, key))
                        self.draw_rectangle_with_text(
                            rect_x=int(x_start),
                            rect_y=int(y_start),
                            rect_w=int(x_end - x_start),
                            rect_h=int(y_end - y_start),
                            text=key["label"],
                            index=index,
                        )
                        x_start = x_end
        
        for index, (x_start, y_start, x_end, y_end, key) in enumerate(self.keys[self.index]):
            self.map[y_start:y_end, x_start:x_end] = index + 1


    def main(self):
        self.show_keys()
        while True:
            if self.queue.empty():
                time.sleep(0.05)
                continue
            data = self.queue.get()
            update, index = self.vkey.input(data)



    def show_keys(self):
        self.fbm.fb_map[self.start_offset:self.end_offset] = self.buffer[self.index, self.START_Y:self.fbm.height].tobytes()

    def set_pixel(self, x, y, index, color=None):
        if color is None:
            color = self.MAIN_COLOR
        if 0 <= x < self.fbm.width and 0 <= y < self.fbm.height:
            self.buffer[index, y, x] = [0, 255, 0, 255]

    def render_char_with_freetype(self, char, font_path=None, font_size=48):
        """
        Renderuje pojedynczy znak z użyciem FreeType i zwraca bitmapę.

        :param char: Znak do wyświetlenia. 
        :param font_path: Ścieżka do pliku czcionki.
        :param font_size: Rozmiar czcionki (w punktach).
        :return: Bitmapa (lista wierszy, gdzie 1 = piksel aktywny, 0 = piksel nieaktywny).
        """
        self.face.set_char_size(font_size * 100)

        # Załaduj znak
        self.face.load_char(char)
        glyph = self.face.glyph
        bitmap = glyph.bitmap

        # Pobierz metryki
        width = bitmap.width
        rows = bitmap.rows
        top = glyph.bitmap_top  # Odległość od linii bazowej do góry bitmapy
        descent = rows - top    # Odległość od linii bazowej do dołu bitmapy

        # Konwertuj dane bitmapy na tablicę 2D (1 = aktywny piksel, 0 = nieaktywny)
        buffer = bitmap.buffer
        rendered_char = []
        for row in range(rows):
            row_data = []
            for col in range(width):
                pixel = buffer[row * width + col]
                row_data.append(1 if pixel > 0 else 0)
            rendered_char.append(row_data)

        # Zaktualizuj metryki maksymalne
        if not hasattr(self, 'max_ascent'):
            self.max_ascent = 0
        if not hasattr(self, 'max_descent'):
            self.max_descent = 0

        self.max_ascent = max(self.max_ascent, top)
        self.max_descent = max(self.max_descent, descent)
        offset = self.max_ascent - top
        empty_row = [0] * width
        rendered_char = [empty_row] * offset + rendered_char

        return rendered_char

    def get_text_image_height(self):
        """
        Oblicza całkowitą wysokość obrazu potrzebną do wyrenderowania tekstu,
        bazując na maksymalnym wznosie (ascent) i maksymalnym opadzie (descent).
        """
        if not hasattr(self, 'max_ascent') or not hasattr(self, 'max_descent'):
            raise ValueError("Nie wyrenderowano żadnych znaków, aby obliczyć wysokość tekstu.")
        
        return self.max_ascent + self.max_descent

    def draw_rectangle_with_text(self, rect_x=200, rect_y=150, rect_w=400, rect_h=300, text="", index=0):
        """
        Rysuje pusty w środku kwadrat z napisem w środku.

        :param device: Ścieżka do urządzenia framebuffer.
        :param width: Szerokość ekranu w pikselach.
        :param height: Wysokość ekranu w pikselach.
        :param rect_x: Lewy górny róg prostokąta (X).
        :param rect_y: Lewy górny róg prostokąta (Y).
        :param rect_w: Szerokość prostokąta.
        :param rect_h: Wysokość prostokąta.
        :param color: Kolor obramowania jako tuple (R, G, B).
        :param text: Tekst do wyświetlenia w środku.
        :param text_color: Kolor tekstu jako tuple (R, G, B).
        """
        try:
            # Rysowanie górnej i dolnej krawędzi
            self.buffer[index, rect_y:(rect_y + rect_h), rect_x] = self.MAIN_COLOR
            self.buffer[index, rect_y:(rect_y + rect_h), (rect_x + rect_w)] = self.MAIN_COLOR
            self.buffer[index, rect_y, rect_x:rect_x + rect_w] = self.MAIN_COLOR
            self.buffer[index, rect_y+ rect_h, rect_x:rect_x + rect_w] = self.MAIN_COLOR


            # Rysowanie tekstu w środku
            char_width = 18  # Szerokość znaku (5 pikseli + 1 przerwy)
            char_height = 14  # Wysokość znaku
            text_start_x = rect_x + (rect_w - len(text) * (char_width + 2)) // 2
            text_start_y = rect_y + (rect_h - char_height) // 2

            self.max_ascent = 0
            self.max_descent = 0
            for char in text:
                bitmap = self.render_char_with_freetype(char, font_size=20)
                for row_idx, row in enumerate(bitmap):
                    for col_idx, pixel in enumerate(row):
                        if pixel:  # Jeśli piksel aktywny
                            self.set_pixel(text_start_x + col_idx, text_start_y + row_idx, index, self.SEC_COLOR)
                text_start_x += len(bitmap[0]) + 2  # Przesunięcie dla kolejnego znaku

        except PermissionError:
            print("Nie masz uprawnień do zapisu w /dev/fb0. Uruchom jako root.")
        except FileNotFoundError:
            print(f"Urządzenie {device} nie istnieje.")
        #except Exception as e:
        #    print(f"Wystąpił błąd: {e}")

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
    #except Exception as e:
    except KeyError as e:
        print(e)


if __name__ == "__main__":
    main()

