# =============================================================================
# ui_database.py — Shu Nutrition Calc v5.2
# Database Manager tab: view, add, and delete food items.
# =============================================================================

import customtkinter as ctk
from tkinter import messagebox, Listbox, SINGLE, END
from models import save_db
from lang import t


class DatabaseFrame(ctk.CTkFrame):

    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        # --- Column headers ---
        header_f = ctk.CTkFrame(self, fg_color="transparent")
        header_f.pack(fill="x", padx=20, pady=(15, 2))

        ctk.CTkLabel(header_f, text=t("db.col_name"),
                     width=300, anchor="w",
                     font=("Segoe UI", 12, "bold"),
                     text_color="gray").pack(side="left", padx=10)
        for col_key in ["db.col_proteins", "db.col_fats",
                        "db.col_carbs", "db.col_kcal"]:
            ctk.CTkLabel(header_f, text=t(col_key), width=85,
                         font=("Segoe UI", 12, "bold"),
                         text_color="gray").pack(side="left", padx=4)

        # --- Listbox ---
        self.db_listbox = Listbox(
            self, font=("Consolas", 12),
            bg="#181818", fg="white",
            borderwidth=0, selectmode=SINGLE,
            activestyle="none"
        )
        self.db_listbox.pack(fill="both", expand=True, padx=20, pady=6)

        # --- Add new item controls ---
        add_ctrl = ctk.CTkFrame(self, fg_color="#2b2b2b")
        add_ctrl.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(add_ctrl,
                     text=t("db.add_title"),
                     font=("Arial", 12, "italic"),
                     text_color="#f5a623").grid(
                         row=0, column=0, columnspan=6, pady=6)

        self.in_n = ctk.CTkEntry(add_ctrl,
                                  placeholder_text=t("db.ph_name"), width=240)
        self.in_n.grid(row=1, column=0, padx=10, pady=10)

        self.in_p = ctk.CTkEntry(add_ctrl,
                                  placeholder_text=t("db.ph_proteins"), width=85)
        self.in_p.grid(row=1, column=1, padx=4)

        self.in_f = ctk.CTkEntry(add_ctrl,
                                  placeholder_text=t("db.ph_fats"), width=85)
        self.in_f.grid(row=1, column=2, padx=4)

        self.in_c = ctk.CTkEntry(add_ctrl,
                                  placeholder_text=t("db.ph_carbs"), width=85)
        self.in_c.grid(row=1, column=3, padx=4)

        self.in_k = ctk.CTkEntry(add_ctrl,
                                  placeholder_text=t("db.ph_kcal_auto"),
                                  width=90, state="disabled")
        self.in_k.grid(row=1, column=4, padx=4)

        ctk.CTkButton(add_ctrl, text=t("db.btn_save"),
                      fg_color="#2a8a38",
                      command=self._add_item).grid(row=1, column=5, padx=15)

        for entry in (self.in_p, self.in_f, self.in_c):
            entry.bind("<KeyRelease>", self._preview_kcal)

        # --- Delete button ---
        ctk.CTkButton(
            self, text=t("db.btn_delete"),
            fg_color="#8B0000",
            command=self._delete_item
        ).pack(pady=10)

        self.refresh()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def refresh(self):
        self.db_listbox.delete(0, END)
        for item in sorted(self.app.db, key=lambda x: x["name"]):
            self.db_listbox.insert(END, self._fmt_row(item))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fmt_row(self, item):
        p_lbl = t("mb.abbr_p")
        f_lbl = t("mb.abbr_f")
        c_lbl = t("mb.abbr_c")
        return (f"{item['name']:<38} | "
                f"{p_lbl}:{item['p']:<7.1f} | "
                f"{f_lbl}:{item['f']:<7.1f} | "
                f"{c_lbl}:{item['c']:<7.1f} | "
                f"{item['kcal']:.1f} kcal")

    def _preview_kcal(self, _event=None):
        try:
            p = float(self.in_p.get())
            f = float(self.in_f.get())
            c = float(self.in_c.get())
            kcal = round(p * 4 + f * 9 + c * 4, 1)
            self.in_k.configure(state="normal")
            self.in_k.delete(0, END)
            self.in_k.insert(0, str(kcal))
            self.in_k.configure(state="disabled")
        except ValueError:
            pass

    def _add_item(self):
        n = self.in_n.get().strip()

        if not n:
            messagebox.showwarning(t("db.err_missing_name_title"),
                                   t("db.err_missing_name_msg"))
            return

        if "|" in n:
            messagebox.showerror(t("db.err_invalid_name_title"),
                                 t("db.err_invalid_name_msg"))
            return

        if any(item["name"].lower() == n.lower() for item in self.app.db):
            messagebox.showerror(t("db.err_duplicate_title"),
                                 t("db.err_duplicate_msg", name=n))
            return

        try:
            p = float(self.in_p.get())
            f = float(self.in_f.get())
            c = float(self.in_c.get())
        except ValueError:
            messagebox.showerror(t("db.err_invalid_input_title"),
                                 t("db.err_invalid_input_msg"))
            return

        if p < 0 or f < 0 or c < 0:
            messagebox.showerror(t("db.err_negative_title"),
                                 t("db.err_negative_msg"))
            return

        if (p + f + c) > 100.01:
            messagebox.showerror(t("db.err_sum_title"),
                                 t("db.err_sum_msg", sum=f"{p+f+c:.1f}"))
            return

        new_item = {
            "name": n,
            "p":    p,
            "f":    f,
            "c":    c,
            "kcal": round(p * 4 + f * 9 + c * 4, 1),
        }
        self.app.db.append(new_item)
        save_db(self.app.db)
        self.refresh()

        for e in (self.in_n, self.in_p, self.in_f, self.in_c):
            e.delete(0, END)
        self.in_k.configure(state="normal")
        self.in_k.delete(0, END)
        self.in_k.configure(state="disabled")

    def _delete_item(self):
        sel = self.db_listbox.curselection()
        if not sel:
            messagebox.showwarning(t("db.err_no_selection_title"),
                                   t("db.err_no_selection_msg"))
            return

        sorted_db = sorted(self.app.db, key=lambda x: x["name"])
        item_to_del = sorted_db[sel[0]]
        name = item_to_del["name"]

        if messagebox.askyesno(t("db.confirm_delete_title"),
                               t("db.confirm_delete_msg", name=name)):
            self.app.db = [i for i in self.app.db if i["name"] != name]
            save_db(self.app.db)
            self.refresh()
