[Setup]
AppName=MazeAgent
AppVersion=1.0
AppPublisher=CSI457 - Inteligencia Artificial
DefaultDirName={autopf}\MazeSolver
DefaultGroupName=MazeSolver
OutputDir=dist
OutputBaseFilename=MazeSolver_Setup
SetupIconFile=maze.ico
UninstallDisplayIcon={app}\_internal\maze.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na Area de Trabalho"; GroupDescription: "Atalhos adicionais:"

[Files]
Source: "dist\MazeSolver\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\MazeAgent"; Filename: "{app}\MazeSolver.exe"; IconFilename: "{app}\_internal\maze.ico"
Name: "{group}\Desinstalar MazeSolver"; Filename: "{uninstallexe}"
Name: "{autodesktop}\MazeAgent"; Filename: "{app}\MazeSolver.exe"; IconFilename: "{app}\_internal\maze.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\MazeSolver.exe"; Description: "Abrir o MazeAgent"; Flags: nowait postinstall skipifsilent
