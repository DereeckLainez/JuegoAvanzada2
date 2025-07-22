# Importamos las librerías necesarias de Ursina
from ursina import *
import math
import random
import time

# --- Configuración de Niveles (CON NUEVOS OBJETIVOS DE PRECISIÓN) ---
LEVEL_CONFIG = {
    1: {'targets': 10, 'speed': (10, 15), 'scale': 2.8, 'accuracy_goal': 40},
    2: {'targets': 10, 'speed': (15, 22), 'scale': 2.0, 'accuracy_goal': 70},
    3: {'targets': 10, 'speed': (20, 28), 'scale': 1.8, 'accuracy_goal': 90}
}

# --- Clase para los Objetivos (Esferas con colores aleatorios) ---
class TargetSphere(Entity):
    def __init__(self, speed_range, scale):
        side = random.choice([-1, 1])
        # Posición Y ajustada para que salgan más bajas
        start_pos = Vec3(22 * side, random.uniform(-8, -2), random.uniform(15, 25))
        direction = Vec3(-side, random.uniform(-.2, .2), random.uniform(-.1, .1))

        # Lista de colores para elegir aleatoriamente
        possible_colors = [color.red, color.blue, color.green, color.yellow, color.magenta, color.cyan]

        super().__init__(
            model='sphere',
            color=random.choice(possible_colors),
            scale=scale,
            position=start_pos,
            collider='sphere' # Colisionador esférico para ser detectado por el ratón y los disparos.
        )
        self.direction = direction
        self.speed = random.uniform(speed_range[0], speed_range[1])

    def update(self):
        self.position += self.direction * self.speed * time.dt
        # Destruir el objetivo si sale de la pantalla y generar uno nuevo
        if abs(self.x) > 24:
            destroy(self)
            invoke(spawn_next_target, delay=0.5)

    def hit(self):
        """
        Esta función se llama cuando el objetivo es impactado por un disparo.
        """
        global hits, points
        # El sonido de impacto se reproduce aquí, separado del sonido del arma.
        hit_sound.play()
        hits += 1
        points += 100
        update_stats_display()

        # --- Efecto de Explosión ---
        for _ in range(random.randint(5, 10)):
            fragment = Entity(
                model='sphere',
                color=self.color,
                scale=self.scale * random.uniform(0.1, 0.3),
                position=self.world_position,
                collider=None
            )
            fragment.animate_position(
                fragment.position + Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)) * 2,
                duration=random.uniform(0.3, 0.6),
                curve=curve.out_quad
            )
            fragment.fade_out(duration=random.uniform(0.3, 0.6))
            destroy(fragment, delay=0.6)

        flash_effect = Entity(model='sphere', color=color.yellow, scale=self.scale * 1.2, position=self.world_position)
        flash_effect.animate_scale(self.scale * 1.5, duration=0.1, curve=curve.out_quad)
        flash_effect.fade_out(duration=0.1)
        destroy(flash_effect, delay=0.1)

        destroy(self)
        invoke(spawn_next_target, delay=0.5)

# --- Variables Globales del Juego ---
hits, points, shots_fired = 0, 0, 0
targets_spawned = 0
unlocked_level = 1 # El jugador empieza solo con el nivel 1 desbloqueado
current_level = 1
game_active = False
last_shot_time = 0
current_bg_music = None

# --- Funciones del Juego ---
def update_stats_display():
    """Actualiza el texto del contador de aciertos y precisión en la UI."""
    total_targets_for_level = LEVEL_CONFIG[current_level]['targets']
    # La precisión ahora se basa en los aciertos sobre el total de objetivos del nivel.
    shot_accuracy = (hits / total_targets_for_level) * 100 if total_targets_for_level > 0 else 0
    stats_text.text = (
        f"Precisión: {shot_accuracy:.0f}%\n" # Se muestra sin decimales
        f"Aciertos: {hits}/{total_targets_for_level}"
    )
    stats_text.color = color.white

