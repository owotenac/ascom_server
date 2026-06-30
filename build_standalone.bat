@echo off
setlocal

echo ========================================
echo  AstroApp Standalone Build
echo ========================================

REM Check if we're in the right directory
if not exist "server_ascom\main.py" (
    echo ERROR: Run this script from C:\Git\astro_app
    exit /b 1
)

set ROOT_DIR=%CD%

echo.
echo [1/3] Building Expo web client...
echo ----------------------------------------
cd "%ROOT_DIR%\client\astro_app"
call npx expo export --platform web --output-dir "%ROOT_DIR%\server_ascom\web_dist"
if errorlevel 1 (
    echo ERROR: Expo build failed
    exit /b 1
)

echo.
echo [2/3] Activating Python virtual environment...
echo ----------------------------------------
cd "%ROOT_DIR%\server_ascom"

REM Activate venv
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo WARNING: No .venv found, using system Python
)

REM Install PyInstaller if needed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo [3/3] Packaging with PyInstaller...
echo ----------------------------------------
pyinstaller --clean --onefile ^
    --name astro_app ^
    --add-data "web_dist;web_dist" ^
    --add-data ".env;." ^
    --hidden-import uvicorn.logging ^
    --hidden-import uvicorn.protocols.http ^
    --hidden-import uvicorn.protocols.http.auto ^
    --hidden-import uvicorn.protocols.websockets ^
    --hidden-import uvicorn.protocols.websockets.auto ^
    --hidden-import uvicorn.lifespan ^
    --hidden-import uvicorn.lifespan.on ^
    main.py

if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    exit /b 1
)

echo.
echo ========================================
echo  Build complete!
echo  Executable: %ROOT_DIR%\server_ascom\dist\astro_app.exe
echo ========================================
echo.
echo To run: cd server_ascom ^& dist\astro_app.exe
echo Then open: http://localhost:5001

cd "%ROOT_DIR%"
