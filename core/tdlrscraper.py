import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import logging

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
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            holidays_data = response.json()
            holidays = [holiday['date'] for holiday in holidays_data]
            self.holidays_cache[year] = holidays
            
            return holidays
            
        except Exception as e:
            logger.warning(f"Erreur API jours fériés: {e}, utilisation fallback")
            fallback_holidays = [
                f"{year}-01-01", f"{year}-07-04", f"{year}-12-25", f"{year}-12-31"
            ]
            self.holidays_cache[year] = fallback_holidays
            return fallback_holidays
    
    def is_business_day(self, target_date: date) -> bool:
        """Vérifie si une date est un jour ouvrable"""
        # Weekend check
        if target_date.weekday() >= 5:
            return False
        
        # Holiday check
        holidays = self.get_holidays_for_year(target_date.year)
        date_str = target_date.strftime("%Y-%m-%d")
        return date_str not in holidays
    
    def get_last_business_day(self, from_date: date = None) -> date:
        """Trouve le dernier jour ouvrable"""
        if from_date is None:
            from_date = date.today()
        
        # Si c'est aujourd'hui et avant midi, prendre hier
        if from_date == date.today() and datetime.now().hour < 12:
            from_date = from_date - timedelta(days=1)
        
        current_date = from_date
        days_checked = 0
        
        while days_checked < self.max_days_back:
            if self.is_business_day(current_date):
                return current_date
            current_date -= timedelta(days=1)
            days_checked += 1
        
        return from_date  # Fallback

