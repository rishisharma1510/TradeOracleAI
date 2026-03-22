"""
AI Trading Bot — Multi-User SaaS Edition
==========================================
- Each user has completely private data
- Access code system (you control who joins)
- Subscription tiers: Basic / Pro / Premium
- Admin panel for you to manage users
- All data stored separately per user

SETUP:
1. Fill in your credentials below
2. Run: python bot_multiuser.py
3. Share your bot link with customers
4. Give them access codes
5. Collect monthly payments

ADMIN COMMANDS (only work for you):
/admin          - admin dashboard
/adduser CODE   - create new access code
/users          - list all users
/revoke USER_ID - revoke user access
/broadcast MSG  - send message to all users
"""

import json, os, asyncio, logging, threading, time, base64, math, requests, re
import smtplib, hashlib, secrets
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters)
import schedule

# ══════════════════════════════════════
# ALL SETTINGS LOADED FROM ENVIRONMENT
# Set these in your .env file or server
# NEVER hardcode credentials in code!
# ══════════════════════════════════════
import os
from dotenv import load_dotenv
load_dotenv()  # loads .env file if present

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_KEY", "")
ADMIN_CHAT_ID  = os.environ.get("ADMIN_CHAT_ID", "")
GMAIL_SENDER   = os.environ.get("GMAIL_SENDER", "")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD", "")

# Bot behavior settings (can be overridden via .env)
SCAN_MINS      = int(os.environ.get("SCAN_INTERVAL", "15"))
BRIEFING       = os.environ.get("BRIEFING_TIME", "08:00")
WATCHLIST_STR  = os.environ.get("WATCHLIST", "NVDA,AAPL,MSFT,GOOGL,NFLX,AMZN,META,TSLA")
MIN_PROFIT     = float(os.environ.get("MIN_PROFIT_ALERT", "7"))
WARN_BUFFER    = float(os.environ.get("WARN_BUFFER", "12"))
DANGER_BUFFER  = float(os.environ.get("DANGER_BUFFER", "5"))
EMERG_BUFFER   = float(os.environ.get("EMERGENCY_BUFFER", "3"))

# Validate required settings on startup
def validate_settings():
    missing = []
    if not TELEGRAM_TOKEN: missing.append("TELEGRAM_TOKEN")
    if not ANTHROPIC_KEY:  missing.append("ANTHROPIC_KEY")
    if not ADMIN_CHAT_ID:  missing.append("ADMIN_CHAT_ID")
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Create a .env file with these values or set them on your server.")
        print("Download .env template from Admin Panel → Bot Settings → Download .env")
        exit(1)
    print(f"✅ All settings loaded from environment")
    print(f"✅ Admin: {ADMIN_CHAT_ID}")
    print(f"✅ Watchlist: {WATCHLIST_STR}")

# ══════════════════════════════════════
# SUBSCRIPTION TIERS
# ══════════════════════════════════════
TIERS = {
    "basic": {
        "name": "Basic",
        "price": 19,
        "commands": ["start","signal","scan","momentum","briefing","positions",
                     "alerts","history","profile","ask"],
        "description": "Signals, scanning, daily briefing, income strategies"
    },
    "pro": {
        "name": "Pro",
        "price": 39,
        "commands": ["start","signal","scan","momentum","briefing","positions",
                     "alerts","history","profile","ask","wheel","daytrade",
                     "options","swing","predictions","setemail","setpassword","testalert"],
        "description": "Everything + Day trading, options analysis, email alerts"
    },
    "premium": {
        "name": "Premium",
        "price": 59,
        "commands": "all",
        "description": "Everything + Unlimited chat, priority support, custom watchlist"
    },
    "trial": {
        "name": "Free Trial",
        "price": 0,
        "commands": ["start","signal","scan","briefing","ask","momentum"],
        "description": "15-day trial — basic features"
    }
}

# ══════════════════════════════════════
# DATA DIRECTORY SETUP
# ══════════════════════════════════════
DATA_DIR = "user_data"
os.makedirs(DATA_DIR, exist_ok=True)

WATCHLIST = os.environ.get("WATCHLIST","NVDA,AAPL,MSFT,GOOGL,NFLX,AMZN,META,TSLA").split(",")
SCAN_MINS = 15

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)
claude  = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ══════════════════════════════════════
# USER MANAGEMENT
# ══════════════════════════════════════
def get_users_db():
    path = os.path.join(DATA_DIR, "users.json")
    if os.path.exists(path):
        try:
            with open(path) as f: return json.load(f)
        except: pass
    return {}

def save_users_db(data):
    path = os.path.join(DATA_DIR, "users.json")
    with open(path, "w") as f: json.dump(data, f, indent=2, default=str)

def get_access_codes():
    path = os.path.join(DATA_DIR, "access_codes.json")
    if os.path.exists(path):
        try:
            with open(path) as f: return json.load(f)
        except: pass
    return {}

def save_access_codes(data):
    path = os.path.join(DATA_DIR, "access_codes.json")
    with open(path, "w") as f: json.dump(data, f, indent=2, default=str)

def create_access_code(tier="pro", days=30):
    code = secrets.token_hex(4).upper()  # e.g. "A3F7B2C1"
    codes = get_access_codes()
    codes[code] = {
        "tier": tier,
        "days": days,
        "created": datetime.now().isoformat(),
        "used": False,
        "used_by": None
    }
    save_access_codes(codes)
    return code

def get_user(chat_id):
    users = get_users_db()
    return users.get(str(chat_id))

def create_user(chat_id, username, tier="trial", days=15):
    users = get_users_db()
    uid = str(chat_id)
    users[uid] = {
        "chat_id": uid,
        "username": username,
        "tier": tier,
        "joined": datetime.now().isoformat(),
        "expires": (datetime.now() + timedelta(days=days)).isoformat(),
        "active": True,
        "message_count": 0,
        "last_active": datetime.now().isoformat()
    }
    save_users_db(users)
    # Create user data directories
    os.makedirs(get_user_dir(uid), exist_ok=True)
    return users[uid]

def update_user(chat_id, updates):
    users = get_users_db()
    uid = str(chat_id)
    if uid in users:
        users[uid].update(updates)
        save_users_db(users)

def is_admin(chat_id):
    return str(chat_id) == str(ADMIN_CHAT_ID)

def is_active(chat_id):
    user = get_user(chat_id)
    if not user: return False
    if not user.get("active"): return False
    # Check expiry
    try:
        expires = datetime.fromisoformat(user["expires"])
        if datetime.now() > expires: return False
    except: pass
    return True

def has_access(chat_id, command):
    if is_admin(chat_id): return True
    user = get_user(chat_id)
    if not user or not is_active(chat_id): return False
    tier = user.get("tier","trial")
    tier_data = TIERS.get(tier, TIERS["trial"])
    allowed = tier_data.get("commands","")
    if allowed == "all": return True
    return command in allowed

def days_remaining(chat_id):
    user = get_user(chat_id)
    if not user: return 0
    try:
        expires = datetime.fromisoformat(user["expires"])
        days = (expires - datetime.now()).days
        return max(0, days)
    except: return 0

# ══════════════════════════════════════
# USER DATA — each user has private files
# ══════════════════════════════════════
def get_user_dir(chat_id):
    return os.path.join(DATA_DIR, str(chat_id))

def load_user_memory(chat_id):
    path = os.path.join(get_user_dir(chat_id), "positions.json")
    if os.path.exists(path):
        try:
            with open(path) as f: return json.load(f)
        except: pass
    return {"positions": {}, "closed": []}

def save_user_memory(chat_id, data):
    os.makedirs(get_user_dir(chat_id), exist_ok=True)
    path = os.path.join(get_user_dir(chat_id), "positions.json")
    with open(path, "w") as f: json.dump(data, f, indent=2, default=str)

