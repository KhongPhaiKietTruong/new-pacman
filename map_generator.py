import random
from config import *

class MapGenerator:
    @staticmethod
    def generate_map(complexity, map_size):
        """
        Generates a 2D map. 
        complexity: float (0.0 to 1.0). 
        map_size: float (0.0 to 1.0).
        """
        # Xac dinh kich thuoc luoi dua tren map_size
        cols = MIN_GRID_COLS + int((MAX_GRID_COLS - MIN_GRID_COLS) * map_size)
        rows = MIN_GRID_ROWS + int((MAX_GRID_ROWS - MIN_GRID_ROWS) * map_size)
        
        # Dam bao cac chieu la so le de tao me cung
        if cols % 2 == 0: cols += 1
        if rows % 2 == 0: rows += 1
            
        # Khoi tao ban do voi tuong (1)
        grid = [[1 for _ in range(cols)] for _ in range(rows)]
        
        # Tao me cung (Recursive Backtracker)
        # Duong di la (0)
        def carve(r, c):
            grid[r][c] = 0
            # Cac huong: Len, Xuong, Trai, Phai
            dirs = [(0, -2), (0, 2), (-2, 0), (2, 0)]
            random.shuffle(dirs)
            
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 1 <= nr < rows - 1 and 1 <= nc < cols - 1 and grid[nr][nc] == 1:
                    # Dao thong qua tuong
                    grid[r + dr//2][c + dc//2] = 0
                    carve(nr, nc)
                    
        # Bat dau dao tu (1, 1)
        carve(1, 1)
        
        # Mot me cung nghiem ngat khong co vong lap (chi co 1 duong giua 2 diem bat ky). 
        # Chung ta muon pha vo cac buc tuong dai de lam chung ngan hon va it ket noi hon,
        # nhung tranh tao ra khong gian trong lon bang cach khong xoa tuong tao ra vung trong 2x2.
        # loop_chance xac dinh ty le xoa tuong de tao vong lap (lam me cung don gian/it phuc tap hon)
        loop_chance = 0.75 - (0.5 * complexity) # 0.75 o do phuc tap 0 (sieu don gian), 0.25 o do phuc tap 1
        for r in range(1, rows - 1):
            for c in range(1, cols - 1):
                if grid[r][c] == 1:
                    # Dem cac buc tuong lan can
                    wall_neighbors = 0
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        if grid[r+dr][c+dc] == 1:
                            wall_neighbors += 1
                            
                    # Chi loai bo tuong neu no ket noi cac duong di va la mot phan cua cau truc tuong dai hon
                    if wall_neighbors >= 2:
                        if (grid[r-1][c] == 0 and grid[r+1][c] == 0) or (grid[r][c-1] == 0 and grid[r][c+1] == 0):
                            # Dam bao chung ta khong tao ra vung duong di 2x2 (so 0)
                            creates_empty_space = False
                            if (grid[r-1][c-1] == 0 and grid[r-1][c] == 0 and grid[r][c-1] == 0) or \
                               (grid[r-1][c] == 0 and grid[r-1][c+1] == 0 and grid[r][c+1] == 0) or \
                               (grid[r][c-1] == 0 and grid[r+1][c-1] == 0 and grid[r+1][c] == 0) or \
                               (grid[r][c+1] == 0 and grid[r+1][c] == 0 and grid[r+1][c+1] == 0):
                                creates_empty_space = True
                                
                            if not creates_empty_space:
                                if random.random() < loop_chance:
                                    grid[r][c] = 0
                            
        # Dam bao 4 diem xuat phat cua con ma o goc la duong di
        spawn_points = [
            (1, 1),
            (1, cols-2),
            (rows-2, 1),
            (rows-2, cols-2)
        ]
        for sr, sc in spawn_points:
            grid[sr][sc] = 0
            
        # Dat 4 vien thuoc nang luong ban dau (2) o cac vi tri duong di ngau nhien quanh moi vung goc
        corner_regions = [
            ((1, 1), range(1, 6), range(1, 6)),
            ((1, cols-2), range(1, 6), range(cols - 6, cols - 1)),
            ((rows-2, 1), range(rows - 6, rows - 1), range(1, 6)),
            ((rows-2, cols-2), range(rows - 6, rows - 1), range(cols - 6, cols - 1))
        ]
        for spawn_pt, r_range, c_range in corner_regions:
            candidates = []
            for r in r_range:
                for c in c_range:
                    if grid[r][c] == 0 and (r, c) != spawn_pt:
                        candidates.append((r, c))
            if candidates:
                pr, pc = random.choice(candidates)
                grid[pr][pc] = 2
            else:
                grid[spawn_pt[0]][spawn_pt[1]] = 2
        
        # Phan trung tam duoc dam bao la duong di vi toa do cua no la so le.
        # Dieu nay ngan chan viec pha vo cau truc me cung hoac tao ra cac vung trong 2x2.
        
        return grid, cols, rows

    @staticmethod
    def spawn_power_pellet(grid, cols, rows):
        # Tao ra chinh xac 1 vien thuoc nang luong tren o duong di hop le (0).
        empty_tiles = []
        for r in range(rows):
            for c in range(cols):
                if grid[r][c] == 0:
                    empty_tiles.append((r, c))
                    
        if empty_tiles:
            r, c = random.choice(empty_tiles)
            grid[r][c] = 2
            return True
        return False
