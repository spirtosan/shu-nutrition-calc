# =============================================================================
# ui_print.py — Shu Nutrition Calc v5.3
# Print/export using HTML (opens in default browser).
# All UI strings via t().
# =============================================================================

import os
import atexit
import threading
import webbrowser
import tempfile
from datetime import datetime
from html import escape

_temp_files = []
_cleanup_registered = False


def _cleanup_temps():
    for p in _temp_files:
        try:
            os.unlink(p)
        except OSError:
            pass

import customtkinter as ctk
from tkinter import messagebox

from models import (load_print_config, save_print_config,
                    calc_per_100g, calc_portion,
                    get_daily_summary, compute_period_averages,
                    entry_macros)
from config import APP_NAME, VERSION, CREATOR
import lang
from lang import t


# =============================================================================
# PRINT DIALOG
# =============================================================================

class PrintDialog(ctk.CTkToplevel):

    def __init__(self, parent, app, mode, meal_data=None, log_data=None, recipe_data=None):
        super().__init__(parent)
        self.app       = app
        self.mode      = mode
        self.meal_data = meal_data
        self.log_data   = log_data
        self.recipe_data = recipe_data
        self.cfg       = load_print_config()

        self.title(t("print.title"))
        self.geometry("520x560")
        self.resizable(False, False)
        self._build_ui()

        self.transient(parent.winfo_toplevel())
        self.update_idletasks()
        self.lift()
        self.grab_set()
        self.focus_force()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        ctk.CTkLabel(self,
                     text=t("print.heading"),
                     font=("Segoe UI", 17, "bold"),
                     text_color="#f5a623").pack(pady=(18, 4))
        ctk.CTkLabel(self,
                     text=t("print.browser_hint"),
                     font=("Segoe UI", 12),
                     text_color="#909090").pack(pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(self, height=400)
        scroll.pack(fill="both", expand=True, padx=20, pady=4)

        # Theme
        self._section(scroll, t("print.section_theme"))
        self.dark_var = ctk.BooleanVar(
            value=self.cfg.get("pdf_dark_theme", False))
        ctk.CTkCheckBox(scroll,
                        text=t("print.dark_theme"),
                        font=("Segoe UI", 13),
                        variable=self.dark_var).pack(
                            anchor="w", padx=16, pady=3)
        ctk.CTkLabel(scroll,
                     text=f"  {t('print.light_hint')}",
                     font=("Segoe UI", 12),
                     text_color="#909090").pack(anchor="w", padx=32)

        if self.mode == "meal":
            self._build_meal_toggles(scroll)
        elif self.mode == "recipe":
            self._build_recipe_toggles(scroll)
        else:
            self._build_log_toggles(scroll)

        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(pady=14)
        ctk.CTkButton(btn_f, text=t("print.btn_open_browser"),
                      fg_color="#2a8a38", width=180,
                      command=self._generate).pack(side="left", padx=12)
        ctk.CTkButton(btn_f, text=t("print.btn_cancel"),
                      fg_color="#8B0000",
                      command=self.destroy).pack(side="left", padx=12)

    def _section(self, parent, title):
        ctk.CTkLabel(parent, text=title,
                     font=("Segoe UI", 13, "bold"),
                     text_color="#f5a623").pack(
                         anchor="w", padx=16, pady=(12, 4))

    def _checkbox(self, parent, key, label, state="normal", hint=None):
        var = ctk.BooleanVar(
            value=self.cfg.get(key, False) if state == "normal" else False)
        self.t_vars[key] = var
        cb = ctk.CTkCheckBox(parent, text=label,
                             font=("Segoe UI", 13),
                             variable=var, state=state)
        cb.pack(anchor="w", padx=16, pady=2)
        if state == "disabled" and hint:
            ctk.CTkLabel(parent, text=f"     ↳ {hint}",
                         font=("Segoe UI", 12),
                         text_color="#666666").pack(
                             anchor="w", padx=24, pady=(0, 2))

    def _build_meal_toggles(self, parent):
        md       = self.meal_data or {}
        has_prep = bool(md.get("prepared_weight") and md.get("prep_totals"))
        has_port = bool(md.get("portion_g"))

        self._section(parent, t("print.section_include"))
        self.t_vars = {}

        self._checkbox(parent, "meal_unprepared",
                       t("print.meal_unprepared"))
        self._checkbox(parent, "meal_prepared",
                       t("print.meal_prepared"),
                       state="normal" if has_prep else "disabled",
                       hint=t("print.hint_need_prep"))

        self._checkbox(parent, "per_100g_unprepared",
                       t("print.per100_raw"))
        self._checkbox(parent, "per_100g_prepared",
                       t("print.per100_prepared"),
                       state="normal" if has_prep else "disabled",
                       hint=t("print.hint_need_prep"))

        self._checkbox(parent, "portion_unprepared",
                       t("print.portion_raw"),
                       state="normal" if has_port else "disabled",
                       hint=t("print.hint_need_portion"))
        self._checkbox(parent, "portion_prepared",
                       t("print.portion_prepared"),
                       state="normal" if (has_prep and has_port) else "disabled",
                       hint=t("print.hint_need_both"))

        self._checkbox(parent, "include_ingredient_details",
                       t("print.ingredients"))

    def _build_log_toggles(self, parent):
        self._section(parent, t("print.section_include"))
        self.t_vars = {}

        self._checkbox(parent, "log_per_meal", t("print.log_per_meal"))
        ctk.CTkLabel(parent, text=t("print.log_per_meal_hint"),
                     font=("Segoe UI", 12),
                     text_color="#666666").pack(
                         anchor="w", padx=24, pady=(0, 4))

        self._checkbox(parent, "log_daily_totals",
                       t("print.log_daily_totals"))
        ctk.CTkLabel(parent, text=t("print.log_daily_totals_hint"),
                     font=("Segoe UI", 12),
                     text_color="#666666").pack(
                         anchor="w", padx=24, pady=(0, 4))

        self._checkbox(parent, "log_daily_average", t("print.log_avg"))
        ctk.CTkLabel(parent, text=t("print.log_avg_hint"),
                     font=("Segoe UI", 12),
                     text_color="#666666").pack(
                         anchor="w", padx=24, pady=(0, 4))

    # ------------------------------------------------------------------
    # Generate
    # ------------------------------------------------------------------

    def _generate(self):
        self.cfg["pdf_dark_theme"] = self.dark_var.get()
        for key, var in self.t_vars.items():
            self.cfg[key] = var.get()
        save_print_config(self.cfg)

        dark = self.cfg["pdf_dark_theme"]

        try:
            if self.mode == "meal":
                html = build_meal_html(self.meal_data, self.cfg, dark)
            elif self.mode == "recipe":
                html = build_recipe_html(self.recipe_data, self.cfg, dark)
            else:
                html = build_log_html(self.log_data, self.cfg, dark)
        except Exception as ex:
            messagebox.showerror(t("print.err_title"),
                                 t("print.err_msg", err=ex))
            return

        global _cleanup_registered
        fd, path = tempfile.mkstemp(suffix=".html", prefix="ShuNutrition_")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)

        _temp_files.append(path)
        if not _cleanup_registered:
            atexit.register(_cleanup_temps)
            _cleanup_registered = True

        def _delete_later(p):
            try:
                os.unlink(p)
            except OSError:
                pass
        threading.Timer(45, _delete_later, args=(path,)).start()

        webbrowser.open(f"file:///{path.replace(os.sep, '/')}")
        self.destroy()


    def _build_recipe_toggles(self, parent):
        rd       = self.recipe_data or {}
        has_prep = bool(rd.get("prepared_weight") and rd.get("prep_totals"))
        has_sv   = bool(rd.get("serving_g"))

        self._section(parent, t("print.section_include"))
        self.t_vars = {}

        self._checkbox(parent, "recipe_ingredients",
                       t("print.recipe_ingredients"))
        self._checkbox(parent, "recipe_raw",
                       t("print.recipe_raw"))
        self._checkbox(parent, "recipe_prepared",
                       t("print.recipe_prepared"),
                       state="normal" if has_prep else "disabled",
                       hint=t("print.hint_need_prep"))
        self._checkbox(parent, "recipe_per100_raw",
                       t("print.recipe_per100_raw"))
        self._checkbox(parent, "recipe_per100_prepared",
                       t("print.recipe_per100_prepared"),
                       state="normal" if has_prep else "disabled",
                       hint=t("print.hint_need_prep"))
        self._checkbox(parent, "recipe_per_serving",
                       t("print.recipe_per_serving"),
                       state="normal" if has_sv else "disabled",
                       hint=t("print.hint_need_serving"))


