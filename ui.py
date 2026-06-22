# pyrefly: ignore [missing-import]
import pygame
import math
import random
from config import *
from custom_maps import load_custom_maps, delete_custom_map

class UI:
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        self.scale = max(0.5, min(self.width / 1920.0, self.height / 1080.0))
        pygame.font.init()
        
        # Thu tai phont chu pixel tuy chinh, quay lai phont chu he thong co dien
        font_path = "assets/PressStart2P-Regular.ttf"
        try:
            self.font_title = pygame.font.Font(font_path, int(140 * self.scale))
            self.font_large = pygame.font.Font(font_path, int(80 * self.scale))
            self.font_med = pygame.font.Font(font_path, int(28 * self.scale))
            self.font_small = pygame.font.Font(font_path, int(18 * self.scale))
            self.font_sidebar = pygame.font.Font(font_path, max(10, int(13 * self.scale)))
            self.using_pixel_font = True
        except Exception as e:
            fonts = pygame.font.get_fonts()
            retro_fonts = ["joystix", "impact", "pressstart2p", "courier", "consolas", "lucidaconsole", "monaco"]
            chosen_font = "Courier"
            for rf in retro_fonts:
                if rf in fonts:
                    chosen_font = rf
                    break
            self.font_title = pygame.font.SysFont(chosen_font, int(200 * self.scale), bold=True)
            self.font_large = pygame.font.SysFont(chosen_font, int(120 * self.scale), bold=True)
            self.font_med = pygame.font.SysFont(chosen_font, int(42 * self.scale), bold=True)
            self.font_small = pygame.font.SysFont(chosen_font, int(28 * self.scale), bold=True)
            self.font_sidebar = pygame.font.SysFont(chosen_font, max(14, int(20 * self.scale)), bold=True)
            self.using_pixel_font = False
        
        # Trang thai menu
        self.complexity = 0.5
        self.map_size = 0.5
        self.dragging_slider = None
        self.mode = "AI vs AI"
        self.selected_map_idx = 0
        self.custom_maps = []
        self.hovered_btn = None
        self.hovered_sidebar_btn = None
        self.menu_view = "main"
        
        try:
            self.font_guide = pygame.font.SysFont("Arial", max(11, int(15 * self.scale)))
        except Exception as e:
            self.font_guide = pygame.font.SysFont("Courier", max(10, int(13 * self.scale)), bold=True)
            
        # Tai anh nen
        self.bg_image = None
        try:
            raw_img = pygame.image.load("assets/waiting_screen_imamge.webp")
            self.bg_image = pygame.transform.scale(raw_img, (self.width, self.height))
        except Exception as e:
            print(f"Error loading background image: {e}")
        self.algorithms = {
            "Pacman": "A*",
            "Blinky": "A*",
            "Pinky": "Greedy",
            "Inky": "DFS",
            "Clyde": "BFS"
        }
        self.pacman_heuristics = {
            1: "d + sum(50.0 / max(0.5, gd) for gd in ghosts if gd < 4)",
            2: "d",
            3: "-g if g != 999 else d"
        }
        self.default_heuristics = {
            1: "d + sum(50.0 / max(0.5, gd) for gd in ghosts if gd < 4)",
            2: "d",
            3: "-g if g != 999 else d"
        }
        self.focused_heuristic_idx = None
        self.sound_volume = 0.8
        self.heuristic_cursor_indices = {
            1: len(self.pacman_heuristics[1]),
            2: len(self.pacman_heuristics[2]),
            3: len(self.pacman_heuristics[3])
        }
        self.heuristic_scrolls = {1: 0, 2: 0, 3: 0}
        
        # Nhom sao cho hoat anh nen (Parallax 3 lop)
        import random
        self.stars = []
        for _ in range(2000):
            layer = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
            if layer == 1:
                size = random.randint(1, 2)
                speed = random.uniform(0.2, 0.5)
                opacity = 100
            elif layer == 2:
                size = random.randint(3, 4)
                speed = random.uniform(0.7, 1.2)
                opacity = 180
            else:
                size = random.randint(5, 6)
                speed = random.uniform(1.6, 2.5)
                opacity = 255
                
            color = random.choice([
                (0, 229, 255),    # Xanh lam
                (255, 0, 85),     # Do
                (255, 102, 204),  # Hong
                (255, 235, 59)    # Vang
            ])
            # Ap dung he so do duc vao mau sac
            color_with_alpha = (int(color[0] * opacity / 255), int(color[1] * opacity / 255), int(color[2] * opacity / 255))
            
            self.stars.append({
                'x': random.randint(0, screen_width),
                'y': random.randint(0, screen_height),
                'speed': speed,
                'size': size,
                'color': color_with_alpha,
                'layer': layer
            })
            
        self.scanline_y = 0
        
        # Trang thai ket thuc
        self.stats = {}
        self.current_rank = None
        self.current_score = None
        self.total_leaderboard_entries = 0
        
        # Cac hat confetti/manh vo khoi tao san cho hoat anh ket thuc (dat lai moi khi ket thuc game)
        self._end_particles = []
        self._bg_particles = []
        self._end_anim_seeded = False

    def draw_neon_text(self, surface, text, font, color, center_pos, glow_radius=10, pulse=1.0):
        # Chu co ban
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=center_pos)
        
        # Anh sang neon
        glow_color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))
        max_glow = int(glow_radius * pulse)
        for i in range(max_glow, 0, -2):
            glow_surf = font.render(text, True, glow_color)
            try:
                glow_surf.set_alpha(int(200 / max_glow) if max_glow > 0 else 0)
            except Exception:
                pass
            surface.blit(glow_surf, (text_rect.x - i//2, text_rect.y - i//2))
            
        surface.blit(text_surf, text_rect)
        return text_rect

    def draw_pixel_sprite(self, surface, x, y, grid, pixel_size, primary_color):
        for r_idx, row in enumerate(grid):
            for c_idx, val in enumerate(row):
                if val == 0:
                    continue
                color = primary_color
                if val == 2:
                    color = (255, 255, 255)
                elif val == 3:
                    color = (0, 0, 255)
                pygame.draw.rect(surface, color, (x + c_idx * pixel_size, y + r_idx * pixel_size, pixel_size, pixel_size))

    def draw_pixel_banner(self, surface, center_pos, size, pulse):
        # Can thoi gian hien tai de thuc hien cac hoat anh
        time_passed = pygame.time.get_ticks() / 1000.0

        w, h = size
        cx, cy = center_pos
        
        # 0. Thu phong bang danh hieu theo nhip tho (bang danh hieu co gian dong bo voi chu)
        scale_factor = 1.0 + pulse * 0.08
        pad_x = int(90 * scale_factor)
        pad_y = int(35 * scale_factor)
        rect_w = w + pad_x * 2
        rect_h = h + pad_y * 2
        rect_x = cx - rect_w // 2
        rect_y = cy - rect_h // 2
        
        # 1. Dinh nghia cac diem cua tam cong nghe mecha ngoai (da giac cyberpunk phuc tap 24 canh voi cac vet lom o ben/tren)
        c_size = 24
        outer_pts = [
            (rect_x + c_size, rect_y),
            (rect_x + rect_w//2 - 120, rect_y),
            (rect_x + rect_w//2 - 100, rect_y + 12),
            (rect_x + rect_w//2 + 100, rect_y + 12),
            (rect_x + rect_w//2 + 120, rect_y),
            (rect_x + rect_w - c_size, rect_y),
            
            (rect_x + rect_w, rect_y + c_size),
            (rect_x + rect_w, cy - 30),
            (rect_x + rect_w - 24, cy - 15),
            (rect_x + rect_w - 24, cy + 15),
            (rect_x + rect_w, cy + 30),
            (rect_x + rect_w, rect_y + rect_h - c_size),
            
            (rect_x + rect_w - c_size, rect_y + rect_h),
            (rect_x + rect_w//2 + 120, rect_y + rect_h),
            (rect_x + rect_w//2 + 100, rect_y + rect_h - 12),
            (rect_x + rect_w//2 - 100, rect_y + rect_h - 12),
            (rect_x + rect_w//2 - 120, rect_y + rect_h),
            (rect_x + c_size, rect_y + rect_h),
            
            (rect_x, rect_y + rect_h - c_size),
            (rect_x, cy + 30),
            (rect_x + 24, cy + 15),
            (rect_x + 24, cy - 15),
            (rect_x, cy - 30),
            (rect_x, rect_y + c_size)
        ]

        # 2. Khoi nen toi voi do trong suot (Da giac mecha phuc tap)
        bg_pts = [(p[0] - rect_x, p[1] - rect_y) for p in outer_pts]
        banner_bg = pygame.Surface((rect_w, rect_h), pygame.SRCALPHA)
        pygame.draw.polygon(banner_bg, (10, 12, 18, 235), bg_pts)
        surface.blit(banner_bg, (rect_x, rect_y))
        
        # Mau sac
        color_cyan = (0, 229, 255)
        color_pink = (255, 102, 204)
        
        # 3. Ve vien ngoai mau xanh lam va hinh bat giac phan bu trong mau hong
        border_thickness = 6
        pygame.draw.polygon(surface, color_cyan, outer_pts, border_thickness)
        
        m = 10
        inner_c_size = c_size - 6
        inner_pts = [
            (rect_x + m + inner_c_size, rect_y + m),
            (rect_x + rect_w - m - inner_c_size, rect_y + m),
            (rect_x + rect_w - m, rect_y + m + inner_c_size),
            (rect_x + rect_w - m, rect_y + rect_h - m - inner_c_size),
            (rect_x + rect_w - m - inner_c_size, rect_y + rect_h - m),
            (rect_x + m + inner_c_size, rect_y + rect_h - m),
            (rect_x + m, rect_y + rect_h - m - inner_c_size),
            (rect_x + m, rect_y + m + inner_c_size)
        ]
        pygame.draw.polygon(surface, color_pink, inner_pts, border_thickness - 3)
        
        # 4. Cac duong mach in (duoc ve ben trong bang danh hieu)
        trace_color = (0, 180, 210) # xanh lam hoi toi hon mot chut
        # Duong mach phia tren ben trai
        pygame.draw.line(surface, trace_color, (rect_x + 50, rect_y + 35), (rect_x + 100, rect_y + 35), 2)
        pygame.draw.line(surface, trace_color, (rect_x + 100, rect_y + 35), (rect_x + 125, rect_y + 60), 2)
        pygame.draw.circle(surface, color_cyan, (rect_x + 125, rect_y + 60), 4)

        # Duong mach phia duoi ben trai
        pygame.draw.line(surface, trace_color, (rect_x + 50, rect_y + rect_h - 35), (rect_x + 100, rect_y + rect_h - 35), 2)
        pygame.draw.line(surface, trace_color, (rect_x + 100, rect_y + rect_h - 35), (rect_x + 125, rect_y + rect_h - 60), 2)
        pygame.draw.circle(surface, color_cyan, (rect_x + 125, rect_y + rect_h - 60), 4)

        # Duong mach phia tren ben phai
        pygame.draw.line(surface, trace_color, (rect_x + rect_w - 50, rect_y + 35), (rect_x + rect_w - 100, rect_y + 35), 2)
        pygame.draw.line(surface, trace_color, (rect_x + rect_w - 100, rect_y + 35), (rect_x + rect_w - 125, rect_y + 60), 2)
        pygame.draw.circle(surface, color_cyan, (rect_x + rect_w - 125, rect_y + 60), 4)

        # Duong mach phia duoi ben phai
        pygame.draw.line(surface, trace_color, (rect_x + rect_w - 50, rect_y + rect_h - 35), (rect_x + rect_w - 100, rect_y + rect_h - 35), 2)
        pygame.draw.line(surface, trace_color, (rect_x + rect_w - 100, rect_y + rect_h - 35), (rect_x + rect_w - 125, rect_y + rect_h - 60), 2)
        pygame.draw.circle(surface, color_cyan, (rect_x + rect_w - 125, rect_y + rect_h - 60), 4)

        # 5. Khung do duong ray goc noi cyber
        rail_len = 30
        rail_gap = 16
        # Ray goc tren ben trai
        pygame.draw.lines(surface, color_pink, False, [
            (rect_x - rail_gap, rect_y + rail_len),
            (rect_x - rail_gap, rect_y - rail_gap),
            (rect_x + rail_len, rect_y - rail_gap)
        ], 3)
        # Tren ben phai
        pygame.draw.lines(surface, color_pink, False, [
            (rect_x + rect_w + rail_gap, rect_y + rail_len),
            (rect_x + rect_w + rail_gap, rect_y - rail_gap),
            (rect_x + rect_w - rail_len, rect_y - rail_gap)
        ], 3)
        # Duoi ben trai
        pygame.draw.lines(surface, color_pink, False, [
            (rect_x - rail_gap, rect_y + rect_h - rail_len),
            (rect_x - rail_gap, rect_y + rect_h + rail_gap),
            (rect_x + rail_len, rect_y + rect_h + rail_gap)
        ], 3)
        # Duoi ben phai
        pygame.draw.lines(surface, color_pink, False, [
            (rect_x + rect_w + rail_gap, rect_y + rect_h - rail_len),
            (rect_x + rect_w + rail_gap, rect_y + rect_h + rail_gap),
            (rect_x + rect_w - rail_len, rect_y + rect_h + rail_gap)
        ], 3)

        # (Cac tab cyber o tren va duoi bang danh hieu da bi loai bo)
        
        # 6.5 Diem nhan vet khia tam vat goc
        tab_sz = 12
        for tx, ty in [
            (rect_x + c_size//2, rect_y + c_size//2),
            (rect_x + rect_w - c_size//2, rect_y + c_size//2),
            (rect_x + rect_w - c_size//2, rect_y + rect_h - c_size//2),
            (rect_x + c_size//2, rect_y + rect_h - c_size//2)
        ]:
            pygame.draw.rect(surface, color_pink, (tx - tab_sz//2, ty - tab_sz//2, tab_sz, tab_sz))
            pygame.draw.rect(surface, color_cyan, (tx - tab_sz//4, ty - tab_sz//4, tab_sz//2, tab_sz//2))

        # 4. Cac sprite Pixel-art hoat hoa (kich thuoc = 8 moi khoi, tong cong 104x104px!)
        sprite_size = 13 * 8
        
        # Hoat anh mieng Pacman ngoam
        pacman_open = [
            [0,0,0,0,1,1,1,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1,1,1,0,0,0],
            [1,1,1,1,1,1,1,1,0,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,0,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,0,0,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,1,1,1,1,1,0,0],
            [0,0,0,0,1,1,1,1,1,0,0,0,0]
        ]
        
        pacman_closed = [
            [0,0,0,0,1,1,1,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,0],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [0,1,1,1,1,1,1,1,1,1,1,1,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,0],
            [0,0,1,1,1,1,1,1,1,1,1,0,0],
            [0,0,0,0,1,1,1,1,1,0,0,0,0]
        ]
        
        pacman_pixels = pacman_open if (int(time_passed * 10) % 2 == 0) else pacman_closed
        
        # Hoat anh mat ma liac
        eye_look_left = (int(time_passed) % 4 < 2)
        
        ghost_pixels = [
            [0,0,0,0,1,1,1,1,1,0,0,0,0],
            [0,0,1,1,1,1,1,1,1,1,1,0,0],
            [0,1,1,1,1,1,1,1,1,1,1,1,0],
            [1,1,2,2,1,1,1,2,2,1,1,1,1] if eye_look_left else [1,1,1,2,2,1,1,1,2,2,1,1,1],
            [1,3,2,2,1,1,3,2,2,1,1,1,1] if eye_look_left else [1,1,3,2,2,1,1,3,2,2,1,1,1],
            [1,3,3,1,1,1,3,3,1,1,1,1,1] if eye_look_left else [1,1,1,3,3,1,1,1,3,3,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,1,0,1,1,1,0,1,1,1,0,1,1],
            [1,0,0,0,1,0,0,0,1,0,0,0,1]
        ]

        # Hoat anh song nhap nho nguoc nhau cho Pacman va Ma
        pacman_wave = math.sin(time_passed * 5) * 16
        ghost_wave = math.sin(time_passed * 5 + math.pi) * 16
        
        # Vi tri Pacman (nhap nho len/duoi + lac nhe sang trai/phai)
        pacman_sway = math.cos(time_passed * 3) * 8
        pacman_x = rect_x - sprite_size - 130 + pacman_sway
        pacman_y = cy - sprite_size // 2 + pacman_wave
        
        # Vi tri Ma (nhap nho len/duoi nguoc voi Pacman)
        ghost_x = rect_x + rect_w + 130
        ghost_y = cy - sprite_size // 2 + ghost_wave

        # 5. Hieu ung dong hat tia lua ban ra tu vien bang danh hieu ra ngoai
        for i in range(16):
            speed = 50 + (i % 4) * 40
            angle = (i % 3 - 1) * 0.15
            t = (time_passed + i * 0.2) % 1.5
            dist = t * speed
            
            # Tia lua ben trai (ban sang trai)
            px1 = rect_x - dist - 10
            py1 = cy + angle * dist + math.sin(time_passed * 12 + i) * 12
            
            # Tia lua ben phai (ban sang phai)
            px2 = rect_x + rect_w + dist + 10
            py2 = cy + angle * dist + math.sin(time_passed * 12 + i) * 12
            
            alpha = int(255 * (1.0 - t / 1.5))
            spark_color = (0, 229, 255) if i % 2 == 0 else (255, 102, 204)
            spark_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
            spark_surf.fill((*spark_color, alpha))
            surface.blit(spark_surf, (px1, py1))
            surface.blit(spark_surf, (px2, py2))

        # 6. Canh chevron pixel lon huong tu cac sprite den bang danh hieu (toa sang theo nhip tho)
        wing_color = (int(color_pink[0] * (0.6 + pulse * 0.4)), int(color_pink[1] * (0.6 + pulse * 0.4)), int(color_pink[2] * (0.6 + pulse * 0.4)))
        # Cac chevron ben trai
        for i in range(4):
            wx = rect_x - 35 - i * 22
            pygame.draw.rect(surface, wing_color, (wx, cy - 10, 14, 20))
            pygame.draw.rect(surface, wing_color, (wx - 8, cy - 30, 8, 20))
            pygame.draw.rect(surface, wing_color, (wx - 8, cy + 10, 8, 20))

        # Cac chevron ben phai
        for i in range(4):
            wx = rect_x + rect_w + 21 + i * 22
            pygame.draw.rect(surface, wing_color, (wx, cy - 10, 14, 20))
            pygame.draw.rect(surface, wing_color, (wx + 14, cy - 30, 8, 20))
            pygame.draw.rect(surface, wing_color, (wx + 14, cy + 10, 8, 20))

        # 7. Hoat anh cuon cham thuc an giua mieng Pacman va bang danh hieu (tang so luong va khoang cach cho phan trong rong hon)
        dot_cycle = (time_passed * 4) % 1.0
        dot_spacing = 40
        num_dots = 4
        for i in range(num_dots):
            dx = (rect_x - 20) - i * dot_spacing + dot_cycle * dot_spacing
            # Ve cham neu no nam ngoai mieng Pacman
            if dx > pacman_x + sprite_size - 10:
                dot_color = (255, 235, 59) if (i + int(time_passed * 4)) % 2 == 0 else (0, 229, 255)
                pygame.draw.rect(surface, dot_color, (dx, cy - 6, 12, 12))

        # 8. Ve cac sprite Pacman va Ma de len tren tat ca hieu ung
        self.draw_pixel_sprite(surface, pacman_x, pacman_y, pacman_pixels, 8, PACMAN_COLOR)
        self.draw_pixel_sprite(surface, ghost_x, ghost_y, ghost_pixels, 8, BLINKY_COLOR)

    def draw_menu(self, surface, time_passed):
        if self.bg_image:
            surface.blit(self.bg_image, (0, 0))
            # Lop phu toi ban trong suot de lam chu de doc hon
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((10, 10, 15, 180)) # Lam mo anh nen
            surface.blit(overlay, (0, 0))
        else:
            surface.fill(BG_COLOR)
        
        # Ve luoi retro di dong o nen
        grid_spacing = 40
        offset_x = int(time_passed * 10) % grid_spacing
        offset_y = int(time_passed * 10) % grid_spacing
        for x in range(-grid_spacing, self.width + grid_spacing, grid_spacing):
            pygame.draw.line(surface, (20, 24, 35), (x + offset_x, 0), (x + offset_x, self.height), 1)
        for y in range(-grid_spacing, self.height + grid_spacing, grid_spacing):
            pygame.draw.line(surface, (20, 24, 35), (0, y + offset_y), (self.width, y + offset_y), 1)
            
        # Cap nhat va ve nen nhom sao
        import random
        for star in self.stars:
            star['y'] += star['speed']
            if star['y'] > self.height:
                star['y'] = 0
                star['x'] = random.randint(0, self.width)
            pygame.draw.rect(surface, star['color'], (star['x'], star['y'], star['size'], star['size']))
            
        # (Quet dong CRT bi tat)
            
        # Vien Neon hoat hoa (Kieu pixel voi border_radius=0)
        pulse = (math.sin(time_passed * 3) + 1) / 2 # 0 den 1
        pygame.draw.rect(surface, WALL_COLOR, (20, 20, self.width - 40, self.height - 40), 2 + int(pulse * 3), border_radius=0)
        
        if self.menu_view == "main":
            # Toa sang nhip tho cua tieu de va nen bang danh hieu pixel lon
            title_text = "PACMAN"
            title_w, title_h = self.font_title.size(title_text)
            self.draw_pixel_banner(surface, (self.width//2, self.height//5), (title_w, title_h), pulse)
            self.draw_neon_text(surface, title_text, self.font_title, PACMAN_COLOR, (self.width//2, self.height//5), glow_radius=30, pulse=pulse)
            
            # Cac nut
            self.hovered_btn = None
            mouse_pos = pygame.mouse.get_pos()
            
            banner_bottom = self.height // 5 + title_h // 2 + 37
            start_y = banner_bottom + int(110 * self.scale)
            display_mode = "NGUOI CHOI VS AI" if self.mode == "Player vs AI" else "AI VS AI"
            btns = [
                ("BAT DAU GAME", "start"),
                (f"CHE DO: {display_mode}", "mode"),
                ("CAI DAT", "settings"),
                ("BAN DO TUY CHINH", "custom_map"),
                ("BANG XEP HANG", "leaderboard"),
                ("THOAT", "exit")
            ]
            
            btn_spacing = int(62 * self.scale)
            btn_h = int(56 * self.scale)
            btn_w = int(700 * self.scale)
            
            for i, (text, action) in enumerate(btns):
                y = start_y + i * btn_spacing
                rect = pygame.Rect(self.width//2 - btn_w//2, y - btn_h//2, btn_w, btn_h)
                
                color = TEXT_COLOR
                prefix = ""
                btn_pulse = 1.0
                if rect.collidepoint(mouse_pos):
                    color = TEXT_HOVER_COLOR
                    prefix = "> "
                    self.hovered_btn = action
                    btn_pulse = pulse + 0.5
                    pygame.draw.rect(surface, WALL_COLOR, (rect.x - 5, rect.y - 5, rect.width + 10, rect.height + 10), 3)
                    
                self.draw_neon_text(surface, prefix + text, self.font_med, color, (self.width//2, y), glow_radius=15, pulse=btn_pulse)
                
            # Hien thi thong tin doi ngu phat trien
            credits = [
                "PHAT TRIEN BOI DOI NGU:",
                "T.A. Kiet 2411026 | T.N.P. Thuy 24110346 | N.T. Dat 24110194"
            ]
            if self.using_pixel_font:
                font_credits = pygame.font.Font("assets/PressStart2P-Regular.ttf", int(14 * self.scale))
            else:
                font_credits = pygame.font.SysFont("Courier", int(20 * self.scale), bold=True)
            line_height = int(font_credits.get_linesize() * 1.8)
            total_height = line_height * len(credits)
            
            # Tinh toan vi tri credits de nam giua nut cuoi cung va vien duoi
            last_btn_y = start_y + 5 * btn_spacing
            avail_top = last_btn_y + int(40 * self.scale)
            avail_bottom = self.height - 25
            center_y = (avail_top + avail_bottom) // 2
            credit_start_y = center_y - total_height // 2
            
            for idx, text in enumerate(credits):
                color = PACMAN_COLOR if idx == 0 else TEXT_COLOR
                lbl = font_credits.render(text, True, color)
                surface.blit(lbl, lbl.get_rect(center=(self.width//2, credit_start_y + idx * line_height + line_height//2)))
            
            return 0, 0, 0
            
        elif self.menu_view == "map_config":
            scale = self.scale
            pulse = (math.sin(time_passed * 5) + 1) / 2
            
            # Panel Rect
            panel_w = int(760 * scale)
            panel_h = int(440 * scale)
            panel_x = self.width // 2 - panel_w // 2
            panel_y = self.height // 2 - panel_h // 2 + int(20 * scale)
            panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
            
            # Title settings screen
            title_text = "CAU HINH BAN DO MOI"
            self.draw_neon_text(surface, title_text, self.font_large, PACMAN_COLOR, (self.width//2, panel_rect.top - int(75 * scale)), glow_radius=30, pulse=pulse)
            
            # Mouse coordinate checking for hover state
            mouse_pos = pygame.mouse.get_pos()
            mouse_x, mouse_y = mouse_pos
            
            # Bottom buttons
            buttons_y = panel_rect.bottom + int(60 * scale)
            action_w = int(320 * scale)
            action_h = int(54 * scale)
            
            confirm_rect = pygame.Rect(self.width // 2 - int(180 * scale) - action_w // 2, buttons_y - action_h // 2, action_w, action_h)
            back_rect = pygame.Rect(self.width // 2 + int(180 * scale) - action_w // 2, buttons_y - action_h // 2, action_w, action_h)
            
            # Map selection row
            map_y = panel_rect.top + int(80 * scale)
            left_arrow_rect = pygame.Rect(self.width // 2 - int(320 * scale) - int(20 * scale), map_y - int(20 * scale), int(40 * scale), int(40 * scale))
            right_arrow_rect = pygame.Rect(self.width // 2 + int(320 * scale) - int(20 * scale), map_y - int(20 * scale), int(40 * scale), int(40 * scale))
            
            is_left_hover = left_arrow_rect.collidepoint(mouse_x, mouse_y)
            is_right_hover = right_arrow_rect.collidepoint(mouse_x, mouse_y)
            
            # Delete button coordinates
            delete_y = panel_rect.top + int(330 * scale)
            delete_w = int(280 * scale)
            delete_h = int(36 * scale)
            delete_rect = pygame.Rect(self.width // 2 - delete_w // 2, delete_y - delete_h // 2, delete_w, delete_h)
            is_delete_hover = delete_rect.collidepoint(mouse_x, mouse_y) if self.selected_map_idx > 0 else False
            
            self.hovered_btn = None
            if confirm_rect.collidepoint(mouse_x, mouse_y):
                self.hovered_btn = "confirm"
            elif back_rect.collidepoint(mouse_x, mouse_y):
                self.hovered_btn = "back"
            elif is_left_hover:
                self.hovered_btn = "left_arrow"
            elif is_right_hover:
                self.hovered_btn = "right_arrow"
            elif is_delete_hover:
                self.hovered_btn = "delete_map"
            else:
                if self.selected_map_idx == 0:
                    # Hover checking for sliders
                    slider_w = int(500 * scale)
                    slider_x = self.width // 2 - slider_w // 2
                    comp_y = panel_rect.top + int(190 * scale)
                    size_y = panel_rect.top + int(310 * scale)
                    
                    if comp_y - int(20 * scale) <= mouse_y <= comp_y + int(20 * scale) and slider_x - 10 <= mouse_x <= slider_x + slider_w + 10:
                        self.hovered_btn = "complexity"
                    elif size_y - int(20 * scale) <= mouse_y <= size_y + int(20 * scale) and slider_x - 10 <= mouse_x <= slider_x + slider_w + 10:
                        self.hovered_btn = "map_size"
            
            # ── VE KHUNG PANEL (GLASSMORPHISM) ──
            # Background trong suot
            temp_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(temp_surf, (8, 12, 20, 210), (0, 0, panel_rect.width, panel_rect.height), border_radius=12)
            surface.blit(temp_surf, (panel_rect.x, panel_rect.y))
            
            # Vien neon
            pygame.draw.rect(surface, (0, 229, 255), panel_rect, 2, border_radius=12)
            

            
            # Map select display
            map_options = ["NGAU NHIEN"] + [m["name"] for m in self.custom_maps]
            current_map_name = map_options[self.selected_map_idx]
            
            self.draw_neon_text(surface, f"BAN DO: {current_map_name}", self.font_med, PACMAN_COLOR, (self.width//2, map_y), glow_radius=15, pulse=pulse)
            
            left_color = TEXT_HOVER_COLOR if is_left_hover else TEXT_COLOR
            right_color = TEXT_HOVER_COLOR if is_right_hover else TEXT_COLOR
            
            self.draw_neon_text(surface, "<", self.font_med, left_color, left_arrow_rect.center, glow_radius=10, pulse=pulse if is_left_hover else 0.5)
            self.draw_neon_text(surface, ">", self.font_med, right_color, right_arrow_rect.center, glow_radius=10, pulse=pulse if is_right_hover else 0.5)
            
            # Sliders or Info
            if self.selected_map_idx == 0:
                slider_w = int(500 * scale)
                slider_x = self.width // 2 - slider_w // 2
                comp_y = panel_rect.top + int(190 * scale)
                size_y = panel_rect.top + int(310 * scale)
                
                # 1. Do Phuc Tap
                self.draw_neon_text(surface, f"DO PHUC TAP BAN DO: {int(self.complexity * 100)}%", self.font_small, (0, 229, 255), (self.width//2, comp_y - int(35 * scale)), glow_radius=8, pulse=pulse)
                pygame.draw.line(surface, WALL_COLOR, (slider_x, comp_y), (slider_x + slider_w, comp_y), 6)
                thumb_comp_x = slider_x + int(self.complexity * slider_w)
                is_comp_h = (self.hovered_btn == "complexity")
                pygame.draw.circle(surface, (255, 235, 59) if is_comp_h else PACMAN_COLOR, (thumb_comp_x, comp_y), int(16 * scale))
                
                # 2. Kich Thuoc
                cols = MIN_GRID_COLS + int((MAX_GRID_COLS - MIN_GRID_COLS) * self.map_size)
                rows = MIN_GRID_ROWS + int((MAX_GRID_ROWS - MIN_GRID_ROWS) * self.map_size)
                if cols % 2 == 0: cols += 1
                if rows % 2 == 0: rows += 1
                
                self.draw_neon_text(surface, f"KICH THUOC LUOI: {cols}x{rows}", self.font_small, (0, 229, 255), (self.width//2, size_y - int(35 * scale)), glow_radius=8, pulse=pulse)
                pygame.draw.line(surface, WALL_COLOR, (slider_x, size_y), (slider_x + slider_w, size_y), 6)
                thumb_size_x = slider_x + int(self.map_size * slider_w)
                is_size_h = (self.hovered_btn == "map_size")
                pygame.draw.circle(surface, (255, 235, 59) if is_size_h else PACMAN_COLOR, (thumb_size_x, size_y), int(16 * scale))
            else:
                # Custom map info
                chosen_map = self.custom_maps[self.selected_map_idx - 1]
                rows = chosen_map["rows"]
                cols = chosen_map["cols"]
                grid = chosen_map["grid"]
                
                pellets = sum(row.count(2) for row in grid)
                ghosts = sum(row.count(4) for row in grid)
                
                self.draw_neon_text(surface, f"KICH THUOC   : {cols}x{rows}", self.font_small, TEXT_COLOR, (self.width//2, panel_rect.top + int(180 * scale)), glow_radius=5)
                self.draw_neon_text(surface, f"VIEN NANG LUONG : {pellets}", self.font_small, TEXT_COLOR, (self.width//2, panel_rect.top + int(240 * scale)), glow_radius=5)
                self.draw_neon_text(surface, f"SO CON MA    : {ghosts}", self.font_small, TEXT_COLOR, (self.width//2, panel_rect.top + int(300 * scale)), glow_radius=5)
                
                # Delete map button rendering
                delete_color = (255, 60, 60) if is_delete_hover else (180, 40, 40)
                delete_pulse = pulse if is_delete_hover else 0.5
                self.draw_neon_text(surface, "[ XOA BAN DO ]", self.font_small, delete_color, delete_rect.center, glow_radius=10, pulse=delete_pulse)
                
                self.draw_neon_text(surface, "SAN SANG KHOI CHAY", self.font_med, (0, 255, 128), (self.width//2, panel_rect.top + int(385 * scale)), glow_radius=15, pulse=pulse)
            
            # ── VE NUT HANH DONG ──
            # Confirm button
            conf_pulse = pulse + 0.5 if self.hovered_btn == "confirm" else 0.5
            conf_color = (0, 255, 128) if self.hovered_btn == "confirm" else (0, 180, 90)
            pygame.draw.rect(surface, (5, 20, 10), confirm_rect, border_radius=6)
            pygame.draw.rect(surface, conf_color, confirm_rect, 2, border_radius=6)
            self.draw_neon_text(surface, "TIEP TUC", self.font_med, conf_color, confirm_rect.center, glow_radius=10, pulse=conf_pulse)
            
            # Back button
            back_pulse = pulse + 0.5 if self.hovered_btn == "back" else 0.5
            back_color = (255, 50, 50) if self.hovered_btn == "back" else (150, 30, 30)
            pygame.draw.rect(surface, (20, 5, 5), back_rect, border_radius=6)
            pygame.draw.rect(surface, back_color, back_rect, 2, border_radius=6)
            self.draw_neon_text(surface, "QUAY LAI", self.font_med, back_color, back_rect.center, glow_radius=10, pulse=back_pulse)
            
            return 0, 0, 0
            
        elif self.menu_view == "settings":
            scale = self.scale
            
            # Start and spacing
            start_y = self.height // 3 - int(45 * scale)
            
            # Available height for cards
            panel_h = self.height - start_y - int(85 * scale)
            
            # Single Center Panel (Ghosts AI & Personality Profile)
            panel_w = int(720 * scale)
            panel_x = self.width // 2 - panel_w // 2
            panel_rect = pygame.Rect(panel_x, start_y - int(75 * scale), panel_w, panel_h)
            
            # Ghost / Pacman buttons
            Center_R = self.width // 2
            ghost_w = int(220 * scale)
            btn_h = int(50 * scale)
            
            ghost_btns = [
                ("Pacman", Center_R, panel_rect.top + int(90 * scale)),
                ("Blinky", Center_R - int(120 * scale), panel_rect.top + int(155 * scale)),
                ("Pinky", Center_R + int(120 * scale), panel_rect.top + int(155 * scale)),
                ("Inky", Center_R - int(120 * scale), panel_rect.top + int(220 * scale)),
                ("Clyde", Center_R + int(120 * scale), panel_rect.top + int(220 * scale))
            ]
            
            # Legend coordinates
            legend_y = panel_rect.top + int(280 * scale)
            legend_w = panel_w - int(40 * scale)
            legend_h = panel_h - int(340 * scale)
            legend_rect = pygame.Rect(panel_rect.centerx - legend_w // 2, panel_rect.top + int(320 * scale), legend_w, legend_h)
            
            # Bottom buttons
            buttons_y = self.height - int(50 * scale)
            action_w = int(350 * scale)
            action_h = int(60 * scale)
            
            reset_rect = pygame.Rect(self.width // 2 - int(200 * scale) - action_w // 2, buttons_y - action_h // 2, action_w, action_h)
            back_rect = pygame.Rect(self.width // 2 + int(200 * scale) - action_w // 2, buttons_y - action_h // 2, action_w, action_h)
            
            # Tieu de settings screen
            title_text = "CAI DAT CAU HINH THUAT TOAN GHOST"
            title_font = self.font_large
            if title_font.size(title_text)[0] > self.width - 80:
                title_font = self.font_med
            self.draw_neon_text(surface, title_text, title_font, PACMAN_COLOR, (self.width//2, self.height//7), glow_radius=30, pulse=pulse)
            
            # Mouse coordinate checking for hover state
            mouse_pos = pygame.mouse.get_pos()
            mouse_x, mouse_y = mouse_pos
            
            self.hovered_btn = None
                    
            for name, gx, gy in ghost_btns:
                rect = pygame.Rect(gx - ghost_w // 2, gy - btn_h // 2, ghost_w, btn_h)
                if rect.collidepoint(mouse_x, mouse_y):
                    self.hovered_btn = name
                    
            if reset_rect.collidepoint(mouse_x, mouse_y):
                self.hovered_btn = "reset"
            elif back_rect.collidepoint(mouse_x, mouse_y):
                self.hovered_btn = "back"
            else:
                slider_w = int(400 * scale)
                slider_x = self.width // 2 - slider_w // 2
                slider_y = buttons_y - int(45 * scale)
                if slider_y - int(20 * scale) <= mouse_y <= slider_y + int(20 * scale) and slider_x - 10 <= mouse_x <= slider_x + slider_w + 10:
                    self.hovered_btn = "volume"
                
            # ── VE KHUNG PANEL (GLASSMORPHISM) ──
            def draw_glass_panel(surf, rect, border_color, tag_text):
                # Background trong suot
                temp_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                pygame.draw.rect(temp_surf, (8, 12, 20, 210), (0, 0, rect.width, rect.height), border_radius=12)
                surf.blit(temp_surf, (rect.x, rect.y))
                
                # Vien neon
                pygame.draw.rect(surf, border_color, rect, 2, border_radius=12)
                
                # Tag hieu he thong o goc top-right
                if tag_text:
                    lbl_tag = self.font_sidebar.render(tag_text, True, (border_color[0]//2 + 127, border_color[1]//2 + 127, border_color[2]//2 + 127))
                    surf.blit(lbl_tag, (rect.right - lbl_tag.get_width() - int(15 * scale), rect.top + int(10 * scale)))
                
                # Cac hoa tiet cyber o goc
                dec = int(8 * scale)
                pygame.draw.line(surf, border_color, (rect.x, rect.y), (rect.x + dec*2, rect.y), 4)
                pygame.draw.line(surf, border_color, (rect.x, rect.y), (rect.x, rect.y + dec*2), 4)
                pygame.draw.line(surf, border_color, (rect.right, rect.bottom), (rect.right - dec*2, rect.bottom), 4)
                pygame.draw.line(surf, border_color, (rect.right, rect.bottom), (rect.right, rect.bottom - dec*2), 4)
            
            draw_glass_panel(surface, panel_rect, (255, 0, 128), "")
            
            # ── VE GHOST ALGORITHMS ──
            self.draw_neon_text(surface, "ALGO CHO PACMAN & GHOSTS", self.font_small, (255, 0, 128), (panel_rect.centerx, panel_rect.top + int(26 * scale)), glow_radius=8, pulse=pulse)
            
            ghost_colors = {
                "Pacman": PACMAN_COLOR,
                "Blinky": BLINKY_COLOR,
                "Pinky": PINKY_COLOR,
                "Inky": INKY_COLOR,
                "Clyde": CLYDE_COLOR
            }
            
            for name, gx, gy in ghost_btns:
                rect = pygame.Rect(gx - ghost_w // 2, gy - btn_h // 2, ghost_w, btn_h)
                
                # To mau nen hieu ung mo theo he mau ma rieng cua tung ghost
                color_bright = ghost_colors[name]
                color_dim = (color_bright[0] // 2, color_bright[1] // 2, color_bright[2] // 2)
                
                is_h = (self.hovered_btn == name)
                border_color = color_bright if is_h else color_dim
                border_thickness = 2 if is_h else 1
                
                bg_color = (color_bright[0] // 16, color_bright[1] // 16, color_bright[2] // 16)
                pygame.draw.rect(surface, bg_color, rect, border_radius=6)
                pygame.draw.rect(surface, border_color, rect, border_thickness, border_radius=6)
                
                btn_pulse = pulse + 0.5 if is_h else 0.5
                text = f"{name.upper()}: {self.algorithms[name]}"
                self.draw_neon_text(surface, text, self.font_small, border_color, rect.center, glow_radius=10, pulse=btn_pulse)
                
                if name == "Pacman":
                    # Draw a beautiful animated Pacman sprite to the left & right of Pacman button
                    time_passed = pygame.time.get_ticks() / 1000.0
                    p_color = PACMAN_COLOR
                        
                    for side in (-1, 1):
                        px = Center_R + side * int(185 * scale)
                        float_y = math.sin(time_passed * 4 + (side * 0.5)) * int(4 * scale)
                        py = gy + float_y
                        prad = int(22 * scale)
                        
                        # Anim mouth
                        mouth_angle = (math.sin(time_passed * 12) + 1) / 2 * math.pi / 4
                        # Rotate mouth to look at the button
                        base_angle = 0 if side == -1 else math.pi
                        
                        points = [(px, py)]
                        for angle in range(int(math.degrees(mouth_angle)), int(math.degrees(2 * math.pi - mouth_angle)), 15):
                            rad = math.radians(angle) + base_angle
                            x = px + prad * math.cos(rad)
                            y = py - prad * math.sin(rad)
                            points.append((x, y))
                            
                        # Draw base body
                        if len(points) > 2:
                            pygame.draw.polygon(surface, p_color, points)
                
            # ── VE LEGEN HANH VI CUA CAC THUC THE BEN DUOI ALGO ──
            self.draw_neon_text(surface, "HANH VI DI CHUYEN CUA CAC THUC THE", self.font_small, PACMAN_COLOR, (panel_rect.centerx, legend_y + int(20 * scale)), glow_radius=5, pulse=0.5)
            
            pygame.draw.rect(surface, (5, 8, 12), legend_rect, border_radius=6)
            pygame.draw.rect(surface, (30, 50, 70), legend_rect, 1, border_radius=6)
            
            legend_lines = [
                "Pacman (Vang): Di chuyen ne ma tim thuc an (A*, Greedy, BFS, DFS)",
                "Blinky (Do): Duoi theo truc tiep vi tri Pacman",
                "Pinky (Hong): Di truoc don dau Pacman 4 o",
                "Inky (Xanh): Su dung DFS (gioi han 15) de truc tiep duoi bat Pacman",
                "Clyde (Cam): Vay bat, ep Pacman vao giua Clyde va Blinky"
            ]
            
            line_spacing = int(22 * scale)
            for idx, line in enumerate(legend_lines):
                if "(" in line and ")" in line:
                    parts = line.split(")", 1)
                    prefix = parts[0] + ")"
                    suffix = parts[1]
                    
                    ghost_name = prefix.split("(")[0].strip()
                    g_col = ghost_colors.get(ghost_name, (200, 200, 200))
                    
                    lbl_prefix = self.font_guide.render(prefix, True, g_col)
                    lbl_suffix = self.font_guide.render(suffix, True, (180, 200, 220))
                    
                    surface.blit(lbl_prefix, (legend_rect.left + int(15 * scale), legend_rect.top + int(15 * scale) + idx * line_spacing))
                    surface.blit(lbl_suffix, (legend_rect.left + int(15 * scale) + lbl_prefix.get_width(), legend_rect.top + int(15 * scale) + idx * line_spacing))
                else:
                    lbl = self.font_guide.render(line, True, (180, 200, 220))
                    surface.blit(lbl, (legend_rect.left + int(15 * scale), legend_rect.top + int(15 * scale) + idx * line_spacing))
                
            slider_w = int(400 * scale)
            slider_h = int(10 * scale)
            slider_x = self.width // 2 - slider_w // 2
            slider_y = buttons_y - int(45 * scale)
            
            # Label
            vol_text = f"AM LUONG HE THONG: {int(self.sound_volume * 100)}%"
            self.draw_neon_text(surface, vol_text, self.font_small, (0, 229, 255), (self.width // 2, slider_y - int(18 * scale)), glow_radius=5, pulse=pulse)
            
            # Slider track
            track_rect = pygame.Rect(slider_x, slider_y - slider_h // 2, slider_w, slider_h)
            pygame.draw.rect(surface, (15, 20, 30), track_rect, border_radius=4)
            pygame.draw.rect(surface, (30, 50, 70), track_rect, 1, border_radius=4)
            
            # Fill track
            fill_w = int(self.sound_volume * slider_w)
            if fill_w > 0:
                fill_rect = pygame.Rect(slider_x, slider_y - slider_h // 2, fill_w, slider_h)
                pygame.draw.rect(surface, (0, 229, 255), fill_rect, border_radius=4)
                
            # Slider thumb (handle)
            thumb_x = slider_x + fill_w
            thumb_r = int(10 * scale)
            is_volume_hovered = (self.hovered_btn == "volume")
            thumb_color = (255, 235, 59) if is_volume_hovered else (255, 255, 255)
            pygame.draw.circle(surface, thumb_color, (thumb_x, slider_y), thumb_r)
            pygame.draw.circle(surface, (0, 229, 255), (thumb_x, slider_y), thumb_r + 2, 1)

            # ── VE NUT HANH DONG DONG BO PHIA DUOI ──
            # Reset button
            reset_pulse = pulse + 0.5 if self.hovered_btn == "reset" else 0.5
            reset_color = PACMAN_COLOR if self.hovered_btn == "reset" else (160, 140, 20)
            pygame.draw.rect(surface, (20, 15, 5), reset_rect, border_radius=6)
            pygame.draw.rect(surface, reset_color, reset_rect, 2, border_radius=6)
            self.draw_neon_text(surface, "MAC DINH", self.font_med, reset_color, reset_rect.center, glow_radius=10, pulse=reset_pulse)
            
            # Back button
            back_pulse = pulse + 0.5 if self.hovered_btn == "back" else 0.5
            back_color = (255, 50, 50) if self.hovered_btn == "back" else (150, 30, 30)
            pygame.draw.rect(surface, (20, 5, 5), back_rect, border_radius=6)
            pygame.draw.rect(surface, back_color, back_rect, 2, border_radius=6)
            self.draw_neon_text(surface, "QUAY LAI", self.font_med, back_color, back_rect.center, glow_radius=10, pulse=back_pulse)
            
            return 0, 0, 0

    def handle_menu_click(self, mouse_pos):
        if self.menu_view == "main":
            if self.hovered_btn == "mode":
                self.mode = "Player vs AI" if self.mode == "AI vs AI" else "AI vs AI"
                return "mode"
            elif self.hovered_btn == "settings":
                self.menu_view = "settings"
                return "settings"
            elif self.hovered_btn == "start":
                self.custom_maps = load_custom_maps()
                self.selected_map_idx = 0
                self.menu_view = "map_config"
                return "map_config"
            elif self.hovered_btn == "custom_map":
                return "custom_map"
            elif self.hovered_btn == "leaderboard":
                return "leaderboard"
            elif self.hovered_btn == "exit":
                return "exit"
        elif self.menu_view == "map_config":
            mouse_x, mouse_y = mouse_pos
            scale = self.scale
            
            panel_w = int(760 * scale)
            panel_h = int(440 * scale)
            panel_x = self.width // 2 - panel_w // 2
            panel_y = self.height // 2 - panel_h // 2 + int(20 * scale)
            
            buttons_y = panel_y + panel_h + int(60 * scale)
            action_w = int(320 * scale)
            action_h = int(54 * scale)
            
            confirm_rect = pygame.Rect(self.width // 2 - int(180 * scale) - action_w // 2, buttons_y - action_h // 2, action_w, action_h)
            back_rect = pygame.Rect(self.width // 2 + int(180 * scale) - action_w // 2, buttons_y - action_h // 2, action_w, action_h)
            
            # Left & Right arrow buttons
            map_y = panel_y + int(80 * scale)
            left_arrow_rect = pygame.Rect(self.width // 2 - int(320 * scale) - int(20 * scale), map_y - int(20 * scale), int(40 * scale), int(40 * scale))
            right_arrow_rect = pygame.Rect(self.width // 2 + int(320 * scale) - int(20 * scale), map_y - int(20 * scale), int(40 * scale), int(40 * scale))
            
            # Delete button bounds
            delete_y = panel_y + int(330 * scale)
            delete_w = int(280 * scale)
            delete_h = int(36 * scale)
            delete_rect = pygame.Rect(self.width // 2 - delete_w // 2, delete_y - delete_h // 2, delete_w, delete_h)
            
            if self.selected_map_idx > 0 and delete_rect.collidepoint(mouse_x, mouse_y):
                chosen_map = self.custom_maps[self.selected_map_idx - 1]
                delete_custom_map(chosen_map["name"])
                self.custom_maps = load_custom_maps()
                self.selected_map_idx = 0
                return "delete_map"
            
            if left_arrow_rect.collidepoint(mouse_x, mouse_y):
                map_options = ["NGAU NHIEN"] + [m["name"] for m in self.custom_maps]
                self.selected_map_idx = (self.selected_map_idx - 1) % len(map_options)
                return "change_map"
            elif right_arrow_rect.collidepoint(mouse_x, mouse_y):
                map_options = ["NGAU NHIEN"] + [m["name"] for m in self.custom_maps]
                self.selected_map_idx = (self.selected_map_idx + 1) % len(map_options)
                return "change_map"
            
            if confirm_rect.collidepoint(mouse_x, mouse_y):
                return "start"
            elif back_rect.collidepoint(mouse_x, mouse_y):
                self.menu_view = "main"
                return "back"
        elif self.menu_view == "settings":
            mouse_x, mouse_y = mouse_pos
            scale = self.scale
            
            # Start and spacing
            start_y = self.height // 3 - int(45 * scale)
            
            # Available height for cards
            panel_h = self.height - start_y - int(60 * scale)
            
            # Center Panel coordinates
            panel_w = int(720 * scale)
            panel_x = self.width // 2 - panel_w // 2
            panel_rect = pygame.Rect(panel_x, start_y - int(75 * scale), panel_w, panel_h)
            
            # Ghost / Pacman buttons
            Center_R = self.width // 2
            ghost_w = int(220 * scale)
            btn_h = int(50 * scale)
            
            ghost_btns = [
                ("Pacman", Center_R, panel_rect.top + int(90 * scale)),
                ("Blinky", Center_R - int(120 * scale), panel_rect.top + int(155 * scale)),
                ("Pinky", Center_R + int(120 * scale), panel_rect.top + int(155 * scale)),
                ("Inky", Center_R - int(120 * scale), panel_rect.top + int(220 * scale)),
                ("Clyde", Center_R + int(120 * scale), panel_rect.top + int(220 * scale))
            ]
            
            # Check if any input box is clicked
            self.focused_heuristic_idx = None
                    
            # Check ghost buttons
            for name, gx, gy in ghost_btns:
                rect = pygame.Rect(gx - ghost_w // 2, gy - btn_h // 2, ghost_w, btn_h)
                if rect.collidepoint(mouse_x, mouse_y):
                    # Rotate algorithm for ghost
                    algos = ["A*", "Greedy", "BFS", "DFS"]
                    idx = algos.index(self.algorithms[name])
                    self.algorithms[name] = algos[(idx + 1) % len(algos)]
                    return f"algo_{name}"
                    
            # Check bottom buttons
            buttons_y = self.height - int(50 * scale)
            action_w = int(350 * scale)
            action_h = int(60 * scale)
            
            reset_rect = pygame.Rect(self.width // 2 - int(200 * scale) - action_w // 2, buttons_y - action_h // 2, action_w, action_h)
            if reset_rect.collidepoint(mouse_x, mouse_y):
                self.sound_volume = 0.8
                self.algorithms = {
                    "Pacman": "A*",
                    "Blinky": "A*",
                    "Pinky": "Greedy",
                    "Inky": "DFS",
                    "Clyde": "BFS"
                }
                return "reset_heuristics"
                
            back_rect = pygame.Rect(self.width // 2 + int(200 * scale) - action_w // 2, buttons_y - action_h // 2, action_w, action_h)
            if back_rect.collidepoint(mouse_x, mouse_y):
                self.menu_view = "main"
                self.focused_heuristic_idx = None
                return "back"
                
            return None

    def handle_settings_keydown(self, event):
        return False


    def handle_mouse_down(self, mouse_pos):
        mouse_x, mouse_y = mouse_pos
        scale = self.scale
        
        if self.menu_view == "settings":
            buttons_y = self.height - int(50 * scale)
            slider_w = int(400 * scale)
            slider_x = self.width // 2 - slider_w // 2
            slider_y = buttons_y - int(45 * scale)
            
            if slider_y - int(20 * scale) <= mouse_y <= slider_y + int(20 * scale) and slider_x - 10 <= mouse_x <= slider_x + slider_w + 10:
                self.dragging_slider = "volume"
                self.sound_volume = max(0.0, min(1.0, (mouse_x - slider_x) / slider_w))
                return True
            return False
            
        elif self.menu_view == "map_config":
            if self.selected_map_idx > 0:
                return False
                
            panel_w = int(760 * scale)
            panel_h = int(440 * scale)
            panel_x = self.width // 2 - panel_w // 2
            panel_y = self.height // 2 - panel_h // 2 + int(20 * scale)
            
            slider_w = int(500 * scale)
            slider_x = self.width // 2 - slider_w // 2
            comp_y = panel_y + int(190 * scale)
            size_y = panel_y + int(310 * scale)
            
            # Kiem tra thanh truot Do Phuc Tap
            if comp_y - int(20 * scale) <= mouse_y <= comp_y + int(20 * scale) and slider_x - 10 <= mouse_x <= slider_x + slider_w + 10:
                self.dragging_slider = "complexity"
                self.complexity = max(0.0, min(1.0, (mouse_x - slider_x) / slider_w))
                return True
                
            # Kiem tra thanh truot Kich Thuoc Ban Do
            if size_y - int(20 * scale) <= mouse_y <= size_y + int(20 * scale) and slider_x - 10 <= mouse_x <= slider_x + slider_w + 10:
                self.dragging_slider = "map_size"
                self.map_size = max(0.0, min(1.0, (mouse_x - slider_x) / slider_w))
                return True
            return False
            
        return False

    def handle_mouse_motion(self, mouse_pos):
        if not self.dragging_slider:
            return None
            
        mouse_x, mouse_y = mouse_pos
        scale = self.scale
        
        if self.menu_view == "settings" and self.dragging_slider == "volume":
            buttons_y = self.height - int(50 * scale)
            slider_w = int(400 * scale)
            slider_x = self.width // 2 - slider_w // 2
            slider_y = buttons_y - int(45 * scale)
            
            self.sound_volume = max(0.0, min(1.0, (mouse_x - slider_x) / slider_w))
            return mouse_x, slider_y
            
        if self.menu_view == "map_config":
            if self.selected_map_idx > 0:
                return None
                
            panel_w = int(760 * scale)
            panel_h = int(440 * scale)
            panel_x = self.width // 2 - panel_w // 2
            panel_y = self.height // 2 - panel_h // 2 + int(20 * scale)
            
            slider_w = int(500 * scale)
            slider_x = self.width // 2 - slider_w // 2
            val = max(0.0, min(1.0, (mouse_x - slider_x) / slider_w))
            
            if self.dragging_slider == "complexity":
                self.complexity = val
                comp_y = panel_y + int(190 * scale)
                return mouse_x, comp_y
            elif self.dragging_slider == "map_size":
                self.map_size = val
                size_y = panel_y + int(310 * scale)
                return mouse_x, size_y
            
        return None

    def handle_mouse_up(self):
        self.dragging_slider = None

    def set_stats(self, time_str, steps, turns, ghosts_eaten=None, map_size=None, mode=None, search_count=None, total_explored_nodes=None, ghost_explored=None):
        self.stats = {
            "THOI GIAN": time_str,
            "SO BUOC DI": str(steps),
            "SO LUOT QUAY": str(turns)
        }
        if ghosts_eaten is not None:
            self.stats["MA AN DUOC"] = f"{ghosts_eaten} / 4"
        if map_size is not None:
            self.stats["BAN DO"] = map_size
        if mode is not None:
            display_mode = "NGUOI CHOI VS AI" if mode == "Player vs AI" else "AI VS AI"
            self.stats["CHE DO"] = display_mode
        if total_explored_nodes is not None:
            self.stats["TONG NUT DUYET"] = f"{total_explored_nodes} NUT"
        if ghost_explored is not None:
            for name, val in ghost_explored.items():
                self.stats[f"TONG NUT {name.upper()}"] = f"{val} NUT"

    def draw_end_screen(self, surface, won):
        # Lop phu trong suot dep hon
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        if won:
            # Man hinh chien thang sang sua, ruc ro hon (Navy trong suot 62%)
            overlay.fill((25, 30, 48, 160))
        else:
            # Man hinh that bai do u toi, nang ne (Den xam tram u, 92% opacity)
            overlay.fill((15, 10, 16, 235))
        surface.blit(overlay, (0, 0))
        
        # Ve luoi retro di dong tuy theo ket qua game
        time_passed = pygame.time.get_ticks() / 1000.0
        grid_spacing = 40
        offset_x = int(time_passed * 5) % grid_spacing
        offset_y = int(time_passed * 5) % grid_spacing
        grid_color = (16, 20, 30)
        for x in range(-grid_spacing, self.width + grid_spacing, grid_spacing):
            pygame.draw.line(surface, grid_color, (x + offset_x, 0), (x + offset_x, self.height), 1)
        for y in range(-grid_spacing, self.height + grid_spacing, grid_spacing):
            pygame.draw.line(surface, grid_color, (0, y + offset_y), (self.width, y + offset_y), 1)
            
        # Cap nhat va ve hat nen tuy chinh (Confetti xoay cho chien thang / Mua nuoc mat u sau cho game-over)
        import random
        if not hasattr(self, '_bg_particles') or not self._bg_particles:
            self._bg_particles = []
            for _ in range(450):
                self._bg_particles.append({
                    'x': random.randint(0, self.width),
                    'y': random.randint(-self.height, 0),
                    'speed': random.uniform(2.5, 5.5) if won else random.uniform(4.5, 8.5),
                    'size': random.uniform(4.0, 9.0) if won else random.uniform(1.0, 3.0),
                    'color': random.choice([
                        (255, 235, 59),   # Vang
                        (0, 229, 255),    # Xanh lo
                        (255, 102, 204),  # Hong
                        (255, 255, 255)   # Trang
                    ]) if won else random.choice([
                        (30, 45, 80),     # Xanh u buon
                        (85, 20, 32),     # Do u toi
                        (100, 100, 120),  # Xam mua
                        (50, 10, 80)      # Tim heo ua
                    ]),
                    'drift': random.uniform(-0.6, 0.6),
                    'angle': random.uniform(0, math.pi * 2) if won else None
                })
                
        if won:
            # Confetti roi xoay tron sinh dong
            for p in self._bg_particles:
                p['y'] += p['speed'] * 0.7
                p['x'] += p['drift']
                if p['angle'] is not None:
                    p['angle'] += 0.05
                    
                if p['y'] > self.height:
                    p['y'] = random.randint(-50, 0)
                    p['x'] = random.randint(0, self.width)
                    
                confetti_w = int(p['size'] * 1.6)
                confetti_h = int(p['size'])
                conf_surf = pygame.Surface((confetti_w * 2, confetti_h * 2), pygame.SRCALPHA)
                pygame.draw.rect(conf_surf, p['color'], (confetti_w // 2, confetti_h // 2, confetti_w, confetti_h), border_radius=2)
                rotated = pygame.transform.rotate(conf_surf, math.degrees(p['angle']))
                surface.blit(rotated, (int(p['x'] - rotated.get_width()//2), int(p['y'] - rotated.get_height()//2)))
        else:
            # Mua roi u sau keo dai vet mua
            for p in self._bg_particles:
                p['y'] += p['speed'] * 1.5
                p['x'] += p['drift'] * 0.3
                
                if p['y'] > self.height:
                    p['y'] = random.randint(-50, 0)
                    p['x'] = random.randint(0, self.width)
                    
                start_pt = (int(p['x']), int(p['y']))
                end_pt = (int(p['x'] + p['drift'] * 0.3), int(p['y'] + 18))
                pygame.draw.line(surface, p['color'], start_pt, end_pt, 2)
             
        pulse = (math.sin(pygame.time.get_ticks() / 300.0) + 1) / 2
        
        # Tieu de
        title = "CHIEN THANG" if won else "KET THUC GAME"
        color = PACMAN_COLOR if won else BLINKY_COLOR
        
        # Tinh toan kich thuoc thuc te cua chu de de banner luon phu hop hoan hao
        title_text_w, title_text_h = self.font_large.size(title)
        banner_w = title_text_w + int(240 * self.scale)
        banner_h = title_text_h + int(60 * self.scale)
        
        # Nen tieu de dep mat tuy chinh theo ket qua game
        if won:
            title_x = self.width // 2
            title_y = self.height // 4
            banner_rect = pygame.Rect(title_x - banner_w // 2, title_y - banner_h // 2, banner_w, banner_h)
            
            banner_bg = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            banner_bg.fill((15, 18, 28, 180)) # Navy dam
            surface.blit(banner_bg, banner_rect.topleft)
            
            time_ms = pygame.time.get_ticks()
            sweep_speed = 0.8
            sweep_pos = int((time_ms * sweep_speed) % (banner_w + 300)) - 150
            
            beam_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            for x_offset in range(-60, 60):
                dist_factor = 1.0 - (abs(x_offset) / 60.0)
                if dist_factor > 0:
                    beam_x = sweep_pos + x_offset
                    if 0 <= beam_x < banner_w:
                        beam_alpha = int(90 * dist_factor * (0.7 + 0.3 * math.sin(time_ms / 40.0)))
                        pygame.draw.line(beam_surf, (*WALL_COLOR, beam_alpha), (beam_x, 0), (beam_x, banner_h), 3)
            surface.blit(beam_surf, banner_rect.topleft)
            
            glow_surf = pygame.Surface((banner_w + 40, banner_h + 40), pygame.SRCALPHA)
            for g in range(6):
                g_alpha = int((35 - g * 5) * (0.5 + 0.5 * pulse))
                g_rect = pygame.Rect(20 - g, 20 - g, banner_w + g * 2, banner_h + g * 2)
                pygame.draw.rect(glow_surf, (*PACMAN_COLOR, g_alpha), g_rect, 2, border_radius=12)
            surface.blit(glow_surf, (banner_rect.x - 20, banner_rect.y - 20))
            
            pygame.draw.rect(surface, PACMAN_COLOR, banner_rect, 3, border_radius=12)
            
            led_radius = int(5 * self.scale)
            corner_offsets = [
                (banner_rect.left + 15, banner_rect.top + 15),
                (banner_rect.right - 15, banner_rect.top + 15),
                (banner_rect.left + 15, banner_rect.bottom - 15),
                (banner_rect.right - 15, banner_rect.bottom - 15)
            ]
            for idx, (lx, ly) in enumerate(corner_offsets):
                is_on = ((time_ms // 180) + idx) % 2 == 0
                led_color = WALL_COLOR if is_on else (20, 35, 45)
                
                if is_on:
                    led_glow_surf = pygame.Surface((led_radius * 6, led_radius * 6), pygame.SRCALPHA)
                    pygame.draw.circle(led_glow_surf, (*WALL_COLOR, 100), (led_radius * 3, led_radius * 3), led_radius * 2.5)
                    surface.blit(led_glow_surf, (lx - led_radius * 3, ly - led_radius * 3))
                    
                pygame.draw.circle(surface, led_color, (lx, ly), led_radius)
        else:
            # Nen tieu de KET THUC GAME u uat voi anh sang quet do loi va den LED nhap nhay cham (glitchy)
            title_x = self.width // 2
            title_y = self.height // 4
            banner_rect = pygame.Rect(title_x - banner_w // 2, title_y - banner_h // 2, banner_w, banner_h)
            
            banner_bg = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            banner_bg.fill((25, 12, 14, 180)) # Do u toi
            surface.blit(banner_bg, banner_rect.topleft)
            
            time_ms = pygame.time.get_ticks()
            sweep_speed = 0.5
            sweep_pos = int((time_ms * sweep_speed) % (banner_w + 300)) - 150
            
            beam_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
            for x_offset in range(-50, 50):
                dist_factor = 1.0 - (abs(x_offset) / 50.0)
                if dist_factor > 0:
                    beam_x = sweep_pos + x_offset
                    if 0 <= beam_x < banner_w:
                        beam_alpha = int(70 * dist_factor * (0.6 + 0.4 * math.sin(time_ms / 60.0)))
                        pygame.draw.line(beam_surf, (255, 0, 85, beam_alpha), (beam_x, 0), (beam_x, banner_h), 2)
            surface.blit(beam_surf, banner_rect.topleft)
            
            glow_surf = pygame.Surface((banner_w + 40, banner_h + 40), pygame.SRCALPHA)
            glitch_intensity = 1.0 if random.random() > 0.08 else 0.2
            for g in range(5):
                g_alpha = int((30 - g * 6) * (0.4 + 0.6 * pulse) * glitch_intensity)
                g_rect = pygame.Rect(20 - g, 20 - g, banner_w + g * 2, banner_h + g * 2)
                pygame.draw.rect(glow_surf, (255, 0, 85, g_alpha), g_rect, 2, border_radius=12)
            surface.blit(glow_surf, (banner_rect.x - 20, banner_rect.y - 20))
            
            pygame.draw.rect(surface, (255, 0, 85), banner_rect, 3, border_radius=12)
            
            led_radius = int(5 * self.scale)
            corner_offsets = [
                (banner_rect.left + 15, banner_rect.top + 15),
                (banner_rect.right - 15, banner_rect.top + 15),
                (banner_rect.left + 15, banner_rect.bottom - 15),
                (banner_rect.right - 15, banner_rect.bottom - 15)
            ]
            for idx, (lx, ly) in enumerate(corner_offsets):
                is_on = ((time_ms // 400) + idx) % 2 == 0
                led_color = (255, 0, 85) if is_on else (45, 15, 20)
                
                if is_on:
                    led_glow_surf = pygame.Surface((led_radius * 6, led_radius * 6), pygame.SRCALPHA)
                    pygame.draw.circle(led_glow_surf, (255, 0, 85, 80), (led_radius * 3, led_radius * 3), led_radius * 2.5)
                    surface.blit(led_glow_surf, (lx - led_radius * 3, ly - led_radius * 3))
                    
                pygame.draw.circle(surface, led_color, (lx, ly), led_radius)
                
        self.draw_neon_text(surface, title, self.font_large, color, (self.width//2, self.height//4), glow_radius=30, pulse=pulse)
        
        # Vien theo chu de nhap nhay (vang cho chien thang, do cho that bai)
        pygame.draw.rect(surface, color, (40, 40, self.width - 80, self.height - 80), 2 + int(pulse * 3), border_radius=0)
        
        # Bang so lieu thong ke
        title_y = self.height // 4
        panel_y = max(title_y + banner_h // 2 + int(40 * self.scale), self.height // 2 - int(240 * self.scale))
        keys = list(self.stats.keys())
        
        # Tinh toan do rong lon nhat cua key de thiet lap cot thang hang tuyet doi
        max_key_w = 0
        for key in keys:
            w, h = self.font_med.size(key)
            if w > max_key_w:
                max_key_w = w
                
        for i, key in enumerate(keys):
            val = self.stats[key]
            cy = panel_y + i * int(40 * self.scale)
            
            # Dich chuyen nhe sang trai khi thang de can bang voi bang xep hang o ben phai
            x_pos = self.width // 2
            if won and getattr(self, 'current_rank', None) is not None:
                x_pos = self.width // 2 - int(250 * self.scale)
                
            x_label_start = x_pos - max_key_w - int(15 * self.scale)
            x_colon = x_pos
            x_val_start = x_pos + int(15 * self.scale)
            
            # Draw label (left aligned)
            lbl_w, lbl_h = self.font_med.size(key)
            lbl_center = (x_label_start + lbl_w // 2, cy)
            self.draw_neon_text(surface, key, self.font_med, TEXT_COLOR, lbl_center, glow_radius=5, pulse=0.5)
            
            # Draw colon (centered)
            self.draw_neon_text(surface, ":", self.font_med, TEXT_COLOR, (x_colon, cy), glow_radius=5, pulse=0.5)
            
            # Draw value (left aligned)
            val_w, val_h = self.font_med.size(val)
            val_center = (x_val_start + val_w // 2, cy)
            self.draw_neon_text(surface, val, self.font_med, TEXT_COLOR, val_center, glow_radius=5, pulse=0.5)
            
        # Neu chien thang, hien thi bang xep hang leaderboard ben phai (side text)
        if won and getattr(self, 'current_rank', None) is not None:
            rank_x = self.width // 2 + int(420 * self.scale)
            rank_y = self.height // 2 - int(50 * self.scale)
            
            box_w = int(400 * self.scale)
            box_h = int(240 * self.scale)
            box_rect = pygame.Rect(rank_x - box_w // 2, rank_y - box_h // 2, box_w, box_h)
            
            # Ve o hien thi hieu ung neon
            pygame.draw.rect(surface, PACMAN_COLOR, box_rect, int(3 * self.scale), border_radius=15)
            
            # Bong neon phat sang mo phia sau panel xep hang
            glow_surf = pygame.Surface((box_w + 20, box_h + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*PACMAN_COLOR, 30), (10, 10, box_w, box_h), int(8 * self.scale), border_radius=15)
            surface.blit(glow_surf, (box_rect.x - 10, box_rect.y - 10))
            
            # Cac dong chu xep hang
            self.draw_neon_text(surface, "XEP HANG BANG DIEM", self.font_small, PACMAN_COLOR, (rank_x, rank_y - int(70 * self.scale)), glow_radius=5)
            rank_str = f"VI TRI: #{self.current_rank}"
            self.draw_neon_text(surface, rank_str, self.font_med, WALL_COLOR, (rank_x, rank_y - int(10 * self.scale)), glow_radius=15, pulse=pulse)
            
            score_str = f"DIEM: {getattr(self, 'current_score', 0)}"
            self.draw_neon_text(surface, score_str, self.font_small, TEXT_COLOR, (rank_x, rank_y + int(40 * self.scale)), glow_radius=5)
            
            total_str = f"TREN TONG SO: {getattr(self, 'total_leaderboard_entries', 0)}"
            self.draw_neon_text(surface, total_str, self.font_small, PINKY_COLOR, (rank_x, rank_y + int(80 * self.scale)), glow_radius=5)
            
        # Cac nut
        self.hovered_btn = None
        mouse_pos = pygame.mouse.get_pos()
        
        btn_y = self.height - 180
        btns = [("[ CHOI LAI ]", "start", self.width//2 - 280), ("[ THOAT ]", "exit", self.width//2 + 280)]
        
        for text, action, x in btns:
            rect = pygame.Rect(x - 220, btn_y - 35, 440, 70)
            
            btn_color = TEXT_COLOR
            btn_pulse = 0.5
            if rect.collidepoint(mouse_pos):
                btn_color = TEXT_HOVER_COLOR
                self.hovered_btn = action
                btn_pulse = pulse + 0.5
                # Ve mot hop pixel neon xung quanh nut duoc di chuot qua
                pygame.draw.rect(surface, WALL_COLOR, (rect.x - 5, rect.y - 5, rect.width + 10, rect.height + 10), 3)
                
            self.draw_neon_text(surface, text, self.font_med, btn_color, (x, btn_y), glow_radius=15, pulse=btn_pulse)

    def draw_sidebar(self, surface, game, time_passed):
        # Ve bang nen
        x_start = self.width - SIDEBAR_WIDTH
        panel_rect = pygame.Rect(x_start, 0, SIDEBAR_WIDTH, self.height)
        
        # Nen mau xanh hai quan toi / xam ban trong suot bong bay
        pygame.draw.rect(surface, (18, 20, 26), panel_rect)
        
        # Vien gioi han ben trai
        pygame.draw.line(surface, WALL_COLOR, (x_start, 0), (x_start, self.height), 4)
        
        pulse = (math.sin(time_passed * 3) + 1) / 2 # 0 den 1
        scale = self.scale
        
        # --- TIEU DE ---
        title_y = max(35, int(50 * scale))
        self.draw_neon_text(surface, "GIAM SAT HE THONG", self.font_sidebar, PACMAN_COLOR, (x_start + SIDEBAR_WIDTH//2, title_y), glow_radius=15, pulse=pulse)
        
        # Bo chia ngang tinh te
        sep_y = title_y + max(25, int(35 * scale))
        pygame.draw.line(surface, (40, 50, 70), (x_start + 20, sep_y), (self.width - 20, sep_y), 2)
        
        # --- TRANG THAI & SO LIEU THONG KE GAME ---
        stats_start_y = title_y + max(35, int(50 * scale))
        
        # Chu trang thai tam dung
        status_text = "TAM DUNG" if game.paused else "DANG CHAY"
        status_color = BLINKY_COLOR if game.paused else (0, 255, 128)
        self.draw_neon_text(surface, f"TRANG THAI: {status_text}", self.font_sidebar, status_color, (x_start + SIDEBAR_WIDTH//2, stats_start_y), glow_radius=5, pulse=pulse)
        
        # Hien thi cac so lieu thong ke khac
        stats_list = [
            f"THOI GIAN : {game.get_time_str()}",
            f"BUOC DI   : {game.steps}",
            f"LUOT QUAY : {game.turns}",
            f"VIEN SUC MANH : {len(game.power_pellets)}",
            f"PHUC TAP  : {int(game.complexity * 100)}%",
            f"BAN DO    : {game.cols}x{game.rows}"
        ]
        
        line_height = self.font_sidebar.get_linesize() + int(10 * scale)
        for i, text in enumerate(stats_list):
            y_pos = stats_start_y + max(25, int(35 * scale)) + i * line_height
            lbl = self.font_sidebar.render(text, True, TEXT_COLOR)
            surface.blit(lbl, (x_start + 40, y_pos))
            
        # Bo chia ngang tinh te
        divider_y = stats_start_y + max(25, int(35 * scale)) + len(stats_list) * line_height + 10
        pygame.draw.line(surface, (40, 50, 70), (x_start + 30, divider_y), (self.width - 30, divider_y), 2)
        
        # --- CHAN DOAN AI CUA THUC THE ---
        diag_start_y = divider_y + max(15, int(25 * scale))
        self.draw_neon_text(surface, "TRANG THAI AI CORE", self.font_sidebar, WALL_COLOR, (x_start + SIDEBAR_WIDTH//2, diag_start_y), glow_radius=4, pulse=0.5)
        
        entities_info = []
        # Pacman
        p_state_str = "BINH THUONG"
        if game.pacman.state == 2:
            p_state_str = "SAN MOI"
        elif game.pacman.state == 3:
            p_state_str = "DANG CHO"
        entities_info.append(("PACMAN", game.pacman.algo, p_state_str, PACMAN_COLOR, game.pacman.get_avg_ram(), game.pacman.total_explored_nodes))
        
        # Cac con ma
        for g in game.ghosts:
            g_name = g.__class__.__name__.upper()
            g_state = "DUOI THEO"
            if g.is_dead:
                g_state = "DA CHET"
            elif g.is_scared:
                g_state = "SO HAI"
            entities_info.append((g_name, g.algo, g_state, g.color, g.get_avg_ram(), g.total_explored_nodes))
            
        block_height = int(line_height * 2.2)
        for i, (name, algo, state, color, avg_ram, total_nodes) in enumerate(entities_info):
            y_pos = diag_start_y + max(20, int(30 * scale)) + i * block_height
            # Dong 1: Ten thuc the & Thuat toan (trai), RAM (phai)
            lbl_name = self.font_sidebar.render(f"{name} ({algo})", True, color)
            surface.blit(lbl_name, (x_start + 30, y_pos))
            
            lbl_ram = self.font_sidebar.render(f"{avg_ram:.1f} KB", True, color)
            surface.blit(lbl_ram, (self.width - 30 - lbl_ram.get_width(), y_pos))
            
            # Dong 2: Trang thai (trai), Nut duyet (phai)
            state_color = (100, 100, 100) if state == "DA CHET" else TEXT_COLOR
            lbl_state = self.font_sidebar.render(f"  > {state}", True, state_color)
            surface.blit(lbl_state, (x_start + 30, y_pos + line_height))
            
            lbl_nodes = self.font_sidebar.render(f"{total_nodes} NUT", True, color)
            surface.blit(lbl_nodes, (self.width - 30 - lbl_nodes.get_width(), y_pos + line_height))

        # --- SPEED SLIDER (Centered in the sidebar, above control buttons) ---
        slider_w = int(320 * scale)
        slider_h = int(10 * scale)
        slider_x = x_start + (SIDEBAR_WIDTH - slider_w) // 2
        slider_y = self.height - int(285 * scale)
        
        # Draw track
        track_rect = pygame.Rect(slider_x, slider_y - slider_h // 2, slider_w, slider_h)
        pygame.draw.rect(surface, (10, 15, 25), track_rect, border_radius=4)
        pygame.draw.rect(surface, (40, 50, 70), track_rect, 1, border_radius=4)
        
        # Current speed scale
        current_speed = getattr(game, 'speed_scale', 1.0)
        fraction = (current_speed - 0.2) / 2.8
        handle_x = slider_x + int(fraction * slider_w)
        
        # Draw ticks & tick labels
        ticks = [0.2, 1.0, 2.0, 3.0]
        for tick in ticks:
            tick_frac = (tick - 0.2) / 2.8
            tick_x = slider_x + int(tick_frac * slider_w)
            pygame.draw.line(surface, (60, 70, 90), (tick_x, slider_y + int(5 * scale)), (tick_x, slider_y + int(10 * scale)), 1)
            
            lbl_text = f"{tick}x"
            lbl_surf = self.font_guide.render(lbl_text, True, (120, 140, 160))
            lbl_rect = lbl_surf.get_rect(centerx=tick_x, top=slider_y + int(14 * scale))
            surface.blit(lbl_surf, lbl_rect)
            
        # Slider Title & Value Label
        title_lbl = self.font_guide.render("TOC DO:", True, WALL_COLOR)
        speed_lbl = self.font_guide.render(f"{current_speed}x", True, PACMAN_COLOR)
        
        total_w = title_lbl.get_width() + speed_lbl.get_width() + int(10 * scale)
        start_title_x = x_start + (SIDEBAR_WIDTH - total_w) // 2
        
        surface.blit(title_lbl, (start_title_x, slider_y - int(32 * scale)))
        surface.blit(speed_lbl, (start_title_x + title_lbl.get_width() + int(10 * scale), slider_y - int(32 * scale)))
        
        # Handle (draggable knob)
        handle_w = int(12 * scale)
        handle_h = int(24 * scale)
        handle_rect = pygame.Rect(handle_x - handle_w // 2, slider_y - handle_h // 2, handle_w, handle_h)
        
        is_hovered_handle = handle_rect.collidepoint(pygame.mouse.get_pos())
        is_dragging = (self.dragging_slider == "speed")
        handle_color = WALL_COLOR if (is_hovered_handle or is_dragging) else TEXT_COLOR
        
        if is_hovered_handle or is_dragging:
            glow_surf = pygame.Surface((handle_w + 12, handle_h + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*WALL_COLOR[:3], 80), (6, 6, handle_w, handle_h), border_radius=3)
            for j in range(1, 5):
                pygame.draw.rect(glow_surf, (*WALL_COLOR[:3], int(40 / j)), (6 - j, 6 - j, handle_w + j*2, handle_h + j*2), 1, border_radius=3)
            surface.blit(glow_surf, (handle_rect.x - 6, handle_rect.y - 6))
            
        pygame.draw.rect(surface, handle_color, handle_rect, border_radius=3)
            
        # --- CAC NUT DIEU KHIEN (O duoi cung) ---
        btn_h = 50
        btn_w = 320
        btn_x = x_start + (SIDEBAR_WIDTH - btn_w) // 2
        
        btn_y_pause = self.height - 210
        btn_y_replay = self.height - 140
        btn_y_exit = self.height - 70
        
        self.buttons = [
            {"rect": pygame.Rect(btn_x, btn_y_pause, btn_w, btn_h), "action": "pause", "text": "TIEP TUC" if game.paused else "TAM DUNG"},
            {"rect": pygame.Rect(btn_x, btn_y_replay, btn_w, btn_h), "action": "replay", "text": "CHOI LAI"},
            {"rect": pygame.Rect(btn_x, btn_y_exit, btn_w, btn_h), "action": "exit", "text": "THOAT RA MENU"}
        ]
        
        for btn in self.buttons:
            rect = btn["rect"]
            text = btn["text"]
            action = btn["action"]
            
            is_hovered = (self.hovered_sidebar_btn == action)
            btn_color = TEXT_HOVER_COLOR if is_hovered else TEXT_COLOR
            btn_pulse = pulse + 0.5 if is_hovered else 0.5
            
            # Ve vien nut
            border_color = WALL_COLOR if is_hovered else (40, 50, 70)
            pygame.draw.rect(surface, border_color, rect, 2)
            
            # Lam noi bat nhe nen khi di chuot qua
            if is_hovered:
                bg_highlight = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                bg_highlight.fill((*WALL_COLOR[:3], 30))
                surface.blit(bg_highlight, (rect.x, rect.y))
                
            self.draw_neon_text(surface, text, self.font_sidebar, btn_color, rect.center, glow_radius=10, pulse=btn_pulse)

    def handle_sidebar_hover(self, mouse_pos):
        self.hovered_sidebar_btn = None
        x_start = self.width - SIDEBAR_WIDTH
        btn_h = 50
        btn_w = 320
        btn_x = x_start + (SIDEBAR_WIDTH - btn_w) // 2
        
        btn_y_pause = self.height - 210
        btn_y_replay = self.height - 140
        btn_y_exit = self.height - 70
        
        buttons = [
            (pygame.Rect(btn_x, btn_y_pause, btn_w, btn_h), "pause"),
            (pygame.Rect(btn_x, btn_y_replay, btn_w, btn_h), "replay"),
            (pygame.Rect(btn_x, btn_y_exit, btn_w, btn_h), "exit")
        ]
        
        for rect, action in buttons:
            if rect.collidepoint(mouse_pos):
                self.hovered_sidebar_btn = action
                break

    def handle_sidebar_click(self, mouse_pos, game):
        self.handle_sidebar_hover(mouse_pos)
        
        # Check if Speed Slider clicked
        scale = self.scale
        x_start = self.width - SIDEBAR_WIDTH
        slider_w = int(320 * scale)
        slider_h = int(20 * scale)
        slider_x = x_start + (SIDEBAR_WIDTH - slider_w) // 2
        slider_y = self.height - int(285 * scale)
        click_rect = pygame.Rect(slider_x - 10, slider_y - slider_h // 2 - 10, slider_w + 20, slider_h + 20)
        
        if click_rect.collidepoint(mouse_pos):
            self.dragging_slider = "speed"
            fraction = (mouse_pos[0] - slider_x) / slider_w
            fraction = max(0.0, min(1.0, fraction))
            game.speed_scale = round(0.2 + fraction * 2.8, 1)
            return "speed"
        
        if self.hovered_sidebar_btn == "pause":
            game.toggle_pause()
            return "pause"
        elif self.hovered_sidebar_btn == "replay":
            self.current_rank = None
            self.current_score = None
            game.start_game(game.complexity, game.map_size, game.mode, self.algorithms, self.pacman_heuristics)
            return "replay"
        elif self.hovered_sidebar_btn == "exit":
            game.state = STATE_MENU
            return "exit"
            
        return None

    def handle_gameplay_mouse_motion(self, mouse_pos, game):
        if self.dragging_slider == "speed":
            scale = self.scale
            x_start = self.width - SIDEBAR_WIDTH
            slider_w = int(320 * scale)
            slider_x = x_start + (SIDEBAR_WIDTH - slider_w) // 2
            
            fraction = (mouse_pos[0] - slider_x) / slider_w
            fraction = max(0.0, min(1.0, fraction))
            game.speed_scale = round(0.2 + fraction * 2.8, 1)

    def draw_start_animation(self, surface, elapsed):
        """
        Cinematic game-start animation. Returns True when animation is done.
        Phases:
          0.00–0.80s : White flash + title zoom-in
          0.80–2.40s : Two black bars slide in from top & bottom (wipe)
          2.40–3.80s : Full black with neon 'INITIATING...' counter + scanlines
          3.80s+     : Done — signal main loop to begin game
        """
        ANIM_TOTAL = 3.8

        cx, cy = self.width // 2, self.height // 2

        # --- Giai doan 0: Nhay trang (0 - 0.80 s) ---
        flash_end = 0.80
        if elapsed < flash_end:
            t = elapsed / flash_end          # 0->1
            # Cuong do: dat dinh tai 0.5 sau do mo dan
            intensity = 1.0 - abs(t - 0.5) * 2.0
            alpha = int(min(255, 255 * intensity))
            flash_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 255, alpha))
            surface.blit(flash_surf, (0, 0))

            # Tieu de thu phong tu 3x xuong 1x
            zoom = 3.0 - 2.0 * t
            zoom_alpha = int(200 * t)
            try:
                title_surf = self.font_title.render("PACMAN", True, PACMAN_COLOR)
                w, h = title_surf.get_size()
                scaled = pygame.transform.scale(title_surf, (int(w * zoom), int(h * zoom)))
                scaled.set_alpha(zoom_alpha)
                surface.blit(scaled, scaled.get_rect(center=(cx, cy)))
            except Exception:
                pass

        # --- Giai doan 1: Cac thanh den quet vao (0.80 - 2.40 s) ---
        wipe_start, wipe_end = 0.80, 2.40
        if elapsed >= wipe_start:
            t = min(1.0, (elapsed - wipe_start) / (wipe_end - wipe_start))
            # Easing cubic trong-ngoai
            ease = t * t * (3 - 2 * t)
            bar_h = int(self.height // 2 * ease)

            # Thanh tren
            pygame.draw.rect(surface, (0, 0, 0), (0, 0, self.width, bar_h))
            # Thanh duoi
            pygame.draw.rect(surface, (0, 0, 0), (0, self.height - bar_h, self.width, bar_h))

            # Cac duong vien neon tren cac thanh
            if bar_h > 2:
                pygame.draw.line(surface, WALL_COLOR, (0, bar_h - 2), (self.width, bar_h - 2), 3)
                pygame.draw.line(surface, WALL_COLOR, (0, self.height - bar_h + 1), (self.width, self.height - bar_h + 1), 3)

        # --- Giai doan 2: Den hoan toan + chu INITIATING (2.40 - 3.80 s) ---
        hold_start = 2.40
        if elapsed >= hold_start:
            # Che phu toan bo man hinh bang mau den
            pygame.draw.rect(surface, (0, 0, 0), (0, 0, self.width, self.height))

            # Hieu ung duong quet
            for sy in range(0, self.height, 4):
                scanline = pygame.Surface((self.width, 2), pygame.SRCALPHA)
                scanline.fill((0, 0, 0, 60))
                surface.blit(scanline, (0, sy))

            # Vien phat sang
            pulse = (math.sin(elapsed * 20) + 1) / 2
            pygame.draw.rect(surface, WALL_COLOR,
                             (20, 20, self.width - 40, self.height - 40),
                             2 + int(pulse * 3), border_radius=0)

            # INITIATING... voi cac dau cham nhap nhay
            dot_count = int((elapsed - hold_start) * 6) % 4
            dots = "." * dot_count
            self.draw_neon_text(surface, f"KHOI TAO{dots}", self.font_med,
                                WALL_COLOR, (cx, cy), glow_radius=20, pulse=pulse)

            # Nhan phu
            self.draw_neon_text(surface, "DANG TAI BAN DO", self.font_small,
                                (100, 200, 255), (cx, cy + 60), glow_radius=8, pulse=0.5)

        # --- Hoan thanh ---
        return elapsed >= ANIM_TOTAL

    # ------------------------------------------------------------------
    # HOAT ANH KET THUC (dien anh chien thang hoac game-over)
    # ------------------------------------------------------------------
    def reset_end_anim(self):
        """Call this whenever a new end-animation should start from scratch."""
        self._end_particles = []
        self._bg_particles = []
        self._end_anim_seeded = False
        self._shared_overlay = None   # Tai su dung mot be mat SRCALPHA moi khung hinh
        self._scanline_surf = None    # Giai duong quet duoc nuong san
        self._crack_lines = []        # Hinh hoc vet nut duoc tinh toan san

    def draw_end_anim(self, surface, won, elapsed):
        """
        Optimised cinematic end animation. Returns True when complete (~4.0 s).
        Perf: one shared SRCALPHA surface per frame, simple rects, pre-baked surfaces.
        """
        import colorsys
        ANIM_TOTAL = 4.0
        cx, cy = self.width // 2, self.height // 2

        # Cap phat cac be mat dung chung mot lan
        if not hasattr(self, '_shared_overlay') or self._shared_overlay is None:
            self._shared_overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        if not hasattr(self, '_scanline_surf') or self._scanline_surf is None:
            self._scanline_surf = pygame.Surface((self.width, 2), pygame.SRCALPHA)
            self._scanline_surf.fill((0, 0, 0, 55))
        if not hasattr(self, '_crack_lines'):
            self._crack_lines = []

        ov = self._shared_overlay

        # Gieo hat cac hat mot lan
        if not self._end_anim_seeded:
            self._end_anim_seeded = True
            self._end_particles = []
            if won:
                VICTORY_COLORS = [
                    (255, 235, 59), (0, 229, 255), (255, 102, 204),
                    (255, 255, 255), (100, 255, 100), (255, 150, 0),
                ]
                for _ in range(120):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(80, 600)
                    self._end_particles.append({
                        'x': float(cx), 'y': float(cy),
                        'vx': math.cos(angle) * speed,
                        'vy': math.sin(angle) * speed - random.uniform(80, 260),
                        'color': random.choice(VICTORY_COLORS),
                        'w': random.randint(6, 16), 'h': random.randint(4, 10),
                        'gravity': random.uniform(200, 420),
                        'lifetime': random.uniform(1.5, 4.0),
                        'born': random.uniform(0.0, 0.8),
                    })
            else:
                DEBRIS_COLORS = [(180, 0, 0), (255, 30, 30), (80, 0, 0), (200, 50, 50)]
                for _ in range(80):
                    angle = random.uniform(0, math.pi * 2)
                    speed = random.uniform(40, 380)
                    self._end_particles.append({
                        'x': float(random.randint(0, self.width)),
                        'y': float(random.randint(0, self.height)),
                        'vx': math.cos(angle) * speed * 0.3,
                        'vy': math.sin(angle) * speed * 0.3,
                        'color': random.choice(DEBRIS_COLORS),
                        'w': random.randint(4, 12), 'h': random.randint(4, 12),
                        'gravity': 40,
                        'lifetime': random.uniform(1.0, 3.5),
                        'born': random.uniform(0.0, 0.6),
                    })
                # Tinh toan truoc hinh hoc vet nut (hat giong co dinh -> cac vet nut giong nhau moi game)
                self._crack_lines = []
                rng = random.Random(42)
                for i in range(12):
                    angle = (i / 12) * math.pi * 2
                    crack_len = rng.randint(80, min(self.width, self.height) // 2)
                    jagged = []
                    x0, y0 = cx, cy
                    seg_len = crack_len // 6
                    for _ in range(6):
                        wobble = rng.uniform(-18, 18)
                        x1 = int(x0 + math.cos(angle + wobble * 0.04) * seg_len)
                        y1 = int(y0 + math.sin(angle + wobble * 0.04) * seg_len)
                        jagged.append((x0, y0))
                        x0, y0 = x1, y1
                    if len(jagged) >= 2:
                        self._crack_lines.append(jagged)

        # ── CHIEN THANG ────────────────────────────────────────────────────
        if won:
            # Nhay vang (be mat don gian + set_alpha = nhanh)
            if elapsed < 0.5:
                alpha = int(255 * (1.0 - elapsed / 0.5))
                flash = pygame.Surface((self.width, self.height))
                flash.fill((255, 235, 100))
                flash.set_alpha(alpha)
                surface.blit(flash, (0, 0))

            # Lop phu lam toi (mot lan fill, mot lan blit)
            if elapsed >= 0.3:
                fade_in = min(1.0, (elapsed - 0.3) / 0.4)
                ov.fill((5, 8, 12, int(210 * fade_in)))
                surface.blit(ov, (0, 0))

            # Tat ca confetti len MOT be mat lop phu
            ov.fill((0, 0, 0, 0))
            drew_any = False
            for p in self._end_particles:
                age = elapsed - p['born']
                if age < 0 or age > p['lifetime']:
                    continue
                frac = age / p['lifetime']
                px = int(p['x'] + p['vx'] * age)
                py = int(p['y'] + p['vy'] * age + 0.5 * p['gravity'] * age * age)
                alpha = int(255 * (1.0 - frac ** 2))
                w = max(1, int(p['w'] * (1.0 - frac * 0.4)))
                h = max(1, int(p['h'] * (1.0 - frac * 0.4)))
                r, g, b = p['color']
                pygame.draw.rect(ov, (r, g, b, alpha), (px - w//2, py - h//2, w, h))
                drew_any = True
            if drew_any:
                surface.blit(ov, (0, 0))

            # Cac vong song xung kich len MOT be mat lop phu
            if 0.4 < elapsed < 2.5:
                ov.fill((0, 0, 0, 0))
                ring_colors = [(255, 235, 59), (0, 229, 255), (255, 102, 204), (255, 255, 255)]
                drew_ring = False
                for i in range(4):
                    ring_age = (elapsed - 0.4) - i * 0.35
                    if ring_age < 0:
                        continue
                    radius = int(ring_age * 600)
                    ring_alpha = max(0, int(220 * (1.0 - ring_age / 1.4)))
                    if radius > 0 and ring_alpha > 0:
                        pygame.draw.circle(ov, (*ring_colors[i % 4], ring_alpha), (cx, cy), radius, 4 + i)
                        drew_ring = True
                if drew_ring:
                    surface.blit(ov, (0, 0))

            # Vien cau vong (ve truc tiep — khong ton chi phi SRCALPHA)
            if elapsed >= 1.5:
                hue = ((elapsed * 120) % 360) / 360.0
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                bw = 3 + int((math.sin(elapsed * 8) + 1) * 3)
                pygame.draw.rect(surface, (int(r*255), int(g*255), int(b*255)),
                                 (15, 15, self.width - 30, self.height - 30), bw)

            # Tieu de VICTORY phong to voi 2 lop phat sang (truoc day la 5)
            title_appear = max(0.0, elapsed - 0.2)
            zoom = 1.0 - (1.0 - min(1.0, title_appear / 0.7)) ** 3
            if zoom > 0.01:
                pulse = (math.sin(elapsed * 4) + 1) / 2
                glow_col = (255, int(200 + 55 * pulse), int(30 * pulse))
                try:
                    raw = self.font_large.render("CHIEN THANG!", True, glow_col)
                    w, h = raw.get_size()
                    scaled = pygame.transform.scale(raw, (max(1, int(w * zoom)), max(1, int(h * zoom))))
                    for gi in [4, 2]:
                        gs = pygame.transform.scale(raw, (max(1, int(w*zoom) + gi*6), max(1, int(h*zoom) + gi*4)))
                        gs.set_alpha(int(55 / gi))
                        surface.blit(gs, gs.get_rect(center=(cx, cy - 60)))
                    surface.blit(scaled, scaled.get_rect(center=(cx, cy - 60)))
                except Exception:
                    pass

            if elapsed >= 1.0:
                sub_alpha = min(255, int(255 * (elapsed - 1.0) / 0.5))
                sub = self.font_small.render("DA TIEU DIET TAT CA MA", True, (200, 255, 200))
                sub.set_alpha(sub_alpha)
                surface.blit(sub, sub.get_rect(center=(cx, cy + 30)))

        # ── KET THUC GAME ──────────────────────────────────────────────────
        else:
            # Nhay do
            if elapsed < 0.6:
                alpha = int(220 * (1.0 - elapsed / 0.6))
                flash = pygame.Surface((self.width, self.height))
                flash.fill((180, 0, 0))
                flash.set_alpha(alpha)
                surface.blit(flash, (0, 0))

            # Lop phu lam toi
            if elapsed >= 0.3:
                fade_in = min(1.0, (elapsed - 0.3) / 0.5)
                ov.fill((5, 0, 0, int(220 * fade_in)))
                surface.blit(ov, (0, 0))

            # Cac vet nut — tat ca len MOT lop phu
            if elapsed < 2.2 and self._crack_lines:
                crack_alpha = max(0, int(200 * (1.0 - elapsed / 2.2)))
                ov.fill((0, 0, 0, 0))
                for jagged in self._crack_lines:
                    pygame.draw.lines(ov, (255, 60, 60, crack_alpha), False, jagged, 2)
                surface.blit(ov, (0, 0))

            # Manh vo — MOT lop phu
            ov.fill((0, 0, 0, 0))
            drew_any = False
            for p in self._end_particles:
                age = elapsed - p['born']
                if age < 0 or age > p['lifetime']:
                    continue
                frac = age / p['lifetime']
                px = int(p['x'] + p['vx'] * age)
                py = int(p['y'] + p['vy'] * age + 0.5 * p['gravity'] * age * age)
                alpha = int(255 * (1.0 - frac))
                w = max(1, int(p['w'] * (1.0 - frac * 0.5)))
                r, g, b = p['color']
                pygame.draw.rect(ov, (r, g, b, alpha), (px - w//2, py - w//2, w, w))
                drew_any = True
            if drew_any:
                surface.blit(ov, (0, 0))

            # Cac duong quet — dai duoc nuong san, blit hang
            if elapsed >= 0.6:
                for sy in range(0, self.height, 5):
                    surface.blit(self._scanline_surf, (0, sy))

            # Cac dai nhieu — lap day hinh chu nhat truc tiep (khong dung SRCALPHA)
            if 0.5 < elapsed < 2.5:
                glitch_rng = random.Random(int(elapsed * 30))
                for _ in range(5):
                    gy = glitch_rng.randint(0, self.height - 20)
                    gh = glitch_rng.randint(3, 16)
                    gx_off = glitch_rng.randint(-30, 30)
                    pygame.draw.rect(surface, (0, 0, 0), (gx_off, gy, self.width, gh))

            # Vien mau do nhap nhay
            pulse = (math.sin(elapsed * 6) + 1) / 2
            pygame.draw.rect(surface, (200, 0, 0),
                             (15, 15, self.width - 30, self.height - 30), 3 + int(pulse * 4))

            # Tieu de GAME OVER roi xuong
            drop_t = min(1.0, max(0.0, elapsed - 0.4) / 0.6)
            drop_ease = 1.0 - (1.0 - drop_t) ** 3
            title_y = int(-200 + (cy - 60 - (-200)) * drop_ease)
            if drop_t > 0.01:
                glitch = random.randint(-5, 5) if (0.8 < elapsed < 2.5 and int(elapsed * 20) % 3 == 0) else 0
                try:
                    go_surf = self.font_large.render("KET THUC GAME", True, BLINKY_COLOR)
                    for gi in [5, 2]:
                        gs = pygame.transform.scale(
                            self.font_large.render("KET THUC GAME", True, (180, 0, 0)),
                            (go_surf.get_width() + gi * 8, go_surf.get_height() + gi * 4)
                        )
                        gs.set_alpha(int(70 / gi))
                        surface.blit(gs, gs.get_rect(center=(cx + glitch, title_y)))
                    surface.blit(go_surf, go_surf.get_rect(center=(cx + glitch, title_y)))
                except Exception:
                    pass

            if elapsed >= 1.2:
                sub_alpha = min(255, int(255 * (elapsed - 1.2) / 0.5))
                sub_col = (255, 60, 60) if int(elapsed * 5) % 2 == 0 else (200, 0, 0)
                sub = self.font_small.render("PACMAN DA BI BAT", True, sub_col)
                sub.set_alpha(sub_alpha)
                surface.blit(sub, sub.get_rect(center=(cx, cy + 30)))

        return elapsed >= ANIM_TOTAL


# ─────────────────────────────────────────────────────────────────────────────
# NAME SELECT SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class NameSelectUI:
    """
    Cyberpunk name-entry screen shown before each game starts.
    Player can type a new name or click an existing one from the list.
    """
    MAX_NAME_LEN = 12
    LIST_VISIBLE = 7       # So luong ten toi da co the hien thi cung luc

    def __init__(self, screen_w, screen_h):
        self.w = screen_w
        self.h = screen_h
        self.scale = max(0.5, min(self.w / 1920.0, self.h / 1080.0))
        font_path = "assets/PressStart2P-Regular.ttf"
        try:
            self.font_title = pygame.font.Font(font_path, int(36 * self.scale))
            self.font_med   = pygame.font.Font(font_path, int(18 * self.scale))
            self.font_small = pygame.font.Font(font_path, int(13 * self.scale))
            self.font_tiny  = pygame.font.Font(font_path, int(10 * self.scale))
        except Exception:
            self.font_title = pygame.font.SysFont("monospace", int(44 * self.scale), bold=True)
            self.font_med   = pygame.font.SysFont("monospace", int(24 * self.scale), bold=True)
            self.font_small = pygame.font.SysFont("monospace", int(18 * self.scale), bold=True)
            self.font_tiny  = pygame.font.SysFont("monospace", int(14 * self.scale), bold=True)

        self.name_input = ""
        self.known_names = []   # duoc dien boi ben goi
        self.scroll_offset = 0
        self.hovered_name = None
        self.confirmed_name = None   # duoc thiet lap khi nguoi choi xac nhan
        self.cancelled = False
        self.last_choice = None

    def reset(self, known_names):
        self.known_names = list(known_names)
        self.scroll_offset = 0
        self.hovered_name = None
        self.confirmed_name = None
        self.cancelled = False
        
        # Remember the last choice from the current session or persistent leaderboard
        if getattr(self, 'last_choice', None):
            self.name_input = self.last_choice
        elif self.known_names:
            self.name_input = self.known_names[0]
        else:
            self.name_input = ""

    def _confirm(self):
        name = self.name_input.strip().upper()
        self.confirmed_name = name if name else "ANON"
        self.last_choice = self.confirmed_name

    def handle_event(self, event, mouse_pos):
        mx, my = mouse_pos
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._confirm()
            elif event.key == pygame.K_ESCAPE:
                self.cancelled = True
            elif event.key == pygame.K_BACKSPACE:
                self.name_input = self.name_input[:-1]
            else:
                ch = event.unicode
                if ch and ch.isprintable() and len(self.name_input) < self.MAX_NAME_LEN:
                    self.name_input += ch.upper()
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_offset = max(0, min(
                len(self.known_names) - self.LIST_VISIBLE,
                self.scroll_offset - event.y
            ))
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Nut xac nhan
            if self._confirm_rect().collidepoint(mx, my):
                self._confirm()
                return
            # Nut quay lai
            if self._back_rect().collidepoint(mx, my):
                self.cancelled = True
                return
            # Cac muc trong danh sach ten
            for i, rect in enumerate(self._name_rects()):
                if rect.collidepoint(mx, my):
                    idx = self.scroll_offset + i
                    if idx < len(self.known_names):
                        self.name_input = self.known_names[idx]

    # ── Trinh tro giup bo cuc ───────────────────────────────────────────────────────

    def _input_rect(self):
        w, h = int(600 * self.scale), int(64 * self.scale)
        return pygame.Rect(self.w // 2 - w // 2, self.h // 2 - int(100 * self.scale), w, h)

    def _confirm_rect(self):
        return pygame.Rect(self.w // 2 + int(30 * self.scale), self.h // 2 + int(250 * self.scale), int(260 * self.scale), int(56 * self.scale))

    def _back_rect(self):
        return pygame.Rect(self.w // 2 - int(290 * self.scale), self.h // 2 + int(250 * self.scale), int(240 * self.scale), int(56 * self.scale))

    def _name_rects(self):
        rects = []
        x0 = self.w // 2 - int(300 * self.scale)
        y0 = self.h // 2 + int(20 * self.scale)
        for i in range(self.LIST_VISIBLE):
            rects.append(pygame.Rect(x0, y0 + i * int(54 * self.scale), int(600 * self.scale), int(46 * self.scale)))
        return rects

    # ── Ve ──────────────────────────────────────────────────────────────

    def draw(self, surface):
        import math
        t = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(t * 3) + 1) / 2
        mouse_pos = pygame.mouse.get_pos()

        # Nen
        surface.fill((6, 8, 14))
        # Luoi tinh te
        gs = 40
        ox = int(t * 8) % gs
        oy = int(t * 8) % gs
        for x in range(-gs, self.w + gs, gs):
            pygame.draw.line(surface, (16, 20, 30), (x + ox, 0), (x + ox, self.h), 1)
        for y in range(-gs, self.h + gs, gs):
            pygame.draw.line(surface, (16, 20, 30), (0, y + oy), (self.w, y + oy), 1)

        # Vien neon
        bw = 2 + int(pulse * 2)
        pygame.draw.rect(surface, (0, 229, 255), (20, 20, self.w - 40, self.h - 40), bw)

        # Tieu de
        title = self.font_title.render("NHAP TEN CUA BAN", True, (255, 235, 59))
        surface.blit(title, title.get_rect(center=(self.w // 2, self.h // 4)))

        # Nhan phu
        sub = self.font_tiny.render("NHAP TEN MOI HOAC NHAP VAO NGUOI CHOI CU DUOI DAY", True, (120, 140, 180))
        surface.blit(sub, sub.get_rect(center=(self.w // 2, self.h // 4 + int(52 * self.scale))))

        # Hop nhap lieu
        ir = self._input_rect()
        pygame.draw.rect(surface, (10, 15, 22), ir)
        pygame.draw.rect(surface, (0, 229, 255), ir, 2 + int(pulse))
        # Chu da nhap + con tro nhap nhay
        cursor = "_" if int(t * 2) % 2 == 0 else " "
        display = self.name_input + cursor
        txt = self.font_med.render(display, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(midleft=(ir.x + int(20 * self.scale), ir.centery)))

        # Tieu de danh sach ten da co
        header = self.font_tiny.render("NGUOI CHOI DA CO", True, (0, 229, 255))
        surface.blit(header, (self.w // 2 - int(300 * self.scale), self.h // 2 - int(20 * self.scale)))

        # Danh sach ten
        rects = self._name_rects()
        visible = self.known_names[self.scroll_offset : self.scroll_offset + self.LIST_VISIBLE]
        for i, name in enumerate(visible):
            rect = rects[i]
            is_hover = rect.collidepoint(mouse_pos)
            is_selected = (name == self.name_input)
            bg = (20, 35, 20) if is_selected else ((18, 25, 35) if is_hover else (10, 13, 20))
            border = (0, 220, 120) if is_selected else ((0, 229, 255) if is_hover else (30, 40, 60))
            pygame.draw.rect(surface, bg, rect)
            pygame.draw.rect(surface, border, rect, 1 + is_selected)
            col = (0, 220, 120) if is_selected else ((200, 230, 255) if is_hover else (160, 170, 200))
            lbl = self.font_small.render(name, True, col)
            surface.blit(lbl, lbl.get_rect(midleft=(rect.x + int(18 * self.scale), rect.centery)))

        # Goi y cuon
        if len(self.known_names) > self.LIST_VISIBLE:
            hint = self.font_tiny.render(f"CUON  ({self.scroll_offset+1}-{min(self.scroll_offset+self.LIST_VISIBLE,len(self.known_names))} / {len(self.known_names)})", True, (60, 80, 110))
            surface.blit(hint, hint.get_rect(center=(self.w // 2, self.h // 2 + self.LIST_VISIBLE * int(54 * self.scale) + int(16 * self.scale))))

        # Cac nut
        def draw_btn(rect, label, active_col, hover_col=(0, 229, 255)):
            is_h = rect.collidepoint(mouse_pos)
            col = hover_col if is_h else (40, 55, 70)
            bg  = (12, 22, 12) if label.startswith("▶") else (22, 12, 12) if label.startswith("←") else (12, 18, 26)
            pygame.draw.rect(surface, bg, rect)
            pygame.draw.rect(surface, active_col if is_h else (35, 45, 60), rect, 2)
            lbl = self.font_small.render(label, True, active_col if is_h else (120, 140, 170))
            surface.blit(lbl, lbl.get_rect(center=rect.center))

        draw_btn(self._back_rect(),    "← QUAY LAI",       (200, 80, 80))
        draw_btn(self._confirm_rect(), "▶ XAC NHAN",    (0, 220, 120))


# ─────────────────────────────────────────────────────────────────────────────
# LEADERBOARD SCREEN
# ─────────────────────────────────────────────────────────────────────────────

class LeaderboardUI:
    """Full-screen leaderboard display with cyberpunk styling."""

    ROWS_VISIBLE = 17

    def __init__(self, screen_w, screen_h):
        self.w = screen_w
        self.h = screen_h
        self.scale = max(0.5, min(self.w / 1920.0, self.h / 1080.0))
        font_path = "assets/PressStart2P-Regular.ttf"
        try:
            self.font_title = pygame.font.Font(font_path, int(32 * self.scale))
            self.font_med   = pygame.font.Font(font_path, int(14 * self.scale))
            self.font_small = pygame.font.Font(font_path, int(11 * self.scale))
            self.font_tiny  = pygame.font.Font(font_path, int(9 * self.scale))
        except Exception:
            self.font_title = pygame.font.SysFont("monospace", int(40 * self.scale), bold=True)
            self.font_med   = pygame.font.SysFont("monospace", int(18 * self.scale), bold=True)
            self.font_small = pygame.font.SysFont("monospace", int(14 * self.scale), bold=True)
            self.font_tiny  = pygame.font.SysFont("monospace", int(11 * self.scale))

        self.entries = []         # danh sach dict tu Leaderboard.get_sorted()
        self.scroll = 0
        self.back_pressed = False
        self.last_entry_name = None   # lam noi bat hang cua nguoi choi gan day nhat
        self.selected_detail = None
        self.selected_detail_rank = None

    def reset(self, entries, last_name=None):
        self.entries = entries
        self.scroll = 0
        self.back_pressed = False
        self.last_entry_name = last_name
        self.selected_detail = None
        self.selected_detail_rank = None

    def _back_rect(self):
        return pygame.Rect(self.w // 2 - int(140 * self.scale), self.h - int(80 * self.scale), int(280 * self.scale), int(50 * self.scale))

    def _modal_rect(self):
        w = int(700 * self.scale)
        h = int(640 * self.scale)
        return pygame.Rect(self.w // 2 - w // 2, self.h // 2 - h // 2, w, h)

    def _modal_close_rect(self):
        mr = self._modal_rect()
        btn_w = int(220 * self.scale)
        btn_h = int(45 * self.scale)
        return pygame.Rect(mr.centerx - btn_w // 2, mr.bottom - int(60 * self.scale), btn_w, btn_h)

    def draw_neon_text(self, surface, text, font, color, center_pos, glow_radius=10, pulse=1.0):
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=center_pos)
        glow_color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))
        max_glow = int(glow_radius * pulse)
        for i in range(max_glow, 0, -2):
            glow_surf = font.render(text, True, glow_color)
            try:
                glow_surf.set_alpha(int(200 / max_glow) if max_glow > 0 else 0)
            except Exception:
                pass
            surface.blit(glow_surf, (text_rect.x - i//2, text_rect.y - i//2))
        surface.blit(text_surf, text_rect)

    def handle_event(self, event, mouse_pos):
        if self.selected_detail is not None:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                    self.selected_detail = None
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._modal_close_rect().collidepoint(*mouse_pos):
                    self.selected_detail = None
                elif not self._modal_rect().collidepoint(*mouse_pos):
                    self.selected_detail = None
            return

        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(len(self.entries) - self.ROWS_VISIBLE, self.scroll - event.y))
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.back_pressed = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._back_rect().collidepoint(*mouse_pos):
                self.back_pressed = True
            else:
                row_y0 = int(150 * self.scale)
                row_h = int(46 * self.scale)
                visible = self.entries[self.scroll : self.scroll + self.ROWS_VISIBLE]
                for i, entry in enumerate(visible):
                    y = row_y0 + i * row_h
                    row_rect = pygame.Rect(50, y, self.w - 100, row_h - 4)
                    if row_rect.collidepoint(*mouse_pos):
                        self.selected_detail = entry
                        self.selected_detail_rank = self.scroll + i + 1
                        break

    def draw(self, surface):
        import math, colorsys
        t = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(t * 3) + 1) / 2

        # Nen
        surface.fill((6, 8, 14))
        gs = 50
        ox = int(t * 5) % gs; oy = int(t * 5) % gs
        for x in range(-gs, self.w + gs, gs):
            pygame.draw.line(surface, (14, 18, 26), (x+ox, 0), (x+ox, self.h), 1)
        for y in range(-gs, self.h + gs, gs):
            pygame.draw.line(surface, (14, 18, 26), (0, y+oy), (self.w, y+oy), 1)

        # Vien cau vong
        hue = (t * 60) % 360 / 360.0
        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 1.0)
        pygame.draw.rect(surface, (int(r*255), int(g*255), int(b*255)),
                         (20, 20, self.w - 40, self.h - 40), 2 + int(pulse))

        # Tieu de
        title = self.font_title.render("BANG XEP HANG", True, (255, 235, 59))
        title_y = int(70 * self.scale)
        # Phat sang
        for gi in [4, 2]:
            gs2 = pygame.transform.scale(title, (title.get_width()+gi*4, title.get_height()+gi*2))
            gs2.set_alpha(40//gi)
            surface.blit(gs2, gs2.get_rect(center=(self.w//2, title_y)))
        surface.blit(title, title.get_rect(center=(self.w//2, title_y)))

        # Tieu de cot
        # Tieu de cot
        col_x = [
            int(self.w * 0.04),
            int(self.w * 0.08),
            int(self.w * 0.23),
            int(self.w * 0.34),
            int(self.w * 0.43),
            int(self.w * 0.49),
            int(self.w * 0.59),
            int(self.w * 0.67),
            int(self.w * 0.75),
            int(self.w * 0.85)
        ]
        headers = ["#", "TEN", "DIEM SO", "KET QUA", "MA", "THOI GIAN", "BUOC", "SO CUA", "BAN DO", "NGAY"]
        header_col = (0, 229, 255)
        header_y = int(120 * self.scale)
        for i, (hdr, x) in enumerate(zip(headers, col_x)):
            lbl = self.font_small.render(hdr, True, header_col)
            surface.blit(lbl, (x, header_y))
        
        divider_y = int(140 * self.scale)
        pygame.draw.line(surface, (0, 160, 200), (50, divider_y), (self.w - 50, divider_y), 1)

        # Cac hang
        row_h = int(46 * self.scale)
        y0 = int(150 * self.scale)
        visible = self.entries[self.scroll : self.scroll + self.ROWS_VISIBLE]
        rank_colors = [(255, 215, 0), (192, 192, 192), (205, 127, 50)]   # Vang, Bac, Dong

        for i, entry in enumerate(visible):
            rank = self.scroll + i + 1
            y = y0 + i * row_h
            row_rect = pygame.Rect(50, y, self.w - 100, row_h - 4)

            is_highlighted = (entry.get("name") == self.last_entry_name)
            is_win = entry.get("result", "LOSS") == "WIN"

            # Nen hang
            if is_highlighted:
                bg = (15, 30, 15)
                pygame.draw.rect(surface, bg, row_rect)
                pygame.draw.rect(surface, (0, 220, 120), row_rect, 1)
            elif rank <= 3:
                bg = (20, 18, 5)
                pygame.draw.rect(surface, bg, row_rect)

            # Cot hang
            rank_col = rank_colors[rank-1] if rank <= 3 else (100, 110, 140)
            rank_lbl = self.font_small.render(str(rank), True, rank_col)
            surface.blit(rank_lbl, (col_x[0], y + int(12 * self.scale)))

            # Ten
            name_col = (0, 220, 120) if is_highlighted else (220, 230, 255)
            name_lbl = self.font_small.render(entry.get("name", "?"), True, name_col)
            surface.blit(name_lbl, (col_x[1], y + int(12 * self.scale)))

            # Diem so
            score_col = (255, 235, 59) if rank <= 3 else (200, 210, 255)
            score_lbl = self.font_med.render(str(entry.get("score", 0)), True, score_col)
            surface.blit(score_lbl, (col_x[2], y + int(10 * self.scale)))

            # Ket qua
            res = entry.get("result", "LOSS")
            res_display = "THANG" if res == "WIN" else "THUA"
            res_col = (0, 220, 120) if res == "WIN" else (255, 60, 60)
            res_lbl = self.font_small.render(res_display, True, res_col)
            surface.blit(res_lbl, (col_x[3], y + int(12 * self.scale)))

            # Ma
            gh_lbl = self.font_small.render(str(entry.get("ghosts", 0)), True, (200, 200, 240))
            surface.blit(gh_lbl, (col_x[4], y + int(12 * self.scale)))

            # Thoi gian
            tm_lbl = self.font_small.render(entry.get("time", "--"), True, (180, 200, 220))
            surface.blit(tm_lbl, (col_x[5], y + int(12 * self.scale)))

            # Buoc
            steps_lbl = self.font_small.render(str(entry.get("steps", 0)), True, (200, 220, 200))
            surface.blit(steps_lbl, (col_x[6], y + int(12 * self.scale)))

            # So cua
            turns_lbl = self.font_small.render(str(entry.get("turns", 0)), True, (200, 220, 200))
            surface.blit(turns_lbl, (col_x[7], y + int(12 * self.scale)))

            # Ban do (Map Size)
            map_sz = entry.get("map_size", "N/A")
            map_lbl = self.font_small.render(str(map_sz), True, (160, 190, 220))
            surface.blit(map_lbl, (col_x[8], y + int(12 * self.scale)))

            # Ngay
            dt_lbl = self.font_tiny.render(entry.get("date", ""), True, (80, 95, 120))
            surface.blit(dt_lbl, (col_x[9], y + int(15 * self.scale)))

        # Goi y cuon
        if len(self.entries) > self.ROWS_VISIBLE:
            hint = self.font_tiny.render(
                f"MUC {self.scroll+1}-{min(self.scroll+self.ROWS_VISIBLE,len(self.entries))} / {len(self.entries)}   CUON DE XEM THEM",
                True, (60, 80, 110)
            )
            surface.blit(hint, hint.get_rect(center=(self.w//2, y0 + self.ROWS_VISIBLE * row_h + int(10 * self.scale))))

        # Nut quay lai
        br = self._back_rect()
        is_h = br.collidepoint(pygame.mouse.get_pos())
        pygame.draw.rect(surface, (20, 10, 10) if is_h else (10, 8, 12), br)
        pygame.draw.rect(surface, (200, 80, 80) if is_h else (50, 30, 40), br, 2)
        back_lbl = self.font_small.render("← QUAY LAI MENU", True, (200, 80, 80) if is_h else (120, 80, 100))
        surface.blit(back_lbl, back_lbl.get_rect(center=br.center))

        # ── VE CHI TIET TRAN DAU MODAL (NEU DUOC CHON) ──
        if self.selected_detail is not None:
            # Dim screen
            overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            overlay.fill((5, 7, 12, 210))
            surface.blit(overlay, (0, 0))

            mr = self._modal_rect()
            res = self.selected_detail.get("result", "LOSS")
            border_color = (0, 229, 255) if res == "WIN" else (255, 0, 128)
            tag_text = "[GAME.WIN]" if res == "WIN" else "[GAME.LOSS]"

            # Glass background
            temp_surf = pygame.Surface((mr.width, mr.height), pygame.SRCALPHA)
            pygame.draw.rect(temp_surf, (8, 12, 20, 240), (0, 0, mr.width, mr.height), border_radius=12)
            surface.blit(temp_surf, (mr.x, mr.y))

            # Neon border
            pygame.draw.rect(surface, border_color, mr, 3, border_radius=12)

            # Cyber corners
            dec = int(10 * self.scale)
            pygame.draw.line(surface, border_color, (mr.x, mr.y), (mr.x + dec*2, mr.y), 4)
            pygame.draw.line(surface, border_color, (mr.x, mr.y), (mr.x, mr.y + dec*2), 4)
            pygame.draw.line(surface, border_color, (mr.right, mr.bottom), (mr.right - dec*2, mr.bottom), 4)
            pygame.draw.line(surface, border_color, (mr.right, mr.bottom), (mr.right, mr.bottom - dec*2), 4)

            # Header
            header_y = mr.top + int(35 * self.scale)
            self.draw_neon_text(surface, "CHI TIET TRAN DAU", self.font_med, (255, 235, 59), (mr.centerx, header_y), glow_radius=10, pulse=pulse)

            # Tag
            lbl_tag = self.font_tiny.render(tag_text, True, border_color)
            surface.blit(lbl_tag, (mr.right - lbl_tag.get_width() - int(20 * self.scale), mr.top + int(15 * self.scale)))

            # Divider
            pygame.draw.line(surface, (40, 50, 70), (mr.x + 30, mr.top + int(70 * self.scale)), (mr.right - 30, mr.top + int(70 * self.scale)), 1)

            # Metrics
            res_text = "THANG (VICTORY)" if res == "WIN" else "THUA (DEFEATED)"
            res_col = (0, 220, 120) if res == "WIN" else (255, 60, 60)
            details = [
                ("HANG (RANK):", f"#{self.selected_detail_rank}", (255, 215, 0) if self.selected_detail_rank <= 3 else (180, 200, 220)),
                ("TEN (NAME):", self.selected_detail.get("name", "ANON"), (220, 230, 255)),
                ("KET QUA (RESULT):", res_text, res_col),
                ("DIEM SO (SCORE):", f"{self.selected_detail.get('score', 0)} PTS", (255, 235, 59)),
                ("SO MA AN (GHOSTS):", f"{self.selected_detail.get('ghosts', 0)} / 4", (200, 200, 240)),
                ("THOI GIAN (TIME):", f"{self.selected_detail.get('time', '--')} ({self.selected_detail.get('elapsed', 0.0)}s)", (180, 200, 220)),
                ("BUOC DI (STEPS):", str(self.selected_detail.get("steps", 0)), (200, 220, 200)),
                ("SO LAN CUA (TURNS):", str(self.selected_detail.get("turns", 0)), (200, 220, 200)),
                ("BAN DO (MAP SIZE):", str(self.selected_detail.get("map_size", "N/A")), (160, 190, 220)),
                ("NGAY CHOI (DATE):", self.selected_detail.get("date", ""), (100, 120, 150))
            ]

            pacman_nodes = self.selected_detail.get("pacman_explored")
            pacman_nodes_str = f"{pacman_nodes} NUT" if pacman_nodes is not None else "N/A"
            details.append(("NUT DUYET PACMAN:", pacman_nodes_str, PACMAN_COLOR))
            
            ghost_explored = self.selected_detail.get("ghost_explored", {})
            if ghost_explored:
                for g_name, col in [("Blinky", BLINKY_COLOR), ("Pinky", PINKY_COLOR), ("Inky", INKY_COLOR), ("Clyde", CLYDE_COLOR)]:
                    val = ghost_explored.get(g_name)
                    val_str = f"{val} NUT" if val is not None else "N/A"
                    details.append((f"NUT DUYET {g_name.upper()}:", val_str, col))
            else:
                for g_name, col in [("Blinky", BLINKY_COLOR), ("Pinky", PINKY_COLOR), ("Inky", INKY_COLOR), ("Clyde", CLYDE_COLOR)]:
                    details.append((f"NUT DUYET {g_name.upper()}:", "N/A", col))

            item_spacing = int(26 * self.scale)
            start_content_y = mr.top + int(90 * self.scale)
            for idx, (label, val, val_col) in enumerate(details):
                cy = start_content_y + idx * item_spacing
                # Draw label
                lbl_surf = self.font_small.render(label, True, (0, 229, 255))
                surface.blit(lbl_surf, (mr.left + int(50 * self.scale), cy))
                # Draw value
                val_surf = self.font_small.render(val, True, val_col)
                surface.blit(val_surf, (mr.right - int(50 * self.scale) - val_surf.get_width(), cy))

            # Close button
            cbr = self._modal_close_rect()
            is_cb_hover = cbr.collidepoint(pygame.mouse.get_pos())
            pygame.draw.rect(surface, (20, 10, 10) if is_cb_hover else (10, 8, 12), cbr, border_radius=6)
            pygame.draw.rect(surface, (200, 80, 80) if is_cb_hover else (80, 50, 60), cbr, 2, border_radius=6)
            close_lbl = self.font_small.render("← QUAY LAI", True, (200, 80, 80) if is_cb_hover else (140, 90, 100))
            surface.blit(close_lbl, close_lbl.get_rect(center=cbr.center))
