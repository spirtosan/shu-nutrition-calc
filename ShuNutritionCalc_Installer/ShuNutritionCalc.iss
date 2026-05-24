; =============================================================================
; ShuNutritionCalc.iss — Inno Setup installer script
; Shu Nutrition Calc v5.3  by Ivan Shumkov
;
; HOW TO USE:
;   1. Install Inno Setup 6 from https://jrsoftware.org/isinfo.php
;   2. Compile your app:
;        python -m PyInstaller --onefile --noconsole ^
;            --collect-all customtkinter ^
;            --collect-all tkcalendar ^
;            shu_nutrition_calc.py
;   3. Copy  dist\ShuNutritionCalc.exe  →  assets\ShuNutritionCalc.exe
;   4. Replace assets\db\food_db_bg.json with your real Bulgarian database
;   5. Open this file in Inno Setup IDE and press Compile (Ctrl+F9)
;   6. Your installer appears in  Output\ShuNutritionCalc_v5.3_Setup.exe
; =============================================================================

#define AppName      "Shu Nutrition Calc"
#define AppVersion   "5.3"
#define AppPublisher "Ivan Shumkov"
#define AppContact   "spirtosan@gmail.com"
#define AppExeName   "ShuNutritionCalc.exe"
#define AppYear      "2026"

