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
        if 'kathana - the coming' in titulo:
            hwnd_juego = hwnd
        elif 'kathana' in titulo and 'tantra automatic' not in titulo:
            if ':' not in titulo: hwnd_juego = hwnd
    return True

user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(callback), 0)

if hwnd_juego:
    cx, cy, cr, cb = obtener_rect_cliente(hwnd_juego)
    cw = cr - cx
    x1 = cx + int(cw * 0.328)
    y1 = cy + 2
    x2 = cx + int(cw * 0.625)
    y2 = cy + 30 # Nueva altura ampliada
    
    print(f"Capturando area: {x1, y1, x2, y2}")
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
    img.save("nombre_monstruo_corregido.png")
    print("Imagen 'nombre_monstruo_corregido.png' guardada.")
else:
    print("No se encontro el juego.")
