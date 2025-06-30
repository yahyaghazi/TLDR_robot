#!/usr/bin/env python3
"""
Automatisation TLDR modifiée pour stockage exclusif dans SQLite
Version migrée automatiquement - Plus de problèmes Notion !
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
from core.aiprocessor import AIProcessor
from core.ttsgenerator import TTSGenerator
from utils.smartdatehandler import SmartDateHandler

# Import du nouveau SQLiteIntegrator
from pathlib import Path
import sqlite3
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monthly_automation_sqlite.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SQLiteIntegrator:
    """Intégration SQLite - Simple et fiable"""
    
    def __init__(self, db_path: str = "data/tldr_database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"✅ SQLite Database initialisée: {self.db_path}")
    
    def _init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table principale pour les articles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titre TEXT NOT NULL,
                    url TEXT,
                    resume_tldr TEXT,
                    etat TEXT DEFAULT 'Nouveau',
                    categories_ia TEXT,
                    duree_lecture TEXT,
                    date_extraction TEXT,
                    source TEXT,
                    newsletter_type TEXT,
                    contenu_brut TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table pour les synthèses quotidiennes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS syntheses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_synthese TEXT NOT NULL,
                    newsletter_type TEXT NOT NULL,
                    contenu TEXT NOT NULL,
                    nb_articles INTEGER DEFAULT 0,
                    temps_traitement REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table pour les rapports quotidiens
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rapports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_rapport TEXT NOT NULL,
                    newsletter_type TEXT NOT NULL,
                    articles_extraits INTEGER DEFAULT 0,
                    articles_stockes INTEGER DEFAULT 0,
                    succes BOOLEAN DEFAULT 0,
                    erreurs TEXT,
                    temps_traitement REAL DEFAULT 0,
                    fichier_audio TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    def test_connection(self) -> bool:
        """Test la connexion à la base SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM articles")
                count = cursor.fetchone()[0]
                logger.info(f"✅ Base SQLite connectée ! ({count} articles)")
                return True
        except Exception as e:
            logger.error(f"❌ Erreur connexion SQLite: {e}")
            return False
    
    def bulk_add_articles(self, articles: List[Dict[str, Any]]) -> List[int]:
        """Ajoute plusieurs articles en lot"""
        article_ids = []
        
        if not articles:
            return article_ids
        
        logger.info(f"📦 Ajout en lot de {len(articles)} articles à SQLite...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for article in articles:
                    categories_json = json.dumps(article.get('categories_ia', []))
                    
                    cursor.execute('''
                        INSERT INTO articles (
                            titre, url, resume_tldr, etat, categories_ia,
                            duree_lecture, date_extraction, source, newsletter_type, contenu_brut
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        article.get('titre', ''),
                        article.get('url', ''),
                        article.get('resume_tldr', ''),
                        article.get('etat', 'Nouveau'),
                        categories_json,
                        article.get('duree_lecture', ''),
                        article.get('date_extraction', datetime.now().strftime('%Y-%m-%d')),
                        article.get('source', ''),
                        article.get('newsletter_type', ''),
                        article.get('contenu_brut', '')
                    ))
                    
                    article_ids.append(cursor.lastrowid)
                
                conn.commit()
                logger.info(f"✅ {len(article_ids)} articles sauvegardés dans SQLite")
                return article_ids
                
        except Exception as e:
            logger.error(f"❌ Erreur ajout en lot: {e}")
            return []
    
    def save_complete_daily_results(self, daily_results: Dict[str, Any]) -> Dict[str, Any]:
        """Sauvegarde complète des résultats quotidiens dans SQLite"""
        
        saved_ids = {
            'articles': [],
            'synthesis_id': None,
            'report_id': None
        }
        
        try:
            # 1. Ajouter tous les articles individuels
            if daily_results.get('articles'):
                logger.info("💾 Sauvegarde des articles individuels...")
                article_ids = self.bulk_add_articles(daily_results['articles'])
                saved_ids['articles'] = article_ids
                daily_results['articles_stored'] = len(article_ids)
            
            # 2. Ajouter la synthèse
            if daily_results.get('synthesis'):
                logger.info("💾 Sauvegarde de la synthèse...")
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO syntheses (date_synthese, newsletter_type, contenu, nb_articles, temps_traitement)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        daily_results.get('date_formatted', ''),
                        daily_results.get('newsletter_type', 'tech'),
                        daily_results.get('synthesis', ''),
                        daily_results.get('articles_extracted', 0),
                        daily_results.get('processing_time', 0)
                    ))
                    saved_ids['synthesis_id'] = cursor.lastrowid
                    conn.commit()
                logger.info("✅ Synthèse sauvegardée dans SQLite")
            
            # 3. Ajouter le rapport quotidien
            logger.info("💾 Sauvegarde du rapport quotidien...")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                erreurs_json = json.dumps(daily_results.get('errors', []))
                
                cursor.execute('''
                    INSERT INTO rapports (
                        date_rapport, newsletter_type, articles_extraits, articles_stockes,
                        succes, erreurs, temps_traitement, fichier_audio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    daily_results.get('date_formatted', ''),
                    daily_results.get('newsletter_type', 'tech'),
                    daily_results.get('articles_extracted', 0),
                    daily_results.get('articles_stored', 0),
                    daily_results.get('success', False),
                    erreurs_json,
                    daily_results.get('processing_time', 0),
                    daily_results.get('audio_file', '')
                ))
                saved_ids['report_id'] = cursor.lastrowid
                conn.commit()
            logger.info("✅ Rapport sauvegardé dans SQLite")
            
            # Résumé final
            total_elements = len(saved_ids['articles']) + (1 if saved_ids['synthesis_id'] else 0) + (1 if saved_ids['report_id'] else 0)
            logger.info(f"✅ Sauvegarde SQLite terminée: {total_elements} éléments créés")
            
            return saved_ids
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde complète: {e}")
            return saved_ids


class MonthlyTLDRAutomationSQLite:
    """Automatisation mensuelle avec stockage exclusif dans SQLite"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialisation des composants
        self.scraper = TLDRScraper(
            newsletter_type=config.get('newsletter_type', 'tech'),
            max_articles=config.get('max_articles', 15),
            country_code=config.get('country_code', 'US')
        )
        
        # SQLite OBLIGATOIRE pour cette version
        self.sqlite = SQLiteIntegrator(
            config.get('sqlite_db_path', 'data/tldr_database.db')
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
        
        # Test de connexion SQLite au démarrage
        if not self.sqlite.test_connection():
            raise ConnectionError("❌ Impossible de se connecter à SQLite!")
        
        logger.info("✅ SQLiteIntegrator connecté et opérationnel")
    
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
        """Traite une journée spécifique et stocke tout dans SQLite"""
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
            'sqlite_ids': {},  # IDs des éléments créés dans SQLite
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
            
            # 4. STOCKAGE COMPLET DANS SQLITE (remplace SQLite)
            logger.info("💾 Sauvegarde complète dans SQLite...")
            
            try:
                saved_ids = self.sqlite.save_complete_daily_results(results)
                results['sqlite_ids'] = saved_ids
                results['articles_stored'] = len(saved_ids.get('articles', []))
                
                logger.info(f"✅ Données sauvegardées dans SQLite:")
                for element_type, element_ids in saved_ids.items():
                    if isinstance(element_ids, list):
                        logger.info(f"   📝 {element_type}: {len(element_ids)} éléments")
                    else:
                        logger.info(f"   📝 {element_type}: {'✅' if element_ids else '❌'}")
                
                results['success'] = True
                
            except Exception as e:
                logger.error(f"❌ Erreur sauvegarde SQLite: {e}")
                results['errors'].append(f"Erreur SQLite: {str(e)}")
            
            if results['success']:
                logger.info(f"✅ Journée {date_str} traitée et stockée avec succès dans SQLite")
            
        except Exception as e:
            logger.error(f"❌ Erreur critique pour {target_date}: {e}")
            results['errors'].append(f"Erreur critique: {str(e)}")
        
        finally:
            results['processing_time'] = round(time.time() - start_time, 2)
        
        return results
    
    def process_month(self, year: int, month: int, delay_between_days: float = 2.0) -> Dict[str, Any]:
        """Traite un mois complet et stocke tout dans SQLite"""
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
            'all_sqlite_ids': [],  # Tous les IDs SQLite créés
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
                # Collecter tous les IDs SQLite
                if day_result.get('sqlite_ids'):
                    for key, value in day_result['sqlite_ids'].items():
                        if isinstance(value, list):
                            monthly_results['all_sqlite_ids'].extend(value)
                        elif value:
                            monthly_results['all_sqlite_ids'].append(value)
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
        
        # OPTIONNEL: Créer un résumé mensuel dans SQLite
        try:
            with sqlite3.connect(self.sqlite.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO rapports (
                        date_rapport, newsletter_type, articles_extraits, articles_stockes,
                        succes, erreurs, temps_traitement, fichier_audio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"{year}-{month:02d}-01",
                    monthly_results['newsletter_type'],
                    monthly_results['total_articles'],
                    monthly_results['total_articles_stored'],
                    monthly_results['successful_days'] > 0,
                    json.dumps([f"Échecs: {monthly_results['failed_days']}/{monthly_results['total_business_days']}"]),
                    monthly_results['total_processing_time'],
                    f"RÉSUMÉ MENSUEL {monthly_results['month']}"
                ))
                monthly_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"📊 Résumé mensuel créé dans SQLite (ID: {monthly_id})")
                monthly_results['monthly_sqlite_id'] = monthly_id
                
        except Exception as e:
            logger.error(f"❌ Erreur création résumé mensuel: {e}")
        
        logger.info(f"🎉 Traitement mensuel terminé - Tout stocké dans SQLite!")
        
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
💾 Total articles stockés dans SQLite: {total_stored}
⏱️ Temps total de traitement: {total_time:.1f}s
📈 Moyenne articles/jour: {total_articles/max(total_days, 1):.1f}
🎵 Fichiers audio générés: {successful}

Taux de réussite: {(successful/max(total_days, 1))*100:.1f}%

💾 STOCKAGE: Toutes les données sont maintenant dans votre base SQLite!
📝 Types d'éléments créés: Articles individuels, Synthèses quotidiennes, Rapports quotidiens
🗂️ Total éléments SQLite: {len(monthly_results.get('all_sqlite_ids', []))}
📁 Base de données: {self.sqlite.db_path}"""

        if failed > 0:
            failed_dates = [
                result['date_formatted'] 
                for result in monthly_results['daily_results'] 
                if not result['success']
            ]
            summary += f"\n\n❌ Jours échoués: {', '.join(failed_dates)}"
        
        return summary


def main():
    """Fonction principale avec stockage SQLite exclusif"""
    
    # Configuration - SQLITE OBLIGATOIRE pour cette version
        # Configuration - SQLITE OBLIGATOIRE pour cette version
    config = {
        'newsletter_type': 'tech',
        'max_articles': 15,
        'country_code': 'US',
        
        # SQLITE (remplace Notion)
        'sqlite_db_path': 'data/tldr_database.db',
        
        # Ollama
        'ollama_model': 'nous-hermes2:latest',
        'ollama_base_url': 'http://localhost:11434',
        'max_articles_per_batch': 12,
        
        # Dossiers de sortie
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
    logger.info(f"💾 Mode: Stockage exclusif dans SQLite")
    
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
        automation = MonthlyTLDRAutomationSQLite(config)
        
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
            
            print(f"\n💾 {len(monthly_results.get('all_sqlite_ids', []))} éléments créés dans SQLite:")
            print(f"   🗂️ Articles individuels, synthèses et rapports")
            print(f"   📁 Base de données: {automation.sqlite.db_path}")
        
        if monthly_results['failed_days'] > 0:
            print(f"\n❌ {monthly_results['failed_days']} jours ont échoué - voir les logs pour plus de détails")
        
        # Affichage des informations de la base SQLite
        print(f"\n🔗 ACCÈS À VOS DONNÉES:")
        print(f"   📊 Base SQLite: {automation.sqlite.db_path}")
        print(f"   🎵 Audio local: {audio_dir}")
        print(f"   📋 Consultez la base avec un outil SQLite ou exportez en JSON")
    
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("TLDR Monthly Automation - Version SQLite")
    print("Usage: python monthly_automation_sqlite.py [YEAR] [MONTH] [NEWSLETTER_TYPE]")
    print("Exemple: python monthly_automation_sqlite.py 2025 6 tech")
    print("Types disponibles: tech, ai, crypto, marketing, design, webdev")
    print("Mode: Stockage exclusif dans SQLite (plus de SQLite)")
    print("-" * 60)
    
    main()