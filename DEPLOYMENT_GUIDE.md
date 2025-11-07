# 🚀 Smart Farming Drones - Complete Deployment Guide

## 📋 Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Testing](#local-testing)
3. [Deploy to Heroku](#deploy-to-heroku)
4. [Deploy to Railway](#deploy-to-railway)
5. [Deploy to Render](#deploy-to-render)
6. [Deploy to PythonAnywhere](#deploy-to-pythonanywhere)
7. [Deploy to Google Cloud](#deploy-to-google-cloud)
8. [Custom Server Deployment](#custom-server-deployment)
9. [Domain Configuration](#domain-configuration)
10. [Post-Deployment](#post-deployment)

---

## ✅ Pre-Deployment Checklist

### 1. **Files Required**
```
✓ requirements.txt (dependencies)
✓ Procfile (process configuration)
✓ runtime.txt (Python version)
✓ .env.example (environment template)
✓ .gitignore (ignore sensitive files)
✓ dashboard/app.py (main application)
✓ All templates and static files
```

### 2. **Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
# Set SECRET_KEY, DEBUG=false, FLASK_ENV=production
```

### 3. **Test Locally First**
```bash
# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test with gunicorn (production server)
gunicorn dashboard.app:app --bind 0.0.0.0:5000

# Open browser: http://localhost:5000
```

---

## 🧪 Local Testing

### Test All Features:
```bash
# 1. Start server
python dashboard/app.py

# 2. Test pages
http://localhost:5000/              # Home
http://localhost:5000/dashboard_enhanced  # Dashboard
http://localhost:5000/api/crop_status    # API

# 3. Test responsiveness
- Desktop (1920px)
- Tablet (768px)
- Mobile (375px)

# 4. Test camera (if available)
- Click "Start Camera"
- Capture image
- Verify analysis

# 5. Test database
python -c "from database.db_manager import db; print(db.get_dashboard_stats())"
```

---

## 🚂 Deploy to Heroku

### Prerequisites:
```bash
# Install Heroku CLI
# Windows: https://devcenter.heroku.com/articles/heroku-cli
# Or use: winget install Heroku.HerokuCLI

# Login
heroku login
```

### Deployment Steps:

**1. Create Heroku App**
```bash
cd "c:\SMART AI POWERED FORMING"

# Create new app
heroku create smart-farming-drones

# Or with custom name
heroku create your-app-name
```

**2. Configure Environment Variables**
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
heroku config:set DEBUG=false
heroku config:set ENABLE_MOCK_DATA=true
```

**3. Initialize Git (if not already)**
```bash
git init
git add .
git commit -m "Initial deployment"
```

**4. Deploy**
```bash
# Add Heroku remote
heroku git:remote -a smart-farming-drones

# Deploy
git push heroku main

# Or if main branch
git push heroku master:main
```

**5. Scale Dynos**
```bash
# Start web dyno
heroku ps:scale web=1

# Open app
heroku open
```

**6. View Logs**
```bash
heroku logs --tail
```

### Heroku Database Setup:
```bash
# If using PostgreSQL (recommended for production)
heroku addons:create heroku-postgresql:hobby-dev

# Get database URL
heroku config:get DATABASE_URL
```

---

## 🛤️ Deploy to Railway

### Steps:

**1. Create Account**
- Visit: https://railway.app
- Sign up with GitHub

**2. Deploy from GitHub**
```
1. Push code to GitHub
2. Go to Railway dashboard
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway auto-detects Python
```

**3. Configure**
```
Settings → Environment Variables:
- FLASK_ENV=production
- SECRET_KEY=your-secret-key
- PORT=5000
```

**4. Deploy**
```
- Railway auto-deploys on git push
- Get URL from dashboard
- Access: https://your-app.railway.app
```

---

## 🎨 Deploy to Render

### Steps:

**1. Create Account**
- Visit: https://render.com
- Sign up

**2. Create Web Service**
```
1. Click "New +"
2. Select "Web Service"
3. Connect GitHub repository
4. Configure:
   - Name: smart-farming-drones
   - Environment: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn dashboard.app:app --bind 0.0.0.0:$PORT
```

**3. Environment Variables**
```
FLASK_ENV=production
SECRET_KEY=your-secret-key
PYTHON_VERSION=3.10.12
```

**4. Deploy**
```
- Render auto-deploys
- Access: https://smart-farming-drones.onrender.com
```

---

## 🐍 Deploy to PythonAnywhere

### Steps:

**1. Create Account**
- Visit: https://www.pythonanywhere.com
- Sign up (Free tier available)

**2. Upload Code**
```bash
# Option A: Git
git clone https://github.com/your-username/smart-farming-drones.git

# Option B: Upload files manually
# Use Files tab in PythonAnywhere
```

**3. Create Virtual Environment**
```bash
# In PythonAnywhere console
mkvirtualenv --python=/usr/bin/python3.10 farming-env
pip install -r requirements.txt
```

**4. Configure Web App**
```
Web tab → Add a new web app:
- Select: Flask
- Python version: 3.10
- Path: /home/yourusername/smart-farming-drones
- WSGI file: Edit to point to dashboard.app:app
```

**5. WSGI Configuration**
```python
import sys
import os

path = '/home/yourusername/smart-farming-drones'
if path not in sys.path:
    sys.path.append(path)

from dashboard.app import app as application
```

**6. Static Files**
```
Static files mapping:
URL: /static
Directory: /home/yourusername/smart-farming-drones/dashboard/static
```

**7. Reload**
```
- Click "Reload" button
- Access: https://yourusername.pythonanywhere.com
```

---

## ☁️ Deploy to Google Cloud Platform

### Prerequisites:
```bash
# Install Google Cloud SDK
# Visit: https://cloud.google.com/sdk/docs/install
```

### Steps:

**1. Create Project**
```bash
gcloud projects create smart-farming-drones
gcloud config set project smart-farming-drones
```

**2. Create app.yaml**
```yaml
runtime: python310

instance_class: F2

env_variables:
  FLASK_ENV: 'production'
  SECRET_KEY: 'your-secret-key'

handlers:
- url: /static
  static_dir: dashboard/static

- url: /.*
  script: auto
```

**3. Deploy**
```bash
gcloud app deploy

# View
gcloud app browse
```

---

## 🖥️ Custom Server Deployment (VPS/Linux)

### For Ubuntu/Debian Server:

**1. Install Dependencies**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3.10 python3-pip nginx git -y

# Install supervisor (process manager)
sudo apt install supervisor -y
```

**2. Clone Project**
```bash
cd /var/www
sudo git clone https://github.com/your-repo/smart-farming-drones.git
cd smart-farming-drones

# Setup virtual environment
sudo python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**3. Configure Gunicorn**
```bash
# Create gunicorn config
sudo nano /etc/supervisor/conf.d/smart-farming.conf
```

**gunicorn config:**
```ini
[program:smart-farming]
directory=/var/www/smart-farming-drones
command=/var/www/smart-farming-drones/venv/bin/gunicorn dashboard.app:app --bind 127.0.0.1:8000 --workers 4
autostart=true
autorestart=true
stderr_logfile=/var/log/smart-farming/gunicorn.err.log
stdout_logfile=/var/log/smart-farming/gunicorn.out.log
```

**4. Configure Nginx**
```bash
sudo nano /etc/nginx/sites-available/smart-farming
```

**nginx config:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /var/www/smart-farming-drones/dashboard/static;
    }
}
```

**5. Enable & Start**
```bash
# Create log directory
sudo mkdir -p /var/log/smart-farming

# Enable site
sudo ln -s /etc/nginx/sites-available/smart-farming /etc/nginx/sites-enabled/

# Test nginx
sudo nginx -t

# Restart services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start smart-farming
sudo systemctl restart nginx
```

**6. SSL Certificate (Optional but Recommended)**
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com
```

---

## 🌐 Domain Configuration

### Point Domain to Your App:

**For Heroku:**
```bash
# Add custom domain
heroku domains:add www.your-domain.com

# Get DNS target
heroku domains

# Update DNS:
# CNAME record: www → your-app.herokuapp.com
```

**For Railway/Render:**
```
1. Go to settings
2. Add custom domain
3. Update DNS with provided CNAME
```

**DNS Records:**
```
Type: CNAME
Name: www
Value: your-app.platform.com
TTL: 3600
```

---

## 🎯 Post-Deployment Checklist

### 1. **Test Everything**
```
✓ Home page loads
✓ All navigation links work
✓ Dashboard displays data
✓ API endpoints respond
✓ Mobile responsive
✓ Camera works (if enabled)
✓ Real-time updates working
✓ Database operations successful
```

### 2. **Monitor**
```bash
# Heroku
heroku logs --tail

# Railway
railway logs

# Custom server
sudo tail -f /var/log/smart-farming/gunicorn.out.log
```

### 3. **Performance**
```
- Load testing
- Response time check
- Database optimization
- CDN for static files (optional)
```

### 4. **Security**
```
✓ HTTPS enabled
✓ Environment variables secure
✓ DEBUG=false
✓ CORS configured
✓ Rate limiting (optional)
✓ Firewall rules
```

### 5. **Backup**
```
✓ Database backup strategy
✓ Code versioning (Git)
✓ Environment config backup
✓ User data backup plan
```

---

## 🔧 Troubleshooting

### Common Issues:

**1. App Won't Start**
```bash
# Check logs
heroku logs --tail

# Common fixes:
- Verify requirements.txt
- Check Procfile syntax
- Verify Python version in runtime.txt
- Check environment variables
```

**2. Database Errors**
```bash
# Initialize database
python -c "from database.db_manager import db; db.ensure_database_exists()"
```

**3. Static Files Not Loading**
```bash
# Check static file configuration
# Verify paths in nginx/apache config
# Run: python dashboard/app.py (check console for errors)
```

**4. Memory Issues**
```bash
# Upgrade dyno/instance
heroku ps:resize web=standard-1x

# Optimize code:
- Reduce model size
- Implement caching
- Lazy loading
```

---

## 📊 Performance Optimization

### Production Tips:

**1. Enable Caching**
```python
from flask_caching import Cache
cache = Cache(app, config={'CACHE_TYPE': 'simple'})
```

**2. Compress Responses**
```python
from flask_compress import Compress
Compress(app)
```

**3. CDN for Static Files**
```
- Use Cloudflare
- Or AWS CloudFront
- Or Azure CDN
```

**4. Database Optimization**
```python
# Add indexes
# Use connection pooling
# Implement query caching
```

---

## 🎉 Deployment Complete!

### Your App is Live! 🚀

**URLs:**
- Heroku: `https://smart-farming-drones.herokuapp.com`
- Railway: `https://smart-farming-drones.railway.app`
- Render: `https://smart-farming-drones.onrender.com`
- Custom: `https://your-domain.com`

### Share:
```
✓ Dashboard: https://your-app.com/dashboard_enhanced
✓ API Docs: https://your-app.com/api/crop_status
✓ GitHub: https://github.com/your-username/smart-farming-drones
```

---

## 📞 Support & Resources

### Deployment Support:
- **Heroku Docs**: https://devcenter.heroku.com/
- **Railway Docs**: https://docs.railway.app/
- **Render Docs**: https://render.com/docs
- **PythonAnywhere**: https://help.pythonanywhere.com/

### Need Help?
```
1. Check logs
2. Review documentation
3. Search Stack Overflow
4. GitHub Issues
```

---

**🎊 Congratulations! Your Smart Farming Drones app is deployed! 🌾🚁**

---

**Made with ❤️ for Modern Agriculture**
