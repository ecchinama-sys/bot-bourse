import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from groq import Groq

# Configuration des logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Récupération des clés
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialisation Groq
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialise le bot avec le bouton permanent."""
    keyboard = [["📈 Lancer le Flash Marché"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🤖 **Boursorama One - Assistant IA**\nPrêt pour ton analyse quotidienne.", 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def flash_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Analyse dynamique via Groq avec le modèle actuel."""
    await update.message.reply_text("🔍 Analyse en cours par l'IA...")
    
    if not groq_client:
        await update.message.reply_text("⚠️ Erreur : Clé GROQ_API_KEY non trouvée sur le serveur.")
        return

    try:
        prompt = (
            "Analyse en expert financier pour : Bitcoin, S&P 500, CAC 40, Tesla, Apple. "
            "Donne pour chaque actif : un signal ([ACHAT], [HOLD], [ATTENTE]) "
            "et une phrase d'explication prudente. "
            "Rappelle de vérifier TradingView."
        )
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b", # Modèle actif et performant sur l'infrastructure Groq
        )
        report = chat_completion.choices[0].message.content
        await update.message.reply_text(report, parse_mode="Markdown")

    except Exception as e:
        error_msg = f"⚠️ Erreur technique IA :\n{str(e)}"
        logging.error(error_msg)
        await update.message.reply_text(error_msg)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "📈 Lancer le Flash Marché":
        await flash_analysis(update, context)

def main():
    if not TELEGRAM_TOKEN:
        print("Erreur : TELEGRAM_TOKEN manquant")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Le bot est en ligne avec Groq.")
    app.run_polling()

if __name__ == '__main__':
    main()
