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

def obtener_rect_ventana(hwnd):
    rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom

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
    print("[ERROR] No se encontro la ventana del juego (Kathana).")
    sys.exit(1)

print("[OK] Ventana encontrada. Tomando captura de la ventana completa en 2 segundos...")
user32.SetForegroundWindow(hwnd_juego)
time.sleep(2)

try:
    vx, vy, vr, vb = obtener_rect_ventana(hwnd_juego)
    print(f"Coordenadas de ventana: {vx}, {vy}, {vr}, {vb}")
    
    img = ImageGrab.grab(bbox=(vx, vy, vr, vb))
    img.save("ventana_completa_juego.png")
    print("\n[EXITO] Se ha guardado 'ventana_completa_juego.png'.")
except Exception as e:
    print(f"[ERROR] {e}")
