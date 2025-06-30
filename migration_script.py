#!/usr/bin/env python3
"""
Script de migration rapide - Remplacement de Notion par SQLite dans TLDR_robot
Modifie votre automation existante pour utiliser SQLite
"""

import shutil
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_existing_files():
    """Crée une sauvegarde des fichiers existants"""
    logger.info("💾 Création de la sauvegarde...")
    
    backup_dir = Path("backup_notion_version")
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "automation/monthly_automation.py",
        "core/notionintegrator.py"
    ]
    
    for file_path in files_to_backup:
        source = Path(file_path)
        if source.exists():
            dest = backup_dir / source.name
            shutil.copy2(source, dest)
            logger.info(f"   ✅ Sauvegardé: {file_path}")
    
    logger.info(f"📁 Sauvegarde créée dans: {backup_dir}")
    return backup_dir

def create_sqlite_integrator():
    """Crée le nouveau SQLiteIntegrator"""
    
    sqlite_code = '''import sqlite3
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import time

# Configuration du logging
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
            cursor.execute(\'\'\'
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    titre TEXT NOT NULL,
                    url TEXT,
                    resume_tldr TEXT,
                    etat TEXT DEFAULT \'Nouveau\',
                    categories_ia TEXT,
                    duree_lecture TEXT,
                    date_extraction TEXT,
                    source TEXT,
                    newsletter_type TEXT,
                    contenu_brut TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            \'\'\')
            
            # Table pour les synthèses quotidiennes
            cursor.execute(\'\'\'
                CREATE TABLE IF NOT EXISTS syntheses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date_synthese TEXT NOT NULL,
                    newsletter_type TEXT NOT NULL,
                    contenu TEXT NOT NULL,
                    nb_articles INTEGER DEFAULT 0,
                    temps_traitement REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            \'\'\')
            
            # Table pour les rapports quotidiens
            cursor.execute(\'\'\'
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
            \'\'\')
            
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
                    categories_json = json.dumps(article.get(\'categories_ia\', []))
                    
                    cursor.execute(\'\'\'
                        INSERT INTO articles (
                            titre, url, resume_tldr, etat, categories_ia,
                            duree_lecture, date_extraction, source, newsletter_type, contenu_brut
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    \'\'\', (
                        article.get(\'titre\', \'\'),
                        article.get(\'url\', \'\'),
                        article.get(\'resume_tldr\', \'\'),
                        article.get(\'etat\', \'Nouveau\'),
                        categories_json,
                        article.get(\'duree_lecture\', \'\'),
                        article.get(\'date_extraction\', datetime.now().strftime(\'%Y-%m-%d\')),
                        article.get(\'source\', \'\'),
                        article.get(\'newsletter_type\', \'\'),
                        article.get(\'contenu_brut\', \'\')
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
            \'articles\': [],
            \'synthesis_id\': None,
            \'report_id\': None
        }
        
        try:
            # 1. Ajouter tous les articles individuels
            if daily_results.get(\'articles\'):
                logger.info("💾 Sauvegarde des articles individuels...")
                article_ids = self.bulk_add_articles(daily_results[\'articles\'])
                saved_ids[\'articles\'] = article_ids
                daily_results[\'articles_stored\'] = len(article_ids)
            
            # 2. Ajouter la synthèse
            if daily_results.get(\'synthesis\'):
                logger.info("💾 Sauvegarde de la synthèse...")
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(\'\'\'
                        INSERT INTO syntheses (date_synthese, newsletter_type, contenu, nb_articles, temps_traitement)
                        VALUES (?, ?, ?, ?, ?)
                    \'\'\', (
                        daily_results.get(\'date_formatted\', \'\'),
                        daily_results.get(\'newsletter_type\', \'tech\'),
                        daily_results.get(\'synthesis\', \'\'),
                        daily_results.get(\'articles_extracted\', 0),
                        daily_results.get(\'processing_time\', 0)
                    ))
                    saved_ids[\'synthesis_id\'] = cursor.lastrowid
                    conn.commit()
                logger.info("✅ Synthèse sauvegardée dans SQLite")
            
            # 3. Ajouter le rapport quotidien
            logger.info("💾 Sauvegarde du rapport quotidien...")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                erreurs_json = json.dumps(daily_results.get(\'errors\', []))
                
                cursor.execute(\'\'\'
                    INSERT INTO rapports (
                        date_rapport, newsletter_type, articles_extraits, articles_stockes,
                        succes, erreurs, temps_traitement, fichier_audio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                \'\'\', (
                    daily_results.get(\'date_formatted\', \'\'),
                    daily_results.get(\'newsletter_type\', \'tech\'),
                    daily_results.get(\'articles_extracted\', 0),
                    daily_results.get(\'articles_stored\', 0),
                    daily_results.get(\'success\', False),
                    erreurs_json,
                    daily_results.get(\'processing_time\', 0),
                    daily_results.get(\'audio_file\', \'\')
                ))
                saved_ids[\'report_id\'] = cursor.lastrowid
                conn.commit()
            logger.info("✅ Rapport sauvegardé dans SQLite")
            
            # Résumé final
            total_elements = len(saved_ids[\'articles\']) + (1 if saved_ids[\'synthesis_id\'] else 0) + (1 if saved_ids[\'report_id\'] else 0)
            logger.info(f"✅ Sauvegarde SQLite terminée: {total_elements} éléments créés")
            
            return saved_ids
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde complète: {e}")
            return saved_ids
'''
    
    # Écrire le fichier
    sqlite_path = Path("core/sqliteintegrator.py")
    with open(sqlite_path, 'w', encoding='utf-8') as f:
        f.write(sqlite_code)
    
    logger.info(f"✅ SQLiteIntegrator créé: {sqlite_path}")
    return sqlite_path

