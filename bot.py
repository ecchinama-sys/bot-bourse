import random
import requests
from datetime import datetime
from groq import Groq

# --- TES CLES API (À remplir avec tes propres clés) ---
GROQ_API_KEY = "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"          
TELEGRAM_BOT_TOKEN = "8820955818:AAGtMB-LwbJSw7CS8uYWIMVVLkT-Lvkkd-s"  
TELEGRAM_CHAT_ID = "6736922134"      
NOTION_API_KEY = "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"
NOTION_DATABASE_ID = "https://app.notion.com/p/3c2ff48f1aed803db912e3f32650c7a5?v=3c2ff48f1aed80499920000c65daf439&source=copy_link"

# Initialisation du client Groq et sélection automatique du modèle Llama disponible
client = Groq(api_key=GROQ_API_KEY)
try:
    models_list = client.models.list().data
    SELECTED_MODEL = next((m.id for m in models_list if "llama" in m.id.lower() and "whisper" not in m.id.lower() and "guard" not in m.id.lower()), "llama-3.1-70b-versatile")
except Exception:
    SELECTED_MODEL = "llama-3.1-70b-versatile"

def add_to_notion(title, content):
    """Enregistre l'article et l'analyse dans Notion avec le titre et la date du jour."""
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
        "children": [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content[:2000]}}]
                }
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code

def generer_analyse():
    """Génère l'actualité boursière avec les faits au début et l'analyse d'expert à la fin."""
    angles = [
        "Focus sur la tech, les valeurs de croissance et l'intelligence artificielle sur les marchés.",
        "Focus sur l'inflation, les décisions des banques centrales (FED, BCE) et les taux d'intérêt.",
        "Focus sur les matières premières (pétrole, or) et les mouvements géopolitiques mondiaux.",
        "Focus sur les résultats d'entreprises, les actions en forte hausse/baisse et les conseils de rotation sectorielle."
    ]
    
    angle_choisi = random.choice(angles)
    
    prompt = (
        f"Tu es un expert analyste financier renommé. Rédige un flash boursier et financier complet "
        f"en suivant STRICTEMENT cet ordre dans la structure :\n"
        f"1. Les faits marquants et l'actualité des marchés (ce qui s'est passé).\n"
        f"2. Les indicateurs clés et les chiffres importants à retenir.\n"
        f"3. Ton analyse d'expert et ton avis tranché (cette partie doit OBLIGATOIREMENT se trouver à la toute fin du texte).\n"
        f"Angle prioritaire pour cette édition : {angle_choisi}. "
        f"Ton style doit être professionnel, direct, percutant et orienté investisseur."
    )
    
    completion = client.chat.completions.create(
        model=SELECTED_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return str(completion.choices[0].message.content)

def envoyer_telegram(message):
    """Envoie le message sur Telegram avec les boutons interactifs en bas (Régénérer + Démarrer)."""
    titre = f"Flash Finance & Bourse - {datetime.now().strftime('%d/%m/%Y')}"
    url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": f"📈 *{titre}*\n\n{message}",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {
                        "text": "🔄 Régénérer un autre article",
                        "callback_data": "regen"
                    }
                ],
                [
                    {
                        "text": "🚀 /start (Redémarrer / Actualiser)",
                        "callback_data": "start_bot"
                    }
                ]
            ]
        }
    }
    requests.post(url_telegram, json=payload)

def main():
    """Fonction principale gérant la vérification des clics et le cycle d'exécution."""
    print("\n🚀 Lancement du script de flash boursier...")
    
    # Vérification des interactions de clic sur Telegram
    try:
        updates = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates").json()
        if "result" in updates:
            for u in updates["result"]:
                if "callback_query" in u:
                    callback_data = u["callback_query"]["data"]
                    if callback_data in ["regen", "start_bot"]:
                        print("🔄 Action interactive détectée depuis Telegram : Génération d'une nouvelle analyse...")
                        requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={u['update_id'] + 1}")
    except Exception as e:
        print(f"Info lors de la vérification des updates : {e}")

    # Génération du contenu via l'IA
    message_ia = generer_analyse()
    
    # Création du titre avec la date du jour
    date_du_jour = datetime.now().strftime("%d/%m/%Y")
    titre_page = f"Flash Finance & Bourse - {date_du_jour}"
    
    # Enregistrement Notion
    status_notion = add_to_notion(titre_page, message_ia)
    if status_notion == 200:
        print("✅ Données enregistrées dans Notion avec succès (titre, contenu et date).")
    else:
        print(f"⚠️ Erreur lors de l'enregistrement Notion (Code : {status_notion})")

    # Envoi Telegram
    envoyer_telegram(message_ia)
    print("✅ Message et boutons interactifs envoyés sur Telegram !")

if __name__ == "__main__":
    main()
