; Скрипт Inno Setup для создания инсталлятора ChatList
; Автоматически использует версию из version.py
; Версия будет подставлена скриптом build-installer.ps1

#define AppName "ChatList"
#define AppVersion "1.0.0"
#define AppPublisher "ChatList"
#define AppURL "https://github.com/rbait31/ChatList"
#define AppExeName "ChatList.exe"

[Setup]
; Информация о приложении
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=installer
OutputBaseFilename=ChatList-Setup-{#AppVersion}
SetupIconFile=app.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\ChatList-{#AppVersion}.exe"; DestDir: "{app}"; DestName: "{#AppExeName}"; Flags: ignoreversion
Source: "app.ico"; DestDir: "{app}"; Flags: ignoreversion
; Добавьте другие необходимые файлы здесь, если они есть

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\app.ico"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon; IconFilename: "{app}\app.ico"
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: quicklaunchicon; IconFilename: "{app}\app.ico"

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Файлы данных теперь хранятся в пользовательской папке %LOCALAPPDATA%\ChatList
; Удаление этих файлов выполняется через кастомный код ниже
Type: dirifempty; Name: "{app}"

[Code]
procedure InitializeUninstallProgressForm();
begin
  // Кастомная логика при деинсталляции, если нужно
end;

function GetUserDataDir: String;
var
  AppDataPath: String;
begin
  // Получаем путь к LOCALAPPDATA (пользовательская папка данных)
  AppDataPath := ExpandConstant('{localappdata}');
  Result := AppDataPath + '\ChatList';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserDataDir: String;
begin
  case CurUninstallStep of
    usUninstall:
      begin
        // Действия перед началом деинсталляции
        // Можно добавить проверки или подтверждения
      end;
    usPostUninstall:
      begin
        // Действия после завершения деинсталляции
        // Удаляем файлы данных из пользовательской папки
        UserDataDir := GetUserDataDir;
        if DirExists(UserDataDir) then
        begin
          // Удаляем файлы базы данных и логов
          DeleteFile(UserDataDir + '\chatlist.db');
          DeleteFile(UserDataDir + '\chatlist.log');
          DeleteFile(UserDataDir + '\.env');
          // Удаляем папку, если она пуста
          RemoveDir(UserDataDir);
        end;
      end;
  end;
end;

