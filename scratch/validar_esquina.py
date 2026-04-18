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
    # Captura TOTAL para diagnostico real
    cx, cy, cr, cb = obtener_rect_cliente(hwnd)
    img = ImageGrab.grab(bbox=(cx, cy, cr, cb), all_screens=True)
    img.save("CAPTURA_CLIENTE_TOTAL.png")
    
    # Captura ESQUINA SUPERIOR DERECHA (30% ancho, 30% alto)
    cw = cr - cx
    ch = cb - cy
    x1 = cx + int(cw * 0.70)
    y1 = cy
    x2 = cr
    y2 = cy + int(ch * 0.35)
    
    img_corner = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
    img_corner.save("PRUEBA_ESQUINA_DERECHA.png")
    
    print(f"Resolucion detectada: {cw}x{ch}")
    print(f"Guardadas CAPTURA_CLIENTE_TOTAL.png y PRUEBA_ESQUINA_DERECHA.png")
else:
    print("No se encontro el juego.")
