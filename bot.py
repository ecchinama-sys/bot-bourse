import os
import logging
from datetime import datetime
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from groq import Groq

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Récupération des clés secrètes
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialisation du client Groq (si la clé est présente)
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

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
    keyboard = [["📈 Lancer le Flash Marché"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_message = (
        "🤖 **Assistant de Veille Macro & Tactique (Mode IA Avancé)**\n\n"
        "Je suis connectée et prête. Utilise le bouton ci-dessous pour générer une analyse de marché fraîche en temps réel."
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown", reply_markup=reply_markup)

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche la liste des actifs suivis."""
    msg = "📊 **Actifs surveillés :**\n\n"
    for asset in PORTFOLIO_ASSETS:
        msg += f"• **{asset['name']}** ({asset['ticker']}) - *{asset['sector']}*\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def flash_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Génère un flash d'analyse dynamique via l'IA Groq."""
    await update.message.reply_text("🔍 Analyse macroéconomique mondiale en cours par l'IA...")
    
    date_str = datetime.now().strftime("%d/%m/%Y")
    
    # Si la clé Groq est configurée, on demande une vraie analyse dynamique à l'IA
    if groq_client:
        try:
            prompt = (
                "Agis en tant qu'analyste financier macroéconomique expert, prudent et pédagogue. "
                "Génère un bulletin flash court et percutant pour les actifs suivants : "
                "Bitcoin, S&P 500, CAC 40, Tesla, Apple. "
                "Pour chaque actif, donne un signal court (ex: [ACHAT PRUDENT], [HOLD], [ATTENTE]) "
                "et une courte phrase d'explication de tendance globale. "
                "Le ton doit être axé sur l'apprentissage et la gestion du risque, en rappelant de vérifier TradingView. "
                "Formatte le tout proprement avec des émojis et du markdown."
            )
            
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
            )
            ai_text = chat_completion.choices[0].message.content
            report = f"📈 **FLASH MARCHÉS (IA) - {date_str}**\n\n{ai_text}"
            
        except Exception as e:
            logging.error(f"Erreur Groq : {e}")
            report = f"📈 **FLASH MARCHÉS - {date_str}**\n\n⚠️ *Erreur lors de la génération IA, passage en mode de secours.*\nAnalyse stable sur les supports mondiaux, surveillance sur TradingView."
    else:
        report = (
            f"📈 **FLASH MARCHÉS - {date_str}**\n\n"
            "🎯 **Profil :** Équilibré / Prudent\n\n"
            "• **Bitcoin** : [ACHAT PRUDENT]\n• **S&P 500 & CAC 40** : [HOLD]\n"
            "💡 *Note : Ajoute ta clé GROQ_API_KEY sur Railway pour débloquer les analyses 100% dynamiques par l'IA !*"
        )
    
    # Correction effectuée ici (parse_mode au lieu de parse_Mime)
    await update.message.reply_text(report, parse_mode="Markdown")

    # Notion sync (optionnel)
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
                    "Name": {"title": [{"text": {"content": f"Bilan Flash IA - {date_str}"}}]},
                    "Date": {"date": {"start": datetime.now().isoformat()}}
                }
            }
            requests.post("https://api.notion.com/v1/pages", json=payload, headers=headers)
        except Exception as e:
            logging.error(f"Erreur lors de la sync Notion : {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère le clic sur le bouton permanent."""
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Le bot est en route avec l'IA...")
    app.run_polling()

if __name__ == '__main__':
    main()
