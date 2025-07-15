# Importamos las librerías necesarias de Ursina
from ursina import *
import math

# --- Configuración de Niveles ---
LEVEL_CONFIG = {
    1: {'targets': 10, 'speed': (10, 15), 'scale': 2.8, 'accuracy_goal': 50},
    2: {'targets': 10, 'speed': (15, 22), 'scale': 2.0, 'accuracy_goal': 60},
    3: {'targets': 10, 'speed': (20, 28), 'scale': 1.8, 'accuracy_goal': 75}
}

# --- Clase para los Objetivos Esféricos (¡Ahora Patos!) ---
class TargetSphere(Entity):
    def __init__(self, speed_range, scale):
        side = random.choice([-1, 1])
        # Posición Y ajustada para que salgan más bajas
        start_pos = Vec3(22 * side, random.uniform(-8, -2), random.uniform(15, 25))
        direction = Vec3(-side, random.uniform(-.2, .2), random.uniform(-.1, .1))

        super().__init__(
            model='quad',  # ¡CAMBIADO A 'quad' para usar una imagen 2D!
            texture='assets/textures/mario.png', # ¡AQUÍ ES DONDE PONES LA RUTA A TU IMAGEN DE PATO!
            color=color.white, # Usa color.white para que la textura no se tiña.
            scale=scale,
            position=start_pos,
            collider='box', # Cambiamos a 'box' o 'quad' porque ya no es una esfera. 'box' es una buena opción general.
            shadow=True,
            billboard=True # ¡IMPORTANTE! Esto hace que el pato siempre mire a la cámara, sin importar la rotación.
        )
        self.direction = direction
        self.speed = random.uniform(speed_range[0], speed_range[1])

    def update(self):
        # Mueve el objetivo
        self.position += self.direction * self.speed * time.dt
        # Destruye el objetivo si sale de la pantalla y spawnea el siguiente
        if abs(self.x) > 24:
            destroy(self)
            invoke(spawn_next_target, delay=0.5)

    def hit(self):
        global hits, points
        hit_sound.play()
        hits += 1
        points += 100
        # Crea un efecto visual de impacto (puedes ajustar este modelo/color si quieres un efecto diferente para los patos)
        # ESCALA DEL EFECTO DE IMPACTO REDUCIDA AQUÍ
        effect = Entity(model='quad', texture='assets/textures/hit_effect.png', color=color.white, scale=self.scale * 0.8, position=self.world_position, shadow=False, billboard=True) # Escala inicial reducida a 0.8 de la escala del objetivo
        effect.animate_scale(self.scale * 1.2, duration=0.2, curve=curve.out_quad) # Animación a un tamaño ligeramente mayor, también reducido
        effect.fade_out(duration=0.2)
        destroy(effect, delay=0.2)

        # Destruye el objetivo y spawnea el siguiente
        destroy(self)
        invoke(spawn_next_target, delay=0.5)

# --- Variables Globales del Juego ---
hits, points, shots_fired = 0, 0, 0
targets_spawned = 0
unlocked_level = 1
current_level = 1
game_active = False
last_shot_time = 0
current_bg_music = None # Global variable to hold the current background music

# --- Funciones del Juego ---
def go_to_level_select():
    main_menu.disable()
    level_select_menu.enable()
    update_level_buttons()

def start_level(level):
    global hits, points, shots_fired, game_active, current_level, targets_spawned, last_shot_time, current_bg_music
    current_level = level
    hits, points, shots_fired, targets_spawned = 0, 0, 0, 0
    game_active = True

    # Stop any currently playing background music
    if current_bg_music:
        current_bg_music.stop()

    # Play background music based on the level
    if current_level == 1:
        current_bg_music = start_sound
    elif current_level == 2:
        current_bg_music = level2_music
    elif current_level == 3:
        current_bg_music = level3_music

    if current_bg_music:
        current_bg_music.play()

    level_select_menu.disable()
    game_hud.enable()
    crosshair.enable()
    mouse.locked = True

    last_shot_time = time.time()

    pistol.disable()
    rifle.disable()
    shotgun.disable()

    if current_level == 1:
        pistol.enable()
    elif current_level == 2:
        rifle.enable()
    elif current_level == 3:
        shotgun.enable()

    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)

    spawn_next_target()

