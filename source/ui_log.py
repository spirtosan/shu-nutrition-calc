# =============================================================================
# ui_log.py — Shu Nutrition Calc v5.3
# Journal tab: view, add, edit, delete meal log entries.
# Period selector with daily summary and missing days handling.
# LogEntryDialog: called from MealBuilderFrame to record a meal.
# All UI strings via t().
# =============================================================================

import customtkinter as ctk
from tkinter import messagebox, Listbox, SINGLE, END
from datetime import datetime, date, timedelta
from models import (load_log, save_log, new_log_entry, _entry_macros,
                    get_period_entries, get_daily_summary,
                    find_missing_periods, compute_period_averages,
                    calc_portion, SaveError)
from config import APP_NAME
from lang import t

try:
    from tkcalendar import DateEntry
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False


# =============================================================================
# JOURNAL FRAME
# =============================================================================

class JournalFrame(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._current_entries = []
        self._period_start    = date.today()
        self._period_end      = date.today()
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Period selector ───────────────────────────────────────────
        period_f = ctk.CTkFrame(self, fg_color="#2b2b2b")
        period_f.pack(fill="x", padx=20, pady=(15, 6))

        ctk.CTkLabel(period_f, text=t("jrn.period_label"),
                     font=("Arial", 12, "bold")).pack(side="left", padx=10)

        period_labels = [
            t("jrn.period_today"),
            t("jrn.period_yesterday"),
            t("jrn.period_last7"),
            t("jrn.period_last30"),
            t("jrn.period_last_month"),
            t("jrn.period_last_year"),
            t("jrn.period_custom"),
        ]
        self.period_var = ctk.StringVar(value=period_labels[0])
        ctk.CTkOptionMenu(
            period_f, values=period_labels,
            variable=self.period_var,
            command=self._on_period_change,
            width=160).pack(side="left", padx=6)

        self.custom_f = ctk.CTkFrame(period_f, fg_color="transparent")
        ctk.CTkLabel(self.custom_f, text=t("jrn.from_label")).pack(
            side="left", padx=4)

        if HAS_CALENDAR:
            self.date_from = DateEntry(self.custom_f, width=11,
                                       date_pattern="dd-mm-yyyy",
                                       firstweekday="monday",
                                       background="#1e1e2a", foreground="white")
            self.date_to   = DateEntry(self.custom_f, width=11,
                                       date_pattern="dd-mm-yyyy",
                                       firstweekday="monday",
                                       background="#1e1e2a", foreground="white")
        else:
            self.date_from = ctk.CTkEntry(self.custom_f, width=100,
                                          placeholder_text="DD-MM-YYYY")
            self.date_to   = ctk.CTkEntry(self.custom_f, width=100,
                                          placeholder_text="DD-MM-YYYY")

        self.date_from.pack(side="left", padx=4)
        ctk.CTkLabel(self.custom_f, text=t("jrn.to_label")).pack(
            side="left", padx=4)
        self.date_to.pack(side="left", padx=4)
        ctk.CTkButton(self.custom_f, text=t("jrn.btn_apply"), width=80,
                      fg_color="#3a5a3a",
                      command=self._apply_custom).pack(side="left", padx=6)
        self.custom_f.pack_forget()

        ctk.CTkButton(period_f, text=t("jrn.btn_refresh"),
                      width=90, fg_color="#3a5a3a",
                      command=self.refresh).pack(side="right", padx=10)

        # ── Summary bar ───────────────────────────────────────────────
        self.summary_f = ctk.CTkFrame(self, fg_color="#181818",
                                       border_width=1, border_color="#333")
        self.summary_f.pack(fill="x", padx=20, pady=4)

        self.lbl_summary = ctk.CTkLabel(
            self.summary_f,
            text=t("jrn.summary_placeholder"),
            font=("Segoe UI", 13, "bold"),
            text_color="#f5a623")
        self.lbl_summary.pack(pady=6)

        # Missing days warning bar
        self.missing_f = ctk.CTkFrame(self, fg_color="#1c1400",
                                       border_width=1, border_color="#c87028")
        self.lbl_missing = ctk.CTkLabel(
            self.missing_f, text="",
            font=("Segoe UI", 12), text_color="#f5a623",
            wraplength=700)
        self.lbl_missing.pack(side="left", padx=12, pady=6,
                               fill="x", expand=True)
        self.missing_f.pack_forget()

        self.missing_btn_f = ctk.CTkFrame(self, fg_color="transparent")
        ctk.CTkButton(self.missing_btn_f,
                      text=t("jrn.btn_show_entries"), width=170,
                      fg_color="#3a5a3a",
                      command=lambda: self._apply_missing_mode("entries")).pack(
                          side="left", padx=6)
        ctk.CTkButton(self.missing_btn_f,
                      text=t("jrn.btn_include_empty"), width=220,
                      fg_color="#3a5a3a",
                      command=lambda: self._apply_missing_mode("all")).pack(
                          side="left", padx=6)
        ctk.CTkButton(self.missing_btn_f,
                      text=t("jrn.btn_fill_missing"), width=170,
                      fg_color="#c87028",
                      command=self._fill_missing_days).pack(
                          side="left", padx=6)
        self.missing_btn_f.pack_forget()

        # ── Column headers ────────────────────────────────────────────
        list_lbl_f = ctk.CTkFrame(self, fg_color="transparent")
        list_lbl_f.pack(fill="x", padx=20, pady=(8, 2))
        for col_key, w in [
            ("jrn.col_datetime",  160),
            ("jrn.col_meal_name", 200),
            ("jrn.col_portion",    90),
            ("jrn.col_kcal",       70),
            ("jrn.col_p",          60),
            ("jrn.col_f",          60),
            ("jrn.col_c",          60),
        ]:
            ctk.CTkLabel(list_lbl_f, text=t(col_key), width=w,
                         font=("Segoe UI", 12, "bold"),
                         text_color="gray").pack(side="left", padx=4)

        # ── Entry list ────────────────────────────────────────────────
        self.entry_list = Listbox(
            self, font=("Consolas", 12),
            bg="#181818", fg="white",
            borderwidth=0, selectmode=SINGLE,
            activestyle="none", height=14)
        self.entry_list.pack(fill="both", expand=True, padx=20, pady=4)
        self.entry_list.bind("<Double-Button-1>", self._edit_entry)

        # ── Action buttons ────────────────────────────────────────────
        act_f = ctk.CTkFrame(self, fg_color="transparent")
        act_f.pack(pady=8)

        ctk.CTkButton(act_f, text=t("jrn.btn_add_entry"),
                      fg_color="#2a8a38",
                      command=self._add_manual_entry).pack(side="left", padx=8)
        ctk.CTkButton(act_f, text=t("jrn.btn_edit"),
                      fg_color="#1a7878",
                      command=self._edit_entry).pack(side="left", padx=8)
        ctk.CTkButton(act_f, text=t("jrn.btn_delete"),
                      fg_color="#8B0000",
                      command=self._delete_entry).pack(side="left", padx=8)

        self.print_log_btn = ctk.CTkButton(
            act_f, text=t("jrn.btn_print_log"),
            fg_color="#4a4a4a", text_color="#aaaaaa",
            state="disabled", command=self._print_log)
        self.print_log_btn.pack(side="left", padx=8)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def refresh(self):
        self.app.log = load_log()
        self._apply_period()

    # ------------------------------------------------------------------
    # Period handling
    # ------------------------------------------------------------------

    def _on_period_change(self, value):
        if value == t("jrn.period_custom"):
            self.custom_f.pack(side="left", padx=6)
        else:
            self.custom_f.pack_forget()
            self._apply_period()

    def _apply_custom(self):
        try:
            if HAS_CALENDAR:
                s = self.date_from.get_date()
                e = self.date_to.get_date()
            else:
                s = datetime.strptime(self.date_from.get(), "%d-%m-%Y").date()
                e = datetime.strptime(self.date_to.get(),   "%d-%m-%Y").date()
            if s > e:
                messagebox.showwarning(t("jrn.err_date_title"),
                                       t("jrn.err_date_range"))
                return
            self._period_start = s
            self._period_end   = e
            self._load_period(s, e)
        except Exception:
            messagebox.showerror(t("jrn.err_date_title"),
                                 t("jrn.err_date_format"))

    def _apply_period(self):
        today = date.today()
        val   = self.period_var.get()
        if   val == t("jrn.period_today"):
            s, e = today, today
        elif val == t("jrn.period_yesterday"):
            d = today - timedelta(1); s, e = d, d
        elif val == t("jrn.period_last7"):
            s, e = today - timedelta(6), today
        elif val == t("jrn.period_last30"):
            s, e = today - timedelta(29), today
        elif val == t("jrn.period_last_month"):
            first = today.replace(day=1)
            lme   = first - timedelta(1)
            s = lme.replace(day=1); e = lme
        elif val == t("jrn.period_last_year"):
            s = today.replace(year=today.year-1, month=1,  day=1)
            e = today.replace(year=today.year-1, month=12, day=31)
        else:
            return
        self._period_start = s
        self._period_end   = e
        self._load_period(s, e)

    def _load_period(self, start, end):
        entries = get_period_entries(self.app.log, start, end)
        self._current_entries = entries
        self._populate_list(entries)
        self._compute_and_show_summary(start, end, mode="entries")
        if entries:
            self.print_log_btn.configure(state="normal",
                                          fg_color="#1a7878",
                                          text_color="white")
        else:
            self.print_log_btn.configure(state="disabled",
                                          fg_color="#4a4a4a",
                                          text_color="#aaaaaa")

    def _compute_and_show_summary(self, start, end, mode="entries"):
        days_data, missing = get_daily_summary(self.app.log, start, end)
        avgs = compute_period_averages(days_data,
                                       include_empty=(mode == "all"))
        days_label = t("jrn.days_counted",
                       n=avgs["days_counted"], total=avgs["days_total"])
        s_fmt = start.strftime("%d-%m-%Y")
        e_fmt = end.strftime("%d-%m-%Y")
        self.lbl_summary.configure(
            text=t("jrn.summary_text",
                   start=s_fmt, end=e_fmt,
                   days=days_label,
                   k=f"{avgs['kcal']:.0f}",
                   p=f"{avgs['p']:.1f}",
                   f=f"{avgs['f']:.1f}",
                   c=f"{avgs['c']:.1f}"))

        if missing:
            periods = find_missing_periods(missing)
            if len(periods) > 3:
                msg = t("jrn.missing_many",
                        n=len(missing), gaps=len(periods))
            else:
                gap_strs = [
                    p[0].strftime("%d-%m-%Y") if p[0] == p[1]
                    else f"{p[0].strftime('%d-%m-%Y')} – {p[1].strftime('%d-%m-%Y')}"
                    for p in periods
                ]
                msg = t("jrn.missing_nodata", dates=",  ".join(gap_strs))
            self.lbl_missing.configure(text=msg)
            self.missing_f.pack(fill="x", padx=20, pady=2)
            self.missing_btn_f.pack(fill="x", padx=20, pady=2)
        else:
            self.missing_f.pack_forget()
            self.missing_btn_f.pack_forget()

    def _apply_missing_mode(self, mode):
        self._compute_and_show_summary(
            self._period_start, self._period_end, mode=mode)

    def _fill_missing_days(self):
        _, missing = get_daily_summary(
            self.app.log, self._period_start, self._period_end)
        if not missing:
            messagebox.showinfo(t("jrn.info_no_missing_title"),
                                t("jrn.info_no_missing_msg"))
            return
        FillMissingDialog(self, self.app, missing, on_done=self.refresh)

    # ------------------------------------------------------------------
    # List population
    # ------------------------------------------------------------------

    def _populate_list(self, entries):
        self.entry_list.delete(0, END)
        for e in sorted(entries, key=lambda x: x["datetime"], reverse=True):
            try:
                dt_obj = datetime.strptime(e["datetime"],
                                           "%Y-%m-%dT%H:%M:%S")
                dt_str = dt_obj.strftime("%d-%m-%Y %H:%M")
            except Exception:
                dt_str = e["datetime"].replace("T", " ")[:16]

            nm = e.get("meal_name", "—")[:22]
            kcal, p, f, c = _entry_macros(e)
            pg = e.get("portion_g")
            pg_str = f"{pg:.0f}" if pg else "—"

            self.entry_list.insert(
                END,
                f"{dt_str:<18}  {nm:<24}  "
                f"{pg_str:>8}g  {kcal:>7.0f}  "
                f"{p:>6.1f}  {f:>6.1f}  {c:>6.1f}")

    def _get_selected_entry(self):
        sel = self.entry_list.curselection()
        if not sel:
            return None
        sorted_entries = sorted(self._current_entries,
                                key=lambda x: x["datetime"], reverse=True)
        if sel[0] >= len(sorted_entries):
            return None
        return sorted_entries[sel[0]]

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def _add_manual_entry(self):
        EditEntryDialog(self, self.app, entry=None,
                        on_save=self._on_entry_saved)

    def _edit_entry(self, _event=None):
        entry = self._get_selected_entry()
        if not entry:
            messagebox.showinfo(t("jrn.info_no_selection"),
                                t("jrn.info_select_edit"))
            return
        EditEntryDialog(self, self.app, entry=entry,
                        on_save=self._on_entry_saved)

    def _delete_entry(self):
        entry = self._get_selected_entry()
        if not entry:
            messagebox.showinfo(t("jrn.info_no_selection"),
                                t("jrn.info_select_del"))
            return
        nm = entry.get("meal_name", "this entry")
        if messagebox.askyesno(t("jrn.confirm_delete_title"),
                               t("jrn.confirm_delete_msg", name=nm)):
            self.app.log = [e for e in self.app.log
                            if e["id"] != entry["id"]]
            try:
                save_log(self.app.log)
            except SaveError as e:
                messagebox.showerror("Save Error",
                                     f"Could not save {e.filename}:\n{e.strerror}")
                return
            self.refresh()

    def _on_entry_saved(self):
        try:
            save_log(self.app.log)
        except SaveError as e:
            messagebox.showerror("Save Error",
                                 f"Could not save {e.filename}:\n{e.strerror}")
            return
        self.refresh()

    # ------------------------------------------------------------------
    # Print log
    # ------------------------------------------------------------------

    def _print_log(self):
        from ui_print import PrintDialog
        dlg = PrintDialog(
            parent=self, app=self.app, mode="log",
            log_data={
                "entries":      self._current_entries,
                "period_start": self._period_start,
                "period_end":   self._period_end,
            })
        self.wait_window(dlg)


# =============================================================================
# LOG ENTRY DIALOG  (called from Meal Builder)
# =============================================================================

class LogEntryDialog(ctk.CTkToplevel):

    def __init__(self, parent, app,
                 ref_totals, ref_weight,
                 prefill_portion, last_logged_name):
        super().__init__(parent)
        self.app              = app
        self.ref_totals       = ref_totals
        self.ref_weight       = ref_weight
        self.prefill_portion  = prefill_portion
        self.last_logged_name = last_logged_name
        self.result           = None

        self.title(t("atj.title"))
        self.geometry("560x460")
        self.resizable(True, False)
        self._build_ui()
        self.transient(parent.winfo_toplevel())
        self.update_idletasks()
        self.lift()
        self.grab_set()
        self.focus_force()

    def _build_ui(self):
        ctk.CTkLabel(self, text=t("atj.heading"),
                     font=("Segoe UI", 17, "bold"),
                     text_color="#f5a623").pack(pady=(18, 8))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=24)
        grid.columnconfigure(1, weight=1)

        # Meal name
        ctk.CTkLabel(grid, text=t("atj.meal_name_label"), width=120,
                     anchor="w").grid(row=0, column=0, pady=6, sticky="w")
        self.name_ent = ctk.CTkEntry(
            grid, width=300,
            placeholder_text=t("atj.meal_name_ph"))
        if self.last_logged_name:
            self.name_ent.insert(0, self.last_logged_name)
        self.name_ent.grid(row=0, column=1, pady=6, sticky="w")

        # Date/time
        ctk.CTkLabel(grid, text=t("atj.datetime_label"), width=120,
                     anchor="w").grid(row=1, column=0, pady=6, sticky="w")

        dt_f = ctk.CTkFrame(grid, fg_color="transparent")
        dt_f.grid(row=1, column=1, pady=6, sticky="w")

        self.use_now_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(dt_f, text=t("atj.use_current_time"),
                        variable=self.use_now_var,
                        command=self._toggle_datetime).pack(side="left")

        self.dt_frame = ctk.CTkFrame(dt_f, fg_color="transparent")
        if HAS_CALENDAR:
            self.cal_entry = DateEntry(self.dt_frame, width=11,
                                       date_pattern="dd-mm-yyyy",
                                       firstweekday="monday")
            self.cal_entry.pack(side="left", padx=4)
        else:
            self.cal_entry = ctk.CTkEntry(self.dt_frame, width=100,
                                          placeholder_text="DD-MM-YYYY")
            self.cal_entry.pack(side="left", padx=4)
        self.time_ent = ctk.CTkEntry(self.dt_frame, width=80,
                                     placeholder_text="HH:MM")
        self.time_ent.pack(side="left", padx=4)
        self.dt_frame.pack_forget()

        # Portion
        ctk.CTkLabel(grid, text=t("atj.portion_label"), width=120,
                     anchor="w").grid(row=2, column=0, pady=6, sticky="w")
        port_f = ctk.CTkFrame(grid, fg_color="transparent")
        port_f.grid(row=2, column=1, pady=6, sticky="w")
        self.portion_ent = ctk.CTkEntry(
            port_f, width=100,
            placeholder_text=t("atj.portion_ph"))
        if self.prefill_portion:
            self.portion_ent.insert(0, f"{self.prefill_portion:.0f}")
        self.portion_ent.pack(side="left")
        self.portion_ent.bind("<KeyRelease>",
                               lambda _e: self._update_preview())
        hint = (t("atj.hint_from_builder") if self.prefill_portion
                else t("atj.hint_enter_amount"))
        ctk.CTkLabel(port_f, text=hint,
                     font=("Segoe UI", 12),
                     text_color="#909090").pack(side="left", padx=8)

        # Notes
        ctk.CTkLabel(grid, text=t("atj.notes_label"), width=120,
                     anchor="nw").grid(row=3, column=0, pady=6, sticky="nw")
        self.notes_ent = ctk.CTkTextbox(grid, height=55, width=300)
        self.notes_ent.grid(row=3, column=1, pady=6, sticky="w")

        # Live preview
        self.preview_f = ctk.CTkFrame(self, fg_color="#181818",
                                       border_width=1, border_color="#333")
        self.preview_f.pack(fill="x", padx=24, pady=6)
        self.lbl_preview = ctk.CTkLabel(
            self.preview_f,
            text=t("atj.preview_placeholder"),
            font=("Consolas", 12), text_color="#909090",
            anchor="w", justify="left", wraplength=490)
        self.lbl_preview.pack(fill="x", padx=12, pady=10)
        self._update_preview()

        # Buttons
        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(pady=12)
        ctk.CTkButton(btn_f, text=t("atj.btn_save"),
                      fg_color="#2a8a38",
                      command=self._save).pack(side="left", padx=12)
        ctk.CTkButton(btn_f, text=t("atj.btn_cancel"),
                      fg_color="#8B0000",
                      command=self.destroy).pack(side="left", padx=12)

    def _toggle_datetime(self):
        if self.use_now_var.get():
            self.dt_frame.pack_forget()
        else:
            self.dt_frame.pack(side="left", padx=8)

    def _update_preview(self):
        try:
            pg = float(self.portion_ent.get())
            if pg <= 0:
                raise ValueError
            p = round(self.ref_totals["p"]    / self.ref_weight * pg, 1)
            f = round(self.ref_totals["f"]    / self.ref_weight * pg, 1)
            c = round(self.ref_totals["c"]    / self.ref_weight * pg, 1)
            k = round(self.ref_totals["kcal"] / self.ref_weight * pg, 0)
            self.lbl_preview.configure(
                text=t("atj.preview_text",
                        p=f"{pg:.0f}", pp=f"{p:.1f}",
                        f=f"{f:.1f}", c=f"{c:.1f}", k=f"{k:.0f}"),
                text_color="#2ecc71")
        except (ValueError, ZeroDivisionError):
            self.lbl_preview.configure(
                text=t("atj.preview_placeholder"),
                text_color="#909090")

    def _save(self):
        name = self.name_ent.get().strip() or t("atj.unnamed_meal")

        # Duplicate check
        today_entries = [
            e for e in self.app.log
            if (e.get("meal_name", "").lower() == name.lower() and
                e["datetime"][:10] == date.today().isoformat())
        ]
        if today_entries:
            from tkinter import messagebox as mb
            if not mb.askyesno(
                    t("atj.confirm_dup_title"),
                    t("atj.confirm_dup_msg",
                      name=name, n=len(today_entries))):
                return

        # Portion — required
        try:
            pg = float(self.portion_ent.get())
            if pg <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(t("atj.err_portion_title"),
                                   t("atj.err_portion_msg"))
            return

        # Datetime
        if self.use_now_var.get():
            dt = datetime.now()
        else:
            try:
                if HAS_CALENDAR:
                    d_val = self.cal_entry.get_date()
                else:
                    d_val = datetime.strptime(
                        self.cal_entry.get(), "%d-%m-%Y").date()
                t_str = self.time_ent.get().strip() or "00:00"
                hh, mm = map(int, t_str.split(":"))
                dt = datetime(d_val.year, d_val.month, d_val.day, hh, mm)
            except Exception:
                messagebox.showerror(t("atj.err_datetime_title"),
                                     t("atj.err_datetime_msg"))
                return

        notes = self.notes_ent.get("1.0", END).strip()

        rw = self.ref_weight
        rt = self.ref_totals
        p    = round(rt["p"]    / rw * pg, 1)
        f    = round(rt["f"]    / rw * pg, 1)
        c    = round(rt["c"]    / rw * pg, 1)
        kcal = round(rt["kcal"] / rw * pg, 0)

        entry = new_log_entry(
            meal_name=name, portion_g=pg,
            p=p, f=f, c=c, kcal=kcal,
            dt=dt, notes=notes)

        self.app.log.append(entry)
        try:
            save_log(self.app.log)
        except SaveError as e:
            self.app.log.pop()
            messagebox.showerror("Save Error",
                                 f"Could not save {e.filename}:\n{e.strerror}")
            return
        self.result = entry
        self.destroy()


