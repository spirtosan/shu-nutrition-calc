# =============================================================================
# shu_nutrition_calc.py — Shu Nutrition Calc v5.2
# Main entry point. Initialises the CTk application, sidebar navigation,
# language switcher, and all tab frames. Holds shared db and log references.
# =============================================================================

import customtkinter as ctk
try:
    from PIL import Image as _PILImage
    _PIL_OK = True
except ImportError:
    _PIL_OK = False
from tkinter import messagebox
import webbrowser
import os

from config import APP_NAME, VERSION, CREATOR, YEAR, BASE_DIR, get_help_file, LOGO_SMALL, LOGO_LARGE
from models import load_db, load_log, load_settings, save_settings
import lang as _lang
from lang import t, SUPPORTED_LANGS

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ShuNutritionCalc(ctk.CTk):
    """
    Root application window.
    Owns:  self.db  — list of food item dicts (shared with all frames)
           self.log — list of meal log entry dicts (shared with all frames)
    Frames are created once and shown/hidden via grid.
    On language switch all frames are destroyed and rebuilt.
    """

    def __init__(self):
        super().__init__()
        # Load settings and init language before building any UI
        settings = load_settings()
        _lang.init_lang(BASE_DIR, settings.get("language", "en"))

        self.title(f"{APP_NAME}  v{VERSION}")
        self.geometry("1280x920")
        self.minsize(1000, 700)

        # Shared data
        self.db      = load_db()
        self.log     = load_log()
        from models import load_recipes
        self.recipes = load_recipes()

        # Track which frame is currently shown
        self._current_frame_key = "calc"

        # Layout: sidebar col 0, main col 1
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_container()
        self._build_frames()

        # Start on Meal Builder
        self.show_frame("calc")

    # ------------------------------------------------------------------
    # Sidebar
    # ------------------------------------------------------------------

    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=210, corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        self._sidebar_frame = sb

        # Branding — logo image with text fallback
        _logo_shown = False
        if _PIL_OK:
            try:
                import os as _os, sys as _sys
                # Support both: running from source and frozen PyInstaller exe
                _base = getattr(_sys, "_MEIPASS", BASE_DIR)
                _small = _os.path.join(_base, "img", "mylogo64.png")
                if not _os.path.exists(_small):
                    _small = LOGO_SMALL  # fallback to config path
                if _os.path.exists(_small):
                    _img = _PILImage.open(_small).resize((64, 64), _PILImage.LANCZOS)
                    _ctk_img = ctk.CTkImage(light_image=_img, dark_image=_img, size=(64, 64))
                    ctk.CTkLabel(sb, image=_ctk_img, text="").pack(pady=(20, 2))
                    _logo_shown = True
            except Exception:
                pass
        if not _logo_shown:
            ctk.CTkLabel(sb, text="SHU",
                         font=("Segoe UI", 28, "bold"),
                         text_color="#f5a623").pack(pady=(28, 0))
            ctk.CTkLabel(sb, text="NUTRITION CALC",
                         font=("Segoe UI", 11, "bold"),
                         text_color="#f5a623").pack()
        ctk.CTkLabel(sb, text=f"v{VERSION}",
                     font=("Segoe UI", 10),
                     text_color="#909090").pack(pady=(2, 16))

        self._nav_btns = {}

        # Navigation buttons
        nav_items = [
            (t("sidebar.meal_builder"),  "calc"),
            (t("sidebar.database"),      "db"),
            (t("sidebar.recipe_book"),   "recipes"),
            (t("sidebar.journal"),       "journal"),
        ]
        for label, key in nav_items:
            btn = ctk.CTkButton(
                sb, text=label, anchor="w",
                fg_color="#1a3a5a",
                hover_color="#1e4a7a",
                font=("Segoe UI", 13),
                command=lambda k=key: self.show_frame(k))
            btn.pack(fill="x", padx=12, pady=3)
            self._nav_btns[key] = btn

        # Separator
        ctk.CTkFrame(sb, height=1, fg_color="#333").pack(
            fill="x", padx=16, pady=10)

        # Help / About
        for label, key in [(t("sidebar.help_manual"), "help"),
                            (t("sidebar.about"),        "about")]:
            btn = ctk.CTkButton(
                sb, text=label, anchor="w",
                fg_color="#1a3a5a", hover_color="#1e4a7a",
                font=("Segoe UI", 12),
                command=lambda k=key: self.show_frame(k))
            btn.pack(fill="x", padx=12, pady=3)
            self._nav_btns[key] = btn

        # Separator
        ctk.CTkFrame(sb, height=1, fg_color="#333").pack(
            fill="x", padx=16, pady=(14, 6))

        # Language switcher
        lang_lbl = ctk.CTkLabel(sb, text="Lang / Язык / Език",
                                font=("Segoe UI", 10),
                                text_color="#666666")
        lang_lbl.pack(pady=(0, 4))

        lang_f = ctk.CTkFrame(sb, fg_color="transparent")
        lang_f.pack(padx=12, pady=(0, 14))
        self._lang_btns = {}
        cur = _lang.get_lang()
        for code, label, _ in SUPPORTED_LANGS:
            active = (code == cur)
            btn = ctk.CTkButton(
                lang_f, text=label, width=52,
                fg_color="#c87028" if active else "#1a3a5a",
                hover_color="#d4902e" if active else "#1e4a7a",
                font=("Segoe UI", 12, "bold"),
                command=lambda c=code: self._set_language(c))
            btn.pack(side="left", padx=3)
            self._lang_btns[code] = btn

    # ------------------------------------------------------------------
    # Language switching
    # ------------------------------------------------------------------

    def _set_language(self, code):
        if code == _lang.get_lang():
            return
        # Save preference
        settings = load_settings()
        settings["language"] = code
        save_settings(settings)
        # Reload translations
        _lang.set_lang(BASE_DIR, code)
        # Rebuild entire UI with new language
        self._rebuild_ui()

    def _rebuild_ui(self):
        """Destroy and rebuild sidebar + all content frames with current language."""
        current_key = self._current_frame_key
        # Destroy sidebar
        self._sidebar_frame.destroy()
        self._nav_btns = {}
        # Destroy all content frames
        for frame in self.frames.values():
            frame.destroy()
        self.frames = {}
        # Rebuild
        self._build_sidebar()
        self._build_frames()
        # Restore same view
        self.show_frame(current_key)

    # ------------------------------------------------------------------
    # Main container
    # ------------------------------------------------------------------

    def _build_main_container(self):
        self.container = ctk.CTkFrame(self,
                                      corner_radius=12,
                                      fg_color="#121212")
        self.container.grid(row=0, column=1,
                            sticky="nsew", padx=16, pady=16)
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)

    def _build_frames(self):
        """Instantiate all tab frames. Import here to avoid circular deps."""
        from ui_meal_builder import MealBuilderFrame
        from ui_database     import DatabaseFrame
        from ui_recipes      import RecipeBookFrame
        from ui_log          import JournalFrame

        self.frames = {}
        self.frames["calc"]    = MealBuilderFrame(self.container, self)
        self.frames["db"]      = DatabaseFrame(self.container, self)
        self.frames["recipes"] = RecipeBookFrame(self.container, self)
        self.frames["journal"] = JournalFrame(self.container, self)
        self.frames["help"]    = HelpFrame(self.container, self)
        self.frames["about"]   = AboutFrame(self.container, self)

        # Keep cross-frame references
        self.db_frame      = self.frames["db"]
        self.recipe_frame  = self.frames["recipes"]
        self.journal_frame = self.frames["journal"]

        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")

    def _switch_tab(self, name):
        self.show_frame(name)

    def show_frame(self, name):
        """Bring the named frame to front and highlight its sidebar button."""
        for frame in self.frames.values():
            frame.grid_remove()
        self.frames[name].grid(row=0, column=0, sticky="nsew")
        self._current_frame_key = name
        for key, btn in self._nav_btns.items():
            if key == name:
                btn.configure(fg_color="#c87028", text_color="white")
            else:
                btn.configure(fg_color="#1a3a5a", text_color="white")


