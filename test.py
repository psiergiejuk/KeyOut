import evdev
from evdev import UInput, ecodes
import os
import struct
import freetype
import mmap


class FB_Manger:
    
    BYTE_PER_PIXEL = 4
    MAIN_COLOR = (100, 120, 100)
    SEC_COLOR = (255, 255, 0)
    FONT = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"

    def __init__(self, device="/dev/fb0", start_x=800, start_y=0, width=1920, height=1080, font_path=None):
        if font_path is None:
            font_path = self.FONT
        self.fb = open(device, "r+b")
        self.stride = self.width * self.BYTE_PER_PIXEL
        self.fb_map = mmap.mmap(fb.fileno(), self.stride * self.height, mmap.MAP_SHARED, mmap.PROT_WRITE | mmap.PROT_READ)
        self.face = freetype.Face(font_path)

    def set_pixel(self, x, y, color=None):
        if color is None:
            color = self.MAIN_COLOR
        if 0 <= x < self.width and 0 <= y < self.height:
            offset = (y * self.stride) + (x * self.BYTE_PER_PIXEL)
            self.fb_map[offset:offset + 4] = struct.pack("B" * 4, color[2], color[1], color[0], 0)

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

    def draw_rectangle_with_text(self, width=800, height=600, rect_x=200, rect_y=150, rect_w=400, rect_h=300):
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
            for x in range(rect_x, rect_x + rect_w):
                self.set_pixel(x, rect_y, color)
                self.set_pixel(x, rect_y + rect_h - 1, color)

            # Rysowanie lewej i prawej krawędzi
            for y in range(rect_y, rect_y + rect_h):
                self.set_pixel(rect_x, y, color)
                self.set_pixel(rect_x + rect_w - 1, y, color)

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
                            self.set_pixel(text_start_x + col_idx, text_start_y + row_idx, (255, 255, 255))
                text_start_x += len(bitmap[0]) + 2  # Przesunięcie dla kolejnego znaku

                print(f"Narysowano pusty kwadrat z napisem '{text}' w środku.")
        except PermissionError:
            print("Nie masz uprawnień do zapisu w /dev/fb0. Uruchom jako root.")
        except FileNotFoundError:
            print(f"Urządzenie {device} nie istnieje.")
        except Exception as e:
            print(f"Wystąpił błąd: {e}")



