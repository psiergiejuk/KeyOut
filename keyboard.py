import struct
import mmap
import freetype
import time
import json
import numpy as np
from evdev import UInput, ecodes


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

    def __init__(self, parent):
        self.parent = parent
        self.shift = 0
        self.alt = 0
        self.spec = 0
        self.fn = 0
        self.keyboard = UInput(
            {
                ecodes.EV_KEY: [
                    ecodes.KEY_ESC, ecodes.KEY_F1, ecodes.KEY_F2, ecodes.KEY_F3, ecodes.KEY_F4, ecodes.KEY_F5,
                    ecodes.KEY_F6, ecodes.KEY_F7, ecodes.KEY_F8, ecodes.KEY_F9, ecodes.KEY_F10, ecodes.KEY_F11,
                    ecodes.KEY_F12, ecodes.KEY_PRINT, ecodes.KEY_GRAVE, ecodes.KEY_1, ecodes.KEY_2, ecodes.KEY_3,
                    ecodes.KEY_4, ecodes.KEY_5, ecodes.KEY_6, ecodes.KEY_7, ecodes.KEY_8, ecodes.KEY_9,
                    ecodes.KEY_0, ecodes.KEY_MINUS, ecodes.KEY_EQUAL, ecodes.KEY_Q, ecodes.KEY_W, ecodes.KEY_E,
                    ecodes.KEY_R, ecodes.KEY_T, ecodes.KEY_Y, ecodes.KEY_U, ecodes.KEY_I, ecodes.KEY_O,
                    ecodes.KEY_P, ecodes.KEY_LEFTBRACE, ecodes.KEY_RIGHTBRACE, ecodes.KEY_A, ecodes.KEY_S,
                    ecodes.KEY_D, ecodes.KEY_F, ecodes.KEY_G, ecodes.KEY_H, ecodes.KEY_J, ecodes.KEY_K,
                    ecodes.KEY_L, ecodes.KEY_SEMICOLON, ecodes.KEY_APOSTROPHE, ecodes.KEY_ENTER, ecodes.KEY_Z,
                    ecodes.KEY_X, ecodes.KEY_C, ecodes.KEY_V, ecodes.KEY_B, ecodes.KEY_N, ecodes.KEY_M,
                    ecodes.KEY_COMMA, ecodes.KEY_DOT, ecodes.KEY_SLASH, ecodes.KEY_LEFTSHIFT, ecodes.KEY_LEFTCTRL,
                    ecodes.KEY_LEFTALT, ecodes.KEY_SPACE, ecodes.KEY_RIGHTALT, ecodes.KEY_RIGHTCTRL,
                    ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_LEFT, ecodes.KEY_RIGHT, ecodes.KEY_BACKSPACE, ecodes.KEY_TAB,
                    ecodes.KEY_DOLLAR,
                ],
                ecodes.EV_SYN: [],
                ecodes.EV_MSC: [ecodes.MSC_SCAN],
            },
            name="Virtual Keyboard",
        )

    def input(self, data):
        key = self.map_touch_to_key(data.x, data.y)
        if key is None:
            return 0,0
        if key["label"] == "Shift":
            self.shift = data.action 
        if key["label"] == "Alt":
            self.alt = data.action 
            

        if key["label"] == "Shift":
            if data.action:
                if self.alt:
                    self.parent.index = 3
                else:
                    self.parent.index = 1
            else:
                if self.alt:
                    self.parent.index = 2
                else:
                    self.parent.index = 0
            self.parent.show_keys()
        if key["label"] == "Alt":
            if data.action:
                if self.shift:
                    self.parent.index = 3
                else:
                    self.parent.index = 2
            else:
                if self.shift:
                    self.parent.index = 1
                else:
                    self.parent.index = 0
            self.parent.show_keys()

        print(key['label'], data.action)
        if "code" in key:

            self.keyboard.write(ecodes.EV_MSC, ecodes.MSC_SCAN, key["code"])  # MSC_SCAN dla kompatybilności
            self.keyboard.write(ecodes.EV_KEY, key["code"], data.action)
            self.keyboard.syn()
        return 0,0

    def map_touch_to_key(self, x, y):
        """Mapuje współrzędne dotyku na klawisz."""
        #for x_start, y_start, x_end, y_end, key in self.parent.keys[self.parent.index]:
        #    if x_start <= x < x_end and y_start <= y < y_end:
        #        return key
        return self.parent.keys[self.parent.index][self.parent.map[x,y][4]]
        #return None


    def send_key_to_system(self, ui, key, is_pressed=True):
        """Wysyła klawisz do systemu jako input z klawiatury."""
        special_keys = {
            "Esc": ecodes.KEY_ESC,
            "Ctrl": ecodes.KEY_LEFTCTRL,
            "Alt": ecodes.KEY_LEFTALT,
            "Shift": ecodes.KEY_LEFTSHIFT,
            "Space": ecodes.KEY_SPACE,
            "Enter": ecodes.KEY_ENTER,
            "Fn": ecodes.KEY_FN,  # Jeśli Fn jest obsługiwane
            "Up": ecodes.KEY_UP,
            "Down": ecodes.KEY_DOWN,
            "Left": ecodes.KEY_LEFT,
            "Right": ecodes.KEY_RIGHT,
            "Back": ecodes.KEY_BACKSPACE,
        }

        # Obsługa klawiszy funkcyjnych (F1-F12)
        if key.startswith("F") and key[1:].isdigit():
            key_event = getattr(ecodes, f"KEY_{key.upper()}", None)
        elif key in special_keys:
            key_event = special_keys[key]
        else:
            key_event = getattr(ecodes, f"KEY_{key.upper()}", None)

        if key_event:
            print(f"Sending: {key} -> {key_event} (pressed={is_pressed})")
            ui.write(ecodes.EV_MSC, ecodes.MSC_SCAN, key_event)  # MSC_SCAN dla kompatybilności
            ui.write(ecodes.EV_KEY, key_event, 1 if is_pressed else 0)
            ui.syn()
        else:
            print(f"Unrecognized key: {key}")


