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
        
        # Créer la base de données et les tables
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
                    categories_ia TEXT,  -- JSON array
                    duree_lecture TEXT,
                    date_extraction TEXT,
                    source TEXT,
                    newsletter_type TEXT,
                    contenu_brut TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    erreurs TEXT,  -- JSON array
                    temps_traitement REAL DEFAULT 0,
                    fichier_audio TEXT,
                    metadonnees TEXT,  -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Index pour les performances
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(date_extraction)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_articles_type ON articles(newsletter_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_syntheses_date ON syntheses(date_synthese)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rapports_date ON rapports(date_rapport)')
            
            conn.commit()
            logger.info("📋 Tables SQLite créées/vérifiées")
    
    def test_connection(self) -> bool:
        """Test la connexion à la base SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM articles")
                count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM syntheses")
                syntheses_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM rapports")
                rapports_count = cursor.fetchone()[0]
                
                logger.info(f"✅ Base SQLite connectée !")
                logger.info(f"📊 Statistiques:")
                logger.info(f"   • Articles: {count}")
                logger.info(f"   • Synthèses: {syntheses_count}")
                logger.info(f"   • Rapports: {rapports_count}")
                
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur connexion SQLite: {e}")
            return False
    
    def add_article_to_db(self, article: Dict[str, Any]) -> Optional[int]:
        """Ajoute un article à la base SQLite"""
        try:
            # Préparer les données
            categories_json = json.dumps(article.get('categories_ia', []))
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
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
                
                article_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"✅ Article ajouté (ID: {article_id}): {article.get('titre', 'Sans titre')[:50]}")
                return article_id
                
        except Exception as e:
            logger.error(f"❌ Erreur ajout article: {e}")
            return None
    
    def bulk_add_articles(self, articles: List[Dict[str, Any]]) -> List[int]:
        """Ajoute plusieurs articles en lot"""
        article_ids = []
        
        if not articles:
            logger.warning("📦 Aucun article à ajouter")
            return article_ids
        
        logger.info(f"📦 Ajout en lot de {len(articles)} articles à SQLite...")
        
        # Préparer toutes les données
        articles_data = []
        for article in articles:
            categories_json = json.dumps(article.get('categories_ia', []))
            articles_data.append((
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
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insertion en lot
                cursor.executemany('''
                    INSERT INTO articles (
                        titre, url, resume_tldr, etat, categories_ia,
                        duree_lecture, date_extraction, source, newsletter_type, contenu_brut
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', articles_data)
                
                # Récupérer les IDs générés
                first_id = cursor.lastrowid - len(articles) + 1
                article_ids = list(range(first_id, cursor.lastrowid + 1))
                
                conn.commit()
                
                logger.info(f"✅ {len(article_ids)} articles ajoutés avec succès à SQLite")
                return article_ids
                
        except Exception as e:
            logger.error(f"❌ Erreur ajout en lot: {e}")
            return []
    
    def add_synthesis_to_db(self, synthesis_data: Dict[str, Any]) -> Optional[int]:
        """Ajoute une synthèse quotidienne à la base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO syntheses (
                        date_synthese, newsletter_type, contenu, nb_articles, temps_traitement
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    synthesis_data.get('date_formatted', datetime.now().strftime('%Y-%m-%d')),
                    synthesis_data.get('newsletter_type', 'tech'),
                    synthesis_data.get('synthesis', ''),
                    synthesis_data.get('articles_extracted', 0),
                    synthesis_data.get('processing_time', 0)
                ))
                
                synthesis_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"✅ Synthèse ajoutée (ID: {synthesis_id})")
                return synthesis_id
                
        except Exception as e:
            logger.error(f"❌ Erreur ajout synthèse: {e}")
            return None
    
    def add_daily_report_to_db(self, daily_results: Dict[str, Any]) -> Optional[int]:
        """Ajoute un rapport quotidien à la base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                erreurs_json = json.dumps(daily_results.get('errors', []))
                metadonnees_json = json.dumps({
                    'day_name': daily_results.get('day_name', ''),
                    'audio_file': daily_results.get('audio_file', ''),
                    'synthesis_preview': daily_results.get('synthesis', '')[:200]
                })
                
                cursor.execute('''
                    INSERT INTO rapports (
                        date_rapport, newsletter_type, articles_extraits, articles_stockes,
                        succes, erreurs, temps_traitement, fichier_audio, metadonnees
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    daily_results.get('date_formatted', datetime.now().strftime('%Y-%m-%d')),
                    daily_results.get('newsletter_type', 'tech'),
                    daily_results.get('articles_extracted', 0),
                    daily_results.get('articles_stored', 0),
                    daily_results.get('success', False),
                    erreurs_json,
                    daily_results.get('processing_time', 0),
                    daily_results.get('audio_file', ''),
                    metadonnees_json
                ))
                
                report_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"✅ Rapport ajouté (ID: {report_id})")
                return report_id
                
        except Exception as e:
            logger.error(f"❌ Erreur ajout rapport: {e}")
            return None
    
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
                
                # Mettre à jour le nombre d'articles stockés
                daily_results['articles_stored'] = len(article_ids)
                logger.info(f"✅ {len(article_ids)} articles sauvegardés dans SQLite")
            
            # 2. Ajouter la synthèse
            if daily_results.get('synthesis'):
                logger.info("💾 Sauvegarde de la synthèse...")
                synthesis_id = self.add_synthesis_to_db(daily_results)
                if synthesis_id:
                    saved_ids['synthesis_id'] = synthesis_id
                    logger.info("✅ Synthèse sauvegardée dans SQLite")
            
            # 3. Ajouter le rapport quotidien
            logger.info("💾 Sauvegarde du rapport quotidien...")
            report_id = self.add_daily_report_to_db(daily_results)
            if report_id:
                saved_ids['report_id'] = report_id
                logger.info("✅ Rapport sauvegardé dans SQLite")
            
            # Résumé final
            total_elements = len(saved_ids['articles']) + (1 if saved_ids['synthesis_id'] else 0) + (1 if saved_ids['report_id'] else 0)
            logger.info(f"✅ Sauvegarde SQLite terminée: {total_elements} éléments créés")
            
            return saved_ids
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde complète: {e}")
            return saved_ids
    
    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques de la base"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Statistiques générales
                cursor.execute("SELECT COUNT(*) FROM articles")
                total_articles = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM syntheses")
                total_syntheses = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM rapports")
                total_rapports = cursor.fetchone()[0]
                
                # Articles par newsletter
                cursor.execute('''
                    SELECT newsletter_type, COUNT(*) 
                    FROM articles 
                    GROUP BY newsletter_type
                ''')
                articles_by_type = dict(cursor.fetchall())
                
                # Articles par date (derniers 7 jours)
                cursor.execute('''
                    SELECT date_extraction, COUNT(*) 
                    FROM articles 
                    WHERE date_extraction >= date('now', '-7 days')
                    GROUP BY date_extraction 
                    ORDER BY date_extraction DESC
                ''')
                recent_articles = dict(cursor.fetchall())
                
                # Dernières synthèses
                cursor.execute('''
                    SELECT date_synthese, newsletter_type, nb_articles 
                    FROM syntheses 
                    ORDER BY created_at DESC 
                    LIMIT 5
                ''')
                recent_syntheses = cursor.fetchall()
                
                return {
                    'total_articles': total_articles,
                    'total_syntheses': total_syntheses,
                    'total_rapports': total_rapports,
                    'articles_by_type': articles_by_type,
                    'recent_articles': recent_articles,
                    'recent_syntheses': recent_syntheses,
                    'db_path': str(self.db_path),
                    'db_size_mb': self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération statistiques: {e}")
            return {}
    
    def export_to_json(self, output_file: str = None) -> str:
        """Exporte toute la base en JSON"""
        if not output_file:
            output_file = f"tldr_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Pour avoir des dictionnaires
                cursor = conn.cursor()
                
                # Récupérer toutes les données
                cursor.execute("SELECT * FROM articles ORDER BY created_at")
                articles = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute("SELECT * FROM syntheses ORDER BY created_at")
                syntheses = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute("SELECT * FROM rapports ORDER BY created_at")
                rapports = [dict(row) for row in cursor.fetchall()]
                
                # Préparer l'export
                export_data = {
                    'export_date': datetime.now().isoformat(),
                    'statistics': self.get_statistics(),
                    'articles': articles,
                    'syntheses': syntheses,
                    'rapports': rapports
                }
                
                # Sauvegarder
                export_path = Path(output_file)
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ Export JSON créé: {export_path}")
                return str(export_path)
                
        except Exception as e:
            logger.error(f"❌ Erreur export JSON: {e}")
            return ""
    
    def search_articles(self, query: str, limit: int = 20) -> List[Dict]:
        """Recherche dans les articles"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM articles 
                    WHERE titre LIKE ? OR resume_tldr LIKE ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (f'%{query}%', f'%{query}%', limit))
                
                results = [dict(row) for row in cursor.fetchall()]
                
                # Parser les catégories JSON
                for result in results:
                    try:
                        result['categories_ia'] = json.loads(result['categories_ia'])
                    except:
                        result['categories_ia'] = []
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return []