# =============================================================================
# HTML BUILDING HELPERS
# =============================================================================

def _css(dark):
    if dark:
        return """
  :root {
    --bg:#0e0e12; --surface:#16161e; --surface2:#1e1e2a;
    --border:#2a2a3a; --text:#dcdce8; --muted:#7a7a90;
    --amber:#f5a623; --blue:#4a9eff; --green:#2ecc71; --red:#e74c3c;
  }
  body { background:var(--bg); color:var(--text); }
  tr:nth-child(even) td { background:#13131a; }
"""
    return """
  :root {
    --bg:#ffffff; --surface:#f5f5f5; --surface2:#e8e8e8;
    --border:#cccccc; --text:#1a1a1a; --muted:#555555;
    --amber:#b06000; --blue:#1a5cb0; --green:#1a7a30; --red:#aa2020;
  }
  body { background:var(--bg); color:var(--text); }
  tr:nth-child(even) td { background:#f0f0f0; }
"""


def _base_css():
    return """
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:'Segoe UI',Arial,sans-serif; font-size:14px;
         line-height:1.6; padding-bottom:40px; }
  header { background:var(--surface); border-bottom:3px solid var(--amber);
           padding:20px 5%; }
  header h1 { color:var(--amber); font-size:1.6rem; }
  header .sub { color:var(--muted); font-size:0.9rem; margin-top:4px; }
  main { padding:24px 5%; max-width:960px; }
  h2 { color:var(--amber); font-size:1.1rem; margin:24px 0 8px;
       border-bottom:1px solid var(--border); padding-bottom:4px; }
  h3 { color:var(--blue); font-size:1rem; margin:14px 0 6px; }
  table { border-collapse:collapse; width:100%; margin:8px 0; }
  th { background:var(--surface2); color:var(--blue); }
  td,th { padding:7px 12px; border:1px solid var(--border);
          text-align:left; font-size:13px; }
  .macro-row { background:var(--surface); border:1px solid var(--border);
               border-radius:6px; padding:12px 18px; margin:8px 0;
               display:flex; gap:28px; flex-wrap:wrap; align-items:center; }
  .macro-row .col .val { font-weight:bold; font-size:1.1rem; }
  .macro-row .col .lbl { font-size:0.8rem; color:var(--muted); }
  .macro-row .tag { font-size:0.78rem; color:var(--muted);
                    font-style:italic; align-self:flex-end; }
  .p-col { color:var(--green); }
  .f-col { color:var(--amber); }
  .c-col { color:var(--blue); }
  .k-col { color:var(--text); }
  .note { background:var(--surface2); border-left:3px solid var(--blue);
          padding:8px 14px; margin:8px 0; font-size:0.88rem;
          color:var(--muted); border-radius:0 6px 6px 0; }
  .warn { background:var(--surface2); border-left:3px solid var(--red);
          padding:8px 14px; margin:8px 0; font-size:0.88rem;
          color:var(--red); border-radius:0 6px 6px 0; }
  footer { margin-top:40px; border-top:1px solid var(--border);
           padding:14px 5%; color:var(--muted); font-size:0.8rem; }
  @media print {
    header { break-inside:avoid; }
    h2 { break-after:avoid; }
    tr { break-inside:avoid; }
  }
"""