def go_to_level_select():
    main_menu.disable()
    level_select_menu.enable()
    update_level_buttons()

def start_level(level):
    global hits, points, shots_fired, game_active, current_level, targets_spawned, last_shot_time, current_bg_music
    current_level = level
    hits, points, shots_fired = 0, 0, 0
    targets_spawned = 0
    
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)

    game_active = True
    
    update_stats_display()

    if current_bg_music:
        current_bg_music.stop()

    if current_level == 1:
        current_bg_music = start_sound
    elif current_level == 2:
        current_bg_music = level2_music
    elif current_level == 3:
        current_bg_music = level3_music

    if current_bg_music:
        current_bg_music.play()
        current_bg_music.volume = 0.8

    level_select_menu.disable()
    crosshair.enable()
    stats_text.enable()
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

    spawn_next_target()

def spawn_next_target():
    global targets_spawned
    if not game_active: return

    if targets_spawned < LEVEL_CONFIG[current_level]['targets']:
        config = LEVEL_CONFIG[current_level]
        TargetSphere(config['speed'], config['scale'])
        targets_spawned += 1
    else:
        invoke(end_level, delay=1)

def end_level():
    global game_active, unlocked_level, current_bg_music
    game_active = False

    if current_bg_music:
        current_bg_music.stop()

    crosshair.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    stats_text.disable()
    mouse.locked = False

    total_targets = LEVEL_CONFIG[current_level]['targets']
    accuracy = (hits / total_targets) * 100 if total_targets > 0 else 0
    goal = LEVEL_CONFIG[current_level]['accuracy_goal']

    end_panel = Entity(parent=camera.ui, model='quad', scale_x=camera.aspect_ratio, scale_y=1, color=color.black90, z=1)
    
    Text(parent=end_panel, text=f"Objetivos Acertados: {hits} / {total_targets}", origin=(0,0), y=0.2, scale=1.5)
    Text(parent=end_panel, text=f"Precisión Final: {accuracy:.0f}%", origin=(0,0), y=0.1, scale=1.5)

    # --- LÓGICA DE BOTONES MEJORADA PARA EVITAR ERRORES ---
    def destroy_and_show_levels():
        destroy(end_panel)
        show_level_select_menu()

    def destroy_and_restart():
        destroy(end_panel)
        start_level(current_level)

    def destroy_and_advance():
        destroy(end_panel)
        if current_level < 3:
            start_level(current_level + 1)
        else:
            show_level_select_menu()

    if accuracy >= goal:
        message = "¡OBJETIVO CUMPLIDO!"
        if current_level < 3:
            unlocked_level = max(unlocked_level, current_level + 1)
        Text(parent=end_panel, text=message, origin=(0,0), y=0.35, scale=2, color=color.green)
        Button(parent=end_panel, text="Avanzar", color=color.green, scale=(0.25, 0.08), y=-.1, on_click=destroy_and_advance)
    else:
        message = "OBJETIVO NO CUMPLIDO"
        Text(parent=end_panel, text=message, origin=(0,0), y=0.35, scale=2, color=color.red)
        Button(parent=end_panel, text="Reiniciar", color=color.black, scale=(0.25, 0.08), y=-.1, on_click=destroy_and_restart)
        Button(parent=end_panel, text="Menú de Niveles", color=color.azure, scale=(0.25, 0.08), y=-.25, on_click=destroy_and_show_levels)

def show_level_select_menu():
    global current_bg_music, game_active
    game_active = False
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    crosshair.disable()
    stats_text.disable()
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)
    level_select_menu.enable()
    update_level_buttons()
    mouse.locked = False
    if current_bg_music:
        current_bg_music.stop()

def show_main_menu():
    global current_bg_music, game_active
    game_active = False
    level_select_menu.disable()
    pistol.disable()
    rifle.disable()
    shotgun.disable()
    crosshair.disable()
    stats_text.disable()
    for t in scene.entities:
        if isinstance(t, TargetSphere):
            destroy(t)
    main_menu.enable()
    mouse.locked = False
    if current_bg_music:
        current_bg_music.stop()

