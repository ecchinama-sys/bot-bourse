import time
import random
import requests
from datetime import datetime
from groq import Groq
import os

# --- TES CLES API (Récupérées depuis les variables d'environnement de l'hébergeur) ---
GROQ_API_KEY = "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"          
TELEGRAM_BOT_TOKEN = "8820955818:AAGtMB-LwbJSw7CS8uYWIMVVLkT-Lvkkd-s"  
TELEGRAM_CHAT_ID = "6736922134"      
NOTION_API_KEY = "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"
NOTION_DATABASE_ID = "https://app.notion.com/p/3c2ff48f1aed803db912e3f32650c7a5?v=3c2ff48f1aed80499920000c65daf439&source=copy_link"

client = Groq(api_key=GROQ_API_KEY)
SELECTED_MODEL = "llama-3.1-70b-versatile"

def add_to_notion(title, content):
    url = "https://api.notion.com/v1/pages"
    date_iso = datetime.now().strftime("%Y-%m-%d")
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
            "Date": {"date": {"start": date_iso}}
        },
        "children": [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": content[:2000]}}]}}]
    }
    requests.post(url, headers=headers, json=data)

def generer_analyse():
    angles = [
        "Focus sur la tech, les valeurs de croissance et l'intelligence artificielle sur les marchés.",
        "Focus sur l'inflation, les décisions des banques centrales (FED, BCE) et les taux d'intérêt.",
        "Focus sur les matières premières (pétrole, or) et les mouvements géopolitiques mondiaux.",
        "Focus sur les résultats d'entreprises, les actions en forte hausse/baisse et les conseils de rotation sectorielle."
    ]
    prompt = (
        f"Tu es un expert analyste financier renommé. Rédige un flash boursier et financier complet "
        f"en suivant STRICTEMENT cet ordre : 1. Les faits marquants, 2. Les indicateurs clés, "
        f"3. Ton analyse d'expert et ton avis tranché à la fin. Angle : {random.choice(angles)}"
    )
    completion = client.chat.completions.create(model=SELECTED_MODEL, messages=[{"role": "user", "content": prompt}])
    return str(completion.choices[0].message.content)

def envoyer_telegram():
    message = generer_analyse()
    titre = f"Flash Finance & Bourse - {datetime.now().strftime('%d/%m/%Y')}"
    add_to_notion(titre, message)
    
    url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"📈 *{titre}*\n\n{message}",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [[{"text": "🔄 Régénérer un autre article", "callback_data": "regen"}]]
        }
    }
    requests.post(url_telegram, json=payload)

def ecouter_telegram():
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
                        if query["data"] == "regen":
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": query["id"], "text": "Génération d'une nouvelle analyse..."})
                            envoyer_telegram()
        except Exception as e:
            print(f"Erreur : {e}")
            time.sleep(5)

if __name__ == "__main__":
    ecouter_telegram()
