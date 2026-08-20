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
    """Initialise le bot et force l'affichage du clavier permanent."""
    keyboard = [["📈 Lancer le Flash Marché"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
    await update.message.reply_text(
        "🤖 **Boursorama One - Assistant IA**\n"
        "Prêt pour ton analyse universelle.\n\n"
        "💡 *Astuce :* Tu peux taper le nom de n'importe quel actif (ex: *Bitcoin, Nvidia, Or...*) pour une analyse sur mesure.", 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def flash_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Génère le flash global multi-marchés."""
    await update.message.reply_text("🔍 Analyse globale multi-marchés en cours...")
    
    if not groq_client:
        await update.message.reply_text("⚠️ Erreur : Clé GROQ_API_KEY non trouvée.")
        return

    try:
        prompt = (
            "En tant qu'assistant de synthèse macroéconomique, donne un résumé court des tendances "
            "pour : Bitcoin, S&P 500, CAC 40, Tesla, Apple, Ethereum, Or, Nvidia."
        )
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-70b-versatile",
        )
        report = chat_completion.choices[0].message.content

        # Boutons interactifs (inline) sous le message
        keyboard = [
            [
                InlineKeyboardButton("🪙 Bitcoin", callback_data="zoom_btc"),
                InlineKeyboardButton("💎 Ethereum", callback_data="zoom_eth")
            ],
            [
                InlineKeyboardButton("📊 S&P 500", callback_data="zoom_sp500"),
                InlineKeyboardButton("📉 CAC 40", callback_data="zoom_cac40")
            ],
            [
                InlineKeyboardButton("🚗 Tesla", callback_data="zoom_tsla"),
                InlineKeyboardButton("🍏 Apple", callback_data="zoom_aapl")
            ],
            [
                InlineKeyboardButton("💻 Nvidia", callback_data="zoom_nvda"),
                InlineKeyboardButton("🥇 Or", callback_data="zoom_gold")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📊 **FLASH MARCHÉS GLOBAL**\n\n{report}\n\n*Clique sur un actif pour un zoom détaillé :*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        await update.message.reply_text(f"⚠️ Erreur technique IA :\n{str(e)}")

async def analyze_specific_asset(update_or_query, context, asset_name, is_callback=True):
    """Analyse un actif spécifique de manière structurée."""
    if is_callback:
        query = update_or_query
        await query.answer()
        await query.edit_message_text(text=f"🔍 Analyse de {asset_name} en cours...")
        target_message = query.edit_message_text
    else:
        sent_msg = await update_or_query.reply_text(f"🔍 Analyse de {asset_name} en cours...")
        target_message = sent_msg.edit_text

    try:
        prompt = (
            f"Analyse l'actif financier : {asset_name}. "
            "Donne une perspective de marché, les niveaux clés et un avis de gestion prudent. "
            "Rappelle de vérifier TradingView."
        )

        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-70b-versatile",
        )
        detail_report = chat_completion.choices[0].message.content

        keyboard = [[InlineKeyboardButton("🔙 Retour au menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        if len(detail_report) > 4000:
            detail_report = detail_report[:4000] + "\n\n...(coupé car trop long)"

        await target_message(
            text=f"🎯 **ANALYSE : {asset_name.upper()}**\n\n{detail_report}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        await target_message(text=f"⚠️ Erreur lors de l'analyse : {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les clics sur les boutons interactifs (inline)."""
    query = update.callback_query
    
    if query.data == "back_to_menu":
        await query.answer()
        await query.edit_message_text(text="✅ Menu principal. Clique sur ton bouton en bas pour relancer un Flash global.")
        return

    asset_map = {
        "zoom_btc": "Bitcoin (BTC)",
        "zoom_eth": "Ethereum (ETH)",
        "zoom_sp500": "S&P 500",
        "zoom_cac40": "CAC 40",
        "zoom_tsla": "Tesla (TSLA)",
        "zoom_aapl": "Apple (AAPL)",
        "zoom_nvda": "Nvidia (NVDA)",
        "zoom_gold": "Or (Gold)"
    }

    selected_asset = asset_map.get(query.data)
    if selected_asset:
        await analyze_specific_asset(update_or_query=query, context=context, asset_name=selected_asset, is_callback=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère le bouton permanent et la saisie libre d'actifs."""
    text = update.message.text
    
    if text == "📈 Lancer le Flash Marché":
        await flash_analysis(update, context)
    else:
        if not groq_client:
            await update.message.reply_text("⚠️ Erreur : Clé GROQ_API_KEY non trouvée.")
            return
        await analyze_specific_asset(update_or_query=update.message, context=context, asset_name=text, is_callback=False)

def main():
    if not TELEGRAM_TOKEN:
        print("Erreur : TELEGRAM_TOKEN manquant")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Le bot universel est en ligne.")
    app.run_polling()

if __name__ == '__main__':
    main()
