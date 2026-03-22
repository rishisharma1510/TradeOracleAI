#!/bin/bash
# ═══════════════════════════════════════════
# TradeOracle AI — SSL Certificate Setup
# Run AFTER setup.sh and AFTER DNS is pointed
# ═══════════════════════════════════════════

DOMAIN="trade-oracle-ai.com"
EMAIL="rishisharma1510@gmail.com"

echo "🔐 Getting SSL certificate for $DOMAIN..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --redirect

echo "✅ SSL certificate installed!"
echo ""
echo "Your site is now live at:"
echo "  https://$DOMAIN"
echo "  https://www.$DOMAIN"
echo ""

# Auto-renew SSL
echo "Setting up auto-renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * certbot renew --quiet") | crontab -
echo "✅ Auto-renewal configured"
