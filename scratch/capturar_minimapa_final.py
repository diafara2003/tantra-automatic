import ctypes
import ctypes.wintypes
from PIL import ImageGrab
import os

user32 = ctypes.windll.user32
hwnd = user32.FindWindowW(None, "Kathana - The Coming of the Dark Ages")

def obtener_rect_cliente(hwnd):
    crect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(crect))
    p = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(p))
    return p.x, p.y, p.x + crect.right, p.y + crect.bottom

if hwnd:
    cx, cy, cr, cb = obtener_rect_cliente(hwnd)
    cw, ch = (cr - cx), (cb - cy)
    
    # Nuevas Coordenadas del Minimapa (78% - 98%)
    MAP_X1_PCT = 0.78
    MAP_X2_PCT = 0.98
    MAP_Y1 = 10
    MAP_Y2 = 250
    
    x1 = cx + int(cw * MAP_X1_PCT)
    y1 = cy + MAP_Y1
    x2 = cx + int(cw * MAP_X2_PCT)
    y2 = cy + MAP_Y2
    
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
    img.save("CAPTURA_MINIMAPA_FINAL.png")
    print(f"Foto guardada como CAPTURA_MINIMAPA_FINAL.png")
else:
    print("No se encontro el juego.")