def load_user_profile(chat_id):
    path = os.path.join(get_user_dir(chat_id), "profile.json")
    if os.path.exists(path):
        try:
            with open(path) as f: return json.load(f)
        except: pass
    return {"completed": False, "account_size": None, "brokers": [],
            "experience_level": None, "risk_tolerance": None,
            "monthly_income_goal": None, "check_frequency": None,
            "stocks_owned": {}}

def save_user_profile(chat_id, profile):
    os.makedirs(get_user_dir(chat_id), exist_ok=True)
    path = os.path.join(get_user_dir(chat_id), "profile.json")
    with open(path, "w") as f: json.dump(profile, f, indent=2, default=str)

# ══════════════════════════════════════
# STOCK DATA
# ══════════════════════════════════════
def get_prices(ticker, days=60):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        r   = requests.get(url,
                params={"interval":"1d","range":f"{days}d"},
                headers={"User-Agent":"Mozilla/5.0"}, timeout=10)
        d   = r.json()["chart"]["result"][0]
        q   = d["indicators"]["quote"][0]
        closes  = [float(x) for x in q["close"]  if x is not None]
        volumes = [float(x) for x in q["volume"] if x is not None]
        highs   = [float(x) for x in q["high"]   if x is not None]
        lows    = [float(x) for x in q["low"]    if x is not None]
        opens   = [float(x) for x in q["open"]   if x is not None]
        meta    = d.get("meta",{})
        return {"price":round(closes[-1],2),"closes":closes,"volumes":volumes,
                "highs":highs,"lows":lows,"opens":opens,
                "chg1d":round(((closes[-1]-closes[-2])/closes[-2])*100,2) if len(closes)>1 else 0,
                "chg5d":round(((closes[-1]-closes[-6])/closes[-6])*100,2) if len(closes)>5 else 0,
                "high52":round(float(meta.get("fiftyTwoWeekHigh",closes[-1])),2),
                "low52":round(float(meta.get("fiftyTwoWeekLow",closes[-1])),2)}
    except Exception as e:
        logger.error(f"Price {ticker}: {e}"); return {}

def get_live_price(ticker):
    try: return get_prices(ticker,5).get("price",0)
    except: return 0

def get_spy_vix():
    try: return get_live_price("SPY"), get_live_price("^VIX")
    except: return 0, 20

def calc_rsi(c,p=14):
    if len(c)<p+1: return 50.0
    g=[max(c[i]-c[i-1],0) for i in range(1,len(c))]
    l=[max(c[i-1]-c[i],0) for i in range(1,len(c))]
    ag=sum(g[-p:])/p; al=sum(l[-p:])/p
    return round(100-(100/(1+ag/al)),1) if al else 100.0

def calc_macd(c):
    if len(c)<26: return {"macd":0,"signal":0,"hist":0,"cross":"none"}
    def ema(data,p):
        k=2/(p+1); e=data[0]
        for x in data[1:]: e=x*k+e*(1-k)
        return e
    ema12=ema(c[-26:],12); ema26=ema(c[-26:],26)
    ml=round(ema12-ema26,3); sig=round(ema(c[-9:],9),3) if len(c)>=9 else ml
    hist=round(ml-sig,3)
    cross="bullish" if hist>0 else "bearish" if hist<0 else "none"
    return {"macd":ml,"signal":sig,"hist":hist,"cross":cross}

def calc_bb(c,p=20):
    if len(c)<p: v=c[-1] if c else 0; return {"u":v,"l":v,"m":v,"pct":50}
    r=c[-p:]; m=sum(r)/p; s=math.sqrt(sum((x-m)**2 for x in r)/p)
    u=round(m+2*s,2); l=round(m-2*s,2)
    pct=round((c[-1]-l)/(u-l)*100,1) if u!=l else 50
    return {"u":u,"l":l,"m":round(m,2),"pct":pct}

def calc_sma(c,p):
    return round(sum(c[-p:])/p,2) if len(c)>=p else (c[-1] if c else 0)

def calc_iv(c):
    if len(c)<20: return 30.0
    ret=[abs((c[i]-c[i-1])/c[i-1]) for i in range(1,len(c))]
    return round(sum(ret[-20:])/20*math.sqrt(252)*100,1)

def calc_atr(highs,lows,closes,p=14):
    if len(closes)<p+1: return 0
    trs=[max(highs[i]-lows[i],abs(highs[i]-closes[i-1]),abs(lows[i]-closes[i-1]))
         for i in range(1,len(closes))]
    return round(sum(trs[-p:])/p,2)

def find_sr(closes,highs,lows):
    if len(closes)<20: return closes[-1]*0.95, closes[-1]*1.05
    sup=round(sum(sorted(lows[-20:])[:3])/3,2)
    res=round(sum(sorted(highs[-20:])[-3:])/3,2)
    return sup, res

def detect_pattern(opens,closes,highs,lows):
    if len(closes)<3: return "No pattern"
    o,c,h,l=opens[-1],closes[-1],highs[-1],lows[-1]
    po,pc=opens[-2],closes[-2]; body=abs(c-o); candle=h-l
    if candle>0 and body/candle<0.1: return "Doji"
    if c>o and (o-l)>body*2 and (h-c)<body*0.5: return "Hammer — bullish"
    if c<o and (h-o)>body*2 and (c-l)<body*0.5: return "Shooting Star — bearish"
    if pc<po and c>o and c>po and o<pc: return "Bullish Engulfing"
    if pc>po and c<o and c<po and o>pc: return "Bearish Engulfing"
    if c>o and body/candle>0.7: return "Strong Bullish"
    if c<o and body/candle>0.7: return "Strong Bearish"
    return "No pattern"

def analyze(ticker):
    d=get_prices(ticker,60)
    if not d or len(d.get("closes",[]))<20:
        return {"ticker":ticker,"signal":"ERROR","score":0,"price":0,
                "rsi":50,"chg1d":0,"chg5d":0,"vol":1,"iv":30,
                "exp_move":0,"high52":0,"low52":0,
                "macd":{"cross":"none"},"bb":{"pct":50},"atr":0,
                "support":0,"resistance":0,"pattern":"Unknown"}
    c=d["closes"]; price=d["price"]
    r=calc_rsi(c); macd=calc_macd(c); bb=calc_bb(c)
    s20=calc_sma(c,20); s50=calc_sma(c,50)
    iv=calc_iv(c); em=round(price*(iv/100)*math.sqrt(30/365),2)
    atr=calc_atr(d["highs"],d["lows"],c)
    sup,res=find_sr(c,d["highs"],d["lows"])
    pat=detect_pattern(d["opens"],c,d["highs"],d["lows"])
    vr=round(d["volumes"][-1]/max(sum(d["volumes"][-20:])/20,1),2)
    score=0
    if r<30: score+=3
    elif r<40: score+=1
    elif r>70: score-=3
    elif r>60: score-=1
    if price<bb["l"]: score+=2
    elif price>bb["u"]: score-=2
    if price>s20 and price>s50: score+=1
    elif price<s20 and price<s50: score-=1
    if macd["cross"]=="bullish": score+=2
    elif macd["cross"]=="bearish": score-=2
    if vr>2: score*=1.3
    score=round(score,1)
    if score>=6: sig="STRONG BUY"
    elif score>=3: sig="BUY"
    elif score<=-6: sig="STRONG SELL"
    elif score<=-3: sig="SELL"
    else: sig="NEUTRAL"
    return {"ticker":ticker,"signal":sig,"score":score,"price":price,
            "rsi":r,"macd":macd,"bb":bb,"sma20":s20,"sma50":s50,
            "chg1d":d["chg1d"],"chg5d":d["chg5d"],"vol":vr,
            "iv":iv,"exp_move":em,"atr":atr,"support":sup,
            "resistance":res,"pattern":pat,
            "high52":d.get("high52",0),"low52":d.get("low52",0)}

