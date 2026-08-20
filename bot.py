import os
import time
import random
import requests
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from groq import Groq

# Récupération des clés API depuis les variables d'environnement Railway
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
NOTION_API_KEY = os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

client = Groq(api_key=GROQ_API_KEY)

# Paramètres de configuration avancés
MOTS_CLES_ALERTES = ["inflation", "fed", "bce", "crise", "crash", "taux", "guerre", "tensions", "secousse"]
VALEURS_SUIVIES = ["Bitcoin", "Tesla", "Apple", "CAC40", "S&P 500", "Nvidia"]

def recuperer_actualites_marches():
    """Récupère, mélange les flux et détecte les mots-clés d'alerte et de ton portfolio"""
    flux = [
        "https://finance.yahoo.com/news/rssindex",
        "https://www.reutersagency.com/feed/?taxonomy=categories&post_type=best-topics&term=financial-markets",
        "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664"
    ]
    
    tous_les_titres = []
    alertes_detectees = []
    actus_portfolio = []
    
    for url in flux:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                for item in root.findall('.//item')[:4]:
                    titre = item.find('title')
                    if titre is not None and titre.text:
                        texte_titre = titre.text
                        tous_les_titres.append(texte_titre)
                        
                        titre_lower = texte_titre.lower()
                        # Vérification des alertes globales
                        for mot in MOTS_CLES_ALERTES:
                            if mot in titre_lower and texte_titre not in alertes_detectees:
                                alertes_detectees.append(texte_titre)
                                
                        # Vérification du portfolio personnel
                        for actif in VALEURS_SUIVIES:
                            if actif.lower() in titre_lower and texte_titre not in actus_portfolio:
                                actus_portfolio.append(texte_titre)
        except Exception as e:
            print(f"Erreur flux {url}: {e}")
    
    random.shuffle(tous_les_titres)
    actus_formatees = "\n".join([f"- {t}" for t in tous_les_titres[:6]])
    
    return actus_formatees, alertes_detectees, actus_portfolio

def generer_analyse_financiere():
    """Génère l'analyse boursière avec Sentiment Score et Focus Portfolio"""
    print("📰 Récupération et analyse multi-sources...")
    actus_du_jour, alertes, portfolio_actus = recuperer_actualites_marches()
    
    consigne_alerte = ""
    if alertes:
        consigne_alerte = f"⚠️ Sujets sensibles à intégrer : {', '.join(alertes)}"
        
    consigne_portfolio = ""
    if portfolio_actus:
        consigne_portfolio = f"🎯 Actualités directes sur tes actifs suivis ({', '.join(VALEURS_SUIVIES)}) : {', '.join(portfolio_actus)}"
    
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
    {consigne_portfolio}
    
    Consigne d'angle : {angle_choisi}
    
    Rédige un flash financier court, percutant, dynamique avec des emojis (📈, 📉, 💡, 💰, 🚀). 
    IMPERATIF : Attribue un "Sentiment Score" de marché sur une échelle de -5 (extrême peur/krach) à +5 (euphorie/haussier) sous format [Score de Sentiment : X/5]. Pas de sources directes, analyse pro et directe.
    """
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-120b",
        temperature=0.95,
    )
    return chat_completion.choices[0].message.content

def generer_resume_hebdomadaire():
    """Interroge Notion pour récupérer l'historique de la semaine et rédiger un bilan macro"""
    print("📊 Récupération de l'historique Notion pour le résumé hebdo...")
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-02-28"
    }
    
    try:
        response = requests.post(url, headers=headers, json={"page_size": 14}) # Récupère les derniers flashs
        data = response.json()
        
        textes_precedents = []
        if "results" in data:
            for page in data["results"]:
                # Extraction basique des blocs enfants ou titre
                titre_page = page.get("properties", {}).get("Titre", {}).get("title", [{}])
                if titre_page:
                    textes_precedents.append(titre_page[0].get("text", {}).get("content", ""))
                    
        historique_str = "\n---\n".join(textes_precedents)
        
        prompt = f"""
        Voici l'historique des analyses financières enregistrées cette semaine dans notre base de données :
        {historique_str}
        
        Rédige un "Résumé Hebdomadaire Stratégique" global de la semaine passée. Identifie les tendances de fond, l'évolution du sentiment général et les points de vigilance pour la semaine à venir. Utilise des emojis et un ton professionnel.
        """
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="openai/gpt-oss-120b",
            temperature=0.7,
        )
        return "📅 **BILAN HEBDOMADAIRE DES MARCHÉS**\n\n" + chat_completion.choices[0].message.content
        
    except Exception as e:
        print(f"Erreur lors de la génération du résumé hebdo via Notion : {e}")
        return "📅 **Bilan Hebdomadaire** : Impossible de récupérer l'historique Notion cette semaine."

