import sqlite3
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLiteIntegrator:
    """Remplacement de Notion par SQLite - Plus simple et plus fiable"""
    
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