def spawn_next_target():
    global targets_spawned
    if not game_active: return

    if targets_spawned < LEVEL_CONFIG.get(current_level, {}).get('targets', 0):
        config = LEVEL_CONFIG.get(current_level, {})
        TargetSphere(config.get('speed', (10, 15)), config.get('scale', 1))
        targets_spawned += 1
        update_hud()
    else:
        invoke(end_level, delay=1)

def end_level():
    global game_active, unlocked_level, current_bg_music
    game_active = False

    # Stop background music when level ends
    if current_bg_music:
        current_bg_music.stop()

    game_hud.disable()
    crosshair.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    mouse.locked = False

    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    goal = LEVEL_CONFIG.get(current_level, {}).get('accuracy_goal', 0)

    end_panel = Entity(parent=camera.ui, model='quad', scale=(.8, .5), color=color.dark_gray.tint(.2), z=1)
    Text(parent=end_panel, text=f"Precisión: {accuracy:.1f}% (Objetivo: {goal}%)", origin=(0,0), y=0, scale=1.5)
    Text(parent=end_panel, text=f"Aciertos: {hits} / {shots_fired}", origin=(0,0), y=-.1, scale=1.5)

    if accuracy >= goal:
        message = f"¡NIVEL {current_level} COMPLETADO!"
        if current_level < 3:
            unlocked_level = max(unlocked_level, current_level + 1)

        Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2)
        Button(parent=end_panel, text="Menú de Niveles", color=color.azure, scale=(0.25, 0.08), y=-.3, on_click=Func(lambda: (destroy(end_panel), show_level_select_menu())))
    else:
        message = "INTÉNTALO DE NUEVO"

        Text(parent=end_panel, text=message, origin=(0,0), y=.2, scale=2)
        Button(parent=end_panel, text="Reintentar", color=color.azure, scale=(0.25, 0.08), y=-.25, on_click=Func(lambda: (destroy(end_panel), start_level(current_level))))
        Button(parent=end_panel, text="Menú de Niveles", color=color.red, scale=(0.25, 0.08), y=-.4, on_click=Func(lambda: (destroy(end_panel), show_level_select_menu())))


def show_level_select_menu():
    global current_bg_music
    game_hud.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    crosshair.disable()
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)
    level_select_menu.enable()
    update_level_buttons()
    mouse.locked = False
    # Stop background music when going to level select
    if current_bg_music:
        current_bg_music.stop()

def show_main_menu():
    global current_bg_music
    level_select_menu.disable()
    game_hud.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    crosshair.disable()
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)
    main_menu.enable()
    mouse.locked = False
    # Stop background music when going to main menu
    if current_bg_music:
        current_bg_music.stop()

def update_hud():
    accuracy = (hits / shots_fired) * 100 if shots_fired > 0 else 0
    hud_text.text = (
        f"NIVEL {current_level}\n"
        f"Objetivo: {targets_spawned}/{LEVEL_CONFIG.get(current_level, {}).get('targets', 0)}\n"
        f"Aciertos: {hits}\n"
        f"Precisión: {accuracy:.1f}%"
    )

def update_level_buttons():
    for i, button in enumerate(level_buttons):
        button.disabled = (i + 1 > unlocked_level)
        button.text_entity.color = color.white if not button.disabled else color.gray

def resume_game():
    global current_bg_music
    pause_menu.disable()
    mouse.locked = True
    application.resume()
    # Resume background music if it was playing
    if current_bg_music:
        current_bg_music.play() # Use play() to resume from where it left off

# --- Inicialización de la Aplicación Ursina ---
# Set fullscreen=True to make the window maximize to the full screen
app = Ursina(title='AIM PRESICION DDC', borderless=False, fullscreen=True)

# --- Sonidos ---
gunshot_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.3)
hit_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.5)
# Main background music (for level 1)
start_sound = Audio('assets/sounds/fondo.mp3', loop=True, autoplay=False, volume=0.8) # Increased volume
# New background music for Level 2
level2_music = Audio('assets/sounds/fondoNivel2.mp3', loop=True, autoplay=False, volume=0.8) # Increased volume
# New background music for Level 3
level3_music = Audio('assets/sounds/fondoNivel3.mp3', loop=True, autoplay=False, volume=0.8) # Increased volume


# --- Creación del Entorno (Cabina de Disparo con estilo oscuro) ---
shooting_range_background = Entity(
    model='quad',
    texture='assets/textures/mapa.png',
    scale=(100, 50),
    position=(0, 0, 50),
    rotation_y=180,
    double_sided=True
).disable()

