@echo off
setlocal
cd /d "%~dp0"

rem Build folders outside of OneDrive
set "BUILD_ROOT=%LOCALAPPDATA%\ProjectDeskBuild"
set "DIST_DIR=%BUILD_ROOT%\dist\ProjectDesk"

echo.
echo [1/3] Installing Python packages
python -m pip install --upgrade -r requirements.txt
if errorlevel 1 goto error

echo.
echo [2/3] Building the program
python -m PyInstaller --noconfirm --clean --windowed --name ProjectDesk --icon "%~dp0projectdesk.ico" --add-data "%~dp0projectdesk.ico;." --workpath "%BUILD_ROOT%\build" --distpath "%BUILD_ROOT%\dist" --specpath "%BUILD_ROOT%" "%~dp0project_desk.py"
if errorlevel 1 goto error

echo.
echo [3/3] Building the installer
for /f "delims=" %%V in ('python -c "import project_desk; print(project_desk.APP_VERSION)"') do set "APP_VERSION=%%V"
if not defined APP_VERSION goto error
echo Version %APP_VERSION%
call :find_iscc
if defined ISCC goto compile

echo.
echo Inno Setup is not installed. The download page opens now.
echo Download and run "innosetup-x.x.x.exe" there.
echo Choose "Install for me only", then no administrator rights are needed.
echo Run build.bat again afterwards.
echo.
echo The program itself is already available at %DIST_DIR%\ProjectDesk.exe
start "" "https://jrsoftware.org/isdl.php"
goto end

:compile
"%ISCC%" "/DDistDir=%DIST_DIR%" "/DAppVersion=%APP_VERSION%" ProjectDesk.iss
if errorlevel 1 goto error
echo.
echo Done: the installer is in the folder "installer"
goto end

:find_iscc
set "ISCC="
for /f "delims=" %%P in ('where ISCC.exe 2^>nul') do set "ISCC=%%P"
for %%V in (6 7 8) do call :check_version %%V
call :check_folder "%ProgramFiles(x86)%"
call :check_folder "%ProgramFiles%"
call :check_folder "%LOCALAPPDATA%\Programs"
exit /b 0

:check_version
call :check_registry "HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup %~1_is1"
call :check_registry "HKLM\Software\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup %~1_is1"
call :check_registry "HKLM\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup %~1_is1"
exit /b 0

:check_folder
for /d %%D in ("%~1\Inno Setup*") do if exist "%%~D\ISCC.exe" set "ISCC=%%~D\ISCC.exe"
exit /b 0

:check_registry
for /f "tokens=2,*" %%A in ('reg query "%~1" /v InstallLocation 2^>nul ^| find "InstallLocation"') do if exist "%%B\ISCC.exe" set "ISCC=%%B\ISCC.exe"
exit /b 0

:error
echo.
echo The build failed, see the messages above.

:end
echo.
pause
