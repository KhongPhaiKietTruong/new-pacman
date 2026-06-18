# pyrefly: ignore [missing-import]
import pygame
import sys
from config import *
from game import GameEngine
from ui import UI, NameSelectUI, LeaderboardUI
from map_editor import MapEditor
from leaderboard import Leaderboard

def main():
    pygame.init()
    pygame.key.set_repeat(400, 50)
    
    # Thu man hinh rong, quay lai cua so neu that bai hoac de thu nghiem
    try:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        info = pygame.display.Info()
        width, height = info.current_w, info.current_h
    except:
        width, height = BASE_WIDTH, BASE_HEIGHT
        screen = pygame.display.set_mode((width, height))
        
    pygame.display.set_caption("Cyberpunk AI Pacman")
    clock = pygame.time.Clock()
    
    game        = GameEngine(width, height)
    ui          = UI(width, height)
    map_editor  = MapEditor(width, height)
    name_ui     = NameSelectUI(width, height)
    lb_ui       = LeaderboardUI(width, height)
    leaderboard = Leaderboard()

    game.play_music('menu_music')
    
    running = True
    time_passed = 0
    start_anim_timer  = 0.0
    pending_start_args  = None   # (do phuc tap, kich thuoc ban do, che do, thuat toan)
    pending_custom_args = None   # doi so ban do tuy chinh tu trinh bien tap ban do
    end_anim_timer = 0.0
    end_anim_won   = False
    current_player = "ANONYMOUS"      # Ten duoc chon tren man hinh chon ten
    # Lieu lan bat dau tiep theo co tu trinh bien tap ban do
    _from_editor = False

    while running:
        dt = clock.tick(FPS) / 1000.0
        time_passed += dt
        
        # Dong bo am luong am thanh trong thoi gian thuc
        game.sound_volume = ui.sound_volume
        if game.music_channel:
            game.music_channel.set_volume(ui.sound_volume * 0.5)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_x, mouse_y = mouse_pos

        # ── Xu ly Su kien ─────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # ── Chon Ten ────────────────────────────────────────────────
            elif game.state == STATE_NAME_SELECT:
                name_ui.handle_event(event, mouse_pos)

            # ── Bang Xep Hang ────────────────────────────────────────────────
            elif game.state == STATE_LEADERBOARD:
                lb_ui.handle_event(event, mouse_pos)

            # ── Trinh Bien Tap Ban Do ─────────────────────────────────────────────────
            elif game.state == STATE_MAP_EDITOR:
                map_editor.handle_event(event, mouse_pos)

            # ── Moi thu khac ────────────────────────────────────────────
            else:
                if event.type == pygame.KEYDOWN:
                    if game.state == STATE_MENU and ui.menu_view == "settings" and ui.handle_settings_keydown(event):
                        continue
                    if event.key == pygame.K_ESCAPE:
                        if game.state == STATE_MAP_EDITOR:
                            game.state = STATE_MENU
                            game.play_music('menu_music')
                        elif game.state == STATE_MENU:
                            if ui.menu_view == "settings":
                                ui.menu_view = "main"
                            else:
                                running = False
                        else:
                            game.state = STATE_MENU
                    elif game.state == STATE_PLAYING and game.mode == "Player vs AI":
                        if event.key in [pygame.K_UP, pygame.K_w]:
                            game.pacman.next_dir = DIR_UP
                        elif event.key in [pygame.K_DOWN, pygame.K_s]:
                            game.pacman.next_dir = DIR_DOWN
                        elif event.key in [pygame.K_LEFT, pygame.K_a]:
                            game.pacman.next_dir = DIR_LEFT
                        elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                            game.pacman.next_dir = DIR_RIGHT
                            
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if game.state == STATE_MENU:
                            if ui.handle_mouse_down(mouse_pos):
                                pass
                            else:
                                res = ui.handle_menu_click(mouse_pos)
                                if res == "start":
                                    if ui.selected_map_idx == 0:
                                        # Di toi chon ten truoc
                                        _from_editor = False
                                        pending_start_args = (ui.complexity, ui.map_size, ui.mode, ui.algorithms, ui.pacman_heuristics)
                                        pending_custom_args = None
                                    else:
                                        _from_editor = True
                                        chosen_map = ui.custom_maps[ui.selected_map_idx - 1]
                                        grid = [row[:] for row in chosen_map["grid"]]
                                        rows = chosen_map["rows"]
                                        cols = chosen_map["cols"]
                                        pacman_pos = None
                                        ghost_positions = []
                                        for r in range(rows):
                                            for c in range(cols):
                                                if grid[r][c] == 3:
                                                    pacman_pos = (r, c)
                                                    grid[r][c] = 0
                                                elif grid[r][c] == 4:
                                                    ghost_positions.append((r, c))
                                                    grid[r][c] = 0
                                        pending_start_args = None
                                        pending_custom_args = (grid, rows, cols, ui.mode, ui.algorithms,
                                                              pacman_pos, ghost_positions, ui.pacman_heuristics)
                                    name_ui.reset(leaderboard.get_known_names())
                                    game.state = STATE_NAME_SELECT
                                elif res == "custom_map":
                                    game.state = STATE_MAP_EDITOR
                                elif res == "leaderboard":
                                    lb_ui.reset(leaderboard.get_sorted())
                                    game.state = STATE_LEADERBOARD
                                elif res == "exit":
                                    running = False
                                    
                        elif game.state == STATE_PLAYING:
                            sidebar_res = ui.handle_sidebar_click(mouse_pos, game)
                            if sidebar_res == "exit":
                                game.stop_music()
                                game.play_music('menu_music')
                            elif sidebar_res == "replay":
                                game.stop_music()
                                game.play_music('game_music')
                                
                        elif game.state in [STATE_GAME_OVER, STATE_VICTORY]:
                            if ui.hovered_btn == "start":
                                # Chon ten lai de choi lai
                                _from_editor = False
                                pending_start_args = (ui.complexity, ui.map_size, ui.mode, ui.algorithms, ui.pacman_heuristics)
                                game.stop_music()
                                name_ui.reset(leaderboard.get_known_names())
                                game.state = STATE_NAME_SELECT
                            elif ui.hovered_btn == "exit":
                                game.stop_music()
                                game.state = STATE_MENU
                                game.play_music('menu_music')
                                
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        ui.handle_mouse_up()
                        
                elif event.type == pygame.MOUSEMOTION:
                    if game.state == STATE_PLAYING:
                        ui.handle_sidebar_hover(mouse_pos)
                        if ui.dragging_slider == "speed":
                            ui.handle_gameplay_mouse_motion(mouse_pos, game)
                    else:
                        res = ui.handle_mouse_motion(mouse_pos)
                        if res:
                            emit_x, emit_y = res
                            game.graphics.particles.emit(emit_x, emit_y, WALL_COLOR, count=1,
                                                         size_range=(2, 4), lifetime_range=(0.2, 0.4))

        # ── Kiem tra trang thai sau su kien ─────────────────────────────────────────

        # Chon ten hoan tat
        if game.state == STATE_NAME_SELECT:
            if name_ui.confirmed_name:
                current_player = name_ui.confirmed_name
                game.stop_music()
                game.play_sound('start_sound')
                game.state = STATE_STARTING
                start_anim_timer = 0.0
                # pending_start_args / pending_custom_args da duoc thiet lap
            elif name_ui.cancelled:
                game.state = STATE_MENU
                game.play_music('menu_music')

        # Trinh bien tap ban do hoan tat
        if game.state == STATE_MAP_EDITOR:
            map_editor.update(dt)
            action = map_editor.poll_action()
            if action:
                if action[0] == "back":
                    game.state = STATE_MENU
                    game.play_music('menu_music')
                elif action[0] == "play":
                    _, play_grid, rows, cols, pacman_pos, ghost_positions = action
                    _from_editor = True
                    pending_start_args  = None
                    pending_custom_args = (play_grid, rows, cols, ui.mode, ui.algorithms,
                                          pacman_pos, ghost_positions, ui.pacman_heuristics)
                    name_ui.reset(leaderboard.get_known_names())
                    game.state = STATE_NAME_SELECT

        # Bang xep hang hoan tat
        if game.state == STATE_LEADERBOARD and lb_ui.back_pressed:
            game.state = STATE_MENU

        # ── Cap nhat ─────────────────────────────────────────────────────────
        if game.state == STATE_STARTING:
            start_anim_timer += dt
        elif game.state == STATE_END_ANIM:
            end_anim_timer += dt
        elif game.state == STATE_PLAYING:
            if not hasattr(game, 'update_accumulator'):
                game.update_accumulator = 0.0
            game.update_accumulator += game.speed_scale
            while game.update_accumulator >= 1.0:
                game.update(dt)
                game.update_accumulator -= 1.0
            if game.state == STATE_END_ANIM:
                end_anim_timer = 0.0
                end_anim_won = (game.pending_end_state == STATE_VICTORY)
                ui.reset_end_anim()
                ghost_explored = {type(g).__name__: g.total_explored_nodes for g in game.ghosts}
                ui.set_stats(game.get_time_str(), game.steps, game.turns, game.ghosts_eaten, f"{game.cols}x{game.rows}", game.mode, game.pacman.search_count, game.pacman.total_explored_nodes, ghost_explored)
                # Luu thong tin bang xep hang
                score = leaderboard.add_entry(
                    name           = current_player,
                    won            = end_anim_won,
                    ghosts_eaten   = game.ghosts_eaten,
                    elapsed_seconds= game.get_elapsed_seconds(),
                    time_str       = game.get_time_str(),
                    steps          = game.steps,
                    turns          = game.turns,
                    map_size       = f"{game.cols}x{game.rows}",
                )
                ui.current_rank = leaderboard.get_last_entry_rank()
                ui.current_score = score
                ui.total_leaderboard_entries = len(leaderboard._data)

        # ── Ve ───────────────────────────────────────────────────────────
        if game.state == STATE_MENU:
            ui.draw_menu(screen, time_passed)
            game.graphics.draw(screen)

        elif game.state == STATE_NAME_SELECT:
            name_ui.draw(screen)

        elif game.state == STATE_LEADERBOARD:
            lb_ui.draw(screen)

        elif game.state == STATE_MAP_EDITOR:
            map_editor.draw(screen)

        elif game.state == STATE_STARTING:
            ui.draw_menu(screen, time_passed)
            done = ui.draw_start_animation(screen, start_anim_timer)
            if done:
                ui.current_rank = None
                ui.current_score = None
                if pending_custom_args is not None:
                    game.start_game_custom(*pending_custom_args)
                    pending_custom_args = None
                elif pending_start_args is not None:
                    game.start_game(*pending_start_args)
                    pending_start_args = None
                game.play_music('game_music')
            
        elif game.state == STATE_PLAYING:
            game.draw(screen, time_passed)
            ui.draw_sidebar(screen, game, time_passed)
            
        elif game.state == STATE_END_ANIM:
            game.draw(screen, time_passed)
            done = ui.draw_end_anim(screen, end_anim_won, end_anim_timer)
            if done:
                game.state = game.pending_end_state
            
        elif game.state in [STATE_GAME_OVER, STATE_VICTORY]:
            game.draw(screen, time_passed)
            ui.draw_end_screen(screen, game.state == STATE_VICTORY)
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
