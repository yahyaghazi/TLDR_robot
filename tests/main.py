import logging
import ollama
from datetime import date

from core.tdlrscraper import TLDRScraper
from tdlrautomationsystem import TLDRAutomationSystem

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_smart_date_system():
    """Test du système de dates intelligent"""
    print("🧪 Test du système de dates intelligent")
    print("=" * 60)
    
    from core.tdlrscraper import SmartDateHandler
    
    # Test avec différents pays
    countries = {"US": "États-Unis", "FR": "France", "DE": "Allemagne", "GB": "Royaume-Uni"}
    
    for code, name in countries.items():
        print(f"\n🌍 {name} ({code}):")
        handler = SmartDateHandler(code)
        
        # Obtenir la meilleure date
        best_date = handler.get_last_business_day()
        print(f"  🎯 Meilleure date: {best_date} ({best_date.strftime('%A')})")
        
        # Analyser les derniers jours
        from datetime import timedelta
        for i in range(5):
            test_date = best_date - timedelta(days=i)
            is_business = handler.is_business_day(test_date)
            status = "✅" if is_business else "❌"
            day_name = test_date.strftime("%A")
            print(f"  {status} {test_date} ({day_name})")

def test_tldr_tech_scraping_smart():
    """Test spécifique pour TLDR Tech avec dates intelligentes"""
    print("\n🧪 Test du scraping TLDR Tech intelligent")
    print("=" * 60)
    
    # NOUVEAU: Scraper avec gestion intelligente des dates
    scraper = TLDRScraper('tech', max_articles=15, country_code='US')
    
    print("🔍 Recherche automatique de la meilleure newsletter...")
    
    # Test de recherche intelligente
    best_url = scraper.find_available_newsletter()
    print(f"📰 URL optimale: {best_url}")
    
    # Test de scraping
    print(f"\n📥 Scraping en cours...")
    articles = scraper.scrape_articles()
    
    print(f"✅ Articles trouvés: {len(articles)}")
    
    if articles:
        print(f"\n📋 Aperçu des articles:")
        for i, article in enumerate(articles[:5], 1):
            print(f"  {i}. {article['titre'][:70]}...")
            if article['url']:
                print(f"     🔗 {article['url'][:60]}...")
            if article['resume_tldr']:
                print(f"     📝 {article['resume_tldr'][:80]}...")
            print()
    else:
        print("❌ Aucun article trouvé")

def main():
    """Configuration et utilisation avec TLDR Tech et dates intelligentes"""
    print("🚀 Lancement du système TLDR automatisé")
    print("=" * 60)
    
    # Configuration optimisée pour TLDR Tech
    config = {
        'newsletter_type': 'tech',
        'notion_token': 'YOUR_NOTION_TOKEN',
        'notion_database_id': 'YOUR_DATABASE_ID',
        'ollama_model': 'nous-hermes2:latest',
        'ollama_base_url': 'http://localhost:11434',
        'audio_output_dir': './audio_summaries',
        'country_code': 'US'  # NOUVEAU: Code pays pour jours fériés
    }
    
    # Initialisation du système
    automation = TLDRAutomationSystem(config)
    
    # Lancement de l'automatisation intelligente
    print("📰 Recherche de la newsletter la plus récente...")
    results = automation.run_daily_automation()
    
    # Sauvegarde des résultats
    automation.save_results(results)
    
    # Affichage des résultats
    print(f"\n📊 RÉSULTATS:")
    print(f"🔍 Articles TLDR Tech extraits: {results['articles_extracted']}")
    print(f"💾 Articles stockés dans Notion: {results['articles_stored']}")
    print(f"📝 Synthèse générée: {len(results['synthesis'])} caractères")
    print(f"🎵 Fichier audio: {results['audio_file']}")
    
    if results['errors']:
        print(f"❌ Erreurs: {results['errors']}")
    else:
        print("✅ Automatisation réussie!")
    
    # Affichage d'un extrait de la synthèse
    if results['synthesis']:
        print(f"\n📊 Aperçu de la synthèse TLDR Tech:")
        print("-" * 50)
        print(results['synthesis'][:400] + "...")
        print("-" * 50)