# =============================================================================
# HELP FRAME
# =============================================================================

class HelpFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="#1e1e1e",
                           border_width=1, border_color="#2a2a2a")
        top.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(top, text=t("help.title"),
                     font=("Segoe UI", 18, "bold"),
                     text_color="#f5a623").pack(side="left", padx=16, pady=10)
        ctk.CTkButton(
            top, text=t("help.btn_open_browser"),
            width=300, fg_color="#1a7878",
            command=self._open_browser
        ).pack(side="right", padx=16, pady=10)

        scroll = ctk.CTkScrollableFrame(self)
        scroll.pack(fill="both", expand=True, padx=20, pady=8)

        for title, body in _help_content():
            ctk.CTkLabel(scroll, text=title,
                         font=("Segoe UI", 15, "bold"),
                         text_color="#f5a623",
                         anchor="w").pack(fill="x", padx=8, pady=(14, 2))
            ctk.CTkLabel(scroll, text=body,
                         font=("Segoe UI", 13),
                         text_color="#b0b0b0",
                         anchor="w", justify="left",
                         wraplength=820).pack(fill="x", padx=20, pady=(0, 4))

    def _open_browser(self):
        lang_code = _lang.get_lang()
        help_file = get_help_file(lang_code)
        if os.path.exists(help_file):
            webbrowser.open(f"file:///{help_file.replace(os.sep, '/')}")
        else:
            messagebox.showwarning(
                t("help.err_missing_title"),
                t("help.err_missing_msg", lang=lang_code))


