#!/usr/bin/env python
# -*- coding: utf-8 -*-
# engine.py (Tkinter, compatible con Python 2.7)
import sys
import os
import io
import time
# Import Tk/Tkinter según versión para evitar tipos unión en Pylance
if sys.version_info[0] >= 3:
    import tkinter as tk
else:
    import Tkinter as tk

# Inserta ruta para importar el analizador existente
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ANALYZER_DIR = os.path.join(BASE_DIR, "Entrega1_Proyecto_Practico")
if ANALYZER_DIR not in sys.path:
    sys.path.append(ANALYZER_DIR)
try:
    import analizador
except ImportError:
    analizador = None

# Definir _reload sin ambigüedades, dependiente de versión
if sys.version_info[0] >= 3:
    from importlib import reload as _reload
else:
    _reload = reload  # builtin en Py2

if analizador is not None:
    _reload(analizador)
    HAS_PARSER = hasattr(analizador, 'Parser')
else:
    HAS_PARSER = False

if sys.version_info[0] >= 3:
    unicode = str

# ---------- Configuración global ----------
WINDOW_SIZE = (640, 480)
WINDOW_TITLE = "Motor Tkinter - Entrega 2"
FPS = 60
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (230, 230, 230)

# ---------- Módulo de Entrada ----------
class InputManager:
    def __init__(self, root):
        self.root = root
        self.keys_down = set()
        self.keys_pressed = set()
        self.keys_released = set()
        root.bind_all('<KeyPress>', self._on_key_down)
        root.bind_all('<KeyRelease>', self._on_key_up)

    def begin_frame(self):
        # Eventos se limpian al final del frame
        pass

    def end_frame(self):
        self.keys_pressed.clear()
        self.keys_released.clear()

    def _on_key_down(self, event):
        key = event.keysym.lower()
        if key not in self.keys_down:
            self.keys_pressed.add(key)
        self.keys_down.add(key)

    def _on_key_up(self, event):
        key = event.keysym.lower()
        if key in self.keys_down:
            self.keys_down.remove(key)
        self.keys_released.add(key)

    def is_down(self, key):
        return key in self.keys_down

    def was_pressed(self, key):
        return key in self.keys_pressed

    def was_released(self, key):
        return key in self.keys_released