def _html_wrap(title, body, dark, lang_code="en"):
    css = _css(dark) + _base_css()
    now = datetime.now().strftime("%d-%m-%Y  %H:%M")
    gen_str = t("rpt.generated", dt=now)
    footer_str = t("rpt.footer")
    return f"""<!DOCTYPE html>
<html lang="{lang_code}">
<head>
<meta charset="UTF-8">
<title>{title} — {APP_NAME}</title>
<style>{css}</style>
</head>
<body>
<header>
  <h1>{APP_NAME} v{VERSION} &nbsp;·&nbsp; {title}</h1>
  <div class="sub">Created by {CREATOR} &nbsp;·&nbsp; {gen_str}</div>
</header>
<main>
{body}
</main>
<footer>{APP_NAME} v{VERSION} · Created by {CREATOR} · {footer_str}</footer>
</body>
</html>"""


def _macro_row(p, f, c, kcal, tag=""):
    p_lbl    = t("rpt.col_protein")
    f_lbl    = t("rpt.col_fat")
    c_lbl    = t("rpt.col_carbs")
    e_lbl    = t("rpt.col_energy")
    tag_html = f'<span class="tag">{escape(tag)}</span>' if tag else ""
    return f"""<div class="macro-row">
  <div class="col p-col"><div class="val">{t("mb.abbr_p")}: {p:.1f} g</div><div class="lbl">{p_lbl}</div></div>
  <div class="col f-col"><div class="val">{t("mb.abbr_f")}: {f:.1f} g</div><div class="lbl">{f_lbl}</div></div>
  <div class="col c-col"><div class="val">{t("mb.abbr_c")}: {c:.1f} g</div><div class="lbl">{c_lbl}</div></div>
  <div class="col k-col"><div class="val">{kcal:.0f} kcal</div><div class="lbl">{e_lbl}</div></div>
  {tag_html}
</div>"""


