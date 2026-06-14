import heapq
from collections import deque

def manhattan_distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def get_neighbors(node, grid, rows, cols):
    r, c = node
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] != 1:
            neighbors.append((nr, nc))
    return neighbors

class Pathfinding:
    @staticmethod
    def a_star_search(start, goal, grid, rows, cols, heuristic=None, cost_fn=None):
        if heuristic is None:
            heuristic = manhattan_distance
            
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {}
        cost_so_far = {}
        
        came_from[start] = None
        cost_so_far[start] = 0
        
        while frontier:
            _, current = heapq.heappop(frontier)
            
            if current == goal:
                break
                
            for next_node in get_neighbors(current, grid, rows, cols):
                step_cost = 1
                if cost_fn is not None:
                    step_cost = cost_fn(current, next_node)
                new_cost = cost_so_far[current] + step_cost
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + heuristic(next_node, goal)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current
                    
        return Pathfinding.reconstruct_path(start, goal, came_from)

    @staticmethod
    def greedy_bfs(start, goal, grid, rows, cols, heuristic=None):
        if heuristic is None:
            heuristic = manhattan_distance
            
        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {}
        came_from[start] = None
        
        while frontier:
            _, current = heapq.heappop(frontier)
            
            if current == goal:
                break
                
            for next_node in get_neighbors(current, grid, rows, cols):
                if next_node not in came_from:
                    priority = heuristic(next_node, goal)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current
                    
        return Pathfinding.reconstruct_path(start, goal, came_from)

    @staticmethod
    def dfs(start, goal, grid, rows, cols, depth_limit=15):
        stack = [(start, [start])]
        visited = set()
        
        best_path = [start]
        min_dist = float('inf')

        while stack:
            current, path = stack.pop()
            
            if current == goal:
                return path[1:]
                
            if len(path) > depth_limit:
                # Luu lai nut gan nhat neu dat gioi han
                dist = manhattan_distance(current, goal)
                if dist < min_dist:
                    min_dist = dist
                    best_path = path
                continue
                
            if current not in visited:
                visited.add(current)
                for next_node in get_neighbors(current, grid, rows, cols):
                    if next_node not in visited:
                        stack.append((next_node, path + [next_node]))
                        
        return best_path[1:]

    @staticmethod
    def bfs(start, goal, grid, rows, cols):
        frontier = deque()
        frontier.append(start)
        came_from = {}
        came_from[start] = None
        
        while frontier:
            current = frontier.popleft()
            
            if current == goal:
                break
                
            for next_node in get_neighbors(current, grid, rows, cols):
                if next_node not in came_from:
                    frontier.append(next_node)
                    came_from[next_node] = current
                    
        return Pathfinding.reconstruct_path(start, goal, came_from)

    @staticmethod
    def reconstruct_path(start, goal, came_from):
        if goal not in came_from:
            # Chua den dich (vd het thoi gian hoac bi chan, du ban do ket noi hoan toan)
            # Tim nut gan nhat da kham pha toi dich lam phuong an du phong
            closest = start
            min_dist = float('inf')
            for node in came_from:
                dist = manhattan_distance(node, goal)
                if dist < min_dist:
                    min_dist = dist
                    closest = node
            goal = closest
            
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    @staticmethod
    def get_clyde_target(blinky_pos, pacman_pos, grid, rows, cols):
        """Vector projection to trap Pacman between Blinky and Clyde."""
        # Vector tu Blinky den Pacman
        dr = pacman_pos[0] - blinky_pos[0]
        dc = pacman_pos[1] - blinky_pos[1]
        
        # Mo rong qua Pacman bang mot phan vector de giu Clyde gan hon
        target_r = pacman_pos[0] + int(dr * 0.5)
        target_c = pacman_pos[1] + int(dc * 0.5)
        
        # Gioi han trong ban do
        target_r = max(1, min(target_r, rows - 2))
        target_c = max(1, min(target_c, cols - 2))
        
        # Neu muc tieu la tuong, tim o duong di gan nhat bang BFS cuc bo (rat nhanh)
        if grid[target_r][target_c] == 1:
            queue = deque([(target_r, target_c)])
            visited = {(target_r, target_c)}
            while queue:
                r, c = queue.popleft()
                if grid[r][c] != 1:
                    return (r, c)
                for dr_step, dc_step in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr_step, c + dc_step
                    if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return pacman_pos
            
        return (target_r, target_c)
