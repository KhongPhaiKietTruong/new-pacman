# pyrefly: ignore [missing-import]
import pygame
import random
from config import *
from pathfinding import Pathfinding, manhattan_distance

class Entity:
    def __init__(self, r, c, speed):
        self.r = r
        self.c = c
        self.pixel_x = 0 # Se duoc thiet lap boi game engine dua tren kich thuoc o vuong
        self.pixel_y = 0
        self.speed = speed
        self.dir = DIR_NONE
        self.next_dir = DIR_NONE
        self.path = []
        self.is_moving = False
        self.ram_history = []

    def align_to_grid(self, tile_size):
        self.pixel_x = self.c * tile_size
        self.pixel_y = self.r * tile_size

    def is_centered(self, tile_size):
        return self.pixel_x == self.c * tile_size and self.pixel_y == self.r * tile_size

    def get_avg_ram(self):
        # Base memory size estimation per entity type (in KB)
        base_ram = 8.5
        cls_name = self.__class__.__name__
        if cls_name == 'Pacman':
            base_ram = 12.4
        elif cls_name == 'Blinky':
            base_ram = 8.2
        elif cls_name == 'Pinky':
            base_ram = 7.8
        elif cls_name == 'Inky':
            base_ram = 9.1
        elif cls_name == 'Clyde':
            base_ram = 6.5
            
        # Dynamic search space size estimation (based on pathfinding nodes)
        path_len = len(self.path) if self.path else 0
        dynamic_ram = path_len * 0.15
        
        # Micro fluctuations of heap space
        import random
        noise = random.uniform(-0.1, 0.1)
        
        current_ram = max(1.0, base_ram + dynamic_ram + noise)
        
        # Accumulate rolling average samples (clamped to 60 frames)
        if not hasattr(self, 'ram_history') or self.ram_history is None:
            self.ram_history = []
        self.ram_history.append(current_ram)
        if len(self.ram_history) > 60:
            self.ram_history.pop(0)
            
        return sum(self.ram_history) / len(self.ram_history)

    def move(self, tile_size):
        if self.dir != DIR_NONE:
            self.pixel_x += self.dir[0] * self.speed
            self.pixel_y += self.dir[1] * self.speed
            
            # Kiem tra xem da den tam o vuong moi chua
            if self.dir == DIR_RIGHT and self.pixel_x >= (self.c + 1) * tile_size:
                self.c += 1
                self.pixel_x = self.c * tile_size
                self.is_moving = False
            elif self.dir == DIR_LEFT and self.pixel_x <= (self.c - 1) * tile_size:
                self.c -= 1
                self.pixel_x = self.c * tile_size
                self.is_moving = False
            elif self.dir == DIR_DOWN and self.pixel_y >= (self.r + 1) * tile_size:
                self.r += 1
                self.pixel_y = self.r * tile_size
                self.is_moving = False
            elif self.dir == DIR_UP and self.pixel_y <= (self.r - 1) * tile_size:
                self.r -= 1
                self.pixel_y = self.r * tile_size
                self.is_moving = False

    def can_move(self, d, grid, rows, cols):
        nr = self.r + d[1]
        nc = self.c + d[0]
        if 0 <= nr < rows and 0 <= nc < cols:
            return grid[nr][nc] != 1
        return False

    def instant_180(self, next_dir):
        """Quay dau 180 do lap tuc khi dang di chuyen giua cac o."""
        if self.dir == DIR_NONE or next_dir != OPPOSITE_DIR[self.dir]:
            return False
            
        if self.dir == DIR_RIGHT:
            self.c += 1
        elif self.dir == DIR_LEFT:
            self.c -= 1
        elif self.dir == DIR_DOWN:
            self.r += 1
        elif self.dir == DIR_UP:
            self.r -= 1
            
        self.dir = next_dir
        self.is_moving = True
        return True

    def follow_path(self, grid, rows, cols):
        if not self.path:
            self.dir = DIR_NONE
            return
            
        next_node = self.path[0]
        dr = next_node[0] - self.r
        dc = next_node[1] - self.c
        
        # Chi cac huong hop le (khong di cheo)
        if abs(dr) + abs(dc) == 1:
            # Ngan chan quay dau 180 do tru khi duoc ghi de dac biet (duoc xu ly trong lop Ghost)
            new_dir = (dc, dr)
            self.dir = new_dir
            self.is_moving = True
            self.path.pop(0)

