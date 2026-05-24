# =============================================================================
# ui_meal_builder.py — Shu Nutrition Calc v5.3
# Meal Builder tab: search, add, prepared weight, portion, journal, print,
# save as recipe, clear. All UI strings via t().
# =============================================================================

import uuid
import customtkinter as ctk
from tkinter import messagebox, simpledialog, Listbox, END
from datetime import datetime
from models import (save_db, new_log_entry, save_log, new_recipe, save_recipes,
                    calc_prepared, calc_per_100g, calc_portion,
                    load_print_config, save_print_config, SaveError)
from config import APP_NAME
from lang import t


class MealBuilderFrame(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app

        self.current_recipe  = []
        self.prepared_weight = None
        self.show_prepared   = False
        self._last_logged_name = None

        cfg = load_print_config()
        self._use_whole = ctk.BooleanVar(
            value=cfg.get("use_whole_meal_as_portion", False))

        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Search / Add row ──────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="#2b2b2b")
        top.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(top, text=t("mb.search_label")).grid(
            row=0, column=0, padx=10, pady=10)
        self.search_ent = ctk.CTkEntry(
            top, width=320,
            placeholder_text=t("mb.search_placeholder"))
        self.search_ent.grid(row=0, column=1, padx=5)
        self.search_ent.bind("<KeyRelease>", self._filter_search)

        ctk.CTkLabel(top, text=t("mb.weight_label")).grid(
            row=0, column=2, padx=10)
        self.weight_ent = ctk.CTkEntry(
            top, width=80,
            placeholder_text=t("mb.weight_placeholder"))
        self.weight_ent.grid(row=0, column=3, padx=5)
        self.weight_ent.bind("<Return>", lambda _e: self._add_item())

        ctk.CTkButton(top, text=t("mb.btn_add_to_meal"), width=130,
                      fg_color="#c87028", hover_color="#d4902e",
                      command=self._add_item).grid(row=0, column=4, padx=15)

        # ── Search results dropdown ───────────────────────────────────
        self.search_list = Listbox(
            self, height=5, font=("Arial", 12),
            bg="#1e1e1e", fg="white",
            borderwidth=0, highlightthickness=1)
        self.search_list.pack(fill="x", padx=150, pady=(0, 8))
        self.search_list.bind("<<ListboxSelect>>", self._select_search)
        self.search_list.bind("<Return>",
                              lambda _e: self.weight_ent.focus_set())

        # ── Meal contents textbox ─────────────────────────────────────
        self.meal_txt = ctk.CTkTextbox(
            self, font=("Consolas", 13), height=220, state="disabled")
        self.meal_txt.pack(fill="both", expand=True, padx=20)
        self.meal_txt.bind("<Double-Button-1>", self._remove_item)

        # ── Prepared weight row ───────────────────────────────────────
        prep_f = ctk.CTkFrame(self, fg_color="#1e1e1e",
                               border_width=1, border_color="#2a2a2a")
        prep_f.pack(fill="x", padx=20, pady=(10, 4))

        ctk.CTkLabel(prep_f, text=t("mb.prepared_label"),
                     font=("Arial", 12)).pack(side="left", padx=14, pady=8)

        self.prep_ent = ctk.CTkEntry(
            prep_f, width=130,
            placeholder_text=t("mb.prepared_placeholder"))
        self.prep_ent.pack(side="left", padx=6)
        self.prep_ent.bind("<KeyRelease>", self._on_prep_weight_change)

        self.prep_status = ctk.CTkLabel(
            prep_f, text="", font=("Segoe UI", 12), text_color="#909090")
        self.prep_status.pack(side="left", padx=10)

        toggle_right = ctk.CTkFrame(prep_f, fg_color="transparent")
        toggle_right.pack(side="right", padx=14, pady=8)

        self.state_indicator = ctk.CTkLabel(
            toggle_right, text=t("mb.viewing_raw"),
            font=("Segoe UI", 12, "bold"), text_color="#909090")
        self.state_indicator.pack(side="left", padx=(0, 8))

        self.toggle_btn = ctk.CTkButton(
            toggle_right, text=t("mb.btn_switch_prepared"),
            width=185, fg_color="#4a4a4a", state="disabled",
            command=self._toggle_prepared)
        self.toggle_btn.pack(side="left")

        # ── Results summary ───────────────────────────────────────────
        res_f = ctk.CTkFrame(self, fg_color="#181818",
                              border_width=1, border_color="#333")
        res_f.pack(fill="x", padx=20, pady=8)

        self.lbl_weight = ctk.CTkLabel(
            res_f,
            text=t("mb.whole_weight",
                   mode=t("mb.mode_raw"), w="0.0"),
            font=("Segoe UI", 15, "bold"), text_color="#f5a623")
        self.lbl_weight.pack(pady=(10, 2))

        self.lbl_whole = ctk.CTkLabel(
            res_f,
            text=t("mb.whole_macros", p="0.0", f="0.0", c="0.0", k="0"),
            font=("Segoe UI", 13, "bold"))
        self.lbl_whole.pack(pady=2)

        self.lbl_100g = ctk.CTkLabel(
            res_f,
            text=t("mb.per100_macros", p="0.0", f="0.0", c="0.0", k="0"),
            font=("Segoe UI", 16, "bold"), text_color="#f5a623")
        self.lbl_100g.pack(pady=(2, 4))

        self.lbl_warn = ctk.CTkLabel(
            res_f, text="",
            font=("Segoe UI", 12, "bold"), text_color="#e74c3c")
        self.lbl_warn.pack(pady=(0, 8))

        # ── Portion row ───────────────────────────────────────────────
        port_f = ctk.CTkFrame(self, fg_color="transparent")
        port_f.pack(fill="x", padx=20, pady=4)

        ctk.CTkLabel(port_f, text=t("mb.portion_label"),
                     font=("Segoe UI", 13)).pack(side="left")
        self.x_input = ctk.CTkEntry(port_f, width=80)
        self.x_input.pack(side="left", padx=8)
        self.x_input.bind("<KeyRelease>", lambda _e: self._update_display())

        ctk.CTkLabel(port_f, text=" │ ",
                     font=("Segoe UI", 13),
                     text_color="#444444").pack(side="left")
        self.whole_cb = ctk.CTkCheckBox(
            port_f,
            text=t("mb.whole_meal_checkbox"),
            font=("Segoe UI", 13),
            variable=self._use_whole,
            command=self._on_whole_toggle)
        self.whole_cb.pack(side="left")

        self.lbl_portion = ctk.CTkLabel(
            port_f,
            text=t("mb.portion_empty"),
            text_color="#2ecc71", font=("Segoe UI", 14, "bold"))
        self.lbl_portion.pack(side="left", padx=16)

        # ── Action buttons ────────────────────────────────────────────
        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(pady=14)

        ctk.CTkButton(btn_f, text=t("mb.btn_save_as_food"),
                      fg_color="#2a8a38",
                      command=self._save_as_food).pack(side="left", padx=8)

        ctk.CTkButton(btn_f, text=t("mb.btn_save_recipe"),
                      fg_color="#c87028",
                      command=self._save_recipe).pack(side="left", padx=8)

        ctk.CTkButton(btn_f, text=t("mb.btn_add_journal"),
                      fg_color="#1a7878",
                      command=self._add_to_journal).pack(side="left", padx=8)

        self.print_btn = ctk.CTkButton(
            btn_f, text=t("mb.btn_print_meal"),
            fg_color="#4a4a4a", text_color="#aaaaaa",
            state="disabled", command=self._print_meal)
        self.print_btn.pack(side="left", padx=8)

        ctk.CTkButton(btn_f, text=t("mb.btn_clear_all"),
                      fg_color="#8B0000",
                      command=self._clear_meal).pack(side="left", padx=8)

    # ------------------------------------------------------------------
    # Persistent checkbox
    # ------------------------------------------------------------------

    def _on_whole_toggle(self):
        cfg = load_print_config()
        cfg["use_whole_meal_as_portion"] = self._use_whole.get()
        try:
            save_print_config(cfg)
        except SaveError as e:
            messagebox.showerror("Save Error",
                                 f"Could not save {e.filename}:\n{e.strerror}")
        self._update_display()

    # ------------------------------------------------------------------
    # Search logic
    # ------------------------------------------------------------------

    def _filter_search(self, _event=None):
        val = self.search_ent.get().lower()
        self.search_list.delete(0, END)
        if not val:
            return
        for item in self.app.db:
            if val in item["name"].lower():
                self.search_list.insert(END, item["name"])

    def _select_search(self, _event=None):
        if not self.search_list.curselection():
            return
        name = self.search_list.get(self.search_list.curselection())
        self.search_ent.delete(0, END)
        self.search_ent.insert(0, name)
        self.weight_ent.focus_set()

    def _add_item(self):
        name = self.search_ent.get().strip()
        if not name:
            return
        food = next((f for f in self.app.db
                     if f["name"].lower() == name.lower()), None)
        if not food:
            messagebox.showwarning(t("mb.err_not_found_title"),
                                   t("mb.err_not_found_msg", q=name))
            return
        try:
            w = float(self.weight_ent.get())
            if w <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(t("mb.err_invalid_weight_title"),
                                   t("mb.err_invalid_weight_msg"))
            return

        scale = w / 100
        self.current_recipe.append({
            "name": food["name"],
            "w": w,
            "p": round(food["p"] * scale, 2),
            "f": round(food["f"] * scale, 2),
            "c": round(food["c"] * scale, 2),
            "k": round(food["kcal"] * scale, 2),
        })
        self.search_ent.delete(0, END)
        self.weight_ent.delete(0, END)
        self.search_list.delete(0, END)
        self._update_display()
        self._re_validate_prepared()
        self.print_btn.configure(state="normal",
                                  fg_color="#1a7878", text_color="white")

    def _remove_item(self, event):
        idx = self.meal_txt.index(f"@{event.x},{event.y}")
        line_no = int(idx.split(".")[0]) - 3
        if 0 <= line_no < len(self.current_recipe):
            self.current_recipe.pop(line_no)
            self._update_display()
            self._re_validate_prepared()
            if not self.current_recipe:
                self.print_btn.configure(state="disabled",
                                          fg_color="#4a4a4a",
                                          text_color="#aaaaaa")

    # ------------------------------------------------------------------
    # Prepared weight handling
    # ------------------------------------------------------------------

    def _re_validate_prepared(self):
        if self.prep_ent.get().strip():
            self._on_prep_weight_change()

    def _on_prep_weight_change(self, _event=None):
        raw_w   = sum(i["w"] for i in self.current_recipe)
        val_str = self.prep_ent.get().strip()

        if not val_str:
            self.prepared_weight = None
            self.show_prepared   = False
            self.prep_status.configure(text="")
            self.toggle_btn.configure(state="disabled")
            self._update_toggle_ui()
            self.state_indicator.configure(text_color="#909090")
            self._update_display()
            return

        try:
            pw = float(val_str)
        except ValueError:
            self.prep_status.configure(text=t("mb.prep_enter_number"),
                                        text_color="#e74c3c")
            self.prepared_weight = None
            self.toggle_btn.configure(state="disabled")
            self.show_prepared = False
            self._update_toggle_ui()
            self.state_indicator.configure(text_color="#909090")
            return

        if pw <= 0:
            self.prep_status.configure(text=t("mb.prep_must_positive"),
                                        text_color="#e74c3c")
            self.prepared_weight = None
            self.toggle_btn.configure(state="disabled")
            self.show_prepared = False
            self._update_toggle_ui()
            self.state_indicator.configure(text_color="#909090")
            return

        if raw_w > 0 and pw > raw_w:
            self.prep_status.configure(
                text=t("mb.prep_exceeds_raw", raw=f"{raw_w:.1f}"),
                text_color="#e74c3c")
            self.prepared_weight = None
            self.toggle_btn.configure(state="disabled")
            self.show_prepared = False
            self._update_toggle_ui()
            self.state_indicator.configure(text_color="#909090")
            return

        dry_mass = sum(i["p"] + i["f"] + i["c"] for i in self.current_recipe)
        if dry_mass > 0 and pw < dry_mass:
            self.prep_status.configure(
                text=t("mb.prep_below_min", min=f"{dry_mass:.1f}"),
                text_color="#e74c3c")
            self.prepared_weight = None
            self.toggle_btn.configure(state="disabled")
            self.show_prepared = False
            self._update_toggle_ui()
            self.state_indicator.configure(text_color="#909090")
            return

        # Valid
        self.prepared_weight = pw
        self.show_prepared   = False

        weight_loss_pct = round((raw_w - pw) / raw_w * 100, 1) if raw_w > 0 else 0
        raw_water  = raw_w - dry_mass
        prep_water = pw    - dry_mass
        if raw_water > 0:
            moisture_pct = round((raw_water - prep_water) / raw_water * 100, 1)
            moisture_str = t("mb.moisture_lost", pct=moisture_pct)
        else:
            moisture_str = t("mb.moisture_no_water")

        self.prep_status.configure(
            text=t("mb.prep_ok", pct=weight_loss_pct, moisture=moisture_str),
            text_color="#2ecc71")
        self.toggle_btn.configure(state="normal")
        self._update_toggle_ui()
        self._update_display()

    def _toggle_prepared(self):
        self.show_prepared = not self.show_prepared
        self._update_toggle_ui()
        self._update_display()

    def _update_toggle_ui(self):
        if self.show_prepared:
            self.state_indicator.configure(
                text=t("mb.viewing_prepared"), text_color="#f5a623")
            self.toggle_btn.configure(
                text=t("mb.btn_switch_raw"), fg_color="#3a5a3a")
        else:
            self.state_indicator.configure(
                text=t("mb.viewing_raw"), text_color="#2ecc71")
            self.toggle_btn.configure(
                text=t("mb.btn_switch_prepared"), fg_color="#3a5a3a")

    # ------------------------------------------------------------------
    # Display update
    # ------------------------------------------------------------------

    def _update_display(self):
        tw = sum(i["w"] for i in self.current_recipe)
        tp = sum(i["p"] for i in self.current_recipe)
        tf = sum(i["f"] for i in self.current_recipe)
        tc = sum(i["c"] for i in self.current_recipe)
        tk = sum(i["k"] for i in self.current_recipe)

        raw_totals = {"p": tp, "f": tf, "c": tc, "kcal": tk}

        prep_totals = None
        if self.prepared_weight and self.prepared_weight < tw:
            prep_totals = calc_prepared(raw_totals, tw, self.prepared_weight)

        disp_totals = (prep_totals
                       if (self.show_prepared and prep_totals)
                       else raw_totals)
        disp_weight = (self.prepared_weight
                       if (self.show_prepared and prep_totals)
                       else tw)

        # Rebuild ingredient list (read-only)
        p_h = t("mb.abbr_p")
        f_h = t("mb.abbr_f")
        c_h = t("mb.abbr_c")
        food_h = t("mb.col_food")
        self.meal_txt.configure(state="normal")
        self.meal_txt.delete("1.0", END)
        header = (f"{food_h:<34} | {'g':>6} | {p_h:>7} | "
                  f"{f_h:>7} | {c_h:>7} | {'kcal':>7}\n")
        self.meal_txt.insert(END, header + "─" * 78 + "\n")
        for i in self.current_recipe:
            self.meal_txt.insert(
                END,
                f"{i['name'][:33]:<34} | {i['w']:>6.1f} | "
                f"{i['p']:>7.1f} | {i['f']:>7.1f} | "
                f"{i['c']:>7.1f} | {i['k']:>7.1f}\n")
        self.meal_txt.configure(state="disabled")

        # Summary labels
        mode = (t("mb.mode_prepared")
                if (self.show_prepared and prep_totals)
                else t("mb.mode_raw"))
        self.lbl_weight.configure(
            text=t("mb.whole_weight", mode=mode, w=f"{disp_weight:.1f}"))
        self.lbl_whole.configure(
            text=t("mb.whole_macros",
                   p=f"{disp_totals['p']:.1f}",
                   f=f"{disp_totals['f']:.1f}",
                   c=f"{disp_totals['c']:.1f}",
                   k=f"{disp_totals['kcal']:.0f}"))

        per100 = calc_per_100g(disp_totals, disp_weight)
        self.lbl_100g.configure(
            text=t("mb.per100_macros",
                   p=f"{per100['p']:.1f}",
                   f=f"{per100['f']:.1f}",
                   c=f"{per100['c']:.1f}",
                   k=f"{per100['kcal']:.0f}"))

        # Impossible-value warning
        warns = []
        macro_sum = per100["p"] + per100["f"] + per100["c"]
        if per100["kcal"] > 900:
            warns.append(t("mb.warn_kcal_exceeds",
                           k=f"{per100['kcal']:.0f}", max=900))
        elif macro_sum > 100:
            warns.append(t("mb.warn_macros_impossible",
                           sum=f"{macro_sum:.1f}"))
        self.lbl_warn.configure(text="  |  ".join(warns))

        # Portion row
        try:
            x = float(self.x_input.get())
            if x <= 0:
                raise ValueError
        except ValueError:
            if self._use_whole.get() and disp_weight > 0:
                x = disp_weight
            else:
                x = None

        if x:
            port = calc_portion(disp_totals, disp_weight, x)
            src  = (t("mb.whole_meal_src")
                    if (x == disp_weight and not self.x_input.get().strip())
                    else "")
            self.lbl_portion.configure(
                text=t("mb.portion_macros",
                       x=f"{x:.0f}", src=src,
                       p=f"{port['p']:.1f}",
                       f=f"{port['f']:.1f}",
                       c=f"{port['c']:.1f}",
                       k=f"{port['kcal']:.0f}"))
        else:
            self.lbl_portion.configure(text=t("mb.portion_empty"))

    # ------------------------------------------------------------------
    # Save as Recipe
    # ------------------------------------------------------------------

    def _save_as_food(self):
        if not self.current_recipe:
            messagebox.showwarning(t("mb.err_empty_meal_title"),
                                   t("mb.err_empty_meal_msg"))
            return

        tw = sum(i["w"] for i in self.current_recipe)
        if tw == 0:
            messagebox.showerror(t("mb.err_error_title"),
                                 t("mb.err_zero_weight_msg"))
            return

        n = simpledialog.askstring(t("mb.dlg_recipe_title"),
                                   t("mb.dlg_recipe_prompt"))
        if not n:
            return

        full_name = f"[R] {n}"
        if any(item["name"].lower() == full_name.lower()
               for item in self.app.db):
            messagebox.showerror(t("mb.err_duplicate_title"),
                                 t("mb.err_duplicate_recipe", name=full_name))
            return

        scale = 100 / tw
        tp = sum(i["p"] for i in self.current_recipe)
        tf = sum(i["f"] for i in self.current_recipe)
        tc = sum(i["c"] for i in self.current_recipe)
        p_val = round(tp * scale, 2)
        f_val = round(tf * scale, 2)
        c_val = round(tc * scale, 2)

        if (p_val + f_val + c_val) > 100.01:
            messagebox.showerror(
                t("mb.err_invalid_macros_title"),
                t("mb.err_invalid_macros_msg",
                  sum=f"{p_val+f_val+c_val:.1f}"))
            return

        self.app.db.append({
            "id": str(uuid.uuid4()),
            "name": full_name,
            "p": p_val, "f": f_val, "c": c_val,
            "kcal": round(p_val * 4 + f_val * 9 + c_val * 4, 1),
        })
        try:
            save_db(self.app.db)
        except SaveError as e:
            self.app.db.pop()
            messagebox.showerror("Save Error",
                                 f"Could not save {e.filename}:\n{e.strerror}")
            return
        self.app.db_frame.refresh()
        messagebox.showinfo(t("mb.info_saved_title"),
                            t("mb.info_saved_recipe", name=full_name))

    # ------------------------------------------------------------------
    # Save Recipe (full recipe to recipes.json)
    # ------------------------------------------------------------------

    def _save_recipe(self):
        if not self.current_recipe:
            messagebox.showwarning(t("svr.err_empty_title"),
                                   t("svr.err_empty_msg"))
            return

        tw = sum(i["w"] for i in self.current_recipe)
        tp = sum(i["p"] for i in self.current_recipe)
        tf = sum(i["f"] for i in self.current_recipe)
        tc = sum(i["c"] for i in self.current_recipe)
        tk = sum(i["k"] for i in self.current_recipe)
        raw_totals = {"p": tp, "f": tf, "c": tc, "kcal": tk}

        prep_totals = None
        if self.prepared_weight:
            from models import calc_prepared
            prep_totals = calc_prepared(raw_totals, tw, self.prepared_weight)

        meal_data = {
            "ingredients":     self.current_recipe,
            "raw_weight":      tw,
            "raw_totals":      raw_totals,
            "prepared_weight": self.prepared_weight,
            "prep_totals":     prep_totals,
            "portion_g":       self._get_portion(),
        }
        from ui_recipes import SaveRecipeDialog
        dlg = SaveRecipeDialog(
            parent=self, app=self.app,
            meal_data=meal_data,
            on_saved=lambda: None)
        self.wait_window(dlg)

    # ------------------------------------------------------------------
    # Load Recipe (from Recipe Book)
    # ------------------------------------------------------------------

    def load_recipe(self, recipe):
        """Load a recipe dict into the Meal Builder, replacing current meal."""
        # Clear current state
        self.current_recipe  = []
        self.prepared_weight = None
        self.show_prepared   = False
        self._last_logged_name = recipe.get("name")

        self.prep_ent.delete(0, END)
        self.prep_status.configure(text="")
        self.toggle_btn.configure(state="disabled")
        self._update_toggle_ui()
        self.state_indicator.configure(text_color="#909090")
        self.print_btn.configure(state="disabled",
                                  fg_color="#4a4a4a", text_color="#aaaaaa")

        # Repopulate ingredients
        for ing in recipe.get("ingredients", []):
            self.current_recipe.append({
                "name": ing["name"],
                "w":    ing["w"],
                "p":    ing["p"],
                "f":    ing["f"],
                "c":    ing["c"],
                "k":    ing["k"],
            })

        # Restore prepared weight if present
        pw = recipe.get("prepared_weight")
        if pw:
            self.prep_ent.delete(0, END)
            self.prep_ent.insert(0, f"{pw:.1f}")
            self._on_prep_weight_change()

        # Restore serving size if present
        sv = recipe.get("serving_g")
        self.x_input.delete(0, END)
        if sv:
            self.x_input.insert(0, f"{sv:.0f}")

        if self.current_recipe:
            self.print_btn.configure(state="normal",
                                      fg_color="#3a5a3a", text_color="white")

        self._update_display()

        # ------------------------------------------------------------------
    # Add to Journal
    # ------------------------------------------------------------------

    def _add_to_journal(self):
        if not self.current_recipe:
            messagebox.showwarning(t("mb.err_empty_meal_title"),
                                   t("mb.err_empty_meal_msg"))
            return

        tw = sum(i["w"] for i in self.current_recipe)
        tp = sum(i["p"] for i in self.current_recipe)
        tf = sum(i["f"] for i in self.current_recipe)
        tc = sum(i["c"] for i in self.current_recipe)
        tk = sum(i["k"] for i in self.current_recipe)
        raw_totals = {"p": tp, "f": tf, "c": tc, "kcal": tk}

        if self.prepared_weight:
            ref_totals = calc_prepared(raw_totals, tw, self.prepared_weight)
            ref_weight = self.prepared_weight
        else:
            ref_totals = raw_totals
            ref_weight = tw

        mb_portion = self._get_portion()
        if mb_portion is not None:
            prefill = mb_portion
        elif self._use_whole.get():
            prefill = ref_weight
        else:
            prefill = None

        from ui_log import LogEntryDialog
        dlg = LogEntryDialog(
            parent=self,
            app=self.app,
            ref_totals=ref_totals,
            ref_weight=ref_weight,
            prefill_portion=prefill,
            last_logged_name=self._last_logged_name,
        )
        self.wait_window(dlg)

        if dlg.result:
            self._last_logged_name = dlg.result.get("meal_name")
            self.app.journal_frame.refresh()
            messagebox.showinfo(t("mb.info_logged_title"),
                                t("mb.info_logged_msg"))

    def _get_portion(self):
        try:
            v = float(self.x_input.get())
            return v if v > 0 else None
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # Print Meal
    # ------------------------------------------------------------------

    def _print_meal(self):
        if not self.current_recipe:
            return
        from ui_print import PrintDialog
        tw = sum(i["w"] for i in self.current_recipe)
        tp = sum(i["p"] for i in self.current_recipe)
        tf = sum(i["f"] for i in self.current_recipe)
        tc = sum(i["c"] for i in self.current_recipe)
        tk = sum(i["k"] for i in self.current_recipe)
        raw_totals = {"p": tp, "f": tf, "c": tc, "kcal": tk}
        prep_totals = None
        if self.prepared_weight:
            prep_totals = calc_prepared(raw_totals, tw, self.prepared_weight)

        dlg = PrintDialog(
            parent=self, app=self.app, mode="meal",
            meal_data={
                "ingredients":     self.current_recipe,
                "raw_weight":      tw,
                "raw_totals":      raw_totals,
                "prepared_weight": self.prepared_weight,
                "prep_totals":     prep_totals,
                "portion_g":       self._get_portion(),
            })
        self.wait_window(dlg)

    # ------------------------------------------------------------------
    # Clear All
    # ------------------------------------------------------------------

    def _clear_meal(self):
        if messagebox.askyesno(t("mb.confirm_clear_title"),
                               t("mb.confirm_clear_msg")):
            self.current_recipe  = []
            self.prepared_weight = None
            self.show_prepared   = False
            self._last_logged_name = None
            self.prep_ent.delete(0, END)
            self.prep_status.configure(text="")
            self.toggle_btn.configure(state="disabled")
            self._update_toggle_ui()
            self.state_indicator.configure(text_color="#909090")
            self.print_btn.configure(state="disabled",
                                      fg_color="#4a4a4a", text_color="#aaaaaa")
            self._update_display()