# =============================================================================
# ABOUT FRAME
# =============================================================================

class AboutFrame(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self._build()

    def _build(self):
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.place(relx=0.5, rely=0.45, anchor="center")

        # Logo image
        if _PIL_OK:
            try:
                import os as _os, sys as _sys
                _base = getattr(_sys, "_MEIPASS", BASE_DIR)
                _large = _os.path.join(_base, "img", "mylogo128.png")
                if not _os.path.exists(_large):
                    _large = LOGO_LARGE
                if _os.path.exists(_large):
                    _img = _PILImage.open(_large).resize((128, 128), _PILImage.LANCZOS)
                    _ctk_img = ctk.CTkImage(light_image=_img, dark_image=_img, size=(128, 128))
                    ctk.CTkLabel(inner, image=_ctk_img, text="").pack(pady=(0, 12))
            except Exception:
                pass

        ctk.CTkLabel(inner, text=APP_NAME,
                     font=("Segoe UI", 32, "bold"),
                     text_color="#f5a623").pack(pady=(0, 6))

        ctk.CTkLabel(inner, text=t("about.version", v=VERSION),
                     font=("Segoe UI", 17),
                     text_color="#f5a623").pack()

        ctk.CTkLabel(inner, text=t("about.created_by", name=CREATOR),
                     font=("Segoe UI", 15)).pack(pady=(6, 2))

        ctk.CTkLabel(inner, text="spirtosan@gmail.com",
                     font=("Segoe UI", 14),
                     text_color="#f5a623").pack(pady=(0, 4))

        ctk.CTkLabel(inner, text=t("about.rights", year=YEAR),
                     font=("Segoe UI", 13),
                     text_color="#909090").pack()

        ctk.CTkLabel(inner, text=t("about.tagline"),
                     font=("Segoe UI", 13),
                     text_color="#909090").pack(pady=2)

        ctk.CTkLabel(inner, text=t("about.disclaimer"),
                     font=("Segoe UI", 12),
                     text_color="#555555").pack(pady=(2, 16))

        hist = ctk.CTkFrame(inner, fg_color="#1e1e1e",
                            border_width=1, border_color="#2a2a2a",
                            corner_radius=10)
        hist.pack(padx=20, pady=8)
        for ver, note_key in [
            ("v4.0", "about.v40_note"),
            ("v5.0", "about.v50_note"),
            ("v5.1", "about.v51_note"),
            ("v5.2", "about.v52_note"),
        ]:
            row = ctk.CTkFrame(hist, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row, text=ver, width=48,
                         font=("Segoe UI", 12, "bold"),
                         text_color="#f5a623").pack(side="left")
            ctk.CTkLabel(row, text=t(note_key),
                         font=("Segoe UI", 12),
                         text_color="#909090").pack(side="left", padx=8)


# =============================================================================
# INLINE HELP CONTENT
# =============================================================================

def _help_content():
    """
    Returns list of (section_title, body_text) tuples for inline display.
    Full details are in help_{lang}.html.
    """
    lang = _lang.get_lang()
    return [
        (t("help_s.quick_setup"),   _help_quick(lang)),
        (t("help_s.meal_builder"),  _help_mb(lang)),
        (t("help_s.database"),      _help_db(lang)),
        (t("help_s.journal"),       _help_jrn(lang)),
        (t("help_s.print"),         _help_print(lang)),
        (t("help_s.calculations"),  _help_calc(lang)),
        (t("help_s.disclaimer"),    _help_disclaimer(lang)),
    ]


def _help_quick(lang):
    if lang == "ru":
        return (
            "Установка не требуется. Поместите ShuNutritionCalc.exe в любую папку. "
            "Файлы данных создаются автоматически при первом запуске:\n"
            "  • food_db.json       — база продуктов и рецептов\n"
            "  • meal_log.json      — все записанные блюда\n"
            "  • print_config.json  — настройки печати\n"
            "  • settings.json      — язык и прочие настройки\n\n"
            "Регулярно делайте резервные копии food_db.json и meal_log.json.")
    if lang == "bg":
        return (
            "Не е необходима инсталация. Поставете ShuNutritionCalc.exe в произволна папка. "
            "Файловете с данни се създават автоматично при първото стартиране:\n"
            "  • food_db.json       — вашата база с продукти и рецепти\n"
            "  • meal_log.json      — всички записани ястия\n"
            "  • print_config.json  — настройки за печат\n"
            "  • settings.json      — език и други настройки\n\n"
            "Редовно правете резервни копия на food_db.json и meal_log.json.")
    return (
        "No installation required. Place ShuNutritionCalc.exe in any folder. "
        "All data files are auto-created on first run in the same folder:\n"
        "  • food_db.json       — your food and recipe library\n"
        "  • meal_log.json      — all logged meals\n"
        "  • print_config.json  — saved print settings\n"
        "  • settings.json      — language and app settings\n\n"
        "Back up food_db.json and meal_log.json regularly.")


def _help_mb(lang):
    if lang == "ru":
        return (
            "Ищите продукты, вводите вес в граммах, нажмите Enter или кнопку '+ Добавить в блюдо'. "
            "Макросы обновляются мгновенно: общий вес, значения на 100г и на порцию.\n\n"
            "Поле порции: введите любой вес, чтобы увидеть его БЖУ. "
            "Чекбокс 'Целое блюдо как одна порция' задаёт предзаполнение в диалоге дневника.\n\n"
            "Вес готового блюда: введите вес после приготовления. "
            "При готовке испаряется только вода — Б, Ж, У и ккал не изменяются. "
            "Переключайте вид RAW / ГОТОВОЕ.\n\n"
            "Сохранить как рецепт: сохраняет блюдо в базу данных как запись [R] с значениями на 100г.")
    if lang == "bg":
        return (
            "Търсете продукти, въведете тегло в грамове, натиснете Enter или '+ Добави към ястието'. "
            "Макросите се актуализират незабавно: общо тегло, стойности на 100г и на порция.\n\n"
            "Поле за порция: въведете произволно тегло, за да видите БМВ. "
            "Отметката 'Използвай цялото ястие като порция' задава предварителното запълване в дневника.\n\n"
            "Тегло на приготвеното ястие: въведете теглото след готвене. "
            "При готвене се изпарява само вода — Б, М, В и ккал остават непроменени. "
            "Превключвайте изглед СУРОВО / ПРИГОТВЕНО.\n\n"
            "Запази като рецепта: запазва ястието в базата данни като запис [R] със стойности на 100г.")
    return (
        "Search for foods, enter weight in grams, press Enter or click '+ Add to Meal'. "
        "Macros update live: whole meal totals, per-100g values, and portion values.\n\n"
        "Portion field: type any weight to see its macros. "
        "The 'Use whole meal as portion' checkbox controls the pre-fill in the Journal dialog.\n\n"
        "Prepared Food Weight: Enter the cooked dish weight after cooking. "
        "Only water changes during cooking — protein, fat, carbs and kcal stay the same. "
        "Use the RAW / PREPARED toggle to switch views.\n\n"
        "Save as Food: saves the meal as a new [R] entry in the food database at per-100g values.\n"
        "Save Recipe: saves the full recipe (all ingredients + values) to the Recipe Book.")


def _help_db(lang):
    if lang == "ru":
        return (
            "Ваша личная база продуктов. Все значения хранятся на 100г. "
            "ккал рассчитывается автоматически: Б × 4 + Ж × 9 + У × 4.\n\n"
            "Правила проверки:\n"
            "  • Б + Ж + У не может превышать 100г на 100г продукта\n"
            "  • Максимум ккал/100г = 900 (чистый жир)\n"
            "  • Нет дубликатов, нет отрицательных значений\n\n"
            "Добавляйте ингредиенты с нулевыми макросами (вода, соль) как 0/0/0/0 — "
            "они влияют на вес и минимальный вес готового блюда.")
    if lang == "bg":
        return (
            "Вашата лична база с продукти. Всички стойности се съхраняват на 100г. "
            "ккал се изчислява автоматично: Б × 4 + М × 9 + В × 4.\n\n"
            "Правила за проверка:\n"
            "  • Б + М + В не може да надвишава 100г на 100г храна\n"
            "  • Максимум ккал/100г = 900 (чисти мазнини)\n"
            "  • Без дублирания, без отрицателни стойности\n\n"
            "Добавяйте съставки с нулеви макроси (вода, сол) като 0/0/0/0 — "
            "те влияят на теглото и минималното тегло на приготвеното ястие.")
    return (
        "Your personal food library. All values are stored per 100g. "
        "kcal is auto-calculated: P × 4 + F × 9 + C × 4.\n\n"
        "Validation rules:\n"
        "  • P + F + C cannot exceed 100g per 100g of food\n"
        "  • Maximum kcal/100g = 900 (pure fat)\n"
        "  • No duplicate names, no negative values\n\n"
        "Add zero-macro ingredients (water, salt) as 0/0/0/0 so they contribute "
        "correctly to raw weight and prepared weight floor checks.")


def _help_jrn(lang):
    if lang == "ru":
        return (
            "Добавить в дневник из Конструктора открывает диалог с:\n"
            "  • Названием блюда (предзаполняется последним использованным)\n"
            "  • Датой/временем (по умолчанию — текущее)\n"
            "  • Порцией (г) — обязательно\n"
            "  • Предпросмотром ккал/Б/Ж/У в реальном времени\n"
            "  • Заметками\n\n"
            "Сводка периода: среднесуточные ккал/Б/Ж/У за выбранный период. "
            "Пропущенные дни можно пропустить, обнулить или заполнить вручную.")
    if lang == "bg":
        return (
            "Добави в дневника от Конструктора отваря диалог с:\n"
            "  • Наименование на ястието (предварително запълнено с последно използваното)\n"
            "  • Дата/час (по подразбиране — текущо)\n"
            "  • Порция (г) — задължително\n"
            "  • Преглед на ккал/Б/М/В в реално време\n"
            "  • Бележки\n\n"
            "Обобщение на периода: средни дневни ккал/Б/М/В за избрания период. "
            "Липсващите дни могат да се пропуснат, нулират или попълнят ръчно.")
    return (
        "Add to Journal from Meal Builder opens a dialog with:\n"
        "  • Meal name (last used name pre-filled)\n"
        "  • Date / Time (defaults to now)\n"
        "  • Portion (g) — required\n"
        "  • Live preview: kcal / P / F / C update as you type the portion\n"
        "  • Notes\n\n"
        "Period Summary: average daily kcal / P / F / C for the selected period. "
        "Missing days can be skipped, zeroed, or filled manually.")


def _help_print(lang):
    if lang == "ru":
        return (
            "Отчёты создаются как HTML-файлы и открываются в браузере. "
            "Для печати используйте Ctrl+P в браузере.\n\n"
            "Переключатели блюда: всё блюдо сырое/приготовленное, на 100г, на порцию, список ингредиентов.\n\n"
            "Переключатели журнала: отдельные записи, суточные итоги, среднее за период.\n\n"
            "Тема: тёмная = для экрана. Светлая = для печати (экономит чернила).")
    if lang == "bg":
        return (
            "Отчетите се генерират като HTML файлове и се отварят в браузъра. "
            "За печат използвайте Ctrl+P в браузъра.\n\n"
            "Превключватели за ястие: цяло ястие сурово/приготвено, на 100г, на порция, списък на съставките.\n\n"
            "Превключватели за дневника: отделни записи, дневни суми, средно за периода.\n\n"
            "Тема: тъмна = за екрана. Светла = за печат (пести мастило).")
    return (
        "Reports are generated as HTML files opened in your default browser. "
        "To print on paper use Ctrl+P in the browser, or Save as PDF.\n\n"
        "Meal print toggles: whole meal raw/prepared, per 100g raw/prepared, "
        "per portion raw/prepared, ingredient list.\n\n"
        "Log print toggles: individual meal entries, daily totals, period average.\n\n"
        "Theme: Dark = screen viewing. Light = printing on paper (saves ink).")


def _help_calc(lang):
    if lang == "ru":
        return (
            "Калории (общие факторы Этуотера):\n"
            "  ккал = Белки × 4 + Жиры × 9 + Углеводы × 4\n\n"
            "Вес готового блюда — физический принцип:\n"
            "  При готовке испаряется только вода. Б, Ж, У и ккал не изменяются — "
            "те же питательные вещества в меньшем весе.\n"
            "  • Итоговые значения готового = итоговые значения сырого\n"
            "  • Минимальный вес готового = Б + Ж + У (сухая масса)\n"
            "  • Максимальный вес готового = вес сырого\n\n"
            "На 100г:   итого_X / вес × 100\n"
            "На порцию: итого_X / вес × граммы_порции")
    if lang == "bg":
        return (
            "Калории (общи фактори на Атуотър):\n"
            "  ккал = Белтъци × 4 + Мазнини × 9 + Въглехидрати × 4\n\n"
            "Тегло на приготвеното ястие — физичен принцип:\n"
            "  При готвене се изпарява само вода. Б, М, В и ккал остават непроменени — "
            "същите хранителни вещества в по-малко тегло.\n"
            "  • Общо приготвено = общо сурово (идентично)\n"
            "  • Минимално тегло приготвено = Б + М + В (суха маса)\n"
            "  • Максимално тегло приготвено = сурово тегло\n\n"
            "На 100г:    общо_X / тегло × 100\n"
            "На порция:  общо_X / тегло × грамове_порция")
    return (
        "Calories (Atwater general factors):\n"
        "  kcal = Protein × 4 + Fat × 9 + Carbohydrates × 4\n\n"
        "Prepared weight — core physics rule:\n"
        "  Only water evaporates during cooking. Protein, fat, carbs and kcal "
        "are unchanged — the same nutrients in less weight.\n"
        "  • Prepared totals = raw totals (identical)\n"
        "  • Minimum prepared weight = P + F + C (dry macro mass)\n"
        "  • Maximum prepared weight = raw total weight\n\n"
        "Per 100g:  total_X / weight × 100\n"
        "Portion:   total_X / weight × portion_g")


def _help_disclaimer(lang):
    if lang == "ru":
        return (
            "Это приложение является персональным инструментом для учёта питания. "
            "Значения калорий являются приблизительными. "
            "Не является медицинской или диетологической рекомендацией — "
            "проконсультируйтесь со специалистом перед существенными изменениями в питании.")
    if lang == "bg":
        return (
            "Това приложение е личен инструмент за проследяване на храненето. "
            "Калоричните стойности са приблизителни. "
            "Не е медицински или диетологичен съвет — "
            "консултирайте се с квалифициран специалист преди значителни промени в диетата.")
    return (
        "This application is a personal nutrition tracking tool. "
        "Calorie values are estimates based on Atwater general factors. "
        "It is not medical or dietary advice — consult a qualified professional "
        "before making significant dietary changes.")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    app = ShuNutritionCalc()
    app.mainloop()
