import os
import time
import requests
from groq import Groq

# Récupération des clés API depuis les variables d'environnement Railway
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

client = Groq(api_key=GROQ_API_KEY)

def generer_analyse_financiere():
    """Génère l'analyse boursière via l'IA Groq"""
    prompt = "Rédige un flash d'analyse financière court et percutant sur les marchés du jour avec les tendances clés."
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": prompt}
        ],
        model="llama-3.1-70b-versatile",
    )
    return chat_completion.choices[0].message.content

def enregistrer_sur_notion(analyse):
    """Enregistre l'analyse générée dans ta base de données Notion"""
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-02-28"
    }
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Titre": {
                "title": [{"text": {"content": "Flash Boursier Automatique"}}]
            }
        },
        "children": [
            {
                "object": "block",
                "paragraph": {
                    "rich_text": [{"text": {"content": analyse}}]
                }
            }
        ]
    }
    requests.post(url, headers=headers, json=data)

def envoyer_telegram():
    """Génère l'analyse, l'envoie sur Notion, puis l'envoie sur Telegram avec le bouton Régénérer"""
    print("🔄 Génération d'une nouvelle analyse en cours...")
    analyse = generer_analyse_financiere()
    
    # Enregistrement Notion
    enregistrer_sur_notion(analyse)
    
    # Ajout du bouton interactif "Régénérer"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": analyse,
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🔄 Régénérer", "callback_data": "regen"}]
            ]
        }
    }
    requests.post(url, json=payload)
    print("✅ Analyse envoyée sur Telegram et enregistrée sur Notion !")

def ecouter_telegram():
    """Boucle d'écoute continue 24h/24 pour intercepter les clics sur les boutons"""
    print("🤖 Bot démarré en écoute continue 24h/24...")
    offset = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=30"
            if offset:
                url += f"&offset={offset}"
            
            response = requests.get(url).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "callback_query" in update:
                        query = update["callback_query"]
                        print(f"👉 Clic détecté ! Donnée : {query['data']}")
                        if query["data"] == "regen":
                            # Valide le clic sur le bouton pour stopper l'animation de chargement sur Telegram
                            requests.post(
                                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", 
                                json={"callback_query_id": query["id"], "text": "Génération d'une nouvelle analyse..."}
                            )
                            envoyer_telegram()
        except Exception as e:
            print(f"Erreur : {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("🚀 Lancement du bot...")
    # Envoie un premier message dès le démarrage, puis lance la boucle d'écoute permanente
    envoyer_telegram()
    ecouter_telegram()