# ══════════════════════════════════════
# AI
# ══════════════════════════════════════
def build_user_context(chat_id):
    profile = load_user_profile(chat_id)
    memory  = load_user_memory(chat_id)
    user    = get_user(chat_id)
    ctx = f"USER PROFILE:\n"
    if profile.get("account_size"):      ctx+=f"- Account: ${profile['account_size']:,}\n"
    if profile.get("brokers"):           ctx+=f"- Brokers: {', '.join(profile['brokers'])}\n"
    if profile.get("experience_level"):  ctx+=f"- Experience: {profile['experience_level']}\n"
    if profile.get("risk_tolerance"):    ctx+=f"- Risk: {profile['risk_tolerance']}\n"
    if profile.get("monthly_income_goal"): ctx+=f"- Goal: ${profile['monthly_income_goal']}/month\n"
    positions = memory.get("positions",{})
    if positions:
        ctx+=f"OPEN POSITIONS:\n"
        for ticker,pos in positions.items():
            t=pos.get("type","")
            if t=="put_credit_spread":
                ctx+=f"- {ticker}: Spread ${pos.get('short_strike')}/${pos.get('long_strike')} exp {pos.get('expiry')}\n"
            elif t=="covered_call":
                ctx+=f"- {ticker}: Covered Call ${pos.get('call_strike')} cost ${pos.get('avg_cost')}\n"
            elif t=="stock":
                ctx+=f"- {ticker}: {pos.get('shares')} shares @ ${pos.get('avg_cost')}\n"
    return ctx

def build_market_ctx(tickers=[]):
    ctx=""
    try:
        spy,vix=get_spy_vix()
        mood="HIGH FEAR" if vix>25 else "ELEVATED" if vix>18 else "CALM"
        ctx+=f"\nLIVE MARKET DATA:\nSPY:${round(spy,2)} VIX:{round(vix,1)} {mood}\n"
        for t in tickers[:5]:
            try:
                s=analyze(t)
                if s.get("price",0)>0:
                    ctx+=(f"{t}:${s['price']} {'+' if s['chg1d']>=0 else ''}{s['chg1d']}% "
                          f"RSI:{s['rsi']} MACD:{s['macd']['cross']} IV:{s['iv']}%\n")
            except: pass
    except: pass
    return ctx

async def ask_claude_for_user(prompt, chat_id, max_tokens=600):
    try:
        user_ctx = build_user_context(chat_id)
        system = f"""You are a personal AI trading advisor.
You have real-time market data — use it. NEVER say you lack real-time data.

STRATEGIES: Wheel, Cash Secured Put, Covered Call, Put Credit Spread, Day Trade, Swing Trade, All Options.
For income traders: ONLY recommend premium selling strategies unless asked otherwise.
For day trades: give exact entry, stop loss, target. Max risk $250-500.
Always give SPECIFIC numbers: strikes, expiry, premiums.
Keep under 300 words. End with ONE action to take now.

{user_ctx}"""
        r=claude.messages.create(model="claude-sonnet-4-20250514",max_tokens=max_tokens,
            system=system,messages=[{"role":"user","content":prompt}])
        return r.content[0].text
    except Exception as e: return f"AI error: {e}"

# ══════════════════════════════════════
# ACCESS GATE — checks every command
# ══════════════════════════════════════
async def check_access(update, context, command):
    chat_id = str(update.effective_chat.id)

    # Admin always has access
    if is_admin(chat_id): return True

    # Check if user exists
    user = get_user(chat_id)
    if not user:
        await update.effective_message.reply_text(
            "Welcome to AI Trading Bot!\n\n"
            "To get started, enter your access code:\n"
            "/activate YOUR_CODE\n\n"
            "Don't have a code? Contact the admin to get one.")
        return False

    # Check if active
    if not is_active(chat_id):
        days = days_remaining(chat_id)
        await update.effective_message.reply_text(
            f"Your subscription has expired!\n\n"
            f"Contact admin to renew your access.\n"
            f"Your data is safe and will be restored when you renew.")
        return False

    # Check tier access
    if not has_access(chat_id, command):
        user_tier = user.get("tier","trial")
        await update.effective_message.reply_text(
            f"This feature requires a higher plan.\n\n"
            f"Your plan: {user_tier.upper()}\n"
            f"Required: PRO or PREMIUM\n\n"
            f"Upgrade to access:\n"
            f"- Day trading setups\n"
            f"- Options analysis\n"
            f"- Swing trading\n"
            f"- Email alerts\n\n"
            f"Contact admin to upgrade!")
        return False

    # Update last active
    update_user(chat_id, {
        "last_active": datetime.now().isoformat(),
        "message_count": (user.get("message_count",0) or 0) + 1
    })
    return True

# ══════════════════════════════════════
# USER ONBOARDING
# ══════════════════════════════════════
async def cmd_start(update, context):
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)

    if is_admin(chat_id):
        await show_admin_start(update, context)
        return

    if not user:
        await update.message.reply_text(
            "Welcome to AI Trading Bot!\n\n"
            "Your personal AI advisor for:\n"
            "- Options income (Wheel, Spreads)\n"
            "- Day trading signals\n"
            "- Swing trading\n"
            "- Technical analysis\n"
            "- Emergency alerts\n\n"
            "To get started:\n"
            "/activate YOUR_CODE\n\n"
            "Don't have a code? Contact admin.")
        return

    if not is_active(chat_id):
        await update.message.reply_text(
            "Your subscription has expired.\n"
            "Contact admin to renew.")
        return

    tier = user.get("tier","trial")
    days = days_remaining(chat_id)
    tier_info = TIERS.get(tier, TIERS["trial"])
    profile = load_user_profile(chat_id)
    memory  = load_user_memory(chat_id)
    n = len(memory.get("positions",{}))

    kbd = [[InlineKeyboardButton("My Positions",   callback_data="positions")],
           [InlineKeyboardButton("Scan Signals",   callback_data="scan")],
           [InlineKeyboardButton("Top Momentum",   callback_data="momentum")],
           [InlineKeyboardButton("Daily Briefing", callback_data="briefing")],
           [InlineKeyboardButton("My Profile",     callback_data="profile_view")]]

    plan_txt = f"{tier_info['name']} Plan"
    if days <= 7: plan_txt += f" ⚠️ {days} days left"

    await update.message.reply_text(
        f"AI TRADING BOT\n"
        f"Plan: {plan_txt}\n\n"
        f"Positions: {n} | Watching: {len(WATCHLIST)}\n\n"
        f"INCOME:\n"
        f"/ask NVDA — income strategy\n"
        f"/wheel NVDA — wheel setup\n\n"
        f"TRADING:\n"
        f"/signal NVDA — technical signals\n"
        f"/daytrade NVDA — day trade setup\n"
        f"/options NVDA — all 4 options\n"
        f"/swing NVDA — swing trade\n\n"
        f"SCAN:\n"
        f"/scan — all stocks\n"
        f"/momentum — top movers\n\n"
        f"Just chat naturally too!\n"
        f"Send screenshot to save trades!",
        reply_markup=InlineKeyboardMarkup(kbd))

