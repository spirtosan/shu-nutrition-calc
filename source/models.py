# =============================================================================
# models.py — Shu Nutrition Calc v5.3
# Data I/O, calculations, and log entry creation.
# =============================================================================

import os
import json
import uuid
from datetime import datetime, timedelta, date

from config import (DB_FILE, LOG_FILE, CONFIG_FILE,
                    DEFAULT_PRINT_CONFIG, DEFAULT_DB)


class SaveError(OSError):
    pass


# =============================================================================
# DATABASE
# =============================================================================

def load_db():
    """Load food_db.json. Auto-create with defaults if missing."""
    if not os.path.exists(DB_FILE):
        save_db(DEFAULT_DB.copy())
        return DEFAULT_DB.copy()
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    migrated = False
    for item in db:
        if "id" not in item:
            item["id"] = str(uuid.uuid4())
            migrated = True
    if migrated:
        save_db(db)
    return db


def save_db(db):
    """Persist food database to disk."""
    tmp = DB_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        os.replace(tmp, DB_FILE)
    except OSError as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise SaveError(e.errno, e.strerror, DB_FILE) from e


# =============================================================================
# MEAL LOG
# =============================================================================

def load_log():
    """Load meal_log.json. Auto-create empty log if missing."""
    if not os.path.exists(LOG_FILE):
        save_log([])
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_log(log):
    """Persist meal log to disk."""
    tmp = LOG_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=4, ensure_ascii=False, default=str)
        os.replace(tmp, LOG_FILE)
    except OSError as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise SaveError(e.errno, e.strerror, LOG_FILE) from e


def new_log_entry(meal_name, portion_g, p, f, c, kcal, dt=None, notes=""):
    """
    Create a new journal entry.
    All macro values (p, f, c, kcal) are for the portion actually eaten.

    meal_name : str
    portion_g : float — grams eaten (None for manual/unknown weight entries)
    p, f, c   : float — grams of protein, fat, carbs for this portion
    kcal      : float — calories for this portion
    dt        : datetime — defaults to now
    notes     : str
    """
    if dt is None:
        dt = datetime.now()
    return {
        "id":        str(uuid.uuid4()),
        "datetime":  dt.strftime("%Y-%m-%dT%H:%M:%S"),
        "meal_name": meal_name,
        "portion_g": round(float(portion_g), 1) if portion_g is not None else None,
        "p":         round(float(p), 1),
        "f":         round(float(f), 1),
        "c":         round(float(c), 1),
        "kcal":      round(float(kcal), 0),
        "notes":     notes,
    }


def entry_macros(entry):
    """
    Return (kcal, p, f, c) for an entry.
    Handles both the current simplified format and legacy entries
    from older versions that stored raw/prepared/portion separately.
    """
    # ── Current format (v5.1+): values already represent the portion eaten ──
    if "kcal" in entry:
        return (float(entry["kcal"]),
                float(entry.get("p", 0)),
                float(entry.get("f", 0)),
                float(entry.get("c", 0)))

    # ── Legacy format (pre-v5.1): reconstruct best estimate ────────────────
    use_prep = (entry.get("logged_view", "raw") == "prepared"
                and entry.get("prep_kcal") is not None)
    if use_prep:
        kcal  = float(entry.get("prep_kcal", 0))
        p     = float(entry.get("prep_p", 0))
        f     = float(entry.get("prep_f", 0))
        c     = float(entry.get("prep_c", 0))
        ref_w = float(entry.get("prepared_weight") or entry.get("raw_weight", 0))
    else:
        kcal  = float(entry.get("raw_kcal", 0))
        p     = float(entry.get("raw_p", 0))
        f     = float(entry.get("raw_f", 0))
        c     = float(entry.get("raw_c", 0))
        ref_w = float(entry.get("raw_weight", 0))

    # Scale to portion if recorded
    if entry.get("logged_as") == "portion" and entry.get("portion_g") and ref_w:
        scale = float(entry["portion_g"]) / ref_w
        kcal *= scale; p *= scale; f *= scale; c *= scale

    return kcal, p, f, c


def get_entry_date(entry):
    """Return date object from a log entry's datetime string."""
    return datetime.strptime(entry["datetime"], "%Y-%m-%dT%H:%M:%S").date()


def get_period_entries(log, start_date, end_date):
    """Return log entries whose date falls within [start_date, end_date]."""
    return [e for e in log
            if start_date <= get_entry_date(e) <= end_date]


def get_daily_summary(log, start_date, end_date):
    """
    Aggregate log entries by calendar day in [start_date, end_date].

    Returns:
        days_data : dict {date: {"entries": [...], "kcal": float,
                                 "p": float, "f": float, "c": float}}
        missing   : list of date objects with no entries
    """
    days_data = {}
    current = start_date
    while current <= end_date:
        days_data[current] = {"entries": [], "kcal": 0.0,
                               "p": 0.0, "f": 0.0, "c": 0.0}
        current += timedelta(days=1)

    for entry in log:
        d = get_entry_date(entry)
        if d in days_data:
            days_data[d]["entries"].append(entry)
            kcal, p, f, c = entry_macros(entry)
            days_data[d]["kcal"] += kcal
            days_data[d]["p"]    += p
            days_data[d]["f"]    += f
            days_data[d]["c"]    += c

    missing = [d for d, v in days_data.items() if not v["entries"]]
    return days_data, sorted(missing)


