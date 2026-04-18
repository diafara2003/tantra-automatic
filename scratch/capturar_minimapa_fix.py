import ctypes
import ctypes.wintypes
from PIL import ImageGrab
import os

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
    print(f"Window at: {cx}, {cy} Size: {cw}x{ch}")
    
    # Grab TOTAL DESKTOP first
    full_img = ImageGrab.grab(all_screens=True)
    
    # Calculate crop coordinates in the full desktop space
    # The full desktop grab (0,0) is the top-left of the primary monitor.
    # cx/cy can be negative.
    # ImageGrab.grab(all_screens=True) usually covers the bounding box of all monitors.
    # We need to find the offset of the bounding box.
    
    import win32api as api
    monitors = api.EnumDisplayMonitors()
    left_most = min([m[2][0] for m in monitors])
    top_most = min([m[2][1] for m in monitors])
    
    print(f"Desktop Offset: {left_most}, {top_most}")
    
    # Area de MINIMAPA (Top Right 25% width, 300px height)
    map_x1 = cx + int(cw * 0.75)
    map_y1 = cy
    map_x2 = cr
    map_y2 = cy + 300
    
    # Convert global screen coordinates to file pixel coordinates
    # (assuming the full image starts at left_most, top_most)
    crop_x1 = map_x1 - left_most
    crop_y1 = map_y1 - top_most
    crop_x2 = map_x2 - left_most
    crop_y2 = map_y2 - top_most
    
    final_box = (crop_x1, crop_y1, crop_x2, crop_y2)
    print(f"Cropping box: {final_box}")
    
    minimap_img = full_img.crop(final_box)
    minimap_img.save("MINIMAPA_DETECCION_ESTRICTA.png")
    print("Guardada MINIMAPA_DETECCION_ESTRICTA.png")
else:
    print("No se encontro el juego.")
