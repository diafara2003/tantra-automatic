"""
Tantra Automatic - Bot para Kathana / Tantra Online
Recreado en Python con tkinter
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ctypes
import ctypes.wintypes
import threading
import json
import os
import sys
import time

# OCR para lectura de nombres de monstruos
try:
    import pytesseract
    from PIL import ImageGrab, ImageOps
    # Buscar Tesseract
    # Buscar Tesseract: primero junto al exe, luego en Program Files
    _base = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    _tesseract_paths = [
        os.path.join(_base, 'tesseract', 'tesseract.exe'),
        os.path.join(_base, 'Tesseract-OCR', 'tesseract.exe'),
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    for _tpath in _tesseract_paths:
        if os.path.exists(_tpath):
            pytesseract.pytesseract.tesseract_cmd = _tpath
            break
    OCR_DISPONIBLE = True
except ImportError:
    OCR_DISPONIBLE = False

# ─── Hacer el proceso DPI-aware (critico para lectura de pixeles) ────
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# ─── Constantes Win32 ────────────────────────────────────────────────
WM_KEYDOWN = 0x0100

VK_CODES = {
    'E': 0x45, 'R': 0x52, 'F': 0x46, 'T': 0x54,
    'W': 0x57, 'A': 0x41, 'S': 0x53, 'D': 0x44,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74,
    'F6': 0x75, 'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79,
}

VK_LSHIFT = 0xA0
VK_LCONTROL = 0xA2

# ─── Posiciones relativas de las barras HP/Mana en la ventana del juego ──
# Detectadas del cliente Kathana con DPI awareness (escala real)
# Filas seleccionadas para evitar texto superpuesto ("330/330", "137/170")
HP_BAR_Y = 76        # fila limpia de la barra HP (rango completo: 74-86)
HP_BAR_X_START = 15   # inicio de la barra
HP_BAR_X_END = 228    # final de la barra

MANA_BAR_Y = 91       # fila limpia de la barra Mana (rango completo: 89-103)
MANA_BAR_X_START = 16
MANA_BAR_X_END = 228

# Panel de target (nombre del monstruo seleccionado) - parte superior derecha
TARGET_X1_PCT = 0.328   # 32.8% del ancho
TARGET_X2_PCT = 0.625   # 62.5% del ancho
TARGET_Y1 = 2           # fila inicio
TARGET_Y2 = 18          # fila fin

# ─── Funciones Win32 ─────────────────────────────────────────────────
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

SendMessage = user32.SendMessageW
SendMessage.argtypes = [ctypes.wintypes.HWND, ctypes.c_uint,
                        ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
SendMessage.restype = ctypes.wintypes.LPARAM

FindWindow = user32.FindWindowW
FindWindow.argtypes = [ctypes.wintypes.LPCWSTR, ctypes.wintypes.LPCWSTR]
FindWindow.restype = ctypes.wintypes.HWND

SetWindowText = user32.SetWindowTextW
SetWindowText.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPCWSTR]
SetWindowText.restype = ctypes.wintypes.BOOL

GetWindowDC = user32.GetWindowDC
GetWindowDC.argtypes = [ctypes.wintypes.HWND]
GetWindowDC.restype = ctypes.wintypes.HDC

ReleaseDC = user32.ReleaseDC
ReleaseDC.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.HDC]
ReleaseDC.restype = ctypes.c_int

GetPixel_fn = gdi32.GetPixel
GetPixel_fn.argtypes = [ctypes.wintypes.HDC, ctypes.c_int, ctypes.c_int]
GetPixel_fn.restype = ctypes.wintypes.COLORREF

GetAsyncKeyState = user32.GetAsyncKeyState
GetAsyncKeyState.argtypes = [ctypes.c_int]
GetAsyncKeyState.restype = ctypes.c_short

GetWindowRect = user32.GetWindowRect
GetWindowRect.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(ctypes.wintypes.RECT)]
GetWindowRect.restype = ctypes.wintypes.BOOL

SetForegroundWindow = user32.SetForegroundWindow
SetForegroundWindow.argtypes = [ctypes.wintypes.HWND]
SetForegroundWindow.restype = ctypes.wintypes.BOOL

IsWindowVisible = user32.IsWindowVisible
IsWindowVisible.argtypes = [ctypes.wintypes.HWND]
IsWindowVisible.restype = ctypes.wintypes.BOOL

GetWindowTextW = user32.GetWindowTextW
GetWindowTextW.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.LPWSTR, ctypes.c_int]
GetWindowTextW.restype = ctypes.c_int

GetWindowTextLengthW = user32.GetWindowTextLengthW
GetWindowTextLengthW.argtypes = [ctypes.wintypes.HWND]
GetWindowTextLengthW.restype = ctypes.c_int

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
EnumWindows = user32.EnumWindows
EnumWindows.argtypes = [WNDENUMPROC, ctypes.wintypes.LPARAM]
EnumWindows.restype = ctypes.wintypes.BOOL


# ─── Funciones auxiliares ─────────────────────────────────────────────

def obtener_ventanas_visibles():
    """Devuelve lista de (hwnd, titulo) de ventanas visibles."""
    ventanas = []
    def callback(hwnd, _lparam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                GetWindowTextW(hwnd, buf, length + 1)
                titulo = buf.value.strip()
                if titulo:
                    ventanas.append((hwnd, titulo))
        return True
    EnumWindows(WNDENUMPROC(callback), 0)
    return ventanas


def obtener_color_pixel(x, y):
    """Lee color de pixel en coordenadas de pantalla. Devuelve (R, G, B)."""
    hdc = GetWindowDC(0)
    color = GetPixel_fn(hdc, x, y)
    ReleaseDC(0, hdc)
    if color == 0xFFFFFFFF:
        return (0, 0, 0)
    r = color & 0xFF
    g = (color >> 8) & 0xFF
    b = (color >> 16) & 0xFF
    return (r, g, b)


def es_rojo_hp(color):
    """Verifica si el color corresponde a la barra de HP llena (rojo)."""
    r, g, b = color
    return r > 120 and g < 60 and b < 60


def es_azul_mana(color):
    """Verifica si el color corresponde a la barra de Mana llena (azul)."""
    r, g, b = color
    return b > 100 and b > r and b > g


def obtener_rect_ventana(hwnd):
    """Obtiene las coordenadas de la ventana del juego (incluye barra titulo)."""
    rect = ctypes.wintypes.RECT()
    GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right, rect.bottom


def obtener_rect_cliente(hwnd):
    """Obtiene las coordenadas del area de juego (sin barra de titulo)."""
    crect = ctypes.wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(crect))
    point = ctypes.wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, point.x + crect.right, point.y + crect.bottom


def enviar_tecla(hwnd, vk_code):
    """Envia una pulsacion de tecla a la ventana objetivo."""
    if hwnd:
        SendMessage(hwnd, WM_KEYDOWN, vk_code, 0)


def leer_nombre_target(hwnd):
    """Lee el nombre del monstruo seleccionado usando OCR.
    El juego debe estar visible en pantalla (no trae el juego al frente)."""
    if not OCR_DISPONIBLE:
        return ""
    try:
        import re
        cx, cy, cr, cb = obtener_rect_cliente(hwnd)
        cw = cr - cx
        if cw < 100:
            return ""

        x1 = cx + int(cw * TARGET_X1_PCT)
        y1 = cy + TARGET_Y1
        x2 = cx + int(cw * TARGET_X2_PCT)
        y2 = cy + TARGET_Y2

        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        big = img.resize((img.width * 5, img.height * 5))
        gray = big.convert('L')
        binary = gray.point(lambda p: 255 if p > 160 else 0)
        texto = pytesseract.image_to_string(binary, config='--psm 7').strip()

        # Limpiar
        texto = texto.strip('-').strip()
        texto = re.sub(r'\s*Lv\.?\s*\d+.*$', '', texto).strip()
        texto = re.sub(r'^[^a-zA-Z]+', '', texto)
        texto = re.sub(r'[^a-zA-Z\s]+$', '', texto).strip()

        if len(texto) >= 3:
            return texto
        return ""
    except Exception:
        return ""


# ─── Aplicacion Principal ────────────────────────────────────────────

class TantraAutomatic(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Tantra Automatic - Python v1.0")
        self.geometry("650x500")
        self.resizable(True, True)
        self.minsize(650, 500)

        # Estado
        self.activo = False
        self.hwnd_objetivo = None
        self.titulo_objetivo = None
        self.skill_timers = {}
        self.autopot_timer_id = None
        self.basic_e_timer_id = None
        self.basic_r_timer_id = None
        self.pick_timer_id = None

        # AutoPot - porcentaje de HP/Mana para activar pocion
        self.hp_porcentaje = tk.IntVar(value=50)
        self.mana_porcentaje = tk.IntVar(value=50)

        # Contador de intentos fallidos para mover al personaje
        self.intentos_fallidos = 0
        self.MAX_INTENTOS = 5

        # Estado de huida (correr cuando HP esta bajo)
        self.huyendo = False
        self.huida_timer_id = None

        # Hilo de hotkey global
        self.hotkey_activo = True
        self.hotkey_thread = threading.Thread(target=self._escuchar_hotkey, daemon=True)
        self.hotkey_thread.start()

        # Construir GUI
        self._construir_gui()
        self._refrescar_procesos()

        self.protocol("WM_DELETE_WINDOW", self._al_cerrar)

    def _al_cerrar(self):
        self.hotkey_activo = False
        if self.activo:
            self._detener()
        self.destroy()

    # ─── Construccion de la GUI ───────────────────────────────────

    def _construir_gui(self):
        # Barra superior: Selector de proceso
        frame_proceso = ttk.LabelFrame(self, text="Proceso", padding=5)
        frame_proceso.pack(fill="x", padx=8, pady=(8, 4))

        self.combo_proceso = ttk.Combobox(frame_proceso, state="readonly", width=40)
        self.combo_proceso.pack(side="left", padx=(0, 5))
        self.combo_proceso.bind("<<ComboboxSelected>>", self._al_seleccionar_proceso)

        ttk.Button(frame_proceso, text="Actualizar", command=self._refrescar_procesos,
                   width=10).pack(side="left", padx=2)

        ttk.Separator(frame_proceso, orient="vertical").pack(side="left", fill="y", padx=8)

        ttk.Label(frame_proceso, text="Renombrar:").pack(side="left")
        self.entry_renombrar = ttk.Entry(frame_proceso, width=18)
        self.entry_renombrar.pack(side="left", padx=(4, 4))
        ttk.Button(frame_proceso, text="Aplicar", command=self._renombrar_proceso,
                   width=7).pack(side="left")

        # Pestanas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=4)

        self._construir_tab_skills()
        self._construir_tab_filtro()
        self._construir_tab_autopot()
        self._construir_tab_presets()

        # Barra inferior: Iniciar/Detener
        frame_inferior = ttk.Frame(self, padding=5)
        frame_inferior.pack(fill="x", padx=8, pady=(0, 8))

        self.btn_iniciar = ttk.Button(frame_inferior, text="INICIAR", command=self._alternar_inicio)
        self.btn_iniciar.pack(side="left", ipadx=20, ipady=5)

        self.label_estado = ttk.Label(frame_inferior, text="Detenido", foreground="red")
        self.label_estado.pack(side="left", padx=10)

        ttk.Label(frame_inferior, text="Ctrl+Shift = Iniciar/Detener",
                  foreground="gray").pack(side="right")

    def _construir_tab_skills(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="Skills")

        # ── Ataque Basico ──
        frame_basico = ttk.LabelFrame(tab, text="Ataque Basico", padding=5)
        frame_basico.pack(fill="x", pady=(0, 6))

        self.basico_activado = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_basico, text="Activar",
                        variable=self.basico_activado).grid(row=0, column=0, padx=4)

        ttk.Label(frame_basico, text="E (ataque) seg:").grid(row=0, column=1, padx=(10, 2))
        self.intervalo_e = ttk.Entry(frame_basico, width=5)
        self.intervalo_e.insert(0, "1")
        self.intervalo_e.grid(row=0, column=2, padx=2)

        ttk.Label(frame_basico, text="R (skill) seg:").grid(row=0, column=3, padx=(10, 2))
        self.intervalo_r = ttk.Entry(frame_basico, width=5)
        self.intervalo_r.insert(0, "1")
        self.intervalo_r.grid(row=0, column=4, padx=2)

        self.modo_mago = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_basico, text="Mago (sin R)",
                        variable=self.modo_mago,
                        command=self._al_cambiar_mago).grid(row=0, column=5, padx=(10, 0))

        # ── Recoger Items ──
        frame_recoger = ttk.LabelFrame(tab, text="Recoger Items (tecla F)", padding=5)
        frame_recoger.pack(fill="x", pady=(0, 6))

        self.recoger_activado = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_recoger, text="Activar",
                        variable=self.recoger_activado).pack(side="left", padx=4)
        ttk.Label(frame_recoger, text="Intervalo (seg):").pack(side="left", padx=(10, 2))
        self.intervalo_recoger = ttk.Entry(frame_recoger, width=5)
        self.intervalo_recoger.insert(0, "1")
        self.intervalo_recoger.pack(side="left", padx=2)

        # ── Skills Primarios (1-0) ──
        frame_primario = ttk.LabelFrame(tab, text="Skills Primarios (1-0)", padding=5)
        frame_primario.pack(fill="x", pady=(0, 6))

        self.checks_primarios = []
        self.intervalos_primarios = []
        teclas_primarias = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']

        for i, tecla in enumerate(teclas_primarias):
            ttk.Label(frame_primario, text=tecla, font=("Segoe UI", 8)).grid(row=0, column=i, padx=4)
            entry = ttk.Entry(frame_primario, width=4)
            entry.insert(0, "1")
            entry.grid(row=1, column=i, padx=4, pady=2)
            self.intervalos_primarios.append(entry)
            var = tk.BooleanVar(value=False)
            ttk.Checkbutton(frame_primario, variable=var).grid(row=2, column=i, padx=4)
            self.checks_primarios.append(var)

        # ── Skills Secundarios (F1-F10) ──
        frame_secundario = ttk.LabelFrame(tab, text="Skills Secundarios (F1-F10)", padding=5)
        frame_secundario.pack(fill="x", pady=(0, 2))

        self.checks_secundarios = []
        self.intervalos_secundarios = []
        teclas_secundarias = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10']

        for i, tecla in enumerate(teclas_secundarias):
            ttk.Label(frame_secundario, text=tecla, font=("Segoe UI", 8)).grid(row=0, column=i, padx=4)
            entry = ttk.Entry(frame_secundario, width=4)
            entry.insert(0, "1")
            entry.grid(row=1, column=i, padx=4, pady=2)
            self.intervalos_secundarios.append(entry)
            var = tk.BooleanVar(value=False)
            ttk.Checkbutton(frame_secundario, variable=var).grid(row=2, column=i, padx=4)
            self.checks_secundarios.append(var)

    def _construir_tab_filtro(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="Filtro Monstruos")

        # Activar filtro
        self.filtro_activado = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Activar filtro de monstruos (solo atacar los indicados)",
                        variable=self.filtro_activado).pack(anchor="w", pady=(0, 8))

        # Lista de nombres
        frame_nombres = ttk.LabelFrame(tab, text="Monstruos a atacar", padding=8)
        frame_nombres.pack(fill="both", expand=True, pady=(0, 8))

        # Entry + boton agregar
        frame_agregar = ttk.Frame(frame_nombres)
        frame_agregar.pack(fill="x", pady=(0, 5))

        ttk.Label(frame_agregar, text="Nombre:").pack(side="left", padx=(0, 4))
        self.entry_monstruo = ttk.Entry(frame_agregar, width=30)
        self.entry_monstruo.pack(side="left", padx=(0, 4))
        ttk.Button(frame_agregar, text="Agregar", command=self._agregar_monstruo,
                   width=8).pack(side="left", padx=2)
        ttk.Button(frame_agregar, text="Quitar", command=self._quitar_monstruo,
                   width=8).pack(side="left", padx=2)

        # Listbox con los nombres
        self.listbox_monstruos = tk.Listbox(frame_nombres, height=6)
        self.listbox_monstruos.pack(fill="both", expand=True, padx=4, pady=4)

        # Estado de deteccion
        frame_estado = ttk.LabelFrame(tab, text="Estado", padding=8)
        frame_estado.pack(fill="x", pady=(0, 8))

        self.label_target_actual = ttk.Label(frame_estado, text="Target actual: --",
                                              font=("Segoe UI", 10))
        self.label_target_actual.pack(anchor="w", pady=2)

        self.label_filtro_estado = ttk.Label(frame_estado, text="Filtro inactivo",
                                              foreground="gray")
        self.label_filtro_estado.pack(anchor="w", pady=2)

        # Instrucciones
        frame_info = ttk.LabelFrame(tab, text="Como funciona", padding=8)
        frame_info.pack(fill="x")

        instrucciones = (
            "1. Agrega los nombres de los monstruos que quieres atacar\n"
            "2. Activa el filtro con el checkbox\n"
            "3. Al iniciar, el bot leera el nombre del monstruo seleccionado\n"
            "4. Si el nombre coincide: ejecuta R y skills 1-8\n"
            "5. Si NO coincide: presiona E para buscar otro objetivo\n"
            "6. La comparacion ignora mayusculas/minusculas\n"
            "7. El nombre debe ser EXACTO (ej: 'Vasabhum Caura', no solo 'Vasabhum')"
        )
        ttk.Label(frame_info, text=instrucciones, wraplength=550, justify="left").pack()

    def _agregar_monstruo(self):
        nombre = self.entry_monstruo.get().strip()
        if not nombre:
            return
        # Evitar duplicados
        items = self.listbox_monstruos.get(0, tk.END)
        if nombre.lower() not in [item.lower() for item in items]:
            self.listbox_monstruos.insert(tk.END, nombre)
            self.entry_monstruo.delete(0, tk.END)

    def _quitar_monstruo(self):
        sel = self.listbox_monstruos.curselection()
        if sel:
            self.listbox_monstruos.delete(sel[0])

    def _obtener_lista_monstruos(self):
        """Devuelve la lista de nombres de monstruos permitidos."""
        return list(self.listbox_monstruos.get(0, tk.END))

    def _nombre_coincide(self, nombre_detectado):
        """Verifica si el nombre detectado es exactamente igual a alguno de la lista."""
        if not nombre_detectado:
            return False
        nombre_lower = nombre_detectado.strip().lower()
        for permitido in self._obtener_lista_monstruos():
            if permitido.strip().lower() == nombre_lower:
                return True
        return False

    def _construir_tab_autopot(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="AutoPot")

        self.autopot_activado = tk.BooleanVar(value=False)
        ttk.Checkbutton(tab, text="Activar AutoPot (deteccion automatica)",
                        variable=self.autopot_activado,
                        command=self._al_cambiar_autopot).pack(anchor="w", pady=(0, 10))

        # Estado de deteccion
        frame_estado = ttk.LabelFrame(tab, text="Estado de Deteccion", padding=8)
        frame_estado.pack(fill="x", pady=(0, 8))

        self.label_hp_estado = ttk.Label(frame_estado, text="HP: --", font=("Segoe UI", 10))
        self.label_hp_estado.pack(anchor="w", pady=2)

        self.label_mana_estado = ttk.Label(frame_estado, text="Mana: --", font=("Segoe UI", 10))
        self.label_mana_estado.pack(anchor="w", pady=2)

        self.label_deteccion = ttk.Label(frame_estado, text="Deteccion inactiva", foreground="gray")
        self.label_deteccion.pack(anchor="w", pady=2)

        # Configuracion de porcentaje
        frame_config = ttk.LabelFrame(tab, text="Configuracion", padding=8)
        frame_config.pack(fill="x", pady=(0, 8))

        # HP threshold
        frame_hp = ttk.Frame(frame_config)
        frame_hp.pack(fill="x", pady=2)
        ttk.Label(frame_hp, text="Usar pocion HP cuando baje de:").pack(side="left")
        self.spin_hp = ttk.Spinbox(frame_hp, from_=10, to=90, width=4,
                                    textvariable=self.hp_porcentaje)
        self.spin_hp.pack(side="left", padx=4)
        ttk.Label(frame_hp, text="% (slot 9)").pack(side="left")

        # Mana threshold
        frame_mana = ttk.Frame(frame_config)
        frame_mana.pack(fill="x", pady=2)
        ttk.Label(frame_mana, text="Usar pocion Mana cuando baje de:").pack(side="left")
        self.spin_mana = ttk.Spinbox(frame_mana, from_=10, to=90, width=4,
                                      textvariable=self.mana_porcentaje)
        self.spin_mana.pack(side="left", padx=4)
        ttk.Label(frame_mana, text="% (slot 0)").pack(side="left")

        # Instrucciones
        frame_info = ttk.LabelFrame(tab, text="Como funciona", padding=8)
        frame_info.pack(fill="x")

        instrucciones = (
            "El sistema detecta automaticamente las barras de HP y Mana\n"
            "dentro de la ventana del juego Kathana.\n\n"
            "1. Coloca la pocion de HP en el slot 9 y la de Mana en el slot 0\n"
            "2. Activa AutoPot con el checkbox de arriba\n"
            "3. El programa lee los pixeles de las barras y envia la tecla\n"
            "   correspondiente cuando el nivel baja del porcentaje configurado\n\n"
            "Nota: Los slots 9 y 0 se reservan para pociones cuando esta activo."
        )
        ttk.Label(frame_info, text=instrucciones, wraplength=550, justify="left").pack()

    def _construir_tab_presets(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="Presets")

        frame_nombre = ttk.Frame(tab)
        frame_nombre.pack(fill="x", pady=(0, 10))

        ttk.Label(frame_nombre, text="Nombre del preset:").pack(side="left", padx=(0, 5))
        self.entry_preset = ttk.Entry(frame_nombre, width=30)
        self.entry_preset.pack(side="left", padx=(0, 10))

        ttk.Button(frame_nombre, text="Guardar", command=self._guardar_preset,
                   width=8).pack(side="left", padx=2)
        ttk.Button(frame_nombre, text="Cargar", command=self._cargar_preset,
                   width=8).pack(side="left", padx=2)

        # Lista de presets
        frame_lista = ttk.LabelFrame(tab, text="Presets Guardados", padding=5)
        frame_lista.pack(fill="both", expand=True)

        self.listbox_presets = tk.Listbox(frame_lista, height=10)
        self.listbox_presets.pack(fill="both", expand=True, padx=4, pady=4)
        self.listbox_presets.bind("<<ListboxSelect>>", self._al_seleccionar_preset)

        self._refrescar_presets()

        ttk.Label(tab, text="Los presets se guardan en formato JSON en la carpeta 'presets'",
                  foreground="gray").pack(pady=(8, 0))

    # ─── Gestion de Procesos ──────────────────────────────────────

    def _refrescar_procesos(self):
        ventanas = obtener_ventanas_visibles()
        self._lista_ventanas = ventanas
        titulos = [titulo for _, titulo in ventanas]
        self.combo_proceso['values'] = titulos

        for i, titulo in enumerate(titulos):
            if 'kathana' in titulo.lower() or 'tantra' in titulo.lower():
                self.combo_proceso.current(i)
                self._al_seleccionar_proceso(None)
                break

    def _al_seleccionar_proceso(self, event):
        idx = self.combo_proceso.current()
        if 0 <= idx < len(self._lista_ventanas):
            hwnd, titulo = self._lista_ventanas[idx]
            self.hwnd_objetivo = hwnd
            self.titulo_objetivo = titulo
            self.entry_renombrar.delete(0, tk.END)
            self.entry_renombrar.insert(0, titulo)

    def _renombrar_proceso(self):
        if not self.hwnd_objetivo:
            messagebox.showinfo("Error", "Selecciona un proceso primero")
            return
        nuevo_nombre = self.entry_renombrar.get().strip()
        if not nuevo_nombre:
            messagebox.showinfo("Error", "Ingresa un nombre valido")
            return
        if len(nuevo_nombre) > 50:
            messagebox.showinfo("Error", "Nombre muy largo")
            return
        SetWindowText(self.hwnd_objetivo, nuevo_nombre)
        self.titulo_objetivo = nuevo_nombre
        self._refrescar_procesos()

    # ─── Iniciar / Detener ────────────────────────────────────────

    def _alternar_inicio(self):
        if self.activo:
            self._detener()
        else:
            self._iniciar()

    def _iniciar(self):
        if not self.hwnd_objetivo:
            messagebox.showinfo("Error", "Selecciona un proceso de la lista")
            return

        # Verificar que la ventana aun existe
        try:
            hwnd = FindWindow(None, self.titulo_objetivo)
            if hwnd:
                self.hwnd_objetivo = hwnd
        except Exception:
            pass

        self.activo = True
        self.btn_iniciar.config(text="DETENER")
        self.label_estado.config(text="Ejecutando", foreground="green")

        # Traer juego al frente
        try:
            SetForegroundWindow(self.hwnd_objetivo)
        except Exception:
            pass

        self._iniciar_ataque_basico()
        self._iniciar_recoger()
        self._iniciar_timers_skills()

        if self.autopot_activado.get():
            self._iniciar_autopot()

        self._iniciar_filtro_ocr()

    def _detener(self):
        self.activo = False
        self.btn_iniciar.config(text="INICIAR")
        self.label_estado.config(text="Detenido", foreground="red")

        for timer_id in self.skill_timers.values():
            self.after_cancel(timer_id)
        self.skill_timers.clear()

        if self.autopot_timer_id:
            self.after_cancel(self.autopot_timer_id)
            self.autopot_timer_id = None
        if self.basic_e_timer_id:
            self.after_cancel(self.basic_e_timer_id)
            self.basic_e_timer_id = None
        if self.basic_r_timer_id:
            self.after_cancel(self.basic_r_timer_id)
            self.basic_r_timer_id = None
        if self.pick_timer_id:
            self.after_cancel(self.pick_timer_id)
            self.pick_timer_id = None
        if self.huyendo:
            self._detener_huida()
        if hasattr(self, '_filtro_timer_id') and self._filtro_timer_id:
            self.after_cancel(self._filtro_timer_id)
            self._filtro_timer_id = None
        self.label_deteccion.config(text="Deteccion inactiva", foreground="gray")

    # ─── Filtro de Monstruos + Ataque ────────────────────────────

    def _iniciar_filtro_ocr(self):
        """Inicia el hilo que lee el nombre del target periodicamente."""
        if self.filtro_activado.get():
            self._target_cache_result = True
            self._ocr_en_curso = False
            self._tick_filtro_ocr()

    def _tick_filtro_ocr(self):
        """Lee el nombre del target en un hilo separado cada 800ms."""
        if not self.activo or not self.filtro_activado.get():
            return
        if self._ocr_en_curso:
            self._filtro_timer_id = self.after(400, self._tick_filtro_ocr)
            return

        self._ocr_en_curso = True
        hwnd = self.hwnd_objetivo

        def _leer():
            nombre = leer_nombre_target(hwnd)
            self.after(0, lambda: self._procesar_filtro_resultado(nombre))

        threading.Thread(target=_leer, daemon=True).start()
        self._filtro_timer_id = self.after(800, self._tick_filtro_ocr)

    def _procesar_filtro_resultado(self, nombre):
        """Procesa el resultado del OCR del filtro (en hilo principal)."""
        self._ocr_en_curso = False

        if nombre:
            self.label_target_actual.config(text=f"Target actual: {nombre}")
        else:
            self.label_target_actual.config(text="Target actual: (ninguno)")

        if not nombre:
            # Sin target - intentar seleccionar uno con E
            self.intentos_fallidos += 1
            self.label_filtro_estado.config(
                text=f"Sin target ({self.intentos_fallidos}/{self.MAX_INTENTOS})",
                foreground="gray")
            self._verificar_mover()
            self._target_cache_result = False
        elif self._nombre_coincide(nombre):
            # Target correcto - atacar
            self.intentos_fallidos = 0
            self.label_filtro_estado.config(
                text=f"ATACANDO: {nombre}", foreground="green")
            self._target_cache_result = True
        else:
            # Target incorrecto - deseleccionar con T y buscar otro
            self.intentos_fallidos += 1
            self.label_filtro_estado.config(
                text=f"IGNORADO: {nombre} -> deseleccionando ({self.intentos_fallidos}/{self.MAX_INTENTOS})",
                foreground="orange")
            enviar_tecla(self.hwnd_objetivo, VK_CODES['T'])  # deseleccionar
            self._verificar_mover()
            self._target_cache_result = False

    def _target_permitido(self):
        """Consulta el resultado cacheado del filtro. No hace OCR."""
        if not self.filtro_activado.get():
            return True
        return getattr(self, '_target_cache_result', True)

    def _verificar_mover(self):
        """Si se alcanzaron los intentos maximos, resetea el contador y sigue buscando."""
        if self.intentos_fallidos >= self.MAX_INTENTOS:
            self.intentos_fallidos = 0
            self.label_filtro_estado.config(
                text="No encontrado, sigue buscando...", foreground="blue")

    # ─── Timers de Ataque Basico ──────────────────────────────────

    def _iniciar_ataque_basico(self):
        if not self.basico_activado.get():
            return
        self._tick_e()
        if not self.modo_mago.get():
            self._tick_r()

    def _tick_e(self):
        if not self.activo or not self.basico_activado.get():
            return
        try:
            intervalo = max(1, int(self.intervalo_e.get())) * 1000
        except (ValueError, tk.TclError):
            intervalo = 1000

        # No atacar si esta huyendo
        if not self.huyendo:
            enviar_tecla(self.hwnd_objetivo, VK_CODES['E'])
        self.basic_e_timer_id = self.after(intervalo, self._tick_e)

    def _tick_r(self):
        if not self.activo or not self.basico_activado.get() or self.modo_mago.get():
            return
        try:
            intervalo = max(1, int(self.intervalo_r.get())) * 1000
        except (ValueError, tk.TclError):
            intervalo = 1000

        # No atacar si esta huyendo
        if not self.huyendo and self._target_permitido():
            enviar_tecla(self.hwnd_objetivo, VK_CODES['R'])

        self.basic_r_timer_id = self.after(intervalo, self._tick_r)

    # ─── Timer de Recoger Items ───────────────────────────────────

    def _iniciar_recoger(self):
        if not self.recoger_activado.get():
            return
        self._tick_recoger()

    def _tick_recoger(self):
        if not self.activo or not self.recoger_activado.get():
            return
        try:
            intervalo = max(1, int(self.intervalo_recoger.get())) * 1000
        except (ValueError, tk.TclError):
            intervalo = 1000
        enviar_tecla(self.hwnd_objetivo, VK_CODES['F'])
        self.pick_timer_id = self.after(intervalo, self._tick_recoger)

    # ─── Timers de Skills ─────────────────────────────────────────

    def _iniciar_timers_skills(self):
        teclas_primarias = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        teclas_secundarias = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10']

        for i, tecla in enumerate(teclas_primarias):
            if self.autopot_activado.get() and tecla in ('9', '0'):
                continue
            if self.checks_primarios[i].get():
                self._programar_skill(tecla, self.intervalos_primarios[i],
                                      self.checks_primarios[i])

        for i, tecla in enumerate(teclas_secundarias):
            if self.checks_secundarios[i].get():
                self._programar_skill(tecla, self.intervalos_secundarios[i],
                                      self.checks_secundarios[i])

    def _programar_skill(self, nombre_tecla, entry_intervalo, check_var):
        def tick():
            if not self.activo or not check_var.get():
                return
            try:
                intervalo = max(1, int(entry_intervalo.get())) * 1000
            except (ValueError, tk.TclError):
                intervalo = 1000

            # No usar skills si esta huyendo (excepto 9 y 0 que son pociones)
            if self.huyendo and nombre_tecla not in ('9', '0'):
                self.skill_timers[nombre_tecla] = self.after(intervalo, tick)
                return

            # Skills 1-8 solo se envian si el target es permitido
            if nombre_tecla in ('1','2','3','4','5','6','7','8'):
                if not self._target_permitido():
                    self.skill_timers[nombre_tecla] = self.after(intervalo, tick)
                    return

            enviar_tecla(self.hwnd_objetivo, VK_CODES[nombre_tecla])
            self.skill_timers[nombre_tecla] = self.after(intervalo, tick)

        try:
            intervalo = max(1, int(entry_intervalo.get())) * 1000
        except (ValueError, tk.TclError):
            intervalo = 1000
        self.skill_timers[nombre_tecla] = self.after(intervalo, tick)

    # ─── AutoPot con Deteccion Automatica ─────────────────────────

    def _al_cambiar_autopot(self):
        activado = self.autopot_activado.get()
        if activado:
            self.checks_primarios[8].set(False)  # slot 9
            self.checks_primarios[9].set(False)  # slot 0
            self.intervalos_primarios[8].config(state="disabled")
            self.intervalos_primarios[9].config(state="disabled")
        else:
            self.intervalos_primarios[8].config(state="normal")
            self.intervalos_primarios[9].config(state="normal")

    def _iniciar_autopot(self):
        self._tick_autopot()

    def _calcular_porcentaje_barra(self, hwnd, bar_y, bar_x_start, bar_x_end, es_hp=True):
        """
        Calcula el porcentaje de llenado de una barra leyendo pixeles.
        Escanea de derecha a izquierda en multiples filas para evitar
        interferencia del texto superpuesto (ej: "330/330").
        """
        try:
            win_x, win_y, _, _ = obtener_rect_ventana(hwnd)
        except Exception:
            return -1

        ancho_barra = bar_x_end - bar_x_start
        verificar_color = es_rojo_hp if es_hp else es_azul_mana

        # Muestrear en 3 filas cercanas para evitar texto
        filas = [bar_y - 1, bar_y, bar_y + 1]
        mejor_ultimo = bar_x_start

        for fila_y in filas:
            for rel_x in range(bar_x_end, bar_x_start - 1, -2):
                abs_x = win_x + rel_x
                abs_y = win_y + fila_y
                color = obtener_color_pixel(abs_x, abs_y)
                if verificar_color(color):
                    if rel_x > mejor_ultimo:
                        mejor_ultimo = rel_x
                    break

        porcentaje = int(((mejor_ultimo - bar_x_start) / ancho_barra) * 100)
        return max(0, min(100, porcentaje))

    def _tick_autopot(self):
        if not self.activo or not self.autopot_activado.get():
            return

        hwnd = self.hwnd_objetivo
        umbral_hp = self.hp_porcentaje.get()
        umbral_mana = self.mana_porcentaje.get()

        # Calcular porcentaje de HP
        hp_pct = self._calcular_porcentaje_barra(
            hwnd, HP_BAR_Y, HP_BAR_X_START, HP_BAR_X_END, es_hp=True)

        # Calcular porcentaje de Mana
        mana_pct = self._calcular_porcentaje_barra(
            hwnd, MANA_BAR_Y, MANA_BAR_X_START, MANA_BAR_X_END, es_hp=False)

        # Actualizar labels
        if hp_pct >= 0:
            color_hp = "green" if hp_pct > umbral_hp else "red"
            self.label_hp_estado.config(text=f"HP: ~{hp_pct}%", foreground=color_hp)

        if mana_pct >= 0:
            color_mana = "green" if mana_pct > umbral_mana else "blue"
            self.label_mana_estado.config(text=f"Mana: ~{mana_pct}%", foreground=color_mana)

        self.label_deteccion.config(text="Detectando...", foreground="green")

        # Enviar pocion si esta bajo el umbral
        if 0 <= hp_pct < umbral_hp:
            enviar_tecla(hwnd, VK_CODES['9'])
            self.label_hp_estado.config(text=f"HP: ~{hp_pct}% >>> POCION!", foreground="red")

        if 0 <= mana_pct < umbral_mana:
            enviar_tecla(hwnd, VK_CODES['0'])
            self.label_mana_estado.config(text=f"Mana: ~{mana_pct}% >>> POCION!", foreground="red")

        # Huida: si HP <= 40% correr, si HP > 60% dejar de correr
        if hp_pct >= 0:
            if hp_pct <= 40 and not self.huyendo:
                self.huyendo = True
                self.label_hp_estado.config(text=f"HP: ~{hp_pct}% HUYENDO!", foreground="red")
                self._iniciar_huida()
            elif hp_pct > 60 and self.huyendo:
                self.huyendo = False
                self._detener_huida()
                self.label_hp_estado.config(text=f"HP: ~{hp_pct}% OK", foreground="green")

        self.autopot_timer_id = self.after(200, self._tick_autopot)

    def _iniciar_huida(self):
        """Cuando HP esta bajo, deja de atacar y spamea pociones."""
        self._tick_huida()

    def _tick_huida(self):
        """Sigue enviando pociones mientras HP esta bajo."""
        if not self.activo or not self.huyendo:
            return
        enviar_tecla(self.hwnd_objetivo, VK_CODES['9'])
        self.huida_timer_id = self.after(500, self._tick_huida)

    def _detener_huida(self):
        """HP recuperado, volver a atacar."""
        if self.huida_timer_id:
            self.after_cancel(self.huida_timer_id)
            self.huida_timer_id = None

    # ─── Modo Mago ────────────────────────────────────────────────

    def _al_cambiar_mago(self):
        if self.modo_mago.get():
            self.intervalo_r.delete(0, tk.END)
            self.intervalo_r.insert(0, "0")
            self.intervalo_r.config(state="disabled")
        else:
            self.intervalo_r.config(state="normal")
            self.intervalo_r.delete(0, tk.END)
            self.intervalo_r.insert(0, "1")

    # ─── Presets ──────────────────────────────────────────────────

    def _obtener_dir_presets(self):
        if getattr(sys, 'frozen', False):
            base = os.path.dirname(sys.executable)
        else:
            base = os.path.dirname(os.path.abspath(__file__))
        d = os.path.join(base, "presets")
        os.makedirs(d, exist_ok=True)
        return d

    def _obtener_config_actual(self):
        teclas_primarias = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        teclas_secundarias = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10']

        config = {
            "basico_activado": self.basico_activado.get(),
            "modo_mago": self.modo_mago.get(),
            "intervalo_e": self.intervalo_e.get(),
            "intervalo_r": self.intervalo_r.get(),
            "recoger_activado": self.recoger_activado.get(),
            "intervalo_recoger": self.intervalo_recoger.get(),
            "autopot_activado": self.autopot_activado.get(),
            "hp_porcentaje": self.hp_porcentaje.get(),
            "mana_porcentaje": self.mana_porcentaje.get(),
            "filtro_activado": self.filtro_activado.get(),
            "monstruos": self._obtener_lista_monstruos(),
            "primarios": {},
            "secundarios": {},
        }

        for i, tecla in enumerate(teclas_primarias):
            config["primarios"][tecla] = {
                "intervalo": self.intervalos_primarios[i].get(),
                "activado": self.checks_primarios[i].get(),
            }

        for i, tecla in enumerate(teclas_secundarias):
            config["secundarios"][tecla] = {
                "intervalo": self.intervalos_secundarios[i].get(),
                "activado": self.checks_secundarios[i].get(),
            }

        return config

    def _aplicar_config(self, config):
        self.basico_activado.set(config.get("basico_activado", True))
        self.modo_mago.set(config.get("modo_mago", False))

        self.intervalo_e.delete(0, tk.END)
        self.intervalo_e.insert(0, config.get("intervalo_e", "1"))

        self.intervalo_r.config(state="normal")
        self.intervalo_r.delete(0, tk.END)
        self.intervalo_r.insert(0, config.get("intervalo_r", "1"))

        self.recoger_activado.set(config.get("recoger_activado", False))
        self.intervalo_recoger.delete(0, tk.END)
        self.intervalo_recoger.insert(0, config.get("intervalo_recoger", "1"))

        self.autopot_activado.set(config.get("autopot_activado", False))
        self.hp_porcentaje.set(config.get("hp_porcentaje", 50))
        self.mana_porcentaje.set(config.get("mana_porcentaje", 50))

        self.filtro_activado.set(config.get("filtro_activado", False))
        self.listbox_monstruos.delete(0, tk.END)
        for nombre in config.get("monstruos", []):
            self.listbox_monstruos.insert(tk.END, nombre)

        teclas_primarias = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
        for i, tecla in enumerate(teclas_primarias):
            data = config.get("primarios", {}).get(tecla, {})
            self.intervalos_primarios[i].config(state="normal")
            self.intervalos_primarios[i].delete(0, tk.END)
            self.intervalos_primarios[i].insert(0, data.get("intervalo", "1"))
            self.checks_primarios[i].set(data.get("activado", False))

        teclas_secundarias = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10']
        for i, tecla in enumerate(teclas_secundarias):
            data = config.get("secundarios", {}).get(tecla, {})
            self.intervalos_secundarios[i].delete(0, tk.END)
            self.intervalos_secundarios[i].insert(0, data.get("intervalo", "1"))
            self.checks_secundarios[i].set(data.get("activado", False))

        self._al_cambiar_mago()
        self._al_cambiar_autopot()

    def _guardar_preset(self):
        nombre = self.entry_preset.get().strip()
        if not nombre:
            messagebox.showinfo("Guardar", "Ingresa un nombre para el preset")
            return

        ruta = os.path.join(self._obtener_dir_presets(), f"{nombre}.json")
        config = self._obtener_config_actual()

        try:
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Guardar", f"Preset '{nombre}' guardado exitosamente")
            self._refrescar_presets()
        except Exception as ex:
            messagebox.showerror("Error al Guardar", f"No se pudo guardar: {ex}")

    def _cargar_preset(self):
        dir_presets = self._obtener_dir_presets()
        ruta = filedialog.askopenfilename(
            initialdir=dir_presets,
            filetypes=[("Archivos JSON", "*.json"), ("Todos", "*.*")]
        )
        if not ruta:
            return
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self._aplicar_config(config)
            nombre = os.path.splitext(os.path.basename(ruta))[0]
            self.entry_preset.delete(0, tk.END)
            self.entry_preset.insert(0, nombre)
            messagebox.showinfo("Cargar", f"Preset '{nombre}' cargado exitosamente")
        except Exception as ex:
            messagebox.showerror("Error al Cargar", f"No se pudo cargar: {ex}")

    def _refrescar_presets(self):
        self.listbox_presets.delete(0, tk.END)
        dir_presets = self._obtener_dir_presets()
        if os.path.exists(dir_presets):
            for f in sorted(os.listdir(dir_presets)):
                if f.endswith('.json'):
                    self.listbox_presets.insert(tk.END, os.path.splitext(f)[0])

    def _al_seleccionar_preset(self, event):
        sel = self.listbox_presets.curselection()
        if sel:
            nombre = self.listbox_presets.get(sel[0])
            self.entry_preset.delete(0, tk.END)
            self.entry_preset.insert(0, nombre)

    # ─── Hotkey Global ────────────────────────────────────────────

    def _escuchar_hotkey(self):
        presionado = False
        while self.hotkey_activo:
            ctrl = GetAsyncKeyState(VK_LCONTROL) & 0x8000
            shift = GetAsyncKeyState(VK_LSHIFT) & 0x8000

            if ctrl and shift:
                if not presionado:
                    presionado = True
                    try:
                        self.after(0, self._alternar_inicio)
                    except Exception:
                        pass
            else:
                presionado = False
            time.sleep(0.1)


# ─── Punto de Entrada ─────────────────────────────────────────────────

def _es_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

if __name__ == "__main__":
    if not _es_admin():
        # Re-lanzar como administrador (necesario para interactuar con el juego)
        if getattr(sys, 'frozen', False):
            exe = sys.executable
        else:
            exe = sys.executable
        params = ' '.join([f'"{a}"' for a in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        sys.exit()
    app = TantraAutomatic()
    app.mainloop()