# **CABINA DE DISPARO - ESTILO OSCURO**
back_wall = Entity(    # Crea una nueva entidad (un objeto en la escena) y la asigna a la variable 'back_wall'.
    model='cube',      # Define la forma de la entidad. En este caso, es un cubo.
    scale=(40, 30, 1), # Ancho: 10 unidades (de X=-5 a X=5), Alto: 30, Profundidad: 1. (Esta es la nueva anchura de referencia).
    position=(0, 5, 30), # Ubicación central: X=0, Y=5, Z=30 (esta es la pared trasera).
    texture='assets/textures/mapa.png', # Cambiado a madera.png
    color=color.white, # Cambiado a blanco para que la textura se vea
    collider='box'     # Asigna un colisionador de tipo caja.
)

left_wall = Entity(
    model='cube',
    scale=(1, 30, 60), # Ancho: 1, Alto: 30, Profundidad: 45. (Cubre desde Z=-15 hasta Z=30).
    position=(-20, 5, 7.5), # Posición X ajustada a -20.
    texture='assets/textures/mapa.png', # Cambiado a madera.png
    color=color.white, # Cambiado a blanco para que la textura se vea
    collider='box'
)

right_wall = Entity(
    model='cube',
    scale=(1, 30, 60), # Ancho: 1, Alto: 30, Profundidad: 45.
    position=(20, 5, 7.5), # Posición X ajustada a 20.
    texture='assets/textures/mapa.png', # Textura de la pared.
    color=color.white, # ¡CAMBIADO A BLANCO!
    collider='box'
)

ceiling = Entity(
    model='cube',
    scale=(42, 1, 45), # ANCHO AJUSTADO: Ahora es 42 para cubrir el espacio de 40 de la pared trasera y un poco más.
    position=(0, 20, 7.5), # Posición X=0 (centrado), Y=20 (altura del techo), Z=7.5 (posición Z central, igual que paredes laterales).
    texture='assets/textures/cieloo.png', # Textura del cielo (asumiendo que 'cieloo.png' es la versión oscura).
    color=color.white, # Asegurarse de que el color sea blanco si hay textura
    collider='box'
)

# Suelo (con textura de cesped oscuro)
ground_plane = Entity(
    model='plane',
    scale=(150, 1, 150), # Un tamaño muy grande para asegurar que siempre haya suelo visible.
    position=(0, -10, 5), # Posición Y ajustada para estar más cerca
    texture='assets/textures/piso.jpg', # Cambiado a una textura de cesped oscuro
    texture_scale=(2, 2), # Escala de la textura para que se vea más grande y cercano.
    collider='box'
)

# Cielo (completamente negro, sin textura si cieloo.png es el fondo oscuro)
sky_color = Sky(color=color.black)

# Luz direccional - ¡AUMENTAMOS SU INTENSIDAD!
sun = DirectionalLight(y=10, x=20, shadows=True, color=color.white) # Cambiado de color.white33 a color.white

# ¡AÑADIMOS LUZ AMBIENTAL para iluminar las áreas en sombra!
ambient_light = AmbientLight(color=color.rgba(100, 100, 100, 255)) # Una luz ambiental gris suave

# --- Configuración del Jugador (Cámara estática) ---
camera.position = (0, 0, -15)
camera.fov = 80

# --- Arma y Mira (DISEÑOS MEJORADOS) ---

# --- Arma y Mira (DISEÑOS MEJORADOS y CORREGIDOS) ---

# Pistola mejorada
# La entidad 'pistol' ahora solo actúa como un contenedor para sus partes.
pistol = Entity(parent=camera, position=(0.4, -0.45, 1.2), rotation=(0, 0, 0))
# Cuerpo principal
Entity(parent=pistol, model='cube', scale=(0.12, 0.2, 0.6), color=color.dark_gray.tint(-0.1))
# Empuñadura
Entity(parent=pistol, model='cube', scale=(0.12, 0.3, 0.2), position=(0, -0.2, -0.2), color=color.black, texture='brick') # Ejemplo: textura 'brick' para empuñadura
# Corredera
Entity(parent=pistol, model='cube', scale=(0.1, 0.15, 0.55), position=(0, 0.07, 0), color=color.gray)
# Cañón asomando
Entity(parent=pistol, model='cube', scale=(0.05, 0.05, 0.1), position=(0, 0.07, 0.3), color=color.black)
# Gatillo
Entity(parent=pistol, model='cube', scale=(0.04, 0.08, 0.05), position=(0, -0.07, -0.1), color=color.gray)
# Miras
Entity(parent=pistol, model='cube', scale=(0.02, 0.02, 0.05), position=(0, 0.15, 0.25), color=color.black) # Mira delantera
Entity(parent=pistol, model='cube', scale=(0.05, 0.02, 0.05), position=(0, 0.15, -0.25), color=color.black) # Mira trasera
pistol.disable()