# =============================================================================
# EDIT ENTRY DIALOG
# =============================================================================

class EditEntryDialog(ctk.CTkToplevel):

    def __init__(self, parent, app, entry, on_save):
        super().__init__(parent)
        self.app     = app
        self.entry   = entry
        self.on_save = on_save
        is_new = entry is None
        self.title(t("edit.title_new") if is_new else t("edit.title_edit"))
        self.geometry("540x460")
        self.resizable(True, True)
        self._build_ui()
        self.transient(parent.winfo_toplevel())
        self.update_idletasks()
        self.lift()
        self.grab_set()
        self.focus_force()

    def _build_ui(self):
        e      = self.entry or {}
        is_new = self.entry is None
        is_new_fmt = "kcal" in e

        ctk.CTkLabel(self,
                     text=t("edit.heading_new") if is_new
                          else t("edit.heading_edit"),
                     font=("Segoe UI", 16, "bold"),
                     text_color="#f5a623").pack(pady=(18, 8))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=24)
        grid.columnconfigure(1, weight=1)

        # Meal name
        ctk.CTkLabel(grid, text=t("edit.meal_name_label"), width=120,
                     anchor="w").grid(row=0, column=0, pady=6, sticky="w")
        self.name_ent = ctk.CTkEntry(
            grid, placeholder_text=t("edit.meal_name_ph"))
        self.name_ent.insert(0, e.get("meal_name", ""))
        self.name_ent.grid(row=0, column=1, columnspan=3,
                            pady=6, sticky="ew")

        # Date/time
        ctk.CTkLabel(grid, text=t("edit.datetime_label"), width=120,
                     anchor="w").grid(row=1, column=0, pady=6, sticky="w")
        self.dt_ent = ctk.CTkEntry(
            grid, placeholder_text=t("edit.datetime_ph"))
        dt_src = e.get("datetime",
                       datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
        try:
            display_dt = datetime.strptime(dt_src[:16], "%Y-%m-%dT%H:%M")\
                                 .strftime("%d-%m-%Y %H:%M")
        except Exception:
            display_dt = dt_src.replace("T", " ")[:16]
        self.dt_ent.insert(0, display_dt)
        self.dt_ent.grid(row=1, column=1, columnspan=3,
                          pady=6, sticky="ew")

        row = 2

        if is_new:
            # Manual entry — kcal only
            note_f = ctk.CTkFrame(grid, fg_color="#1e1e1e",
                                   border_width=1, border_color="#2a2a2a",
                                   corner_radius=6)
            note_f.grid(row=row, column=0, columnspan=4,
                        sticky="ew", pady=(8, 4))
            ctk.CTkLabel(note_f, text=t("edit.tip_use_builder"),
                         font=("Segoe UI", 13), text_color="#cccccc",
                         justify="left", wraplength=460).pack(
                             anchor="w", padx=10, pady=8)
            row += 1

            ctk.CTkLabel(grid, text=t("edit.kcal_label"), width=120,
                         anchor="w").grid(row=row, column=0,
                                          pady=6, sticky="w")
            self._ent_k = ctk.CTkEntry(grid, width=120,
                                        placeholder_text="0")
            self._ent_k.grid(row=row, column=1, pady=6, sticky="w")
            row += 1

        elif is_new_fmt:
            # New-format entry — all fields editable
            fields = [
                (t("edit.portion_label"), "portion_g", 120),
                (t("edit.kcal_label"),    "kcal",      120),
                (t("edit.protein_label"), "p",         120),
                (t("edit.fat_label"),     "f",         120),
                (t("edit.carbs_label"),   "c",         120),
            ]
            self._macro_ents = {}
            for label, key, w in fields:
                ctk.CTkLabel(grid, text=label, width=120,
                             anchor="w").grid(row=row, column=0,
                                              pady=4, sticky="w")
                ent = ctk.CTkEntry(grid, width=w)
                val = e.get(key)
                if val is not None:
                    ent.insert(0, f"{val:.1f}"
                               if isinstance(val, float) else str(val))
                ent.grid(row=row, column=1, pady=4, sticky="w")
                self._macro_ents[key] = ent
                row += 1

        else:
            # Legacy entry — read-only snapshot
            kcal, p, f, c = _entry_macros(e)
            pg = e.get("portion_g")
            info = (f"{'Portion: ' + str(int(pg)) + 'g   ' if pg else ''}"
                    f"P:{p:.1f}  F:{f:.1f}  C:{c:.1f}  {kcal:.0f} kcal  "
                    f"{t('edit.legacy_readonly')}")
            ctk.CTkLabel(grid, text=info,
                         font=("Consolas", 12),
                         text_color="#909090",
                         wraplength=360).grid(row=row, column=0,
                                              columnspan=4,
                                              pady=4, sticky="w")
            row += 1

        # Notes
        ctk.CTkLabel(grid, text=t("edit.notes_label"), width=120,
                     anchor="nw").grid(row=row, column=0,
                                       pady=6, sticky="nw")
        self.notes_txt = ctk.CTkTextbox(grid, height=70)
        self.notes_txt.insert("1.0", e.get("notes", ""))
        self.notes_txt.grid(row=row, column=1, columnspan=3,
                             pady=6, sticky="ew")

        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(pady=14)
        ctk.CTkButton(btn_f, text=t("edit.btn_save"),
                      fg_color="#2a8a38",
                      command=self._save).pack(side="left", padx=12)
        ctk.CTkButton(btn_f, text=t("edit.btn_cancel"),
                      fg_color="#8B0000",
                      command=self.destroy).pack(side="left", padx=12)

    def _save(self):
        name   = self.name_ent.get().strip() or t("edit.unnamed")
        dt_str = self.dt_ent.get().strip()
        notes  = self.notes_txt.get("1.0", END).strip()

        try:
            dt = datetime.strptime(dt_str, "%d-%m-%Y %H:%M")
        except ValueError:
            messagebox.showerror(t("edit.err_date_title"),
                                 t("edit.err_date_msg"))
            return

        is_new    = self.entry is None
        is_new_fmt = self.entry is not None and "kcal" in self.entry

        if is_new:
            try:
                kcal = float(self._ent_k.get())
            except (ValueError, AttributeError):
                kcal = 0.0
            entry = new_log_entry(
                meal_name=name, portion_g=None,
                p=0, f=0, c=0, kcal=kcal,
                dt=dt, notes=notes)
            self.app.log.append(entry)

        elif is_new_fmt:
            def _fv(key, default=0.0):
                try:
                    return float(self._macro_ents[key].get())
                except (ValueError, KeyError):
                    return default

            for e in self.app.log:
                if e["id"] == self.entry["id"]:
                    e["meal_name"] = name
                    e["datetime"]  = dt.strftime("%Y-%m-%dT%H:%M:%S")
                    e["portion_g"] = _fv("portion_g") or None
                    e["kcal"]      = round(_fv("kcal"), 0)
                    e["p"]         = round(_fv("p"), 1)
                    e["f"]         = round(_fv("f"), 1)
                    e["c"]         = round(_fv("c"), 1)
                    e["notes"]     = notes
                    break
        else:
            # Legacy — update name/datetime/notes only
            for e in self.app.log:
                if e["id"] == self.entry["id"]:
                    e["meal_name"] = name
                    e["datetime"]  = dt.strftime("%Y-%m-%dT%H:%M:%S")
                    e["notes"]     = notes
                    break

        try:
            save_log(self.app.log)
        except SaveError as e:
            messagebox.showerror("Save Error",
                                 f"Could not save {e.filename}:\n{e.strerror}")
            return
        self.on_save()
        self.destroy()


# =============================================================================
# FILL MISSING DAYS DIALOG
# =============================================================================

class FillMissingDialog(ctk.CTkToplevel):

    def __init__(self, parent, app, missing_dates, on_done):
        super().__init__(parent)
        self.app           = app
        self.missing_dates = list(missing_dates)
        self.on_done       = on_done
        self.idx           = 0
        self.title(t("fill.title"))
        self.geometry("520x310")
        self.grab_set()
        self._build_ui()
        self._load_day()

    def _build_ui(self):
        self.lbl_day = ctk.CTkLabel(self, text="",
                                    font=("Segoe UI", 16, "bold"),
                                    text_color="#f5a623")
        self.lbl_day.pack(pady=(20, 4))

        self.lbl_progress = ctk.CTkLabel(self, text="",
                                         font=("Segoe UI", 13),
                                         text_color="#909090")
        self.lbl_progress.pack(pady=2)

        ctk.CTkLabel(self, text=t("fill.question"),
                     font=("Segoe UI", 13)).pack(pady=(10, 4))

        self._apply_all = ctk.BooleanVar(value=False)
        self._apply_all_cb = ctk.CTkCheckBox(
            self,
            text=t("fill.apply_all"),
            font=("Segoe UI", 13),
            variable=self._apply_all,
            command=self._on_apply_all_toggle)
        self._apply_all_cb.pack(pady=(0, 8))

        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(pady=8)
        self._skip_btn = ctk.CTkButton(
            btn_f, text=t("fill.btn_skip"),
            width=170, fg_color="#3a5a3a",
            command=self._skip)
        self._skip_btn.pack(side="left", padx=8)

        self._zero_btn = ctk.CTkButton(
            btn_f, text=t("fill.btn_zero"),
            width=140, fg_color="#3a5a3a",
            command=self._fill_zero)
        self._zero_btn.pack(side="left", padx=8)

        self._manual_btn = ctk.CTkButton(
            btn_f, text=t("fill.btn_manual"),
            width=140, fg_color="#c87028",
            command=self._enter_manual)
        self._manual_btn.pack(side="left", padx=8)

        ctk.CTkButton(self, text=t("fill.btn_done"),
                      fg_color="#8B0000",
                      command=self._finish).pack(pady=14)

    def _on_apply_all_toggle(self):
        if self._apply_all.get():
            self._manual_btn.configure(state="disabled")
        else:
            self._manual_btn.configure(state="normal")

    def _load_day(self):
        if self.idx >= len(self.missing_dates):
            self._finish()
            return
        d = self.missing_dates[self.idx]
        self.lbl_day.configure(text=d.strftime("%d-%m-%Y"))
        self.lbl_progress.configure(
            text=t("fill.progress",
                   n=self.idx + 1, total=len(self.missing_dates)))

    def _skip(self):
        if self._apply_all.get():
            self.idx = len(self.missing_dates)
        else:
            self.idx += 1
        self._load_day()

    def _fill_zero(self):
        targets = (self.missing_dates[self.idx:]
                   if self._apply_all.get()
                   else [self.missing_dates[self.idx]])
        for d in targets:
            dt = datetime(d.year, d.month, d.day, 0, 0, 0)
            entry = new_log_entry(
                meal_name=t("fill.zeroed_name"),
                portion_g=None, p=0, f=0, c=0, kcal=0,
                dt=dt, notes=t("fill.zeroed_notes"))
            self.app.log.append(entry)
        try:
            save_log(self.app.log)
        except SaveError as e:
            messagebox.showerror("Save Error",
                                 f"Could not save {e.filename}:\n{e.strerror}")
            return
        self.idx = (len(self.missing_dates)
                    if self._apply_all.get() else self.idx + 1)
        self._load_day()

    def _enter_manual(self):
        d = self.missing_dates[self.idx]
        pre_entry = {
            "id":        "",
            "datetime":  f"{d}T00:00:00",
            "meal_name": "",
            "kcal":      0.0,
            "p": 0.0, "f": 0.0, "c": 0.0,
            "portion_g": None,
            "notes":     "",
        }

        def on_saved():
            try:
                save_log(self.app.log)
            except SaveError as e:
                messagebox.showerror("Save Error",
                                     f"Could not save {e.filename}:\n{e.strerror}")
                return
            self.idx += 1
            self._load_day()

        EditEntryDialog(self, self.app, entry=pre_entry, on_save=on_saved)

    def _finish(self):
        try:
            save_log(self.app.log)
        except SaveError as e:
            messagebox.showerror("Save Error",
                                 f"Could not save {e.filename}:\n{e.strerror}")
            return
        self.on_done()
        self.destroy()
