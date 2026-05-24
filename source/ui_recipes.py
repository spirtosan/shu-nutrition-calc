# =============================================================================
# ui_recipes.py — Shu Nutrition Calc v5.3
# Recipe Book tab: search, preview, load into Meal Builder, edit, print, delete.
# SaveRecipeDialog: called from MealBuilderFrame.
# EditRecipeDialog: full in-place recipe editor.
# =============================================================================

import customtkinter as ctk
from tkinter import messagebox, Listbox, SINGLE, END
from datetime import datetime

from models import (load_recipes, save_recipes, new_recipe,
                    calc_per_100g, calc_portion)
from lang import t


# =============================================================================
# RECIPE BOOK FRAME
# =============================================================================

class RecipeBookFrame(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._all_recipes    = []
        self._shown_recipes  = []
        self._selected_recipe = None
        self._build_ui()
        self.refresh()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # ── Search row ────────────────────────────────────────────────
        top = ctk.CTkFrame(self, fg_color="#2b2b2b")
        top.pack(fill="x", padx=20, pady=(15, 6))

        ctk.CTkLabel(top, text=t("rcb.search_label"),
                     font=("Segoe UI", 13)).pack(side="left", padx=12, pady=10)
        self.search_ent = ctk.CTkEntry(
            top, width=360,
            placeholder_text=t("rcb.search_placeholder"))
        self.search_ent.pack(side="left", padx=6)
        self.search_ent.bind("<KeyRelease>", self._filter)

        ctk.CTkButton(top, text=t("rcb.btn_refresh"),
                      width=110, fg_color="#3a5a3a",
                      command=self.refresh).pack(side="right", padx=12)

        # ── Column headers ────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(8, 0))
        for col_key, w in [
            ("rcb.col_name",        300),
            ("rcb.col_date",        110),
            ("rcb.col_ingredients",  55),
            ("rcb.col_raw_weight",   85),
            ("rcb.col_serving",      80),
        ]:
            ctk.CTkLabel(hdr, text=t(col_key), width=w, anchor="w",
                         font=("Segoe UI", 12, "bold"),
                         text_color="gray").pack(side="left", padx=4)

        # ── Recipe list ───────────────────────────────────────────────
        self.recipe_list = Listbox(
            self, font=("Consolas", 12),
            bg="#181818", fg="white",
            borderwidth=0, selectmode=SINGLE,
            activestyle="none", height=8)
        self.recipe_list.pack(fill="x", padx=20, pady=(2, 4))
        self.recipe_list.bind("<<ListboxSelect>>", self._on_select)
        self.recipe_list.bind("<Double-Button-1>",
                              lambda _e: self._load_into_builder())

        # ── Detail panel ──────────────────────────────────────────────
        detail_outer = ctk.CTkFrame(self, fg_color="#1a1a1a",
                                    border_width=1, border_color="#2a2a2a")
        detail_outer.pack(fill="both", expand=True, padx=20, pady=(0, 4))

        detail_hdr = ctk.CTkFrame(detail_outer, fg_color="transparent")
        detail_hdr.pack(fill="x", padx=10, pady=(6, 0))
        self.lbl_detail_name = ctk.CTkLabel(
            detail_hdr, text=t("rcb.detail_empty"),
            font=("Segoe UI", 13, "bold"),
            text_color="#f5a623", anchor="w")
        self.lbl_detail_name.pack(side="left")
        self.lbl_detail_notes = ctk.CTkLabel(
            detail_hdr, text="",
            font=("Segoe UI", 12), text_color="#909090", anchor="e")
        self.lbl_detail_notes.pack(side="right")

        self.detail_txt = ctk.CTkTextbox(
            detail_outer, font=("Consolas", 12), height=130, state="disabled")
        self.detail_txt.pack(fill="x", padx=10, pady=(4, 0))

        self.lbl_detail_macros = ctk.CTkLabel(
            detail_outer, text="",
            font=("Segoe UI", 12), text_color="#909090",
            anchor="w", justify="left")
        self.lbl_detail_macros.pack(fill="x", padx=14, pady=(4, 8))

        # ── Action buttons ────────────────────────────────────────────
        act = ctk.CTkFrame(self, fg_color="transparent")
        act.pack(pady=8)

        ctk.CTkButton(act, text=t("rcb.btn_load"),
                      fg_color="#1a7878", width=185,
                      command=self._load_into_builder).pack(side="left", padx=6)

        ctk.CTkButton(act, text=t("rcb.btn_edit"),
                      fg_color="#c87028", width=150,
                      command=self._edit_recipe).pack(side="left", padx=6)

        ctk.CTkButton(act, text=t("rcb.btn_print"),
                      fg_color="#3a5a3a", width=120,
                      command=self._print_recipe).pack(side="left", padx=6)

        ctk.CTkButton(act, text=t("rcb.btn_delete"),
                      fg_color="#8B0000",
                      command=self._delete_recipe).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def refresh(self):
        self.app.recipes     = load_recipes()
        self._all_recipes    = self.app.recipes
        self._selected_recipe = None
        self.search_ent.delete(0, END)
        self._filter()
        self._clear_detail()

    # ------------------------------------------------------------------
    # List management
    # ------------------------------------------------------------------

    def _filter(self, _event=None):
        q = self.search_ent.get().lower().strip()
        self._shown_recipes = (
            [r for r in self._all_recipes if q in r["name"].lower()]
            if q else list(self._all_recipes)
        )
        self._populate_list()

    def _populate_list(self):
        self.recipe_list.delete(0, END)
        if not self._shown_recipes:
            self.recipe_list.insert(END, f"  {t('rcb.no_recipes')}")
            return
        for r in self._sorted():
            try:
                dt_str = datetime.strptime(
                    r["created"], "%Y-%m-%dT%H:%M:%S").strftime("%d-%m-%Y")
            except Exception:
                dt_str = r.get("created", "")[:10]
            n_ing  = len(r.get("ingredients", []))
            raw_w  = r.get("raw_weight", 0)
            sv_g   = r.get("serving_g")
            sv_str = f"{sv_g:.0f}g" if sv_g else "—"
            self.recipe_list.insert(
                END,
                f"{r['name'][:36]:<38}  {dt_str:<12}"
                f"{n_ing:>4}    {raw_w:>7.1f}g  {sv_str:>7}")

    def _sorted(self):
        return sorted(self._shown_recipes,
                      key=lambda x: x.get("created", ""), reverse=True)

    def _on_select(self, _event=None):
        sel = self.recipe_list.curselection()
        if not sel or not self._shown_recipes:
            self._clear_detail()
            return
        s = self._sorted()
        if sel[0] >= len(s):
            self._clear_detail()
            return
        self._selected_recipe = s[sel[0]]
        self._show_detail(self._selected_recipe)

    def _get_selected(self):
        return self._selected_recipe

    # ------------------------------------------------------------------
    # Detail panel
    # ------------------------------------------------------------------

    def _clear_detail(self):
        self._selected_recipe = None
        self.lbl_detail_name.configure(text=t("rcb.detail_empty"))
        self.lbl_detail_notes.configure(text="")
        self.detail_txt.configure(state="normal")
        self.detail_txt.delete("1.0", END)
        self.detail_txt.configure(state="disabled")
        self.lbl_detail_macros.configure(text="")

    def _show_detail(self, r):
        notes    = r.get("notes", "")
        ing      = r.get("ingredients", [])
        rw       = r.get("raw_weight", 0)
        rt       = r.get("raw_totals", {})
        pw       = r.get("prepared_weight")
        pt       = r.get("prep_totals")
        sv       = r.get("serving_g")
        has_prep = bool(pw and pt)

        self.lbl_detail_name.configure(text=r.get("name", ""))
        self.lbl_detail_notes.configure(
            text=f"{t('rcb.detail_notes')} {notes}" if notes else "")

        p_h = t("mb.abbr_p"); f_h = t("mb.abbr_f"); c_h = t("mb.abbr_c")
        self.detail_txt.configure(state="normal")
        self.detail_txt.delete("1.0", END)
        header = (f"{'Food':<34} | {'g':>6} | {p_h:>6} | "
                  f"{f_h:>6} | {c_h:>6} | {'kcal':>6}\n")
        self.detail_txt.insert(END, header + "─" * 68 + "\n")
        for i in ing:
            self.detail_txt.insert(
                END,
                f"{i['name'][:33]:<34} | {i['w']:>6.1f} | "
                f"{i['p']:>6.1f} | {i['f']:>6.1f} | "
                f"{i['c']:>6.1f} | {i['k']:>6.1f}\n")
        self.detail_txt.configure(state="disabled")

        ref_t = pt if has_prep else rt
        ref_w = pw if has_prep else rw
        lines = []
        if ref_w and ref_w > 0:
            mode   = t("mb.mode_prepared") if has_prep else t("mb.mode_raw")
            rp = round(ref_t.get("p",0), 1); rf = round(ref_t.get("f",0), 1)
            rc = round(ref_t.get("c",0), 1); rk = round(ref_t.get("kcal",0))
            lines.append(
                t("mb.whole_weight", mode=mode, w=f"{ref_w:.1f}") + "   " +
                t("mb.whole_macros",
                  p=str(rp), f=str(rf), c=str(rc), k=str(int(rk))))
            p100 = calc_per_100g(ref_t, ref_w)
            lines.append(
                t("mb.per100_macros",
                  p=f"{p100['p']:.1f}", f=f"{p100['f']:.1f}",
                  c=f"{p100['c']:.1f}", k=f"{p100['kcal']:.0f}"))
            if sv and ref_w > 0:
                port = calc_portion(ref_t, ref_w, sv)
                lines.append(
                    t("mb.portion_macros",
                      x=f"{sv:.0f}", src="",
                      p=f"{port['p']:.1f}", f=f"{port['f']:.1f}",
                      c=f"{port['c']:.1f}", k=f"{port['kcal']:.0f}"))
        self.lbl_detail_macros.configure(text="\n".join(lines))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _load_into_builder(self):
        recipe = self._get_selected()
        if not recipe:
            messagebox.showinfo(t("rcb.err_no_selection_title"),
                                t("rcb.err_no_selection_msg"))
            return
        if messagebox.askyesno(
                t("rcb.confirm_load_title"),
                t("rcb.confirm_load_msg", name=recipe["name"])):
            self.app.frames["calc"].load_recipe(recipe)
            self.app.show_frame("calc")

    def _edit_recipe(self):
        recipe = self._get_selected()
        if not recipe:
            messagebox.showinfo(t("rcb.err_no_selection_title"),
                                t("rcb.err_no_selection_msg"))
            return
        EditRecipeDialog(self, self.app, recipe, on_saved=self.refresh)

    def _print_recipe(self):
        recipe = self._get_selected()
        if not recipe:
            messagebox.showinfo(t("rcb.err_no_selection_title"),
                                t("rcb.err_no_selection_msg"))
            return
        from ui_print import PrintDialog
        PrintDialog(parent=self, app=self.app,
                    mode="recipe", recipe_data=recipe)

    def _delete_recipe(self):
        recipe = self._get_selected()
        if not recipe:
            messagebox.showinfo(t("rcb.err_no_selection_title"),
                                t("rcb.err_no_selection_msg"))
            return
        if messagebox.askyesno(
                t("rcb.confirm_delete_title"),
                t("rcb.confirm_delete_msg", name=recipe["name"])):
            self.app.recipes = [
                r for r in self.app.recipes if r["id"] != recipe["id"]]
            save_recipes(self.app.recipes)
            self.refresh()


# =============================================================================
# EDIT RECIPE DIALOG
# =============================================================================

class EditRecipeDialog(ctk.CTkToplevel):

    def __init__(self, parent, app, recipe, on_saved):
        super().__init__(parent)
        self.app              = app
        self.recipe           = recipe
        self.on_saved         = on_saved
        self.ingredients      = [dict(i) for i in recipe.get("ingredients", [])]
        self._prepared_weight = recipe.get("prepared_weight")

        self.title(t("edr.title", name=recipe["name"]))
        self.geometry("800x720")
        self.resizable(True, True)
        self._build_ui()
        self._update_ing_display()
        self._update_summary()
        if self._prepared_weight:
            self.prep_ent.insert(0, f"{self._prepared_weight:.1f}")
            self._on_prep_change()

        self.transient(parent.winfo_toplevel())
        self.update_idletasks()
        self.lift()
        self.grab_set()
        self.focus_force()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        ctk.CTkLabel(self, text=t("edr.heading"),
                     font=("Segoe UI", 16, "bold"),
                     text_color="#f5a623").pack(pady=(14, 4))

        # ── Name + serving ────────────────────────────────────────────
        meta = ctk.CTkFrame(self, fg_color="#2b2b2b")
        meta.pack(fill="x", padx=16, pady=(0, 8))
        meta.columnconfigure(1, weight=1)
        meta.columnconfigure(3, weight=0)

        ctk.CTkLabel(meta, text=t("edr.name_label"),
                     width=100, anchor="w").grid(
                         row=0, column=0, padx=10, pady=10, sticky="w")
        self.name_ent = ctk.CTkEntry(meta)
        self.name_ent.insert(0, self.recipe.get("name", ""))
        self.name_ent.grid(row=0, column=1, padx=6, pady=10, sticky="ew")

        ctk.CTkLabel(meta, text=t("edr.serving_label"),
                     width=160, anchor="w").grid(
                         row=0, column=2, padx=(16, 4), pady=10, sticky="w")
        self.serving_ent = ctk.CTkEntry(meta, width=90,
                                         placeholder_text=t("edr.serving_ph"))
        sv = self.recipe.get("serving_g")
        if sv:
            self.serving_ent.insert(0, f"{sv:.0f}")
        self.serving_ent.grid(row=0, column=3, padx=(0, 14), pady=10)

        # ── Search / add ingredient row ───────────────────────────────
        add_f = ctk.CTkFrame(self, fg_color="#1e1e1e",
                              border_width=1, border_color="#2a2a2a")
        add_f.pack(fill="x", padx=16, pady=(0, 4))

        ctk.CTkLabel(add_f, text=t("edr.search_label"),
                     font=("Segoe UI", 12)).pack(side="left", padx=10, pady=8)
        self.search_ent = ctk.CTkEntry(
            add_f, width=280,
            placeholder_text=t("edr.search_ph"))
        self.search_ent.pack(side="left", padx=6)
        self.search_ent.bind("<KeyRelease>", self._filter_search)

        ctk.CTkLabel(add_f, text="g",
                     font=("Segoe UI", 12)).pack(side="left", padx=(10, 2))
        self.weight_ent = ctk.CTkEntry(add_f, width=80,
                                        placeholder_text=t("edr.weight_ph"))
        self.weight_ent.pack(side="left", padx=4)
        self.weight_ent.bind("<Return>", lambda _e: self._add_ingredient())

        ctk.CTkButton(add_f, text=t("edr.btn_add"), width=100,
                      fg_color="#c87028",
                      command=self._add_ingredient).pack(
                          side="left", padx=10, pady=8)

        # Search dropdown
        self.search_drop = Listbox(
            self, height=4, font=("Arial", 12),
            bg="#1e1e1e", fg="white",
            borderwidth=0, highlightthickness=1)
        self.search_drop.pack(fill="x", padx=80, pady=(0, 2))
        self.search_drop.bind("<<ListboxSelect>>", self._pick_search)
        self.search_drop.bind("<Return>",
                               lambda _e: self.weight_ent.focus_set())

        # ── Ingredient textbox ────────────────────────────────────────
        p_h = t("mb.abbr_p"); f_h = t("mb.abbr_f"); c_h = t("mb.abbr_c")
        ctk.CTkLabel(self,
                     text=f"  {'Food':<34} | {'g':>6} | {p_h:>6} | "
                          f"{f_h:>6} | {c_h:>6} | {'kcal':>6}"
                          f"    ({t('edr.hint_remove')})",
                     font=("Consolas", 11),
                     text_color="#666666", anchor="w").pack(
                         fill="x", padx=16)
        self.ing_txt = ctk.CTkTextbox(
            self, font=("Consolas", 12), height=155, state="disabled")
        self.ing_txt.pack(fill="x", padx=16, pady=(2, 0))
        self.ing_txt.bind("<Double-Button-1>", self._remove_ingredient)

        # ── Prepared weight ───────────────────────────────────────────
        prep_f = ctk.CTkFrame(self, fg_color="#1e1e1e",
                               border_width=1, border_color="#2a2a2a")
        prep_f.pack(fill="x", padx=16, pady=(8, 4))

        ctk.CTkLabel(prep_f, text=t("edr.prepared_label"),
                     font=("Segoe UI", 12)).pack(side="left", padx=12, pady=8)
        self.prep_ent = ctk.CTkEntry(prep_f, width=90)
        self.prep_ent.pack(side="left", padx=6)
        self.prep_ent.bind("<KeyRelease>", self._on_prep_change)
        self.prep_status = ctk.CTkLabel(
            prep_f, text="",
            font=("Segoe UI", 11), text_color="#909090")
        self.prep_status.pack(side="left", padx=10)

        # ── Macro summary ─────────────────────────────────────────────
        sum_f = ctk.CTkFrame(self, fg_color="#181818",
                              border_width=1, border_color="#333")
        sum_f.pack(fill="x", padx=16, pady=4)
        self.lbl_sum = ctk.CTkLabel(
            sum_f, text="",
            font=("Segoe UI", 12), text_color="#f5a623",
            anchor="w", justify="left")
        self.lbl_sum.pack(fill="x", padx=12, pady=6)

        # ── Notes ─────────────────────────────────────────────────────
        notes_f = ctk.CTkFrame(self, fg_color="transparent")
        notes_f.pack(fill="x", padx=16, pady=(4, 0))
        ctk.CTkLabel(notes_f, text=t("edr.notes_label"),
                     font=("Segoe UI", 12)).pack(side="left", padx=(0, 8))
        self.notes_ent = ctk.CTkEntry(notes_f)
        self.notes_ent.insert(0, self.recipe.get("notes", ""))
        self.notes_ent.pack(side="left", fill="x", expand=True)

        # ── Buttons ───────────────────────────────────────────────────
        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(pady=12)
        ctk.CTkButton(btn_f, text=t("edr.btn_save"),
                      fg_color="#2a8a38", width=180,
                      command=self._save).pack(side="left", padx=12)
        ctk.CTkButton(btn_f, text=t("edr.btn_cancel"),
                      fg_color="#8B0000",
                      command=self.destroy).pack(side="left", padx=12)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def _filter_search(self, _event=None):
        val = self.search_ent.get().lower()
        self.search_drop.delete(0, END)
        if not val:
            return
        for item in self.app.db:
            if val in item["name"].lower():
                self.search_drop.insert(END, item["name"])

    def _pick_search(self, _event=None):
        if not self.search_drop.curselection():
            return
        name = self.search_drop.get(self.search_drop.curselection())
        self.search_ent.delete(0, END)
        self.search_ent.insert(0, name)
        self.weight_ent.focus_set()

    # ------------------------------------------------------------------
    # Ingredient management
    # ------------------------------------------------------------------

    def _add_ingredient(self):
        name = self.search_ent.get().strip()
        if not name:
            return
        food = next((f for f in self.app.db
                     if f["name"].lower() == name.lower()), None)
        if not food:
            messagebox.showwarning("", t("edr.err_not_found", q=name))
            return
        try:
            w = float(self.weight_ent.get())
            if w <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("", t("edr.err_weight"))
            return

        scale = w / 100
        self.ingredients.append({
            "name": food["name"], "w": w,
            "p": round(food["p"] * scale, 2),
            "f": round(food["f"] * scale, 2),
            "c": round(food["c"] * scale, 2),
            "k": round(food["kcal"] * scale, 2),
        })
        self.search_ent.delete(0, END)
        self.weight_ent.delete(0, END)
        self.search_drop.delete(0, END)
        self._update_ing_display()
        self._update_summary()
        self._revalidate_prep()

    def _remove_ingredient(self, event):
        idx = self.ing_txt.index(f"@{event.x},{event.y}")
        line_no = int(idx.split(".")[0]) - 3
        if 0 <= line_no < len(self.ingredients):
            self.ingredients.pop(line_no)
            self._update_ing_display()
            self._update_summary()
            self._revalidate_prep()

    def _update_ing_display(self):
        p_h = t("mb.abbr_p"); f_h = t("mb.abbr_f"); c_h = t("mb.abbr_c")
        self.ing_txt.configure(state="normal")
        self.ing_txt.delete("1.0", END)
        header = (f"{'Food':<34} | {'g':>6} | {p_h:>6} | "
                  f"{f_h:>6} | {c_h:>6} | {'kcal':>6}\n")
        self.ing_txt.insert(END, header + "─" * 68 + "\n")
        for i in self.ingredients:
            self.ing_txt.insert(
                END,
                f"{i['name'][:33]:<34} | {i['w']:>6.1f} | "
                f"{i['p']:>6.1f} | {i['f']:>6.1f} | "
                f"{i['c']:>6.1f} | {i['k']:>6.1f}\n")
        self.ing_txt.configure(state="disabled")

    # ------------------------------------------------------------------
    # Prepared weight
    # ------------------------------------------------------------------

    def _revalidate_prep(self):
        if self.prep_ent.get().strip():
            self._on_prep_change()

    def _on_prep_change(self, _event=None):
        raw_w = sum(i["w"] for i in self.ingredients)
        val   = self.prep_ent.get().strip()
        if not val:
            self._prepared_weight = None
            self.prep_status.configure(text="")
            self._update_summary()
            return
        try:
            pw = float(val)
        except ValueError:
            self._prepared_weight = None
            self.prep_status.configure(
                text=t("mb.prep_enter_number"), text_color="#e74c3c")
            return
        if pw <= 0:
            self._prepared_weight = None
            self.prep_status.configure(
                text=t("mb.prep_must_positive"), text_color="#e74c3c")
            return
        dry = sum(i["p"] + i["f"] + i["c"] for i in self.ingredients)
        if raw_w > 0 and pw > raw_w:
            self._prepared_weight = None
            self.prep_status.configure(
                text=t("mb.prep_exceeds_raw", raw=f"{raw_w:.1f}"),
                text_color="#e74c3c")
            return
        if dry > 0 and pw < dry:
            self._prepared_weight = None
            self.prep_status.configure(
                text=t("mb.prep_below_min", min=f"{dry:.1f}"),
                text_color="#e74c3c")
            return
        self._prepared_weight = pw
        self.prep_status.configure(text="✓", text_color="#2ecc71")
        self._update_summary()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def _update_summary(self):
        if not self.ingredients:
            self.lbl_sum.configure(text="")
            return
        rw = sum(i["w"] for i in self.ingredients)
        rt = {
            "p":    sum(i["p"] for i in self.ingredients),
            "f":    sum(i["f"] for i in self.ingredients),
            "c":    sum(i["c"] for i in self.ingredients),
            "kcal": sum(i["k"] for i in self.ingredients),
        }
        has_prep = bool(self._prepared_weight)
        if has_prep:
            from models import calc_prepared
            ref_t = calc_prepared(rt, rw, self._prepared_weight)
            ref_w = self._prepared_weight
        else:
            ref_t = rt
            ref_w = rw

        mode  = t("mb.mode_prepared") if has_prep else t("mb.mode_raw")
        line1 = (t("mb.whole_weight", mode=mode, w=f"{ref_w:.1f}") + "   " +
                 t("mb.whole_macros",
                   p=f"{ref_t['p']:.1f}", f=f"{ref_t['f']:.1f}",
                   c=f"{ref_t['c']:.1f}", k=f"{ref_t['kcal']:.0f}"))
        p100  = calc_per_100g(ref_t, ref_w)
        line2 = t("mb.per100_macros",
                  p=f"{p100['p']:.1f}", f=f"{p100['f']:.1f}",
                  c=f"{p100['c']:.1f}", k=f"{p100['kcal']:.0f}")
        self.lbl_sum.configure(text=f"{line1}\n{line2}")

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def _save(self):
        name = self.name_ent.get().strip()
        if not name:
            messagebox.showwarning(t("edr.err_name"), t("edr.err_name"))
            return
        # Duplicate check — allow same name if it IS this recipe
        for r in self.app.recipes:
            if r["name"].lower() == name.lower() and r["id"] != self.recipe["id"]:
                messagebox.showerror(t("svr.err_dup_title"),
                                     t("svr.err_dup_msg", name=name))
                return

        rw = sum(i["w"] for i in self.ingredients)
        rt = {
            "p":    sum(i["p"] for i in self.ingredients),
            "f":    sum(i["f"] for i in self.ingredients),
            "c":    sum(i["c"] for i in self.ingredients),
            "kcal": sum(i["k"] for i in self.ingredients),
        }
        pt = None
        if self._prepared_weight and rw > 0:
            from models import calc_prepared
            pt = calc_prepared(rt, rw, self._prepared_weight)

        sv_str    = self.serving_ent.get().strip()
        serving_g = None
        if sv_str:
            try:
                sv = float(sv_str)
                serving_g = sv if sv > 0 else None
            except ValueError:
                pass

        updated = dict(self.recipe)
        updated.update({
            "name":            name,
            "notes":           self.notes_ent.get().strip(),
            "serving_g":       serving_g,
            "raw_weight":      rw,
            "prepared_weight": self._prepared_weight,
            "ingredients":     self.ingredients,
            "raw_totals":      rt,
            "prep_totals":     pt,
        })

        self.app.recipes = [
            updated if r["id"] == self.recipe["id"] else r
            for r in self.app.recipes
        ]
        save_recipes(self.app.recipes)
        self.on_saved()
        self.destroy()


# =============================================================================
# SAVE RECIPE DIALOG  (called from MealBuilderFrame)
# =============================================================================

class SaveRecipeDialog(ctk.CTkToplevel):

    def __init__(self, parent, app, meal_data, on_saved):
        super().__init__(parent)
        self.app       = app
        self.meal_data = meal_data
        self.on_saved  = on_saved
        self.result    = None

        self.title(t("svr.title"))
        self.geometry("520x400")
        self.resizable(True, False)
        self._build_ui()

        self.transient(parent.winfo_toplevel())
        self.update_idletasks()
        self.lift()
        self.grab_set()
        self.focus_force()

    def _build_ui(self):
        ctk.CTkLabel(self, text=t("svr.heading"),
                     font=("Segoe UI", 17, "bold"),
                     text_color="#f5a623").pack(pady=(18, 10))

        md  = self.meal_data
        rw  = md["raw_weight"]
        ing = md["ingredients"]
        pw  = md.get("prepared_weight")

        info_parts = [f"{len(ing)} ingredients · {rw:.0f}g raw"]
        if pw:
            info_parts.append(f"{pw:.0f}g prepared")
        ctk.CTkLabel(self, text="  ·  ".join(info_parts),
                     font=("Segoe UI", 12),
                     text_color="#909090").pack(pady=(0, 10))

        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=28)
        grid.columnconfigure(1, weight=1)

        ctk.CTkLabel(grid, text=t("svr.name_label"),
                     width=140, anchor="w").grid(
                         row=0, column=0, pady=8, sticky="w")
        self.name_ent = ctk.CTkEntry(
            grid, placeholder_text=t("svr.name_ph"))
        self.name_ent.grid(row=0, column=1, pady=8, sticky="ew")

        ctk.CTkLabel(grid, text=t("svr.serving_label"),
                     width=140, anchor="w").grid(
                         row=1, column=0, pady=8, sticky="w")
        sv_f = ctk.CTkFrame(grid, fg_color="transparent")
        sv_f.grid(row=1, column=1, pady=8, sticky="w")
        self.serving_ent = ctk.CTkEntry(
            sv_f, width=100, placeholder_text=t("svr.serving_ph"))
        if md.get("portion_g"):
            self.serving_ent.insert(0, f"{md['portion_g']:.0f}")
        self.serving_ent.pack(side="left")
        ctk.CTkLabel(sv_f, text=" g",
                     text_color="#909090").pack(side="left")

        ctk.CTkLabel(grid, text=t("svr.notes_label"),
                     width=140, anchor="nw").grid(
                         row=2, column=0, pady=8, sticky="nw")
        self.notes_txt = ctk.CTkTextbox(grid, height=65)
        self.notes_txt.grid(row=2, column=1, pady=8, sticky="ew")

        btn_f = ctk.CTkFrame(self, fg_color="transparent")
        btn_f.pack(pady=16)
        ctk.CTkButton(btn_f, text=t("svr.btn_save"),
                      fg_color="#2a8a38",
                      command=self._save).pack(side="left", padx=12)
        ctk.CTkButton(btn_f, text=t("svr.btn_cancel"),
                      fg_color="#8B0000",
                      command=self.destroy).pack(side="left", padx=12)

    def _save(self):
        name = self.name_ent.get().strip()
        if not name:
            messagebox.showwarning(t("svr.err_name_title"),
                                   t("svr.err_name_msg"))
            return
        if any(r["name"].lower() == name.lower() for r in self.app.recipes):
            messagebox.showerror(t("svr.err_dup_title"),
                                 t("svr.err_dup_msg", name=name))
            return

        serving_g = None
        sv_str = self.serving_ent.get().strip()
        if sv_str:
            try:
                sv = float(sv_str)
                serving_g = sv if sv > 0 else None
            except ValueError:
                pass

        notes = self.notes_txt.get("1.0", END).strip()
        md    = self.meal_data

        recipe = new_recipe(
            name            = name,
            ingredients     = md["ingredients"],
            raw_weight      = md["raw_weight"],
            raw_totals      = md["raw_totals"],
            prepared_weight = md.get("prepared_weight"),
            prep_totals     = md.get("prep_totals"),
            serving_g       = serving_g,
            notes           = notes,
        )

        self.app.recipes.append(recipe)
        save_recipes(self.app.recipes)
        self.app.recipe_frame.refresh()
        self.result = recipe
        messagebox.showinfo(t("svr.info_saved_title"),
                            t("svr.info_saved_msg", name=name))
        self.on_saved()
        self.destroy()
