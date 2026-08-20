import os
import random
import requests
from datetime import datetime
from groq import Groq

# --- TES CLES API ---
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8820955818:AAGtMB-LwbJSw7CS8uYWIMVVLkT-Lvkkd-s"
TELEGRAM_CHAT_ID = "6736922134"
NOTION_API_KEY = "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"
NOTION_DATABASE_ID = "https://app.notion.com/p/3c2ff48f1aed803db912e3f32650c7a5?v=3c2ff48f1aed80499920000c65daf439&source=copy_link"

# Initialisation Groq et sélection automatique du modèle
client = Groq(api_key=GROQ_API_KEY)
models_list = client.models.list().data
SELECTED_MODEL = next((m.id for m in models_list if "llama" in m.id.lower() and "guard" not in m.id.lower()), models_list[0].id)

# Fonction d'envoi vers Notion
def add_to_notion(title, content):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {"Name": {"title": [{"text": {"content": title}}]}},
        "children": [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"type": "text", "text": {"content": content[:2000]}}]}}]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code

# Fonction principale de génération du flash de minuit
def tache_flash_bourse():
    print("\n🌙 Minuit : Lancement de la génération automatique du flash boursier...")
    
    angles_possibles = [
        "Focus sur la tech, les valeurs de croissance et l'intelligence artificielle sur les marchés.",
        "Focus sur l'inflation, les décisions des banques centrales (FED, BCE) et les taux d'intérêt.",
        "Focus sur les matières premières (pétrole, or) et les mouvements géopolitiques mondiaux.",
        "Focus sur les résultats d'entreprises, les actions en forte hausse/baisse et les conseils de rotation sectorielle."
    ]
    angle_du_jour = random.choice(angles_possibles)
    
    prompt = f"""Tu es un analyste financier senior. Rédige un flash d'actualité boursière percutant et diversifié.
    
Angle prioritaire pour cette édition : {angle_du_jour}

Format attendu :
1. 📈 **Tendance & Contexte Général** : Bref état d'esprit des places financières (CAC40, Wall Street, tendances macro).
2. 📰 **Actualités & Thématiques Clés** : 3 ou 4 actualités boursières ou économiques variées et distinctes.
3. 💡 **Le Regard de l'Expert / À Surveiller** : Un indicateur ou un événement stratégique à suivre de près.

Style : Professionnel, direct, percutant et lisible sur mobile."""

    # Génération IA
    completion = client.chat.completions.create(
        model=SELECTED_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    message_ia = str(completion.choices[0].message.content)
    
    # Enregistrement et Envoi
    date_du_jour = datetime.now().strftime("%d/%m/%Y")
    titre_page = f"Flash Bourse & Actu - {date_du_jour}"
    status_notion = add_to_notion(titre_page, message_ia)
    
    url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"🌙 *Flash Automatique de Minuit*\n\n📰 *{titre_page}* \n\n{message_ia}",
        "parse_mode": "Markdown"
    }
    res_tg = requests.post(url_telegram, json=payload)
    
    if status_notion == 200 and res_tg.status_code == 200:
        print(f"✅ Flash de minuit envoyé avec succès sur Notion et Telegram !")
    else:
        print(f"⚠️ Erreur lors de l'envoi automatique.")

tache_flash_bourse()
