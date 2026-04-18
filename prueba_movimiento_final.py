import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

# Estructuras para SendInput (Simulacion de hardware real)
class KEYBDINPUT(ctypes.Structure):
    _fields_ = (('wVk', wintypes.WORD),
                ('wScan', wintypes.WORD),
                ('dwFlags', wintypes.DWORD),
                ('time', wintypes.DWORD),
                ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)))

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (('ki', KEYBDINPUT),
                    ('mi', ctypes.c_int * 6),
                    ('hi', ctypes.c_int * 4))
    _anonymous_ = ('_input',)
    _fields_ = (('type', wintypes.DWORD),
                ('_input', _INPUT))

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# W Key
VK_W = 0x57
SCAN_W = 0x11 

def press_key(hexKeyCode, scan_code):
    extra = ctypes.c_ulong(0)
    ii_ = INPUT._INPUT()
    ii_.ki = KEYBDINPUT(hexKeyCode, scan_code, KEYEVENTF_SCANCODE, 0, ctypes.pointer(extra))
    x = INPUT(INPUT_KEYBOARD, ii_)
    user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

def release_key(hexKeyCode, scan_code):
    extra = ctypes.c_ulong(0)
    ii_ = INPUT._INPUT()
    ii_.ki = KEYBDINPUT(hexKeyCode, scan_code, KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra))
    x = INPUT(INPUT_KEYBOARD, ii_)
    user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

# Buscar ventana del juego
hwnd_juego = None
def callback(hwnd, _):
    global hwnd_juego
    if user32.IsWindowVisible(hwnd):
        buf = ctypes.create_unicode_buffer(512)
        user32.GetWindowTextW(hwnd, buf, 512)
        titulo = buf.value.lower()
        if 'kathana - the coming' in titulo:
            hwnd_juego = hwnd
    return True

user32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)(callback), 0)

if hwnd_juego:
    print('Trayendo juego al frente...')
    user32.ShowWindow(hwnd_juego, 5) # SW_SHOW
    user32.SetForegroundWindow(hwnd_juego)
    time.sleep(1.0) # Dar tiempo para el foco
    
    print('Simulando W mantenida por 1.5 segundos...')
    press_key(VK_W, SCAN_W)
    time.sleep(1.5)
    release_key(VK_W, SCAN_W)
    print('Prueba finalizada.')
else:
    print('No se encontro el juego.')
