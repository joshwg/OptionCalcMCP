@echo off
echo ================================================
echo   Option Calculator - MCP Server Deployment
echo ================================================
echo.

echo Step 1: Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
echo ✓ Python found
echo.

echo Step 2: Creating virtual environment in mcp-server...
cd mcp-server
if exist venv (
    echo Virtual environment already exists
) else (
    python -m venv venv
    echo ✓ Virtual environment created
)
echo.

echo Step 3: Activating virtual environment...
call venv\Scripts\activate
echo ✓ Virtual environment activated
echo.

echo Step 4: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo Step 5: Testing MCP server locally...
echo Starting server test (will timeout after 5 seconds)...
timeout /t 5 /nobreak >nul
python server.py
echo.

echo ================================================
echo   Local Setup Complete!
echo ================================================
echo.
echo To deploy to Railway:
echo 1. Create a Railway account at https://railway.app
echo 2. Install Railway CLI: npm i -g @railway/cli
echo 3. Run: railway login
echo 4. Run: railway init
echo 5. Run: railway up
echo.
echo Or deploy via GitHub:
echo 1. Push this code to GitHub
echo 2. Connect your GitHub repo to Railway
echo 3. Railway will auto-detect and deploy
echo.
pause