async def cmd_activate(update, context):
    """User enters access code to activate account"""
    chat_id  = str(update.effective_chat.id)
    username = update.effective_user.username or update.effective_user.first_name or "User"
    args = context.args

    if not args:
        await update.message.reply_text(
            "Enter your access code:\n/activate YOUR_CODE\n\n"
            "Example: /activate A3F7B2C1")
        return

    code = args[0].upper().strip()
    codes = get_access_codes()

    if code not in codes:
        await update.message.reply_text(
            "Invalid access code.\n"
            "Please check and try again.\n"
            "Contact admin if you need a new code.")
        return

    code_data = codes[code]
    if code_data.get("used"):
        await update.message.reply_text(
            "This code has already been used.\n"
            "Contact admin for a new code.")
        return

    # Activate user
    tier = code_data.get("tier","pro")
    days = code_data.get("days",30)
    user = get_user(chat_id)

    if user:
        # Renewing existing user
        new_expiry = datetime.now() + timedelta(days=days)
        update_user(chat_id, {
            "tier": tier,
            "expires": new_expiry.isoformat(),
            "active": True
        })
        msg = f"Subscription renewed!\n\nPlan: {TIERS[tier]['name']}\nActive for: {days} days"
    else:
        # New user
        create_user(chat_id, username, tier, days)
        msg = (f"Welcome {username}!\n\n"
               f"Plan: {TIERS[tier]['name']}\n"
               f"Active for: {days} days\n\n"
               f"Features: {TIERS[tier]['description']}\n\n"
               f"Let's set up your profile!\nType /start to begin")

    # Mark code as used
    codes[code]["used"] = True
    codes[code]["used_by"] = chat_id
    codes[code]["used_at"] = datetime.now().isoformat()
    save_access_codes(codes)

    # Notify admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"NEW USER ACTIVATED!\n"
                 f"User: {username} ({chat_id})\n"
                 f"Plan: {tier} for {days} days\n"
                 f"Code used: {code}")
    except: pass

    await update.message.reply_text(msg)

# ══════════════════════════════════════
# ADMIN COMMANDS
# ══════════════════════════════════════
async def show_admin_start(update, context):
    users = get_users_db()
    active = sum(1 for u in users.values() if is_active(u["chat_id"]))
    codes  = get_access_codes()
    unused = sum(1 for c in codes.values() if not c.get("used"))

    kbd = [[InlineKeyboardButton("All Users",       callback_data="admin_users")],
           [InlineKeyboardButton("Create Code",     callback_data="admin_create_code")],
           [InlineKeyboardButton("Unused Codes",    callback_data="admin_codes")],
           [InlineKeyboardButton("Broadcast",       callback_data="admin_broadcast")],
           [InlineKeyboardButton("Revenue Stats",   callback_data="admin_revenue")]]

    await update.message.reply_text(
        f"ADMIN DASHBOARD\n"
        f"{'='*25}\n\n"
        f"Total users: {len(users)}\n"
        f"Active users: {active}\n"
        f"Unused codes: {unused}\n\n"
        f"Monthly Revenue Estimate:\n"
        f"{sum(TIERS.get(u.get('tier','trial'),{}).get('price',0) for u in users.values() if is_active(u['chat_id']))} USD\n\n"
        f"Commands:\n"
        f"/adduser pro 30 — create Pro code (30 days)\n"
        f"/adduser basic 30 — create Basic code\n"
        f"/adduser premium 30 — create Premium code\n"
        f"/users — list all users\n"
        f"/revoke USER_ID — revoke access\n"
        f"/broadcast MESSAGE — message all users",
        reply_markup=InlineKeyboardMarkup(kbd))

async def cmd_admin(update, context):
    if not is_admin(update.effective_chat.id):
        await update.message.reply_text("Not authorized.")
        return
    await show_admin_start(update, context)

async def cmd_adduser(update, context):
    """Create new access code: /adduser pro 30"""
    if not is_admin(update.effective_chat.id):
        return
    args = context.args
    tier = args[0].lower() if args else "pro"
    days = int(args[1]) if len(args)>1 else 30

    if tier not in TIERS:
        await update.message.reply_text(f"Invalid tier. Use: basic, pro, premium, trial")
        return

    code = create_access_code(tier, days)
    price = TIERS[tier]["price"]

    await update.message.reply_text(
        f"NEW ACCESS CODE CREATED\n\n"
        f"Code: {code}\n"
        f"Plan: {TIERS[tier]['name']} (${price}/month)\n"
        f"Valid for: {days} days\n\n"
        f"Send this to your customer:\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome to AI Trading Bot!\n\n"
        f"Your access code: {code}\n\n"
        f"To activate:\n"
        f"1. Open Telegram\n"
        f"2. Search @{(await context.bot.get_me()).username}\n"
        f"3. Send: /activate {code}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━")

async def cmd_users(update, context):
    """List all users"""
    if not is_admin(update.effective_chat.id):
        return
    users = get_users_db()
    if not users:
        await update.message.reply_text("No users yet.")
        return

    text = f"ALL USERS ({len(users)})\n{'='*25}\n\n"
    for uid, u in users.items():
        active = "✅" if is_active(uid) else "❌"
        days = days_remaining(uid)
        tier = u.get("tier","trial")
        name = u.get("username","?")
        msgs = u.get("message_count",0)
        text += f"{active} {name} ({uid})\n"
        text += f"   Plan:{tier} Days left:{days} Msgs:{msgs}\n\n"

    await update.message.reply_text(text[:4000])

async def cmd_revoke(update, context):
    """Revoke user access: /revoke USER_ID"""
    if not is_admin(update.effective_chat.id):
        return
    args = context.args
    if not args:
        await update.message.reply_text("/revoke USER_ID")
        return
    uid = args[0]
    update_user(uid, {"active": False})
    await update.message.reply_text(f"Access revoked for user {uid}")
    try:
        await context.bot.send_message(
            chat_id=uid,
            text="Your access has been revoked. Contact admin for details.")
    except: pass

async def cmd_broadcast(update, context):
    """Send message to all active users: /broadcast MESSAGE"""
    if not is_admin(update.effective_chat.id):
        return
    if not context.args:
        await update.message.reply_text("/broadcast YOUR MESSAGE HERE")
        return
    msg = " ".join(context.args)
    users = get_users_db()
    sent = 0; failed = 0
    for uid in users:
        if is_active(uid):
            try:
                await context.bot.send_message(chat_id=uid, text=f"📢 ANNOUNCEMENT\n\n{msg}")
                sent += 1
            except: failed += 1
    await update.message.reply_text(f"Broadcast sent!\nSuccess: {sent}\nFailed: {failed}")

# ══════════════════════════════════════
# TRADING COMMANDS (user-aware)
# ══════════════════════════════════════
async def cmd_signal(update, context):
    if not await check_access(update, context, "signal"): return
    chat_id = str(update.effective_chat.id)
    args = context.args
    if not args:
        await update.message.reply_text("/signal NVDA\n/signal AAPL"); return
    ticker = args[0].upper()
    msg = await update.message.reply_text(f"Analyzing {ticker}...")
    try:
        s = analyze(ticker)
        if s.get("signal")=="ERROR":
            await msg.edit_text(f"Cannot find {ticker}."); return
        user_ctx = build_user_context(chat_id)
        spy,vix = get_spy_vix()
        ai = await ask_claude_for_user(
            f"LIVE: {ticker} ${s['price']} RSI:{s['rsi']} MACD:{s['macd']['cross']} "
            f"BB:{s['bb']['pct']}% IV:{s['iv']}% ATR:{s['atr']} "
            f"Support:{s['support']} Resist:{s['resistance']} "
            f"Pattern:{s['pattern']} Signal:{s['signal']}\n"
            f"VIX:{round(vix,1)}\n\n"
            f"Give trading signal in 150 words:\n"
            f"1. TREND: up/down/sideways\n"
            f"2. BEST TRADE: exact entry, stop, target\n"
            f"3. OPTIONS: best options trade\n"
            f"4. RISK: main risk", chat_id)
        e="+" if s["chg1d"]>=0 else ""
        header=(f"SIGNALS: {ticker}\n${s['price']} ({e}{s['chg1d']}%)\n"
                f"RSI:{s['rsi']} MACD:{s['macd']['cross'].upper()}\n"
                f"BB:{s['bb']['pct']}% IV:{s['iv']}%\n"
                f"Support:${s['support']} Resist:${s['resistance']}\n"
                f"Pattern:{s['pattern']}\n"
                f"Score:{s['score']:+.1f}/10\n{'='*25}\n\n")
        kbd=[[InlineKeyboardButton("Day Trade",callback_data=f"daytrade_{ticker}"),
              InlineKeyboardButton("Options",callback_data=f"options_{ticker}")],
             [InlineKeyboardButton("Swing",callback_data=f"swing_{ticker}"),
              InlineKeyboardButton("Refresh",callback_data=f"signal_{ticker}")]]
        await msg.edit_text((header+ai)[:4000],reply_markup=InlineKeyboardMarkup(kbd))
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

