import os
import sys
import ctypes
import ctypes.wintypes
from PIL import ImageGrab
import pytesseract
import time

print("--- INICIANDO DIAGNOSTICO OCR ---")

# 1. Comprobar rutas de Tesseract
_tesseract_paths = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tesseract', 'tesseract.exe'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Tesseract-OCR', 'tesseract.exe'),
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
]
tesseract_encontrado = False
for _tpath in _tesseract_paths:
    if os.path.exists(_tpath):
        pytesseract.pytesseract.tesseract_cmd = _tpath
        tesseract_encontrado = True
        print(f"[OK] Tesseract encontrado en: {_tpath}")
        break

if not tesseract_encontrado:
    print("[ERROR] No se encontro tesseract.exe. Rutas buscadas:")
    for p in _tesseract_paths: print(f" - {p}")
    sys.exit(1)

# 2. Buscar ventana del juego
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
            if 'kathana' in titulo or 'tantra' in titulo:
                hwnd_juego = hwnd
    return True
user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(callback), 0)

if not hwnd_juego:
    print("[ERROR] No se encontro la ventana del juego (Kathana/Tantra).")
    sys.exit(1)

print(f"[OK] Ventana del juego encontrada.")

# 3. Capturar area
def obtener_rect_cliente(hwnd):
    crect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(crect))
    point = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + crect.right, point.y + crect.bottom

# Coordenadas originales del bot
TARGET_X1_PCT = 0.328
TARGET_X2_PCT = 0.625
TARGET_Y1 = 2
TARGET_Y2 = 18

try:
    cx, cy, cr, cb = obtener_rect_cliente(hwnd_juego)
    cw = cr - cx
    print(f"Resolucion detectada: {cw}x{cb-cy}")
    
    x1 = cx + int(cw * TARGET_X1_PCT)
    y1 = cy + TARGET_Y1
    x2 = cx + int(cw * TARGET_X2_PCT)
    y2 = cy + TARGET_Y2
    
    print("Capturando imagen...")
    img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
    img.save("test_target_captura.png")
    
    # OCR
    big = img.resize((img.width * 5, img.height * 5))
    gray = big.convert('L')
    binary = gray.point(lambda p: 255 if p > 160 else 0)
    texto = pytesseract.image_to_string(binary, config='--psm 7').strip()
    
    print(f"\n--- RESULTADO ---")
    print(f"Texto detectado: '{texto}'")
    print(f"Imagen guardada como 'test_target_captura.png'")
    
except Exception as e:
    print(f"[ERROR] {e}")
