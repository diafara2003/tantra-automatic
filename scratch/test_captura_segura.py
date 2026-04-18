import ctypes
import ctypes.wintypes
from PIL import ImageGrab
import os
import win32api

# Configurar para ser DPI-Aware
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

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
    
    # Coordenadas finales exactas (Minimapa)
    MAP_X1_PCT = 0.78
    MAP_X2_PCT = 0.98
    MAP_Y1 = 10
    MAP_Y2 = 250
    
    x1 = cx + int(cw * MAP_X1_PCT)
    y1 = cy + MAP_Y1
    x2 = cx + int(cw * MAP_X2_PCT)
    y2 = cy + MAP_Y2
    
    # --- LOGICA MULTIMONITOR QUE APLIQUE AL BOT ---
    full_img = ImageGrab.grab(all_screens=True)
    left_most = min([m[2][0] for m in win32api.EnumDisplayMonitors()])
    top_most = min([m[2][1] for m in win32api.EnumDisplayMonitors()])
    
    img = full_img.crop((x1 - left_most, y1 - top_most, x2 - left_most, y2 - top_most))
    img.save("CAPTURA_MODO_SEGURO_FINAL.png")
    print(f"Foto guardada como CAPTURA_MODO_SEGURO_FINAL.png")
else:
    print("No se encontro el juego.")
