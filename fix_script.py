import re

with open('tantra_automatic.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Imports
if 'import math' not in code:
    code = code.replace('import time', 'import time\nimport math\nimport re')

# 2. Add MAP constants and SendInput structures if not exist
if 'MAP_X1_PCT' not in code:
    consts = """
MAP_X1_PCT, MAP_X2_PCT, MAP_Y1, MAP_Y2 = 0.75, 1.0, 0, 300

class MOUSEINPUT(ctypes.Structure):
    _fields_ = (('dx', ctypes.c_long), ('dy', ctypes.c_long), ('mouseData', ctypes.c_ulong), ('dwFlags', ctypes.c_ulong), ('time', ctypes.c_ulong), ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)))

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = (('mi', MOUSEINPUT), ('ki', ctypes.c_int * 6), ('hi', ctypes.c_int * 4))
    _anonymous_ = ('_input',)
    _fields_ = (('type', ctypes.c_ulong), ('_input', _INPUT))

def send_mouse_event(flags, dx=0, dy=0):
    extra = ctypes.c_ulong(0)
    ii_ = INPUT._INPUT()
    ii_.mi = MOUSEINPUT(dx, dy, 0, flags, 0, ctypes.pointer(extra))
    x = INPUT(0, ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(x), ctypes.sizeof(x))

MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP, MOUSEEVENTF_MOVE = 0x0008, 0x0010, 0x0001
"""
    code = code.replace("TARGET_Y2 = 60          # fila fin (aumentado para capturar nombre + sangre)", "TARGET_Y2 = 60" + consts)

# 3. Add leer_coordenadas_mapa
if 'def leer_coordenadas_mapa' not in code:
    map_func = """
def leer_coordenadas_mapa(hwnd):
    if not OCR_DISPONIBLE: return None, None
    try:
        cx, cy, cr, cb = obtener_rect_cliente(hwnd)
        cw = cr - cx
        if cw < 100: return None, None
        x1, y1 = cx + int(cw * MAP_X1_PCT), cy + MAP_Y1
        x2, y2 = cx + int(cw * MAP_X2_PCT), cy + MAP_Y2
        from PIL import ImageGrab
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2), all_screens=True)
        big = img.resize((img.width * 3, img.height * 3))
        binary = big.convert('L').point(lambda p: 255 if p > 180 else 0)
        import pytesseract
        texto = pytesseract.image_to_string(binary, config='--psm 11').strip()
        m = re.search(r'(\d+)\s*/\s*(\d+)', texto)
        if m: return int(m.group(1)), int(m.group(2))
        return None, None
    except: return None, None

"""
    code = code.replace("# ─── Aplicacion Principal", map_func + "# ─── Aplicacion Principal")

# 4. Constructor variables
if 'self.geo_activada' not in code:
    geo_vars = """
        self._lista_ventanas = []
        self.geo_activada = tk.BooleanVar(value=False)
        self.geo_x_ini = tk.StringVar(value="0")
        self.geo_y_ini = tk.StringVar(value="0")
        self.geo_radio = tk.StringVar(value="50")
        self.geo_coord_actual = tk.StringVar(value="-- / --")
        self.fuera_de_rango = False
        self.distancia_anterior = 999999
        self.geo_lim_n = tk.StringVar(value="--")
        self.geo_lim_s = tk.StringVar(value="--")
        self.geo_lim_e = tk.StringVar(value="--")
        self.geo_lim_o = tk.StringVar(value="--")
        self.geo_x_ini.trace_add("write", lambda *a: self._actualizar_limites_geo())
        self.geo_y_ini.trace_add("write", lambda *a: self._actualizar_limites_geo())
        self.geo_radio.trace_add("write", lambda *a: self._actualizar_limites_geo())
"""
    code = code.replace("self.skill_timers = {}", "self.skill_timers = {}" + geo_vars)

# 5. Geofence Tab and Update Limites
if 'def _construir_tab_geocerca' not in code:
    geo_tab = """
    def _construir_tab_geocerca(self):
        tab = ttk.Frame(self.notebook, padding=8)
        self.notebook.add(tab, text="Geocerca")
        ttk.Checkbutton(tab, text="Activar Geocerca", variable=self.geo_activada).pack(anchor="w", pady=5)
        f_in = ttk.Frame(tab); f_in.pack(fill="x", pady=5)
        ttk.Label(f_in, text="X:").pack(side="left"); ttk.Entry(f_in, textvariable=self.geo_x_ini, width=6).pack(side="left")
        ttk.Label(f_in, text="Y:").pack(side="left", padx=5); ttk.Entry(f_in, textvariable=self.geo_y_ini, width=6).pack(side="left")
        ttk.Label(f_in, text="Radio:").pack(side="left", padx=5); ttk.Entry(f_in, textvariable=self.geo_radio, width=6).pack(side="left")
        
        f_lims = ttk.LabelFrame(tab, text="Limites", padding=5); f_lims.pack(fill="x", pady=5)
        ttk.Label(f_lims, text="N:").pack(side="left"); ttk.Label(f_lims, textvariable=self.geo_lim_n).pack(side="left", padx=2)
        ttk.Label(f_lims, text="S:").pack(side="left", padx=(5,0)); ttk.Label(f_lims, textvariable=self.geo_lim_s).pack(side="left", padx=2)
        ttk.Label(f_lims, text="E:").pack(side="left", padx=(5,0)); ttk.Label(f_lims, textvariable=self.geo_lim_e).pack(side="left", padx=2)
        ttk.Label(f_lims, text="O:").pack(side="left", padx=(5,0)); ttk.Label(f_lims, textvariable=self.geo_lim_o).pack(side="left", padx=2)
        
        self.lbl_coord_act = ttk.Label(tab, textvariable=self.geo_coord_actual, font=("Consolas", 12, "bold")); self.lbl_coord_act.pack(pady=5)
        self.lbl_geo_est = ttk.Label(tab, text="DENTRO", foreground="green", font=("Segoe UI", 10, "bold")); self.lbl_geo_est.pack()
        ttk.Label(tab, text="Nota: El mapa debe estar en modo MINIMAPA.", foreground="red").pack()

    def _actualizar_limites_geo(self):
        try:
            x, y, r = int(self.geo_x_ini.get()), int(self.geo_y_ini.get()), int(self.geo_radio.get())
            self.geo_lim_n.set(str(y+r)); self.geo_lim_s.set(str(y-r)); self.geo_lim_e.set(str(x+r)); self.geo_lim_o.set(str(x-r))
        except: pass
"""
    code = code.replace("def _construir_tab_autopot", geo_tab + "\n    def _construir_tab_autopot")
    code = code.replace("self._construir_tab_filtro()", "self._construir_tab_filtro()\n        self._construir_tab_geocerca()")

# 6. Build the navigation inside _tick_filtro_ocr
if 'cur_x' not in code:
    new_ocr = """
    def _iniciar_filtro_ocr(self):
        self._ocr_en_curso = False
        self._tick_filtro_ocr()

    def _tick_filtro_ocr(self):
        if not self.activo: return
        if getattr(self, '_ocr_en_curso', False):
            self.after(200, self._tick_filtro_ocr)
            return
        self._ocr_en_curso = True
        def _task():
            n, h = leer_nombre_target(self.hwnd_objetivo) if self.filtro_activado.get() else (None, None)
            cx, cy = leer_coordenadas_mapa(self.hwnd_objetivo) if self.geo_activada.get() else (None, None)
            self.after(0, lambda: self._procesar_ocr(n, h, cx, cy))
        threading.Thread(target=_task, daemon=True).start()
        self.after(400, self._tick_filtro_ocr)

    def _procesar_ocr(self, n, h, cx, cy):
        self._ocr_en_curso = False
        if self.geo_activada.get() and cx is not None:
            self.geo_coord_actual.set(f"{cx} / {cy}")
            try:
                ix, iy, r = int(self.geo_x_ini.get()), int(self.geo_y_ini.get()), int(self.geo_radio.get())
                dist = math.sqrt((cx-ix)**2 + (cy-iy)**2)
                if dist > r:
                    if not self.fuera_de_rango:
                        self.fuera_de_rango = True
                        self.distancia_anterior = dist
                    self.lbl_geo_est.config(text="FUERA DE RANGO", foreground="red")
                    if dist >= self.distancia_anterior:
                        ctypes.windll.user32.SetForegroundWindow(self.hwnd_objetivo)
                        time.sleep(0.1)
                        send_mouse_event(MOUSEEVENTF_RIGHTDOWN)
                        for _ in range(25):
                            send_mouse_event(MOUSEEVENTF_MOVE, 18, 0)
                            time.sleep(0.01)
                        send_mouse_event(MOUSEEVENTF_RIGHTUP)
                    self.distancia_anterior = dist
                    self._caminar(2)
                else:
                    if self.fuera_de_rango:
                        self._caminar(3)
                    self.fuera_de_rango = False
                    self.lbl_geo_est.config(text="DENTRO", foreground="green")
            except: pass
        if self.filtro_activado.get() and not self.fuera_de_rango:
            info = f"{n if n else '?'}" + (f" (HP: {h})" if h else "")
            self.label_target_actual.config(text=f"Target: {info}")
            if not n and not h:
                self.intentos_fallidos += 1
                self._verificar_mover()
                self._target_cache_result = False
            elif self._match(n, h):
                self.intentos_fallidos = 0
                self.label_filtro_estado.config(text="ATACANDO", foreground="green")
                self._target_cache_result = True
            else:
                self.intentos_fallidos += 1
                self.label_filtro_estado.config(text="IGNORADO", foreground="orange")
                self._verificar_mover()
                self._target_cache_result = False

    def _match(self, n, h):
        filtros = self._get_filters()
        if not filtros: return True
        for f in filtros:
            if (f['n'] is None or (n and n.lower() == f['n'])) and (f['h'] is None or h == f['h']): return True
        return False

    def _caminar(self, clicks):
        try:
            rect = ctypes.wintypes.RECT()
            user32.GetClientRect(self.hwnd_objetivo, ctypes.byref(rect))
            lp = (int(rect.bottom*0.45) << 16) | (rect.right//2 & 0xFFFF)
            for _ in range(clicks):
                user32.PostMessageW(self.hwnd_objetivo, 0x0201, 1, lp)
                time.sleep(0.05)
                user32.PostMessageW(self.hwnd_objetivo, 0x0202, 0, lp)
                time.sleep(0.1)
        except: pass
"""
    # Replace existing _tick_filtro_ocr with the new one
    import re
    code = re.sub(r'def _iniciar_filtro_ocr\(self\):.*?def _target_permitido\(self\):', new_ocr + '\n    def _target_permitido(self):', code, flags=re.DOTALL)

# 7. Modify _verificar_mover to use clicks instead of keys and respect range
if 'self._caminar(2)' not in code and 'self.intentos_fallidos = 0' in code:
    code = code.replace("""    def _verificar_mover(self):
        \"\"\"Si se alcanzaron los intentos maximos, resetea el contador y sigue buscando.\"\"\"
        if self.intentos_fallidos >= self.MAX_INTENTOS:
            self.intentos_fallidos = 0
            self.label_filtro_estado.config(
                text="No encontrado, sigue buscando...", foreground="blue")""", """    def _verificar_mover(self):
        if self.intentos_fallidos >= self.MAX_INTENTOS and not self.fuera_de_rango:
            self.intentos_fallidos = 0
            self.label_filtro_estado.config(text="Atascado. Caminando al frente...", foreground="blue")
            self._caminar(2)""")

with open('tantra_automatic.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Fix script applied successfully.")
