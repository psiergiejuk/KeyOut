import evdev
from evdev import UInput, ecodes
import os
import struct

def generate_font_table():
    FONT_10x14 = {
    "A": [
        0x03C0, 0x0420, 0x0810, 0x0810, 0x0810, 0x0FF0, 0x0810, 0x0810, 0x0810, 0x0810,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "B": [
        0x0FE0, 0x0820, 0x0810, 0x0810, 0x0820, 0x0FE0, 0x0820, 0x0810, 0x0810, 0x0820,
        0x0FE0, 0x0000, 0x0000, 0x0000
    ],
    "C": [
        0x03C0, 0x0420, 0x0810, 0x0800, 0x0800, 0x0800, 0x0800, 0x0800, 0x0810, 0x0420,
        0x03C0, 0x0000, 0x0000, 0x0000
    ],
    "D": [
        0x0FC0, 0x0820, 0x0810, 0x0810, 0x0810, 0x0810, 0x0810, 0x0810, 0x0820, 0x0FC0,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "E": [
        0x0FF0, 0x0800, 0x0800, 0x0800, 0x0FF0, 0x0800, 0x0800, 0x0800, 0x0800, 0x0FF0,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "F": [
        0x0FF0, 0x0800, 0x0800, 0x0800, 0x0FF0, 0x0800, 0x0800, 0x0800, 0x0800, 0x0800,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "0": [
        0x03C0, 0x0420, 0x0810, 0x0990, 0x0A50, 0x0C30, 0x0810, 0x0810, 0x0420, 0x03C0,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "1": [
        0x0180, 0x0380, 0x0580, 0x0980, 0x0180, 0x0180, 0x0180, 0x0180, 0x0180, 0x0FF0,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "!": [
        0x0180, 0x0180, 0x0180, 0x0180, 0x0180, 0x0000, 0x0180, 0x0180, 0x0000, 0x0000,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    ".": [
        0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0180, 0x0180, 0x0180,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "?": [
        0x03C0, 0x0600, 0x0810, 0x0020, 0x0040, 0x0080, 0x0100, 0x0200, 0x0200, 0x0000,
        0x0200, 0x0000, 0x0000, 0x0000
    ],
    ":": [
        0x0000, 0x0000, 0x0000, 0x0180, 0x0180, 0x0000, 0x0000, 0x0180, 0x0180, 0x0000,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    ";": [
        0x0000, 0x0000, 0x0000, 0x0180, 0x0180, 0x0000, 0x0000, 0x0180, 0x00C0, 0x0060,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "'": [
        0x0180, 0x0180, 0x0180, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "-": [
        0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0FF0, 0x0000, 0x0000, 0x0000, 0x0000,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "_": [
        0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0FFF,
        0x0000, 0x0000, 0x0000, 0x0000
    ],
    "/": [
        0x0003, 0x0006, 0x000C, 0x0018, 0x0030, 0x0060, 0x00C0, 0x0180, 0x0300, 0x0600,
        0x0000, 0x0000, 0x0000, 0x0000
    ]
    # Kontynuuj dla wszystkich liter, cyfr i znaków
    }
    font_5x7 = {
        "A": [0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
        "B": [0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110],
        "C": [0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110],
        "D": [0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110],
        "E": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111],
        "F": [0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000],
        "G": [0b01110, 0b10001, 0b10000, 0b10011, 0b10001, 0b10001, 0b01110],
        "H": [0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001],
        "I": [0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
        "J": [0b00001, 0b00001, 0b00001, 0b00001, 0b10001, 0b10001, 0b01110],
        "K": [0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001],
        "L": [0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111],
        "M": [0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001],
        "N": [0b10001, 0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001],
        "O": [0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
        "P": [0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000],
        "Q": [0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101],
        "R": [0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001],
        "S": [0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110],
        "T": [0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100],
        "U": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110],
        "V": [0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100],
        "W": [0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010],
        "X": [0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001],
        "Y": [0b10001, 0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100],
        "Z": [0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111],
        "0": [0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110],
        "1": [0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110],
        "2": [0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111],
        "3": [0b01110, 0b10001, 0b00001, 0b00110, 0b00001, 0b10001, 0b01110],
        "4": [0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010],
        "5": [0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110],
        "6": [0b01110, 0b10000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110],
        "7": [0b11111, 0b00001, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000],
        "8": [0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110],
        "9": [0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00001, 0b01110],
    }
    return font_5x7


def draw_rectangle_with_text(device="/dev/fb0", width=800, height=600, rect_x=200, rect_y=150, rect_w=400, rect_h=300, color=(255, 255, 255), text="Hello", text_color=(255, 255, 255)):
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
    # Generowanie tablicy fontów
    font_table = generate_font_table()
    try:
        with open(device, "r+b") as fb:
            bytes_per_pixel = 4
            stride = width * bytes_per_pixel

            def set_pixel(x, y, color):
                if 0 <= x < width and 0 <= y < height:
                    offset = (y * stride) + (x * bytes_per_pixel)
                    fb.seek(offset)
                    fb.write(struct.pack("B" * 4, color[2], color[1], color[0], 0))

            # Rysowanie górnej i dolnej krawędzi
            for x in range(rect_x, rect_x + rect_w):
                set_pixel(x, rect_y, color)
                set_pixel(x, rect_y + rect_h - 1, color)

            # Rysowanie lewej i prawej krawędzi
            for y in range(rect_y, rect_y + rect_h):
                set_pixel(rect_x, y, color)
                set_pixel(rect_x + rect_w - 1, y, color)

            # Rysowanie tekstu w środku
            char_width = 6  # Szerokość znaku (5 pikseli + 1 przerwy)
            char_height = 7  # Wysokość znaku
            text_start_x = rect_x + (rect_w - len(text) * char_width) // 2
            text_start_y = rect_y + (rect_h - char_height) // 2
            for i, char in enumerate(text):
                if char in font_table:
                    char_bitmap = font_table[char]
                    char_x = text_start_x + i * char_width
                    for row, row_data in enumerate(char_bitmap):
                        for col in range(5):  # Każda litera ma 5 kolumn
                            if row_data & (1 << (4 - col)):
                                set_pixel(char_x + col, text_start_y + row, text_color)

            print(f"Narysowano pusty kwadrat z napisem '{text}' w środku.")
    except PermissionError:
        print("Nie masz uprawnień do zapisu w /dev/fb0. Uruchom jako root.")
    except FileNotFoundError:
        print(f"Urządzenie {device} nie istnieje.")
    except Exception as e:
        print(f"Wystąpił błąd: {e}")



def find_touch_device(device_name):
    """Znajduje urządzenie dotykowe po nazwie."""
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if device_name.lower() in device.name.lower():
            return device
    raise FileNotFoundError(f"Nie znaleziono urządzenia o nazwie zawierającej: {device_name}")


def generate_keyboard_layout(max_x, max_y):
    """Generuje układ klawiatury w stylu ThinkPad."""
    # Parametry ekranu i prostokąta
    screen_width = 1920  # szerokość ekranu w pikselach
    screen_height = 1200  # wysokość ekranu w pikselach
    rect_color = (100, 128, 100)  # czerwony kolor linii (RGB)
    text_color = (255, 255, 0)  # Żółty

    rows = [
        ["Esc", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12", "PrtSc"],
        ["~", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="],
        ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]"],
        ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
        ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Shift"],
        ["Fn", "Ctrl", "Alt", "Space", "Alt", "Ctrl", "Left", "Down", "Up", "Right"]
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
                text_color=text_color
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
        "PrtSc": ecodes.KEY_PRINT,
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


def main():
    """Główna funkcja programu."""
    try:
        device_name = "Finger"
        touch_device = find_touch_device(device_name)

        abs_info = touch_device.capabilities().get(ecodes.EV_ABS, [])
        max_x = max_y = None
        for code, abs_data in abs_info:
            if code == ecodes.ABS_X:
                max_x = abs_data.max
            elif code == ecodes.ABS_Y:
                max_y = abs_data.max

        layout = generate_keyboard_layout(max_x, max_y)

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
                    ecodes.KEY_UP, ecodes.KEY_DOWN, ecodes.KEY_LEFT, ecodes.KEY_RIGHT
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

        for event in touch_device.read_loop():
            if event.type == ecodes.EV_ABS:
                if event.code == ecodes.ABS_X:
                    x = event.value
                elif event.code == ecodes.ABS_Y:
                    y = event.value

                # Jeśli współrzędne są dostępne, przetwarzamy Touch Down
                if awaiting_coordinates and x is not None and y is not None:
                    print(f"Processing Touch Down: X={x}, Y={y}")
                    key = map_touch_to_key(x, y, layout)
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

