import os
import logging
import re
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

def clean_text_for_telegram(text):
    """Supprime les symboles de titres Markdown (#) pour un affichage propre."""
    if not text:
        return ""
    # Retire les dièses de titres en début de ligne (ex: ### Titre -> Titre)
    text = re.sub(r'^[#]+\s*', '', text, flags=re.MULTILINE)
    # Retire les dièses au milieu si l'IA en met
    text = text.replace('#', '')
    return text

def get_menu_keyboard():
    """Génère le menu principal avec l'unique bouton pour lancer le flash."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Lancer le Flash Marché Global", callback_data="launch_flash")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialise le bot et affiche l'accueil."""
    await update.message.reply_text(
        "🤖 *Boursorama One - Assistant IA*\n"
        "Prêt pour ton analyse universelle.\n\n"
        "💡 *Astuce :* Clique sur le bouton ci-dessous pour générer ton flash complet, ou tape directement le nom de n'importe quel actif pour une recherche ciblée.", 
        reply_markup=get_menu_keyboard(),
        parse_mode="Markdown"
    )

async def flash_analysis(update_or_query, context, is_callback=True):
    """Génère un flash complet, aéré, sans dièses, avec résumé et orientation claire."""
    if is_callback:
        query = update_or_query
        await query.answer()
        await query.edit_message_text(text="🔍 Génération du flash complet des marchés en cours...")
        target_func = query.edit_message_text
    else:
        sent_msg = await update_or_query.reply_text("🔍 Génération du flash complet des marchés en cours...")
        target_func = sent_msg.edit_text

    if not groq_client:
        await target_func(text="⚠️ Erreur : Clé GROQ_API_KEY non trouvée.", reply_markup=get_menu_keyboard())
        return

    try:
        prompt = (
            "Rédige un flash boursier et macroéconomique complet et aéré pour ces actifs : "
            "Bitcoin, Ethereum, S&P 500, CAC 40, Tesla, Apple, Nvidia, Or. "
            "Règles de mise en forme strictes :\n"
            "- N'utilise JAMAIS les symboles dièse (#) ou de titres Markdown.\n"
            "- N'utilise PAS de tableaux Markdown (| |), fais uniquement des paragraphes aérés.\n"
            "- Utilise des emojis pour chaque actif.\n"
            "- Pour chaque actif, donne une indication claire : [Posture : ACHAT / VENTE / NEUTRE].\n"
            "- Termine obligatoirement par une section 'RÉSUMÉ STRATÉGIQUE GLOBAL' qui résume s'il faut privilégier les achats ou la prudence sur la période."
        )
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        report = clean_text_for_telegram(chat_completion.choices[0].message.content)

        keyboard = [[InlineKeyboardButton("🔄 Relancer un Flash", callback_data="launch_flash")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        full_text = f"📊 *FLASH MARCHÉS & ORIENTATIONS*\n\n{report}"
        
        if len(full_text) > 4000:
            full_text = full_text[:3900] + "\n\n...(Rapport ajusté pour affichage)"

        await target_func(text=full_text, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        await target_func(text=f"⚠️ Erreur technique IA :\n{str(e)}", reply_markup=get_menu_keyboard())

async def analyze_specific_asset(update_or_query, context, asset_name, is_callback=True):
    """Analyse un actif spécifique en cas de saisie libre."""
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
            f"Analyse l'actif : {asset_name}.\n"
            "Rédige une réponse aérée, sans dièse (#) ni tableaux.\n"
            "Commence par : 'Posture : [ACHAT / VENTE / NEUTRE]'\n"
            "Puis détaille la tendance, les niveaux clés et les risques."
        )

        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        detail_report = clean_text_for_telegram(chat_completion.choices[0].message.content)

        keyboard = [[InlineKeyboardButton("🏠 Menu Principal", callback_data="back_to_menu")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        full_text = f"🎯 *ANALYSE : {asset_name.upper()}*\n\n{detail_report}"
        
        if len(full_text) > 4000:
            full_text = full_text[:3900] + "\n\n...(Ajusté pour affichage)"

        await target_func(text=full_text, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        await target_func(text=f"⚠️ Erreur lors de l'analyse : {str(e)}", reply_markup=get_menu_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les actions des boutons."""
    query = update.callback_query
    data = query.data
    
    if data == "back_to_menu":
        await query.answer()
        await query.edit_message_text(
            text="🤖 *Boursorama One - Assistant IA*\n\nClique ci-dessous pour lancer ton flash complet :",
            reply_markup=get_menu_keyboard(),
            parse_mode="Markdown"
        )
        return

    if data == "launch_flash":
        await flash_analysis(query, context, is_callback=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère la saisie textuelle libre d'un actif."""
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