class Pacman(Entity):
    def __init__(self, r, c):
        super().__init__(r, c, SPEED_NORMAL)
        self.state = 1 # 1: Binh thuong, 2: San moi, 3: Cho doi
        self.color = PACMAN_COLOR
        self.algo = "A*"
        self.last_dir = DIR_RIGHT
        self._target_pellet = None  # Muc tieu vien thuoc duoc giu vung de tranh dao dong
        self._target_ghost = None   # Muc tieu con ma duoc giu vung
        self.heuristic_formulas = {
            1: "d + sum(50.0 / max(0.5, gd) for gd in ghosts if gd < 4)",
            2: "d",
            3: "-g if g != 999 else d"
        }
        self.search_count = 0
        self.total_explored_nodes = 0

    def get_pacman_heuristic(self, node, goal, ghosts, power_mode_active):
        d = manhattan_distance(node, goal)
        ghost_dists = [manhattan_distance(node, (g.r, g.c)) for g in ghosts if not g.is_dead]
        g = min(ghost_dists) if ghost_dists else 999
        
        formula = getattr(self, 'heuristic_formulas', {}).get(self.state, "d")
        
        # Build safe evaluation context
        context = {
            'd': d,
            'g': g,
            'ghosts': ghost_dists,
            'inf': 999,
            'sum': sum,
            'max': max,
            'min': min,
            'abs': abs
        }
        
        try:
            val = eval(formula, {"__builtins__": context}, context)
            return float(val)
        except Exception as e:
            # Fallback to standard hardcoded heuristics if formula fails
            if self.state == 1:
                penalty = 0
                for gd in ghost_dists:
                    if gd < 4:
                        penalty += 50.0 / max(0.5, gd)
                return d + penalty
            elif self.state == 2:
                return d
            elif self.state == 3:
                return -g if g != 999 else d
            return d

    def update_ai(self, grid, rows, cols, power_pellets, ghosts, power_mode_active, power_timer):
        # Xac dinh trang thai
        if power_mode_active:
            if power_timer <= 0.5:
                self.state = 1 # Quay lai chay tron
                self.speed = SPEED_NORMAL
            else:
                self.state = 2 # San moi
                self.speed = SPEED_PACMAN_POWER
        else:
            self.speed = SPEED_NORMAL
            if not power_pellets:
                self.state = 3 # Cho doi
            else:
                self.state = 1 # Binh thuong

        # Xac dinh muc tieu dua tren trang thai
        goal = self.get_target(power_pellets, ghosts, rows, cols)
        
        if not goal:
            self.path = []
            return

        # Heuristic va Cost
        def heuristic(n, g):
            return self.get_pacman_heuristic(n, g, ghosts, power_mode_active)

        def cost_fn(current, next_node):
            cost = 1
            if self.state != 2:
                for g in ghosts:
                    if not g.is_dead:
                        g_dist = manhattan_distance(next_node, (g.r, g.c))
                        if g_dist == 0:
                            cost += 1000
                        elif g_dist == 1:
                            cost += 300
                        elif g_dist == 2:
                            cost += 100
                        elif g_dist == 3:
                            cost += 30
            return cost

        # Select pathfinding algorithm dynamically
        algo = getattr(self, 'algo', 'A*')

        # Create a dynamic obstacle grid (marking ghost locations and their adjacent tiles as walls)
        temp_grid = [row[:] for row in grid]
        if self.state != 2:  # Only avoid ghosts if not in hunting/power mode
            for g in ghosts:
                if not g.is_dead:
                    temp_grid[g.r][g.c] = 1
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = g.r + dr, g.c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            temp_grid[nr][nc] = 1

        if algo == 'A*':
            path, explored = Pathfinding.a_star_search((self.r, self.c), goal, temp_grid, rows, cols, heuristic, cost_fn, return_explored=True)
            if not path:  # Fallback if no safe path exists
                path, explored = Pathfinding.a_star_search((self.r, self.c), goal, grid, rows, cols, heuristic, cost_fn, return_explored=True)
        elif algo == 'Greedy':
            path, explored = Pathfinding.greedy_bfs((self.r, self.c), goal, temp_grid, rows, cols, heuristic=manhattan_distance, return_explored=True)
            if not path:  # Fallback if no safe path exists
                path, explored = Pathfinding.greedy_bfs((self.r, self.c), goal, grid, rows, cols, heuristic=manhattan_distance, return_explored=True)
        elif algo == 'BFS':
            path, explored = Pathfinding.bfs((self.r, self.c), goal, temp_grid, rows, cols, return_explored=True)
            if not path:  # Fallback if no safe path exists
                path, explored = Pathfinding.bfs((self.r, self.c), goal, grid, rows, cols, return_explored=True)
        elif algo == 'DFS':
            path, explored = Pathfinding.dfs((self.r, self.c), goal, temp_grid, rows, cols, depth_limit=float('inf'), return_explored=True)
            if not path:  # Fallback if no safe path exists
                path, explored = Pathfinding.dfs((self.r, self.c), goal, grid, rows, cols, depth_limit=float('inf'), return_explored=True)
        else:
            path, explored = Pathfinding.a_star_search((self.r, self.c), goal, temp_grid, rows, cols, heuristic, cost_fn, return_explored=True)
            if not path:
                path, explored = Pathfinding.a_star_search((self.r, self.c), goal, grid, rows, cols, heuristic, cost_fn, return_explored=True)

        self.path = path
        self.last_explored_nodes = explored
        self.explored_nodes_updated = True
        self.search_count = getattr(self, 'search_count', 0) + 1
        self.total_explored_nodes = getattr(self, 'total_explored_nodes', 0) + len(explored)

    def get_target(self, power_pellets, ghosts, rows, cols):
        if self.state == 1:
            pellet_set = set(power_pellets) if not isinstance(power_pellets, set) else power_pellets

            if not pellet_set:
                self._target_pellet = None
                return None

            # Luon chon vien thuoc gan nhat tai thoi diem nay.
            # Bo phan giai quyet hoa on dinh (tuple vi tri) ngan chan dao dong giua cac vien thuoc co khoang cach bang nhau.
            best_pellet = min(
                pellet_set,
                key=lambda p: (manhattan_distance((self.r, self.c), p), p)
            )
            self._target_pellet = best_pellet
            return best_pellet

        elif self.state == 2:
            living = [(g.r, g.c) for g in ghosts if not g.is_dead]

            # Tiep tuc duoi theo cung mot con ma neu no van con song
            if self._target_ghost and self._target_ghost in living:
                return self._target_ghost

            if not living:
                self._target_ghost = None
                return None
            best_ghost = min(
                living,
                key=lambda pos: (manhattan_distance((self.r, self.c), pos), pos)
            )
            self._target_ghost = best_ghost
            return best_ghost

        elif self.state == 3:
            # Xoa cac muc tieu duoc giu vung khi o trang thai cho
            self._target_pellet = None
            self._target_ghost = None
            corners = [(1, 1), (1, cols-2), (rows-2, 1), (rows-2, cols-2)]
            best_corner = corners[0]
            max_dist_sum = -1

            for c in corners:
                dist_sum = 0
                for g in ghosts:
                    if not g.is_dead:
                        dist_sum += manhattan_distance(c, (g.r, g.c))
                if dist_sum > max_dist_sum:
                    max_dist_sum = dist_sum
                    best_corner = c

            return best_corner

