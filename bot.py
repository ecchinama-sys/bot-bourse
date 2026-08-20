import os
import time
import random
import requests
import urllib.request
import xml.etree.ElementTree as ET
from groq import Groq

# Récupération des clés API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

client = Groq(api_key=GROQ_API_KEY)

def recuperer_actualites_marches():
    """Récupère et mélange des titres depuis plusieurs flux financiers pour garantir la variété"""
    flux = [
        "https://finance.yahoo.com/news/rssindex",
        "https://www.reutersagency.com/feed/?taxonomy=categories&post_type=best-topics&term=financial-markets",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"
    ]
    
    tous_les_titres = []
    
    for url in flux:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                for item in root.findall('.//item')[:3]: # On prend les 3 derniers de chaque
                    titre = item.find('title')
                    if titre is not None and titre.text:
                        tous_les_titres.append(titre.text)
        except Exception as e:
            print(f"Erreur flux {url}: {e}")
    
    # Mélange aléatoire pour que l'analyse change à chaque fois
    random.shuffle(tous_les_titres)
    return "\n".join([f"- {t}" for t in tous_les_titres[:6]])

def generer_analyse_financiere():
    print("📰 Récupération des actualités (multi-sources)...")
    actus_du_jour = recuperer_actualites_marches()
    
    angles = [
        "Focus sur la macroéconomie et les décisions des banques centrales.",
        "Analyse de la psychologie des marchés et de la volatilité actuelle.",
        "Perspective tactique : opportunités à court terme et signaux techniques.",
        "Vision prudente : analyse des risques et zones de support."
    ]
    angle_choisi = random.choice(angles)
    
    prompt = f"""
    Voici les actualités financières du jour :
    {actus_du_jour}
    
    Consigne : {angle_choisi}
    Rédige un flash financier court, percutant, dynamique avec des emojis (📈, 📉, 💡, 💰, 🚀). Pas de sources, juste une analyse pro et directe.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-120b",
        temperature=0.95, # Très créatif
    )
    return chat_completion.choices[0].message.content

def enregistrer_sur_notion(analyse):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-02-28"
    }
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {"Titre": {"title": [{"text": {"content": "Flash Boursier RAG Multi-Sources"}}]}},
        "children": [{"object": "block", "paragraph": {"rich_text": [{"text": {"content": analyse}}]}}]
    }
    requests.post(url, headers=headers, json=data)

def envoyer_telegram():
    print("🔄 Génération en cours...")
    analyse = generer_analyse_financiere().replace("*", "")
    enregistrer_sur_notion(analyse)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": analyse,
        "reply_markup": {"inline_keyboard": [[{"text": "🔄 Régénérer", "callback_data": "regen"}]]}
    }
    requests.post(url, json=payload)

def ecouter_telegram():
    print("🤖 Bot en écoute...")
    offset = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=30&offset={offset}" if offset else f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=30"
            response = requests.get(url).json()
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "callback_query" in update:
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": update["callback_query"]["id"]})
                        envoyer_telegram()
                    elif "message" in update and update["message"].get("text") == "/start":
                        envoyer_telegram()
        except Exception as e:
            print(f"Erreur : {e}")
            time.sleep(5)

if __name__ == "__main__":
    envoyer_telegram()
    ecouter_telegram()
