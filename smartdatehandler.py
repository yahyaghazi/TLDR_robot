import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SmartDateHandler:
    """Gestionnaire intelligent de dates pour éviter weekends et jours fériés"""
    
    def __init__(self, country_code: str = "US", max_days_back: int = 14):
        self.country_code = country_code
        self.max_days_back = max_days_back
        self.holidays_cache = {}
        self.base_url = "https://date.nager.at/api/v3"
        
    def get_holidays_for_year(self, year: int) -> List[str]:
        """Récupère les jours fériés pour une année donnée"""
        if year in self.holidays_cache:
            return self.holidays_cache[year]
        
        try:
            url = f"{self.base_url}/publicholidays/{year}/{self.country_code}"
            logger.info(f"🗓️ Récupération jours fériés {year} pour {self.country_code}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            holidays_data = response.json()
            holidays = [holiday['date'] for holiday in holidays_data]
            
            self.holidays_cache[year] = holidays
            logger.info(f"✅ {len(holidays)} jours fériés trouvés pour {year}")
            
            return holidays
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération jours fériés: {e}")
            # Fallback : jours fériés courants US/EU
            fallback_holidays = self._get_fallback_holidays(year)
            self.holidays_cache[year] = fallback_holidays
            return fallback_holidays
    
    def _get_fallback_holidays(self, year: int) -> List[str]:
        """Jours fériés de base en cas d'échec API"""
        holidays = [
            f"{year}-01-01",  # New Year
            f"{year}-07-04",  # Independence Day (US)
            f"{year}-12-25",  # Christmas
            f"{year}-12-31",  # New Year's Eve
        ]
        return holidays
    
    def is_holiday(self, target_date: date) -> bool:
        """Vérifie si une date est un jour férié"""
        holidays = self.get_holidays_for_year(target_date.year)
        date_str = target_date.strftime("%Y-%m-%d")
        return date_str in holidays
    
    def is_weekend(self, target_date: date) -> bool:
        """Vérifie si une date est un weekend (samedi=5, dimanche=6)"""
        return target_date.weekday() >= 5
    
    def is_business_day(self, target_date: date) -> bool:
        """Vérifie si une date est un jour ouvrable"""
        return not (self.is_weekend(target_date) or self.is_holiday(target_date))
    
    def get_last_business_day(self, from_date: date = None) -> date:
        """Trouve le dernier jour ouvrable avant une date donnée"""
        if from_date is None:
            from_date = date.today()
        
        # Si c'est aujourd'hui et qu'on est avant midi, prendre hier
        if from_date == date.today() and datetime.now().hour < 12:
            from_date = from_date - timedelta(days=1)
        
        current_date = from_date
        days_checked = 0
        
        logger.info(f"🔍 Recherche du dernier jour ouvrable avant {from_date}")
        
        while days_checked < self.max_days_back:
            if self.is_business_day(current_date):
                reason = "jour ouvrable trouvé"
                if self.is_weekend(current_date):
                    reason += " (weekend évité)"
                if self.is_holiday(current_date):
                    reason += " (jour férié évité)"
                
                logger.info(f"✅ Date retenue: {current_date} ({reason})")
                return current_date
            
            # Log pourquoi cette date est évitée
            skip_reason = []
            if self.is_weekend(current_date):
                skip_reason.append("weekend")
            if self.is_holiday(current_date):
                skip_reason.append("jour férié")
            
            logger.info(f"⏭️ {current_date} ignoré: {', '.join(skip_reason)}")
            
            current_date -= timedelta(days=1)
            days_checked += 1
        
        # Fallback : retourner la date originale si aucun jour ouvrable trouvé
        logger.warning(f"⚠️ Aucun jour ouvrable trouvé, utilisation de {from_date}")
        return from_date
    
    def get_smart_dates_sequence(self, count: int = 3) -> List[date]:
        """Génère une séquence de dates intelligente pour les tests"""
        dates = []
        current_date = date.today()
        
        for i in range(count):
            # Chercher le dernier jour ouvrable
            business_day = self.get_last_business_day(current_date)
            dates.append(business_day)
            
            # Passer au jour précédent pour la prochaine itération
            current_date = business_day - timedelta(days=1)
        
        return dates
    
    def check_date_availability(self, target_date: date) -> Dict[str, Any]:
        """Analyse complète d'une date"""
        info = {
            'date': target_date,
            'date_str': target_date.strftime("%Y-%m-%d"),
            'is_weekend': self.is_weekend(target_date),
            'is_holiday': self.is_holiday(target_date),
            'is_business_day': self.is_business_day(target_date),
            'day_name': target_date.strftime("%A"),
            'recommended': False,
            'reason': []
        }
        
        if info['is_weekend']:
            info['reason'].append("Weekend")
        if info['is_holiday']:
            info['reason'].append("Jour férié")
        if target_date >= date.today():
            info['reason'].append("Date future")
        
        info['recommended'] = len(info['reason']) == 0
        
        return info


class TLDRSmartScraper:
    """Scraper TLDR avec gestion intelligente des dates"""
    
    def __init__(self, newsletter_type: str = "tech", country_code: str = "US"):
        self.newsletter_type = newsletter_type
        self.base_url = f"https://tldr.tech/{newsletter_type}"
        self.date_handler = SmartDateHandler(country_code)
        
        # Headers optimisés
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
    
    def get_best_available_date(self) -> date:
        """Trouve la meilleure date disponible pour scraper"""
        return self.date_handler.get_last_business_day()
    
    def get_newsletter_url(self, target_date: date = None) -> str:
        """Génère l'URL de la newsletter pour une date optimale"""
        if target_date is None:
            target_date = self.get_best_available_date()
        
        date_str = target_date.strftime("%Y-%m-%d")
        return f"{self.base_url}/{date_str}"
    
    def test_date_availability(self, target_date: date) -> bool:
        """Test si une date a probablement du contenu TLDR"""
        url = f"{self.base_url}/{target_date.strftime('%Y-%m-%d')}"
        
        try:
            response = requests.head(url, headers=self.headers, timeout=10)
            available = response.status_code == 200
            
            logger.info(f"📅 {target_date}: {'✅ Disponible' if available else '❌ Indisponible'} (HTTP {response.status_code})")
            return available
            
        except Exception as e:
            logger.warning(f"📅 {target_date}: ❓ Test échoué ({e})")
            return False
    
    def find_best_available_content(self, max_attempts: int = 7) -> Optional[date]:
        """Trouve la date avec du contenu disponible"""
        logger.info(f"🔍 Recherche de contenu TLDR disponible (max {max_attempts} tentatives)")
        
        current_date = date.today()
        
        for attempt in range(max_attempts):
            # Obtenir la date business recommandée
            business_date = self.date_handler.get_last_business_day(current_date)
            
            # Analyser cette date
            date_info = self.date_handler.check_date_availability(business_date)
            
            logger.info(f"📊 Tentative {attempt + 1}: {business_date} ({date_info['day_name']})")
            
            if date_info['reason']:
                logger.info(f"   ⚠️ Problèmes: {', '.join(date_info['reason'])}")
            
            # Tester la disponibilité du contenu
            if self.test_date_availability(business_date):
                logger.info(f"🎯 Date retenue: {business_date}")
                return business_date
            
            # Passer au jour précédent
            current_date = business_date - timedelta(days=1)
        
        logger.error(f"❌ Aucun contenu trouvé après {max_attempts} tentatives")
        return None
    
    def get_smart_test_urls(self, count: int = 3) -> List[str]:
        """Génère une liste d'URLs intelligente pour les tests"""
        urls = []
        
        # Date optimale
        best_date = self.find_best_available_content()
        if best_date:
            urls.append(f"{self.base_url}/{best_date.strftime('%Y-%m-%d')}")
        
        # Dates alternatives
        smart_dates = self.date_handler.get_smart_dates_sequence(count - 1)
        for date_obj in smart_dates:
            if date_obj != best_date:  # Éviter les doublons
                urls.append(f"{self.base_url}/{date_obj.strftime('%Y-%m-%d')}")
        
        return urls[:count]


def test_smart_date_system():
    """Test du système de dates intelligent"""
    print("🧪 Test du système de dates intelligent")
    print("=" * 50)
    
    # Test avec différents pays
    countries = ["US", "FR", "DE", "GB"]
    
    for country in countries:
        print(f"\n🌍 Test pour {country}:")
        handler = SmartDateHandler(country)
        
        # Analyser les 7 prochains jours
        today = date.today()
        for i in range(7):
            test_date = today - timedelta(days=i)
            info = handler.check_date_availability(test_date)
            
            status = "✅" if info['recommended'] else "❌"
            reasons = f" ({', '.join(info['reason'])})" if info['reason'] else ""
            
            print(f"  {status} {test_date} ({info['day_name']}){reasons}")
        
        # Meilleure date
        best_date = handler.get_last_business_day()
        print(f"  🎯 Meilleure date: {best_date}")


def test_smart_scraper():
    """Test du scraper intelligent"""
    print("\n🧪 Test du scraper TLDR intelligent")
    print("=" * 50)
    
    scraper = TLDRSmartScraper("tech", "US")
    
    # Trouver la meilleure date
    best_date = scraper.find_best_available_content()
    if best_date:
        print(f"🎯 Meilleure date trouvée: {best_date}")
        
        # Générer les URLs de test
        test_urls = scraper.get_smart_test_urls()
        print(f"\n📋 URLs de test générées:")
        for i, url in enumerate(test_urls, 1):
            print(f"  {i}. {url}")
    else:
        print("❌ Aucune date disponible trouvée")


if __name__ == "__main__":
    test_smart_date_system()
    test_smart_scraper()