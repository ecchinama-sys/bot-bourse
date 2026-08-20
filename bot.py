import os
import time
import random
import requests
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from groq import Groq

# Récupération des clés API
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

client = Groq(api_key=GROQ_API_KEY)

# Liste des mots-clés sensibles pour déclencher une alerte
MOTS_CLES_ALERTES = ["inflation", "fed", "bce", "crise", "crash", "taux", "guerre", "tensions", "secousse"]

def recuperer_actualites_marches():
    """Récupère, mélange les flux et détecte les mots-clés d'alerte"""
    flux = [
        "https://finance.yahoo.com/news/rssindex",
        "https://www.reutersagency.com/feed/?taxonomy=categories&post_type=best-topics&term=financial-markets",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"
    ]
    
    tous_les_titres = []
    alertes_detectees = []
    
    for url in flux:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                for item in root.findall('.//item')[:3]:
                    titre = item.find('title')
                    if titre is not None and titre.text:
                        texte_titre = titre.text
                        tous_les_titres.append(texte_titre)
                        
                        # Vérification des mots-clés d'alerte dans le titre
                        titre_lower = texte_titre.lower()
                        for mot in MOTS_CLES_ALERTES:
                            if mot in titre_lower and texte_titre not in alertes_detectees:
                                alertes_detectees.append(texte_titre)
        except Exception as e:
            print(f"Erreur flux {url}: {e}")
    
    random.shuffle(tous_les_titres)
    actus_formatees = "\n".join([f"- {t}" for t in tous_les_titres[:6]])
    
    return actus_formatees, alertes_detectees

def generer_analyse_financiere():
    print("📰 Récupération et analyse des flux...")
    actus_du_jour, alertes = recuperer_actualites_marches()
    
    # Formattage des alertes pour l'IA si des mots-clés ont été trouvés
    consigne_alerte = ""
    if alertes:
        consigne_alerte = f"⚠️ ATTENTION - Sujets sensibles détectés dans l'actualité à intégrer absolument dans l'analyse : {', '.join(alertes)}"
    
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
    
    {consigne_alerte}
    
    Consigne d'angle : {angle_choisi}
    Rédige un flash financier court, percutant, dynamique avec des emojis (📈, 📉, 💡, 💰, 🚀). Pas de sources, juste une analyse pro et directe.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-120b",
        temperature=0.95,
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
        "properties": {"Titre": {"title": [{"text": {"content": "Flash Boursier Alerte & Planifié"}}]}},
        "children": [{"object": "block", "paragraph": {"rich_text": [{"text": {"content": analyse}}]}}]
    }
    requests.post(url, headers=headers, json=data)

def envoyer_telegram():
    print("🔄 Génération et envoi de l'analyse...")
    analyse = generer_analyse_financiere().replace("*", "")
    enregistrer_sur_notion(analyse)
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": analyse,
        "reply_markup": {"inline_keyboard": [[{"text": "🔄 Régénérer", "callback_data": "regen"}]]}
    }
    requests.post(url, json=payload)
    print("✅ Envoyé avec succès !")

def ecouter_telegram():
    print("🤖 Bot en écoute et planificateur actif (heures cibles : 08:30 et 18:00)...")
    offset = None
    
    # Pour la planification automatique (garde en mémoire la dernière date d'envoi automatique)
    dernier_envoi_auto = ""
    
    while True:
        try:
            # 1. Vérification de la planification automatique (Cron-like en Python)
            maintenant = datetime.now()
            heure_actuelle = maintenant.strftime("%H:%M")
            date_actuelle = maintenant.strftime("%Y-%m-%d")
            
            # Heures programmées : 08:30 et 18:00 (heure du serveur Railway, souvent UTC)
            if heure_actuelle in ["08:30", "18:00"] and dernier_envoi_auto != f"{date_actuelle}-{heure_actuelle}":
                print(f"⏰ Déclenchement automatique programmé ({heure_actuelle})...")
                envoyer_telegram()
                dernier_envoi_auto = f"{date_actuelle}-{heure_actuelle}"
                # Petite pause pour éviter de déclencher deux fois dans la même minute
                time.sleep(60)

            # 2. Gestion des interactions Telegram (boutons et commandes)
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=10&offset={offset}" if offset else f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=10"
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
            print(f"Erreur dans la boucle : {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Envoi direct au démarrage pour vérifier que tout fonctionne, puis lancement de la boucle d'écoute et de planification
    envoyer_telegram()
    ecouter_telegram()
