import json
import os
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass
class AppSettings:
    language: str = "en"
    start_combo_max_interval: float = 0.5


def _resolve_legacy_settings_path() -> str:
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "settings.json")


def resolve_settings_path() -> str:
    """Return the settings file path in AppData on Windows, else legacy path."""
    if sys.platform == "win32":
        appdata_dir = os.getenv("APPDATA") or os.getenv("LOCALAPPDATA")
        if appdata_dir:
            return os.path.join(appdata_dir, "MortarAid", "settings.json")
    return _resolve_legacy_settings_path()


def load_settings(path: str, allowed_intervals: Iterable[float]) -> AppSettings:
    settings = AppSettings()
    candidate_paths = [path]
    legacy_path = _resolve_legacy_settings_path()
    if legacy_path not in candidate_paths:
        candidate_paths.append(legacy_path)

    selected_path = None
    for candidate in candidate_paths:
        if os.path.exists(candidate):
            selected_path = candidate
            break

    if selected_path is None:
        return settings

    try:
        with open(selected_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return settings

    lang = data.get("language")
    if isinstance(lang, str):
        settings.language = lang

    interval = data.get("start_combo_max_interval")
    if isinstance(interval, (int, float)):
        for option in allowed_intervals:
            if abs(float(interval) - float(option)) < 1e-6:
                settings.start_combo_max_interval = float(option)
                break

    return settings


def save_settings(path: str, settings: AppSettings) -> None:
    data = {
        "language": settings.language,
        "start_combo_max_interval": settings.start_combo_max_interval,
    }
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        # Keep app usable even when settings cannot be written.
        pass
