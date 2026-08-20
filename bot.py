import os
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
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
    """Initialise le bot avec le clavier permanent."""
    keyboard = [["📈 Lancer le Flash Marché"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "🤖 **Boursorama One - Assistant IA**\nPrêt pour ton analyse interactive.", 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def flash_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Génère le flash global avec des boutons de zoom interactifs."""
    await update.message.reply_text("🔍 Analyse globale en cours...")
    
    if not groq_client:
        await update.message.reply_text("⚠️ Erreur : Clé GROQ_API_KEY non trouvée sur le serveur.")
        return

    try:
        prompt = (
            "Fais un résumé ultra-bref (en quelques lignes) de la tendance globale pour : "
            "Bitcoin, S&P 500, CAC 40, Tesla, Apple. "
            "Donne une vue d'ensemble rapide."
        )
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        report = chat_completion.choices[0].message.content

        # Création des boutons interactifs sous le message
        keyboard = [
            [
                InlineKeyboardButton("🪙 Bitcoin", callback_data="zoom_btc"),
                InlineKeyboardButton("📊 S&P 500", callback_data="zoom_sp500")
            ],
            [
                InlineKeyboardButton("📉 CAC 40", callback_data="zoom_cac40"),
                InlineKeyboardButton("🚗 Tesla", callback_data="zoom_tsla")
            ],
            [
                InlineKeyboardButton("🍏 Apple", callback_data="zoom_aapl")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📊 **FLASH MARCHÉS GLOBAL**\n\n{report}\n\n*Clique sur un actif ci-dessous pour un zoom détaillé :*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        error_msg = f"⚠️ Erreur technique IA :\n{str(e)}"
        logging.error(error_msg)
        await update.message.reply_text(error_msg)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les clics sur les boutons interactifs (inline)."""
    query = update.callback_query
    await query.answer() # Empêche le bouton de tourner en rond sur Telegram

    # Associer chaque bouton à son actif
    asset_map = {
        "zoom_btc": "Bitcoin (BTC)",
        "zoom_sp500": "S&P 500",
        "zoom_cac40": "CAC 40",
        "zoom_tsla": "Tesla (TSLA)",
        "zoom_aapl": "Apple (AAPL)"
    }

    selected_asset = asset_map.get(query.data)
    if not selected_asset:
        return

    await query.edit_message_text(text=f"🔍 Analyse approfondie de {selected_asset} en cours...")

    try:
        prompt = (
            f"Fais une analyse technique détaillée et spécifique pour l'actif : {selected_asset}. "
            "Donne un signal clair ([ACHAT], [HOLD], [ATTENTE]), les niveaux clés (supports/résistances) "
            "et une explication prudente. Rappelle de vérifier TradingView."
        )

        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        detail_report = chat_completion.choices[0].message.content

        # On renvoie le rapport détaillé avec un bouton pour revenir en arrière ou relancer
        keyboard = [[InlineKeyboardButton("🔙 Retour au menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"🎯 **ZOOM : {selected_asset}**\n\n{detail_report}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        await query.edit_message_text(text=f"⚠️ Erreur lors de l'analyse de l'actif : {str(e)}")

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
    app.add_handler(CallbackQueryHandler(button_callback)) # Gestionnaire pour les boutons cliquables

    print("Le bot est en ligne avec les boutons interactifs.")
    app.run_polling()

if __name__ == '__main__':
    main()
