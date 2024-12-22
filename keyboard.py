import struct
import mmap
import freetype
import json
import numpy as np



class KeyboardManager:

    LAYOUT = {
            "EN": "EN.json",
            "PL": "PL.json",
            }
    ROWS_LEN = 13
    START_Y = 800
    BYTE_PER_PIXEL = 4
    MAIN_COLOR = (100, 120, 100)
    SEC_COLOR = (255, 255, 0)
    FONT = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"

    def __init__(self, fbm, layout=None):
        if layout is None:
            layout = "EN"
        self.fbm = fbm
        self.layout = layout
        self.face = freetype.Face(self.FONT)
        self.buffer = np.zeros((self.fbm.height, self.fbm.width, 4), dtype=np.uint8)  # 4 for RGBA
        self.stride = self.fbm.width * self.BYTE_PER_PIXEL
        buffer_size = self.buffer.nbytes  # Size of the buffer in bytes
        self.row_height = int((self.fbm.height - self.START_Y) / 5 )-1  # Wysokość jednego rzędu
        self.col_widths = int(self.fbm.width / self.ROWS_LEN) -1  # Szerokość kolumn w każdym wierszu
        self.start_offset = self.START_Y * self.stride
        self.end_offset = self.start_offset + (self.fbm.height - self.START_Y) * self.stride

        # Wczytanie JSON-a
        with open(self.LAYOUT[self.layout], "r") as file:
            layout = []
            keyboard_config = json.load(file)
            keyboard = keyboard_config["keyboard"]["AD1"]
            for row_index, row in enumerate(keyboard):
                y_start = row_index * self.row_height + self.START_Y
                y_end = y_start + self.row_height
                x_start = 0
                for col_index, key in enumerate(row):
                    x_end = x_start + int(self.col_widths * key["width"])
                    layout.append((x_start, y_start, x_end, y_end, key))
                    print((x_start, y_start, x_end, y_end, key))
                    self.draw_rectangle_with_text(
                        rect_x=int(x_start),
                        rect_y=int(y_start),
                        rect_w=int(x_end - x_start),
                        rect_h=int(y_end - y_start),
                        text=key["label"],
                    )
                    x_start = x_end
        #self.fbm.fb.write(self.buffer.tobytes())
        
        print(self.start_offset, self.end_offset)
        self.fbm.fb_map[self.start_offset:self.end_offset] = self.buffer[self.START_Y:self.fbm.height].tobytes()

    def set_pixel(self, x, y, color=None):
        if color is None:
            color = self.MAIN_COLOR
        if 0 <= x < self.fbm.width and 0 <= y < self.fbm.height:
            self.buffer[y, x] = [0, 255, 0, 255]

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

    def draw_rectangle_with_text(self, rect_x=200, rect_y=150, rect_w=400, rect_h=300, text=""):
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
            self.buffer[rect_y:(rect_y + rect_h), rect_x] = [0, 255, 0, 255]
            self.buffer[rect_y:(rect_y + rect_h), (rect_x + rect_w)] = [0,155,155,155]
            self.buffer[rect_y, rect_x:rect_x + rect_w] = [0, 255, 0, 255]
            self.buffer[rect_y+ rect_h, rect_x:rect_x + rect_w] = [0,155,155,155]


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

        except PermissionError:
            print("Nie masz uprawnień do zapisu w /dev/fb0. Uruchom jako root.")
        except FileNotFoundError:
            print(f"Urządzenie {device} nie istnieje.")
        #except Exception as e:
        #    print(f"Wystąpił błąd: {e}")


def generate_keyboard_layout(fbm, max_x, max_y, stride):
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
            fbm.draw_rectangle_with_text(
                width=screen_width ,
                height=screen_height,
                rect_x=int(x_start*0.22),
                rect_y=int(y_start*0.22),
                rect_w=int(0.22 * (x_end - x_start)),
                rect_h=int(0.22 * (y_end - y_start)),
                text=key,
            )

    return layout
