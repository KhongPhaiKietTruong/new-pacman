"""
map_editor.py — Cyberpunk in-game map editor for Pacman.

Grid cell values:
  0 = empty path
  1 = wall
  2 = power pellet
  3 = Pacman spawn (exactly 1)
  4 = ghost spawn  (up to 4)
"""

import pygame
import math
import random
from config import *

# ─── Bang mau ──────────────────────────────────────────────────────────
COL_BG          = (8, 10, 14)
COL_GRID_LINE   = (25, 30, 40)
COL_WALL        = (0, 229, 255)       # xanh lo
COL_PATH        = (18, 22, 30)
COL_PELLET      = (255, 255, 255)
COL_PACMAN_CELL = (255, 235, 59)      # yellow
COL_GHOST_CELL  = [
    (255, 0, 85),    # Blinky do
    (255, 102, 204), # Pinky hong
    (0, 204, 255),   # Inky xanh duong
    (255, 153, 0),   # Clyde cam
]
COL_PANEL       = (12, 14, 20)
COL_PANEL_BORDER= (0, 229, 255)
COL_TEXT        = (220, 220, 240)
COL_ACTIVE_TOOL = (255, 235, 59)
COL_HOVER       = (0, 200, 220)
COL_ERROR       = (255, 50, 50)
COL_OK          = (0, 220, 120)

# ─── ID Cong cu ────────────────────────────────────────────────────────────────
TOOL_WALL    = "WALL"
TOOL_ERASE   = "ERASE"
TOOL_PELLET  = "PELLET"
TOOL_PACMAN  = "PACMAN"
TOOL_GHOST   = "GHOST"

DEFAULT_COLS = 25
DEFAULT_ROWS = 21