def find_missing_periods(missing_dates):
    """
    Group consecutive missing dates into periods.
    Returns list of (start_date, end_date) tuples.
    """
    if not missing_dates:
        return []
    periods = []
    start = prev = missing_dates[0]
    for d in missing_dates[1:]:
        if (d - prev).days == 1:
            prev = d
        else:
            periods.append((start, prev))
            start = prev = d
    periods.append((start, prev))
    return periods


def compute_period_averages(days_data, include_empty=True):
    """
    Compute average daily kcal/macros over days_data.
    include_empty: if False, skip days with no entries.
    """
    days = [v for v in days_data.values()
            if include_empty or v["entries"]]
    if not days:
        return {"kcal": 0, "p": 0, "f": 0, "c": 0,
                "days_counted": 0, "days_total": len(days_data)}
    n = len(days)
    return {
        "kcal":         round(sum(d["kcal"] for d in days) / n, 1),
        "p":            round(sum(d["p"]    for d in days) / n, 1),
        "f":            round(sum(d["f"]    for d in days) / n, 1),
        "c":            round(sum(d["c"]    for d in days) / n, 1),
        "days_counted": n,
        "days_total":   len(days_data),
    }


# =============================================================================
# PRINT / APP CONFIG
# =============================================================================

def load_print_config():
    """Load print_config.json. Auto-create with defaults if missing."""
    if not os.path.exists(CONFIG_FILE):
        save_print_config(DEFAULT_PRINT_CONFIG.copy())
        return DEFAULT_PRINT_CONFIG.copy()
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        stored = json.load(f)
    cfg = DEFAULT_PRINT_CONFIG.copy()
    cfg.update(stored)
    return cfg


def save_print_config(cfg):
    """Persist config to disk."""
    tmp = CONFIG_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        os.replace(tmp, CONFIG_FILE)
    except OSError as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise SaveError(e.errno, e.strerror, CONFIG_FILE) from e


# =============================================================================
# MEAL CALCULATIONS
# =============================================================================

def calc_prepared(raw_totals, raw_weight, prepared_weight):
    """
    Return macro totals for the prepared (cooked) meal.

    PHYSICS: Only water evaporates during cooking. Protein, fat, carbohydrates
    and calories do NOT change — the same nutrients are now in less weight,
    so concentration per 100g increases but totals are identical.

    Returns the same totals unchanged. The caller passes prepared_weight as
    the reference weight for per-100g and per-portion calculations.
    """
    if not prepared_weight or prepared_weight <= 0:
        return None
    return {
        "p":    round(raw_totals["p"],    2),
        "f":    round(raw_totals["f"],    2),
        "c":    round(raw_totals["c"],    2),
        "kcal": round(raw_totals["kcal"], 2),
    }


def calc_per_100g(totals, weight):
    """Return macros per 100g given totals and total weight."""
    if not weight:
        return {"p": 0, "f": 0, "c": 0, "kcal": 0}
    f = 100 / weight
    return {
        "p":    round(totals["p"]    * f, 1),
        "f":    round(totals["f"]    * f, 1),
        "c":    round(totals["c"]    * f, 1),
        "kcal": round(totals["kcal"] * f, 1),
    }


def calc_portion(totals, weight, portion_g):
    """Return macros for a specific portion size."""
    if not weight or not portion_g:
        return {"p": 0, "f": 0, "c": 0, "kcal": 0}
    f = portion_g / weight
    return {
        "p":    round(totals["p"]    * f, 1),
        "f":    round(totals["f"]    * f, 1),
        "c":    round(totals["c"]    * f, 1),
        "kcal": round(totals["kcal"] * f, 1),
    }


# =============================================================================
# SETTINGS (language preference etc.)
# =============================================================================

def load_settings():
    """Load settings.json. Auto-create with defaults if missing."""
    from config import SETTINGS_FILE, DEFAULT_SETTINGS
    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        stored = json.load(f)
    cfg = DEFAULT_SETTINGS.copy()
    cfg.update(stored)
    return cfg


def save_settings(cfg):
    """Persist settings to disk."""
    from config import SETTINGS_FILE
    tmp = SETTINGS_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        os.replace(tmp, SETTINGS_FILE)
    except OSError as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise SaveError(e.errno, e.strerror, SETTINGS_FILE) from e


# =============================================================================
# Recipe storage
# =============================================================================

def load_recipes():
    """Load recipes.json. Returns list; creates empty file if missing."""
    from config import RECIPES_FILE
    if not os.path.exists(RECIPES_FILE):
        return []
    try:
        with open(RECIPES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_recipes(recipes):
    from config import RECIPES_FILE
    tmp = RECIPES_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(recipes, f, ensure_ascii=False, indent=2)
        os.replace(tmp, RECIPES_FILE)
    except OSError as e:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise SaveError(e.errno, e.strerror, RECIPES_FILE) from e


def new_recipe(name, ingredients, raw_weight, raw_totals,
               prepared_weight=None, prep_totals=None,
               serving_g=None, notes=""):
    """Create a new recipe dict ready for storage."""
    from datetime import datetime as _dt
    return {
        "id":               str(uuid.uuid4()),
        "name":             name,
        "created":          _dt.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "notes":            notes or "",
        "serving_g":        serving_g,
        "raw_weight":       raw_weight,
        "prepared_weight":  prepared_weight,
        "ingredients":      ingredients,
        "raw_totals":       raw_totals,
        "prep_totals":      prep_totals,
    }