async def cmd_daytrade(update, context):
    if not await check_access(update, context, "daytrade"): return
    chat_id = str(update.effective_chat.id)
    q = getattr(update,"callback_query",None)
    args = context.args
    ticker=(args[0].upper() if args else (q.data.split("_",1)[1] if q and "_" in q.data else ""))
    if not ticker:
        await (q.message if q else update.message).reply_text("/daytrade NVDA"); return
    if q: msg=await q.message.edit_text(f"Day trade for {ticker}...")
    else: msg=await update.message.reply_text(f"Day trade for {ticker}...")
    try:
        s=analyze(ticker); spy,vix=get_spy_vix()
        ai=await ask_claude_for_user(
            f"LIVE: {ticker} ${s['price']} RSI:{s['rsi']} MACD:{s['macd']['cross']} "
            f"IV:{s['iv']}% ATR:{s['atr']} Support:{s['support']} Resist:{s['resistance']} "
            f"Pattern:{s['pattern']} VIX:{round(vix,1)}\n\n"
            f"Day trade setup (selective trader, 1-2 best trades only):\n"
            f"SIGNAL: X/10 — TRADE or SKIP?\n"
            f"Direction: LONG/SHORT\n"
            f"Entry: $__ Stop: $__ (max loss $__)\n"
            f"Target 1: $__ Target 2: $__\n"
            f"Risk/Reward: 1:__\n"
            f"OPTIONS: Buy __ $__ exp __ cost $__\n"
            f"WHY/RISK in one sentence each.", chat_id)
        e="+" if s["chg1d"]>=0 else ""
        header=f"DAY TRADE: {ticker}\n${s['price']} ({e}{s['chg1d']}%)\n{'='*25}\n\n"
        kbd=[[InlineKeyboardButton("Signals",callback_data=f"signal_{ticker}"),
              InlineKeyboardButton("Options",callback_data=f"options_{ticker}")]]
        await msg.edit_text((header+ai)[:4000],reply_markup=InlineKeyboardMarkup(kbd))
    except Exception as e: await msg.edit_text(f"Error: {e}")

async def cmd_options(update, context):
    if not await check_access(update, context, "options"): return
    chat_id = str(update.effective_chat.id)
    q=getattr(update,"callback_query",None)
    args=context.args
    ticker=(args[0].upper() if args else (q.data.split("_",1)[1] if q and "_" in q.data else ""))
    if not ticker:
        await (q.message if q else update.message).reply_text("/options NVDA"); return
    if q: msg=await q.message.edit_text(f"Options for {ticker}...")
    else: msg=await update.message.reply_text(f"Options for {ticker}...")
    try:
        s=analyze(ticker); spy,vix=get_spy_vix()
        ai=await ask_claude_for_user(
            f"LIVE: {ticker} ${s['price']} RSI:{s['rsi']} IV:{s['iv']}% Signal:{s['signal']}\n\n"
            f"All 4 options:\n"
            f"BUY CALL: GOOD/WEAK/SKIP Strike $__ Exp __ Cost $__ Win __%\n"
            f"BUY PUT: GOOD/WEAK/SKIP Strike $__ Exp __ Cost $__ Win __%\n"
            f"SELL CALL: GOOD/WEAK/SKIP Strike $__ Exp __ Collect $__ Win __%\n"
            f"SELL PUT: GOOD/WEAK/SKIP Strike $__ Exp __ Collect $__ Win __%\n"
            f"BEST NOW: which and why", chat_id, max_tokens=500)
        e="+" if s["chg1d"]>=0 else ""
        header=f"OPTIONS: {ticker}\n${s['price']} ({e}{s['chg1d']}%) RSI:{s['rsi']} IV:{s['iv']}%\n{'='*25}\n\n"
        kbd=[[InlineKeyboardButton("Day Trade",callback_data=f"daytrade_{ticker}"),
              InlineKeyboardButton("Signals",callback_data=f"signal_{ticker}")]]
        await msg.edit_text((header+ai)[:4000],reply_markup=InlineKeyboardMarkup(kbd))
    except Exception as e: await msg.edit_text(f"Error: {e}")

async def cmd_swing(update, context):
    if not await check_access(update, context, "swing"): return
    chat_id=str(update.effective_chat.id)
    q=getattr(update,"callback_query",None)
    args=context.args
    ticker=(args[0].upper() if args else (q.data.split("_",1)[1] if q and "_" in q.data else ""))
    if not ticker:
        await (q.message if q else update.message).reply_text("/swing NVDA"); return
    if q: msg=await q.message.edit_text(f"Swing trade for {ticker}...")
    else: msg=await update.message.reply_text(f"Swing trade for {ticker}...")
    try:
        s=analyze(ticker)
        ai=await ask_claude_for_user(
            f"LIVE: {ticker} ${s['price']} RSI:{s['rsi']} MACD:{s['macd']['cross']} "
            f"IV:{s['iv']}% ATR:{s['atr']} 5d:{s['chg5d']}%\n\n"
            f"Swing trade (2-5 day hold):\n"
            f"SIGNAL: STRONG/MODERATE/WEAK\n"
            f"Entry $__ Stop $__ Target $__ Hold __ days\n"
            f"OPTIONS: Buy __ $__ exp __ cost $__\n"
            f"KEY LEVELS: must hold $__ breakout at $__\n"
            f"EARNINGS: next date", chat_id)
        e="+" if s["chg1d"]>=0 else ""
        header=f"SWING: {ticker}\n${s['price']} ({e}{s['chg1d']}%) 5d:{s['chg5d']}%\n{'='*25}\n\n"
        kbd=[[InlineKeyboardButton("Day Trade",callback_data=f"daytrade_{ticker}"),
              InlineKeyboardButton("Options",callback_data=f"options_{ticker}")]]
        await msg.edit_text((header+ai)[:4000],reply_markup=InlineKeyboardMarkup(kbd))
    except Exception as e: await msg.edit_text(f"Error: {e}")

async def cmd_ask(update, context):
    if not await check_access(update, context, "ask"): return
    chat_id=str(update.effective_chat.id)
    args=context.args
    if not args:
        await update.message.reply_text("/ask NVDA — income strategy\n/ask AAPL — wheel setup"); return
    ticker=args[0].upper()
    msg=await update.message.reply_text(f"Income strategy for {ticker}...")
    try:
        s=analyze(ticker)
        if s.get("signal")=="ERROR":
            await msg.edit_text(f"Cannot find {ticker}."); return
        spy,vix=get_spy_vix()
        ai=await ask_claude_for_user(
            f"LIVE: {ticker} ${s['price']} RSI:{s['rsi']} IV:{s['iv']}% Signal:{s['signal']}\n"
            f"Support:{s['support']} VIX:{round(vix,1)}\n\n"
            f"Income strategy:\n"
            f"OUTLOOK: safe for premium selling?\n"
            f"WHEEL: Sell $__ Put exp __ collect $__ Collateral $__ Monthly $__\n"
            f"SPREAD: Sell $__/Buy $__ exp __ credit $__ maxloss $__ winprob __%\n"
            f"BEST CHOICE + EARNINGS WARNING", chat_id)
        e="+" if s["chg1d"]>=0 else ""
        header=f"{ticker} INCOME\n${s['price']} ({e}{s['chg1d']}%) {s['signal']}\nIV:{s['iv']}% +-${s['exp_move']}/30d\n{'='*25}\n\n"
        kbd=[[InlineKeyboardButton("Signals",callback_data=f"signal_{ticker}"),
              InlineKeyboardButton("Options",callback_data=f"options_{ticker}")],
             [InlineKeyboardButton("Day Trade",callback_data=f"daytrade_{ticker}"),
              InlineKeyboardButton("Wheel",callback_data=f"wheel_{ticker}")]]
        await msg.edit_text((header+ai)[:4000],reply_markup=InlineKeyboardMarkup(kbd))
    except Exception as e: await msg.edit_text(f"Error: {e}")

