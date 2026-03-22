# AWS DEPLOYMENT GUIDE
## TradeOracle AI — trade-oracle-ai.com
## Complete step-by-step from zero to live

---

## OVERVIEW

```
What we're building:
┌─────────────────────────────────────────┐
│           AWS EC2 Server                │
│                                         │
│  ┌─────────────┐   ┌─────────────────┐  │
│  │  Python Bot  │   │  Nginx Website  │  │
│  │  (Telegram)  │   │  (trade-oracle  │  │
│  │  port: bg    │   │  -ai.com)       │  │
│  └─────────────┘   └─────────────────┘  │
│                                         │
│  ┌─────────────────────────────────────┐│
│  │  user_data/ (all user files)        ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
         ↕                    ↕
   Telegram API          trade-oracle-ai.com
```

---

## PART 1 — CREATE AWS ACCOUNT (5 minutes)

```
1. Go to aws.amazon.com
2. Click "Create a Free Account"
3. Enter email + password
4. Account type: Personal
5. Add credit card (won't be charged for free tier)
6. Choose "Basic Support (Free)"
7. Verify phone number
8. Log into AWS Console
```

**FREE for 12 months:**
- EC2 t2.micro — 750 hours/month ✅
- 30GB storage ✅
- Enough for 200+ users ✅

---

## PART 2 — LAUNCH SERVER (10 minutes)

### Step 1 — Go to EC2
```
AWS Console → Search "EC2" → Click it
→ Click "Launch Instance" (orange button)
```

### Step 2 — Configure Instance
```
Name: TradeOracleAI

OS: Ubuntu Server 22.04 LTS
    (Select "Free tier eligible")

Instance type: t2.micro
    (Shows "Free tier eligible")

Key pair:
    → Click "Create new key pair"
    → Name: tradeoracleai-key
    → Type: RSA
    → Format: .pem
    → Click "Create key pair"
    → FILE DOWNLOADS AUTOMATICALLY
    → SAVE THIS FILE SOMEWHERE SAFE!
    → You need it to connect to server

Network settings:
    → Create security group
    → Allow SSH from: My IP
    → Allow HTTP: ✅ (port 80)
    → Allow HTTPS: ✅ (port 443)

Storage: 20 GB (free tier allows 30GB)

→ Click "Launch Instance"
→ Wait 60 seconds
→ Click "View Instances"
→ Copy your PUBLIC IP ADDRESS (e.g. 54.123.456.789)
```

---

## PART 3 — CONNECT TO SERVER (5 minutes)

### On Windows — Using AWS Browser Console (Easiest!)
```
1. Go to EC2 → Instances
2. Click your instance checkbox
3. Click "Connect" button at top
4. Click "Connect" again
5. Browser terminal opens!
6. You're in! Skip to Part 4.
```

### On Windows — Using PuTTY
```
1. Download PuTTY: putty.org
2. Download PuTTYgen: putty.org

Convert .pem to .ppk:
1. Open PuTTYgen
2. Load → select your .pem file
3. Save private key → save as tradeoracleai.ppk

Connect with PuTTY:
1. Open PuTTY
2. Host: ubuntu@YOUR_SERVER_IP
3. Port: 22
4. SSH → Auth → Credentials
5. Browse to your .ppk file
6. Click Open
```

### On Mac/Linux
```bash
chmod 400 tradeoracleai-key.pem
ssh -i tradeoracleai-key.pem ubuntu@YOUR_SERVER_IP
```

---

## PART 4 — DEPLOY THE BOT (10 minutes)

Once connected to your server, run these commands:

### Step 1 — Download and run setup script
```bash
# Download setup script from your GitHub repo
curl -o setup.sh https://raw.githubusercontent.com/rishisharma1510/TradeOracleAI/main/deploy/setup.sh

# Make it executable
chmod +x setup.sh

# Run it (takes 3-5 minutes)
sudo bash setup.sh
```

This automatically:
- Updates the server
- Installs Python + all packages
- Clones your GitHub repo
- Sets up systemd service (auto-restart)
- Configures Nginx web server
- Sets up firewall
- Configures log rotation

### Step 2 — Fill in your credentials
```bash
nano /opt/tradeoracleai/.env
```

Fill in each value:
```
TELEGRAM_TOKEN=8342430923:AAG8iZ0ZV-...
ADMIN_CHAT_ID=7853695195
ANTHROPIC_KEY=sk-ant-api03-...
GMAIL_SENDER=rishisharma1510@gmail.com
GMAIL_PASSWORD=your_16_digit_app_password
SCAN_INTERVAL=15
BRIEFING_TIME=08:00
WATCHLIST=NVDA,AAPL,MSFT,GOOGL,NFLX,AMZN,META,TSLA
```

