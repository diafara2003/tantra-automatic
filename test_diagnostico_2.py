import os
import sys
import ctypes
import ctypes.wintypes
from PIL import ImageGrab
import pytesseract
import time

# DPI Awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

def obtener_rect_cliente(hwnd):
    crect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(crect))
    point = ctypes.wintypes.POINT(0, 0)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + crect.right, point.y + crect.bottom

def obtener_rect_ventana(hwnd):
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

# Buscar la ventana del juego
user32 = ctypes.windll.user32
hwnd_juego = None
def callback(hwnd, _):
    global hwnd_juego
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            titulo = buf.value.lower()
            if 'kathana' in titulo or 'tantra' in titulo:
                hwnd_juego = hwnd
    return True
user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(callback), 0)

if not hwnd_juego:
    print("Error: No se encontro el juego.")
    sys.exit(1)

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

cx, cy, cr, cb = obtener_rect_cliente(hwnd_juego)
vx, vy, vr, vb = obtener_rect_ventana(hwnd_juego)
cw = cr - cx
ch = cb - cy

print(f"Ventana (Rect): {vx}, {vy}, {vr}, {vb}")
print(f"Cliente (Area Juego): {cx}, {cy}, {cr}, {cb}")
print(f"Tamaño Cliente: {cw}x{ch}")

# Intentar capturar una franja mas ancha para ver donde cae el nombre
# Capturamos del 20% al 80% del ancho, y los primeros 50 pixeles de alto
x1 = cx + int(cw * 0.2)
y1 = cy
x2 = cx + int(cw * 0.8)
y2 = cy + 50

print(f"Capturando area amplia: {x1}, {y1} hasta {x2}, {y2}")
img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
img.save("test_pantalla_superior.png")

# Tambien probamos la caja original
ox1 = cx + int(cw * 0.328)
oy1 = cy + 2
ox2 = cx + int(cw * 0.625)
oy2 = cy + 18
img_orig = ImageGrab.grab(bbox=(ox1, oy1, ox2, oy2))
img_orig.save("test_caja_original.png")

print("He guardado dos imagenes:")
print("1. 'test_pantalla_superior.png': Una franja ancha de la parte superior.")
print("2. 'test_caja_original.png': Lo que el bot intenta leer actualmente.")
print("Por favor, mira las imagenes y dime si en alguna se ve el nombre del monstruo.")