# Rifle mejorado
# La entidad 'rifle' ahora solo actúa como un contenedor.
rifle = Entity(parent=camera, position=(0.6, -0.55, 1.8), rotation=(0,0,0))
# Cuerpo principal / Receptor
Entity(parent=rifle, model='cube', scale=(0.1, 0.1, 1.2), color=color.dark_gray.tint(-0.1))
# Cañón
Entity(parent=rifle, model='cylinder', scale=(0.05, 0.05, 0.8), position=(0, 0, 0.6), rotation_x=90, color=color.gray)
# Culata
Entity(parent=rifle, model='cube', scale=(0.1, 0.25, 0.3), position=(0, -0.1, -0.6), color=color.black)
# Empuñadura de pistola
Entity(parent=rifle, model='cube', scale=(0.08, 0.2, 0.1), position=(0, -0.15, -0.3), color=color.black)
# Mira telescópica
Entity(parent=rifle, model='cylinder', scale=(0.05, 0.05, 0.3), position=(0, 0.08, 0.2), rotation_x=90, color=color.black)
# Lente de mira
Entity(parent=rifle, model='circle', scale=0.04, position=(0, 0.08, 0.35), rotation_x=90, color=color.light_gray)
# Bípode
Entity(parent=rifle, model='cube', scale=(0.02, 0.1, 0.02), position=(-0.05, -0.08, 0.3), color=color.gray)
Entity(parent=rifle, model='cube', scale=(0.02, 0.1, 0.02), position=(0.05, -0.08, 0.3), color=color.gray)
# Cargador
Entity(parent=rifle, model='cube', scale=(0.06, 0.2, 0.1), position=(0, -0.1, -0.1), color=color.dark_gray)
# Riel Picatinny en la parte superior
Entity(parent=rifle, model='cube', scale=(0.08, 0.01, 0.8), position=(0, 0.06, 0), color=color.dark_gray)
rifle.disable()

# Escopeta mejorada
# La entidad 'shotgun' ahora solo actúa como un contenedor.
shotgun = Entity(parent=camera, position=(0.5, -0.65, 1.5), rotation=(0,0,0))
# Cuerpo principal
Entity(parent=shotgun, model='cube', scale=(0.18, 0.15, 1.0), color=color.dark_gray.tint(-0.1))
# Cañón
Entity(parent=shotgun, model='cylinder', scale=(0.08, 0.08, 0.8), position=(0, 0, 0.5), rotation_x=90, color=color.gray)
# Guardamanos/Bomba
Entity(parent=shotgun, model='cube', scale=(0.12, 0.1, 0.25), position=(0, -0.05, 0.2), color=color.black)
# Empuñadura de pistola (o parte de la culata)
Entity(parent=shotgun, model='cube', scale=(0.18, 0.3, 0.15), position=(0, -0.2, -0.4), color=color.black, texture='wood') # Ejemplo: textura 'wood'
# Recámara o parte superior del cuerpo
Entity(parent=shotgun, model='cube', scale=(0.18, 0.05, 0.3), position=(0, 0.1, -0.1), color=color.dark_gray)
# Cargador tubular bajo el cañón
Entity(parent=shotgun, model='cylinder', scale=(0.05, 0.05, 0.7), position=(0, -0.08, 0.3), rotation_x=90, color=color.dark_gray)
# Alza y mira delantera
Entity(parent=shotgun, model='cube', scale=(0.02, 0.03, 0.05), position=(0, 0.08, 0.45), color=color.black) # Mira delantera
Entity(parent=shotgun, model='cube', scale=(0.05, 0.02, 0.05), position=(0, 0.08, -0.2), color=color.black) # Alza trasera
shotgun.disable()

crosshair = Entity(parent=camera.ui, model='circle', scale=0.008, color=color.red)

# --- Interfaz de Usuario (UI) Mejorada ---
game_hud = Entity(parent=camera.ui, enabled=False)
hud_background = Entity(parent=game_hud, model='quad', scale=(.35, .25), position=window.bottom_left, color=color.black66)
hud_text = Text(parent=hud_background, text="", origin=(-.5, .5), position=(-.45, .45), scale=1.2)