def modify_monthly_automation():
    """Modifie le script d'automatisation mensuelle pour utiliser SQLite"""
    
    automation_path = Path("automation/monthly_automation.py")
    
    if not automation_path.exists():
        logger.error(f"❌ Fichier non trouvé: {automation_path}")
        return False
    
    # Lire le fichier existant
    with open(automation_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Modifications nécessaires
    modifications = [
        # Remplacer l'import Notion par SQLite
        ("from core.notionintegrator import NotionIntegrator", "from core.sqliteintegrator import SQLiteIntegrator"),
        
        # Remplacer la classe Enhanced par la classe simple
        ("class EnhancedNotionIntegrator:", "# ANCIEN CODE NOTION SUPPRIMÉ"),
        
        # Modifier la classe principale
        ("MonthlyTLDRAutomationNotion", "MonthlyTLDRAutomationSQLite"),
        
        # Remplacer Notion par SQLite dans le __init__
        ("self.notion = EnhancedNotionIntegrator(", "self.sqlite = SQLiteIntegrator("),
        ("config['notion_token']", "'data/tldr_database.db'"),
        ("config['notion_database_id']", "# SQLite ne nécessite pas de database_id"),
        
        # Remplacer les appels Notion par SQLite
        ("self.notion.test_connection()", "self.sqlite.test_connection()"),
        ("self.notion.save_complete_daily_results(", "self.sqlite.save_complete_daily_results("),
        
        # Modifier les messages de log
        ("Notion", "SQLite"),
        ("notion_ids", "sqlite_ids"),
        
        # Supprimer les références aux tokens Notion
        ("'notion_token': 'ntn_", "# Plus besoin de token Notion"),
        ("'notion_database_id': '21e", "# Plus besoin de database ID"),
    ]
    
    # Appliquer les modifications
    for old, new in modifications:
        content = content.replace(old, new)
    
    # Configuration spéciale pour SQLite
    sqlite_config = '''    # Configuration - SQLITE OBLIGATOIRE pour cette version
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
    }'''
    
    # Remplacer la section config
    import re
    config_pattern = r'config = \{[^}]+\}'
    content = re.sub(config_pattern, sqlite_config, content, flags=re.DOTALL)
    
    # Ajouter un commentaire en haut
    header = '''#!/usr/bin/env python3
"""
Automatisation TLDR modifiée pour stockage exclusif dans SQLite
Version migrée automatiquement - Plus de problèmes Notion !
"""

'''
    
    # Remplacer le header existant
    if content.startswith('#!/usr/bin/env python3'):
        lines = content.split('\n')
        # Garder seulement à partir de la première ligne d'import
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                content = '\n'.join(lines[i:])
                break
    
    content = header + content
    
    # Écrire le fichier modifié
    with open(automation_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"✅ Automatisation modifiée: {automation_path}")
    return True

def create_quick_test():
    """Crée un script de test rapide"""
    
    test_code = '''#!/usr/bin/env python3
"""
Test rapide du nouveau système SQLite
"""

from core.sqliteintegrator import SQLiteIntegrator
from pathlib import Path

def test_sqlite():
    print("🧪 Test du nouveau système SQLite...")
    
    # Test de connexion
    sqlite = SQLiteIntegrator("data/tldr_database.db")
    
    if sqlite.test_connection():
        print("✅ SQLite fonctionne parfaitement !")
        
        # Test d'ajout d'un article
        test_article = {
            'titre': 'Test Migration SQLite',
            'url': 'https://example.com/test',
            'resume_tldr': 'Article de test après migration vers SQLite',
            'etat': 'Test',
            'categories_ia': ['Test', 'Migration', 'SQLite'],
            'newsletter_type': 'tech',
            'source': 'Migration-Test'
        }
        
        article_ids = sqlite.bulk_add_articles([test_article])
        
        if article_ids:
            print(f"✅ Article de test ajouté (ID: {article_ids[0]})")
            print("🎉 Migration réussie ! Votre système utilise maintenant SQLite.")
        else:
            print("❌ Problème avec l'ajout d'article")
    else:
        print("❌ Problème de connexion SQLite")

if __name__ == "__main__":
    test_sqlite()
'''
    
    test_path = Path("test_sqlite_migration.py")
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_code)
    
    logger.info(f"✅ Script de test créé: {test_path}")
    return test_path

