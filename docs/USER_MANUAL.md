# AI TRADING BOT — COMPLETE MANUAL
### Your Personal AI Trading Advisor
**Version:** Complete Edition | **Date:** March 2026

---

## TABLE OF CONTENTS
1. Getting Started
2. Daily Routine
3. Income Strategies (Wheel, Spreads, Covered Calls)
4. Day Trading
5. Swing Trading
6. Options — All 4 Directions
7. Technical Signals
8. Position Management
9. Alerts & Emergency System
10. Email Setup
11. Profile Setup
12. All Commands Reference
13. Screenshots — How To Save Trades
14. Rules To Never Break

---

## 1. GETTING STARTED

### Start The Bot Every Day
Open Termux app on your phone and run:
```
nohup python ~/bot.py > ~/bot.log 2>&1 &
```
Then minimize Termux (don't close it).

### Check If Bot Is Running
```
ps aux | grep bot.py
```
If nothing shows, restart with command above.

### Open Telegram
Search for your bot: **Rks-ai-market**
Type: `/start`

---

## 2. DAILY ROUTINE (5-10 minutes)

### Morning (Before Market Opens 9AM)
```
/briefing
```
Shows you:
- Market mood (VIX level)
- Your open positions status
- Best opportunities today
- Any alerts on your positions

### During Market Hours
Just chat naturally or use commands.
Bot scans automatically every 5 minutes.

### End of Day
```
/positions
```
Check all positions are safe for overnight.

---

## 3. INCOME STRATEGIES

### 3A. Wheel Strategy
**Best for:** Stocks you are happy to own
**Risk:** Medium | **Income:** Monthly

```
/wheel NVDA
/wheel AAPL
/wheel NFLX
```

**What you get:**
- Exact put strike to sell
- Exact expiry date
- Premium to collect
- Monthly income estimate
- What to do if assigned

**How Wheel Works:**
```
Step 1: Sell cash secured put
        → Collect $120-300 premium
        → Stock stays above strike = PROFIT ✅
        → Stock drops below strike = GET ASSIGNED

Step 2: If assigned, own 100 shares
        → Immediately sell covered call
        → Collect more premium

Step 3: Call expires or gets called away
        → Start again from Step 1
        → Repeat every month
```

### 3B. Cash Secured Put
**Best for:** Stocks you want to own cheap
**Risk:** Medium | **Income:** Monthly

```
/ask NVDA
```
Then look for CASH SECURED PUT section.

**Example:**
```
NVDA at $180
Sell $165 Put Apr 17
Collect $120 premium
Collateral needed: $16,500
If NVDA stays above $165 → keep $120 ✅
If NVDA drops below $165 → own shares at $165
```

### 3C. Covered Call (Your NFLX Strategy)
**Best for:** Stocks you already own
**Risk:** Low | **Income:** Monthly

**Your NFLX Setup:**
```
You own: 100 shares at $103.68
Current price: ~$94.70
Loss: ~$898

Every month:
- Sell $100 Call before earnings
- Collect ~$100-135/month
- Recover loss in 8-9 months

IMPORTANT: Always use expiry BEFORE April 16 earnings
Use April 10 expiry, NOT April 17!
```

**Steps on Fidelity:**
```
1. Open Fidelity app
2. Go to NFLX → Trade → Options
3. Select: Sell to Open
4. Type: Call
5. Expiry: Apr 10, 2026
6. Strike: $100
7. Qty: 1
8. Limit: $1.08
9. Preview → Submit
```

### 3D. Put Credit Spread
**Best for:** Defined risk, less capital needed
**Risk:** Low-Medium | **Income:** Monthly

**Your 4-Stock Plan:**
```
NVDA: Sell $165 / Buy $155 Put Apr 17
      Collect ~$240 | Collateral $2,000

AAPL: Sell $230 / Buy $220 Put Apr 17
      Collect ~$200 | Collateral $2,000

MSFT: Sell $365 / Buy $355 Put Apr 17
      Collect ~$200 | Collateral $2,000

GOOGL: Sell $280 / Buy $270 Put Apr 17
       Collect ~$200 | Collateral $2,000

TOTAL: ~$840/month from $8,000 deployed
```

**Alert Levels For Each Spread:**
```
Buffer > 8%  = SAFE (no action)
Buffer 5-8%  = WATCH (check daily)
Buffer < 5%  = WARNING (prepare to close)
Buffer < 3%  = DANGER (close now!)
```

---

## 4. DAY TRADING

**Your Rules:**
- Maximum 1-2 trades per day
- Only trade STRONG signals (7+/10)
- Always set stop loss BEFORE entering
- Risk maximum $250-500 per trade
- Best times: 9:45-11AM and 2-3PM EST
- Never chase a stock already moving fast

### Get Day Trade Setup
```
/daytrade NVDA
/daytrade AAPL
/daytrade TSLA
```

**What you get:**
```
SIGNAL STRENGTH: 8/10 — TRADE ✅

Direction: LONG (buy)
Entry: $181.50
Stop Loss: $179.50 (max loss: $200)
Target 1: $183.50 (+1.1%) = $200 profit
Target 2: $185.00 (+1.9%) = $350 profit
Risk/Reward: 1:2
Best entry time: 10-11 AM EST

OPTIONS ALTERNATIVE:
Buy $182 Call expiry today
Cost: ~$80 | Target: ~$160
Max loss: $80
```

### Day Trade Rules
```
✅ TRADE when:
- Signal score 7+/10
- MACD bullish crossover
- RSI between 40-60 (not extreme)
- Volume above average
- Clear support/resistance level

❌ SKIP when:
- Signal score below 6/10
- Earnings within 2 weeks
- VIX above 30 (too volatile)
- Already missed the move
- Monday morning or Friday afternoon
```

---

## 5. SWING TRADING

**Hold time:** 2-5 days
**Best for:** Catching 5-15% moves

```
/swing NVDA
/swing AAPL
/swing META
```

**What you get:**
- Entry price and level
- Stop loss level
- 2-5 day price target
- Options trade for leverage
- Key levels to watch
- Upcoming catalysts

**Swing Trade Rules:**
```
✅ Enter on pullbacks (stock dipped)
✅ Use options for leverage with defined risk
✅ Set alerts at stop loss level
✅ Take partial profit at Target 1

❌ Never enter on breakouts (already moved)
❌ Never hold through earnings
❌ Never risk more than $500
```

---

## 6. OPTIONS — ALL 4 DIRECTIONS

```
/options NVDA
/options AAPL
```

### Understanding All 4 Options

**BUY CALL (Bullish)**
```
When to use: Stock going UP
You pay premium upfront
Profit: Stock rises above strike
Loss: Limited to what you paid
Best when: RSI below 35, MACD bullish, IV low
Example: Buy $182 Call → costs $80 → profit if NVDA > $182
```

**BUY PUT (Bearish)**
```
When to use: Stock going DOWN
You pay premium upfront
Profit: Stock falls below strike
Loss: Limited to what you paid
Best when: RSI above 65, MACD bearish, IV low
Example: Buy $178 Put → costs $75 → profit if NVDA < $178
```

**SELL CALL (Neutral/Bearish)**
```
When to use: Stock staying flat or going down
You COLLECT premium
Profit: Stock stays below strike
Loss: Unlimited if no shares (always own shares first!)
Best when: You own shares, want monthly income
Example: Sell $190 Call → collect $80 → profit if NVDA < $190
```

**SELL PUT (Neutral/Bullish)**
```
When to use: Stock staying flat or going up
You COLLECT premium
Profit: Stock stays above strike
Loss: Must buy shares if assigned
Best when: RSI below 40, bullish market, IV high
Example: Sell $165 Put → collect $120 → profit if NVDA > $165
```

### When To Buy vs Sell Options
```
IV (Implied Volatility) BELOW 25%:
→ GOOD time to BUY options (cheap)
→ BAD time to SELL options

IV ABOVE 30%:
→ BAD time to BUY options (expensive)
→ GOOD time to SELL options ✅

VIX above 20 = elevated IV everywhere
VIX above 30 = very high IV, great for selling
```

---

## 7. TECHNICAL SIGNALS

```
/signal NVDA
/signal AAPL
/momentum
/scan
```

### Understanding The Indicators

**RSI (Relative Strength Index)**
```
Below 30 = Oversold → BUY signal 🟢
30-40    = Low → Slightly bullish
40-60    = Neutral → No signal
60-70    = High → Slightly bearish
Above 70 = Overbought → SELL signal 🔴
```

**MACD**
```
Bullish crossover = Momentum turning UP 🟢
Bearish crossover = Momentum turning DOWN 🔴
```

**Bollinger Bands**
```
Price near lower band = Oversold, potential bounce 🟢
Price near upper band = Overbought, potential drop 🔴
Price in middle      = Neutral
```

**Volume**
```
2x+ average volume = Strong signal, more reliable
Normal volume      = Weak signal, less reliable
```

**Signal Score**
```
+6 to +10 = STRONG BUY  🟢🟢
+3 to +5  = BUY         🟢
-2 to +2  = NEUTRAL     ⬜
-3 to -5  = SELL        🔴
-6 to -10 = STRONG SELL 🔴🔴
```

---

## 8. POSITION MANAGEMENT

### View All Positions
```
/positions
```

### Check For Alerts
```
/alerts
```

### Close A Position (Robinhood)
```
1. Go to your position
2. Tap Close Position
3. Set limit price = current ask
4. Submit
```

### Stop Loss Rules
```
Put Credit Spread:
- Set phone alert when stock near strike
- Alert at: strike price + 5%
- Close if buffer drops below 5%

Covered Call:
- Close if stock drops 15%+ below cost
- Roll call down if stock near strike

Day Trade:
- Always set stop before entering
- Never move stop loss lower
- Take 50% profit at Target 1
```

### The 2x Rule
```
You collected $120 premium
If spread now costs $240 to close (2x)
→ CLOSE IMMEDIATELY
→ Take the $120 loss
→ Saved from potential $880 max loss
```

---

## 9. ALERTS & EMERGENCY SYSTEM

### How The Alert System Works

**Every 5 minutes bot checks:**
```
Buffer > 12% = Silent ✅

Buffer 8-12% + MACD turning bad:
→ ⚠️ WARNING sent to Telegram
→ Email sent
→ "Watch closely — 30 min heads up"

Buffer 5-8%:
→ ⚠️ WARNING sent
→ Email sent
→ "Prepare to close — 15 min heads up"

Buffer < 5%:
→ 🚨 EMERGENCY sent to Telegram
→ Phone vibrates even on silent!
→ Email sent immediately
→ Exact steps to close

Buffer < 2%:
→ 🚨🚨 DOUBLE EMERGENCY
→ Close NOW
```

### Profit Alerts
```
When spread reaches $7+ profit:
→ Bot notifies you
→ "Consider locking in profit"
→ Even small wins add up!
```

### Enable Phone Vibration On Silent
```
Android Settings:
1. Apps → Telegram → Notifications
2. Set priority to HIGH or URGENT
3. Allow override Do Not Disturb
4. Turn on vibration

This makes Telegram vibrate 
even when phone is silent!
```

---

## 10. EMAIL SETUP

### Get Gmail App Password
```
1. Go to myaccount.google.com/apppasswords
2. Select app: Mail
3. Select device: Other → "Trading Bot"
4. Click Generate
5. Copy the 16-digit password
```

### Connect Email To Bot
In Telegram send:
```
/setpassword abcdefghijklmnop
```
(your 16-digit password, no spaces)

### Test It Works
```
/testalert
```
You should get:
- Telegram emergency message
- Email to rishisharma1510@gmail.com

### Email Alerts You Will Receive
```
Subject: 🚨 EMERGENCY: NVDA NEEDS ACTION NOW
Subject: ⚠️ WARNING: AAPL — Act Soon
Subject: ✅ Trading Bot Email Connected!
```

---

## 11. PROFILE SETUP

### Update Your Profile
```
/profile
```
Shows menu:
```
1. Account Size: $25,000
2. Brokers: Robinhood, Fidelity
3. Experience: Beginner
4. Risk: Conservative
5. Monthly Goal: $500/mo
6. Check Frequency: Once a day
7. Holdings: 1 stocks
```
Reply with number to update just that field.

### What Profile Does
Bot uses your profile to:
- Give strategies matching your account size
- Recommend correct broker (Robinhood vs Fidelity)
- Adjust risk levels for conservative style
- Remember your holdings for covered call advice

---

## 12. ALL COMMANDS REFERENCE

### Income Commands
```
/ask SYMBOL    Full income strategy (wheel + spread + put)
/wheel SYMBOL  Dedicated wheel strategy setup
```

### Trading Commands
```
/signal SYMBOL    Full technical analysis (RSI, MACD, BB, patterns)
/daytrade SYMBOL  Day trade setup with entry, stop, target
/options SYMBOL   All 4 options directions analyzed
/swing SYMBOL     2-5 day swing trade setup
```

### Scanning Commands
```
/scan        Scan all 8 watchlist stocks
/momentum    Top momentum stocks right now
/predictions AI predictions for top stocks
```

### Position Commands
```
/positions   View all open positions with P&L
/alerts      Check position alerts
/history     View closed positions
```

### Information Commands
```
/briefing    Full daily market briefing
/profile     View and update your profile
```

### Alert Commands
```
/setemail EMAIL       Set alert email address
/setpassword PASSWORD Connect Gmail
/testalert           Test emergency alert system
```

### Natural Chat
Just type anything:
```
"what should i do with nvda today?"
"is aapl good for a day trade?"
"give me a swing trade idea"
"my account is now $30,000"
"explain put credit spreads"
"should i close my position?"
```

---

## 13. SCREENSHOTS — SAVE TRADES

### How To Save Any Trade
1. Take screenshot on Robinhood or Fidelity
2. Send the screenshot to bot in Telegram
3. Bot reads it automatically
4. Saves to your positions
5. Starts monitoring immediately

### What Bot Can Read
```
✅ Put credit spreads
✅ Covered calls
✅ Cash secured puts
✅ Stock positions
✅ Call options bought
✅ Put options bought
```

### After Saving
Bot shows buttons:
- AI Strategy → get advice on the position
- Signals → technical analysis
- Remove → delete from monitoring

### To Close A Position
Send closing screenshot and bot removes it from monitoring automatically.

---

## 14. RULES TO NEVER BREAK

### Capital Protection Rules
```
1. Never risk more than $500 on any single trade
2. Always set stop loss BEFORE entering
3. Never average down (buy more of losing position)
4. Never trade with emotions
5. Cash reserve: always keep $10,000+ untouched
```

### Options Rules
```
6. Never buy options before earnings
7. Never sell spreads with less than 5% buffer
8. Always use defined risk (spreads not naked)
9. Close position if 2x premium rule triggers
10. Never let options expire — close early
```

### Day Trading Rules
```
11. Maximum 2 trades per day
12. Only trade score 7+/10 signals
13. Best times: 9:45-11AM and 2-3PM EST
14. Never chase a stock already moving
15. Take partial profit at Target 1
```

### NFLX Specific Rules
```
16. NEVER sell call expiring after April 16
    (earnings date — huge risk!)
17. Always use April 10 expiry for April trade
18. Strike must be above $94.70 current price
19. Sell $100 strike for safety
```

### General Rules
```
20. Check positions once every morning
21. Act immediately on emergency alerts
22. Small consistent wins beat big risky trades
23. If unsure — ask the bot first
24. Keep learning — ask bot to explain anything
```

---

## QUICK REFERENCE CARD

### Morning Checklist (2 minutes)
```
□ Open Telegram → /briefing
□ Check VIX level (safe if below 20)
□ Check your positions status
□ Note best opportunity for today
```

### Before Any Trade
```
□ Ask bot: "/signal SYMBOL"
□ Check score (need 6+/10)
□ Set stop loss level
□ Confirm risk amount (max $500)
□ Check for upcoming earnings
```

### Alert Response
```
⚠️ Warning received:
→ Check position in Robinhood
→ Prepare to close if buffer < 5%
→ Reply to bot: "should I close NVDA?"

🚨 Emergency received:
→ Open Robinhood IMMEDIATELY
→ Close Position → Market order
→ Don't wait — act now!
```

### Monthly Income Targets
```
NFLX covered call:  ~$108-135/month (Fidelity)
NVDA spread:        ~$240/month (Robinhood)
AAPL spread:        ~$200/month (Robinhood)
MSFT spread:        ~$200/month (Robinhood)
GOOGL spread:       ~$200/month (Robinhood)
─────────────────────────────────
TOTAL TARGET:       ~$948-975/month
```

---

*Manual created March 2026*
*Your bot: @Rks-ai-market on Telegram*
*Email alerts: rishisharma1510@gmail.com*