def update_level_buttons():
    for i, button in enumerate(level_buttons):
        button.disabled = (i + 1 > unlocked_level)
        button.text_entity.color = color.white if not button.disabled else color.gray

# --- NUEVAS FUNCIONES DE PAUSA ---
def resume_game():
    """Reanuda el juego, restaurando la UI y la música."""
    application.paused = False
    pause_menu.enabled = False
    mouse.locked = True
    crosshair.enabled = True
    stats_text.enabled = True
    if current_bg_music:
        current_bg_music.volume = 0.8

def pause_game():
    """Pausa el juego, mostrando el menú y ocultando la UI."""
    application.paused = True
    pause_menu.enabled = True
    mouse.locked = False
    crosshair.enabled = False
    stats_text.enabled = False # Oculta las estadísticas
    if current_bg_music:
        current_bg_music.volume = 0

def go_to_main_menu_from_pause():
    """Función para transicionar del menú de pausa al menú principal de forma segura."""
    application.paused = False
    pause_menu.disable()
    show_main_menu()

def go_to_level_select_from_pause():
    """Función para transicionar del menú de pausa a la selección de nivel de forma segura."""
    application.paused = False
    pause_menu.disable()
    show_level_select_menu()

def restart_level_from_pause():
    """Reinicia el nivel actual desde el menú de pausa de forma estable."""
    application.paused = False
    pause_menu.disable()
    start_level(current_level) # Llama directamente a start_level para un reinicio limpio.

# --- Inicialización de la Aplicación Ursina ---
app = Ursina(title='AIM PRESICION DDC', borderless=False, fullscreen=True)
window.fps_counter.enabled = False
window.entity_counter.enabled = False
window.collider_counter.enabled = False

# --- Sonidos ---
pistol_shot_sound = Audio('assets/sounds/pistol_shot.mp3', loop=False, autoplay=False, volume=0.3)
rifle_shot_sound = Audio('assets/sounds/ak-47-89833.mp3', loop=False, autoplay=False, volume=0.3)
shotgun_shot_sound = Audio('assets/sounds/gunshot-372470.mp3', loop=False, autoplay=False, volume=0.3)
hit_sound = Audio('assets/sounds/hit.mp3', loop=False, autoplay=False, volume=0.5)
start_sound = Audio('assets/sounds/fondo.mp3', loop=True, autoplay=False, volume=0.8)
level2_music = Audio('assets/sounds/fondoNivel2.mp3', loop=True, autoplay=False, volume=0.8)
level3_music = Audio('assets/sounds/fondoNivel3.mp3', loop=True, autoplay=False, volume=0.8)
ricochet_sound = Audio('assets/sounds/ricochet.mp3', loop=False, autoplay=False, volume=0.4)

# --- Creación del Entorno (Estilo Piedra) ---
# Se utiliza la textura de piedra para crear un ambiente de cueva o búnker.
back_wall = Entity(model='cube', scale=(40, 30, 1), position=(0, 5, 30), texture='assets/textures/Piedra.jpg', color=color.white, collider='box', texture_scale=(10,10))
left_wall = Entity(model='cube', scale=(1, 30, 90), position=(-20, 5, 7.5), texture='assets/textures/Piedra.jpg', color=color.white, collider='box', texture_scale=(20,10))
right_wall = Entity(model='cube', scale=(1, 30, 90), position=(20, 5, 7.5), texture='assets/textures/Piedra.jpg', color=color.white, collider='box', texture_scale=(20,10))
ceiling = Entity(model='cube', scale=(42, 1, 85), position=(0, 20, 7.5), texture='assets/textures/Piedra.jpg', color=color.white, collider='box', texture_scale=(10,20))
ground_plane = Entity(model='plane', scale=(150, 1, 150), position=(0, -10, 5), texture='assets/textures/Piedra.jpg', texture_scale=(20, 20), collider='box')
# El cielo se mantiene negro para simular un espacio cerrado.
sky_color = Sky(color=color.black)
# Se ajusta la iluminación para un ambiente de piedra.
sun = DirectionalLight(y=10, x=20, shadows=True, color=color.white)
ambient_light = AmbientLight(color=color.rgba(120, 120, 120, 255)) # Luz ambiental más clara para ver la textura

