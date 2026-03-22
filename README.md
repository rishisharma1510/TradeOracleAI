# ⚡ TradeOracle AI
### Your Personal AI Trading Advisor on Telegram

![TradeOracle AI](https://img.shields.io/badge/TradeOracle-AI-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-green?style=for-the-badge)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge)
![Claude AI](https://img.shields.io/badge/Claude-AI-purple?style=for-the-badge)
![License](https://img.shields.io/badge/License-Private-red?style=for-the-badge)

---

## 🚀 What Is TradeOracle AI?

TradeOracle AI is a **multi-user SaaS Telegram trading bot** powered by Claude AI and real-time market data. It gives every user a personal AI trading advisor in their pocket — 24/7.

### Features
- 💰 **Income Strategies** — Wheel, Cash Secured Put, Covered Call, Put Credit Spread
- ⚡ **Day Trading** — Entry, stop loss, profit target, risk/reward
- 📈 **All 4 Options** — Buy call, buy put, sell call, sell put
- 🔄 **Swing Trading** — 2-5 day hold setups
- 📊 **Technical Analysis** — RSI, MACD, Bollinger Bands, Support/Resistance
- 🚨 **Emergency Alerts** — Vibrates phone even on silent
- 📧 **Email Alerts** — Position warnings sent to email
- 📸 **Screenshot Reading** — AI reads any Robinhood/Fidelity screenshot
- 💬 **Natural Chat** — Just talk to it like texting a friend
- 🔒 **Multi-User** — Each user's data completely private

---

## 📁 Repository Structure

```
TradeOracleAI/
├── bot/
│   └── bot.py              # Main multi-user Telegram bot
├── website/
│   └── index.html          # Landing page (host on GitHub Pages)
├── docs/
│   ├── AWS_SETUP.md        # Deploy to AWS free tier
│   └── USER_MANUAL.md      # Complete user guide
└── README.md               # This file
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Bot Framework | python-telegram-bot |
| AI Brain | Anthropic Claude 3.5 |
| Market Data | Yahoo Finance API (free) |
| Language | Python 3.10+ |
| Database | JSON files (per user) |
| Hosting | AWS EC2 Free Tier |
| Website | GitHub Pages (free) |

---

## 💼 Business Model

| Plan | Price | Duration |
|---|---|---|
| Free Trial | $0 | 15 days |
| Basic | $19/month | Monthly |
| Pro | $39/month | Monthly |
| Premium | $59/month | Monthly |
| Lifetime | $299 | Forever |

**Revenue potential at 200 users: ~$7,800/month**

---

## ⚙️ Setup Instructions

### 1. Clone The Repository
```bash
git clone https://github.com/rishisharma1510/TradeOracleAI.git
cd TradeOracleAI
```

### 2. Install Dependencies
```bash
pip install python-telegram-bot anthropic requests schedule
```

### 3. Configure Credentials
Edit `bot/bot.py` and fill in:
```python
TELEGRAM_TOKEN = "your_telegram_bot_token"
ANTHROPIC_KEY  = "your_anthropic_api_key"
ADMIN_CHAT_ID  = "your_telegram_chat_id"
GMAIL_SENDER   = "your_gmail@gmail.com"
GMAIL_PASSWORD = "your_gmail_app_password"
```

### 4. Run The Bot
```bash
python bot/bot.py
```

### 5. Deploy To AWS (Production)
See [docs/AWS_SETUP.md](docs/AWS_SETUP.md) for complete free tier deployment.

---

## 🌐 Website / Landing Page

The landing page is in `website/index.html`.

### Host FREE on GitHub Pages:
```
1. Go to your repo Settings
2. Click Pages (left menu)
3. Source: Deploy from branch
4. Branch: main / website folder
5. Save
6. Your site: rishisharma1510.github.io/TradeOracleAI
```

---

## 📱 Admin Commands

Only accessible by the admin (your Telegram ID):

| Command | Description |
|---|---|
| `/admin` | Dashboard with revenue stats |
| `/adduser pro 30` | Create Pro access code (30 days) |
| `/users` | List all users and activity |
| `/revoke USER_ID` | Cancel user access |
| `/broadcast MESSAGE` | Send message to all users |

---

## 👤 User Commands

| Command | Plan | Description |
|---|---|---|
| `/start` | All | Main menu |
| `/activate CODE` | All | Activate subscription |
| `/ask NVDA` | All | Full income strategy |
| `/signal NVDA` | All | Technical analysis |
| `/wheel NVDA` | Basic+ | Wheel strategy setup |
| `/daytrade NVDA` | Pro+ | Day trade setup |
| `/options NVDA` | Pro+ | All 4 options directions |
| `/swing NVDA` | Pro+ | Swing trade setup |
| `/scan` | All | Scan all stocks |
| `/momentum` | All | Top momentum stocks |
| `/positions` | All | Your open positions |
| `/briefing` | All | Daily market summary |
| `/profile` | All | Update your profile |

---

## 🔒 Security & Privacy

- Each user's data stored in separate files: `user_data/CHAT_ID/`
- No user can see another user's data
- API keys stored as environment variables in production
- Access controlled via unique codes you generate
- All data encrypted at rest on AWS

---

## 📊 Watchlist

Default stocks monitored:
`NVDA, AAPL, MSFT, GOOGL, NFLX, AMZN, META, TSLA`

---

## 📞 Support

- Email: rishisharma1510@gmail.com
- Telegram: @TradeOracleAIBot

---

## ⚠️ Disclaimer

Trading involves risk. Past performance does not guarantee future results. This software is for educational purposes only and does not constitute financial advice. Always do your own research before making trading decisions.

---

## 📄 License

Private — All rights reserved © 2026 TradeOracle AI
