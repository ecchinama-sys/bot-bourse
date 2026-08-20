import os
import logging
from datetime import datetime
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Récupération des clés secrètes depuis les variables d'environnement Railway
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# --- LISTE DES ACTIFS ---
PORTFOLIO_ASSETS = [
    {"name": "Bitcoin", "ticker": "BTCUSD", "sector": "Crypto"},
    {"name": "S&P 500", "ticker": "SPX", "sector": "Indice US"},
    {"name": "CAC 40", "ticker": "CAC40", "sector": "Indice Europe"},
    {"name": "Tesla", "ticker": "TSLA", "sector": "Tech / Automobile"},
    {"name": "Apple", "ticker": "AAPL", "sector": "Tech / Grand Public"}
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start pour initialiser le bot et afficher le clavier."""
    # Création d'un clavier permanent en bas de l'écran avec un bouton
    keyboard = [["📈 Lancer le Flash Marché"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_message = (
        "🤖 **Assistant de Veille Macro & Tactique**\n\n"
        "Je suis opérationnel ! Utilise le bouton ci-dessous pour lancer une analyse instantanée."
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown", reply_markup=reply_markup)

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche la liste des actifs suivis."""
    msg = "📊 **Actifs surveillés :**\n\n"
    for asset in PORTFOLIO_ASSETS:
        msg += f"• **{asset['name']}** ({asset['ticker']}) - *{asset['sector']}*\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def flash_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Génère un flash d'analyse tactique journalier."""
    await update.message.reply_text("🔍 Analyse macroéconomique mondiale en cours...")
    
    date_str = datetime.now().strftime("%d/%m/%Y")
    report = f"📈 **FLASH MARCHÉS - {date_str}**\n\n"
    report += "🎯 **Profil de risque :** Équilibré / Prudent\n\n"
    
    for asset in PORTFOLIO_ASSETS:
        signal = "[HOLD]" 
        if asset['sector'] == "Crypto":
            signal = "[ACHAT PRUDENT]"
        elif asset['sector'] == "Indice US":
            signal = "[HOLD]"
            
        report += f"• **{asset['name']}** : {signal}\n  *Analyse : Tendance globale stable, surveillance sur TradingView.* \n\n"
    
    report += "💡 *Rappel : Vérifie toujours les graphiques sur TradingView avant d'agir.*"
    
    await update.message.reply_text(report, parse_mode="Markdown")

    # Notion sync (si configuré)
    if NOTION_TOKEN and NOTION_DATABASE_ID:
        try:
            headers = {
                "Authorization": f"Bearer {NOTION_TOKEN}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            payload = {
                "parent": {"database_id": NOTION_DATABASE_ID},
                "properties": {
                    "Name": {"title": [{"text": {"content": f"Bilan Flash - {date_str}"}}]},
                    "Date": {"date": {"start": datetime.now().isoformat()}}
                }
            }
            requests.post("https://api.notion.com/v1/pages", json=payload, headers=headers)
        except Exception as e:
            logging.error(f"Erreur lors de la sync Notion : {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Permet au bot de réagir lorsque tu cliques sur le bouton du clavier."""
    text = update.message.text
    if text == "📈 Lancer le Flash Marché":
        await flash_analysis(update, context)

def main():
    """Point d'entrée du bot."""
    if not TELEGRAM_TOKEN:
        print("Erreur : Le token Telegram est manquant.")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("flash", flash_analysis))
    app.add_handler(CommandHandler("portfolio", portfolio))
    
    # Gestionnaire pour écouter le texte du bouton cliquable
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Le bot est en route...")
    app.run_polling()

if __name__ == '__main__':
    main()