# --- Configuración del Jugador (Cámara estática) ---
camera.position = (0, 0, -15)
camera.fov = 80
camera.clip_plane_far = 5000

# --- Armas ---
pistol = Entity(parent=camera, model='assets/models/GUN.obj', texture='assets/textures/GUN_Material.003_BaseColor.jpg', unlit=True, rotation=(5, 180, 0), position=(0.4, -0.4, 1.3), scale=0.15)
rifle = Entity(parent=camera, model='assets/models/xm177.obj', color=color.black, rotation=(0, 100, -5), position=(0.6, -0.5, 1.5), scale=0.03)
shotgun = Entity(parent=camera, model='assets/models/Shotgun.obj', texture='assets/textures/Shotgun_Albedo.png', unlit=True, rotation=(0, 90, 0), position=(0.5, -0.5, 1.6), scale=0.15)
crosshair = Entity(parent=camera.ui, model='circle', scale=0.008, color=color.red)

# --- Interfaz de Usuario (UI) ---
# === MENÚ PRINCIPAL ===
main_menu = Entity(parent=camera.ui, model='quad', texture='assets/textures/logo.jpg', scale_x=camera.aspect_ratio, scale_y=1, enabled=True, z=0.1, color=color.white)
start_button = Button(parent=main_menu, text="INICIAR", color=color.blue.tint(-0.2), scale=(0.25, 0.1), position=(-0.3, -0.35), on_click=go_to_level_select)
quit_button = Button(parent=main_menu, text="SALIR", color=color.red.tint(-0.2), scale=(0.25, 0.1), position=(0.3, -0.35), on_click=application.quit)

# === MENÚ DE SELECCIÓN DE NIVEL (CON BOTÓN DE VOLVER) ===
level_select_menu = Entity(parent=camera.ui, enabled=False)
level_background = Entity(parent=level_select_menu, model='quad', texture='assets/textures/Levels.png', scale_x=camera.aspect_ratio, scale_y=1, z=0.1, color=color.white)
button_container = Entity(parent=level_select_menu, y=-0.3) # Se mueve un poco hacia arriba para hacer espacio
level_1_button = Button(parent=button_container, text="Nivel 1", scale=(0.25, 0.12), x=-0.35, on_click=lambda: start_level(1), color=color.azure.tint(-0.2), highlight_scale=1.1, highlight_color=color.azure)
level_2_button = Button(parent=button_container, text="Nivel 2", scale=(0.25, 0.12), x=0, on_click=lambda: start_level(2), color=color.azure.tint(-0.2), highlight_scale=1.1, highlight_color=color.azure)
level_3_button = Button(parent=button_container, text="Nivel 3", scale=(0.25, 0.12), x=0.35, on_click=lambda: start_level(3), color=color.azure.tint(-0.2), highlight_scale=1.1, highlight_color=color.azure)
level_buttons = [level_1_button, level_2_button, level_3_button]
Button(parent=level_select_menu, text="Volver al Menú", scale=(0.25, 0.08), y=-0.45, on_click=show_main_menu, color=color.red.tint(-0.2))


# === MENÚ DE PAUSA (CON BOTÓN DE REINICIO) ===
pause_menu = Entity(parent=camera.ui, enabled=False, z=2)
Entity(parent=pause_menu, model='quad', scale_x=camera.aspect_ratio, scale_y=1, color=color.black90)
Text(parent=pause_menu, text="PAUSA", origin=(0,0), y=0.3, scale=3)
Button(parent=pause_menu, text="Reanudar", color=color.green.tint(-0.2), scale=(0.4, 0.1), y=0.15, on_click=resume_game)
Button(parent=pause_menu, text="Reiniciar Partida", color=color.orange.tint(-0.2), scale=(0.4, 0.1), y=0.0, on_click=restart_level_from_pause)
Button(parent=pause_menu, text="Ir al menú de niveles", color=color.azure, scale=(0.4, 0.1), y=-0.15, on_click=go_to_level_select_from_pause)
Button(parent=pause_menu, text="Ir al menú principal", color=color.red, scale=(0.4, 0.1), y=-0.30, on_click=go_to_main_menu_from_pause)

