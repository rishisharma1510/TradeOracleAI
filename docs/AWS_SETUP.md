# AWS FREE TIER SETUP GUIDE
## AI Trading Bot — Production Deployment
## FREE for 12 months!

---

## WHAT YOU GET FREE FOR 1 YEAR
```
EC2 t2.micro instance:
- 1 vCPU, 1GB RAM
- 750 hours/month FREE
- Enough for 200+ users
- Linux server 24/7

Also free:
- 5GB S3 storage (backups)
- 15GB data transfer
- Route 53 DNS
```

---

## STEP 1 — CREATE AWS ACCOUNT

```
1. Go to aws.amazon.com
2. Click "Create Free Account"
3. Enter email + password
4. Account type: Personal
5. Add credit card (won't be charged)
6. Select FREE support plan
7. Wait for verification email
8. Login to AWS Console
```

---

## STEP 2 — LAUNCH YOUR SERVER

```
1. Go to AWS Console
2. Search "EC2" → click it
3. Click "Launch Instance"
4. Name: "trading-bot"

5. Choose OS:
   → Ubuntu Server 22.04 LTS
   → Architecture: 64-bit x86

6. Instance type:
   → t2.micro (FREE TIER)

7. Key pair (login):
   → Click "Create new key pair"
   → Name: trading-bot-key
   → Type: RSA
   → Format: .pem
   → Download the .pem file!
     SAVE THIS — you need it to login!

8. Network settings:
   → Allow SSH from: My IP
   → Allow HTTPS: Yes
   → Allow HTTP: Yes

9. Storage: 8GB (free tier)

10. Click "Launch Instance"
11. Wait 2 minutes
12. Copy the Public IP address
```

---

## STEP 3 — CONNECT TO YOUR SERVER

### On Windows:
```
Option A — Use AWS Console (easiest):
1. Go to EC2 → Instances
2. Select your instance
3. Click "Connect"
4. Click "Connect" again
5. Browser opens terminal!

Option B — PuTTY:
1. Download PuTTY from putty.org
2. Convert .pem to .ppk:
   - Download PuTTYgen
   - Load your .pem file
   - Save as .ppk
3. Open PuTTY
4. Host: ubuntu@YOUR_IP
5. SSH → Auth → browse to .ppk
6. Click Open
```

### On Mac/Linux:
```bash
chmod 400 trading-bot-key.pem
ssh -i trading-bot-key.pem ubuntu@YOUR_SERVER_IP
```

---

## STEP 4 — SETUP SERVER

Run these commands one by one:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and tools
sudo apt install python3 python3-pip git screen -y

# Install bot packages
pip3 install python-telegram-bot anthropic requests schedule

# Create bot folder
mkdir -p /home/ubuntu/trading_bot/user_data
cd /home/ubuntu/trading_bot

# Test Python works
python3 --version
```

---

## STEP 5 — UPLOAD BOT FILE

### Option A — Direct paste:
```bash
nano /home/ubuntu/trading_bot/bot.py
# Paste your entire bot code
# Ctrl+X → Y → Enter to save
```

### Option B — SFTP (Windows):
```
1. Download WinSCP from winscp.net
2. New Connection:
   Protocol: SFTP
   Host: YOUR_SERVER_IP
   Username: ubuntu
   Private key: your .ppk file
3. Connect
4. Drag bot_multiuser.py to server
```

### Option C — From GitHub (best):
```bash
# First push code to GitHub (private repo)
# Then on server:
git clone https://github.com/YOU/trading-bot.git
cd trading-bot
```

---

## STEP 6 — SET ENVIRONMENT VARIABLES

Never put API keys directly in code for production!

```bash
# Create environment file
sudo nano /etc/environment

# Add these lines:
TELEGRAM_TOKEN="8342430923:AAG8iZ0ZV-ww94qrw4-c0nzPRD840AxyzZI"
ANTHROPIC_KEY="sk-ant-api03-..."
ADMIN_CHAT_ID="7853695195"
GMAIL_SENDER="rishisharma1510@gmail.com"
GMAIL_PASSWORD="your_app_password"

# Save and reload
source /etc/environment
```

---

## STEP 7 — RUN AS SERVICE (NEVER DIES!)

```bash
# Create systemd service
sudo nano /etc/systemd/system/tradingbot.service
```

Paste this:
```ini
[Unit]
Description=AI Trading Bot
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/trading_bot
ExecStart=/usr/bin/python3 /home/ubuntu/trading_bot/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable tradingbot
sudo systemctl start tradingbot

# Check status
sudo systemctl status tradingbot

# Watch live logs
sudo journalctl -u tradingbot -f
```

---

## STEP 8 — AUTO BACKUP TO S3

```bash
# Install AWS CLI
sudo apt install awscli -y

# Create S3 bucket in AWS Console
# Name it: trading-bot-backups-yourname

# Create backup script
cat > /home/ubuntu/backup.sh << 'BACKUP'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M)
tar -czf /tmp/backup_$DATE.tar.gz /home/ubuntu/trading_bot/user_data/
aws s3 cp /tmp/backup_$DATE.tar.gz s3://trading-bot-backups-yourname/
rm /tmp/backup_$DATE.tar.gz
echo "Backup complete: $DATE"
BACKUP

chmod +x /home/ubuntu/backup.sh

# Auto-run daily at 3 AM
(crontab -l 2>/dev/null; echo "0 3 * * * /home/ubuntu/backup.sh") | crontab -
```

---

## STEP 9 — SECURITY HARDENING

```bash
# Firewall rules
sudo ufw allow 22      # SSH
sudo ufw allow 80      # HTTP (website)
sudo ufw allow 443     # HTTPS (website)
sudo ufw enable

# Fail2ban (blocks brute force)
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Auto security updates
sudo apt install unattended-upgrades -y
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## STEP 10 — DOMAIN NAME (OPTIONAL)

For professional look: yourbot.com

```
1. Buy domain at namecheap.com (~$10/year)
2. In AWS Route 53:
   → Create hosted zone
   → Add A record pointing to server IP
3. Install SSL certificate (free):
   sudo apt install certbot -y
   sudo certbot certonly --standalone -d yourdomain.com
```

---

## MONITORING YOUR SERVER

```bash
# Check server resources
htop

# Check disk space
df -h

# Check bot status
sudo systemctl status tradingbot

# Restart bot
sudo systemctl restart tradingbot

# View last 100 log lines
sudo journalctl -u tradingbot -n 100
```

---

## AWS FREE TIER LIMITS

```
What's FREE for 12 months:
✅ 750 hours EC2 t2.micro/month
✅ 30GB EBS storage
✅ 5GB S3 storage
✅ 15GB data transfer out
✅ 1 million Lambda requests

After 12 months:
t2.micro = ~$8.50/month
Still very affordable!
```

---

## ESTIMATED COSTS

```
Year 1:  $0/month (AWS free tier)
Year 2+: $8-12/month (EC2 + S3)

Your revenue at 200 users: $7,800/month
Your costs: $10-50/month
Net profit: $7,750+/month
```

