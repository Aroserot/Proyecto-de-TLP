# engine.py
import pygame
import sys
from typing import Tuple

# ---------- Configuración global ----------
WINDOW_SIZE = (640, 480)
WINDOW_TITLE = "Motor Gráfico y de Juego - Entrega 2"
FPS = 60
BG_COLOR = (30, 30, 30)
TEXT_COLOR = (230, 230, 230)

# ---------- Módulo de Entrada ----------
class InputManager:
    """Gestiona el estado del teclado (polling simple)."""
    def __init__(self):
        self.keys_down = set()
        self.keys_pressed = set()
        self.keys_released = set()

    def begin_frame(self):
        self.keys_pressed.clear()
        self.keys_released.clear()

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            key = event.key
            if key not in self.keys_down:
                self.keys_pressed.add(key)
            self.keys_down.add(key)
        elif event.type == pygame.KEYUP:
            key = event.key
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
    """Funciones para dibujar bloques, texto, puntuación, etc."""
    def __init__(self, surface):
        self.surface = surface
        self.font = pygame.font.SysFont("Arial", 20)

    def clear(self, color=BG_COLOR):
        self.surface.fill(color)

    def draw_block(self, x: int, y: int, w: int = 40, h: int = 20, color: Tuple[int,int,int]=(200,80,80)):
        """Dibuja un bloque (ladrillo) en coordenadas (x,y)."""
        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(self.surface, color, rect)
        pygame.draw.rect(self.surface, (0,0,0), rect, 2)  # borde

    def draw_text(self, text: str, x: int, y: int, color: Tuple[int,int,int]=TEXT_COLOR):
        surf = self.font.render(text, True, color)
        self.surface.blit(surf, (x, y))

    def draw_score(self, score: int, x: int = 8, y: int = 8):
        self.draw_text(f"Puntuación: {score}", x, y)

# ---------- Objetos de juego ----------
class Brick:
    """Representa un ladrillo controlable."""
    def __init__(self, x: int, y: int, w: int=60, h: int=24, color=(80,160,220)):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.speed = 200  # px/seg

    def update(self, dt: float, input_manager: InputManager):
        # Movimiento horizontal con flechas o A/D
        dx = 0
        if input_manager.is_down(pygame.K_LEFT) or input_manager.is_down(pygame.K_a):
            dx -= 1
        if input_manager.is_down(pygame.K_RIGHT) or input_manager.is_down(pygame.K_d):
            dx += 1

        self.x += dx * self.speed * dt

        # Limitar dentro de la ventana
        self.x = max(0, min(self.x, WINDOW_SIZE[0] - self.w))
        # Movimiento vertical opcional con W/S
        dy = 0
        if input_manager.is_down(pygame.K_UP) or input_manager.is_down(pygame.K_w):
            dy -= 1
        if input_manager.is_down(pygame.K_DOWN) or input_manager.is_down(pygame.K_s):
            dy += 1
        self.y += dy * self.speed * dt
        self.y = max(0, min(self.y, WINDOW_SIZE[1] - self.h))

    def draw(self, renderer: Renderer):
        renderer.draw_block(int(self.x), int(self.y), self.w, self.h, self.color)

# ---------- Motor principal ----------
class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)
        self.screen = pygame.display.set_mode(WINDOW_SIZE)
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)
        self.input = InputManager()
        self.is_running = False

        # Estado del juego
        self.score = 0
        # Crea un ladrillo inicial en el centro
        start_x = (WINDOW_SIZE[0] - 60) // 2
        start_y = (WINDOW_SIZE[1] - 24) // 2
        self.player_brick = Brick(start_x, start_y)

    def handle_events(self):
        self.input.begin_frame()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
            else:
                self.input.process_event(event)

            # Ejemplo: incrementar puntuación al pulsar espacio
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.score += 1

    def update(self, dt: float):
        # Actualiza lógica del juego
        self.player_brick.update(dt, self.input)

    def render(self):
        self.renderer.clear()
        # Dibujar objetos
        self.player_brick.draw(self.renderer)
        # Dibujar puntuación y texto
        self.renderer.draw_score(self.score)
        self.renderer.draw_text("Usa flechas o A/D para mover. Espacio: +puntos", 8, WINDOW_SIZE[1] - 28)
        pygame.display.flip()

    def run(self):
        self.is_running = True
        while self.is_running:
            dt = self.clock.tick(FPS) / 1000.0  # segundos desde el último frame
            self.handle_events()
            self.update(dt)
            self.render()
        self.quit()

    def quit(self):
        pygame.quit()
        sys.exit()

# ---------- Entrada punto de ejecución ----------
if __name__ == "__main__":
    engine = GameEngine()
    engine.run()