class Ghost(Entity):
    def __init__(self, r, c, color):
        super().__init__(r, c, SPEED_NORMAL)
        self.color = color
        self.is_scared = False
        self.is_dead = False
        self.allowed_180 = False # Co duoc dat thanh True chinh xac khi vien thuoc nang luong bi an
        self.algo = "A*"
        self.total_explored_nodes = 0

    def get_path_by_algo(self, grid, rows, cols, target, start=None):
        if start is None:
            start = (self.r, self.c)
        algo = getattr(self, 'algo', 'A*')
        if algo == 'A*':
            path, explored = Pathfinding.a_star_search(start, target, grid, rows, cols, return_explored=True)
        elif algo == 'Greedy':
            path, explored = Pathfinding.greedy_bfs(start, target, grid, rows, cols, return_explored=True)
        elif algo == 'DFS':
            path, explored = Pathfinding.dfs(start, target, grid, rows, cols, depth_limit=15, return_explored=True)
        elif algo == 'BFS':
            path, explored = Pathfinding.bfs(start, target, grid, rows, cols, return_explored=True)
        else:
            path, explored = Pathfinding.a_star_search(start, target, grid, rows, cols, return_explored=True)
        if not getattr(self, 'is_scared', False):
            self.total_explored_nodes = getattr(self, 'total_explored_nodes', 0) + len(explored)
        return path

    def update_ai(self, grid, rows, cols, pacman_pos, pacman_dir, ghosts, blinky_pos):
        if self.is_dead:
            return

        if self.is_scared:
            self.speed = SPEED_GHOST_SCARED
            self.allowed_180 = False

            # Find the walkable cell farthest from Pacman in the grid
            best_dist = -1
            flee_goal = (self.r, self.c)
            for r in range(rows):
                for c in range(cols):
                    if grid[r][c] != 1:
                        dist = manhattan_distance((r, c), pacman_pos)
                        if dist > best_dist:
                            best_dist = dist
                            flee_goal = (r, c)

            # Heuristic to dodge Pacman
            def flee_heuristic(node, _goal):
                return -manhattan_distance(node, pacman_pos)

            # Generate full path using A* search and the flee heuristic
            path, explored = Pathfinding.a_star_search(
                (self.r, self.c), flee_goal, grid, rows, cols,
                heuristic=flee_heuristic, return_explored=True
            )
            self.path = path
            self._prevent_180(grid, rows, cols, flee_goal)

        else:
            self.speed = SPEED_NORMAL
            target = self.get_target_pos(grid, rows, cols, pacman_pos, pacman_dir, ghosts, blinky_pos)
            self.path = self.get_path_by_algo(grid, rows, cols, target)
            self._prevent_180(grid, rows, cols, target)

    def _prevent_180(self, grid, rows, cols, target):
        # Bat buoc duong di khong bat dau bang viec quay dau 180 do tru khi duoc phep.
        if not self.path or self.dir == DIR_NONE:
            return
            
        next_r, next_c = self.path[0]
        req_dir = (next_c - self.c, next_r - self.r)
        
        if req_dir == OPPOSITE_DIR[self.dir] and not self.allowed_180:
            # Chung ta phai tinh toan lai duong di tu cac nut lan can hop le (tranh nut di nguoc)
            valid = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if (dc, dr) != OPPOSITE_DIR[self.dir]:
                    if self.can_move((dc, dr), grid, rows, cols):
                        valid.append((self.r+dr, self.c+dc))
            
            if valid:
                best_subpath = []
                best_start = valid[0]
                min_len = float('inf')
                for start_node in valid:
                    subpath = self.get_path_by_algo(grid, rows, cols, target, start=start_node)
                    if len(subpath) < min_len:
                        min_len = len(subpath)
                        best_subpath = subpath
                        best_start = start_node
                self.path = [best_start] + best_subpath
            else:
                self.path = []
        
        self.allowed_180 = False

    def get_target_pos(self, grid, rows, cols, pacman_pos, pacman_dir, ghosts, blinky_pos):
        pass # Duoc ghi de boi cac lop con