# Fonction de remplacement pour l'automatisation
def create_sqlite_integrator(config: Dict[str, Any]) -> SQLiteIntegrator:
    """
    Crée un SQLiteIntegrator pour remplacer NotionIntegrator
    
    Args:
        config: Configuration (compatibilité avec l'ancien système)
    
    Returns:
        SQLiteIntegrator: Instance configurée
    """
    db_path = config.get('sqlite_db_path', 'data/tldr_database.db')
    return SQLiteIntegrator(db_path)

if __name__ == "__main__":
    logger.info("🚀 Test du SQLiteIntegrator")
    
    # Créer l'intégrator
    db = SQLiteIntegrator("test_tldr.db")

    if db.test_connection():
        logger.info("✅ Test de connexion réussi")

        test_articles = [
            {
                'titre': 'Test Article 1 SQLite',
                'url': 'https://example.com/1',
                'resume_tldr': 'Premier article de test pour SQLite',
                'etat': 'Test',
                'categories_ia': ['Test', 'SQLite'],
                'newsletter_type': 'tech',
                'source': 'Test-Manual'
            },
            {
                'titre': 'Test Article 2 SQLite',
                'url': 'https://example.com/2',
                'resume_tldr': 'Deuxième article de test pour SQLite',
                'etat': 'Test',
                'categories_ia': ['Test', 'Database'],
                'newsletter_type': 'tech',
                'source': 'Test-Manual'
            }
        ]

        article_ids = db.bulk_add_articles(test_articles)
        logger.info(f"Articles ajoutés: {article_ids}")

        synthesis_data = {
            'date_formatted': '2025-06-30',
            'newsletter_type': 'tech',
            'synthesis': 'Test de synthèse pour SQLite',
            'articles_extracted': 2,
            'processing_time': 1.5
        }
        synthesis_id = db.add_synthesis_to_db(synthesis_data)
        logger.info(f"Synthèse ajoutée: {synthesis_id}")

        daily_results = {
            'date_formatted': '2025-06-30',
            'newsletter_type': 'tech',
            'articles_extracted': 2,
            'articles_stored': 2,
            'success': True,
            'errors': [],
            'processing_time': 5.0,
            'audio_file': 'test.wav'
        }
        report_id = db.add_daily_report_to_db(daily_results)
        logger.info(f"Rapport ajouté: {report_id}")
        
        # Statistiques
        stats = db.get_statistics()
        logger.info(f"📊 Statistiques:")
        for key, value in stats.items():
            logger.info(f"   {key}: {value}")
        
        # Recherche
        results = db.search_articles("SQLite")
        logger.info(f"🔍 Résultats recherche 'SQLite': {len(results)} articles")
        
        # Export
        export_file = db.export_to_json("test_export.json")
        logger.info(f"📤 Export créé: {export_file}")
        
        logger.info("🎉 Tous les tests SQLite réussis!")
    else:
        logger.error("❌ Échec du test de connexion")