def _ingredients_table(ingredients):
    p_h = t("mb.abbr_p")
    f_h = t("mb.abbr_f")
    c_h = t("mb.abbr_c")
    food_h = t("rpt.col_meal")
    rows = "".join(
        f"<tr><td>{escape(i['name'])}</td>"
        f"<td>{i['w']:.1f}</td>"
        f"<td>{i['p']:.1f}</td>"
        f"<td>{i['f']:.1f}</td>"
        f"<td>{i['c']:.1f}</td>"
        f"<td>{i['k']:.1f}</td></tr>"
        for i in ingredients
    )
    return (f"<table><thead><tr>"
            f"<th>{food_h}</th><th>g</th>"
            f"<th>{p_h} (g)</th><th>{f_h} (g)</th>"
            f"<th>{c_h} (g)</th><th>kcal</th>"
            f"</tr></thead><tbody>{rows}</tbody></table>")


# =============================================================================
# MEAL HTML REPORT
# =============================================================================

def build_meal_html(meal_data, cfg, dark):
    ingredients     = meal_data["ingredients"]
    raw_weight      = meal_data["raw_weight"]
    raw_totals      = meal_data["raw_totals"]
    prepared_weight = meal_data.get("prepared_weight")
    prep_totals     = meal_data.get("prep_totals")
    portion_g       = meal_data.get("portion_g")
    has_prep        = bool(prepared_weight and prep_totals)

    body = ""

    if cfg.get("include_ingredient_details") and ingredients:
        body += f"<h2>{t('rpt.ingredients')}</h2>\n"
        body += _ingredients_table(ingredients)
        if has_prep:
            body += (f'<div class="note">{t("rpt.ing_note")}</div>\n')

    if cfg.get("meal_unprepared"):
        body += f"<h2>{t('rpt.whole_meal_raw', w=f'{raw_weight:.1f}')}</h2>\n"
        body += _macro_row(raw_totals["p"], raw_totals["f"],
                           raw_totals["c"], raw_totals["kcal"])

    if cfg.get("meal_prepared") and has_prep:
        body += (f"<h2>"
                 f"{t('rpt.whole_meal_prep', w=f'{prepared_weight:.1f}')}"
                 f"</h2>\n")
        body += _macro_row(prep_totals["p"], prep_totals["f"],
                           prep_totals["c"], prep_totals["kcal"])

    if cfg.get("per_100g_unprepared") and raw_weight > 0:
        p100 = calc_per_100g(raw_totals, raw_weight)
        body += f"<h2>{t('rpt.per100_raw')}</h2>\n"
        body += _macro_row(p100["p"], p100["f"], p100["c"], p100["kcal"])

    if cfg.get("per_100g_prepared") and has_prep:
        p100p = calc_per_100g(prep_totals, prepared_weight)
        body += f"<h2>{t('rpt.per100_prep')}</h2>\n"
        body += _macro_row(p100p["p"], p100p["f"], p100p["c"], p100p["kcal"])

    if portion_g:
        if cfg.get("portion_unprepared") and raw_weight > 0:
            port = calc_portion(raw_totals, raw_weight, portion_g)
            body += f"<h2>{t('rpt.portion_raw', w=f'{portion_g:.0f}')}</h2>\n"
            body += _macro_row(port["p"], port["f"], port["c"], port["kcal"])
        if cfg.get("portion_prepared") and has_prep:
            portp = calc_portion(prep_totals, prepared_weight, portion_g)
            body += f"<h2>{t('rpt.portion_prep', w=f'{portion_g:.0f}')}</h2>\n"
            body += _macro_row(portp["p"], portp["f"], portp["c"], portp["kcal"])

    if not body.strip():
        body = f'<div class="warn">{t("rpt.no_content")}</div>'

    return _html_wrap(t("rpt.meal_report"), body, dark, lang_code=lang.get_lang())


