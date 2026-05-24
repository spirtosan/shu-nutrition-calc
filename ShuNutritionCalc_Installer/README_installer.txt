================================================================================
  Shu Nutrition Calc v5.3 — Installer Project
================================================================================

WHAT IS THIS FOLDER?
────────────────────
This folder contains everything needed to build a Windows installer (.exe)
for Shu Nutrition Calc using the free tool Inno Setup 6.

BEFORE YOU BUILD — REQUIRED STEPS
────────────────────────────────────

  Step 1 — Install Inno Setup 6 (free)
    Download from: https://jrsoftware.org/isinfo.php
    Install with default settings.

  Step 2 — Compile the Python app
    Open a command prompt in your source folder and run:

      pip install customtkinter tkcalendar pyinstaller
      PowerShell (use backtick ` for line continuation):

      python -m PyInstaller --onefile --noconsole `
          --name ShuNutritionCalc `
          --icon=mylogo.ico `
          --add-data "img;img" `
          --collect-all customtkinter `
          --collect-all tkcalendar `
          shu_nutrition_calc.py

      Or all on one line (works in both PowerShell and cmd.exe):

      python -m PyInstaller --onefile --noconsole --name ShuNutritionCalc --icon=mylogo.ico --add-data "img;img" --collect-all customtkinter --collect-all tkcalendar shu_nutrition_calc.py

    This creates: dist\ShuNutritionCalc.exe

  Step 3 — Place the .exe into assets\
    Copy:  dist\ShuNutritionCalc.exe
    To:    assets\ShuNutritionCalc.exe   ← this installer folder

  Step 4 — Replace the Bulgarian database (important!)
    The file  assets\db\food_db_bg.json  currently contains only 11 demo items.
    Replace it with your real food_db.json to include all your Bulgarian foods.

  Step 5 — Compile the installer
    Open  ShuNutritionCalc.iss  in Inno Setup (double-click the file).
    Press  Ctrl+F9  or go to  Build → Compile.
    Your installer will appear at:  Output\ShuNutritionCalc_v5.3_Setup.exe


FOLDER STRUCTURE
────────────────────────────────────────────────────────────────────────────────

  ShuNutritionCalc_Installer/
  │
  ├── ShuNutritionCalc.iss        ← Inno Setup script — the installer recipe
  ├── README_installer.txt        ← this file
  │
  ├── assets/                     ← everything that gets installed on user's PC
  │   ├── ShuNutritionCalc.exe    ← ⚠  PLACE YOUR COMPILED EXE HERE
  │   │
  │   ├── lang/                   ← UI translation strings (all 3 languages)
  │   │   ├── lang_en.json
  │   │   ├── lang_ru.json
  │   │   └── lang_bg.json
  │   │
  │   ├── help/                   ← User manuals
  │   │   ├── help_en.html
  │   │   ├── help_ru.html
  │   │   └── help_bg.html
  │   │
  │   └── db/                     ← Starter food databases
  │       ├── food_db_bg.json     ← ⚠  REPLACE with your real Bulgarian DB
  │       ├── food_db_ru.json     ← starter Russian database (11 basic items)
  │       ├── food_db_en.json     ← starter English database (11 basic items)
  │       └── food_db_empty.json  ← empty [ ] — for "start from scratch" option
  │
  └── Output/                     ← created automatically by Inno Setup
      └── ShuNutritionCalc_v5.3_Setup.exe   ← your final installer


WHAT THE INSTALLER DOES (user experience)
────────────────────────────────────────────────────────────────────────────────

  1. Welcome screen
  2. Choose installation folder
     Default: C:\Program Files\Shu Nutrition Calc
     (user can change this freely)
  3. Choose starter food database
     ● Bulgarian food database  (default, recommended)
     ○ Russian food database
     ○ English / international food database
     ○ Empty database — start from scratch
  4. Optional shortcuts
     □ Create desktop shortcut  (unchecked by default)
     ☑ Create Start Menu folder (checked by default)
  5. Install — copies all files
  6. Finish — option to launch the app immediately

  On UNINSTALL: asks "Keep your personal data files?"
    YES → food_db.json, meal_log.json, recipes.json kept on disk
    NO  → all data files deleted along with the app


WHAT GETS INSTALLED WHERE
────────────────────────────────────────────────────────────────────────────────

  {install_folder}\
  ├── ShuNutritionCalc.exe       ← main application
  ├── food_db.json               ← created from chosen starter database
  ├── lang\
  │   ├── lang_en.json
  │   ├── lang_ru.json
  │   └── lang_bg.json
  ├── help\
  │   ├── help_en.html
  │   ├── help_ru.html
  │   └── help_bg.html
  └── db\
      ├── food_db_bg.json        ← kept for reference / future use
      ├── food_db_ru.json
      ├── food_db_en.json
      └── food_db_empty.json

  Files auto-created on first run:
      meal_log.json, recipes.json, settings.json, print_config.json


NOTES
────────────────────────────────────────────────────────────────────────────────

  • No administrator rights required — installs per-user by default
  • No registry entries written by the application itself
  • Installer supports Windows 10 and later
  • Output installer is a single .exe (~30-60 MB depending on Python bundling)
  • To rebuild after updating the app: repeat Steps 2-3-5 only

================================================================================