# === CONTADOR DE ESTADÍSTICAS ===
stats_text = Text(parent=camera.ui, text="Precisión: 0.0%\nAciertos: 0/0", origin=(-0.5, 0.5), position=(-0.75, -0.4), scale=1.5, color=color.white, enabled=False)

# --- Lógica Principal ---
def update():
    if not application.paused and game_active:
        camera.rotation_y += mouse.velocity.x * 60
        camera.rotation_x -= mouse.velocity.y * 60
        camera.rotation_x = clamp(camera.rotation_x, -50, 50)
        camera.rotation_y = clamp(camera.rotation_y, -80, 80)

def input(key):
    global shots_fired, last_shot_time
    
    # --- LÓGICA DE PAUSA REFINADA ---
    if key == 'escape' and game_active:
        if application.paused:
            resume_game()
        else:
            pause_game()
        return

    if application.paused or not game_active:
        return

    if key == 'left mouse down':
        if time.time() - last_shot_time < 0.5:
            return
        
        last_shot_time = time.time()
        
        # El sonido del disparo del arma correspondiente siempre se reproduce
        if current_level == 1:
            pistol_shot_sound.play()
            pistol.rotation_x = -10
            pistol.animate_rotation_x(0, duration=0.1)
        elif current_level == 2:
            rifle_shot_sound.play()
            rifle.rotation_x = -10
            rifle.animate_rotation_x(0, duration=0.1)
        elif current_level == 3:
            shotgun_shot_sound.play()
            shotgun.rotation_x = -10
            shotgun.animate_rotation_x(0, duration=0.1)

        shots_fired += 1
        
        # --- LÓGICA DE DISPARO CON SONIDO DE FALLO MEJORADA ---
        hit_entity = mouse.hovered_entity 

        def play_result_sound():
            if hit_entity and isinstance(hit_entity, TargetSphere):
                # No llamamos a hit() directamente para evitar que el sonido se reproduzca dos veces.
                # En su lugar, separamos la lógica.
                global hits, points
                hit_sound.play()
                hits += 1
                points += 100
                
                # --- Efecto de Explosión (copiado de la función hit) ---
                for _ in range(random.randint(5, 10)):
                    fragment = Entity(model='sphere', color=hit_entity.color, scale=hit_entity.scale * random.uniform(0.1, 0.3), position=hit_entity.world_position, collider=None)
                    fragment.animate_position(fragment.position + Vec3(random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1)) * 2, duration=random.uniform(0.3, 0.6), curve=curve.out_quad)
                    fragment.fade_out(duration=random.uniform(0.3, 0.6))
                    destroy(fragment, delay=0.6)
                flash_effect = Entity(model='sphere', color=color.yellow, scale=hit_entity.scale * 1.2, position=hit_entity.world_position)
                flash_effect.animate_scale(hit_entity.scale * 1.5, duration=0.1, curve=curve.out_quad)
                flash_effect.fade_out(duration=0.1)
                destroy(flash_effect, delay=0.1)
                destroy(hit_entity)
                invoke(spawn_next_target, delay=0.5)
            else:
                # Si no se acierta a un objetivo, suena el sonido de rebote.
                ricochet_sound.play()
            
            update_stats_display()

        # Se usa un pequeño retraso para que el sonido del arma y el del resultado no se pisen.
        invoke(play_result_sound, delay=0.05)

# --- Iniciar el Juego ---
pistol.disable()
rifle.disable()
shotgun.disable()
crosshair.disable()
stats_text.disable()
mouse.locked = False
app.run()
