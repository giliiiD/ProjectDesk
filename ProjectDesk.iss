#define AppName "ProjectDesk"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppExe "ProjectDesk.exe"
#ifndef DistDir
  #define DistDir "dist\ProjectDesk"
#endif

[Setup]
AppId={{D5C1F394-F96F-4775-A084-433911723958}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableDirPage=auto
PrivilegesRequired=lowest
UsedUserAreasWarning=no
OutputDir=installer
OutputBaseFilename=ProjectDesk_Setup
SetupIconFile=projectdesk.ico
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[InstallDelete]
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\ToDo.exe"
Type: files; Name: "{autoprograms}\ToDo.lnk"
Type: files; Name: "{autodesktop}\ToDo.lnk"

[Registry]
Root: HKA; Subkey: "Software\Classes\.pdesk"; ValueType: string; ValueName: ""; ValueData: "ProjectDesk.File"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\ProjectDesk.File"; ValueType: string; ValueName: ""; ValueData: "ProjectDesk Export"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\ProjectDesk.File\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#AppExe},0"
Root: HKA; Subkey: "Software\Classes\ProjectDesk.File\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
