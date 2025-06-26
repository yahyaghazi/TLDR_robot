import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, date
from typing import List, Dict, Any
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TLDRScraper:
    """Niveau 1 - Découverte: Extraction des articles TLDR Tech optimisée"""
    
    def __init__(self, newsletter_type="tech"):
        self.newsletter_type = newsletter_type
        self.base_url = f"https://tldr.tech/{newsletter_type}"
        
        # Headers optimisés pour TLDR
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
    def get_todays_newsletter(self) -> str:
        """Récupère l'URL de la newsletter du jour"""
        today = date.today().strftime("%Y-%m-%d")
        return f"{self.base_url}/{today}"
    
    def get_newsletter_by_date(self, target_date: str) -> str:
        """Récupère l'URL pour une date spécifique (format YYYY-MM-DD)"""
        return f"{self.base_url}/{target_date}"
    
    def scrape_articles(self, url: str = None) -> List[Dict[str, Any]]:
        """Extrait tous les articles de la newsletter TLDR"""
        if not url:
            url = self.get_todays_newsletter()
            
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
            
            # Filtrer et nettoyer les articles
            cleaned_articles = self._clean_and_validate_articles(articles)
            
            logger.info(f"Extracted {len(cleaned_articles)} articles from {url}")
            return cleaned_articles
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
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
                
                if articles:
                    break
        
        return articles
    
    def _scrape_method_links(self, soup, url: str) -> List[Dict[str, Any]]:
        """Méthode 2: Extraction basée sur les liens externes"""
        articles = []
        
        # Recherche de tous les liens externes
        external_links = soup.find_all('a', href=re.compile(r'^https?://(?!tldr\.tech)'))
        
        for link in external_links:
            # Éviter les liens de navigation/footer
            if self._is_article_link(link):
                article = self._extract_article_from_link(link, url)
                if article:
                    articles.append(article)
        
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
            for match in matches:
                article = self._create_article_from_match(match, url)
                if article:
                    articles.append(article)
        
        return articles
    
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
    
    def _is_article_link(self, link) -> bool:
        """Vérifie si un lien pointe vers un article"""
        href = link.get('href', '')
        text = link.get_text(strip=True)
        
        # Exclusions
        exclusions = [
            'unsubscribe', 'subscribe', 'footer', 'header',
            'privacy', 'terms', 'about', 'contact', 'sponsor',
            'twitter.com', 'linkedin.com', 'facebook.com',
            'tldr.tech/unsubscribe', 'tldr.tech/jobs'
        ]
        
        for exclusion in exclusions:
            if exclusion in href.lower() or exclusion in text.lower():
                return False
        
        # Critères positifs
        if len(text) > 20 and any(domain in href for domain in [
            'github.com', 'medium.com', 'dev.to', 'hackernews',
            'techcrunch.com', 'wired.com', 'arstechnica.com',
            'theverge.com', 'engadget.com'
        ]):
            return True
            
        return len(text) > 15 and href.startswith('http')
    
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
        """Nettoie et valide la liste d'articles"""
        cleaned = []
        seen_titles = set()
        
        for article in articles:
            title = article.get('titre', '').strip()
            
            # Validation
            if (len(title) < 10 or 
                title.lower() in seen_titles or
                any(skip in title.lower() for skip in [
                    'subscribe', 'unsubscribe', 'privacy policy', 
                    'terms of service', 'contact us'
                ])):
                continue
            
            seen_titles.add(title.lower())
            cleaned.append(article)
        
        return cleaned