# =============================================================================
# LOG HTML REPORT
# =============================================================================

def build_log_html(log_data, cfg, dark):
    entries      = log_data["entries"]
    period_start = log_data["period_start"]
    period_end   = log_data["period_end"]

    s_fmt = period_start.strftime("%d-%m-%Y")
    e_fmt = period_end.strftime("%d-%m-%Y")
    body  = f"<h2>{t('rpt.period', start=s_fmt, end=e_fmt)}</h2>\n"
    has_content = False

    # Period average
    if cfg.get("log_daily_average"):
        days_data, _ = get_daily_summary(entries, period_start, period_end)
        avgs = compute_period_averages(days_data, include_empty=False)
        if avgs["days_counted"] > 0:
            has_content = True
            body += f"<h3>{t('rpt.daily_avg', n=avgs['days_counted'])}</h3>\n"
            body += _macro_row(avgs["p"], avgs["f"], avgs["c"], avgs["kcal"],
                               tag=t("rpt.avg_per_day"))

    # Daily totals
    if cfg.get("log_daily_totals"):
        days_data, _ = get_daily_summary(entries, period_start, period_end)
        days_with_data = {d: v for d, v in days_data.items() if v["entries"]}
        if days_with_data:
            has_content = True
            p_h = t("mb.abbr_p")
            f_h = t("mb.abbr_f")
            c_h = t("mb.abbr_c")
            body += f"<h2>{t('rpt.daily_totals')}</h2>\n"
            body += (f"<table><thead><tr>"
                     f"<th>{t('rpt.col_date')}</th>"
                     f"<th>{t('rpt.col_meals_count')}</th>"
                     f"<th>kcal</th>"
                     f"<th>{p_h} (g)</th>"
                     f"<th>{f_h} (g)</th>"
                     f"<th>{c_h} (g)</th>"
                     f"</tr></thead><tbody>\n")
            for d in sorted(days_with_data.keys()):
                v = days_with_data[d]
                body += (f"<tr>"
                         f"<td>{d.strftime('%d-%m-%Y')}</td>"
                         f"<td>{len(v['entries'])}</td>"
                         f"<td><strong>{v['kcal']:.0f}</strong></td>"
                         f"<td>{v['p']:.1f}</td>"
                         f"<td>{v['f']:.1f}</td>"
                         f"<td>{v['c']:.1f}</td>"
                         f"</tr>\n")
            body += "</tbody></table>\n"

    # Individual entries
    if cfg.get("log_per_meal"):
        if entries:
            has_content = True
            p_h = t("mb.abbr_p")
            f_h = t("mb.abbr_f")
            c_h = t("mb.abbr_c")
            body += f"<h2>{t('rpt.individual')}</h2>\n"
            body += (f"<table><thead><tr>"
                     f"<th>{t('rpt.col_date')}</th>"
                     f"<th>{t('rpt.col_meal')}</th>"
                     f"<th>{t('rpt.col_portion')}</th>"
                     f"<th>kcal</th>"
                     f"<th>{p_h} (g)</th>"
                     f"<th>{f_h} (g)</th>"
                     f"<th>{c_h} (g)</th>"
                     f"<th>{t('rpt.col_notes')}</th>"
                     f"</tr></thead><tbody>\n")

            for e in sorted(entries, key=lambda x: x["datetime"]):
                try:
                    dt_str = datetime.strptime(
                        e["datetime"],
                        "%Y-%m-%dT%H:%M:%S").strftime("%d-%m-%Y %H:%M")
                except Exception:
                    dt_str = e["datetime"].replace("T", " ")[:16]

                kcal, p, f, c = entry_macros(e)
                pg     = e.get("portion_g")
                pg_str = f"{pg:.0f}" if pg else "—"
                nm     = escape(e.get("meal_name", "—"))
                notes  = escape((e.get("notes") or "")[:80] or "—")

                body += (f"<tr>"
                         f"<td>{dt_str}</td>"
                         f"<td><strong>{nm}</strong></td>"
                         f"<td>{pg_str}</td>"
                         f"<td>{kcal:.0f}</td>"
                         f"<td>{p:.1f}</td>"
                         f"<td>{f:.1f}</td>"
                         f"<td>{c:.1f}</td>"
                         f"<td style='color:var(--muted)'>{notes}</td>"
                         f"</tr>\n")

            body += "</tbody></table>\n"

    if not entries:
        body += f'<div class="note">{t("rpt.no_entries")}</div>\n'
    elif not has_content:
        body += f'<div class="warn">{t("rpt.no_content")}</div>'

    return _html_wrap(t("rpt.journal_report"), body, dark, lang_code=lang.get_lang())