def test_holidays_api():
    """Test de l'API des jours fériés"""
    print("\n🧪 Test de l'API Nager.Date (jours fériés)")
    print("=" * 60)
    
    from core.tdlrscraper import SmartDateHandler
    import requests
    
    # Test direct de l'API
    countries_to_test = ['US', 'FR', 'DE', 'GB', 'CA']
    year = 2025
    
    for country in countries_to_test:
        print(f"\n🌍 Test {country}:")
        try:
            url = f"https://date.nager.at/api/v3/publicholidays/{year}/{country}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                holidays = response.json()
                print(f"  ✅ {len(holidays)} jours fériés trouvés")
                
                # Afficher les 3 premiers
                for holiday in holidays[:3]:
                    print(f"    📅 {holiday['date']}: {holiday['name']}")
            else:
                print(f"  ❌ Erreur HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    # Test avec le gestionnaire intelligent
    print(f"\n🧠 Test avec gestionnaire intelligent:")
    handler = SmartDateHandler('US')
    
    from datetime import date, timedelta
    today = date.today()
    
    for i in range(10):
        test_date = today - timedelta(days=i)
        is_business = handler.is_business_day(test_date)
        status = "✅ Business" if is_business else "❌ Non-business"
        print(f"  {test_date} ({test_date.strftime('%A')}): {status}")

def test_all_newsletters_smart():
    """Test de tous les types de newsletters TLDR avec dates intelligentes"""
    print("\n🧪 Test de toutes les newsletters TLDR")
    print("=" * 60)
    
    newsletters = ['tech', 'ai', 'crypto', 'marketing', 'design', 'webdev']
    
    for newsletter in newsletters:
        print(f"\n📰 TLDR {newsletter.upper()}:")
        try:
            scraper = TLDRScraper(newsletter, max_articles=10, country_code='US')
            
            # Recherche intelligente
            best_url = scraper.find_available_newsletter()
            print(f"  🎯 URL: {best_url}")
            
            # Test rapide
            if scraper._test_url_availability(best_url):
                print(f"  ✅ Contenu disponible")
                # Articles = scraper.scrape_articles()
                # print(f"  📊 {len(articles)} articles trouvés")
            else:
                print(f"  ❌ Contenu indisponible")
                
        except Exception as e:
            print(f"  ❌ Erreur: {e}")

def diagnostic_complet():
    """Diagnostic complet du système"""
    print("🔧 DIAGNOSTIC COMPLET DU SYSTÈME")
    print("=" * 60)
    
    # 1. Test Ollama
    print("\n1️⃣ Test Ollama:")
    try:
        import ollama
        response = ollama.chat(
            model='nous-hermes2:latest',
            messages=[{'role': 'user', 'content': 'Hello, respond with "OK"'}],
            options={'num_predict': 10}
        )
        print("  ✅ Ollama fonctionne")
        print(f"  📝 Réponse: {response['message']['content']}")
    except Exception as e:
        print(f"  ❌ Ollama erreur: {e}")
    
    # 2. Test API jours fériés
    print("\n2️⃣ Test API Nager.Date:")
    test_holidays_api()
    
    # 3. Test dates intelligentes
    print("\n3️⃣ Test système de dates:")
    test_smart_date_system()
    
    # 4. Test scraping
    print("\n4️⃣ Test scraping intelligent:")
    test_tldr_tech_scraping_smart()
    
    print(f"\n🎉 Diagnostic terminé!")

if __name__ == "__main__":
    # Choix du test à exécuter
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        mode = "smart"  # Mode par défaut
    
    if mode == "diagnostic":
        diagnostic_complet()
    elif mode == "dates":
        test_smart_date_system()
    elif mode == "holidays":
        test_holidays_api()
    elif mode == "all":
        test_all_newsletters_smart()
    elif mode == "automation":
        main()  # Automatisation complète
    else:
        # Mode par défaut: test intelligent
        test_smart_date_system()
        test_tldr_tech_scraping_smart()

# Instructions d'utilisation:
# python main.py              # Test intelligent par défaut
# python main.py diagnostic   # Diagnostic complet
# python main.py dates        # Test système de dates
# python main.py holidays     # Test API jours fériés
# python main.py all          # Test toutes newsletters
# python main.py automation   # Lancement automatisation complète