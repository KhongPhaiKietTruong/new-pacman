# pyrefly: ignore [missing-import]
import pygame

# --- Cua so va Hien thi ---
# Dung ti le khung hinh HD chuan cho logic co ban, viec co gian tu dong xu ly
BASE_WIDTH = 1920
BASE_HEIGHT = 1080
SIDEBAR_WIDTH = 460
FPS = 60

# --- Cau hinh Luoi ---
# Kich thuoc o vuong bang pixel (se co gian theo kich thuoc man hinh/luoi)
TILE_SIZE = 40  
# Kich thuoc luoi Toi da va Toi thieu dua tren thanh truot do phuc tap (0.0 den 1.0)
MIN_GRID_COLS = 15
MIN_GRID_ROWS = 15
MAX_GRID_COLS = 55
MAX_GRID_ROWS = 35

# --- Mau chu de (Cyberpunk/Neon) ---
BG_COLOR = (11, 12, 16)       # Xanh navy sieu dam / den
WALL_COLOR = (0, 229, 255)    # Neon xanh lo phat sang
WALL_WIDTH = 2                # Duong line mong

TEXT_COLOR = (255, 255, 255)  # Trang tinh
TEXT_HOVER_COLOR = (0, 229, 255) # Xanh lo

PACMAN_COLOR = (255, 235, 59) # Vang sang
PACMAN_AURA_COLOR = (255, 255, 255) 

# Mau Sac Con Ma
BLINKY_COLOR = (255, 0, 85)   # Do Neon
PINKY_COLOR = (255, 102, 204) # Hong Neon
INKY_COLOR = (0, 204, 255)    # Xanh Duong Neon
CLYDE_COLOR = (255, 153, 0)   # Cam Neon

GHOST_SCARED_COLOR = (26, 35, 126) # Xanh Dam #1A237E
POWER_PELLET_COLOR = (255, 255, 255)

# --- Thoi gian & Thoi luong ---
POWER_MODE_DURATION = 8.0  # giay
PELLET_RESPAWN_TIME = 15.0 # giay

# --- Toc do Thuc the ---
# Toc do tinh bang pixel moi khung hinh. Phai la uoc so cua TILE_SIZE.
# Neu TILE_SIZE la 40, cac toc do 2, 4, 5, 8 se hoat dong tot.
SPEED_NORMAL = 4
SPEED_PACMAN_POWER = 4
SPEED_GHOST_SCARED = 2

# --- Trang thai Game ---
STATE_MENU = 0
STATE_PLAYING = 1
STATE_GAME_OVER = 2
STATE_VICTORY = 3
STATE_STARTING = 4  # Hieu ung intro dien anh truoc khi bat dau game
STATE_END_ANIM = 5  # Hieu ung outro dien anh truoc khi den man hinh ket thuc
STATE_MAP_EDITOR = 6  # Trinh chinh sua ban do tuy chinh trong game
STATE_NAME_SELECT = 7   # Nhap ten / chon nguoi choi truoc game
STATE_LEADERBOARD = 8   # Man hinh hien thi bang xep hang


# --- ID Thuc the ---
DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)
DIR_NONE = (0, 0)

# Huong nguoc lai de ngan chan quay dau 180 do
OPPOSITE_DIR = {
    DIR_UP: DIR_DOWN,
    DIR_DOWN: DIR_UP,
    DIR_LEFT: DIR_RIGHT,
    DIR_RIGHT: DIR_LEFT,
    DIR_NONE: DIR_NONE
}