# --- Menú Principal ---
main_menu = Entity(
    parent=camera.ui,
    model='quad',
    texture='assets/textures/logo.png',
    scale_x=camera.aspect_ratio,
    scale_y=1,
    enabled=True,
    z=0.1,
    color=color.white
)

start_button = Button(parent=main_menu, text="INICIAR", color=color.azure, scale=(0.4, 0.1), y=-0.1, on_click=go_to_level_select)
quit_button = Button(parent=main_menu, text="SALIR", color=color.azure, scale=(0.4, 0.1), y=-0.25, on_click=application.quit)


# --- Menú de Selección de Nivel ---
level_select_menu = Entity(parent=camera.ui, enabled=False)
level_title = Text(parent=level_select_menu, text="Seleccionar Nivel", scale=3, origin=(0,0), y=0.4)
level_1_button = Button(parent=level_select_menu, text="Nivel 1", scale=(0.3, 0.1), y=0.1, on_click=lambda: start_level(1))
level_2_button = Button(parent=level_select_menu, text="Nivel 2", scale=(0.3, 0.1), y=0, on_click=lambda: start_level(2))
level_3_button = Button(parent=level_select_menu, text="Nivel 3", scale=(0.3, 0.1), y=-0.1, on_click=lambda: start_level(3))
level_buttons = [level_1_button, level_2_button, level_3_button]

# --- Menú de Pausa ---
pause_menu = Entity(parent=camera.ui, enabled=False, model='quad', scale=(0.5, 0.5), color=color.black90)
Text(parent=pause_menu, text="Juego en Pausa", origin=(0,0), y=0.4, scale=2)

Button(parent=pause_menu, text="Reanudar Juego", color=color.azure, scale=(0.8, 0.2), y=0.15, on_click=resume_game)
Button(parent=pause_menu, text="Menú de Niveles", color=color.blue, scale=(0.8, 0.2), y=-0.1, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_level_select_menu())))
Button(parent=pause_menu, text="Salir al Menú Principal", color=color.red, scale=(0.8, 0.2), y=-0.35, on_click=Func(lambda: (application.resume(), pause_menu.disable(), show_main_menu())))


# --- Lógica Principal ---
def update():
    global current_bg_music
    if not application.paused and game_active:
        update_hud()
        camera.rotation_y += mouse.velocity.x * 60
        camera.rotation_x -= mouse.velocity.y * 60
        camera.rotation_x = clamp(camera.rotation_x, -50, 50)
        camera.rotation_y = clamp(camera.rotation_y, -80, 80)
    elif application.paused and current_bg_music and current_bg_music.playing:
        current_bg_music.pause() # Pause music when game is paused

def input(key):
    global shots_fired, last_shot_time, current_bg_music
    if key == 'escape' and game_active:
        application.paused = not application.paused
        pause_menu.enabled = application.paused
        mouse.locked = not pause_menu.enabled
        # Pause or resume music based on game pause state
        if application.paused:
            if current_bg_music:
                current_bg_music.pause()
        else:
            if current_bg_music:
                current_bg_music.play()

    if application.paused:
        return

    if game_active and key == 'left mouse down':
        # Control de cadencia de fuego para todas las armas
        if time.time() - last_shot_time < 0.5: # Disparo cada 0.5 segundos
            return
        last_shot_time = time.time() # Actualiza el tiempo del último disparo

        shots_fired += 1
        gunshot_sound.play()

        if current_level == 1:
            pistol.rotation_x = -10
            pistol.animate_rotation_x(0, duration=0.1)
            ignore_list = [pistol]
        elif current_level == 2:
            rifle.rotation_x = -5
            rifle.animate_rotation_x(0, duration=0.1)
            ignore_list = [rifle]
        elif current_level == 3:
            shotgun.rotation_x = -15
            shotgun.animate_rotation_x(0, duration=0.1)
            ignore_list = [shotgun]
        else:
            ignore_list = []

        hit_info = raycast(camera.world_position, camera.forward, distance=200, ignore=ignore_list)
        if hit_info.hit and hasattr(hit_info.entity, 'hit'):
            hit_info.entity.hit()

# --- Iniciar el Juego ---
game_hud.disable()
pistol.disable()
rifle.disable()
shotgun.disable()
crosshair.disable()
mouse.locked = False
app.run()