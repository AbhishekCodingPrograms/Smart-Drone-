#!/bin/bash
# Quick Deployment Script for Smart Farming Drones

echo "🚀 Smart Farming Drones - Deployment Script"
echo "==========================================="
echo ""

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit - Smart Farming Drones"
fi

# Ask for deployment platform
echo "Choose deployment platform:"
echo "1) Heroku"
echo "2) Railway  
echo "3) Render"
echo "4) Skip (manual deployment)"
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo ""
        echo "🚂 Deploying to Heroku..."
        echo ""
        
        # Check if Heroku CLI is installed
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI not found. Please install it first:"
            echo "   https://devcenter.heroku.com/articles/heroku-cli"
            exit 1
        fi
        
        # Login to Heroku
        echo "🔐 Logging into Heroku..."
        heroku login
        
        # Create app
        read -p "Enter app name (or press Enter for random): " appname
        if [ -z "$appname" ]; then
            heroku create
        else
            heroku create "$appname"
        fi
        
        # Set environment variables
        echo "⚙️  Setting environment variables..."
        heroku config:set FLASK_ENV=production
        heroku config:set DEBUG=false
        heroku config:set ENABLE_MOCK_DATA=true
        
        # Generate secret key
        SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
        heroku config:set SECRET_KEY="$SECRET_KEY"
        
        # Deploy
        echo "🚀 Deploying to Heroku..."
        git push heroku main || git push heroku master:main
        
        # Scale dynos
        heroku ps:scale web=1
        
        # Open app
        echo "✅ Deployment complete!"
        heroku open
        ;;
        
    2)
        echo ""
        echo "🛤️  Railway Deployment"
        echo ""
        echo "📝 Steps:"
        echo "1. Push code to GitHub"
        echo "2. Go to https://railway.app"
        echo "3. Click 'New Project'"
        echo "4. Select 'Deploy from GitHub repo'"
        echo "5. Choose your repository"
        echo "6. Railway will auto-deploy!"
        echo ""
        read -p "Press Enter to open Railway dashboard..." dummy
        python -m webbrowser https://railway.app
        ;;
        
    3)
        echo ""
        echo "🎨 Render Deployment"
        echo ""
        echo "📝 Steps:"
        echo "1. Push code to GitHub"
        echo "2. Go to https://render.com"
        echo "3. Click 'New +' → 'Web Service'"
        echo "4. Connect your GitHub repository"
        echo "5. Configure:"
        echo "   - Build: pip install -r requirements.txt"
        echo "   - Start: gunicorn dashboard.app:app --bind 0.0.0.0:\$PORT"
        echo "6. Click 'Create Web Service'"
        echo ""
        read -p "Press Enter to open Render dashboard..." dummy
        python -m webbrowser https://render.com
        ;;
        
    4)
        echo ""
        echo "📖 Manual Deployment"
        echo ""
        echo "See DEPLOYMENT_GUIDE.md for detailed instructions"
        echo ""
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "✅ Deployment process initiated!"
echo "📚 For detailed instructions, see DEPLOYMENT_GUIDE.md"
echo ""
