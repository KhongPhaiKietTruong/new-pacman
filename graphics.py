import pygame
import random
import math
from config import *

class Particle:
    def __init__(self, x, y, color, speed_range, size_range, lifetime_range, angle=None):
        self.x = x
        self.y = y
        self.color = color
        
        if angle is None:
            angle = random.uniform(0, math.pi * 2)
            
        speed = random.uniform(*speed_range)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        
        self.size = random.uniform(*size_range)
        self.lifetime = random.uniform(*lifetime_range)
        self.max_lifetime = self.lifetime
        self.alpha = 255

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= dt
        if self.lifetime > 0:
            self.alpha = int((self.lifetime / self.max_lifetime) * 255)
            
    def draw(self, surface):
        if self.lifetime > 0:
            s = pygame.Surface((int(self.size), int(self.size)), pygame.SRCALPHA)
            s.fill((*self.color[:3], self.alpha))
            surface.blit(s, (int(self.x), int(self.y)))

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=10, speed_range=(1, 5), size_range=(2, 6), lifetime_range=(0.2, 0.5), angle=None):
        for _ in range(count):
            self.particles.append(Particle(x, y, color, speed_range, size_range, lifetime_range, angle))

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.lifetime > 0]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

class Graphics:
    def __init__(self):
        self.particles = ParticleSystem()
        
    def update(self, dt):
        self.particles.update(dt)
        
    def draw(self, surface):
        self.particles.draw(surface)

    @staticmethod
    def draw_neon_wall(surface, x, y, width, height, color=None):
        """Draws a glowing neon line for walls."""
        if color is None:
            color = WALL_COLOR
        # Tinh toan mau nen filled va mau glow neon
        fill_color = (color[0] // 5, color[1] // 5, color[2] // 5)
        glow_color = (max(0, color[0]-100), max(0, color[1]-50), max(0, color[2]-50))
        
        rect = pygame.Rect(x, y, width, height)
        # Ve to mau day phan than tuong
        pygame.draw.rect(surface, fill_color, rect, border_radius=0)
        # Ve phan vien glow va border sang truoc tuong
        pygame.draw.rect(surface, glow_color, rect, WALL_WIDTH + 2, border_radius=0)
        pygame.draw.rect(surface, color, rect, WALL_WIDTH, border_radius=0)

    @staticmethod
    def draw_dashed_path(surface, path, start_pixel, color, tile_size):
        """Draws a flowing dashed shadow path using alpha."""
        if not path:
            return
            
        path_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        alpha_color = (*color[:3], 150) # Make it slightly more vibrant
        
        points = [start_pixel]
        for r, c in path:
            points.append((c * tile_size + tile_size // 2, r * tile_size + tile_size // 2))
            
        dash_length = 6
        gap_length = 6
        period = dash_length + gap_length
        
        # Toc do luon song/chay cua duong net dut (flow speed in pixels per second)
        # "increase it": Dat toc do cao (120 px/s) de tao cam giac chay rat nhanh va muot ma
        flow_speed = 120.0
        time_passed = pygame.time.get_ticks() / 1000.0
        offset = (time_passed * flow_speed) % period
        
        total_dist_traveled = 0.0
        
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i+1]
            
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            segment_dist = math.hypot(dx, dy)
            if segment_dist == 0:
                continue
                
            dx /= segment_dist
            dy /= segment_dist
            
            curr_seg_dist = 0.0
            while curr_seg_dist < segment_dist:
                global_d = total_dist_traveled + curr_seg_dist
                phase = (global_d - offset) % period
                
                if phase < dash_length:
                    dash_rem = dash_length - phase
                    step = min(dash_rem, segment_dist - curr_seg_dist)
                    
                    start_pt = (int(p1[0] + dx * curr_seg_dist), int(p1[1] + dy * curr_seg_dist))
                    end_pt = (int(p1[0] + dx * (curr_seg_dist + step)), int(p1[1] + dy * (curr_seg_dist + step)))
                    pygame.draw.line(path_surface, alpha_color, start_pt, end_pt, 3)
                    
                    curr_seg_dist += step
                else:
                    gap_rem = period - phase
                    step = min(gap_rem, segment_dist - curr_seg_dist)
                    curr_seg_dist += step
                    
            total_dist_traveled += segment_dist
            
        surface.blit(path_surface, (0, 0))

    @staticmethod
    def draw_power_pellet(surface, x, y, tile_size, time_passed):
        """Draws a pulsing power pellet."""
        pulse = (math.sin(time_passed * 5) + 1) / 2 # tu 0 den 1
        radius = int(tile_size * 0.25 + (tile_size * 0.1 * pulse))
        
        center = (x + tile_size // 2, y + tile_size // 2)
        
        # Sang bong
        glow_surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 255, 255, 100), (tile_size//2, tile_size//2), radius + 2)
        surface.blit(glow_surf, (x, y))
        
        # Nhan
        pygame.draw.circle(surface, POWER_PELLET_COLOR, center, radius)

    @staticmethod
    def draw_path_spread(surface, nodes, age, duration, color, tile_size):
        """Draws a noticeable propagating spread of pathfinding search space."""
        if not nodes:
            return
            
        node_lifetime = 0.35  # lifetime of each explored tile visual
        num_nodes = len(nodes)
        
        # Draw each explored node if it has been activated by the propagation wave
        for i, (r, c) in enumerate(nodes):
            # The entire search space propagates within the duration
            t_activate = (i / num_nodes) * duration
            
            if age >= t_activate:
                t_active = age - t_activate
                if t_active < node_lifetime:
                    progress = t_active / node_lifetime
                    
                    # Noticeable fading alpha (max 95 for clear visibility)
                    alpha = int(95 * (1.0 - progress))
                    
                    # Constant size to avoid pop up / scale animation
                    cell_size = tile_size - 6
                    cx = c * tile_size + tile_size // 2
                    cy = r * tile_size + tile_size // 2
                    x = cx - cell_size // 2
                    y = cy - cell_size // 2
                    
                    if cell_size > 0:
                        cell_surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                        
                        # Soft filled rect
                        fill_color = (*color[:3], int(alpha * 0.35))
                        pygame.draw.rect(cell_surf, fill_color, (0, 0, cell_size, cell_size), border_radius=4)
                        
                        # Glowing border
                        border_color = (*color[:3], alpha)
                        pygame.draw.rect(cell_surf, border_color, (0, 0, cell_size, cell_size), 2, border_radius=4)
                        
                        surface.blit(cell_surf, (x, y))
