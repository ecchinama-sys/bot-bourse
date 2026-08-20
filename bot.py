import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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

def get_menu_keyboard():
    """Génère le menu principal sous forme de boutons interactifs."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Lancer le Flash Marché", callback_data="launch_flash")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialise le bot et affiche le message d'accueil avec le bouton principal."""
    await update.message.reply_text(
        "🤖 **Boursorama One - Assistant IA**\n"
        "Prêt pour ton analyse universelle.\n\n"
        "💡 *Astuce :* Clique sur le bouton ci-dessous pour lancer un flash global, ou tape directement le nom de n'importe quel actif (ex: *Bitcoin, Nvidia, Or...*) pour une analyse sur mesure.", 
        reply_markup=get_menu_keyboard(),
        parse_mode="Markdown"
    )

async def flash_analysis(update_or_query, context, is_callback=True):
    """Génère le flash global multi-marchés de manière compacte."""
    if is_callback:
        query = update_or_query
        await query.answer()
        await query.edit_message_text(text="🔍 Analyse globale multi-marchés en cours...")
        target_func = query.edit_message_text
    else:
        sent_msg = await update_or_query.reply_text("🔍 Analyse globale multi-marchés en cours...")
        target_func = sent_msg.edit_text

    if not groq_client:
        await target_func(text="⚠️ Erreur : Clé GROQ_API_KEY non trouvée.", reply_markup=get_menu_keyboard())
        return

    try:
        prompt = (
            "Fais un résumé macroéconomique ultra-concis (maximum 2500 caractères) des tendances actuelles "
            "pour : Bitcoin, S&P 500, CAC 40, Tesla, Apple, Ethereum, Or, Nvidia. "
            "Sois direct et va à l'essentiel pour tenir dans un seul message Telegram."
        )
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        report = chat_completion.choices[0].message.content

        # Boutons de zoom et de retour au menu
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
            ],
            [
                InlineKeyboardButton("🏠 Menu Principal", callback_data="back_to_menu")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        full_text = f"📊 **FLASH MARCHÉS GLOBAL**\n\n{report}\n\n*Clique sur un actif pour un zoom détaillé :*"
        
        # Sécurité longueur
        if len(full_text) > 4000:
            full_text = full_text[:3900] + "\n\n...(Rapport abrégé pour affichage optimal)"

        await target_func(text=full_text, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        await target_func(text=f"⚠️ Erreur technique IA :\n{str(e)}", reply_markup=get_menu_keyboard())

async def analyze_specific_asset(update_or_query, context, asset_name, is_callback=True):
    """Analyse un actif spécifique avec avis clair (Achat/Vente/Neutre)."""
    if is_callback:
        query = update_or_query
        await query.answer()
        await query.edit_message_text(text=f"🔍 Analyse de {asset_name} en cours...")
        target_func = query.edit_message_text
    else:
        sent_msg = await update_or_query.reply_text(f"🔍 Analyse de {asset_name} en cours...")
        target_func = sent_msg.edit_text

    try:
        prompt = (
            f"Fais un point d'analyse de marché pour l'actif : {asset_name}. "
            "Donne clairement une perspective de positionnement parmi ces choix : [ACHAT FORT / ACHAT / NEUTRE / VENTE / VENTE FORTE], "
            "puis explique brièvement la tendance, les niveaux clés et un avertissement de gestion des risques."
        )

        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        detail_report = chat_completion.choices[0].message.content

        keyboard = [
            [InlineKeyboardButton("📈 Relancer un Flash", callback_data="launch_flash")],
            [InlineKeyboardButton("🏠 Menu Principal", callback_data="back_to_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        full_text = f"🎯 **ANALYSE & SIGNAL : {asset_name.upper()}**\n\n{detail_report}"
        
        if len(full_text) > 4000:
            full_text = full_text[:3900] + "\n\n...(Ajusté pour affichage)"

        await target_func(text=full_text, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        await target_func(text=f"⚠️ Erreur lors de l'analyse : {str(e)}", reply_markup=get_menu_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère l'ensemble des clics sur les boutons interactifs de manière sécurisée."""
    query = update.callback_query
    data = query.data
    
    if data == "back_to_menu":
        await query.answer()
        await query.edit_message_text(
            text="🤖 **Boursorama One - Assistant IA**\n\nChoisis une option ou tape le nom d'un actif :",
            reply_markup=get_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    if data == "launch_flash":
        await flash_analysis(query, context, is_callback=True)
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

    selected_asset = asset_map.get(data)
    if selected_asset:
        await analyze_specific_asset(query, context, selected_asset, is_callback=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la saisie libre d'actifs par l'utilisateur."""
    text = update.message.text
    if not groq_client:
        await update.message.reply_text("⚠️ Erreur : Clé GROQ_API_KEY non trouvée.", reply_markup=get_menu_keyboard())
        return
    await analyze_specific_asset(update, context, asset_name=text, is_callback=False)

def main():
    if not TELEGRAM_TOKEN:
        print("Erreur : TELEGRAM_TOKEN manquant")
        return

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("flash", lambda u, c: flash_analysis(u.message, c, is_callback=False)))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Le bot universel est en ligne.")
    app.run_polling()

if __name__ == '__main__':
    main()