def generate_keyboard_layout(max_x, max_y, stride):
    """Generuje układ klawiatury w stylu ThinkPad."""
    # Parametry ekranu i prostokąta
    screen_width = 1920  # szerokość ekranu w pikselach
    screen_height = 1200  # wysokość ekranu w pikselach
    rect_color = (100, 128, 100)  # czerwony kolor linii (RGB)
    text_color = (255, 255, 0)  # Żółty

    rows = [
        ["Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "Back"],
        ["~", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", "Enter"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter", "Enter"],
        ["Shift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Up", "Shift"],
        ["Fn", "Ctrl", "Alt", "Space", "Space", "Alt", "Ctrl", "Left", "Down", "Right"]
    ]

    layout = []
    row_height = max_y/2 // len(rows)  # Wysokość jednego rzędu
    col_widths = [max_x // len(row) for row in rows]  # Szerokość kolumn w każdym wierszu

    for row_index, row in enumerate(rows):
        y_start = row_index * row_height + max_y/2
        y_end = y_start + row_height
        col_width = col_widths[row_index]

        for col_index, key in enumerate(row):
            x_start = col_index * col_width
            x_end = x_start + col_width
            layout.append((x_start, y_start, x_end, y_end, key))
            # Rysowanie prostokąta z tekstem
            draw_rectangle_with_text(
                width=screen_width ,
                height=screen_height,
                rect_x=int(x_start*0.22),
                rect_y=int(y_start*0.22),
                rect_w=int(0.22 * (x_end - x_start)),
                rect_h=int(0.22 * (y_end - y_start)),
                color=rect_color,
                text=key,
                text_color=text_color,
                stride=stride
            )

    return layout

def map_touch_to_key(x, y, layout):
    """Mapuje współrzędne dotyku na klawisz."""
    for x_start, y_start, x_end, y_end, key in layout:
        if x_start <= x < x_end and y_start <= y < y_end:
            return key
    return None


def send_key_to_system(ui, key, is_pressed=True):
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


class Event:
    
    def __init__(self, x, y, slot=0):
        self.x = x
        self.y = y
        self.slot = slot


    def __repr__(self):
        return f"<Event x:{self.x} y:{self.y} slot:{self.slot}>"

class Touch:

    def __init__(self, name="Finger"):
        self.touch_device = self.find_touch_device(name)
        abs_info = self.touch_device.capabilities().get(ecodes.EV_ABS, [])
        self.max_x = None
        self.max_y = None
        for code, abs_data in abs_info:
            if code == ecodes.ABS_X:
                self.max_x = abs_data.max
            elif code == ecodes.ABS_Y:
                self.max_y = abs_data.max

    def find_touch_device(self.device_name):
        """Znajduje urządzenie dotykowe po nazwie."""
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
        for device in devices:
            if device_name.lower() in device.name.lower():
                return device
        raise FileNotFoundError(f"Nie znaleziono urządzenia o nazwie zawierającej: {device_name}")

    def read(self):
        for event in self.touch.read_loop():
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    x = event.value
                elif event.code == ecodes.ABS_Y:
                    y = event.value
                elif event.code == ecodes.ABS_MT_SLOT:  # ID kontaktu
                    touch_data["slot"] = event.value

                # Jeśli współrzędne są dostępne, przetwarzamy Touch Down
                if awaiting_coordinates and x is not None and y is not None:

                    print(f"Processing Touch Down: X={x}, Y={y}")
                    key = map_touch_to_key(x, y, layout)
                    if key == "Fn":
                        layout = generate_keyboard_layout(touch.max_x, touch.max_y, stride)                        
                    if key and pressed_key is None:
                        send_key_to_system(ui, key, is_pressed=True)
                        pressed_key = key
                    awaiting_coordinates = False  # Współrzędne zostały przetworzone

            elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                if event.value == 1:  # Touch Down
                    print(f"Touch Down initiated, waiting for coordinates.")
                    awaiting_coordinates = True
                elif event.value == 0:  # Touch Up
                    print(f"Touch Up: X={x}, Y={y}")
                    if pressed_key:
                        send_key_to_system(ui, pressed_key, is_pressed=False)
                        pressed_key = None  # Zresetuj naciśnięty klawisz
                    x, y = None, None  # Reset współrzędnych
                    awaiting_coordinates = False  # Nie oczekujemy już współrzędnych
            yield event



def main():
    """Główna funkcja programu."""
    try:
        touch = Touch()
        bytes_per_pixel = 4
        stride = touch.max_x * bytes_per_pixel
        layout = generate_keyboard_layout(touch.max_x, max_y, stride)

        ui = UInput(
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
                    ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_LEFT, ecodes.KEY_RIGHT, ecodes.KEY_BACKSPACE,
                ],
                ecodes.EV_SYN: [],
                ecodes.EV_MSC: [ecodes.MSC_SCAN],
            },
            name="Virtual Keyboard",
        )

        print(f"Virtual Keyboard created: {ui.name}")
        print(f"Device node: {ui.device}")

        x, y = None, None
        pressed_key = None  # Śledzi aktualnie naciśnięty klawisz
        awaiting_coordinates = False  # Czy czekamy na współrzędne po Touch Down

        for event in touch.read():

            if 
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    x = event.value
                elif event.code == ecodes.ABS_Y:
                    y = event.value

                # Jeśli współrzędne są dostępne, przetwarzamy Touch Down
                if awaiting_coordinates and x is not None and y is not None:

                    print(f"Processing Touch Down: X={x}, Y={y}")
                    key = map_touch_to_key(x, y, layout)
                    if key == "Fn":
                        layout = generate_keyboard_layout(touch.max_x, touch.max_y, stride)                        
                    if key and pressed_key is None:
                        send_key_to_system(ui, key, is_pressed=True)
                        pressed_key = key
                    awaiting_coordinates = False  # Współrzędne zostały przetworzone

            elif event.type == ecodes.EV_KEY and event.code == ecodes.BTN_TOUCH:
                if event.value == 1:  # Touch Down
                    print(f"Touch Down initiated, waiting for coordinates.")
                    awaiting_coordinates = True
                elif event.value == 0:  # Touch Up
                    print(f"Touch Up: X={x}, Y={y}")
                    if pressed_key:
                        send_key_to_system(ui, pressed_key, is_pressed=False)
                        pressed_key = None  # Zresetuj naciśnięty klawisz
                    x, y = None, None  # Reset współrzędnych
                    awaiting_coordinates = False  # Nie oczekujemy już współrzędnych

    except Exception as e:
        print(f"Błąd: {e}")



if __name__ == "__main__":
    main()

