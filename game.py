# pyrefly: ignore [missing-import]
import pygame
import time
import math
from config import *
from map_generator import MapGenerator
from entities import Pacman, Blinky, Pinky, Inky, Clyde
from graphics import Graphics
from pathfinding import manhattan_distance


import struct

class SoundSynth:
    @staticmethod
    def generate_eat_pellet():
        try:
            sample_rate = 22050
            duration = 0.08
            num_samples = int(sample_rate * duration)
            data = []
            for i in range(num_samples):
                t = i / sample_rate
                # Tang dan tan so tu 600Hz den 1200Hz
                freq = 600 + 600 * (t / duration)
                val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                envelope = 1.0 - (t / duration)
                sample = int(val * envelope * 0.1 * 32767)
                data.append(sample)
            return pygame.mixer.Sound(buffer=struct.pack(f'<{len(data)}h', *data))
        except Exception as e:
            print(f"Error generating eat pellet sound: {e}")
            return None

    @staticmethod
    def generate_eat_ghost():
        try:
            sample_rate = 22050
            duration = 0.3
            num_samples = int(sample_rate * duration)
            data = []
            import random
            for i in range(num_samples):
                t = i / sample_rate
                # Giam dan tan so tu 400Hz
                freq = 400 * (1.0 - (t / duration))
                wave = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                noise = random.uniform(-1.0, 1.0)
                val = 0.6 * wave + 0.4 * noise
                envelope = 1.0 - (t / duration)
                sample = int(val * envelope * 0.8 * 32767)
                data.append(sample)
            return pygame.mixer.Sound(buffer=struct.pack(f'<{len(data)}h', *data))
        except Exception as e:
            print(f"Error generating eat ghost sound: {e}")
            return None

    @staticmethod
    def generate_death():
        try:
            sample_rate = 22050
            duration = 0.8
            num_samples = int(sample_rate * duration)
            data = []
            for i in range(num_samples):
                t = i / sample_rate
                freq = 800 * (1.0 - (t / duration))
                # Them hieu ung rung
                freq += math.sin(2 * math.pi * 30 * t) * 50
                val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                envelope = 1.0 - (t / duration)
                sample = int(val * envelope * 0.2 * 32767)
                data.append(sample)
            return pygame.mixer.Sound(buffer=struct.pack(f'<{len(data)}h', *data))
        except Exception as e:
            print(f"Error generating death sound: {e}")
            return None

    @staticmethod
    def generate_victory():
        try:
            sample_rate = 22050
            notes = [523.25, 659.25, 784.00] # C5, E5, G5
            note_duration = 0.15
            num_samples_per_note = int(sample_rate * note_duration)
            data = []
            for freq in notes:
                for i in range(num_samples_per_note):
                    t = i / sample_rate
                    val = math.sin(2 * math.pi * freq * t)
                    envelope = 1.0 - (t / note_duration)
                    sample = int(val * envelope * 0.25 * 32767)
                    data.append(sample)
            return pygame.mixer.Sound(buffer=struct.pack(f'<{len(data)}h', *data))
        except Exception as e:
            print(f"Error generating victory sound: {e}")
            return None

    @staticmethod
    def generate_menu_music():
        try:
            sample_rate = 22050
            # Cac not nhac: A2 (110.0), C3 (130.81), E3 (164.81), G3 (196.0)
            bass_line = [110.0, 130.81, 164.81, 196.0]
            note_duration = 0.5
            num_samples_per_note = int(sample_rate * note_duration)
            data = []
            
            for note_idx, freq in enumerate(bass_line):
                for i in range(num_samples_per_note):
                    t = i / sample_rate
                    # Tron song tam giac/sine cho am bass tram am
                    sine_wave = math.sin(2 * math.pi * freq * t)
                    triangle_wave = 2.0 * abs(2.0 * (t * freq - math.floor(t * freq + 0.5))) - 1.0
                    val = 0.7 * sine_wave + 0.3 * triangle_wave
                    
                    # Them not rai tan so cao (vd hoa am thu 4)
                    arp_freq = freq * 4
                    arp_val = math.sin(2 * math.pi * arp_freq * t * 2)
                    val += arp_val * 0.08
                    
                    # Envelope cho moi not nhac de tao tieng ghep
                    envelope = math.exp(-3.0 * (t / note_duration))
                    sample = int(val * envelope * 0.15 * 32767)
                    data.append(sample)
            return pygame.mixer.Sound(buffer=struct.pack(f'<{len(data)}h', *data))
        except Exception as e:
            print(f"Error generating menu music: {e}")
            return None

    @staticmethod
    def generate_gameplay_music():
        try:
            sample_rate = 22050
            # 8 not moc don trong mot nhip nhanh: A3, C4, E4, G4, A4, G4, E4, C4
            melody = [220.00, 261.63, 329.63, 392.00, 440.00, 392.00, 329.63, 261.63]
            note_duration = 0.2
            num_samples_per_note = int(sample_rate * note_duration)
            data = []
            for freq in melody:
                for i in range(num_samples_per_note):
                    t = i / sample_rate
                    # Song vuong cho khong khi game co dien
                    val = 1.0 if math.sin(2 * math.pi * freq * t) >= 0 else -1.0
                    # Not nhac nen bass (subharmonic)
                    bass_val = math.sin(2 * math.pi * (freq / 2) * t)
                    val = 0.6 * val + 0.4 * bass_val
                    # Pluck envelope
                    envelope = math.exp(-4.0 * (t / note_duration))
                    sample = int(val * envelope * 0.06 * 32767)
                    data.append(sample)
            return pygame.mixer.Sound(buffer=struct.pack(f'<{len(data)}h', *data))
        except Exception as e:
            print(f"Error generating gameplay music: {e}")
            return None

    @staticmethod
    def generate_game_over():
        try:
            sample_rate = 22050
            # Hop am thu giam dan
            notes = [220.00, 207.65, 196.00, 185.00]
            note_duration = 0.25
            num_samples_per_note = int(sample_rate * note_duration)
            data = []
            for freq in notes:
                for i in range(num_samples_per_note):
                    t = i / sample_rate
                    val = math.sin(2 * math.pi * freq * t)
                    envelope = 1.0 - (t / note_duration)
                    sample = int(val * envelope * 0.25 * 32767)
                    data.append(sample)
            return pygame.mixer.Sound(buffer=struct.pack(f'<{len(data)}h', *data))
        except Exception as e:
            print(f"Error generating game over music: {e}")
            return None

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.state = STATE_MENU
        self.pending_end_state = None  # Se la STATE_GAME_OVER hoac STATE_VICTORY sau hieu ung
        self.complexity = 0.5
        self.paused = False
        
        self.grid = []
        self.cols = 0
        self.rows = 0
        self.tile_size = 0
        self.offset_x = 0
        self.offset_y = 0
        
        self.power_pellets = []
        
        self.pacman = None
        self.ghosts = []
        self.blinky = None
        
        self.power_mode_active = False
        self.power_start_time = 0
        
        self.waiting_for_pellet = False
        self.wait_start_time = 0
        
        self.start_time = 0
        self.game_time = 0.0
        self.speed_scale = 1.0
        self.steps = 0
        self.turns = 0
        
        self.screen_shake_time = 0.0
        self.screen_shake_intensity = 0
        self.pacman_trail = []
        self.dying = False
        self.dying_timer = 0.0
        self.ghosts_eaten = 0
        
        self.graphics = Graphics()
        
        self.sound_volume = 0.8
        self.current_music = None
        self._last_pacman_pos = None
        self._last_blinky_pos = None
        self._last_power_mode_active = None
        self._last_ghost_positions = ()
        
        # Bien soan hieu ung am thanh tong hop va vong lap am nhac
        menu_music_sound = None
        try:
            menu_music_sound = pygame.mixer.Sound("assets/waiting_screen_soundtrack.mp3")
        except Exception as e:
            print(f"Error loading custom menu soundtrack, falling back to synth: {e}")
            menu_music_sound = SoundSynth.generate_menu_music()

        # Tai nhac nen tu tep tin, dung ban tong hop neu loi
        game_music_sound = self._load_sound_file("assets/gameplay_music1.mp3")
        if game_music_sound is None:
            game_music_sound = SoundSynth.generate_gameplay_music()

        self.sounds = {
            'eat_pellet': SoundSynth.generate_eat_pellet(),
            'eat_ghost': SoundSynth.generate_eat_ghost(),
            'death': SoundSynth.generate_death(),
            'victory': self._load_sound_file("assets/winining_sound.wav") or SoundSynth.generate_victory(),
            'menu_music': menu_music_sound,
            'game_music': game_music_sound,
            'game_over': self._load_sound_file("assets/losing_sound.wav") or SoundSynth.generate_game_over(),
            'start_sound': self._load_sound_file("assets/start_sound.mp3"),
        }
        
        # Kenh nhac chuyen dung
        try:
            self.music_channel = pygame.mixer.Channel(0)
            self.music_channel.set_volume(0.5) # Nhac nen nen nho hon mot chut
        except Exception as e:
            self.music_channel = None
        
        # Khoi tao cac hat bui troi noi lam nen
        import random
        self.bg_particles = []
        for _ in range(120):
            self.bg_particles.append({
                'x': random.randint(0, width),
                'y': random.randint(0, height),
                'base_speed_y': random.uniform(-0.6, -1.5), # Troi nhanh hon
                'speed_x': random.uniform(-0.3, 0.3),       # Lac manh hon
                'radius': random.uniform(40, 90),           # Lon hon 5 lan! (tu 8-18 thanh 40-90)
                'opacity': random.randint(8, 25),           # Giam do mo (rat nhe, sang diu)
                'color': random.choice([
                    (0, 229, 255),    # Xanh lo
                    (255, 0, 85),     # Do
                    (255, 102, 204),  # Hong
                    (255, 235, 59)    # Vang
                ])
            })

    def _load_sound_file(self, path):
        try:
            return pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Error loading sound '{path}': {e}")
            return None

    def play_sound(self, name):
        sound = self.sounds.get(name)
        if sound:
            try:
                volume = getattr(self, 'sound_volume', 0.5)
                if name == 'victory':
                    # Tang am luong nhac chien thang vi am thanh goc kha nho
                    volume = min(2.0, volume * 4.0)
                sound.set_volume(volume)
                sound.play()
            except:
                pass

    def play_music(self, name):
        if self.music_channel:
            if getattr(self, 'current_music', None) == name:
                if self.music_channel.get_busy():
                    return
            sound = self.sounds.get(name)
            if sound:
                try:
                    self.music_channel.set_volume(getattr(self, 'sound_volume', 0.5) * 0.5)
                    self.music_channel.play(sound, loops=-1)
                    self.current_music = name
                except:
                    pass

    def stop_music(self):
        if self.music_channel:
            try:
                self.music_channel.stop()
                self.current_music = None
            except:
                pass

    def toggle_pause(self):
        self.paused = not self.paused
        if self.music_channel:
            if self.paused:
                try:
                    self.music_channel.pause()
                except:
                    pass
            else:
                try:
                    self.music_channel.unpause()
                except:
                    pass

    def start_game(self, complexity, map_size, mode, algorithms, pacman_heuristics=None):
        self.complexity = complexity
        self.map_size = map_size
        self.mode = mode
        self.state = STATE_PLAYING
        
        # Tao Ban Do
        self.grid, self.cols, self.rows = MapGenerator.generate_map(self.complexity, self.map_size)
        
        # Tinh toan ty le de vua man hinh (tru thanh ben va vung thanh truot toc do)
        available_w = self.width - SIDEBAR_WIDTH - 60
        max_tile_w = available_w // self.cols
        max_tile_h = self.height // self.rows
        self.tile_size = min(max_tile_w, max_tile_h)
        
        # Canh giua ban do trong vung choi (ben trai)
        self.offset_x = (available_w - (self.cols * self.tile_size)) // 2
        self.offset_y = (self.height - (self.rows * self.tile_size)) // 2
        self.paused = False
        
        self.power_pellets = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 2:
                    self.power_pellets.append((r, c))
                    self.grid[r][c] = 0 # Thay the bang duong di trong logic luoi
                    
        # Khoi tao cac thuc the
        center_r = self.rows // 2 if (self.rows // 2) % 2 != 0 else (self.rows // 2) + 1
        center_c = self.cols // 2 if (self.cols // 2) % 2 != 0 else (self.cols // 2) + 1
        self.pacman = Pacman(center_r, center_c)
        self.pacman.algo = "A*"
        if pacman_heuristics is not None:
            self.pacman.heuristic_formulas = pacman_heuristics.copy()
        self.pacman.last_dir = DIR_RIGHT
        self.pacman.align_to_grid(self.tile_size)
        
        # Chon ma xuat hien o 4 goc
        spawn_points = [
            (1, self.cols-2), # Goc Tren Ben Phai (Blinky)
            (1, 1),           # Goc Tren Ben Trai (Pinky)
            (self.rows-2, self.cols-2), # Goc Duoi Ben Phai (Inky)
            (self.rows-2, 1)  # Goc Duoi Ben Trai (Clyde)
        ]
        
        self.blinky = Blinky(spawn_points[0][0], spawn_points[0][1], self.rows, self.cols)
        pinky = Pinky(spawn_points[1][0], spawn_points[1][1], self.rows, self.cols)
        inky = Inky(spawn_points[2][0], spawn_points[2][1], self.rows, self.cols)
        clyde = Clyde(spawn_points[3][0], spawn_points[3][1], self.rows, self.cols)
        
        self.blinky.algo = algorithms["Blinky"]
        pinky.algo = algorithms["Pinky"]
        inky.algo = algorithms["Inky"]
        clyde.algo = algorithms["Clyde"]
        
        self.ghosts = [self.blinky, pinky, inky, clyde]
        for g in self.ghosts:
            g.align_to_grid(self.tile_size)
            
        self.power_mode_active = False
        self.waiting_for_pellet = False
        self.game_time = 0.0
        self.steps = 0
        self.turns = 0
        self.pacman_trail = []
        self.dying = False
        self.dying_timer = 0.0
        self.ghosts_eaten = 0

    def start_game_custom(self, grid, rows, cols, mode, algorithms, pacman_pos, ghost_positions, pacman_heuristics=None):
        # Bat dau tro choi bang ban do tuy chinh tu trinh bien tap ban do.
        self.complexity = 0.5
        self.map_size   = 0.5
        self.mode       = mode
        self.state      = STATE_PLAYING

        self.grid = [row[:] for row in grid]
        self.rows = rows
        self.cols = cols

        # Tinh toan ty le de vua man hinh (tru thanh ben va vung thanh truot toc do)
        available_w = self.width - SIDEBAR_WIDTH - 60
        max_tile_w  = available_w // self.cols
        max_tile_h  = self.height  // self.rows
        self.tile_size = min(max_tile_w, max_tile_h)

        # Canh giua ban do
        self.offset_x = (available_w - self.cols * self.tile_size) // 2
        self.offset_y = (self.height  - self.rows * self.tile_size) // 2
        self.paused   = False

        # Thu thap cac vien thuoc nang luong
        self.power_pellets = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 2:
                    self.power_pellets.append((r, c))
                    self.grid[r][c] = 0

        # Pacman
        pr, pc = pacman_pos
        self.pacman = Pacman(pr, pc)
        self.pacman.algo = "A*"
        if pacman_heuristics is not None:
            self.pacman.heuristic_formulas = pacman_heuristics.copy()
        self.pacman.last_dir = DIR_RIGHT
        self.pacman.align_to_grid(self.tile_size)

        # Cho ghost_positions luon du 4 phan tu (lap lai neu it hon)
        while len(ghost_positions) < 4:
            ghost_positions.append(ghost_positions[0])
        ghost_positions = ghost_positions[:4]

        self.blinky = Blinky(ghost_positions[0][0], ghost_positions[0][1], self.rows, self.cols)
        pinky  = Pinky (ghost_positions[1][0], ghost_positions[1][1], self.rows, self.cols)
        inky   = Inky  (ghost_positions[2][0], ghost_positions[2][1], self.rows, self.cols)
        clyde  = Clyde (ghost_positions[3][0], ghost_positions[3][1], self.rows, self.cols)

        self.blinky.algo = algorithms["Blinky"]
        pinky.algo       = algorithms["Pinky"]
        inky.algo        = algorithms["Inky"]
        clyde.algo       = algorithms["Clyde"]

        self.ghosts = [self.blinky, pinky, inky, clyde]
        for g in self.ghosts:
            g.align_to_grid(self.tile_size)

        self.power_mode_active  = False
        self.waiting_for_pellet = False
        self.game_time          = 0.0
        self.steps              = 0
        self.turns              = 0
        self.pacman_trail       = []
        self.dying              = False
        self.dying_timer        = 0.0
        self.ghosts_eaten       = 0

    def update(self, dt):
        if self.state != STATE_PLAYING or self.paused:
            self.graphics.update(dt)
            return

        self.game_time += dt

        if self.dying:
            self.dying_timer -= dt
            if self.dying_timer <= 0:
                self.dying = False
                self.state = STATE_END_ANIM
                self.pending_end_state = STATE_GAME_OVER
            if self.screen_shake_time > 0:
                self.screen_shake_time -= dt
                if self.screen_shake_time <= 0:
                    self.screen_shake_intensity = 0
            self.graphics.update(dt)
            return

        current_time = self.game_time
        power_time_left = 0
        
        # Quan ly Che do Suc manh
        if self.power_mode_active:
            power_time_left = POWER_MODE_DURATION - (current_time - self.power_start_time)
            if power_time_left <= 0:
                self.power_mode_active = False
                self.pacman.speed = SPEED_NORMAL
                for g in self.ghosts:
                    g.is_scared = False
            else:
                if power_time_left <= 1.0:
                    self.pacman.speed = SPEED_NORMAL
                else:
                    self.pacman.speed = SPEED_PACMAN_POWER
        else:
            self.pacman.speed = SPEED_NORMAL
        
        # Quan ly viec Tai sinh Thuoc nang luong
        if not self.power_pellets and any(not g.is_dead for g in self.ghosts):
            if not self.waiting_for_pellet:
                self.waiting_for_pellet = True
                self.wait_start_time = current_time
            elif current_time - self.wait_start_time >= PELLET_RESPAWN_TIME:
                if MapGenerator.spawn_power_pellet(self.grid, self.cols, self.rows):
                    # Tim vi tri xuat hien va them vao danh sach
                    for r in range(self.rows):
                        for c in range(self.cols):
                            if self.grid[r][c] == 2:
                                self.power_pellets.append((r, c))
                                self.grid[r][c] = 0
                self.waiting_for_pellet = False

        # Cap nhat AI cua thuc the
        entities = [self.pacman] + self.ghosts
        
        # Check tracking changes to minimize A* pathfinding calls
        pacman_pos = (self.pacman.r, self.pacman.c)
        blinky_pos = (self.blinky.r, self.blinky.c) if (self.blinky and not self.blinky.is_dead) else None
        
        pacman_pos_changed = (self._last_pacman_pos != pacman_pos)
        blinky_pos_changed = (self._last_blinky_pos != blinky_pos)
        power_mode_changed = (self._last_power_mode_active != self.power_mode_active)
        
        ghost_positions = tuple((g.r, g.c) for g in self.ghosts)
        ghosts_pos_changed = (self._last_ghost_positions != ghost_positions)
        
        self._last_pacman_pos = pacman_pos
        self._last_blinky_pos = blinky_pos
        self._last_power_mode_active = self.power_mode_active
        self._last_ghost_positions = ghost_positions
        
        # Check if any active ghost is close to Pacman to enable split-second evasion/chase updates
        ghost_is_close = False
        for g in self.ghosts:
            if not g.is_dead:
                if manhattan_distance(pacman_pos, (g.r, g.c)) < 5:
                    ghost_is_close = True
                    break
        
        for e in entities:
            need_update = (
                not e.is_moving or
                e.is_centered(self.tile_size) or
                not e.path or
                power_mode_changed
            )
            
            if not need_update:
                if e == self.pacman:
                    if self.mode != "Player vs AI":
                        if ghosts_pos_changed or ghost_is_close:
                            need_update = True
                else:
                    if pacman_pos_changed or blinky_pos_changed or e.is_scared:
                        need_update = True
                        
            if need_update:
                if e == self.pacman:
                    if self.mode != "Player vs AI":
                        self.pacman.update_ai(self.grid, self.rows, self.cols, self.power_pellets, self.ghosts, self.power_mode_active, power_time_left)
                else:
                    e.update_ai(self.grid, self.rows, self.cols, pacman_pos, self.pacman.dir, self.ghosts, blinky_pos)

        # Kiem tra quay dau 180 do lap tuc cho Pacman (ca che do choi bang tay va AI)
        if self.pacman.dir != DIR_NONE and not self.pacman.is_centered(self.tile_size):
            if self.mode == "Player vs AI":
                if self.pacman.next_dir == OPPOSITE_DIR[self.pacman.dir]:
                    if self.pacman.instant_180(self.pacman.next_dir):
                        self.pacman.next_dir = DIR_NONE
            else:
                if self.pacman.path:
                    next_node = self.pacman.path[0]
                    desired_dir = (next_node[1] - self.pacman.c, next_node[0] - self.pacman.r)
                    if desired_dir == OPPOSITE_DIR[self.pacman.dir]:
                        if self.pacman.instant_180(desired_dir):
                            self.pacman.path.pop(0)

        for e in entities:
            # Chi di chuyen va doi huong di khi thuc the dung im hoac can doi giua o vuong
            if not e.is_moving or e.is_centered(self.tile_size):
                if e == self.pacman:
                    if self.mode == "Player vs AI":
                        # Nguoi choi dieu khien thu cong
                        if self.pacman.next_dir != DIR_NONE and self.pacman.can_move(self.pacman.next_dir, self.grid, self.rows, self.cols):
                            self.pacman.dir = self.pacman.next_dir
                            self.pacman.is_moving = True
                        elif self.pacman.dir != DIR_NONE and self.pacman.can_move(self.pacman.dir, self.grid, self.rows, self.cols):
                            self.pacman.is_moving = True
                        else:
                            self.pacman.dir = DIR_NONE
                            self.pacman.is_moving = False
                    else:
                        # AI dieu khien
                        old_dir = self.pacman.dir
                        self.pacman.follow_path(self.grid, self.rows, self.cols)
                        if self.pacman.dir != old_dir and self.pacman.dir != DIR_NONE:
                            self.turns += 1
                else:
                    e.follow_path(self.grid, self.rows, self.cols)
                    
            old_r, old_c = e.r, e.c
            e.move(self.tile_size)
            if e.dir != DIR_NONE:
                if e == self.pacman:
                    self.pacman.last_dir = e.dir
                    if e.r != old_r or e.c != old_c:
                        self.steps += 1

        # Kiem tra va cham
        pac_rect = pygame.Rect(self.pacman.pixel_x, self.pacman.pixel_y, self.tile_size, self.tile_size)
        
        # Va cham voi vien thuoc
        for p in self.power_pellets[:]:
            p_rect = pygame.Rect(p[1]*self.tile_size, p[0]*self.tile_size, self.tile_size, self.tile_size)
            if pac_rect.colliderect(p_rect):
                self.power_pellets.remove(p)
                self.power_mode_active = True
                self.power_start_time = current_time
                self.play_sound('eat_pellet')
                # Hieu ung chop man hinh (Manh liet!)
                self.graphics.particles.emit(self.pacman.pixel_x + self.tile_size//2, self.pacman.pixel_y + self.tile_size//2, (0, 255, 255), count=60, speed_range=(3, 10), size_range=(3, 6), lifetime_range=(0.3, 0.6))
                self.screen_shake_time = 0.2
                self.screen_shake_intensity = 6
                for g in self.ghosts:
                    if not g.is_dead:
                        g.is_scared = True
                        g.allowed_180 = True

        # Va cham voi con ma
        all_dead = True
        for g in self.ghosts:
            if g.is_dead:
                continue
            all_dead = False
            g_rect = pygame.Rect(g.pixel_x, g.pixel_y, self.tile_size, self.tile_size)
            if pac_rect.colliderect(g_rect):
                if self.power_mode_active and g.is_scared:
                    g.is_dead = True
                    self.ghosts_eaten += 1
                    self.play_sound('eat_ghost')
                    # Hieu ung chet (Manh liet!)
                    self.graphics.particles.emit(g.pixel_x + self.tile_size//2, g.pixel_y + self.tile_size//2, g.color, count=120, speed_range=(4, 15), size_range=(4, 8), lifetime_range=(0.4, 0.8))
                    self.screen_shake_time = 0.4
                    self.screen_shake_intensity = 15
                else:
                    self.dying = True
                    self.dying_timer = 1.5
                    self.stop_music()
                    self.play_music('game_over')
                    self.play_sound('death')
                    # Vay no LON!
                    self.graphics.particles.emit(
                        self.pacman.pixel_x + self.tile_size//2,
                        self.pacman.pixel_y + self.tile_size//2,
                        PACMAN_COLOR,
                        count=300,
                        speed_range=(4, 25),
                        size_range=(5, 12),
                        lifetime_range=(0.6, 1.5)
                    )
                    self.screen_shake_time = 1.5
                    self.screen_shake_intensity = 25
                    return

        if all_dead and self.state not in (STATE_VICTORY, STATE_END_ANIM):
            self.state = STATE_END_ANIM
            self.pending_end_state = STATE_VICTORY
            # Dung moi rung dong con lai de hieu ung ket thuc duoc dep
            self.screen_shake_time = 0.0
            self.screen_shake_intensity = 0
            self.stop_music()
            self.play_sound('victory')
            
        if self.power_mode_active and self.pacman.speed == SPEED_PACMAN_POWER:
            # Phat ra cac tia lua chay them tu Pacman
            pulse = (math.sin(time.time() * 10) + 1) / 2
            spark_color = (255, 60 + int(100 * pulse), 0)
            self.graphics.particles.emit(
                self.pacman.pixel_x + self.tile_size//2, 
                self.pacman.pixel_y + self.tile_size//2, 
                spark_color, 
                count=2, 
                speed_range=(2, 6), 
                size_range=(2, 5), 
                lifetime_range=(0.2, 0.5)
            )
            self.graphics.particles.emit(self.pacman.pixel_x + self.tile_size//2, self.pacman.pixel_y + self.tile_size//2, PACMAN_COLOR, count=1, speed_range=(1, 3), size_range=(2, 4), lifetime_range=(0.1, 0.3))
            
            p_dir = self.pacman.dir
            if p_dir == DIR_NONE:
                p_dir = getattr(self.pacman, 'last_dir', DIR_RIGHT)
            base_angle = 0
            if p_dir == DIR_UP: base_angle = math.pi / 2
            elif p_dir == DIR_DOWN: base_angle = -math.pi / 2
            elif p_dir == DIR_LEFT: base_angle = math.pi
            elif p_dir == DIR_RIGHT: base_angle = 0
            
            mouth_angle = (math.sin(time.time() * 15) + 1) / 2 * math.pi / 4
            
            self.pacman_trail.append((self.pacman.pixel_x, self.pacman.pixel_y, mouth_angle, base_angle))
            if len(self.pacman_trail) > 15:
                self.pacman_trail.pop(0)
        else:
            self.pacman_trail = []

        # Phat ra cac tia lua xanh/tim tu cac con ma bi hoang so
        if self.power_mode_active:
            for g in self.ghosts:
                if not g.is_dead and g.is_scared:
                    self.graphics.particles.emit(
                        g.pixel_x + self.tile_size//2,
                        g.pixel_y + self.tile_size//2,
                        (0, 100, 255),
                        count=1,
                        speed_range=(1, 3),
                        size_range=(2, 4),
                        lifetime_range=(0.2, 0.4)
                    )
            
        if self.screen_shake_time > 0:
            self.screen_shake_time -= dt
            if self.screen_shake_time <= 0:
                self.screen_shake_intensity = 0
                
        self.graphics.update(dt)

    def draw(self, surface, time_passed):
        if self.power_mode_active:
            # Mau nen tim/hong sam nhe trong che do suc manh
            surface.fill((16, 12, 20))
        else:
            surface.fill(BG_COLOR)
            
        # Ve luoi co dien di chuyen trong nen (nhe, toi, di chuyen cham)
        grid_spacing = 60
        offset_x = int(time_passed * 3) % grid_spacing
        offset_y = int(time_passed * 3) % grid_spacing
        
        grid_line_color = (16, 18, 24)
        if self.power_mode_active:
            pulse = (math.sin(time_passed * 8) + 1) / 2
            grid_line_color = (int(16 + 8 * pulse), 14, 18)
            
        gameplay_width = self.width - SIDEBAR_WIDTH
        for x in range(-grid_spacing, gameplay_width + grid_spacing, grid_spacing):
            pygame.draw.line(surface, grid_line_color, (x + offset_x, 0), (x + offset_x, self.height), 1)
        for y in range(-grid_spacing, self.height + grid_spacing, grid_spacing):
            pygame.draw.line(surface, grid_line_color, (0, y + offset_y), (gameplay_width, y + offset_y), 1)
            
        # Cap nhat va ve cac hat bui troi noi o nen (chi trong chieu rong vung choi)
        import random
        for p in self.bg_particles:
            if not self.paused:
                # Slower speed multiplier for a more subtle look
                speed_multiplier = 1.5 if self.power_mode_active else 1.0
                p['y'] += p['base_speed_y'] * speed_multiplier
                p['x'] += p['speed_x'] * speed_multiplier
                if p['y'] < 0:
                     p['y'] = self.height
                     p['x'] = random.randint(0, gameplay_width)
                if p['x'] < 0:
                     p['x'] = gameplay_width
                elif p['x'] > gameplay_width:
                     p['x'] = 0
            
            if p['x'] < gameplay_width:
                opacity = p['opacity']
                color = p['color']
                radius = p['radius']
                
                if self.power_mode_active:
                    # Kich thuoc xung nhe
                    pulse = (math.sin(time_passed * 8 + p['x']) + 1) / 2
                    radius = p['radius'] * (1.0 + 0.15 * pulse)
                    # Mau neon tim/hong sam diu
                    color = (180, 50, 220)
                    opacity = min(255, p['opacity'] + 15)
                    
                s = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
                pygame.draw.circle(s, (*color[:3], opacity), (int(radius), int(radius)), int(radius))
                surface.blit(s, (int(p['x'] - radius), int(p['y'] - radius)))
        
        # Tao subsurface cho luoi de de dang xu ly cac do lech
        grid_surface = pygame.Surface((self.cols * self.tile_size, self.rows * self.tile_size), pygame.SRCALPHA)
        
        # Ve Ban Do
        wall_color = None
        if self.power_mode_active:
            # Mau neon tim/hong sam dep cho ve ngoai cong nghe cao diu
            wall_color = (255, 0, 128)

        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 1:
                    Graphics.draw_neon_wall(grid_surface, c*self.tile_size, r*self.tile_size, self.tile_size, self.tile_size, color=wall_color)

        # Ve cac Duong bong mo
        if not self.dying:
            path_to_draw = self.pacman.path
            if self.pacman.is_moving and self.pacman.dir != DIR_NONE:
                next_cell = (self.pacman.r + self.pacman.dir[1], self.pacman.c + self.pacman.dir[0])
                if not path_to_draw or path_to_draw[0] != next_cell:
                    path_to_draw = [next_cell] + list(path_to_draw)
            Graphics.draw_dashed_path(grid_surface, path_to_draw, (self.pacman.pixel_x + self.tile_size//2, self.pacman.pixel_y + self.tile_size//2), PACMAN_COLOR, self.tile_size)
        for g in self.ghosts:
            if not g.is_dead:
                 path_to_draw = g.path
                 if g.is_moving and g.dir != DIR_NONE:
                     next_cell = (g.r + g.dir[1], g.c + g.dir[0])
                     if not path_to_draw or path_to_draw[0] != next_cell:
                         path_to_draw = [next_cell] + list(path_to_draw)
                 Graphics.draw_dashed_path(grid_surface, path_to_draw, (g.pixel_x + self.tile_size//2, g.pixel_y + self.tile_size//2), g.color if not g.is_scared else GHOST_SCARED_COLOR, self.tile_size)

        # Ve cac Vien thuoc
        for r, c in self.power_pellets:
            Graphics.draw_power_pellet(grid_surface, c*self.tile_size, r*self.tile_size, self.tile_size, time_passed)

        # Ve Vet duong di cua Pacman
        if not self.dying and self.power_mode_active and self.pacman_trail:
            for idx, (tx, ty, t_mouth_angle, t_base_angle) in enumerate(self.pacman_trail):
                alpha = int((idx + 1) / len(self.pacman_trail) * 120)
                shadow_color = (255, 235, 59, alpha)
                t_center_x = tx + self.tile_size // 2
                t_center_y = ty + self.tile_size // 2
                t_radius = int(self.tile_size * 0.4)
                t_points = [(t_center_x, t_center_y)]
                for angle in range(int(math.degrees(t_mouth_angle)), int(math.degrees(2 * math.pi - t_mouth_angle)), 15):
                    rad = math.radians(angle) + t_base_angle
                    x = t_center_x + t_radius * math.cos(rad)
                    y = t_center_y - t_radius * math.sin(rad)
                    t_points.append((x, y))
                if len(t_points) > 2:
                    pygame.draw.polygon(grid_surface, shadow_color, t_points)

        # Ve Pacman
        if not self.dying:
            p_color = PACMAN_AURA_COLOR if self.power_mode_active else self.pacman.color
            center_x = self.pacman.pixel_x + self.tile_size // 2
            center_y = self.pacman.pixel_y + self.tile_size // 2
            radius = int(self.tile_size * 0.4)
            
            # Goc chuyen dong cua mieng
            mouth_angle = (math.sin(time.time() * 15) + 1) / 2 * math.pi / 4  # 0 to 45 degrees
            
            # Xac dinh huong xoay co ban dua tren huong di
            p_dir = self.pacman.dir
            if p_dir == DIR_NONE:
                p_dir = getattr(self.pacman, 'last_dir', DIR_RIGHT)
                
            base_angle = 0
            if p_dir == DIR_UP: base_angle = math.pi / 2
            elif p_dir == DIR_DOWN: base_angle = -math.pi / 2
            elif p_dir == DIR_LEFT: base_angle = math.pi
            elif p_dir == DIR_RIGHT: base_angle = 0
            
            points = [(center_x, center_y)]
            for angle in range(int(math.degrees(mouth_angle)), int(math.degrees(2 * math.pi - mouth_angle)), 15):
                rad = math.radians(angle) + base_angle
                x = center_x + radius * math.cos(rad)
                y = center_y - radius * math.sin(rad)
                points.append((x, y))
            if len(points) > 2:
                pygame.draw.polygon(grid_surface, p_color, points)
        
        # Ve cac Con Ma
        for g in self.ghosts:
            if g.is_dead:
                continue
            
            color = g.color
            if g.is_scared:
                color = GHOST_SCARED_COLOR
                # Nhap nhay neu sap het thoi gian
                if self.power_mode_active and (self.game_time - self.power_start_time) > POWER_MODE_DURATION - 2.0:
                    if int(self.game_time * 10) % 2 == 0:
                        color = (255, 255, 255)
                        
            gx = g.pixel_x
            gy = g.pixel_y
            ts = self.tile_size
            
            # Ve Than Con Ma
            body_rect = pygame.Rect(gx, gy, ts, ts - ts // 4)
            pygame.draw.rect(grid_surface, color, body_rect, border_top_left_radius=ts//2, border_top_right_radius=ts//2)
            
            # Ve Duoi Con Ma
            skirt_points = []
            skirt_points.append((gx, gy + ts - ts // 4))
            num_waves = 3
            wave_width = ts / num_waves
            for i in range(num_waves):
                # Duong cong phia duoi
                skirt_points.append((gx + i * wave_width + wave_width / 2, gy + ts))
                skirt_points.append((gx + (i + 1) * wave_width, gy + ts - ts // 4))
            pygame.draw.polygon(grid_surface, color, skirt_points)
            
            # Ve Mat
            if g.is_scared:
                pygame.draw.line(grid_surface, (255,255,255), (gx + ts//4, gy + ts//4), (gx + ts//2.5, gy + ts//2.5), 2)
                pygame.draw.line(grid_surface, (255,255,255), (gx + ts//2.5, gy + ts//4), (gx + ts//4, gy + ts//2.5), 2)
                # con mat con lai
                pygame.draw.line(grid_surface, (255,255,255), (gx + ts - ts//2.5, gy + ts//4), (gx + ts - ts//4, gy + ts//2.5), 2)
                pygame.draw.line(grid_surface, (255,255,255), (gx + ts - ts//4, gy + ts//4), (gx + ts - ts//2.5, gy + ts//2.5), 2)
            else:
                # Long trang cua mat
                pygame.draw.circle(grid_surface, (255, 255, 255), (int(gx + ts * 0.3), int(gy + ts * 0.35)), int(ts * 0.15))
                pygame.draw.circle(grid_surface, (255, 255, 255), (int(gx + ts * 0.7), int(gy + ts * 0.35)), int(ts * 0.15))
                # Con nguoi (nhin theo huong di chuyen)
                px_offset = g.dir[0] * ts * 0.05 if g.dir != DIR_NONE else 0
                py_offset = g.dir[1] * ts * 0.05 if g.dir != DIR_NONE else 0
                pygame.draw.circle(grid_surface, (0, 0, 255), (int(gx + ts * 0.3 + px_offset), int(gy + ts * 0.35 + py_offset)), int(ts * 0.07))
                pygame.draw.circle(grid_surface, (0, 0, 255), (int(gx + ts * 0.7 + px_offset), int(gy + ts * 0.35 + py_offset)), int(ts * 0.07))

        self.graphics.draw(grid_surface)
        
        # Ap dung do lech rung man hinh (dem nguoc o day de no hoat dong o moi trang thai)
        shake_x, shake_y = 0, 0
        if self.screen_shake_time > 0:
            import random
            self.screen_shake_time = max(0.0, self.screen_shake_time - (1 / 60.0))
            if self.screen_shake_time <= 0:
                self.screen_shake_intensity = 0
            else:
                shake_x = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)
                shake_y = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)
            
        # Blit luoi len man hinh chinh
        surface.blit(grid_surface, (self.offset_x + shake_x, self.offset_y + shake_y))

        # Ve mot duong vien neon nhe quanh vung ban do choi khi che do suc manh duoc kich hoat
        if self.power_mode_active:
            border_rect = pygame.Rect(self.offset_x - 4, self.offset_y - 4, self.cols * self.tile_size + 8, self.rows * self.tile_size + 8)
            pygame.draw.rect(surface, (255, 0, 128), border_rect, 2)

    def get_time_str(self):
        t = int(self.game_time)
        return f"{t//60:02d}:{t%60:02d}"

    def get_elapsed_seconds(self):
        return self.game_time
