import ctypes
import ctypes.wintypes
from PIL import ImageGrab
import time

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try: ctypes.windll.user32.SetProcessDPIAware()
    except Exception: pass

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
    print(f"Esquina superior izquierda del juego: {cx}, {cy}")
    
    # 1. Captura de la esquina superior izquierda (HP/Mana)
    # Tomamos un cuadro de 300x150 para ver toda la zona de barras
    img_hp = ImageGrab.grab(bbox=(cx, cy, cx + 300, cy + 150), all_screens=True)
    img_hp.save("check_hp_area.png")
    
    # 2. Captura de la zona superior central (Target/Monstruo)
    # Tomamos una franja mas ancha y alta
    cw = cr - cx
    x1 = cx + int(cw * 0.2)
    x2 = cx + int(cw * 0.8)
    img_target = ImageGrab.grab(bbox=(x1, cy, x2, cy + 100), all_screens=True)
    img_target.save("check_target_area.png")
    
    print("Imagenes 'check_hp_area.png' y 'check_target_area.png' guardadas.")
else:
    print("No se encontro el juego.")
