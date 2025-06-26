import logging
import ollama

from tdlrscraper import TLDRScraper
from tdlrautomationsystem import TLDRAutomationSystem

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Configuration et utilisation avec TLDR Tech
def main():
    # Configuration optimisée pour TLDR Tech
    config = {
        'newsletter_type': 'tech',  # Changé de 'marketing' à 'tech'
        'notion_token': 'YOUR_NOTION_TOKEN',
        'notion_database_id': 'YOUR_DATABASE_ID',
        'ollama_model': 'nous-hermes2:latest',
        'ollama_base_url': 'http://localhost:11434',
        'audio_output_dir': './audio_summaries'
    }
    
    # Initialisation du système
    automation = TLDRAutomationSystem(config)
    
    # Test avec une date spécifique (exemple)
    # scraper = TLDRScraper('tech')
    # articles = scraper.scrape_articles('https://tldr.tech/tech/2025-06-25')
    
    # Lancement de l'automatisation pour aujourd'hui
    results = automation.run_daily_automation()
    
    # Sauvegarde des résultats
    automation.save_results(results)
    
    # Affichage des résultats
    print(f"🔍 Articles TLDR Tech extraits: {results['articles_extracted']}")
    print(f"💾 Articles stockés dans Notion: {results['articles_stored']}")
    print(f"📝 Synthèse générée: {len(results['synthesis'])} caractères")
    print(f"🎵 Fichier audio: {results['audio_file']}")
    
    if results['errors']:
        print(f"❌ Erreurs: {results['errors']}")
    
    # Affichage d'un extrait de la synthèse
    if results['synthesis']:
        print(f"\n📊 Aperçu de la synthèse TLDR Tech:")
        print(results['synthesis'][:300] + "...")


def test_tldr_tech_scraping():
    """Test spécifique pour TLDR Tech"""
    print("🧪 Test du scraping TLDR Tech")
    
    scraper = TLDRScraper('tech')
    
    # Test avec différentes URLs
    test_urls = [
        'https://tldr.tech/tech/2025-06-25',
        scraper.get_todays_newsletter(),
        scraper.get_newsletter_by_date('2025-06-24')
    ]
    
    for url in test_urls:
        print(f"\n📰 Test: {url}")
        articles = scraper.scrape_articles(url)
        print(f"✅ Articles trouvés: {len(articles)}")
        
        if articles:
            for i, article in enumerate(articles[:3], 1):
                print(f"  {i}. {article['titre'][:60]}...")
                if article['url']:
                    print(f"     🔗 {article['url'][:50]}...")
                if article['resume_tldr']:
                    print(f"     📝 {article['resume_tldr'][:80]}...")
                print()


def test_all_newsletters():
    """Test de tous les types de newsletters TLDR"""
    newsletters = ['tech', 'ai', 'crypto', 'marketing', 'design', 'webdev']
    
    for newsletter in newsletters:
        print(f"\n🧪 Test TLDR {newsletter.upper()}:")
        try:
            scraper = TLDRScraper(newsletter)
            url = scraper.get_todays_newsletter()
            articles = scraper.scrape_articles(url)
            print(f"✅ {newsletter}: {len(articles)} articles")
        except Exception as e:
            print(f"❌ {newsletter}: {e}")


if __name__ == "__main__":
    # Test spécifique TLDR Tech
    test_tldr_tech_scraping()
    
    # Ou lancer l'automatisation complète
    # main()
    
    # Ou tester toutes les newsletters
    # test_all_newsletters()


def test_ollama_models():
    """Fonction utilitaire pour tester différents modèles Ollama"""
    models_to_test = [
        'nous-hermes2:latest',
        'llama2:latest', 
        'mistral:latest',
        'codellama:latest',
        'phi:latest'
    ]
    
    for model in models_to_test:
        print(f"\n🧪 Test du modèle: {model}")
        try:
            response = ollama.chat(
                model=model,
                messages=[{
                    'role': 'user',
                    'content': 'Réponds en français: Catégorise cet article en 2 mots: "Introduction to Machine Learning for beginners"'
                }],
                options={'num_predict': 20}
            )
            print(f"✅ {model}: {response['message']['content']}")
        except Exception as e:
            print(f"❌ {model}: {e}")


if __name__ == "__main__":
    # Tester d'abord les modèles disponibles (optionnel)
    # test_ollama_models()
    
    # Lancer l'automatisation principale
    main()


# INSTRUCTIONS D'INSTALLATION OLLAMA UNIQUEMENT
"""
🚀 SETUP OLLAMA (LLM LOCAL UNIQUEMENT)

1. Installation d'Ollama:
   - Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh
   - Windows: Télécharger depuis https://ollama.ai/download
   
2. Démarrer Ollama:
   ollama serve

3. Installer le modèle recommandé:
   ollama pull nous-hermes2:latest
   
   Autres modèles performants:
   ollama pull mistral:latest      # Plus rapide, bon pour la catégorisation
   ollama pull llama2:latest       # Modèle de référence
   ollama pull phi:latest          # Très compact et rapide

4. Installation des dépendances Python (SIMPLICITÉ):
   pip install requests beautifulsoup4 ollama notion-client pyttsx3

5. Configuration ultra-simple:
   config = {
       'newsletter_type': 'marketing',
       'notion_token': 'YOUR_NOTION_TOKEN',
       'notion_database_id': 'YOUR_DATABASE_ID',
       'ollama_model': 'nous-hermes2:latest'
   }

AVANTAGES OLLAMA PUR:
✅ 100% Gratuit et illimité
✅ 100% Privé (tout en local)
✅ Aucune dépendance Internet pour l'IA
✅ Performance excellente
✅ Plus simple : pas de choix de provider
✅ Pas de clé API à gérer

MODÈLES RECOMMANDÉS:
- nous-hermes2:latest -> Le meilleur pour l'analyse (RECOMMANDÉ)
- mistral:latest -> Plus rapide, excellent aussi
- phi:latest -> Ultra compact pour machines limitées

6. Test simple:
   python -c "import ollama; print('Ollama OK')"

7. Lancement:
   python tldr_automation.py

Plus simple, plus rapide, 100% gratuit !
"""