[Setup]
AppId={{E3A7F2B1-4C8D-4A2E-9F1B-7D3C8A5E6F2D}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=mailto:{#AppContact}
AppSupportURL=mailto:{#AppContact}
AppContact={#AppContact}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=Output
OutputBaseFilename=ShuNutritionCalc_v{#AppVersion}_Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
WizardSizePercent=120
SetupIconFile=assets\img\mylogo.ico
; Require Windows 10 or later
MinVersion=10.0
PrivilegesRequiredOverridesAllowed=dialog
; Show "Are you sure?" before aborting
PrivilegesRequired=lowest
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\img\mylogo.ico
; Installer branding colours (Inno Setup 6.3+)
WizardSmallImageFile=

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "ru"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "bg"; MessagesFile: "assets\Bulgarian.isl"

[CustomMessages]
; ── Database selection page ──────────────────────────────────────────────────
en.DBPageCaption=Choose Food Database
en.DBPageDescription=Select the starter food database to install.
en.DBPageSubCaption=You can always add, edit or delete food items inside the app.
en.DBOpt_EN=English / international food database (default)
en.DBOpt_BG=Bulgarian food database
en.DBOpt_RU=Russian food database
en.DBOpt_Empty=Empty database — start from scratch
; ── Shortcut page ────────────────────────────────────────────────────────────
en.Shortcut_Desktop=Create a &desktop shortcut
; ── Finish page ──────────────────────────────────────────────────────────────
en.FinishRunApp=&Start {#AppName} now
; ── Uninstall ────────────────────────────────────────────────────────────────
en.UninstallKeepData=Keep your personal data files (food_db.json, meal_log.json, recipes.json)?
en.UninstallRemoving=Removing {#AppName}...

ru.DBPageCaption=Выбор базы данных продуктов
ru.DBPageDescription=Выберите начальную базу данных.
ru.DBPageSubCaption=Вы всегда можете добавлять, редактировать и удалять продукты в программе.
ru.DBOpt_EN=Английская / международная (по умолчанию)
ru.DBOpt_BG=Болгарская база данных
ru.DBOpt_RU=Русская база данных
ru.DBOpt_Empty=Пустая база — начать с нуля
ru.Shortcut_Desktop=Создать ярлык на &рабочем столе
ru.FinishRunApp=&Запустить {#AppName} сейчас
ru.UninstallKeepData=Сохранить файлы данных (food_db.json, meal_log.json, recipes.json)?
ru.UninstallRemoving=Удаление {#AppName}...

bg.DBPageCaption=Избор на база данни
bg.DBPageDescription=Изберете начална база данни с храни.
bg.DBPageSubCaption=Можете да добавяте, редактирате и изтривате храни в програмата.
bg.DBOpt_EN=Английска / международна (по подразбиране)
bg.DBOpt_BG=Българска база данни
bg.DBOpt_RU=Руска база данни
bg.DBOpt_Empty=Празна база — започни от нулата
bg.Shortcut_Desktop=Създай пряк път на &работния плот
bg.FinishRunApp=&Стартирай {#AppName} сега
bg.UninstallKeepData=Запази файловете с данни (food_db.json, meal_log.json, recipes.json)?
bg.UninstallRemoving=Премахване на {#AppName}...

; ── Inno Setup built-in custom messages — bg ─────────────────────────────────
bg.NameAndVersion=%1 версия %2
bg.AdditionalIcons=Допълнителни икони:
bg.CreateDesktopIcon=Създай икона на &работния плот
bg.CreateQuickLaunchIcon=Създай икона в лентата за &бързо стартиране
bg.ProgramOnTheWeb=%1 в интернет
bg.UninstallProgram=Деинсталиране на %1
bg.LaunchProgram=Стартирай %1
bg.AssocFileExtension=Асоциирай %1 с разширение %2
bg.AssocingFileExtension=Асоциране на %1 с разширение %2...
bg.AutoStartProgramGroupDescription=Автоматично стартиране:
bg.AutoStartProgram=Стартирай автоматично %1
bg.AddonHostProgramNotFound=%1 не е намерен. Желаете ли да продължите?

; ── Inno Setup built-in custom messages — ru ─────────────────────────────────
ru.NameAndVersion=%1 версия %2
ru.AdditionalIcons=Дополнительные значки:
ru.CreateDesktopIcon=Создать значок на &рабочем столе
ru.CreateQuickLaunchIcon=Создать значок на панели &быстрого запуска
ru.ProgramOnTheWeb=%1 в интернете
ru.UninstallProgram=Удалить %1
ru.LaunchProgram=Запустить %1
ru.AssocFileExtension=Связать %1 с расширением %2
ru.AssocingFileExtension=Связывание %1 с расширением %2...
ru.AutoStartProgramGroupDescription=Автозапуск:
ru.AutoStartProgram=Автоматически запускать %1
ru.AddonHostProgramNotFound=%1 не найден. Продолжить?

[Tasks]
Name: "desktopicon"; Description: "{cm:Shortcut_Desktop}"; \
    GroupDescription: "{#AppName}"; Flags: unchecked

[Files]
; ── Main executable ──────────────────────────────────────────────────────────
Source: "assets\{#AppExeName}"; DestDir: "{app}"; \
    Flags: ignoreversion
; ── Image / icon files ──────────────────────────────────────────────────────
Source: "assets\img\mylogo.ico";    DestDir: "{app}\img"; Flags: ignoreversion
Source: "assets\img\mylogo.svg";    DestDir: "{app}\img"; Flags: ignoreversion
Source: "assets\img\mylogo64.png";  DestDir: "{app}\img"; Flags: ignoreversion
Source: "assets\img\mylogo128.png"; DestDir: "{app}\img"; Flags: ignoreversion
Source: "assets\img\mylogo256.png"; DestDir: "{app}\img"; Flags: ignoreversion

; ── Language files ───────────────────────────────────────────────────────────
Source: "assets\lang\lang_en.json"; DestDir: "{app}\lang"; Flags: ignoreversion
Source: "assets\lang\lang_ru.json"; DestDir: "{app}\lang"; Flags: ignoreversion
Source: "assets\lang\lang_bg.json"; DestDir: "{app}\lang"; Flags: ignoreversion

; ── Help / manual files ──────────────────────────────────────────────────────
Source: "assets\help\help_en.html"; DestDir: "{app}\help"; Flags: ignoreversion
Source: "assets\help\help_ru.html"; DestDir: "{app}\help"; Flags: ignoreversion
Source: "assets\help\help_bg.html"; DestDir: "{app}\help"; Flags: ignoreversion

; ── Starter databases (all copied to {app}\db, one selected as food_db.json) ─
Source: "assets\db\food_db_bg.json";    DestDir: "{app}\db"; Flags: ignoreversion
Source: "assets\db\food_db_ru.json";    DestDir: "{app}\db"; Flags: ignoreversion
Source: "assets\db\food_db_en.json";    DestDir: "{app}\db"; Flags: ignoreversion
Source: "assets\db\food_db_empty.json"; DestDir: "{app}\db"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#AppName}";          Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
; Desktop (only if task ticked)
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; \
    Description: "{cm:FinishRunApp}"; \
    Flags: nowait postinstall skipifsilent

[UninstallRun]
; Nothing extra needed — data files are left in place (handled in Code)

; =============================================================================
; PASCAL SCRIPT — database selection wizard page + conditional file copy
; =============================================================================

[Code]

var
  DBPage: TInputOptionWizardPage;

// ── Create custom wizard pages ─────────────────────────────────────────────

procedure InitializeWizard;
begin
  // Page 1: Database selection — appears after the destination dir page
  DBPage := CreateInputOptionPage(
    wpSelectDir,
    CustomMessage('DBPageCaption'),
    CustomMessage('DBPageDescription'),
    CustomMessage('DBPageSubCaption'),
    True,   // exclusive (radio buttons)
    False   // no scroll
  );
  DBPage.Add(CustomMessage('DBOpt_EN'));
  DBPage.Add(CustomMessage('DBOpt_BG'));
  DBPage.Add(CustomMessage('DBOpt_RU'));
  DBPage.Add(CustomMessage('DBOpt_Empty'));
  DBPage.SelectedValueIndex := 0;  // English selected by default
end;


// ── Write food_db.json after all files are installed ──────────────────────

procedure CurStepChanged(CurStep: TSetupStep);
var
  SrcFile, DestFile: String;
begin
  if CurStep = ssPostInstall then
  begin
    DestFile := ExpandConstant('{app}\food_db.json');

    case DBPage.SelectedValueIndex of
      0: SrcFile := ExpandConstant('{app}\db\food_db_en.json');
      1: SrcFile := ExpandConstant('{app}\db\food_db_bg.json');
      2: SrcFile := ExpandConstant('{app}\db\food_db_ru.json');
      3: SrcFile := ExpandConstant('{app}\db\food_db_empty.json');
    else
      SrcFile := ExpandConstant('{app}\db\food_db_en.json');
    end;

    if FileExists(SrcFile) then
    begin
      if not CopyFile(SrcFile, DestFile, False) then
        MsgBox('Warning: could not create food_db.json.' + #13#10 +
               'Please copy the database file manually from the db\ folder.',
               mbError, MB_OK);
    end;
  end;
end;


// ── Uninstall: ask whether to keep personal data ─────────────────────────

function InitializeUninstall(): Boolean;
var
  MsgResult: Integer;
begin
  Result := True;
  MsgResult := MsgBox(
    CustomMessage('UninstallKeepData'),
    mbConfirmation,
    MB_YESNO or MB_DEFBUTTON1
  );

  if MsgResult = IDNO then
  begin
    // User chose to delete data — remove personal files
    DeleteFile(ExpandConstant('{app}\food_db.json'));
    DeleteFile(ExpandConstant('{app}\meal_log.json'));
    DeleteFile(ExpandConstant('{app}\recipes.json'));
    DeleteFile(ExpandConstant('{app}\settings.json'));
    DeleteFile(ExpandConstant('{app}\print_config.json'));
  end;
end;