class MapEditor:
    """Full-featured in-game map editor."""

    def __init__(self, screen_width, screen_height):
        self.screen_w = screen_width
        self.screen_h = screen_height

        # Font chu
        font_path = "assets/PressStart2P-Regular.ttf"
        try:
            self.font_med   = pygame.font.Font(font_path, 16)
            self.font_small = pygame.font.Font(font_path, 11)
            self.font_tiny  = pygame.font.Font(font_path, 9)
        except Exception:
            self.font_med   = pygame.font.SysFont("monospace", 22, bold=True)
            self.font_small = pygame.font.SysFont("monospace", 16, bold=True)
            self.font_tiny  = pygame.font.SysFont("monospace", 12, bold=True)

        # Chieu rong bang thanh cong cu ben phai
        self.panel_w = 260
        self.grid_area_w = screen_width - self.panel_w

        # Trang thai trinh bien tap
        self.cols = DEFAULT_COLS
        self.rows = DEFAULT_ROWS
        self._init_grid()

        self.tool        = TOOL_WALL
        self.painting    = False          # Nhan giu chuot trai
        self.erasing     = False          # Nhan giu chuot phai
        self.paint_value = 1              # gia tri dang duoc ve

        # Camera/pan
        self.cam_x  = 0.0
        self.cam_y  = 0.0
        self.zoom   = 1.0                 # He so nhan tile_size

        # Kich thuoc o vuong co ban vua voi vung luoi
        self._update_tile_size()

        # Hover / trang thai
        self.hover_cell  = None           # (r, c) duoi con tro
        self.status_msg  = ""
        self.status_ok   = True
        self.status_timer= 0.0

        # Hanh dong de quay lai vong lap chinh
        self._action = None               # "play" | "back"
        self._play_data = None            # tuple ket qua khi action=="play"

        # Danh sach nut thanh cong cu duoc xay dung truoc
        self._build_toolbar()

    # ── Trinh ho tro Luoi ─────────────────────────────────────────────────────────

    def _init_grid(self):
        """Reset to a mostly-walled grid with open border paths."""
        self.grid = [[1] * self.cols for _ in range(self.rows)]
        # Mo cac hang tren + duoi va cac cot trai + phai lam duong bien
        for c in range(self.cols):
            self.grid[0][c] = 1
            self.grid[self.rows - 1][c] = 1
        for r in range(self.rows):
            self.grid[r][0] = 1
            self.grid[r][self.cols - 1] = 1
        # Dao mot duong di ban dau don gian de no khong phai la mot buc tuong trong
        for r in range(1, self.rows - 1):
            for c in range(1, self.cols - 1):
                self.grid[r][c] = 0
        # Them lai mot so buc tuong theo dang luoi don gian lam mau
        for r in range(2, self.rows - 1, 4):
            for c in range(2, self.cols - 1, 4):
                self.grid[r][c] = 1
        # Dat diem xuat phat mac dinh cua pacman o trung tam
        pr, pc = self.rows // 2, self.cols // 2
        self.grid[pr][pc] = 3
        # Diem xuat phat mac dinh cua con ma o cac goc
        for gr, gc in [(1, 1), (1, self.cols-2), (self.rows-2, 1), (self.rows-2, self.cols-2)]:
            if self.grid[gr][gc] != 3:
                self.grid[gr][gc] = 4
        # Cac vien thuoc nang luong mac dinh gan cac goc
        for pr2, pc2 in [(2, 2), (2, self.cols-3), (self.rows-3, 2), (self.rows-3, self.cols-3)]:
            if self.grid[pr2][pc2] == 0:
                self.grid[pr2][pc2] = 2

    def _update_tile_size(self):
        """Compute tile size to fit the grid in the left panel."""
        max_tw = (self.grid_area_w - 20) // self.cols
        max_th = (self.screen_h - 20) // self.rows
        base = max(8, min(max_tw, max_th))
        self.base_tile = base
        self.tile_size = int(base * self.zoom)
        # Canh giua luoi o khu vuc ben trai
        self._recenter()

    def _recenter(self):
        grid_px_w = self.tile_size * self.cols
        grid_px_h = self.tile_size * self.rows
        self.cam_x = (self.grid_area_w - grid_px_w) // 2
        self.cam_y = (self.screen_h - grid_px_h) // 2

    # ── Thanh Cong Cu ──────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        """Build a list of toolbar button descriptors."""
        px = self.grid_area_w + 20
        py = 60
        bw = self.panel_w - 40
        bh = 44
        gap = 12

        self.toolbar = []
        tools = [
            (TOOL_WALL,   "TUONG",         "Dat tuong"),
            (TOOL_ERASE,  "XOA",        "Xoa o"),
            (TOOL_PELLET, "VIEN NANG LUONG", "Dat diem vien"),
            (TOOL_PACMAN, "PACMAN SPAWN", "Thiet lap vi tri bat dau"),
            (TOOL_GHOST,  "MA SPAWN",  "Thiet lap vi tri ma"),
        ]
        for tid, label, tip in tools:
            self.toolbar.append({
                "type": "tool",
                "id": tid,
                "label": label,
                "tip": tip,
                "rect": pygame.Rect(px, py, bw, bh),
            })
            py += bh + gap

        py += 10  # khoang cach phan chia

        # Dieu khien kich thuoc luoi
        self.toolbar.append({
            "type": "label", "label": "KICH THUOC LUOI", "rect": pygame.Rect(px, py, bw, 22)
        })
        py += 28
        btn_w3 = (bw - 8) // 3
        self.toolbar.append({
            "type": "action", "id": "cols-",
            "label": "R-", "rect": pygame.Rect(px, py, btn_w3, 36)
        })
        self.toolbar.append({
            "type": "action", "id": "cols+",
            "label": "R+", "rect": pygame.Rect(px + btn_w3 + 4, py, btn_w3, 36)
        })
        self.toolbar.append({
            "type": "action", "id": "rows+",
            "label": "C+", "rect": pygame.Rect(px + (btn_w3 + 4) * 2, py, btn_w3, 36)
        })
        py += 44
        self.toolbar.append({
            "type": "action", "id": "rows-",
            "label": "C-", "rect": pygame.Rect(px, py, btn_w3, 36)
        })
        py += 50

        # Thu phong
        self.toolbar.append({
            "type": "label", "label": "THU PHONG", "rect": pygame.Rect(px, py, bw, 22)
        })
        py += 28
        self.toolbar.append({
            "type": "action", "id": "zoom-",
            "label": "THU PHONG -", "rect": pygame.Rect(px, py, (bw - 8) // 2, 36)
        })
        self.toolbar.append({
            "type": "action", "id": "zoom+",
            "label": "THU PHONG +", "rect": pygame.Rect(px + (bw - 8) // 2 + 8, py, (bw - 8) // 2, 36)
        })
        py += 50

        # Nut xoa sach
        self.toolbar.append({
            "type": "action", "id": "clear",
            "label": "XOA TAT CA", "rect": pygame.Rect(px, py, bw, bh)
        })
        py += bh + gap

        # Dien day tuong xung quanh bien
        self.toolbar.append({
            "type": "action", "id": "fill_border",
            "label": "VIEN BIEN", "rect": pygame.Rect(px, py, bw, bh)
        })
        py += bh + 24

        # Nut PLAY (o duoi cung cua bang)
        play_y = self.screen_h - 140
        self.toolbar.append({
            "type": "action", "id": "play",
            "label": "▶ CHOI BAN DO", "rect": pygame.Rect(px, play_y, bw, 52)
        })
        self.toolbar.append({
            "type": "action", "id": "back",
            "label": "← QUAY LAI", "rect": pygame.Rect(px, play_y + 64, bw, 44)
        })

    # ── Trinh ho tro O vuong ─────────────────────────────────────────────────────────

    def _cell_at(self, mx, my):
        """Return (r, c) for a screen pixel, or None if out of grid."""
        gx = mx - self.cam_x
        gy = my - self.cam_y
        if gx < 0 or gy < 0:
            return None
        c = int(gx // self.tile_size)
        r = int(gy // self.tile_size)
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return (r, c)
        return None

    def _count(self, val):
        return sum(1 for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == val)

    def _ghost_index(self):
        """Return number of ghost spawns already placed (0-3)."""
        return self._count(4)

    def _paint_cell(self, r, c, value):
        """Paint a cell, enforcing uniqueness rules."""
        cur = self.grid[r][c]
        if value == 3:  # Pacman spawn — only one allowed
            # Remove any existing spawn
            for rr in range(self.rows):
                for cc in range(self.cols):
                    if self.grid[rr][cc] == 3:
                        self.grid[rr][cc] = 0
        elif value == 4:  # Ghost spawn — max 4
            if cur != 4 and self._count(4) >= 4:
                self._show_status("Toi da 4 vi tri ma xuat phat!", ok=False)
                return
        self.grid[r][c] = value

    def _show_status(self, msg, ok=True):
        self.status_msg   = msg
        self.status_ok    = ok
        self.status_timer = 3.0

    # ── Kiem Tra Hop Le ───────────────────────────────────────────────────────────

    def _validate(self):
        """Returns (ok, error_message). Also returns play data if ok."""
        # 1. Check Pacman spawn
        pacman_cells = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == 3]
        if len(pacman_cells) != 1:
            return False, "Can chinh xac 1 o PACMAN SPAWN"

        # 2. Check ghost spawns
        ghost_cells = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == 4]
        if len(ghost_cells) == 0:
            return False, "Can it nhat 1 o GHOST SPAWN"

        # 3. Check at least 1 power pellet
        pellet_cells = [(r, c) for r in range(self.rows) for c in range(self.cols) if self.grid[r][c] == 2]
        if len(pellet_cells) == 0:
            return False, "Can it nhat 1 VIEN NANG LUONG"

        # 4. Reachability: flood fill from Pacman spawn through non-wall cells
        pr, pc = pacman_cells[0]
        visited = [[False] * self.cols for _ in range(self.rows)]
        stack = [(pr, pc)]
        visited[pr][pc] = True
        while stack:
            rr, cc = stack.pop()
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = rr+dr, cc+dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and not visited[nr][nc]:
                    if self.grid[nr][nc] != 1:  # khong phai tuong
                        visited[nr][nc] = True
                        stack.append((nr, nc))

        # Check all ghost spawns are reachable
        for gr, gc in ghost_cells:
            if not visited[gr][gc]:
                return False, "Ma khong the tiep can tu vi tri Pacman!"

        # Check all pellets are reachable
        for pr2, pc2 in pellet_cells:
            if not visited[pr2][pc2]:
                return False, "Vien nang luong khong the tiep can tu Pacman!"

        return True, "Hop le"

    def _build_play_grid(self):
        """Return a copy of the grid with cell-3 and cell-4 converted to 0."""
        g = [row[:] for row in self.grid]
        pacman_pos = None
        ghost_positions = []
        for r in range(self.rows):
            for c in range(self.cols):
                if g[r][c] == 3:
                    pacman_pos = (r, c)
                    g[r][c] = 0
                elif g[r][c] == 4:
                    ghost_positions.append((r, c))
                    g[r][c] = 0
        return g, pacman_pos, ghost_positions

    # ── Thay doi kich thuoc luoi ──────────────────────────────────────────────────────────

    def _resize_grid(self, new_cols, new_rows):
        new_cols = max(15, min(55, new_cols))
        new_rows = max(15, min(35, new_rows))
        new_grid = [[1] * new_cols for _ in range(new_rows)]
        for r in range(min(self.rows, new_rows)):
            for c in range(min(self.cols, new_cols)):
                new_grid[r][c] = self.grid[r][c]
        self.cols = new_cols
        self.rows = new_rows
        self.grid = new_grid
        self._update_tile_size()
        self._build_toolbar()

    # ── API Cong khai ───────────────────────────────────────────────────────────

    def poll_action(self):
        """Call from main loop. Returns ("play", grid, rows, cols, pacman_pos, ghost_positions)
        or ("back", ...) or None."""
        if self._action == "play" and self._play_data:
            result = ("play", *self._play_data)
            self._action = None
            return result
        if self._action == "back":
            self._action = None
            return ("back",)
        return None

    def handle_event(self, event, mouse_pos):
        mx, my = mouse_pos

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Kiem tra thanh cong cu truoc
            for btn in self.toolbar:
                if btn["rect"].collidepoint(mx, my):
                    self._handle_toolbar_click(btn)
                    return

            # Ve luoi
            if mx < self.grid_area_w:
                cell = self._cell_at(mx, my)
                if cell:
                    r, c = cell
                    if event.button == 1:
                        self.painting = True
                        val = self._tool_value()
                        self._paint_cell(r, c, val)
                    elif event.button == 3:
                        self.erasing = True
                        if self.grid[r][c] != 1:
                            self.grid[r][c] = 0

        elif event.type == pygame.MOUSEBUTTONUP:
            self.painting = False
            self.erasing  = False

        elif event.type == pygame.MOUSEMOTION:
            if mx < self.grid_area_w:
                self.hover_cell = self._cell_at(mx, my)
                if self.painting and self.hover_cell:
                    r, c = self.hover_cell
                    val = self._tool_value()
                    # Khong keo ve cac ky hieu duy nhat
                    if val not in (3, 4):
                        self._paint_cell(r, c, val)
                    else:
                        self._paint_cell(r, c, val)
                elif self.erasing and self.hover_cell:
                    r, c = self.hover_cell
                    if self.grid[r][c] != 1:
                        self.grid[r][c] = 0
            else:
                self.hover_cell = None

        elif event.type == pygame.MOUSEWHEEL:
            if mx < self.grid_area_w:
                # Thu phong bang banh xe cuon chuot
                old_zoom = self.zoom
                self.zoom = max(0.5, min(4.0, self.zoom + event.y * 0.1))
                self.tile_size = int(self.base_tile * self.zoom)
                self._recenter()

        elif event.type == pygame.KEYDOWN:
            # Phim tat ban phim
            keymap = {
                pygame.K_1: TOOL_WALL,
                pygame.K_2: TOOL_ERASE,
                pygame.K_3: TOOL_PELLET,
                pygame.K_4: TOOL_PACMAN,
                pygame.K_5: TOOL_GHOST,
            }
            if event.key in keymap:
                self.tool = keymap[event.key]
            elif event.key == pygame.K_ESCAPE:
                self._action = "back"

    def _handle_toolbar_click(self, btn):
        if btn["type"] == "tool":
            self.tool = btn["id"]
        elif btn["type"] == "action":
            aid = btn["id"]
            if aid == "clear":
                self._init_grid()
                self._update_tile_size()
                self._show_status("Da xoa luoi.")
            elif aid == "fill_border":
                for c in range(self.cols):
                    self.grid[0][c] = 1
                    self.grid[self.rows-1][c] = 1
                for r in range(self.rows):
                    self.grid[r][0] = 1
                    self.grid[r][self.cols-1] = 1
                self._show_status("Da vien bien.")
            elif aid == "cols-":
                self._resize_grid(self.cols - 2, self.rows)
            elif aid == "cols+":
                self._resize_grid(self.cols + 2, self.rows)
            elif aid == "rows-":
                self._resize_grid(self.cols, self.rows - 2)
            elif aid == "rows+":
                self._resize_grid(self.cols, self.rows + 2)
            elif aid == "zoom-":
                self.zoom = max(0.5, self.zoom - 0.2)
                self.tile_size = int(self.base_tile * self.zoom)
                self._recenter()
            elif aid == "zoom+":
                self.zoom = min(4.0, self.zoom + 0.2)
                self.tile_size = int(self.base_tile * self.zoom)
                self._recenter()
            elif aid == "play":
                ok, msg = self._validate()
                if ok:
                    play_grid, pacman_pos, ghost_positions = self._build_play_grid()
                    self._play_data = (play_grid, self.rows, self.cols, pacman_pos, ghost_positions)
                    self._action = "play"
                else:
                    self._show_status(msg, ok=False)
            elif aid == "back":
                self._action = "back"

    def _tool_value(self):
        return {
            TOOL_WALL:   1,
            TOOL_ERASE:  0,
            TOOL_PELLET: 2,
            TOOL_PACMAN: 3,
            TOOL_GHOST:  4,
        }[self.tool]

    def update(self, dt):
        if self.status_timer > 0:
            self.status_timer = max(0, self.status_timer - dt)

    # ── Ve ──────────────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(COL_BG)
        self._draw_grid(surface)
        self._draw_panel(surface)
        self._draw_status_bar(surface)

    def _draw_grid(self, surface):
        ts = self.tile_size
        cx, cy = int(self.cam_x), int(self.cam_y)

        # Gioi han viec ve trong vung luoi
        clip_rect = pygame.Rect(0, 0, self.grid_area_w, self.screen_h)
        surface.set_clip(clip_rect)

        for r in range(self.rows):
            for c in range(self.cols):
                x = cx + c * ts
                y = cy + r * ts
                if x + ts < 0 or x > self.grid_area_w or y + ts < 0 or y > self.screen_h:
                    continue  # Loai bo cac o ngoai man hinh

                cell = self.grid[r][c]
                rect = pygame.Rect(x, y, ts, ts)

                # To mau o
                if cell == 1:
                    # Tuong: ve lap day voi duong vien neon xanh lo
                    pygame.draw.rect(surface, (0, 50, 70), rect)
                    pygame.draw.rect(surface, COL_WALL, rect, max(1, ts // 8))
                elif cell == 0:
                    pygame.draw.rect(surface, COL_PATH, rect)
                elif cell == 2:
                    pygame.draw.rect(surface, COL_PATH, rect)
                    # Diem vien thuoc nang luong
                    pr = max(2, ts // 4)
                    pygame.draw.circle(surface, COL_PELLET, rect.center, pr)
                    pygame.draw.circle(surface, (180, 180, 255), rect.center, max(1, pr - 2))
                elif cell == 3:
                    pygame.draw.rect(surface, (40, 35, 5), rect)
                    # Bieu tuong Pacman (hinh tron vang lap day co mieng)
                    cr = max(2, ts // 2 - 2)
                    pygame.draw.circle(surface, COL_PACMAN_CELL, rect.center, cr)
                elif cell == 4:
                    # Diem xuat phat con ma — to mau theo chi so
                    gi = 0
                    idx = 0
                    for rr in range(self.rows):
                        for cc in range(self.cols):
                            if self.grid[rr][cc] == 4:
                                if rr == r and cc == c:
                                    gi = idx
                                idx += 1
                    pygame.draw.rect(surface, (20, 5, 5), rect)
                    cr = max(2, ts // 2 - 2)
                    gcol = COL_GHOST_CELL[gi % 4]
                    pygame.draw.circle(surface, gcol, rect.center, cr)

                # Duong luoi
                pygame.draw.rect(surface, COL_GRID_LINE, rect, 1)

        # Noi bat khi hover
        if self.hover_cell:
            r, c = self.hover_cell
            x = cx + c * ts
            y = cy + r * ts
            hover_surf = pygame.Surface((ts, ts), pygame.SRCALPHA)
            hover_surf.fill((255, 255, 255, 40))
            surface.blit(hover_surf, (x, y))
            pygame.draw.rect(surface, (255, 255, 100), (x, y, ts, ts), 2)

        surface.set_clip(None)

        # Vien luoi
        gw = self.cols * ts
        gh = self.rows * ts
        pygame.draw.rect(surface, COL_WALL,
                         (cx - 2, cy - 2, gw + 4, gh + 4), 2)

    def _draw_panel(self, surface):
        # Nen cua bang
        panel_rect = pygame.Rect(self.grid_area_w, 0, self.panel_w, self.screen_h)
        pygame.draw.rect(surface, COL_PANEL, panel_rect)
        pygame.draw.line(surface, COL_PANEL_BORDER,
                         (self.grid_area_w, 0), (self.grid_area_w, self.screen_h), 3)

        t_now = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(t_now * 3) + 1) / 2

        # Tieu de
        title = self.font_med.render("TRINH BIEN TAP BAN DO", True, COL_ACTIVE_TOOL)
        surface.blit(title, (self.grid_area_w + 20, 18))

        mouse_pos = pygame.mouse.get_pos()

        for btn in self.toolbar:
            rect = btn["rect"]
            if not rect:
                continue

            btype = btn["type"]
            if btype == "label":
                lbl = self.font_tiny.render(btn["label"], True, (120, 130, 160))
                surface.blit(lbl, (rect.x, rect.y))
                continue

            is_hovered = rect.collidepoint(mouse_pos)
            is_active  = (btype == "tool" and btn["id"] == self.tool)

            # Nen cua nut
            if is_active:
                bg_col = (30, 40, 20)
                border_col = COL_ACTIVE_TOOL
                text_col   = COL_ACTIVE_TOOL
                bw = 2 + int(pulse * 2)
            elif btn.get("id") == "play":
                bg_col = (10, 50, 20) if not is_hovered else (15, 70, 30)
                border_col = COL_OK
                text_col   = COL_OK
                bw = 2
            elif btn.get("id") == "back":
                bg_col = (30, 10, 10) if not is_hovered else (50, 15, 15)
                border_col = (180, 60, 60)
                text_col   = (200, 80, 80)
                bw = 2
            elif is_hovered:
                bg_col = (20, 30, 40)
                border_col = COL_HOVER
                text_col   = COL_HOVER
                bw = 2
            else:
                bg_col = (15, 18, 24)
                border_col = (40, 55, 70)
                text_col   = COL_TEXT
                bw = 1

            pygame.draw.rect(surface, bg_col, rect)
            pygame.draw.rect(surface, border_col, rect, bw)

            lbl = self.font_tiny.render(btn["label"], True, text_col)
            surface.blit(lbl, lbl.get_rect(center=rect.center))

        # Phan thong tin: so luong o
        info_y = self.screen_h - 270
        counts = [
            (f"TUONG:    {self._count(1)}", COL_WALL),
            (f"DIEM:  {self._count(2)}", COL_PELLET),
            (f"LUOI: {self.cols}x{self.rows}", (150, 150, 200)),
        ]
        pygame.draw.line(surface, (30, 40, 55),
                         (self.grid_area_w + 10, info_y - 10),
                         (self.screen_w - 10, info_y - 10), 1)
        for i, (txt, col) in enumerate(counts):
            lbl = self.font_tiny.render(txt, True, col)
            surface.blit(lbl, (self.grid_area_w + 20, info_y + i * 20))

        # Goi y phim tat ban phim
        hints = [
            "1=TUONG  2=XOA",
            "3=DIEM 4=PAC",
            "5=MA  CUON=ZOOM",
        ]
        hy = self.screen_h - 195
        pygame.draw.line(surface, (30, 40, 55),
                         (self.grid_area_w + 10, hy - 8),
                         (self.screen_w - 10, hy - 8), 1)
        for i, h in enumerate(hints):
            lbl = self.font_tiny.render(h, True, (70, 80, 100))
            surface.blit(lbl, (self.grid_area_w + 12, hy + i * 18))

    def _draw_status_bar(self, surface):
        if self.status_timer <= 0 and not self.hover_cell:
            return

        bar_h = 36
        bar_rect = pygame.Rect(0, self.screen_h - bar_h, self.grid_area_w, bar_h)
        pygame.draw.rect(surface, (10, 12, 18), bar_rect)
        pygame.draw.line(surface, COL_PANEL_BORDER,
                         (0, self.screen_h - bar_h),
                         (self.grid_area_w, self.screen_h - bar_h), 1)

        msg = ""
        col = COL_TEXT
        if self.status_timer > 0:
            col = COL_OK if self.status_ok else COL_ERROR
            msg = self.status_msg
        elif self.hover_cell:
            r, c = self.hover_cell
            cell = self.grid[r][c]
            names = {0: "DUONG DI", 1: "TUONG", 2: "DIEM VIEN", 3: "PACMAN SPAWN", 4: "GHOST SPAWN"}
            msg = f"[{r},{c}]  {names.get(cell,'?')}   CONG CU: {self.tool}"

        lbl = self.font_tiny.render(msg, True, col)
        surface.blit(lbl, (12, self.screen_h - bar_h + 10))
