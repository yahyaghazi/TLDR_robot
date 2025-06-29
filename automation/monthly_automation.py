#!/usr/bin/env python3
"""
Automatisation TLDR modifiée pour stockage exclusif dans Notion
Plus de fichiers JSON - tout va dans la base de données Notion
Version complète et améliorée
"""

import requests
import ollama
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List
import time
import sys
import os

# Ajouter les chemins pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Imports du projet
from core.tdlrscraper import TLDRScraper
from core.notionintegrator import NotionIntegrator
from core.aiprocessor import AIProcessor
from core.ttsgenerator import TTSGenerator
from utils.smartdatehandler import SmartDateHandler

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monthly_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedNotionIntegrator:
    """Version améliorée du NotionIntegrator pour le stockage complet"""
    
    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.properties_cache = None
    
    def test_connection(self) -> bool:
        """Test la connexion à Notion"""
        try:
            url = f"https://api.notion.com/v1/databases/{self.database_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            database_info = response.json()
            logger.info(f"✅ Connexion Notion réussie: {database_info.get('title', [{}])[0].get('plain_text', 'Base inconnue')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion Notion: {e}")
            return False
    
    def get_database_properties(self) -> Dict:
        """Récupère les propriétés de la base de données"""
        if self.properties_cache:
            return self.properties_cache
            
        try:
            url = f"https://api.notion.com/v1/databases/{self.database_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            database_info = response.json()
            self.properties_cache = database_info.get('properties', {})
            
            logger.info(f"Propriétés récupérées: {list(self.properties_cache.keys())}")
            return self.properties_cache
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des propriétés: {e}")
            return {}
    
    def format_value_for_notion(self, value: Any, property_type: str, property_name: str = "") -> Dict:
        """Formate une valeur selon le type de propriété Notion"""
        
        if not value:
            return None
        
        if property_type == 'title':
            return {
                "title": [
                    {
                        "text": {
                            "content": str(value)[:100]  # Limitation Notion
                        }
                    }
                ]
            }
        
        elif property_type == 'rich_text':
            return {
                "rich_text": [
                    {
                        "text": {
                            "content": str(value)[:2000]  # Limitation Notion
                        }
                    }
                ]
            }
        
        elif property_type == 'url':
            return {"url": str(value) if str(value).startswith('http') else None}
        
        elif property_type == 'select':
            return {"select": {"name": str(value)[:100]}}
        
        elif property_type == 'multi_select':
            if isinstance(value, list):
                options = value
            else:
                options = [opt.strip() for opt in str(value).split(',')]
            
            return {
                "multi_select": [{"name": opt[:100]} for opt in options if opt][:10]  # Max 10 options
            }
                        
        elif property_type == 'number':
            try:
                return {"number": float(value)}
            except (ValueError, TypeError):
                return None
        
        elif property_type == 'checkbox':
            return {"checkbox": bool(value)}
        
        elif property_type == 'date':
            try:
                if isinstance(value, str):
                    # Essayer de parser la date
                    from datetime import datetime
                    if 'T' in value:
                        date_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    else:
                        date_obj = datetime.strptime(value, '%Y-%m-%d')
                    return {"date": {"start": date_obj.isoformat()}}
                elif hasattr(value, 'isoformat'):
                    return {"date": {"start": value.isoformat()}}
            except:
                pass
            return None
        
        else:
            logger.warning(f"Type de propriété non supporté: {property_type}")
            return None
    
    def add_article_to_notion(self, article: Dict[str, Any]) -> bool:
        """Ajoute un article à la base de données Notion"""
        
        properties = self.get_database_properties()
        if not properties:
            logger.error("Impossible de récupérer les propriétés de la base")
            return False
        
        notion_properties = {}
        
        # Mapping intelligent basé sur les clés communes
        property_mapping = {
            'titre': ['titre', 'Titre', 'Title', 'Name'],
            'url': ['url', 'URL', 'Link', 'Lien'],
            'resume_tldr': ['resume_tldr', 'Résumé', 'Resume', 'Summary', 'Description'],
            'etat': ['etat', 'État', 'Etat', 'Status', 'State'],
            'categories_ia': ['categories_ia', 'Catégories', 'Categories', 'Tags'],
            'duree_lecture': ['duree_lecture', 'Durée', 'Duration', 'Reading Time'],
            'date_extraction': ['date_extraction', 'Date', 'Created', 'Date ajout'],
            'source': ['source', 'Source', 'Origin']
        }
        
        # Trouver les correspondances
        for article_key, possible_notion_keys in property_mapping.items():
            if article_key in article:
                # Chercher la première clé qui existe dans les propriétés Notion
                notion_key = None
                for possible_key in possible_notion_keys:
                    if possible_key in properties:
                        notion_key = possible_key
                        break
                
                if notion_key:
                    property_type = properties[notion_key]['type']
                    formatted_value = self.format_value_for_notion(
                        article[article_key], 
                        property_type,
                        notion_key
                    )
                    
                    if formatted_value:
                        notion_properties[notion_key] = formatted_value
                        logger.debug(f"✅ Mappé '{article_key}' -> '{notion_key}' ({property_type})")
        
        # Valeurs par défaut si pas trouvées
        if not notion_properties:
            # Essayer avec le titre au minimum
            title_fields = ['titre', 'Titre', 'Title', 'Name']
            for field in title_fields:
                if field in properties and properties[field]['type'] == 'title':
                    notion_properties[field] = {
                        "title": [
                            {
                                "text": {
                                    "content": article.get('titre', 'Article sans titre')[:100]
                                }
                            }
                        ]
                    }
                    break
        
        if not notion_properties:
            logger.error("Aucune propriété valide trouvée pour l'article")
            return False
        
        # Préparer les données pour l'API Notion
        data = {
            "parent": {"database_id": self.database_id},
            "properties": notion_properties
        }
        
        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Article ajouté à Notion: {article.get('titre', 'Sans titre')[:50]}")
                return response.json()['id']
            else:
                error_info = response.json()
                error_msg = error_info.get('message', 'Erreur inconnue')
                logger.error(f"❌ Erreur API Notion: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur de requête Notion: {e}")
            return False
    
    def bulk_add_articles(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Ajoute plusieurs articles en lot"""
        page_ids = []
        for i, article in enumerate(articles, 1):
            logger.info(f"📝 Ajout article {i}/{len(articles)} à Notion...")
            page_id = self.add_article_to_notion(article)
            if page_id:
                page_ids.append(page_id)
            
            # Petite pause pour éviter les limites de taux
            if i % 3 == 0:
                time.sleep(0.5)
        
        return page_ids
    
    def save_complete_daily_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Sauvegarde complète des résultats journaliers dans Notion"""
        saved_ids = {
            'articles': [],
            'summary_id': None,
            'report_id': None
        }
        
        try:
            # 1. Sauvegarder tous les articles
            if 'articles' in results and results['articles']:
                logger.info(f"💾 Sauvegarde de {len(results['articles'])} articles...")
                article_ids = self.bulk_add_articles(results['articles'])
                saved_ids['articles'] = article_ids
                logger.info(f"✅ {len(article_ids)} articles sauvegardés dans Notion")
            
            # 2. Créer un résumé de synthèse
            if results.get('synthesis'):
                logger.info("📊 Création du résumé de synthèse...")
                synthesis_article = {
                    'titre': f"📊 SYNTHÈSE {results['newsletter_type'].upper()} {results['date_formatted']}",
                    'url': '',
                    'resume_tldr': results['synthesis'][:2000],
                    'etat': 'Synthèse',
                    'date_extraction': results['date'],
                    'categories_ia': ['Synthèse', 'Daily', 'Auto'],
                    'source': f"TLDR-{results['newsletter_type']}-Synthesis"
                }
                
                synthesis_id = self.add_article_to_notion(synthesis_article)
                if synthesis_id:
                    saved_ids['summary_id'] = synthesis_id
                    logger.info("✅ Synthèse sauvegardée dans Notion")
            
            # 3. Créer un rapport de traitement
            logger.info("📋 Création du rapport de traitement...")
            report_content = f"""📈 RAPPORT AUTOMATISATION {results['date_formatted']}

✅ Articles extraits: {results['articles_extracted']}
💾 Articles stockés: {results['articles_stored']}
🎵 Audio généré: {'✅' if results.get('audio_file') else '❌'}
⏱️ Temps de traitement: {results.get('processing_time', 0)}s

🔗 Fichier audio: {results.get('audio_file', 'Non généré')}

📊 Statut: {'✅ Succès' if results['success'] else '❌ Échec'}"""

            if results.get('errors'):
                report_content += f"\n\n❌ Erreurs:\n" + "\n".join(f"• {error}" for error in results['errors'])
            
            report_article = {
                'titre': f"📋 RAPPORT {results['newsletter_type'].upper()} {results['date_formatted']}",
                'url': '',
                'resume_tldr': report_content[:2000],
                'etat': 'Rapport',
                'date_extraction': results['date'],
                'categories_ia': ['Rapport', 'Automation', 'Log'],
                'source': f"TLDR-{results['newsletter_type']}-Report"
            }
            
            report_id = self.add_article_to_notion(report_article)
            if report_id:
                saved_ids['report_id'] = report_id
                logger.info("✅ Rapport sauvegardé dans Notion")
            
            return saved_ids
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde complète: {e}")
            return saved_ids


class MonthlyTLDRAutomationNotion:
    """Automatisation mensuelle avec stockage exclusif dans Notion"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialisation des composants
        self.scraper = TLDRScraper(
            newsletter_type=config.get('newsletter_type', 'tech'),
            max_articles=config.get('max_articles', 15),
            country_code=config.get('country_code', 'US')
        )
        
        # Notion OBLIGATOIRE pour cette version
        if not config.get('notion_token') or not config.get('notion_database_id'):
            raise ValueError("❌ Token et Database ID Notion sont obligatoires pour cette version!")
        
        self.notion = EnhancedNotionIntegrator(
            config['notion_token'], 
            config['notion_database_id']
        )
        
        # IA Processor avec Ollama
        self.ai_processor = AIProcessor(
            model=config.get('ollama_model', 'nous-hermes2:latest'),
            base_url=config.get('ollama_base_url', 'http://localhost:11434'),
            max_articles_per_batch=config.get('max_articles_per_batch', 12)
        )
        
        # TTS Generator
        audio_dir = Path(config.get('audio_output_dir', './audio_summaries'))
        audio_dir.mkdir(exist_ok=True)
        self.tts = TTSGenerator(output_dir=str(audio_dir))
        
        # Gestionnaire de dates
        self.date_handler = SmartDateHandler(config.get('country_code', 'US'))
        
        # Test de connexion Notion au démarrage
        if not self.notion.test_connection():
            raise ConnectionError("❌ Impossible de se connecter à Notion!")
        
        logger.info("✅ NotionIntegrator connecté et opérationnel")
    
    def get_business_days_for_month(self, year: int, month: int) -> List[date]:
        """Récupère tous les jours ouvrables d'un mois donné"""
        start_date = date(year, month, 1)
        
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        business_days = []
        current_date = start_date
        
        while current_date < end_date:
            if self.date_handler.is_business_day(current_date):
                business_days.append(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"📅 {len(business_days)} jours ouvrables trouvés pour {month:02d}/{year}")
        return business_days
    
    def process_single_day(self, target_date: date) -> Dict[str, Any]:
        """Traite une journée spécifique et stocke tout dans Notion"""
        logger.info(f"🔄 Traitement du {target_date.strftime('%Y-%m-%d')} ({target_date.strftime('%A')})")
        
        results = {
            'date': target_date.isoformat(),
            'date_formatted': target_date.strftime('%Y-%m-%d'),
            'day_name': target_date.strftime('%A'),
            'newsletter_type': self.config.get('newsletter_type', 'tech'),
            'articles_extracted': 0,
            'articles_stored': 0,
            'synthesis': '',
            'audio_file': None,
            'notion_ids': {},  # IDs des éléments créés dans Notion
            'errors': [],
            'processing_time': 0,
            'success': False
        }
        
        start_time = time.time()
        
        try:
            # 1. Extraction des articles
            date_str = target_date.strftime('%Y-%m-%d')
            newsletter_url = self.scraper.get_newsletter_by_date(date_str)
            
            logger.info(f"📰 Extraction depuis: {newsletter_url}")
            articles = self.scraper.scrape_articles(newsletter_url)
            
            results['articles_extracted'] = len(articles)
            
            if not articles:
                logger.warning(f"❌ Aucun article trouvé pour {date_str}")
                results['errors'].append(f"Aucun article extrait pour {date_str}")
                return results
            
            logger.info(f"✅ {len(articles)} articles extraits")
            
            # 2. Traitement IA (catégorisation et synthèse)
            logger.info("🤖 Traitement IA en cours...")
            categorized_articles = self.ai_processor.categorize_articles(articles)
            synthesis = self.ai_processor.synthesize_articles(categorized_articles)
            
            results['synthesis'] = synthesis
            results['articles'] = categorized_articles
            
            # 3. Génération audio
            logger.info("🎵 Génération audio...")
            date_formatted = target_date.strftime('%d %B %Y')
            synthesis_with_date = f"Résumé TLDR {self.config.get('newsletter_type', 'tech')} du {date_formatted}.\n\n{synthesis}"
            
            audio_filename = f"tldr_{self.config.get('newsletter_type', 'tech')}_{date_str}.wav"
            audio_dir = Path(self.config.get('audio_output_dir', './audio_summaries'))
            audio_path = audio_dir / audio_filename
            
            try:
                self.tts.engine.save_to_file(synthesis_with_date, str(audio_path))
                self.tts.engine.runAndWait()
                results['audio_file'] = str(audio_path)
                logger.info(f"🎵 Audio généré: {audio_filename}")
            except Exception as e:
                logger.error(f"❌ Erreur génération audio: {e}")
                results['errors'].append(f"Erreur audio: {str(e)}")
            
            # 4. STOCKAGE COMPLET DANS NOTION (remplace les fichiers JSON)
            logger.info("💾 Sauvegarde complète dans Notion...")
            
            try:
                saved_ids = self.notion.save_complete_daily_results(results)
                results['notion_ids'] = saved_ids
                results['articles_stored'] = len(saved_ids.get('articles', []))
                
                logger.info(f"✅ Données sauvegardées dans Notion:")
                for element_type, element_ids in saved_ids.items():
                    if isinstance(element_ids, list):
                        logger.info(f"   📝 {element_type}: {len(element_ids)} éléments")
                    else:
                        logger.info(f"   📝 {element_type}: {'✅' if element_ids else '❌'}")
                
                results['success'] = True
                
            except Exception as e:
                logger.error(f"❌ Erreur sauvegarde Notion: {e}")
                results['errors'].append(f"Erreur Notion: {str(e)}")
            
            if results['success']:
                logger.info(f"✅ Journée {date_str} traitée et stockée avec succès dans Notion")
            
        except Exception as e:
            logger.error(f"❌ Erreur critique pour {target_date}: {e}")
            results['errors'].append(f"Erreur critique: {str(e)}")
        
        finally:
            results['processing_time'] = round(time.time() - start_time, 2)
        
        return results
    
    def process_month(self, year: int, month: int, delay_between_days: float = 2.0) -> Dict[str, Any]:
        """Traite un mois complet et stocke tout dans Notion"""
        logger.info(f"🚀 Début du traitement mensuel pour {month:02d}/{year}")
        
        business_days = self.get_business_days_for_month(year, month)
        
        monthly_results = {
            'month': f"{year}-{month:02d}",
            'newsletter_type': self.config.get('newsletter_type', 'tech'),
            'total_business_days': len(business_days),
            'processed_days': 0,
            'successful_days': 0,
            'failed_days': 0,
            'total_articles': 0,
            'total_articles_stored': 0,
            'total_processing_time': 0,
            'daily_results': [],
            'all_notion_ids': [],  # Tous les IDs Notion créés
            'summary': '',
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        start_time = time.time()
        
        # Traiter chaque jour
        for i, business_day in enumerate(business_days, 1):
            logger.info(f"📊 Progression: {i}/{len(business_days)} jours")
            
            day_result = self.process_single_day(business_day)
            monthly_results['daily_results'].append(day_result)
            
            # Mise à jour des statistiques
            monthly_results['processed_days'] += 1
            monthly_results['total_articles'] += day_result['articles_extracted']
            monthly_results['total_articles_stored'] += day_result['articles_stored']
            monthly_results['total_processing_time'] += day_result['processing_time']
            
            if day_result['success']:
                monthly_results['successful_days'] += 1
                # Collecter tous les IDs Notion
                if day_result.get('notion_ids'):
                    for key, value in day_result['notion_ids'].items():
                        if isinstance(value, list):
                            monthly_results['all_notion_ids'].extend(value)
                        elif value:
                            monthly_results['all_notion_ids'].append(value)
            else:
                monthly_results['failed_days'] += 1
            
            # Délai entre les jours
            if i < len(business_days):
                logger.info(f"⏳ Pause de {delay_between_days}s avant le jour suivant...")
                time.sleep(delay_between_days)
        
        # Finalisation
        monthly_results['end_time'] = datetime.now().isoformat()
        monthly_results['total_processing_time'] = round(time.time() - start_time, 2)
        
        # Génération du résumé mensuel
        monthly_results['summary'] = self._generate_monthly_summary(monthly_results)
        
        # OPTIONNEL: Créer un résumé mensuel dans Notion
        try:
            monthly_summary_article = {
                'titre': f"📊 RÉSUMÉ MENSUEL TLDR {monthly_results['newsletter_type'].upper()} {monthly_results['month']}",
                'url': '',
                'resume_tldr': monthly_results['summary'][:2000],
                'duree_lecture': f"{monthly_results['total_processing_time']:.1f}s",
                'etat': 'Résumé Mensuel',
                'date_extraction': f"{year}-{month:02d}-01",
                'categories_ia': ['Résumé', 'Mensuel', 'Métadonnées'],
                'source': f"TLDR-{monthly_results['newsletter_type']}-Monthly"
            }
            
            monthly_id = self.notion.add_article_to_notion(monthly_summary_article)
            if monthly_id:
                logger.info(f"📊 Résumé mensuel créé dans Notion")
                monthly_results['monthly_notion_id'] = monthly_id
                
        except Exception as e:
            logger.error(f"❌ Erreur création résumé mensuel: {e}")
        
        logger.info(f"🎉 Traitement mensuel terminé - Tout stocké dans Notion!")
        
        return monthly_results
    
    def _generate_monthly_summary(self, monthly_results: Dict[str, Any]) -> str:
        """Génère un résumé du mois traité"""
        total_days = monthly_results['total_business_days']
        successful = monthly_results['successful_days']
        failed = monthly_results['failed_days']
        total_articles = monthly_results['total_articles']
        total_stored = monthly_results['total_articles_stored']
        total_time = monthly_results['total_processing_time']
        newsletter_type = monthly_results['newsletter_type']
        
        summary = f"""📊 RÉSUMÉ MENSUEL TLDR {newsletter_type.upper()} {monthly_results['month']}

✅ Jours traités avec succès: {successful}/{total_days}
❌ Jours échoués: {failed}/{total_days}
📰 Total articles extraits: {total_articles}
💾 Total articles stockés dans Notion: {total_stored}
⏱️ Temps total de traitement: {total_time:.1f}s
📈 Moyenne articles/jour: {total_articles/max(total_days, 1):.1f}
🎵 Fichiers audio générés: {successful}

Taux de réussite: {(successful/max(total_days, 1))*100:.1f}%

💾 STOCKAGE: Toutes les données sont maintenant dans votre base Notion!
📝 Types d'éléments créés: Articles individuels, Synthèses quotidiennes, Rapports quotidiens
🗂️ Total éléments Notion: {len(monthly_results.get('all_notion_ids', []))}"""

        if failed > 0:
            failed_dates = [
                result['date_formatted'] 
                for result in monthly_results['daily_results'] 
                if not result['success']
            ]
            summary += f"\n\n❌ Jours échoués: {', '.join(failed_dates)}"
        
        return summary


def main():
    """Fonction principale avec stockage Notion exclusif"""
    
    # Configuration - TOKEN NOTION OBLIGATOIRE
    config = {
        'newsletter_type': 'tech',
        'max_articles': 15,
        'country_code': 'US',
        
        # NOTION OBLIGATOIRE pour cette version
        'notion_token': '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',
        'notion_database_id': '21e7d425746b80a0a867e9adfbcbff26',
        
        # Ollama
        'ollama_model': 'nous-hermes2:latest',
        'ollama_base_url': 'http://localhost:11434',
        'max_articles_per_batch': 12,
        
        # Dossiers de sortie (pour l'audio uniquement)
        'audio_output_dir': './audio_summaries'
    }
    
    # Gestion des arguments
    if len(sys.argv) >= 3:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
    else:
        # Par défaut: juin 2025
        year = 2025
        month = 6
    
    # Newsletter type depuis les arguments
    if len(sys.argv) >= 4:
        config['newsletter_type'] = sys.argv[3]
    
    logger.info(f"🎯 Configuration: TLDR {config['newsletter_type']} pour {month:02d}/{year}")
    logger.info(f"💾 Mode: Stockage exclusif dans Notion")
    
    # Vérification d'Ollama
    try:
        test_response = ollama.chat(
            model=config['ollama_model'],
            messages=[{'role': 'user', 'content': 'Test'}],
            options={'num_predict': 5}
        )
        logger.info("✅ Ollama opérationnel")
    except Exception as e:
        logger.error(f"❌ Erreur Ollama: {e}")
        logger.error("Assurez-vous qu'Ollama est lancé: ollama serve")
        return
    
    # Initialisation et lancement
    try:
        automation = MonthlyTLDRAutomationNotion(config)
        
        # Traitement du mois avec délai de 3 secondes entre les jours
        monthly_results = automation.process_month(year, month, delay_between_days=3.0)
        
        # Affichage du résumé final
        print("\n" + "="*60)
        print("📊 RÉSULTATS FINAUX")
        print("="*60)
        print(monthly_results['summary'])
        print("="*60)
        
        # Statistiques détaillées
        successful_days = [r for r in monthly_results['daily_results'] if r['success']]
        if successful_days:
            audio_dir = Path(config['audio_output_dir'])
            
            print(f"\n🎵 {len(successful_days)} fichiers audio générés dans:")
            print(f"   📁 {audio_dir}")
            
            print(f"\n💾 {len(monthly_results.get('all_notion_ids', []))} éléments créés dans Notion:")
            print(f"   🗂️ Articles individuels, synthèses et rapports")
            print(f"   🔗 Consultez votre base Notion pour voir tous les résultats")
        
        if monthly_results['failed_days'] > 0:
            print(f"\n❌ {monthly_results['failed_days']} jours ont échoué - voir les logs pour plus de détails")
        
        # Affichage du lien vers la base Notion
        print(f"\n🔗 ACCÈS À VOS DONNÉES:")
        print(f"   📊 Base Notion: https://notion.so/{config['notion_database_id'].replace('-', '')}")
        print(f"   🎵 Audio local: {audio_dir}")
    
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("TLDR Monthly Automation - Version Notion Intégrée")
    print("Usage: python monthly_automation.py [YEAR] [MONTH] [NEWSLETTER_TYPE]")
    print("Exemple: python monthly_automation.py 2025 6 tech")
    print("Types disponibles: tech, ai, crypto, marketing, design, webdev")
    print("Mode: Stockage exclusif dans Notion (plus de fichiers JSON)")
    print("-" * 60)
    
    main()