# =============================================================================
# RECIPE HTML REPORT
# =============================================================================

def build_recipe_html(recipe_data, cfg, dark):
    rd       = recipe_data
    name     = escape(rd.get("name", "Recipe"))
    created  = rd.get("created", "")
    notes    = escape(rd.get("notes", ""))
    serving_g      = rd.get("serving_g")
    raw_weight     = rd.get("raw_weight", 0)
    raw_totals     = rd.get("raw_totals", {})
    prepared_weight = rd.get("prepared_weight")
    prep_totals    = rd.get("prep_totals")
    ingredients    = rd.get("ingredients", [])
    has_prep       = bool(prepared_weight and prep_totals)

    try:
        created_fmt = datetime.strptime(
            created, "%Y-%m-%dT%H:%M:%S").strftime("%d-%m-%Y %H:%M")
    except Exception:
        created_fmt = created[:16]

    body = f"<h2>{name}</h2>\n"
    body += f'<div class="note">{t("rpt.recipe_created", dt=created_fmt)}'
    if notes:
        body += f"<br>{t('rpt.recipe_notes')}: {notes}"
    body += "</div>\n"

    if cfg.get("recipe_ingredients") and ingredients:
        body += f"<h2>{t('rpt.ingredients')}</h2>\n"
        body += _ingredients_table(ingredients)

    if cfg.get("recipe_raw"):
        body += f"<h2>{t('rpt.whole_meal_raw', w=f'{raw_weight:.1f}')}</h2>\n"
        body += _macro_row(raw_totals.get("p", 0), raw_totals.get("f", 0),
                           raw_totals.get("c", 0), raw_totals.get("kcal", 0))

    if cfg.get("recipe_prepared") and has_prep:
        body += (f"<h2>"
                 f"{t('rpt.whole_meal_prep', w=f'{prepared_weight:.1f}')}"
                 f"</h2>\n")
        body += _macro_row(prep_totals.get("p", 0), prep_totals.get("f", 0),
                           prep_totals.get("c", 0), prep_totals.get("kcal", 0))

    if cfg.get("recipe_per100_raw") and raw_weight > 0:
        p100 = calc_per_100g(raw_totals, raw_weight)
        body += f"<h2>{t('rpt.per100_raw')}</h2>\n"
        body += _macro_row(p100["p"], p100["f"], p100["c"], p100["kcal"])

    if cfg.get("recipe_per100_prepared") and has_prep:
        p100p = calc_per_100g(prep_totals, prepared_weight)
        body += f"<h2>{t('rpt.per100_prep')}</h2>\n"
        body += _macro_row(p100p["p"], p100p["f"], p100p["c"], p100p["kcal"])

    if cfg.get("recipe_per_serving") and serving_g:
        ref_t  = prep_totals if has_prep else raw_totals
        ref_w  = prepared_weight if has_prep else raw_weight
        if ref_w:
            port = calc_portion(ref_t, ref_w, serving_g)
            body += f"<h2>{t('rpt.recipe_serving', w=f'{serving_g:.0f}')}</h2>\n"
            body += _macro_row(port["p"], port["f"], port["c"], port["kcal"])

    if not body.strip():
        body = f'<div class="warn">{t("rpt.no_content")}</div>'

    return _html_wrap(name, body, dark, lang_code=lang.get_lang())

