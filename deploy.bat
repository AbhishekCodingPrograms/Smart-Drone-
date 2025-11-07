@echo off
REM Quick Deployment Script for Smart Farming Drones (Windows)

echo ========================================
echo 🚀 Smart Farming Drones - Deployment
echo ========================================
echo.

REM Check if git is initialized
if not exist ".git" (
    echo 📦 Initializing Git repository...
    git init
    git add .
    git commit -m "Initial commit - Smart Farming Drones"
    echo.
)

echo Choose deployment platform:
echo 1) Heroku
echo 2) Railway
echo 3) Render
echo 4) View Deployment Guide
echo 5) Cancel
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto heroku
if "%choice%"=="2" goto railway
if "%choice%"=="3" goto render
if "%choice%"=="4" goto guide
if "%choice%"=="5" goto end

:heroku
echo.
echo 🚂 Deploying to Heroku...
echo.

REM Check if Heroku CLI is installed
where heroku >nul 2>nul
if errorlevel 1 (
    echo ❌ Heroku CLI not found!
    echo.
    echo Please install Heroku CLI:
    echo https://devcenter.heroku.com/articles/heroku-cli
    echo.
    echo Or use: winget install Heroku.HerokuCLI
    pause
    goto end
)

echo 🔐 Logging into Heroku...
call heroku login

set /p appname="Enter app name (or press Enter for random): "

if "%appname%"=="" (
    call heroku create
) else (
    call heroku create %appname%
)

echo.
echo ⚙️  Setting environment variables...
call heroku config:set FLASK_ENV=production
call heroku config:set DEBUG=false
call heroku config:set ENABLE_MOCK_DATA=true

REM Generate secret key
for /f %%i in ('python -c "import secrets; print(secrets.token_hex(32))"') do set SECRET_KEY=%%i
call heroku config:set SECRET_KEY=%SECRET_KEY%

echo.
echo 🚀 Deploying to Heroku...
git push heroku main
if errorlevel 1 (
    git push heroku master:main
)

echo.
echo 📊 Scaling dynos...
call heroku ps:scale web=1

echo.
echo ✅ Deployment complete!
call heroku open

goto end

:railway
echo.
echo 🛤️  Railway Deployment
echo.
echo 📝 Follow these steps:
echo 1. Push your code to GitHub
echo 2. Visit https://railway.app
echo 3. Click "New Project"
echo 4. Select "Deploy from GitHub repo"
echo 5. Choose your repository
echo 6. Railway will auto-deploy!
echo.
echo Opening Railway in browser...
start https://railway.app
goto end

:render
echo.
echo 🎨 Render Deployment
echo.
echo 📝 Follow these steps:
echo 1. Push your code to GitHub
echo 2. Visit https://render.com
echo 3. Click "New +" then "Web Service"
echo 4. Connect your GitHub repository
echo 5. Configure:
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: gunicorn dashboard.app:app --bind 0.0.0.0:$PORT
echo 6. Click "Create Web Service"
echo.
echo Opening Render in browser...
start https://render.com
goto end

:guide
echo.
echo 📖 Opening Deployment Guide...
if exist "DEPLOYMENT_GUIDE.md" (
    start DEPLOYMENT_GUIDE.md
) else (
    echo DEPLOYMENT_GUIDE.md not found in current directory
)
goto end

:end
echo.
echo ========================================
echo 📚 For detailed instructions:
echo    See DEPLOYMENT_GUIDE.md
echo ========================================
echo.
pause
