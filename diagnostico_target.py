import os
import sys
import ctypes
import ctypes.wintypes
from PIL import ImageGrab
import time

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass

def obtener_rect_cliente(hwnd):
    crect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(crect))
    point = ctypes.wintypes.POINT(0, 0)
    ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + crect.right, point.y + crect.bottom

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
            if 'kathana - the coming' in titulo:
                hwnd_juego = hwnd
            elif ('kathana' in titulo or 'tantra' in titulo) and 'tantra automatic' not in titulo:
                hwnd_juego = hwnd
    return True
user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(callback), 0)

if not hwnd_juego:
    print("[ERROR] No se encontro la ventana del juego (Kathana). Asegurate de que este abierto.")
    sys.exit(1)

print("[OK] Ventana de Kathana encontrada.")
print("Trayendo el juego al frente y esperando 2 segundos...")
user32.SetForegroundWindow(hwnd_juego)
time.sleep(2)

TARGET_X1_PCT = 0.328
TARGET_X2_PCT = 0.625
TARGET_Y1 = 2
TARGET_Y2 = 18

try:
    cx, cy, cr, cb = obtener_rect_cliente(hwnd_juego)
    cw = cr - cx
    ch = cb - cy
    print(f"Resolucion detectada del juego: {cw}x{ch}")
    
    # 1. Caja exacta
    x1 = cx + int(cw * TARGET_X1_PCT)
    y1 = cy + TARGET_Y1
    x2 = cx + int(cw * TARGET_X2_PCT)
    y2 = cy + TARGET_Y2
    img_bot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    img_bot.save("captura_1_caja_bot.png")
    
    # 2. Caja amplia
    wa1 = cx + int(cw * 0.20)
    wy1 = cy
    wa2 = cx + int(cw * 0.80)
    wy2 = cy + 40
    img_amplia = ImageGrab.grab(bbox=(wa1, wy1, wa2, wy2))
    img_amplia.save("captura_2_area_amplia.png")

    print("\n[EXITO] Se guardaron 'captura_1_caja_bot.png' y 'captura_2_area_amplia.png'.")
except Exception as e:
    print(f"[ERROR] {e}")
