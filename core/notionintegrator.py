import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionIntegrator:
    """Version améliorée - Stockage complet dans Notion (articles + synthèses + métadonnées)"""
    
    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.properties_cache = None
    
    def get_database_properties(self) -> Optional[Dict]:
        """Récupère les propriétés de la base de données"""
        if self.properties_cache:
            return self.properties_cache
            
        url = f"https://api.notion.com/v1/databases/{self.database_id}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            database_info = response.json()
            self.properties_cache = database_info.get('properties', {})
            
            logger.info(f"Propriétés Notion récupérées: {list(self.properties_cache.keys())}")
            return self.properties_cache
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des propriétés Notion: {e}")
            return None
    
    def format_value_for_notion(self, value: Any, property_type: str, property_name: str = "") -> Optional[Dict]:
        """Formate une valeur selon le type de propriété Notion"""
        
        if not value:
            return None
        
        try:
            if property_type == 'title':
                return {
                    "title": [
                        {
                            "text": {
                                "content": str(value)[:2000]  # Limite Notion
                            }
                        }
                    ]
                }
            
            elif property_type == 'rich_text':
                return {
                    "rich_text": [
                        {
                            "text": {
                                "content": str(value)[:2000]  # Limite Notion
                            }
                        }
                    ]
                }
            
            elif property_type == 'url':
                url_str = str(value)
                # Validation basique d'URL
                if not url_str.startswith(('http://', 'https://')):
                    url_str = 'https://' + url_str
                return {"url": url_str}
            
            elif property_type == 'select':
                return {"select": {"name": str(value)[:100]}}
            
            elif property_type == 'multi_select':
                if isinstance(value, list):
                    options = value
                else:
                    options = [opt.strip() for opt in str(value).split(',')]
                
                return {
                    "multi_select": [{"name": opt[:100]} for opt in options if opt][:25]
                }
            
            elif property_type == 'date':
                if isinstance(value, str):
                    if 'T' in value or len(value) == 10:
                        return {"date": {"start": value}}
                    else:
                        try:
                            parsed_date = datetime.strptime(value, "%Y-%m-%d")
                            return {"date": {"start": parsed_date.isoformat()[:10]}}
                        except ValueError:
                            logger.warning(f"Format de date non reconnu: {value}")
                            return None
                else:
                    return {"date": {"start": str(value)}}
            
            elif property_type == 'number':
                try:
                    return {"number": float(value)}
                except (ValueError, TypeError):
                    logger.warning(f"Impossible de convertir en nombre: {value}")
                    return None
            
            elif property_type == 'checkbox':
                return {"checkbox": bool(value)}
            
            else:
                logger.warning(f"Type de propriété non supporté: {property_type}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors du formatage de {property_name}: {e}")
            return None
    
    def add_article_to_notion(self, article: Dict[str, Any]) -> Optional[str]:
        """Ajoute un article individuel à Notion"""
        
        properties = self.get_database_properties()
        if not properties:
            logger.error("Impossible de récupérer les propriétés de la base Notion")
            return None
        
        notion_properties = {}
        
        # Mapping des propriétés d'article
        property_mapping = {
            'titre': 'titre',
            'url': 'url', 
            'resume_tldr': 'resume_tldr',
            'etat': 'etat',
            'categories_ia': 'categories_ia',
        }
        
        # Ajouter la date actuelle si pas fournie
        if 'date' not in article or not article['date']:
            article['date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Ajouter un état par défaut si pas fourni
        if 'etat' not in article or not article['etat']:
            article['etat'] = 'Nouveau'
        
        for article_key, notion_key in property_mapping.items():
            if article_key in article and notion_key in properties:
                property_type = properties[notion_key]['type']
                
                formatted_value = self.format_value_for_notion(
                    article[article_key], 
                    property_type,
                    notion_key
                )
                
                if formatted_value:
                    notion_properties[notion_key] = formatted_value
                    logger.debug(f"✅ Mappé '{article_key}' -> '{notion_key}' ({property_type})")
        
        if not notion_properties:
            logger.error("Aucune propriété valide trouvée pour l'article")
            return None
        
        # Vérifier qu'on a au moins un titre
        if 'titre' not in notion_properties:
            logger.error("Le titre est obligatoire pour créer un article")
            return None
        
        # Préparer les données pour l'API Notion
        data = {
            "parent": {"database_id": self.database_id},
            "properties": notion_properties
        }
        
        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                page_id = response.json().get('id', 'Unknown')
                logger.info(f"✅ Article ajouté à Notion: {article.get('titre', 'Sans titre')}")
                return page_id
            else:
                error_info = response.json()
                error_msg = error_info.get('message', 'Erreur inconnue')
                logger.error(f"❌ Erreur API Notion ({response.status_code}): {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'ajout de l'article: {e}")
            return None
    
    def add_synthesis_to_notion(self, synthesis_data: Dict[str, Any]) -> Optional[str]:
        """Ajoute une synthèse quotidienne à Notion comme article spécial"""
        
        # Créer un article spécial pour la synthèse
        synthesis_article = {
            'titre': f"📊 Synthèse TLDR {synthesis_data.get('newsletter_type', 'tech')} - {synthesis_data.get('date_formatted', 'N/A')}",
            'url': '',  # Pas d'URL pour une synthèse
            'resume_tldr': synthesis_data.get('synthesis', '')[:2000],  # Limité par Notion
            'etat': 'Synthèse',
            'categories_ia': ['Synthèse', 'IA-Generated'],
        }
        
        return self.add_article_to_notion(synthesis_article)
    
    def add_daily_report_to_notion(self, daily_results: Dict[str, Any]) -> Optional[str]:
        """Ajoute un rapport quotidien complet à Notion"""
        
        # Préparer le résumé du rapport
        report_summary = f"""📈 RAPPORT QUOTIDIEN
        
🗓️ Date: {daily_results.get('date_formatted', 'N/A')} ({daily_results.get('day_name', 'N/A')})
📰 Articles extraits: {daily_results.get('articles_extracted', 0)}
💾 Articles stockés: {daily_results.get('articles_stored', 0)}
⏱️ Temps de traitement: {daily_results.get('processing_time', 0)}s
✅ Succès: {'Oui' if daily_results.get('success', False) else 'Non'}

🎵 Fichier audio: {'Généré' if daily_results.get('audio_file') else 'Non généré'}
"""
        
        if daily_results.get('errors'):
            report_summary += f"\n❌ Erreurs: {', '.join(daily_results['errors'])}"
        
        # Créer un article spécial pour le rapport
        report_article = {
            'titre': f"📈 Rapport quotidien TLDR {daily_results.get('newsletter_type', 'tech')} - {daily_results.get('date_formatted', 'N/A')}",
            'url': daily_results.get('audio_file', ''),  # Chemin vers le fichier audio
            'resume_tldr': report_summary[:2000],
            'etat': 'Rapport' if daily_results.get('success', False) else 'Erreur',
            'categories_ia': ['Rapport', 'Métadonnées'],
        }
        
        return self.add_article_to_notion(report_article)
    
    def bulk_add_articles(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Ajoute plusieurs articles en lot et retourne les IDs créés"""
        page_ids = []
        
        logger.info(f"📦 Ajout en lot de {len(articles)} articles à Notion...")
        
        for i, article in enumerate(articles, 1):
            logger.info(f"📝 Traitement article {i}/{len(articles)}: {article.get('titre', 'Sans titre')[:50]}...")
            
            page_id = self.add_article_to_notion(article)
            if page_id:
                page_ids.append(page_id)
            
            # Petite pause pour éviter de surcharger l'API Notion
            if i % 10 == 0:
                import time
                time.sleep(1)
        
        logger.info(f"✅ {len(page_ids)}/{len(articles)} articles ajoutés avec succès à Notion")
        return page_ids
    
    def save_complete_daily_results(self, daily_results: Dict[str, Any]) -> Dict[str, str]:
        """Sauvegarde complète des résultats quotidiens dans Notion"""
        
        saved_ids = {}
        
        try:
            # 1. Ajouter tous les articles individuels
            if daily_results.get('articles'):
                logger.info("💾 Sauvegarde des articles individuels...")
                article_ids = self.bulk_add_articles(daily_results['articles'])
                saved_ids['articles'] = article_ids
                
                # Mettre à jour le nombre d'articles stockés
                daily_results['articles_stored'] = len(article_ids)
            
            # 2. Ajouter la synthèse comme article spécial
            if daily_results.get('synthesis'):
                logger.info("💾 Sauvegarde de la synthèse...")
                synthesis_id = self.add_synthesis_to_notion(daily_results)
                if synthesis_id:
                    saved_ids['synthesis'] = synthesis_id
            
            # 3. Ajouter le rapport quotidien
            logger.info("💾 Sauvegarde du rapport quotidien...")
            report_id = self.add_daily_report_to_notion(daily_results)
            if report_id:
                saved_ids['report'] = report_id
            
            logger.info(f"✅ Sauvegarde Notion terminée: {len(saved_ids)} éléments créés")
            return saved_ids
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde complète: {e}")
            return saved_ids
    
    def test_connection(self) -> bool:
        """Teste la connexion à Notion"""
        properties = self.get_database_properties()
        return properties is not None
    
    def list_database_properties(self) -> Dict:
        """Retourne les propriétés de la base de données pour debug"""
        return self.get_database_properties() or {}

# Fonction utilitaire pour tester la connexion
def test_notion_connection(token: str, database_id: str) -> bool:
    """
    Teste rapidement la connexion à Notion
    
    Returns:
        bool: True si la connexion fonctionne
    """
    try:
        notion = NotionIntegrator(token, database_id)
        return notion.test_connection()
    except Exception as e:
        logger.error(f"Erreur de test de connexion: {e}")
        return False
