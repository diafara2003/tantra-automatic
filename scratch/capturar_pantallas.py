
import ctypes
import ctypes.wintypes
import os
from PIL import ImageGrab

# --- Hacer el proceso DPI-aware (critico para lectura de pixeles) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# --- Funciones de Windows ---
user32 = ctypes.windll.user32

def obtener_ventanas():
    ventanas = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    
    def callback(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buf, length + 1)
                ventanas.append((hwnd, buf.value))
        return True
    
    user32.EnumWindows(WNDENUMPROC(callback), 0)
    return ventanas

def obtener_rect_cliente(hwnd):
    crect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(crect))
    point = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + crect.right, point.y + crect.bottom

# --- Configuración ---
NOMBRE_JUEGO = "Kathana - The coming of the dark ages"
MAP_X1_PCT = 0.75
MAP_X2_PCT = 1.0
MAP_Y1 = 0
MAP_Y2 = 300

# --- Ejecución ---
if __name__ == "__main__":
    print("Buscando ventana...")
    target_hwnd = None
    for hwnd, titulo in obtener_ventanas():
        if NOMBRE_JUEGO.lower() in titulo.lower():
            target_hwnd = hwnd
            print(f"Ventana encontrada: {titulo}")
            break
            
    if not target_hwnd:
        print(f"Error: No se encontró la ventana '{NOMBRE_JUEGO}'")
    else:
        # 1. Capturar Pantalla Completa
        x1, y1, x2, y2 = obtener_rect_cliente(target_hwnd)
        cw = x2 - x1
        ch = y2 - y1
        
        print(f"Capturando pantalla completa ({cw}x{ch})...")
        img_full = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
        path_full = os.path.abspath("juego_completo.png")
        img_full.save(path_full)
        print(f"Guardado en: {path_full}")
        
        # 2. Capturar Minimapa
        mx1 = x1 + int(cw * MAP_X1_PCT)
        my1 = y1 + MAP_Y1
        mx2 = x1 + int(cw * MAP_X2_PCT)
        my2 = y1 + MAP_Y2
        
        print("Capturando minimapa...")
        img_map = ImageGrab.grab(bbox=(mx1, my1, mx2, my2), all_screens=True)
        path_map = os.path.abspath("minimapa.png")
        img_map.save(path_map)
        print(f"Guardado en: {path_map}")
        
        print("\nProceso terminado con éxito.")
