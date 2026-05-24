# =============================================================================
# config.py — Shu Nutrition Calc v5.2
# Central configuration: app identity, file paths, defaults.
# =============================================================================

import os
import sys

APP_NAME = "Shu Nutrition Calc"
VERSION  = "5.3"
CREATOR  = "Ivan Shumkov"
YEAR     = "2026"

# ---------------------------------------------------------------------------
# File paths — all data files live next to the executable / script
# ---------------------------------------------------------------------------
def _base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR      = _base_dir()
DB_FILE       = os.path.join(BASE_DIR, "food_db.json")
LOG_FILE      = os.path.join(BASE_DIR, "meal_log.json")
CONFIG_FILE   = os.path.join(BASE_DIR, "print_config.json")
SETTINGS_FILE  = os.path.join(BASE_DIR, "settings.json")
RECIPES_FILE   = os.path.join(BASE_DIR, "recipes.json")
LANG_DIR      = os.path.join(BASE_DIR, "lang")

HELP_DIR   = os.path.join(BASE_DIR, "help")
IMG_DIR    = os.path.join(BASE_DIR, "img")
LOGO_SMALL = os.path.join(IMG_DIR, "mylogo64.png")
LOGO_LARGE = os.path.join(IMG_DIR, "mylogo128.png")

def get_help_file(lang_code="en"):
    """Return path to the help HTML file for the given language code.
    Looks in help/ subfolder first, then next to exe (backward compat)."""
    in_subdir = os.path.join(HELP_DIR, f"help_{lang_code}.html")
    if os.path.exists(in_subdir):
        return in_subdir
    legacy = os.path.join(BASE_DIR, f"help_{lang_code}.html")
    if os.path.exists(legacy):
        return legacy
    en_subdir = os.path.join(HELP_DIR, "help_en.html")
    if os.path.exists(en_subdir):
        return en_subdir
    return os.path.join(BASE_DIR, "help_en.html")

# ---------------------------------------------------------------------------
# App-wide persistent config defaults
# Stored in print_config.json (name kept for backward compatibility)
# ---------------------------------------------------------------------------
DEFAULT_PRINT_CONFIG = {
    # Print — meal
    "meal_unprepared":            False,
    "meal_prepared":              False,
    "per_100g_unprepared":        False,
    "per_100g_prepared":          False,
    "portion_unprepared":         False,
    "portion_prepared":           False,
    "include_ingredient_details": False,
    "pdf_dark_theme":             False,
    # Print — journal
    "log_per_meal":               False,
    "log_daily_totals":           False,
    "log_daily_average":          False,
    # Print — recipe
    "recipe_ingredients":     False,
    "recipe_raw":             False,
    "recipe_prepared":        False,
    "recipe_per100_raw":      False,
    "recipe_per100_prepared": False,
    "recipe_per_serving":     False,
    # Meal Builder behaviour
    "use_whole_meal_as_portion":  False,
}

# ---------------------------------------------------------------------------
# Settings defaults
# ---------------------------------------------------------------------------
DEFAULT_SETTINGS = {
    "language": "en",
}

# ---------------------------------------------------------------------------
# Default food database (used when food_db.json is missing)
# ---------------------------------------------------------------------------
DEFAULT_DB = [
    {"id": "d140424c-83c7-4bba-81a5-d37ae6eadf1e", "name": "Protein",      "p": 100, "f":   0, "c":   0, "kcal": 400},
    {"id": "5ff5b847-6ee3-4441-ad96-255a3db43743", "name": "Fat",          "p":   0, "f": 100, "c":   0, "kcal": 900},
    {"id": "0539ba08-7ae6-4628-a210-5b1a99545963", "name": "Carbohydrate", "p":   0, "f":   0, "c": 100, "kcal": 400},
]
