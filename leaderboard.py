"""
leaderboard.py — Persistent JSON leaderboard for Cyberpunk Pacman.

Score formula:
  WIN  : 1000 + (ghosts_eaten × 250) + max(0, 500 - elapsed_seconds × 5)
  LOSS :           ghosts_eaten × 100
"""

import json
import os
from datetime import datetime

LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), "leaderboard.json")


class Leaderboard:
    def __init__(self):
        self._data = []
        self._usernames = []
        self._load()

    # ── Luu tru Ben vung ──────────────────────────────────────────────────────────

    def _load(self):
        try:
            if os.path.exists(LEADERBOARD_FILE):
                with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                    if isinstance(raw, dict):
                        self._data = raw.get("entries", [])
                        self._usernames = raw.get("usernames", [])
                    elif isinstance(raw, list):
                        self._data = raw
                        # Backwards compatibility: populate usernames from entries
                        self._usernames = []
                        for e in reversed(self._data):
                            if e.get("name") and e["name"] not in self._usernames:
                                self._usernames.append(e["name"])
        except Exception:
            self._data = []
            self._usernames = []

    def _save(self):
        try:
            with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
                raw = {
                    "entries": self._data,
                    "usernames": self._usernames
                }
                json.dump(raw, f, indent=2)
        except Exception as e:
            print(f"[Leaderboard] Could not save: {e}")

    # ── API Cong khai ───────────────────────────────────────────────────────────

    @staticmethod
    def calc_score(won: bool, ghosts_eaten: int, elapsed_seconds: float) -> int:
        if won:
            time_bonus = max(0, int(500 - elapsed_seconds * 5))
            return 1000 + ghosts_eaten * 250 + time_bonus
        else:
            return ghosts_eaten * 100

    def add_entry(self, name: str, won: bool, ghosts_eaten: int,
                  elapsed_seconds: float, time_str: str,
                  steps: int, turns: int, map_size: str = "N/A",
                  pacman_explored: int = None, ghost_explored: dict = None,
                  pacman_algo: str = "A*", ghost_algos: dict = None) -> int:
        """Add a new entry and return the achieved score."""
        score = self.calc_score(won, ghosts_eaten, elapsed_seconds)
        name_upper = name.strip().upper() or "ANON"
        
        # Track unique username history (most-recently-used first)
        if name_upper in self._usernames:
            self._usernames.remove(name_upper)
        self._usernames.insert(0, name_upper)

        entry = {
            "name":         name_upper,
            "score":        score,
            "result":       "WIN" if won else "LOSS",
            "ghosts":       ghosts_eaten,
            "time":         time_str,
            "elapsed":      round(elapsed_seconds, 1),
            "steps":        steps,
            "turns":        turns,
            "map_size":     map_size,
            "date":         datetime.now().strftime("%Y-%m-%d"),
            "pacman_algo":  pacman_algo,
        }
        if ghost_algos is not None:
            entry["ghost_algos"] = ghost_algos
        if pacman_explored is not None:
            entry["pacman_explored"] = pacman_explored
        if ghost_explored is not None:
            entry["ghost_explored"] = ghost_explored
        self._data.append(entry)
        self._save()
        return score

    def get_sorted(self, limit: int = 100):
        """Return entries sorted by score descending."""
        return sorted(self._data, key=lambda e: e["score"], reverse=True)[:limit]

    def get_last_entry_rank(self) -> int:
        """Return the 1-based rank of the last added entry in the sorted leaderboard."""
        if not self._data:
            return 1
        last_entry = self._data[-1]
        sorted_data = sorted(self._data, key=lambda e: e["score"], reverse=True)
        for i, entry in enumerate(sorted_data):
            if entry is last_entry:
                return i + 1
        return len(sorted_data)

    def get_known_names(self):
        """Return unique names seen so far, most-recently-used first."""
        if not self._usernames and self._data:
            seen = []
            for e in reversed(self._data):
                if e["name"] not in seen:
                    seen.append(e["name"])
            self._usernames = seen
        return self._usernames

    def delete_entry(self, entry):
        """Remove a specific entry from the data list and save."""
        if entry in self._data:
            self._data.remove(entry)
            self._save()
            return True
        return False

    def clear(self):
        """Clear all entries from the leaderboard but preserve usernames."""
        self._data = []
        self._save()