async def cmd_wheel(update, context):
    if not await check_access(update, context, "wheel"): return
    chat_id=str(update.effective_chat.id)
    q=getattr(update,"callback_query",None)
    args=context.args
    ticker=(args[0].upper() if args else (q.data.split("_",1)[1] if q and "_" in q.data else ""))
    if not ticker:
        await (q.message if q else update.message).reply_text("/wheel NVDA"); return
    if q: msg=await q.message.edit_text(f"Wheel setup for {ticker}...")
    else: msg=await update.message.reply_text(f"Wheel setup for {ticker}...")
    try:
        s=analyze(ticker)
        ai=await ask_claude_for_user(
            f"LIVE: {ticker} ${s['price']} RSI:{s['rsi']} IV:{s['iv']}% Support:{s['support']}\n\n"
            f"Wheel strategy:\n"
            f"Phase 1: Sell $__ Put exp __ premium $__ collateral $__ breakeven $__ annual __%\n"
            f"If assigned Phase 2: Sell $__ Call exp __ premium $__\n"
            f"Monthly income $__ Account needed $__\n"
            f"Rating __/10 + why + support level", chat_id)
        e="+" if s["chg1d"]>=0 else ""
        header=f"WHEEL: {ticker}\n${s['price']} ({e}{s['chg1d']}%)\n{'='*25}\n\n"
        await msg.edit_text((header+ai)[:4000])
    except Exception as e: await msg.edit_text(f"Error: {e}")

async def cmd_scan(update, context):
    if not await check_access(update, context, "scan"): return
    q=getattr(update,"callback_query",None)
    if q: msg=await q.message.edit_text("Scanning...")
    else: msg=await update.message.reply_text("Scanning...")
    chat_id=str(update.effective_chat.id)
    memory=load_user_memory(chat_id)
    positions=memory.get("positions",{})
    results=sorted([analyze(t) for t in WATCHLIST],key=lambda x:abs(x.get("score",0)),reverse=True)
    spy,vix=get_spy_vix()
    text=f"SCAN\n{datetime.now().strftime('%b %d %I:%M %p')}\nVIX:{round(vix,1)}\n\n"
    for s in results:
        ticker=s["ticker"]; e="+" if s["chg1d"]>=0 else ""
        owned="[YOURS] " if ticker in positions else ""
        macd="UP" if s["macd"]["cross"]=="bullish" else "DN"
        text+=f"{owned}{ticker} ${s['price']} {e}{s['chg1d']}%\n{s['signal']} RSI:{s['rsi']} MACD:{macd} IV:{s['iv']}%\n\n"
    kbd=[[InlineKeyboardButton("Refresh",callback_data="scan")]]
    try: await msg.edit_text(text[:4000],reply_markup=InlineKeyboardMarkup(kbd))
    except: await update.effective_chat.send_message(text[:4000],reply_markup=InlineKeyboardMarkup(kbd))

async def cmd_momentum(update, context):
    if not await check_access(update, context, "momentum"): return
    q=getattr(update,"callback_query",None)
    if q: msg=await q.message.edit_text("Finding momentum...")
    else: msg=await update.message.reply_text("Finding momentum...")
    chat_id=str(update.effective_chat.id)
    memory=load_user_memory(chat_id)
    positions=memory.get("positions",{})
    results=sorted([analyze(t) for t in WATCHLIST],key=lambda x:abs(x.get("score",0)),reverse=True)
    spy,vix=get_spy_vix()
    text=f"MOMENTUM\n{datetime.now().strftime('%b %d %I:%M %p')}\nVIX:{round(vix,1)}\n\n"
    for s in results[:6]:
        ticker=s["ticker"]; e="+" if s["chg1d"]>=0 else ""
        owned="[YOURS] " if ticker in positions else ""
        text+=f"{owned}{ticker} ${s['price']} {e}{s['chg1d']}%\n{s['signal']} RSI:{s['rsi']} IV:{s['iv']}%\n\n"
    kbd=[[InlineKeyboardButton(s["ticker"],callback_data=f"signal_{s['ticker']}") for s in results[:4]],
         [InlineKeyboardButton("Refresh",callback_data="momentum")]]
    try: await msg.edit_text(text[:4000],reply_markup=InlineKeyboardMarkup(kbd))
    except: await update.effective_chat.send_message(text[:4000],reply_markup=InlineKeyboardMarkup(kbd))

async def cmd_positions(update, context):
    if not await check_access(update, context, "positions"): return
    chat_id=str(update.effective_chat.id)
    q=getattr(update,"callback_query",None)
    memory=load_user_memory(chat_id)
    positions=memory.get("positions",{})
    if not positions:
        text="No positions saved.\nSend a screenshot to save any trade!"
        if q: await q.message.edit_text(text)
        else: await update.message.reply_text(text)
        return
    text=f"YOUR POSITIONS ({len(positions)})\n{datetime.now().strftime('%b %d %I:%M %p')}\n\n"
    for ticker,pos in positions.items():
        try:
            price=get_live_price(ticker); t=pos.get("type","")
            text+=f"{ticker} [{pos.get('broker','?')}]\n"
            if t=="put_credit_spread":
                short=pos.get("short_strike",0)
                buf=round(((price-short)/price)*100,1) if short and price else 0
                stat="SAFE" if buf>8 else "WATCH" if buf>4 else "DANGER"
                text+=f"  Spread ${short}/{pos.get('long_strike')} [{stat}] buf:{buf}%\n\n"
            elif t=="covered_call":
                text+=f"  Call ${pos.get('call_strike')} exp:{pos.get('call_expiry')}\n\n"
            elif t=="stock":
                cost=pos.get("avg_cost",0); pl=round((price-cost)*pos.get("shares",0),2) if cost else 0
                text+=f"  {pos.get('shares')} shares @ ${cost} PL:${pl}\n\n"
        except: text+=f"  Error\n\n"
    kbd=[[InlineKeyboardButton("Refresh",callback_data="positions")]]
    try:
        if q: await q.message.edit_text(text[:4000],reply_markup=InlineKeyboardMarkup(kbd))
        else: await update.message.reply_text(text[:4000],reply_markup=InlineKeyboardMarkup(kbd))
    except: await update.effective_chat.send_message(text[:4000],reply_markup=InlineKeyboardMarkup(kbd))

