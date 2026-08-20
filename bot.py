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
    """Nettoie le texte pour éviter les erreurs de balises Markdown."""
    if not text:
        return ""
    # Retire les dièses de titres
    text = re.sub(r'^[#]+\s*', '', text, flags=re.MULTILINE)
    text = text.replace('#', '')
    return text

async def send_long_message(target_func, text, reply_markup=None):
    """Découpe et envoie un message s'il dépasse la limite Telegram (4096 caractères)."""
    max_length = 4000
    if len(text) <= max_length:
        await target_func(text=text, reply_markup=reply_markup)
        return

    # Découpage par morceaux propres
    chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    for index, chunk in enumerate(chunks):
        # On n'attache les boutons qu'au dernier message
        markup = reply_markup if index == len(chunks) - 1 else None
        if index == 0:
            await target_func(text=chunk, reply_markup=markup)
        else:
            # Pour les messages suivants, on utilise context.bot.send_message si c'est un objet query ou message
            pass

def get_menu_keyboard():
    """Génère le menu principal avec l'unique bouton pour lancer le flash."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📈 Lancer le Flash Marché Global (Tout)", callback_data="launch_flash")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initialise le bot et affiche l'accueil."""
    await update.message.reply_text(
        "🤖 Boursorama One - Assistant IA\n"
        "Prêt pour ton analyse universelle de tous les marchés.\n\n"
        "💡 Astuce : Clique ci-dessous pour un flash complet et global, ou tape le nom de n'importe quel actif pour une recherche ciblée.", 
        reply_markup=get_menu_keyboard()
    )

async def flash_analysis(update_or_query, context, is_callback=True):
    """Génère un flash complet couvrant l'ensemble des marchés mondiaux sans risque de plantage."""
    if is_callback:
        query = update_or_query
        await query.answer()
        await query.edit_message_text(text="🔍 Analyse globale de TOUS les marchés en cours...")
        target_func = query.edit_message_text
    else:
        sent_msg = await update_or_query.reply_text("🔍 Analyse globale de TOUS les marchés en cours...")
        target_func = sent_msg.edit_text

    if not groq_client:
        await target_func(text="⚠️ Erreur : Clé GROQ_API_KEY non trouvée.", reply_markup=get_menu_keyboard())
        return

    try:
        prompt = (
            "Rédige un flash boursier et macroéconomique concis, synthétique et aéré couvrant tous les grands secteurs : "
            "les cryptomonnaies majeures, les indices boursiers (USA, Europe), les actions technologiques phares, "
            "les matières premières (or, pétrole) et le forex.\n"
            "Règles strictes :\n"
            "- N'utilise JAMAIS les symboles dièse (#).\n"
            "- N'utilise PAS de tableaux (| |).\n"
            "- Utilise des emojis.\n"
            "- Pour chaque grande catégorie, donne une indication claire : [Posture : ACHAT / VENTE / NEUTRE].\n"
            "- Termine par une section 'RÉSUMÉ STRATÉGIQUE GLOBAL'."
        )
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
        )
        report = clean_text_for_telegram(chat_completion.choices[0].message.content)

        keyboard = [[InlineKeyboardButton("🔄 Relancer un Flash Global", callback_data="launch_flash")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        full_text = f"📊 FLASH MONDIAL DE TOUS LES MARCHÉS\n\n{report}"
        
        # Envoi sécurisé avec gestion de la longueur (sans parse_mode pour éliminer les erreurs de syntaxe)
        if len(full_text) > 4000:
            full_text = full_text[:3950] + "\n\n...(Rapport tronqué pour optimiser l'affichage)"

        await target_func(text=full_text, reply_markup=reply_markup)

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
            f"Analyse l'actif ou le marché : {asset_name}.\n"
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

        full_text = f"🎯 ANALYSE : {asset_name.upper()}\n\n{detail_report}"
        
        if len(full_text) > 4000:
            full_text = full_text[:3950] + "\n\n...(Ajusté pour affichage)"

        await target_func(text=full_text, reply_markup=reply_markup)

    except Exception as e:
        await target_func(text=f"⚠️ Erreur lors de l'analyse : {str(e)}", reply_markup=get_menu_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les actions des boutons."""
    query = update.callback_query
    data = query.data
    
    if data == "back_to_menu":
        await query.answer()
        await query.edit_message_text(
            text="🤖 Boursorama One - Assistant IA\n\nClique ci-dessous pour lancer ton flash complet de tous les marchés :",
            reply_markup=get_menu_keyboard()
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
