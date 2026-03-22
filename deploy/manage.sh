#!/bin/bash
# ═══════════════════════════════════════════
# TradeOracle AI — Bot Management
# ═══════════════════════════════════════════

case "$1" in
    start)
        systemctl start tradeoracleai
        echo "✅ Bot started"
        systemctl status tradeoracleai --no-pager
        ;;
    stop)
        systemctl stop tradeoracleai
        echo "🛑 Bot stopped"
        ;;
    restart)
        systemctl restart tradeoracleai
        echo "🔄 Bot restarted"
        systemctl status tradeoracleai --no-pager
        ;;
    status)
        systemctl status tradeoracleai --no-pager
        ;;
    logs)
        tail -f /var/log/tradeoracleai/bot.log
        ;;
    errors)
        tail -f /var/log/tradeoracleai/bot.error.log
        ;;
    update)
        echo "📥 Pulling latest from GitHub..."
        cd /opt/tradeoracleai
        git pull origin main
        systemctl restart tradeoracleai
        echo "✅ Updated and restarted"
        ;;
    users)
        echo "👥 Active users:"
        python3 -c "
import json, os
path = '/opt/tradeoracleai/user_data/users.json'
if os.path.exists(path):
    users = json.load(open(path))
    active = [u for u in users.values() if u.get('active')]
    print(f'Total: {len(users)} | Active: {len(active)}')
    for u in list(users.values())[:10]:
        print(f'  {u.get(\"username\",\"?\")} | {u.get(\"tier\",\"?\")} | expires: {u.get(\"expires\",\"?\")[:10]}')
else:
    print('No users yet')
"
        ;;
    backup)
        DATE=$(date +%Y%m%d_%H%M)
        tar -czf /tmp/backup_$DATE.tar.gz /opt/tradeoracleai/user_data/
        echo "✅ Backup: /tmp/backup_$DATE.tar.gz"
        ;;
    *)
        echo "TradeOracle AI Bot Manager"
        echo ""
        echo "Usage: bash manage.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start    — Start the bot"
        echo "  stop     — Stop the bot"
        echo "  restart  — Restart the bot"
        echo "  status   — Check if running"
        echo "  logs     — View live logs"
        echo "  errors   — View error logs"
        echo "  update   — Pull from GitHub & restart"
        echo "  users    — Show user stats"
        echo "  backup   — Backup user data"
        ;;
esac