async def cmd_briefing(update, context):
    if not await check_access(update, context, "briefing"): return
    chat_id=str(update.effective_chat.id)
    q=getattr(update,"callback_query",None)
    if q: msg=await q.message.edit_text("Building briefing...")
    else: msg=await update.message.reply_text("Building briefing...")
    memory=load_user_memory(chat_id)
    positions=memory.get("positions",{})
    spy,vix=get_spy_vix()
    mood="HIGH FEAR" if vix>25 else "ELEVATED" if vix>18 else "CALM"
    text=f"DAILY BRIEFING\n{datetime.now().strftime('%B %d %Y %I:%M %p')}\nSPY:${round(spy,2)} VIX:{round(vix,1)} {mood}\n\n"
    if positions:
        text+=f"POSITIONS ({len(positions)})\n"
        for ticker,pos in positions.items():
            try:
                price=get_live_price(ticker); t=pos.get("type","")
                if t=="put_credit_spread":
                    short=pos.get("short_strike",0)
                    buf=round(((price-short)/price)*100,1) if short and price else 0
                    text+=f"  {'OK' if buf>8 else 'WATCH' if buf>4 else 'DANGER'} {ticker} ${price} Spread ${short} {buf}%\n"
                else: text+=f"  {ticker} ${price} {t}\n"
            except: pass
        text+="\n"
    results=sorted([analyze(t) for t in WATCHLIST],key=lambda x:abs(x.get("score",0)),reverse=True)
    text+="TOP SIGNALS\n"
    for s in results[:4]:
        e="+" if s["chg1d"]>=0 else ""
        text+=f"  {s['ticker']} ${s['price']} {e}{s['chg1d']}% {s['signal']}\n"
    kbd=[[InlineKeyboardButton("Positions",callback_data="positions"),
          InlineKeyboardButton("Momentum",callback_data="momentum")]]
    try: await msg.edit_text(text[:4000],reply_markup=InlineKeyboardMarkup(kbd))
    except: await update.effective_chat.send_message(text[:4000],reply_markup=InlineKeyboardMarkup(kbd))

async def cmd_alerts(update, context):
    if not await check_access(update, context, "alerts"): return
    await update.message.reply_text("Use /positions to check your positions.\nAuto-alerts are sent every 5 minutes automatically.")

async def cmd_history(update, context):
    if not await check_access(update, context, "history"): return
    chat_id=str(update.effective_chat.id)
    memory=load_user_memory(chat_id)
    closed=memory.get("closed",[])
    text=("No closed positions." if not closed else
          f"CLOSED ({len(closed)})\n\n"+"".join(
          f"{p.get('ticker','?')} {p.get('type','')}\n{p.get('closed_at','')[:10]}\n\n"
          for p in closed[-10:]))
    await update.message.reply_text(text)

async def cmd_profile(update, context):
    if not await check_access(update, context, "profile"): return
    chat_id=str(update.effective_chat.id)
    profile=load_user_profile(chat_id)
    text=(f"YOUR PROFILE\n{'='*20}\n"
          f"Account: ${profile.get('account_size','Not set')}\n"
          f"Brokers: {profile.get('brokers','Not set')}\n"
          f"Experience: {profile.get('experience_level','Not set')}\n"
          f"Risk: {profile.get('risk_tolerance','Not set')}\n"
          f"Goal: ${profile.get('monthly_income_goal','Not set')}/month\n\n"
          f"To update, just tell me:\n"
          f"'My account is now $30,000'\n"
          f"'I use Robinhood and Fidelity'\n"
          f"'My goal is $800/month'")
    await update.message.reply_text(text)

