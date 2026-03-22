#!/bin/bash
set -e
APP=/opt/tradeoracleai
echo "TradeOracle AI — AWS Deployment"

sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv python3-full git nginx ufw curl nano

sudo python3 -m venv $APP/venv
sudo $APP/venv/bin/pip install --upgrade pip
sudo $APP/venv/bin/pip install python-telegram-bot anthropic requests schedule python-dotenv

sudo mkdir -p $APP/config $APP/user_data $APP/logs
sudo chown -R ubuntu:ubuntu $APP

if [ ! -f "$APP/.env" ]; then
    touch $APP/.env
    chmod 600 $APP/.env
fi

sudo tee /etc/systemd/system/tradeoracleai.service > /dev/null << SERVICE
[Unit]
Description=TradeOracle AI Bot
After=network-online.target tradeoracleai-config.service
[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP
ExecStart=$APP/venv/bin/python3 $APP/bot/bot.py
Restart=always
RestartSec=10
EnvironmentFile=$APP/.env
StandardOutput=append:$APP/logs/bot.log
StandardError=append:$APP/logs/bot.error.log
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
SERVICE

sudo tee /etc/systemd/system/tradeoracleai-config.service > /dev/null << SERVICE
[Unit]
Description=TradeOracle AI Config Server
After=network.target
[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP
ExecStart=$APP/venv/bin/python3 $APP/bot/config_server.py
Restart=always
RestartSec=5
StandardOutput=append:$APP/logs/config.log
StandardError=append:$APP/logs/config.error.log
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
SERVICE

sudo tee /etc/nginx/sites-available/tradeoracleai > /dev/null << 'NGINX'
server {
    listen 80;
    server_name trade-oracle-ai.com www.trade-oracle-ai.com _;
    root /opt/tradeoracleai/website;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }
    location /api/ {
        proxy_pass http://127.0.0.1:8765;
        proxy_set_header X-Admin-Token $http_x_admin_token;
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, X-Admin-Token' always;
        if ($request_method = OPTIONS) { return 204; }
    }
    gzip on;
}
NGINX

sudo ln -sf /etc/nginx/sites-available/tradeoracleai /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

sudo systemctl daemon-reload
sudo systemctl enable tradeoracleai-config tradeoracleai
sudo systemctl start tradeoracleai-config
sleep 2

echo ""
echo "Set your admin portal password:"
read -s -p "Password (min 8 chars): " PW
echo ""
if [ ${#PW} -ge 8 ]; then
    curl -s -X POST http://localhost:8765/api/setup-password \
        -H "Content-Type: application/json" \
        -d "{\"password\":\"$PW\"}" > /dev/null
    echo "Password set!"
fi

IP=$(curl -s ifconfig.me)
echo ""
echo "DONE! Open: http://$IP/admin.html"
echo "Sign in → Bot Settings → Fill API keys → Save"
echo "Bot starts automatically after saving!"
