import ctypes
import ctypes.wintypes
from PIL import ImageGrab, ImageOps
import pytesseract
import time
import os

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32

def obtener_rect_cliente(hwnd):
    crect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(crect))
    point = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + crect.right, point.y + crect.bottom

hwnd_juego = None
def callback(hwnd, _):
    global hwnd_juego
    if user32.IsWindowVisible(hwnd):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        titulo = buf.value.lower()
        if 'kathana - the coming' in titulo or ('kathana' in titulo and 'tantra automatic' not in titulo and ':' not in titulo):
            hwnd_juego = hwnd
    return True

user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(callback), 0)

if hwnd_juego:
    cx, cy, cr, cb = obtener_rect_cliente(hwnd_juego)
    cw = cr - cx
    
    # Coordenadas bot (Y ampliado a 60)
    x1 = cx + int(cw * 0.328)
    y1 = cy + 2
    x2 = cx + int(cw * 0.625)
    y2 = cy + 60 
    
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
    img.save("vista_bot_reintento.png")
    
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    big = img.resize((img.width * 4, img.height * 4))
    gray = big.convert('L')
    
    # Probar 3 umbrales distintos para ver cual pilla mejor los numeros rojos
    for threshold in [100, 130, 160]:
        binary = gray.point(lambda p: 255 if p > threshold else 0)
        binary.save(f"test_filtro_{threshold}.png")
        res = pytesseract.image_to_string(binary, config='--psm 6').strip()
        print(f"Umbral {threshold}: '{res}'")

    print("\nNuevas imagenes guardadas. Revisa 'vista_bot_reintento.png' y los 'test_filtro_XXX.png'")
else:
    print("No se encontro el juego.")