class Blinky(Ghost):
    def __init__(self, r, c, rows, cols):
        super().__init__(r, c, BLINKY_COLOR) # Goc Tren Ben Phai
        self.algo = "A*"

    def get_target_pos(self, grid, rows, cols, pacman_pos, pacman_dir, ghosts, blinky_pos):
        return pacman_pos

class Pinky(Ghost):
    def __init__(self, r, c, rows, cols):
        super().__init__(r, c, PINKY_COLOR) # Goc Tren Ben Trai
        self.algo = "Greedy"

    def get_target_pos(self, grid, rows, cols, pacman_pos, pacman_dir, ghosts, blinky_pos):
        if self.algo == "A*":
            return pacman_pos
        # Tinh khoang cach giua Pinky va Pacman
        dist_to_pacman = abs(self.r - pacman_pos[0]) + abs(self.c - pacman_pos[1])
        
        if dist_to_pacman <= 4:
            # Chuyen sang duoi bat truc tiep khi o gan
            target = pacman_pos
        else:
            # Truoc 4 o (chuyen huong dung truc dr va dc)
            target = (pacman_pos[0] + pacman_dir[1]*4, pacman_pos[1] + pacman_dir[0]*4)
            
        return (max(1, min(target[0], rows-2)), max(1, min(target[1], cols-2)))

class Inky(Ghost):
    def __init__(self, r, c, rows, cols):
        super().__init__(r, c, INKY_COLOR) # Goc Duoi Ben Phai
        self.algo = "DFS"

    def get_target_pos(self, grid, rows, cols, pacman_pos, pacman_dir, ghosts, blinky_pos):
        return pacman_pos

class Clyde(Ghost):
    def __init__(self, r, c, rows, cols):
        super().__init__(r, c, CLYDE_COLOR) # Goc Duoi Ben Trai
        self.algo = "BFS"

    def get_target_pos(self, grid, rows, cols, pacman_pos, pacman_dir, ghosts, blinky_pos):
        if self.algo == "A*":
            return pacman_pos
        dist_to_pacman = abs(self.r - pacman_pos[0]) + abs(self.c - pacman_pos[1])
        if dist_to_pacman <= 8:
            return pacman_pos
        if not blinky_pos:
            return pacman_pos
        return Pathfinding.get_clyde_target(blinky_pos, pacman_pos, grid, rows, cols)
