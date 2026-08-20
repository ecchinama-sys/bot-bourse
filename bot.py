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
        "🤖 **Boursorama One - Assistant IA**\n"
        "Prêt pour ton analyse universelle.\n\n"
        "💡 *Astuce :* Tu peux aussi taper directement le nom de n'importe quel actif (ex: *Ethereum, Nvidia, Or, TotalEnergies...*) dans le chat pour que je l'analyse !", 
        reply_markup=reply_markup, 
        parse_mode="Markdown"
    )

async def flash_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Génère le flash global avec des boutons de zoom interactifs."""
    await update.message.reply_text("🔍 Analyse globale multi-marchés en cours...")
    
    if not groq_client:
        await update.message.reply_text("⚠️ Erreur : Clé GROQ_API_KEY non trouvée sur le serveur.")
        return

    try:
        prompt = (
            "Fais un résumé ultra-bref de la tendance globale pour : "
            "Bitcoin, S&P 500, CAC 40, Tesla, Apple, Ethereum, Or, Nvidia. "
            "Donne une vue d'ensemble rapide."
        )
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        report = chat_completion.choices[0].message.content

        # Boutons interactifs élargis
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
                InlineKeyboardButton("🥇 Or (Gold)", callback_data="zoom_gold")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📊 **FLASH MARCHÉS UNIVERSEL**\n\n{report}\n\n*Clique sur un actif ci-dessous ou tape son nom directement pour un zoom détaillé :*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        error_msg = f"⚠️ Erreur technique IA :\n{str(e)}"
        logging.error(error_msg)
        await update.message.reply_text(error_msg)

async def analyze_specific_asset(update_or_query, context, asset_name, is_callback=True):
    """Fonction générique pour analyser n'importe quel actif demandé (bouton ou texte libre)."""
    
    if is_callback:
        query = update_or_query
        await query.answer()
        await query.edit_message_text(text=f"🔍 Analyse approfondie de {asset_name} en cours...")
        target_message = query.edit_message_text
    else:
        message = update_or_query
        sent_msg = await message.reply_text(f"🔍 Analyse sur mesure de {asset_name} en cours...")
        target_message = sent_msg.edit_text

    try:
        prompt = (
            f"Agis en expert financier. Fais une analyse technique détaillée pour l'actif : {asset_name}. "
            "Donne un signal clair ([ACHAT], [HOLD], [ATTENTE]), les niveaux clés (supports/résistances) "
            "et une explication prudente. Rappelle de vérifier TradingView."
        )

        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        detail_report = chat_completion.choices[0].message.content

        keyboard = [[InlineKeyboardButton("🔙 Retour au menu", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await target_message(
            text=f"🎯 **ANALYSE : {asset_name.upper()}**\n\n{detail_report}",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        await target_message(text=f"⚠️ Erreur lors de l'analyse : {str(e)}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les clics sur les boutons interactifs."""
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
        await analyze_specific_asset(query, context, selected_asset, is_callback=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "📈 Lancer le Flash Marché":
        await flash_analysis(update, context)
    else:
        # Si tu écris n'importe quel autre mot/actif dans le chat, le bot l'interpréte comme une demande d'analyse !
        if not groq_client:
            await update.message.reply_text("⚠️ Erreur : Clé GROQ_API_KEY non trouvée.")
            return
        await analyze_specific_asset(update.message, context, text, is_callback=False)

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
