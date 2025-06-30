#!/usr/bin/env python3
"""
Script d'automatisation mensuelle pour TLDR
Génère les résumés audio pour tous les jours ouvrables d'un mois donné
"""

import json
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, Any, List
import time
import sys
import os

# Import des modules du projet
from tdlrscraper import TLDRScraper
from notionintegrator import NotionIntegrator
from aiprocessor import AIProcessor
from ttsgenerator import TTSGenerator
from smartdatehandler import SmartDateHandler

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


class MonthlyTLDRAutomation:
    """Automatisation mensuelle complète des newsletters TLDR"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialisation des composants
        self.scraper = TLDRScraper(
            newsletter_type=config.get('newsletter_type', 'tech'),
            max_articles=config.get('max_articles', 15),
            country_code=config.get('country_code', 'US')
        )
        
        # Notion (optionnel si pas de token)
        self.notion = None
        if config.get('notion_token') and config.get('notion_database_id'):
            self.notion = NotionIntegrator(
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
        self.tts = TTSGenerator(
            output_dir=config.get('audio_output_dir', './audio_summaries')
        )
        
        # Gestionnaire de dates
        self.date_handler = SmartDateHandler(config.get('country_code', 'US'))
        
        # Création des dossiers de sortie
        self._create_output_directories()
    
    def _create_output_directories(self):
        """Crée les dossiers de sortie nécessaires"""
        dirs = [
            self.config.get('audio_output_dir', './audio_summaries'),
            self.config.get('json_output_dir', './json_results'),
            self.config.get('logs_dir', './logs')
        ]
        
        for dir_path in dirs:
            Path(dir_path).mkdir(exist_ok=True)
    
    def get_business_days_for_month(self, year: int, month: int) -> List[date]:
        """Récupère tous les jours ouvrables d'un mois donné"""
        # Premier jour du mois
        start_date = date(year, month, 1)
        
        # Premier jour du mois suivant (pour calculer la fin)
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
        """Traite une journée spécifique"""
        logger.info(f"🔄 Traitement du {target_date.strftime('%Y-%m-%d')} ({target_date.strftime('%A')})")
        
        results = {
            'date': target_date.isoformat(),
            'date_formatted': target_date.strftime('%Y-%m-%d'),
            'day_name': target_date.strftime('%A'),
            'articles_extracted': 0,
            'articles_stored': 0,
            'synthesis': '',
            'audio_file': None,
            'json_file': None,
            'errors': [],
            'processing_time': 0,
            'success': False
        }
        
        start_time = time.time()
        
        try:
            # 1. Extraction des articles pour cette date spécifique
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
            
            # 3. Stockage Notion (si configuré)
            if self.notion:
                logger.info("💾 Stockage dans Notion...")
                try:
                    page_ids = self.notion.bulk_add_articles(categorized_articles)
                    results['articles_stored'] = len(page_ids)
                    logger.info(f"✅ {len(page_ids)} articles stockés dans Notion")
                except Exception as e:
                    logger.error(f"❌ Erreur Notion: {e}")
                    results['errors'].append(f"Erreur Notion: {str(e)}")
            
            # 4. Génération audio
            logger.info("🎵 Génération audio...")
            audio_filename = f"tldr_{self.config.get('newsletter_type', 'tech')}_{date_str}.wav"
            audio_path = Path(self.config.get('audio_output_dir', './audio_summaries')) / audio_filename
            
            # Personnaliser le TTS pour inclure la date
            date_formatted = target_date.strftime('%d %B %Y')
            synthesis_with_date = f"Résumé TLDR {self.config.get('newsletter_type', 'tech')} du {date_formatted}.\n\n{synthesis}"
            
            try:
                self.tts.engine.save_to_file(synthesis_with_date, str(audio_path))
                self.tts.engine.runAndWait()
                results['audio_file'] = str(audio_path)
                logger.info(f"🎵 Audio généré: {audio_path}")
            except Exception as e:
                logger.error(f"❌ Erreur génération audio: {e}")
                results['errors'].append(f"Erreur audio: {str(e)}")
            
            # 5. Sauvegarde JSON
            json_filename = f"tldr_{self.config.get('newsletter_type', 'tech')}_{date_str}.json"
            json_path = Path(self.config.get('json_output_dir', './json_results')) / json_filename
            
            # Enrichir les résultats avec les articles
            results['articles'] = categorized_articles
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            results['json_file'] = str(json_path)
            results['success'] = True
            
            logger.info(f"✅ Journée {date_str} traitée avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur critique pour {target_date}: {e}")
            results['errors'].append(f"Erreur critique: {str(e)}")
        
        finally:
            results['processing_time'] = round(time.time() - start_time, 2)
        
        return results
    
    def process_month(self, year: int, month: int, delay_between_days: float = 2.0) -> Dict[str, Any]:
        """Traite un mois complet"""
        logger.info(f"🚀 Début du traitement mensuel pour {month:02d}/{year}")
        
        # Récupérer tous les jours ouvrables
        business_days = self.get_business_days_for_month(year, month)
        
        monthly_results = {
            'month': f"{year}-{month:02d}",
            'total_business_days': len(business_days),
            'processed_days': 0,
            'successful_days': 0,
            'failed_days': 0,
            'total_articles': 0,
            'total_processing_time': 0,
            'daily_results': [],
            'summary': '',
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        start_time = time.time()
        
        # Traiter chaque jour
        for i, business_day in enumerate(business_days, 1):
            logger.info(f"📊 Progression: {i}/{len(business_days)} jours")
            
            # Traitement du jour
            day_result = self.process_single_day(business_day)
            monthly_results['daily_results'].append(day_result)
            
            # Mise à jour des statistiques
            monthly_results['processed_days'] += 1
            monthly_results['total_articles'] += day_result['articles_extracted']
            monthly_results['total_processing_time'] += day_result['processing_time']
            
            if day_result['success']:
                monthly_results['successful_days'] += 1
            else:
                monthly_results['failed_days'] += 1
            
            # Délai entre les jours pour éviter la surcharge
            if i < len(business_days):  # Pas de délai après le dernier jour
                logger.info(f"⏳ Pause de {delay_between_days}s avant le jour suivant...")
                time.sleep(delay_between_days)
        
        # Finalisation
        monthly_results['end_time'] = datetime.now().isoformat()
        monthly_results['total_processing_time'] = round(time.time() - start_time, 2)
        
        # Génération du résumé mensuel
        monthly_results['summary'] = self._generate_monthly_summary(monthly_results)
        
        # Sauvegarde du résultat mensuel
        monthly_json = f"tldr_{self.config.get('newsletter_type', 'tech')}_monthly_{year}_{month:02d}.json"
        monthly_path = Path(self.config.get('json_output_dir', './json_results')) / monthly_json
        
        with open(monthly_path, 'w', encoding='utf-8') as f:
            json.dump(monthly_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"🎉 Traitement mensuel terminé: {monthly_path}")
        
        return monthly_results
    
    def _generate_monthly_summary(self, monthly_results: Dict[str, Any]) -> str:
        """Génère un résumé du mois traité"""
        total_days = monthly_results['total_business_days']
        successful = monthly_results['successful_days']
        failed = monthly_results['failed_days']
        total_articles = monthly_results['total_articles']
        total_time = monthly_results['total_processing_time']
        
        summary = f"""📊 RÉSUMÉ MENSUEL TLDR {monthly_results['month']}

✅ Jours traités avec succès: {successful}/{total_days}
❌ Jours échoués: {failed}/{total_days}
📰 Total articles extraits: {total_articles}
⏱️ Temps total de traitement: {total_time:.1f}s
📈 Moyenne articles/jour: {total_articles/total_days:.1f}

Taux de réussite: {(successful/total_days)*100:.1f}%"""

        if failed > 0:
            failed_dates = [
                result['date_formatted'] 
                for result in monthly_results['daily_results'] 
                if not result['success']
            ]
            summary += f"\n\n❌ Jours échoués: {', '.join(failed_dates)}"
        
        return summary


def main():
    """Fonction principale avec configuration"""
    
    # Configuration par défaut
    config = {
        'newsletter_type': 'tech',  # tech, ai, crypto, marketing, design, webdev
        'max_articles': 15,
        'country_code': 'US',
        
        # Notion (optionnel - commentez si pas utilisé)
        # 'notion_token': 'YOUR_NOTION_TOKEN',
        # 'notion_database_id': 'YOUR_DATABASE_ID',
        
        # Ollama
        'ollama_model': 'nous-hermes2:latest',
        'ollama_base_url': 'http://localhost:11434',
        'max_articles_per_batch': 12,
        
        # Dossiers de sortie
        'audio_output_dir': './audio_summaries',
        'json_output_dir': './json_results',
        'logs_dir': './logs'
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
    
    # Vérification d'Ollama
    try:
        import ollama
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
    automation = MonthlyTLDRAutomation(config)
    
    try:
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
            print(f"\n🎵 {len(successful_days)} fichiers audio générés dans:")
            print(f"   📁 {config['audio_output_dir']}")
            
            print(f"\n📊 {len(successful_days)} fichiers JSON générés dans:")
            print(f"   📁 {config['json_output_dir']}")
        
        if monthly_results['failed_days'] > 0:
            print(f"\n❌ {monthly_results['failed_days']} jours ont échoué - voir les logs pour plus de détails")
    
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")


if __name__ == "__main__":
    print("🤖 TLDR Monthly Automation")
    print("Usage: python monthly_automation.py [YEAR] [MONTH] [NEWSLETTER_TYPE]")
    print("Exemple: python monthly_automation.py 2025 6 tech")
    print("Types disponibles: tech, ai, crypto, marketing, design, webdev")
    print("-" * 60)
    
    main()