[Setup]
AppName=Tantra Automatic
AppVersion=1.0
AppPublisher=HylianSoft
DefaultDirName={autopf}\TantraAutomatic
DefaultGroupName=Tantra Automatic
OutputDir=C:\Users\jaud_\Documents\tantra\output
OutputBaseFilename=TantraAutomatic_Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=
UninstallDisplayName=Tantra Automatic

[Files]
Source: "C:\Users\jaud_\Documents\tantra\installer\TantraAutomatic.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\jaud_\Documents\tantra\installer\tesseract\*"; DestDir: "{app}\tesseract"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Tantra Automatic"; Filename: "{app}\TantraAutomatic.exe"
Name: "{commondesktop}\Tantra Automatic"; Filename: "{app}\TantraAutomatic.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\TantraAutomatic.exe"; Description: "Ejecutar Tantra Automatic"; Flags: nowait postinstall skipifsilent