def enregistrer_sur_notion(analyse, titre_page="Flash Boursier Avancé"):
    """Enregistre le texte dans Notion"""
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-02-28"
    }
    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {"Titre": {"title": [{"text": {"content": titre_page}}]}},
        "children": [{"object": "block", "paragraph": {"rich_text": [{"text": {"content": analyse}}]}}]
    }
    requests.post(url, headers=headers, json=data)

def envoyer_telegram(est_hebdo=False):
    """Génère l'analyse (standard ou hebdo), l'enregistre sur Notion et l'envoie sur Telegram"""
    print("🔄 Génération en cours...")
    
    if est_hebdo:
        analyse = generer_resume_hebdomadaire().replace("*", "")
        enregistrer_sur_notion(analyse, titre_page="Résumé Hebdomadaire Stratégique")
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": analyse
        }
    else:
        analyse = generer_analyse_financiere().replace("*", "")
        enregistrer_sur_notion(analyse, titre_page="Flash Boursier Avancé")
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": analyse,
            "reply_markup": {"inline_keyboard": [[{"text": "🔄 Régénérer", "callback_data": "regen"}]]}
        }
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json=payload)
    print("✅ Envoyé sur Telegram et Notion avec succès !")

def ecouter_telegram():
    print("🤖 Bot en écoute, planificateur actif (Flashs : 08:30 & 18:00 | Hebdo : Dimanche 20:00)...")
    offset = None
    dernier_envoi_auto = ""
    
    while True:
        try:
            maintenant = datetime.now()
            heure_actuelle = maintenant.strftime("%H:%M")
            date_actuelle = maintenant.strftime("%Y-%m-%d")
            jour_semaine = maintenant.strftime("%A") # ex: Sunday
            
            # 1. Planification Hebdomadaire (Dimanche à 20:00)
            if jour_semaine == "Sunday" and heure_actuelle == "20:00" and dernier_envoi_auto != f"{date_actuelle}-hebdo":
                print("📅 Déclenchement du bilan hebdomadaire...")
                envoyer_telegram(est_hebdo=True)
                dernier_envoi_auto = f"{date_actuelle}-hebdo"
                time.sleep(60)
                
            # 2. Planification Quotidienne (08:30 et 18:00)
            elif heure_actuelle in ["08:30", "18:00"] and dernier_envoi_auto != f"{date_actuelle}-{heure_actuelle}":
                print(f"⏰ Déclenchement automatique programmé ({heure_actuelle})...")
                envoyer_telegram(est_hebdo=False)
                dernier_envoi_auto = f"{date_actuelle}-{heure_actuelle}"
                time.sleep(60)

            # 3. Écoute des interactions Telegram (Boutons / Commandes)
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=10&offset={offset}" if offset else f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?timeout=10"
            response = requests.get(url).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "callback_query" in update:
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": update["callback_query"]["id"]})
                        envoyer_telegram(est_hebdo=False)
                    elif "message" in update and update["message"].get("text") == "/start":
                        envoyer_telegram(est_hebdo=False)
                        
        except Exception as e:
            print(f"Erreur dans la boucle : {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Test au démarrage, puis lancement de la boucle globale
    envoyer_telegram(est_hebdo=False)
    ecouter_telegram()