Save: Ctrl+X → Y → Enter

### Step 3 — Start the bot
```bash
sudo systemctl start tradeoracleai
```

### Step 4 — Verify it's running
```bash
sudo systemctl status tradeoracleai
```

Should show: **Active: active (running)**

### Step 5 — Watch live logs
```bash
tail -f /var/log/tradeoracleai/bot.log
```

Should show:
```
TradeOracle AI — Multi-User SaaS Edition
✅ All settings loaded from environment
Scanner running every 15 min
Bot is LIVE!
```

---

## PART 5 — CONNECT YOUR DOMAIN (10 minutes)

### Step 1 — Get your server IP
```bash
curl ifconfig.me
# Shows something like: 54.123.456.789
```

### Step 2 — Update DNS at your registrar
Go to wherever you bought trade-oracle-ai.com:

```
Add these DNS records:

Type: A
Name: @  (or leave blank)
Value: YOUR_SERVER_IP
TTL: 300

Type: A  
Name: www
Value: YOUR_SERVER_IP
TTL: 300
```

Wait 5-30 minutes for DNS to propagate.

### Step 3 — Test DNS is working
```bash
ping trade-oracle-ai.com
# Should show your server IP
```

### Step 4 — Get free SSL certificate
```bash
sudo bash /opt/tradeoracleai/deploy/ssl_setup.sh
```

Your site is now live at **https://trade-oracle-ai.com** ✅

---

## PART 6 — VERIFY EVERYTHING WORKS

### Test the website
```
Open browser → https://trade-oracle-ai.com
Should show landing page ✅
```

### Test admin panel
```
https://trade-oracle-ai.com/admin.html
Sign in with rishisharma1510@gmail.com ✅
```

### Test the bot
```
Open Telegram → @TradeOracleAIBot
Send /start
Should respond with menu ✅
```

---

## PART 7 — DAILY MANAGEMENT

Use the manage script for everything:

```bash
# Check status
bash /opt/tradeoracleai/deploy/manage.sh status

# View live logs
bash /opt/tradeoracleai/deploy/manage.sh logs

# Restart bot
bash /opt/tradeoracleai/deploy/manage.sh restart

# Update from GitHub
bash /opt/tradeoracleai/deploy/manage.sh update

# View users
bash /opt/tradeoracleai/deploy/manage.sh users

# Backup data
bash /opt/tradeoracleai/deploy/manage.sh backup
```

---

## PART 8 — UPDATE BOT CODE

When you make changes to bot.py:

```bash
# On your computer, push to GitHub:
git add .
git commit -m "Update bot"
git push

# On AWS server, pull and restart:
bash /opt/tradeoracleai/deploy/manage.sh update
```

---

## TROUBLESHOOTING

### Bot not starting
```bash
# Check errors
cat /var/log/tradeoracleai/bot.error.log

# Common fix: check .env file
cat /opt/tradeoracleai/.env
```

### Website not loading
```bash
# Check nginx
sudo nginx -t
sudo systemctl status nginx

# Check firewall
sudo ufw status
```

### Bot crashes and restarts
```bash
# systemd auto-restarts it — check why it crashed
journalctl -u tradeoracleai -n 50
```

### SSL certificate issues
```bash
# Renew manually
sudo certbot renew
sudo systemctl restart nginx
```

---

## COSTS

```
Year 1 (AWS free tier):    $0/month
Year 2+ (after free tier): $8-12/month

Your revenue at 50 users:  $1,950/month
Your revenue at 200 users: $7,800/month
Your costs:                ~$12-50/month
NET PROFIT at 200 users:   ~$7,750/month
```

---

## ARCHITECTURE SUMMARY

```
trade-oracle-ai.com (DNS)
        ↓
AWS EC2 t2.micro (Ubuntu 22.04)
        ↓
Nginx (port 80/443)
  ├── /          → website/index.html
  └── /admin     → website/admin.html

Python Bot (systemd service)
  ├── Telegram polling (background)
  ├── Signal scanner (every 15 min)
  ├── Position monitor (every 5 min)
  └── Morning briefing (8 AM daily)

user_data/
  ├── users.json          (all users)
  ├── access_codes.json   (codes)
  └── {chat_id}/
      ├── positions.json  (per user)
      └── profile.json    (per user)
```