class TLDRScraper:
    """Niveau 1 - Découverte: Extraction des articles TLDR Tech optimisée avec dates intelligentes et traduction automatique"""

    def __init__(self, newsletter_type="tech", max_articles=20, country_code="US", year=None, month=None, day=None, target_language=None, deepl_api_key=None):
        self.newsletter_type = newsletter_type
        self.base_url = f"https://tldr.tech/{newsletter_type}"
        self.max_articles = max_articles
        self.date_handler = SmartDateHandler(country_code)
        self.year = year
        self.month = month
        self.day = day
        self.target_language = target_language  # e.g. 'FR', 'ES', 'DE', etc.
        self.deepl_api_key = deepl_api_key

        # Headers optimisés pour TLDR
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

        # Initialiser le traducteur DeepL si clé fournie
        self.translator = None
        if self.target_language and self.deepl_api_key:
            try:
                self.translator = deepl.Translator(self.deepl_api_key)
            except Exception as e:
                logger.warning(f"Erreur d'initialisation DeepL: {e}")

    def translate_text(self, text, target_lang=None):
        """Traduit un texte avec DeepL si activé"""
        if not text or not self.translator or not (target_lang or self.target_language):
            return text
        try:
            result = self.translator.translate_text(text, target_lang=(target_lang or self.target_language))
            return result.text
        except Exception as e:
            logger.warning(f"Erreur traduction DeepL: {e}")
            return text
        
    def get_todays_newsletter(self) -> str:
        """Récupère l'URL de la newsletter du jour (jour ouvrable)"""
        best_date = self.date_handler.get_last_business_day()
        date_str = best_date.strftime("%Y-%m-%d")
        logger.info(f"📅 Date optimale sélectionnée: {date_str}")
        return f"{self.base_url}/{date_str}"
    
    def get_newsletter_by_date(self, target_date: str) -> str:
        """Récupère l'URL pour une date spécifique (format YYYY-MM-DD)"""
        return f"{self.base_url}/{target_date}"
    
    def find_available_newsletter(self, max_attempts: int = 7) -> str:
        """NOUVEAU: Trouve une newsletter disponible en testant plusieurs dates"""
        current_date = date.today()
        
        for attempt in range(max_attempts):
            # Obtenir le jour ouvrable
            business_date = self.date_handler.get_last_business_day(current_date)
            url = f"{self.base_url}/{business_date.strftime('%Y-%m-%d')}"

            if self._test_url_availability(url):
                logger.info(f"✅ Newsletter trouvée: {business_date}")
                return url
            
            logger.info(f"⏭️ {business_date} non disponible, test jour précédent")
            current_date = business_date - timedelta(days=1)
        
        # Fallback: retourner l'URL du jour
        logger.warning("⚠️ Aucune newsletter récente trouvée, utilisation date du jour")
        return self.get_todays_newsletter()
    
    def _test_url_availability(self, url: str) -> bool:
        """Test rapide si une URL retourne du contenu"""
        try:
            response = requests.head(url, headers=self.headers, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def scrape_articles(self, url: str = None) -> List[Dict[str, Any]]:
        """Extrait tous les articles de la newsletter TLDR avec gestion intelligente des dates ou date ciblée"""
        if not url:
            # Si l'utilisateur a spécifié une année/mois(/jour), construire l'URL correspondante
            if self.year and self.month:
                if self.day:
                    target_date = f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
                else:
                    target_date = f"{self.year:04d}-{self.month:02d}-01"
                url = self.get_newsletter_by_date(target_date)
            else:
                url = self.find_available_newsletter()

        try:
            logger.info(f"Scraping TLDR {self.newsletter_type}: {url}")
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []

            # Méthodes de scraping TLDR par ordre de priorité
            scraping_methods = [
                self._scrape_method_structured,
                self._scrape_method_links,
                self._scrape_method_fallback
            ]

            for method in scraping_methods:
                articles = method(soup, url)
                if articles:
                    logger.info(f"Méthode réussie: {method.__name__}")
                    break

            # Si aucune méthode ne marche et que l'URL était auto-détectée,
            # essayer avec une date manuelle
            if not articles and url == self.find_available_newsletter():
                logger.warning("Aucun article trouvé avec date auto, test avec dates manuelles")
                return self._try_fallback_dates()

            # Filtrer et nettoyer les articles
            cleaned_articles = self._clean_and_validate_articles(articles)

            # Limitation du nombre d'articles
            if len(cleaned_articles) > self.max_articles:
                logger.info(f"Limitation de {len(cleaned_articles)} à {self.max_articles} articles")
                cleaned_articles = cleaned_articles[:self.max_articles]

            logger.info(f"Extracted {len(cleaned_articles)} articles from {url}")
            return cleaned_articles

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")

            if "Failed to resolve" in str(e) or "NameResolutionError" in str(e):
                logger.info("Erreur DNS détectée, tentative avec dates alternatives...")
                return self._try_fallback_dates()

            return []
    
    def _try_fallback_dates(self) -> List[Dict[str, Any]]:
        """NOUVEAU: Essaie plusieurs dates en cas d'échec"""
        fallback_dates = [
            "2025-06-24", "2025-06-21", "2025-06-20", 
            "2025-06-19", "2025-06-18", "2025-06-17"
        ]
        
        for date_str in fallback_dates:
            try:
                url = self.get_newsletter_by_date(date_str)
                if self._test_url_availability(url):
                    logger.info(f"✅ Date de fallback réussie: {date_str}")
                    
                    response = requests.get(url, headers=self.headers, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Essayer les méthodes de scraping
                    for method in [self._scrape_method_structured, self._scrape_method_links]:
                        articles = method(soup, url)
                        if articles:
                            cleaned = self._clean_and_validate_articles(articles)
                            if len(cleaned) > self.max_articles:
                                cleaned = cleaned[:self.max_articles]
                            return cleaned
                            
            except Exception as e:
                logger.warning(f"Fallback {date_str} échoué: {e}")
                continue
        
        logger.error("❌ Toutes les dates de fallback ont échoué")
        return []
    
    def _scrape_method_structured(self, soup, url: str) -> List[Dict[str, Any]]:
        """Méthode 1: Scraping basé sur la structure TLDR"""
        articles = []
        
        # Sélecteurs spécifiques TLDR
        article_selectors = [
            'article',
            '.story',
            '.newsletter-item',
            '.post-content',
            '.content-section',
            '[data-testid*="article"]',
            '[id*="story"]'
        ]
        
        for selector in article_selectors:
            sections = soup.find_all(selector)
            if sections:
                logger.info(f"Found {len(sections)} sections with selector: {selector}")
                
                for section in sections:
                    article = self._extract_article_from_section(section, url)
                    if article:
                        articles.append(article)
                        
                        if len(articles) >= self.max_articles * 2:  # Buffer pour le nettoyage
                            break
                
                if articles:
                    break
        
        return articles
    
    def _scrape_method_links(self, soup, url: str) -> List[Dict[str, Any]]:
        """Méthode 2: Extraction basée sur les liens externes (AMÉLIORÉE)"""
        articles = []
        
        # Recherche de tous les liens externes
        external_links = soup.find_all('a', href=re.compile(r'^https?://(?!tldr\.tech)'))

        filtered_links = []
        for link in external_links:
            if self._is_article_link(link):
                filtered_links.append(link)
                # Limite précoce pour éviter trop de liens
                if len(filtered_links) >= self.max_articles * 3:
                    break
        
        logger.info(f"Filtered to {len(filtered_links)} potential article links")
        
        for link in filtered_links:
            article = self._extract_article_from_link(link, url)
            if article:
                articles.append(article)
                
                if len(articles) >= self.max_articles * 2:
                    break
        
        return articles
    
    def _scrape_method_fallback(self, soup, url: str) -> List[Dict[str, Any]]:
        """Méthode 3: Fallback - extraction par patterns de texte"""
        articles = []
        text_content = soup.get_text()
        
        # Patterns typiques TLDR
        patterns = [
            r'([A-Z][^.!?]*(?:minute read|min read))',
            r'(https?://[^\s]+)\s*[–-]\s*([^.!?]*)',
            r'([A-Z][^.!?]*)\s*\((\d+)\s*minute?\s*read\)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_content, re.MULTILINE)
            count = 0
            for match in matches:
                if count >= self.max_articles:  
                    break
                article = self._create_article_from_match(match, url)
                if article:
                    articles.append(article)
                    count += 1
        
        return articles
    
    def _is_article_link(self, link) -> bool:
        """Vérifie si un lien pointe vers un article (AMÉLIORATION)"""
        href = link.get('href', '')
        text = link.get_text(strip=True)

        exclusions = [
            'unsubscribe', 'subscribe', 'footer', 'header',
            'privacy', 'terms', 'about', 'contact', 'sponsor',
            'advertise', 'jobs', 'careers', 'support',
            'twitter.com', 'linkedin.com', 'facebook.com',
            'instagram.com', 'youtube.com', 'tiktok.com',
            'tldr.tech/unsubscribe', 'tldr.tech/jobs',
            'tldr.tech/sponsor', 'tldr.tech/advertise',
            'mailto:', 'tel:', 'javascript:',
            # Exclusions spécifiques TLDR
            'tldr.tech/marketing', 'tldr.tech/ai', 'tldr.tech/crypto',
            '/unsubscribe', '/subscribe', '/privacy'
        ]
        
        # Vérification stricte des exclusions
        href_lower = href.lower()
        text_lower = text.lower()
        
        for exclusion in exclusions:
            if exclusion in href_lower or exclusion in text_lower:
                return False

        # Le texte doit être assez long et descriptif
        if len(text) < 15:
            return False

        quality_domains = [
            'github.com', 'medium.com', 'dev.to', 'stackoverflow.com',
            'techcrunch.com', 'theverge.com', 'arstechnica.com', 'wired.com',
            'engadget.com', 'venturebeat.com', 'hackernews', 'reddit.com',
            'blog.', 'docs.', 'research.', 'paper', 'arxiv.org',
            'news.', 'press.', 'announce'
        ]
        
        # Si c'est un domaine de qualité, on accepte plus facilement
        for domain in quality_domains:
            if domain in href_lower:
                return len(text) > 10
        
        # Sinon, critères plus stricts
        return len(text) > 25 and href.startswith('http') and '.' in href
    
    def _extract_article_from_section(self, section, base_url: str) -> Dict[str, Any]:
        """Extrait un article d'une section HTML"""
        try:
            # Extraction du titre
            title_selectors = ['h1', 'h2', 'h3', 'h4', '.title', '.headline', 'strong', 'b']
            title = ""
            title_elem = None
            
            for selector in title_selectors:
                title_elem = section.find(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if len(title) > 20:  # Titre suffisamment long
                        break
            
            if not title:
                return None
            
            # Extraction de l'URL
            link_elem = section.find('a', href=True)
            if not link_elem:
                # Chercher dans le titre
                if title_elem:
                    parent = title_elem.parent
                    if parent and parent.name == 'a':
                        link_elem = parent
                    else:
                        link_elem = title_elem.find_parent('a')
            
            url = ""
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('http'):
                    url = href
                elif href.startswith('/'):
                    url = f"https://tldr.tech{href}"
            
            # Extraction du résumé
            summary = self._extract_summary_from_section(section, title)
            
            # Extraction de la durée de lecture
            duration = self._extract_reading_time(section.get_text())
            
            if title and (url or summary):
                return {
                    'titre': self._clean_title(title),
                    'url': url,
                    'duree_lecture': duration,
                    'resume_tldr': summary,
                    'contenu_brut': section.get_text(strip=True)[:500],
                    'date_extraction': datetime.now().isoformat(),
                    'source': f'TLDR-{self.newsletter_type}',
                    'newsletter_type': self.newsletter_type
                }
                
        except Exception as e:
            logger.error(f"Error extracting article from section: {e}")
        
        return None
    
    def _extract_article_from_link(self, link, base_url: str) -> Dict[str, Any]:
        """Extrait un article à partir d'un lien externe"""
        try:
            url = link.get('href', '')
            title = link.get_text(strip=True)
            
            # Chercher le contexte autour du lien
            parent = link.parent
            context = ""
            
            # Remonter pour trouver le contexte
            for _ in range(3):  # Maximum 3 niveaux
                if parent:
                    context = parent.get_text(strip=True)
                    if len(context) > len(title) + 50:
                        break
                    parent = parent.parent
            
            # Extraire le résumé du contexte
            summary = self._extract_summary_from_context(context, title)
            duration = self._extract_reading_time(context)
            
            if title and url and len(title) > 10:
                return {
                    'titre': self._clean_title(title),
                    'url': url,
                    'duree_lecture': duration,
                    'resume_tldr': summary,
                    'contenu_brut': context[:500],
                    'date_extraction': datetime.now().isoformat(),
                    'source': f'TLDR-{self.newsletter_type}',
                    'newsletter_type': self.newsletter_type
                }
                
        except Exception as e:
            logger.error(f"Error extracting article from link: {e}")
        
        return None
    
    def _extract_summary_from_section(self, section, title: str) -> str:
        """Extrait le résumé d'une section"""
        text = section.get_text(strip=True)
        
        # Supprimer le titre du texte
        if title in text:
            text = text.replace(title, '', 1).strip()
        
        # Chercher des patterns de résumé
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Prendre les 2-3 premières phrases pertinentes
        summary_parts = []
        for sentence in sentences[:4]:
            if len(sentence) > 20 and not any(skip in sentence.lower() for skip in [
                'click here', 'read more', 'subscribe', 'minute read'
            ]):
                summary_parts.append(sentence)
                if len(' '.join(summary_parts)) > 150:
                    break
        
        summary = '. '.join(summary_parts[:3])
        return summary[:300] + "..." if len(summary) > 300 else summary
    
    def _extract_summary_from_context(self, context: str, title: str) -> str:
        """Extrait le résumé du contexte autour d'un lien"""
        if title in context:
            # Prendre le texte après le titre
            parts = context.split(title, 1)
            if len(parts) > 1:
                after_title = parts[1].strip()
                # Prendre la première phrase significative
                sentences = [s.strip() for s in after_title.split('.') if len(s.strip()) > 10]
                if sentences:
                    return sentences[0][:200]
        
        return ""
    
    def _extract_reading_time(self, text: str) -> str:
        """Extrait la durée de lecture du texte"""
        patterns = [
            r'(\d+)\s*(?:minute|min)\s*read',
            r'(\d+)\s*(?:minute|min)',
            r'read\s*(?:in\s*)?(\d+)\s*(?:minute|min)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} minute read"
        
        return ""
    
    def _clean_title(self, title: str) -> str:
        """Nettoie et formate le titre"""
        # Supprimer les caractères indésirables
        title = re.sub(r'[^\w\s\-\(\):\.,!?]', '', title)
        
        # Supprimer les patterns de durée du titre
        title = re.sub(r'\(\d+\s*(?:minute|min)\s*read\)', '', title, flags=re.IGNORECASE)
        
        # Nettoyer les espaces
        title = ' '.join(title.split())
        
        return title.strip()
    
    def _create_article_from_match(self, match, base_url: str) -> Dict[str, Any]:
        """Crée un article à partir d'une regex match"""
        try:
            full_match = match.group(0)
            
            # Extraction basique
            title = full_match
            if 'minute read' in full_match:
                parts = full_match.split('(')
                title = parts[0].strip()
            
            return {
                'titre': self._clean_title(title),
                'url': "",
                'duree_lecture': self._extract_reading_time(full_match),
                'resume_tldr': "",
                'contenu_brut': full_match,
                'date_extraction': datetime.now().isoformat(),
                'source': f'TLDR-{self.newsletter_type}',
                'newsletter_type': self.newsletter_type
            }
        except:
            return None
    
    def _clean_and_validate_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Nettoie, valide et traduit la liste d'articles (AMÉLIORATION)"""
        cleaned = []
        seen_titles = set()
        seen_urls = set()

        for article in articles:
            title = article.get('titre', '').strip()
            url = article.get('url', '').strip()
            summary = article.get('resume_tldr', '').strip()

            if (len(title) < 15 or  # Titre plus long requis
                title.lower() in seen_titles or
                (url and url in seen_urls) or
                any(skip in title.lower() for skip in [
                    'subscribe', 'unsubscribe', 'privacy policy', 
                    'terms of service', 'contact us', 'sponsor',
                    'advertise', 'newsletter', 'tldr', 'sign up'
                ])):
                continue

            if url:
                seen_urls.add(url)
            seen_titles.add(title.lower())

            # Traduction si activée
            if self.translator:
                article['titre_traduit'] = self.translate_text(title)
                article['resume_tldr_traduit'] = self.translate_text(summary)

            cleaned.append(article)

            if len(cleaned) >= self.max_articles:
                break

        return cleaned