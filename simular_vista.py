import ctypes
import ctypes.wintypes
from PIL import ImageGrab, ImageOps
import pytesseract
import time
import os

# DPI Awareness
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

# Buscar la ventana del juego
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
    
    # Coordenadas exactas del bot actualizado
    TARGET_X1_PCT = 0.328
    TARGET_X2_PCT = 0.625
    TARGET_Y1 = 2
    TARGET_Y2 = 60 
    
    x1 = cx + int(cw * TARGET_X1_PCT)
    y1 = cy + TARGET_Y1
    x2 = cx + int(cw * TARGET_X2_PCT)
    y2 = cy + TARGET_Y2
    
    print(f"Capturando area del bot: {x1, y1, x2, y2}")
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
    img.save("vista_bot_nombre_hp.png")
    
    # Simular procesamiento de OCR
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    big = img.resize((img.width * 4, img.height * 4))
    gray = big.convert('L')
    binary = gray.point(lambda p: 255 if p > 150 else 0)
    binary.save("vista_bot_procesada.png")
    
    texto = pytesseract.image_to_string(binary, config='--psm 6').strip()
    print("\n--- TEXTO QUE LEE EL BOT ---")
    print(texto)
    print("----------------------------")
    print("Imagenes guardadas:")
    print("- 'vista_bot_nombre_hp.png' (Original)")
    print("- 'vista_bot_procesada.png' (Como la ve el OCR)")
else:
    print("No se encontro el juego.")