def main():
    """Migration complète vers SQLite"""
    
    print("🚀 MIGRATION TLDR_robot: NOTION → SQLITE")
    print("=" * 60)
    print("Cette migration va :")
    print("✅ Créer une sauvegarde de vos fichiers actuels")
    print("✅ Remplacer NotionIntegrator par SQLiteIntegrator")
    print("✅ Modifier votre automatisation pour utiliser SQLite")
    print("✅ Créer un script de test")
    print()
    
    confirm = input("❓ Continuer la migration? (o/N): ").strip().lower()
    
    if confirm not in ['o', 'oui', 'y', 'yes']:
        print("👋 Migration annulée")
        return
    
    try:
        # 1. Sauvegarde
        backup_dir = backup_existing_files()
        
        # 2. Créer SQLiteIntegrator
        sqlite_path = create_sqlite_integrator()
        
        # 3. Modifier l'automatisation
        if modify_monthly_automation():
            logger.info("✅ Automatisation modifiée")
        
        # 4. Créer le script de test
        test_path = create_quick_test()
        
        print("\n" + "=" * 60)
        print("🎉 MIGRATION TERMINÉE AVEC SUCCÈS !")
        print("=" * 60)
        print(f"💾 Sauvegarde: {backup_dir}")
        print(f"🗄️ SQLiteIntegrator: {sqlite_path}")
        print(f"🧪 Test: {test_path}")
        print()
        print("📋 PROCHAINES ÉTAPES:")
        print("1. Testez la migration:")
        print(f"   python {test_path}")
        print()
        print("2. Lancez votre automatisation comme d'habitude:")
        print("   python automation/run_monthly.py")
        print()
        print("3. Consultez vos données SQLite:")
        print("   python sqlite_viewer.py")
        print()
        print("🎯 AVANTAGES DE SQLITE:")
        print("   ✅ Plus de problèmes de connexion")
        print("   ✅ Données stockées localement")
        print("   ✅ Pas de limites API")
        print("   ✅ Performances améliorées")
        print("   ✅ Recherche et export faciles")
        print()
        print("📁 Vos données seront dans: data/tldr_database.db")
        
    except Exception as e:
        logger.error(f"❌ Erreur durant la migration: {e}")
        print(f"\n💥 ÉCHEC DE LA MIGRATION: {e}")
        print(f"💾 Vos fichiers originaux sont sauvegardés dans: backup_notion_version/")
        print(f"🔧 Vous pouvez restaurer manuellement si nécessaire")

def rollback_migration():
    """Annule la migration et restaure les fichiers Notion"""
    
    print("🔄 RESTAURATION DE LA VERSION NOTION")
    print("=" * 50)
    
    backup_dir = Path("backup_notion_version")
    
    if not backup_dir.exists():
        print("❌ Aucune sauvegarde trouvée")
        return
    
    files_to_restore = [
        ("monthly_automation.py", "automation/monthly_automation.py"),
        ("notionintegrator.py", "core/notionintegrator.py")
    ]
    
    for backup_file, target_path in files_to_restore:
        backup_path = backup_dir / backup_file
        target = Path(target_path)
        
        if backup_path.exists():
            shutil.copy2(backup_path, target)
            logger.info(f"✅ Restauré: {target_path}")
    
    # Supprimer les fichiers SQLite
    sqlite_files = [
        "core/sqliteintegrator.py",
        "test_sqlite_migration.py",
        "sqlite_viewer.py"
    ]
    
    for file_path in sqlite_files:
        file_to_remove = Path(file_path)
        if file_to_remove.exists():
            file_to_remove.unlink()
            logger.info(f"🗑️ Supprimé: {file_path}")
    
    print("✅ Restauration terminée - Vous utilisez à nouveau Notion")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        main()