# ---------- Renderizador / Funciones gráficas ----------
class Renderer:
    def __init__(self, canvas):
        self.canvas = canvas

    def clear(self, color=BG_COLOR):
        self.canvas.delete('all')
        self.canvas.configure(bg=_rgb(color))

    def draw_block(self, x, y, w=40, h=20, color=(200,80,80)):
        self.canvas.create_rectangle(x, y, x+w, y+h, fill=_rgb(color), outline=_rgb((0,0,0)))

    def draw_text(self, text, x, y, color=TEXT_COLOR):
        self.canvas.create_text(x, y, text=text, anchor='nw', fill=_rgb(color), font=('Arial', 14))

    def draw_text_center(self, text, y, color=TEXT_COLOR):
        self.canvas.create_text(WINDOW_SIZE[0]//2, y, text=text, anchor='n', fill=_rgb(color), font=('Arial', 16))

    def draw_score(self, score, x=8, y=8):
        self.draw_text("Puntuación: {0}".format(score), x, y)

    def draw_grid(self, x0, y0, cols, rows, cell, color=(70,70,70)):
        for c in range(cols+1):
            x = x0 + c*cell
            self.canvas.create_line(x, y0, x, y0 + rows*cell, fill=_rgb(color))
        for r in range(rows+1):
            y = y0 + r*cell
            self.canvas.create_line(x0, y, x0 + cols*cell, y, fill=_rgb(color))

    def draw_playfield(self, x0, y0, cols, rows, cell, bg=(20,20,20), border=(200,200,200)):
        self.canvas.create_rectangle(x0, y0, x0+cols*cell, y0+rows*cell, fill=_rgb(bg), outline=_rgb(border))

def _rgb(rgb_tuple):
    return '#%02x%02x%02x' % rgb_tuple

def color_from_name(name):
    cmap = {
        'cian': (0, 255, 255),
        'amarillo': (255, 255, 0),
        'magenta': (255, 0, 255),
        'naranja': (255, 165, 0),
        'azul': (0, 120, 255),
        'verde': (0, 200, 0),
        'rojo': (220, 40, 40),
        'rojo_especial': (220, 40, 40),
        'celeste': (135, 206, 235),
        'azul_especial': (80, 120, 255),
        'dorado': (220, 180, 30),
        'azul_cielo': (60, 120, 220),
        'blanco': (255, 255, 255),
        'morado': (128, 0, 128),
    }
    return cmap.get(name, (200, 140, 40))

# ---------- CARGA DE ARCHIVOS .brik ----------
class BrikLoader:
    @staticmethod
    def parse_arg(node):
        if node.type in ('Numero',):
            try:
                return float(node.value) if '.' in node.value else int(node.value)
            except:
                return node.value
        if node.type in ('Cadena', 'ID'):
            v = node.value
            if isinstance(v, str) and len(v) >= 2 and v[0] == "'" and v[-1] == "'":
                return v[1:-1]
            return v
        if node.type == 'Lista':
            return [BrikLoader.parse_arg(c) for c in node.children]
        return node.value

    @staticmethod
    def load(path):
        if not analizador:
            return {}
        try:
            with io.open(path, 'r', encoding='utf-8') as f:
                code = f.read()
        except TypeError:
            with open(path, 'r') as f:
                code = f.read()
        if hasattr(analizador, 'parse_code'):
            try:
                ast = analizador.parse_code(code)
            except Exception:
                return {}
        elif hasattr(analizador, 'Parser'):
            try:
                tokens = analizador.lexer(code)
                parser = analizador.Parser(tokens)
                ast = parser.parse()
            except Exception:
                return {}
        else:
            facts = {}
            import re
            patron = re.compile(r"^([a-zA-Z_]\w*)\s*\((.*)\)\s*\.\s*$")
            for line in code.splitlines():
                line = line.strip()
                if not line or line.startswith('%'):
                    continue
                m = patron.match(line)
                if not m:
                    continue
                pred = m.group(1)
                cuerpo = [s.strip() for s in m.group(2).split(',')]
                facts.setdefault(pred, []).append(cuerpo)
            return facts
        facts = {}
        for hecho in ast.children:
            if hecho.type != 'Hecho' or not hecho.children:
                continue
            pred = hecho.children[0].value
            args = [BrikLoader.parse_arg(a) for a in hecho.children[1:]]
            facts.setdefault(pred, []).append(args)
        return facts

def list_brik_files():
    folder = ANALYZER_DIR
    files = []
    try:
        for name in os.listdir(folder):
            if name.lower().endswith('.brik'):
                files.append(os.path.join(folder, name))
    except Exception:
        return []
    return files

def get_rule_values(data, nombre_regla, clave):
    return [r[2] for r in data.get('regla', []) if len(r) >= 3 and r[0] == nombre_regla and r[1] == clave]

def get_rule_value(data, nombre_regla, clave, default=None, cast=float):
    vals = get_rule_values(data, nombre_regla, clave)
    if not vals:
        return default
    v = vals[0]
    try:
        return cast(v)
    except:
        return v

def get_fact_value(data, predicado, clave, default=None):
    for rec in data.get(predicado, []):
        if rec and rec[0] == clave:
            return rec[1]
    return default

def get_numeric_fact(data, predicado, clave, default, cast=float):
    v = get_fact_value(data, predicado, clave, None)
    if v is None:
        return default
    try:
        return cast(v)
    except:
        return default

def get_dimensions(data):
    dims = get_fact_value(data, 'tablero', 'dimensiones', [10, 20])
    if isinstance(dims, list) and len(dims) >= 2:
        return dims[0], dims[1]
    return 10, 20

# ---------- JUEGOS DINÁMICOS ----------
class BaseGame:
    def __init__(self, data):
        self.data = data
        self.score = 0
        self.game_over = False
        self.paused = False
        self.hint_color = (160,160,160)
        self.key_pause = None
        self.key_restart = None

    def update(self, dt, input_manager): pass
    def render(self, renderer): pass
    def build_hint(self):
        # Devolver str no-literal para evitar que Pylance infiera Literal[""]
        hint = "".join([])
        return hint

    def get_key_for_action(self, action):
        for registro in self.data.get('control', []):
            if len(registro) == 2:
                nombre_accion = registro[0]
                # Normalizar nombre de acción por si viene con comillas
                if isinstance(nombre_accion, (str, unicode)) and len(nombre_accion) >= 2:
                    if nombre_accion[0] == '\'' and nombre_accion[-1] == '\'':
                        nombre_accion = nombre_accion[1:-1]
                if nombre_accion == action:
                    tecla = registro[1]
                    # Aceptar tanto str como unicode (Py2)
                    if isinstance(tecla, (str, unicode)) and len(tecla) >= 1:
                        # Quitar comillas simples si quedaron del parser simple
                        if len(tecla) >= 2 and tecla[0] == '\'' and tecla[-1] == '\'':
                            tecla = tecla[1:-1]
                        return tecla.lower()
        return None

class SnakeGame(BaseGame):
    def __init__(self, data):
        BaseGame.__init__(self, data)
        self.grid_w, self.grid_h = get_dimensions(data)
        self.cell = max(12, 20)
        self.speed = get_numeric_fact(data, 'juego', 'velocidad_inicial', 4.0, float)
        self.timer_move = 0.0
        self.time_total = 0.0
        longitud = int(get_fact_value(data, 'serpiente', 'longitud_inicial', 3))
        start_x, start_y = self.grid_w // 2, self.grid_h // 2
        self.snake = [(start_x - i, start_y) for i in range(longitud)]
        self.dir = (1, 0)
        self.next_dir = self.dir
        self.fruit_type = 'normal'
        self.speed_effect_end = 0.0
        self.prob_dorada = get_rule_value(data, 'fruta_dorada', 'probabilidad', 0.2, float)
        self.prob_explosiva = get_rule_value(data, 'fruta_explosiva', 'probabilidad', 0.12, float)
        self.prob_ralentizar = get_rule_value(data, 'powerup_ralentizar', 'probabilidad', 0.1, float)
        self.ralentizar_mult = get_rule_value(data, 'powerup_ralentizar', 'multiplicador', 0.5, float)
        self.ralentizar_dur = get_rule_value(data, 'powerup_ralentizar', 'duracion_efecto', 8, int)
        self.prob_morada = get_rule_value(data, 'fruta_morada', 'probabilidad', 0.15, float)
        self.morada_mult = get_rule_value(data, 'fruta_morada', 'multiplicador', 1.5, float)
        self.morada_dur = get_rule_value(data, 'fruta_morada', 'duracion_efecto', 6, int)
        self.base_fruit_color = color_from_name('blanco')
        self.fruit = self.spawn_fruit()
        self.score_add = next((int(r[2]) for r in data.get('regla', []) if r[0]=='comer_fruta' and r[1]=='puntuacion'), 10)
        self.key_cache = {
            'izq': self.get_key_for_action('mover_izquierda') or 'left',
            'der': self.get_key_for_action('mover_derecha') or 'right',
            'arr': self.get_key_for_action('mover_arriba') or 'up',
            'aba': self.get_key_for_action('mover_abajo') or 'down',
        }
        self.key_pause = self.get_key_for_action('pausar') or 'p'
        self.key_restart = self.get_key_for_action('reiniciar') or 'r'
        self.offset_x = (WINDOW_SIZE[0] - self.grid_w * self.cell) // 2
        self.offset_y = (WINDOW_SIZE[1] - self.grid_h * self.cell) // 2
        self.explosiva_dur = get_rule_value(data, 'fruta_explosiva', 'duracion_segundos', 5, int)
        self.fruit_spawn_time = 0.0
        self.last_speed_mult = 1.0
        self.level = 1
        self.points_per_level = get_rule_value(data, 'niveles_velocidad', 'puntos_por_nivel', 50, int) or 50
        self.speed_mult_level = get_rule_value(data, 'niveles_velocidad', 'multiplicador_velocidad', 1.1, float) or 1.1

    def spawn_fruit(self):
        import random
        while True:
            pos = (random.randint(0, self.grid_w - 1), random.randint(0, self.grid_h - 1))
            if pos not in self.snake:
                break
        r = random.random()
        if r < self.prob_explosiva:
            self.fruit_type = 'explosiva'
        elif r < self.prob_explosiva + self.prob_ralentizar:
            self.fruit_type = 'ralentizar'
        elif r < self.prob_explosiva + self.prob_ralentizar + self.prob_dorada:
            self.fruit_type = 'dorada'
        elif r < self.prob_explosiva + self.prob_ralentizar + self.prob_dorada + self.prob_morada:
            self.fruit_type = 'morada'
        else:
            self.fruit_type = 'normal'
        self.fruit_spawn_time = self.time_total
        return pos

    def update(self, dt, input_manager):
        if self.game_over or self.paused:
            return
        self.time_total += dt
        k = self.key_cache
        if k['izq'] and input_manager.was_pressed(k['izq']):
            if self.dir != (1,0):
                self.next_dir = (-1,0)
        if k['der'] and input_manager.was_pressed(k['der']):
            if self.dir != (-1,0):
                self.next_dir = (1,0)
        if k['arr'] and input_manager.was_pressed(k['arr']):
            if self.dir != (0,1):
                self.next_dir = (0,-1)
        if k['aba'] and input_manager.was_pressed(k['aba']):
            if self.dir != (0,-1):
                self.next_dir = (0,1)
        self.timer_move += dt
        step_time = max(0.05, 0.25 / self.speed)
        if self.timer_move >= step_time:
            self.timer_move = 0.0
            self.dir = self.next_dir
            head = (self.snake[0][0] + self.dir[0], self.snake[0][1] + self.dir[1])
            if (head[0] < 0 or head[0] >= self.grid_w or head[1] < 0 or head[1] >= self.grid_h or head in self.snake):
                self.game_over = True
                return
            self.snake.insert(0, head)
            if head == self.fruit:
                self.score += self.score_add
                if self.score // self.points_per_level + 1 > self.level:
                    self.level = self.score // self.points_per_level + 1
                    self.speed *= self.speed_mult_level
                if self.fruit_type == 'dorada':
                    self.score += self.score_add * 2
                    self.fruit = self.spawn_fruit()
                elif self.fruit_type == 'explosiva':
                    self.game_over = True
                elif self.fruit_type == 'ralentizar':
                    self.speed_effect_end = self.time_total + self.ralentizar_dur
                    self.last_speed_mult = self.ralentizar_mult
                    self.speed *= self.last_speed_mult
                    self.fruit = self.spawn_fruit()
                elif self.fruit_type == 'morada':
                    self.speed_effect_end = self.time_total + self.morada_dur
                    self.last_speed_mult = self.morada_mult
                    self.speed *= self.last_speed_mult
                    self.fruit = self.spawn_fruit()
                else:
                    self.fruit = self.spawn_fruit()
            else:
                self.snake.pop()
        if self.speed_effect_end and self.time_total >= self.speed_effect_end:
            self.speed_effect_end = 0.0
            if self.last_speed_mult != 0:
                self.speed /= self.last_speed_mult
            self.last_speed_mult = 1.0
        if self.fruit_type == 'explosiva' and (self.time_total - self.fruit_spawn_time) >= self.explosiva_dur:
            self.fruit = self.spawn_fruit()
            self.fruit_type = 'normal'

    def build_hint(self):
        return "Mover: W/A/S/D  Pausa: P  Reiniciar: R"

    def render(self, renderer):
        renderer.draw_playfield(self.offset_x, self.offset_y, self.grid_w, self.grid_h, self.cell,
                                bg=(25,25,25), border=(180,180,180))
        renderer.draw_grid(self.offset_x, self.offset_y, self.grid_w, self.grid_h, self.cell, color=(50,50,50))
        for i,(x,y) in enumerate(self.snake):
            color = (0,180,0) if i == 0 else (0,120,0)
            renderer.draw_block(self.offset_x + x*self.cell, self.offset_y + y*self.cell,
                                self.cell, self.cell, color)
        fruit_color = {
            'normal': color_from_name('blanco'),
            'dorada': color_from_name('dorado'),
            'explosiva': color_from_name('rojo'),
            'ralentizar': color_from_name('azul_cielo'),
            'morada': color_from_name('morado'),
        }.get(self.fruit_type, color_from_name('blanco'))
        renderer.draw_block(self.offset_x + self.fruit[0]*self.cell,
                            self.offset_y + self.fruit[1]*self.cell,
                            self.cell, self.cell, fruit_color)
        renderer.draw_score(self.score)
        renderer.draw_text("Nivel: {0}".format(self.level), 8, 32)
        if self.game_over:
            renderer.draw_text_center("GAME OVER - Enter para volver", WINDOW_SIZE[1]//2 - 10)
        if self.paused and not self.game_over:
            renderer.draw_text_center("PAUSA - P/R para continuar/reiniciar", WINDOW_SIZE[1]//2 + 30)

class TetrisGame(BaseGame):
    def __init__(self, data):
        BaseGame.__init__(self, data)
        gw, gh = get_dimensions(data)
        self.grid_w, self.grid_h = gw, gh
        self.cell = max(12, min(WINDOW_SIZE[0] // max(self.grid_w,1), WINDOW_SIZE[1] // max(self.grid_h,1)))
        self.neutral_color = (180,180,180)
        self.speed_base = get_numeric_fact(data, 'juego', 'velocidad_inicial', 1.0, float)
        self.speed = self.speed_base
        self.score_base = next((int(r[2]) for r in data.get('regla', []) if r[0]=='puntuacion_lineas' and r[1]=='puntuacion_base'), 100)
        mults = next((r[2] for r in data.get('regla', []) if r[0]=='puntuacion_lineas' and r[1]=='multiplicadores'), [1,3,5,8])
        self.multiplicadores = mults if isinstance(mults, list) else [1,3,5,8]
        self.key_cache = {
            'izq': (self.get_key_for_action('mover_izquierda') or 'left'),
            'der': (self.get_key_for_action('mover_derecha') or 'right'),
            'down': (self.get_key_for_action('acelerar_abajo') or 'down'),
            'hold': (self.get_key_for_action('evitar_caida') or 'w'),
            'rot': (self.get_key_for_action('rotar') or 'e'),
        }
        self.key_pause = self.get_key_for_action('pausar') or 'p'
        self.key_restart = self.get_key_for_action('reiniciar') or 'r'
        self.shapes = self._load_shapes()
        self.board = [[None]*self.grid_w for _ in range(self.grid_h)]
        self.timer = 0.0
        self.prob_bomba = get_rule_value(data, 'aparicion_piezas', 'probabilidad_bomba', 0.0, float) or 0.0
        self.prob_inversion = get_rule_value(data, 'aparicion_piezas', 'probabilidad_inversion', 0.0, float) or 0.0
        self.prob_congelada = get_rule_value(data, 'aparicion_piezas', 'probabilidad_congelada', 0.0, float) or 0.0
        self.bomba_radio = get_rule_value(data, 'bomba_ladrillo', 'radio_destruccion', 2, int)
        self.inversion_dur = get_rule_value(data, 'inversion_ladrillo', 'duracion_inversion', 5, int)
        self.congelada_mult = get_rule_value(data, 'ficha_congelada', 'multiplicador_velocidad', 1.0, float)
        self.congelada_dur = get_rule_value(data, 'ficha_congelada', 'duracion_efecto', 0, int)
        self.congelada_active_end = 0.0
        self.inversion_active_end = 0.0
        self.time_total = 0.0
        self.current = self.spawn_piece()
        self.offset_x = (WINDOW_SIZE[0] - self.grid_w * self.cell) // 2
        self.offset_y = (WINDOW_SIZE[1] - self.grid_h * self.cell) // 2
        self.level = 1
        self.points_per_level = get_rule_value(data, 'niveles_velocidad', 'puntos_por_nivel', 1000, int) or 1000
        self.speed_mult_level = get_rule_value(data, 'niveles_velocidad', 'multiplicador_velocidad', 1.2, float) or 1.2

    def _load_shapes(self):
        shapes = []
        nc = self.neutral_color
        for pieza in self.data.get('pieza', []):
            if len(pieza) == 2:
                nombre = pieza[0]
                rotaciones = pieza[1]
                color_rgb = nc
            elif len(pieza) >= 3:
                nombre = pieza[0]
                color_rgb = color_from_name(pieza[1])
                rotaciones = pieza[2]
            else:
                continue
            parsed = [rot for rot in rotaciones]
            shapes.append((nombre, color_rgb, parsed))
        return shapes or [('dummy', nc, [[[1]]])]

    def _spawn_center_x(self, rots):
        shape = rots[0] if rots else [[1]]
        width = max(len(shape[0]), 1)
        return max(0, (self.grid_w - width) // 2)

    def spawn_piece(self):
        import random
        r = random.random()
        limite_bomba = self.prob_bomba
        limite_inversion = limite_bomba + self.prob_inversion
        limite_congelada = limite_inversion + self.prob_congelada
        if r < limite_bomba:
            target = 'bomba'
        elif r < limite_inversion:
            target = 'inversion'
        elif r < limite_congelada:
            target = 'congelada'
        else:
            normales = [p for p in self.shapes if p[0] not in ('bomba', 'inversion', 'congelada')]
            if not normales:
                normales = self.shapes
            nombre, color, rots = random.choice(normales)
            return {'name': nombre, 'color': color, 'rots': rots, 'rot': 0,
                    'x': self._spawn_center_x(rots), 'y': 0}
        for n, color, rots in self.shapes:
            if n == target:
                return {'name': n, 'color': color, 'rots': rots, 'rot': 0,
                        'x': self._spawn_center_x(rots), 'y': 0}
        return {'name': 'dummy', 'color': self.neutral_color, 'rots': [[[1]]],
                'rot': 0, 'x': self._spawn_center_x([[[1]]]), 'y': 0}

    def collides(self, px, py, rot):
        shape = self.current['rots'][rot]
        for j,row in enumerate(shape):
            for i,val in enumerate(row):
                if val:
                    x = px + i
                    y = py + j
                    if x < 0 or x >= self.grid_w or y < 0 or y >= self.grid_h:
                        return True
                    if self.board[y][x] is not None:
                        return True
        return False

    def _apply_bomb(self, cx, cy):
        for dy in range(-self.bomba_radio, self.bomba_radio+1):
            for dx in range(-self.bomba_radio, self.bomba_radio+1):
                x = cx + dx
                y = cy + dy
                if 0 <= x < self.grid_w and 0 <= y < self.grid_h:
                    self.board[y][x] = None
        self._settle_gravity()

    def lock_piece(self):
        shape = self.current['rots'][self.current['rot']]
        col = self.current['color']
        hit_cells = []
        for j,row in enumerate(shape):
            for i,val in enumerate(row):
                if val:
                    x = self.current['x'] + i
                    y = self.current['y'] + j
                    if 0 <= y < self.grid_h and 0 <= x < self.grid_w:
                        self.board[y][x] = (1, col)
                        hit_cells.append((x,y))
        if self.current['name'] == 'bomba' and hit_cells:
            cx, cy = hit_cells[0]
            self._apply_bomb(cx, cy)
        if self.current['name'] == 'inversion':
            self.inversion_active_end = self.time_total + self.inversion_dur
        if self.current['name'] == 'congelada':
            self.congelada_active_end = self.time_total + self.congelada_dur
        cleared = self.clear_lines()
        if self.score // self.points_per_level + 1 > self.level:
            self.level = self.score // self.points_per_level + 1
            self.speed *= self.speed_mult_level
        if cleared > 0:
            self._settle_gravity()
        fin_cond = next((r[2] for r in self.data.get('regla', [])
                         if r[0]=='fin_juego' and r[1]=='condicion'), None)
        if fin_cond == 'pieza_alcanza_tope':
            if any(cell is not None for cell in self.board[0]):
                self.game_over = True
        if not self.game_over:
            self.current = self.spawn_piece()
            if self.collides(self.current['x'], self.current['y'], self.current['rot']):
                self.game_over = True

    def clear_lines(self):
        new_board = [row for row in self.board if not all(row)]
        cleared = self.grid_h - len(new_board)
        if cleared > 0:
            idx = min(cleared-1, len(self.multiplicadores)-1)
            mult = self.multiplicadores[idx]
            self.score += self.score_base * mult
            for _ in range(cleared):
                new_board.insert(0, [None]*self.grid_w)
            self.board = new_board
        return cleared

    def _settle_gravity(self):
        moved = True
        while moved:
            moved = False
            for y in range(self.grid_h-2, -1, -1):
                for x in range(self.grid_w):
                    if self.board[y][x] is not None and self.board[y+1][x] is None:
                        self.board[y+1][x] = self.board[y][x]
                        self.board[y][x] = None
                        moved = True

    def build_hint(self):
        return "Mover: A/D  Caer rápido: S  Mantener: W  Rotar: E  Pausa: P  Reiniciar: R"

    def update(self, dt, input_manager):
        if self.game_over or self.paused:
            return
        k = self.key_cache
        inverted = self.inversion_active_end and self.time_total < self.inversion_active_end
        congelada_activa = self.congelada_active_end and self.time_total < self.congelada_active_end
        current_speed = self.speed_base * (self.congelada_mult if congelada_activa else 1.0)
        if k['izq'] and input_manager.was_pressed(k['izq']):
            delta = 1 if inverted else -1
            if not self.collides(self.current['x'] + delta, self.current['y'], self.current['rot']):
                self.current['x'] += delta
        if k['der'] and input_manager.was_pressed(k['der']):
            delta = -1 if inverted else 1
            if not self.collides(self.current['x'] + delta, self.current['y'], self.current['rot']):
                self.current['x'] += delta
        if k['rot'] and input_manager.was_pressed(k['rot']):
            nr = (self.current['rot'] + 1) % len(self.current['rots'])
            if not self.collides(self.current['x'], self.current['y'], nr):
                self.current['rot'] = nr
        hold_down = self.key_cache['hold'] and input_manager.is_down(self.key_cache['hold'])
        fall_speed = max(0.05, 0.7 / max(0.001, current_speed))
        if k['down'] and input_manager.is_down(k['down']):
            fall_speed *= 0.25
        self.timer += dt
        if not hold_down and self.timer >= fall_speed:
            self.timer = 0.0
            if not self.collides(self.current['x'], self.current['y'] + 1, self.current['rot']):
                self.current['y'] += 1
            else:
                self.lock_piece()
        self.time_total += dt

    def render(self, renderer):
        renderer.draw_playfield(self.offset_x, self.offset_y, self.grid_w, self.grid_h, self.cell,
                                bg=(25,25,25), border=(180,180,180))
        renderer.draw_grid(self.offset_x, self.offset_y, self.grid_w, self.grid_h, self.cell, color=(60,60,60))
        for y,row in enumerate(self.board):
            for x,val in enumerate(row):
                if val is not None:
                    col = val[1] if isinstance(val, tuple) and len(val) == 2 else self.neutral_color
                    renderer.draw_block(self.offset_x + x*self.cell,
                                        self.offset_y + y*self.cell,
                                        self.cell, self.cell, col)
        shape = self.current['rots'][self.current['rot']]
        col = self.current.get('color') or self.neutral_color
        for j,r in enumerate(shape):
            for i,val in enumerate(r):
                if val:
                    renderer.draw_block(self.offset_x + (self.current['x']+i)*self.cell,
                                        self.offset_y + (self.current['y']+j)*self.cell,
                                        self.cell, self.cell, col)
        renderer.draw_score(self.score)
        renderer.draw_text("Nivel: {0}".format(self.level), 8, 32)
        if self.game_over:
            renderer.draw_text_center("GAME OVER - Enter para volver", WINDOW_SIZE[1]//2)
        if self.paused and not self.game_over:
            renderer.draw_text_center("PAUSA - P/R para continuar/reiniciar", WINDOW_SIZE[1]//2 + 30)

class GameFactory:
    @staticmethod
    def create(data):
        if 'elementos_disponibles' in data:
            return SnakeGame(data)
        if 'figuras_disponibles' in data or 'pieza' in data:
            return TetrisGame(data)
        return SnakeGame(data)

class GameEngine:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        # Usar un Frame como contenedor para evitar discrepancias de tipos en Pylance
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill='both', expand=True)
        self.canvas = tk.Canvas(self.frame, width=WINDOW_SIZE[0], height=WINDOW_SIZE[1], bg=_rgb(BG_COLOR))
        self.canvas.pack()
        self.renderer = Renderer(self.canvas)
        self.input = InputManager(self.root)
        self.is_running = False
        self.mode = 'menu'
        try:
            self.games_meta = self.load_game_list()
        except Exception:
            self.games_meta = []
        self.menu_index = 0
        self.current_game = None
        self._last_time = time.time()

    def load_game_list(self):
        files = list_brik_files()
        listado = []
        for f in files:
            try:
                data = BrikLoader.load(f)
            except Exception:
                continue
            nombre = None
            for j in data.get('juego', []):
                if j[0] == 'nombre':
                    nombre = j[1]
            if not nombre:
                nombre = os.path.basename(f)
            # Quitar comillas simples si vienen del .brik
            if isinstance(nombre, (str, unicode)) and len(nombre) >= 2:
                if nombre[0] == '\'' and nombre[-1] == '\'':
                    nombre = nombre[1:-1]
            listado.append({'path': f, 'name': nombre, 'data': data})
        return listado

    def start(self):
        self.is_running = True
        self.root.after(int(1000.0/FPS), self._tick)
        self.root.mainloop()

    def _tick(self):
        if not self.is_running:
            return
        now = time.time()
        dt = max(0.0, now - self._last_time)
        self._last_time = now
        if self.mode == 'menu':
            if self.input.was_pressed('down') or self.input.was_pressed('s'):
                if self.games_meta:
                    self.menu_index = (self.menu_index + 1) % len(self.games_meta)
            if self.input.was_pressed('up') or self.input.was_pressed('w'):
                if self.games_meta:
                    self.menu_index = (self.menu_index - 1) % len(self.games_meta)
            if self.input.was_pressed('return') or self.input.was_pressed('space'):
                self.start_game()
        elif self.mode == 'juego':
            cg = self.current_game
            if cg:
                if cg.key_pause and self.input.was_pressed(cg.key_pause):
                    if not cg.game_over:
                        cg.paused = not cg.paused
                if cg.key_restart and self.input.was_pressed(cg.key_restart):
                    self.restart_current_game()
                if self.input.was_pressed('escape'):
                    self.mode = 'menu'
                    self.current_game = None
                if cg and cg.game_over and self.input.was_pressed('return'):
                    self.mode = 'menu'
                    self.current_game = None
                if self.current_game and not self.current_game.paused:
                    self.current_game.update(dt, self.input)
        self.renderer.clear()
        if self.mode == 'menu':
            self.render_menu()
        elif self.mode == 'juego' and self.current_game:
            self.current_game.render(self.renderer)
        # Limpiar eventos discretos al final del frame
        self.input.end_frame()
        self.root.after(int(1000.0/FPS), self._tick)

    def render_menu(self):
        self.renderer.draw_text_center("SELECCIONA UN JUEGO", 50)
        for i, game in enumerate(self.games_meta):
            nombre = game['name']
            y = 100 + i * 30
            color = TEXT_COLOR if i == self.menu_index else (150, 150, 150)
            self.renderer.draw_text(nombre, 50, y, color)
        self.renderer.draw_text("Usa flechas o W/S y Enter", 50, 350, (200, 200, 200))

    def start_game(self):
        if not self.games_meta:
            return
        game_data = self.games_meta[self.menu_index]
        data = game_data['data']
        self.current_game = GameFactory.create(data)
        if self.current_game:
            self.mode = 'juego'
        else:
            self.mode = 'menu'

    def restart_current_game(self):
        if not self.current_game:
            return
        data_ref = self.current_game.data
        self.current_game = GameFactory.create(data_ref)

# ---------- Entrada punto de ejecución ----------
if __name__ == "__main__":
    engine = GameEngine()
    engine.start()