class KeyboardManager:

    LAYOUT = {
            "EN": "EN.json",
            "PL": "PL.json",
            }
    ROWS_LEN = 13
    START_Y = 800
    BYTE_PER_PIXEL = 4
    MAIN_COLOR = (100, 100, 120, 0)
    SEC_COLOR = (255, 0,  255, 0)
    FONT = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"

    def __init__(self, queue, layout=None):
        if layout is None:
            layout = "EN"
        self.index = 0
        self.queue = queue
        self.fbm = FB_Manger(font_path=self.FONT)
        self.layout = layout
        self.vkey = VirtualKeyboard(self)
        self.face = freetype.Face(self.FONT)
        self.buffer = np.zeros((4, self.fbm.height, self.fbm.width, 4), dtype=np.uint8)  # 4 for RGBA
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
            for index in range(4):
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
            self.map[x_start:x_start, y_start:y_end] = index


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
        self.face.set_char_size(font_size * 64)

        # Załaduj znak
        self.face.load_char(char)
        bitmap = self.face.glyph.bitmap

        # Pobierz wymiary bitmapy
        width, rows = bitmap.width, bitmap.rows
        buffer = bitmap.buffer

        # Konwertuj dane bitmapy na tablicę 2D (1 = aktywny piksel, 0 = nieaktywny)
        rendered_char = []
        for row in range(rows):
            row_data = []
            for col in range(width):
                pixel = buffer[row * width + col]
                row_data.append(1 if pixel > 0 else 0)
            rendered_char.append(row_data)

        return rendered_char

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
            char_width = 11  # Szerokość znaku (5 pikseli + 1 przerwy)
            char_height = 14  # Wysokość znaku
            text_start_x = rect_x + (rect_w - len(text) * char_width) // 2
            text_start_y = rect_y + (rect_h - char_height) // 2

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