async def handle_photo(update, context):
    if not await check_access(update, context, "positions"): return
    chat_id=str(update.effective_chat.id)
    msg=await update.message.reply_text("Reading screenshot...")
    try:
        photo=update.message.photo[-1]
        file=await context.bot.get_file(photo.file_id)
        img=await file.download_as_bytearray()
        b64=base64.standard_b64encode(bytes(img)).decode()
        resp=claude.messages.create(model="claude-sonnet-4-20250514",max_tokens=400,
            messages=[{"role":"user","content":[
                {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":b64}},
                {"type":"text","text":"""Extract trade. Return ONLY JSON:
{"action":"open/close","ticker":"SYMBOL","broker":"Robinhood/Fidelity",
"type":"put_credit_spread/covered_call/cash_secured_put/stock/call_option/put_option",
"shares":null,"avg_cost":null,"short_strike":null,"long_strike":null,
"call_strike":null,"put_strike":null,"expiry":"YYYY-MM-DD",
"premium_collected":null,"contracts":null,"max_profit":null,"max_loss":null,
"confidence":"high/medium/low"}"""}]}])
        raw=resp.content[0].text.strip()
        if "```" in raw: raw=raw.split("```")[1].replace("json","").strip()
        ex=json.loads(raw)
        ticker=ex.get("ticker","").upper(); conf=ex.get("confidence","low")
        if not ticker or conf=="low":
            await msg.edit_text("Could not read. Try clearer screenshot."); return
        memory=load_user_memory(chat_id)
        t=ex.get("type","unknown")
        pos={"broker":ex.get("broker","?"),"type":t,"source":"screenshot"}
        if t=="put_credit_spread":
            pos.update({"short_strike":ex.get("short_strike"),"long_strike":ex.get("long_strike"),
                        "expiry":ex.get("expiry"),"premium_collected":ex.get("premium_collected"),
                        "contracts":ex.get("contracts",1),"max_profit":ex.get("max_profit"),
                        "max_loss":ex.get("max_loss")})
        elif t=="covered_call":
            pos.update({"shares":ex.get("shares",100),"avg_cost":ex.get("avg_cost"),
                        "call_strike":ex.get("call_strike"),"call_expiry":ex.get("expiry"),
                        "call_premium":ex.get("premium_collected")})
        elif t=="stock":
            pos.update({"shares":ex.get("shares"),"avg_cost":ex.get("avg_cost")})
        action=ex.get("action","open")
        if action=="close" and ticker in memory["positions"]:
            memory["positions"].pop(ticker)
            save_user_memory(chat_id, memory)
            await msg.edit_text(f"{ticker} CLOSED and removed from monitoring.")
        else:
            memory["positions"][ticker]=pos
            save_user_memory(chat_id, memory)
            kbd=[[InlineKeyboardButton("AI Strategy",callback_data=f"ai_{ticker}"),
                  InlineKeyboardButton("Signals",callback_data=f"signal_{ticker}")]]
            await msg.edit_text(f"{ticker} SAVED!\n{t} [{ex.get('broker','?')}]\nMonitoring automatically!",
                reply_markup=InlineKeyboardMarkup(kbd))
    except Exception as e: await msg.edit_text(f"Error: {e}")

async def handle_text(update, context):
    if not await check_access(update, context, "start"): return
    chat_id=str(update.effective_chat.id)
    user=get_user(chat_id)
    tier=user.get("tier","trial") if user else "trial"
    # Premium and Pro get full chat
    if tier not in ["premium","pro"] and not is_admin(chat_id):
        await update.message.reply_text(
            "Natural chat is available on Pro and Premium plans.\n\n"
            "Upgrade to just talk naturally!\n"
            "Use commands for now:\n/signal NVDA\n/daytrade AAPL\n/ask NVDA")
        return
    msg=await update.message.reply_text("Thinking... (~15 sec)")
    try:
        user_text=update.message.text.strip()
        mentioned=re.findall(r'\b(NVDA|AAPL|MSFT|GOOGL|NFLX|AMZN|META|TSLA)\b',user_text.upper())
        market_ctx=build_market_ctx(mentioned)
        profile=load_user_profile(chat_id)
        user_ctx=build_user_context(chat_id)
        system=(f"You are a personal trading advisor on Telegram with LIVE market data.\n"
                f"You have real-time prices — use them. NEVER say you lack real-time data.\n"
                f"{user_ctx}\n{market_ctx}\n"
                f"Give specific advice with exact numbers. Under 300 words.")
        resp=claude.messages.create(model="claude-sonnet-4-20250514",max_tokens=500,
            system=system,messages=[{"role":"user","content":user_text}])
        # Check for profile updates
        ai=resp.content[0].text
        matches=re.findall(r'\[PROFILE_UPDATE: (\w+)=([^\]]+)\]',ai)
        for key,value in matches:
            profile[key]=value.strip()
            save_user_profile(chat_id,profile)
        ai=re.sub(r'\[PROFILE_UPDATE:[^\]]+\]','',ai).strip()
        await msg.edit_text(ai[:4000])
    except Exception as e: await msg.edit_text(f"Error: {e}")

async def button_handler(update, context):
    q=update.callback_query; await q.answer(); d=q.data
    chat_id=str(update.effective_chat.id)
    if   d=="positions":  await cmd_positions(update,context)
    elif d=="scan":       await cmd_scan(update,context)
    elif d=="momentum":   await cmd_momentum(update,context)
    elif d=="briefing":   await cmd_briefing(update,context)
    elif d=="profile_view": await cmd_profile(update,context)
    elif d=="admin_users": await cmd_users(update,context)
    elif d=="admin_create_code":
        if is_admin(chat_id):
            code=create_access_code("pro",30)
            await q.message.reply_text(f"New PRO code (30 days):\n{code}")
    elif d=="admin_revenue":
        if is_admin(chat_id):
            users=get_users_db()
            rev=sum(TIERS.get(u.get("tier","trial"),{}).get("price",0)
                   for u in users.values() if is_active(u["chat_id"]))
            await q.message.reply_text(f"Monthly Revenue: ${rev}\nActive Users: {sum(1 for u in users.values() if is_active(u['chat_id']))}")
    elif d.startswith("signal_"):  ticker=d[7:]; context.args=[ticker]; await cmd_signal(update,context)
    elif d.startswith("daytrade_"):ticker=d[9:]; context.args=[ticker]; await cmd_daytrade(update,context)
    elif d.startswith("options_"): ticker=d[8:]; context.args=[ticker]; await cmd_options(update,context)
    elif d.startswith("swing_"):   ticker=d[6:]; context.args=[ticker]; await cmd_swing(update,context)
    elif d.startswith("wheel_"):   ticker=d[6:]; context.args=[ticker]; await cmd_wheel(update,context)
    elif d.startswith("ask_"):     ticker=d[4:]; context.args=[ticker]; await cmd_ask(update,context)
    elif d.startswith("ai_"):
        ticker=d[3:]; s=analyze(ticker)
        ai=await ask_claude_for_user(f"LIVE: {ticker} ${s['price']} RSI:{s['rsi']} {s['signal']}\nQuick 100-word income strategy.", chat_id)
        await q.message.reply_text(f"{ticker}\n\n{ai}")

async def send_msg_to(app, chat_id, text):
    try: await app.bot.send_message(chat_id=chat_id, text=text)
    except: pass

def run_position_monitor(app, loop):
    """Monitor all users' positions every 5 minutes"""
    async def monitor():
        users=get_users_db()
        for uid in users:
            if not is_active(uid): continue
            try:
                memory=load_user_memory(uid)
                positions=memory.get("positions",{})
                for ticker,pos in positions.items():
                    price=get_live_price(ticker)
                    if not price: continue
                    t=pos.get("type","")
                    if t=="put_credit_spread":
                        short=float(pos.get("short_strike",0) or 0)
                        if short and price:
                            buf=round(((price-short)/price)*100,1)
                            if buf<3:
                                await send_msg_to(app,uid,
                                    f"🚨 EMERGENCY: {ticker}\n"
                                    f"Only {buf}% above ${short}!\n"
                                    f"Close position NOW on Robinhood!")
                            elif buf<5:
                                await send_msg_to(app,uid,
                                    f"⚠️ WARNING: {ticker}\n"
                                    f"Buffer {buf}% getting thin\n"
                                    f"Prepare to close if drops more")
            except: pass
    def t():
        time.sleep(120)
        while True:
            try: asyncio.run_coroutine_threadsafe(monitor(),loop).result(120)
            except: pass
            time.sleep(300)
    threading.Thread(target=t,daemon=True).start()
    logger.info("Position monitor running every 5 min (all users)")

def run_signal_scanner(app, loop):
    """Scan for strong signals and alert relevant users"""
    async def scan():
        for ticker in WATCHLIST:
            try:
                s=analyze(ticker); score=s.get("score",0)
                if abs(score)<6: continue
                users=get_users_db()
                for uid in users:
                    if not is_active(uid): continue
                    try:
                        e="+" if s["chg1d"]>=0 else ""
                        label="STRONG BUY!" if score>=6 else "STRONG SELL!"
                        await send_msg_to(app,uid,
                            f"{label}\n{ticker} ${s['price']} {e}{s['chg1d']}%\n"
                            f"RSI:{s['rsi']} Score:{score:+.1f}\n\n"
                            f"/signal {ticker} for full analysis")
                    except: pass
                await asyncio.sleep(1)
            except: pass
    def t():
        while True:
            try: asyncio.run_coroutine_threadsafe(scan(),loop).result(180)
            except: pass
            time.sleep(SCAN_MINS*60)
    threading.Thread(target=t,daemon=True).start()
    logger.info("Signal scanner running")

async def cmd_cancel(update, context):
    """User requests cancellation"""
    chat_id = str(update.effective_chat.id)
    user = get_user(chat_id)
    if not user:
        await update.message.reply_text("You don't have an active subscription.")
        return
    days = days_remaining(chat_id)
    tier = user.get("tier","trial")
    await update.message.reply_text(
        f"CANCEL SUBSCRIPTION\n\n"
        f"Current plan: {tier.upper()}\n"
        f"Access until: {user.get('expires','')[:10]}\n"
        f"Days remaining: {days}\n\n"
        f"To cancel:\n"
        f"1. Email: {GMAIL_SENDER}\n"
        f"2. Subject: Cancel - @{user.get('username','?')}\n"
        f"3. Your access continues until expiry date\n"
        f"4. No refunds for partial months\n\n"
        f"Your data will be exported and deleted after 30 days.\n\n"
        f"We're sorry to see you go! If there's anything we can improve, "
        f"please let us know in your cancellation email.")
    # Notify admin
    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=f"CANCELLATION REQUEST\n"
                 f"User: {user.get('username','?')} ({chat_id})\n"
                 f"Plan: {tier}\n"
                 f"Days left: {days}\n"
                 f"Action needed: confirm cancellation")
    except: pass


def main():
    validate_settings()
    print("\nTradeOracle AI — Multi-User SaaS Edition")
    print("==========================================")
    users=get_users_db()
    print(f"Total users: {len(users)}")
    print(f"Active users: {sum(1 for u in users.values() if is_active(u['chat_id']))}")

    # Create initial admin code if no users
    codes=get_access_codes()
    if not codes:
        code=create_access_code("premium",365)
        print(f"\nYour admin access code: {code}")
        print("This gives 1 year premium access")

    app=Application.builder().token(TELEGRAM_TOKEN).build()
    loop=asyncio.new_event_loop()

    for cmd,fn in [
        ("start",cmd_start),("activate",cmd_activate),
        ("admin",cmd_admin),("adduser",cmd_adduser),
        ("users",cmd_users),("revoke",cmd_revoke),
        ("broadcast",cmd_broadcast),
        ("ask",cmd_ask),("wheel",cmd_wheel),
        ("signal",cmd_signal),("daytrade",cmd_daytrade),
        ("options",cmd_options),("swing",cmd_swing),
        ("scan",cmd_scan),("momentum",cmd_momentum),
        ("positions",cmd_positions),("briefing",cmd_briefing),
        ("alerts",cmd_alerts),("history",cmd_history),
        ("profile",cmd_profile),
        ("cancel",cmd_cancel)]:
        app.add_handler(CommandHandler(cmd,fn))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    run_position_monitor(app,loop)
    run_signal_scanner(app,loop)

    print("\nBot is LIVE!")
    print(f"Admin ID: {ADMIN_CHAT_ID}")
    print("Share bot link with customers")
    print("Use /adduser pro 30 to create access codes")

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":
    main()
