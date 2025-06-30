#!/usr/bin/env python3
"""
SQLite Viewer et Export Tool pour TLDR_robot
Consultez et exportez vos données facilement
"""

import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TLDRSQLiteViewer:
    """Visualiseur et exporteur pour la base SQLite TLDR"""
    
    def __init__(self, db_path: str = "data/tldr_database.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"❌ Base de données non trouvée: {db_path}")
        
        logger.info(f"📊 Connexion à la base: {self.db_path}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques complètes de la base"""
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
                
                # Articles par newsletter type
                cursor.execute('''
                    SELECT newsletter_type, COUNT(*) 
                    FROM articles 
                    GROUP BY newsletter_type
                    ORDER BY COUNT(*) DESC
                ''')
                articles_by_type = dict(cursor.fetchall())
                
                # Articles par date (derniers 30 jours)
                cursor.execute('''
                    SELECT date_extraction, COUNT(*) 
                    FROM articles 
                    WHERE date_extraction >= date('now', '-30 days')
                    GROUP BY date_extraction 
                    ORDER BY date_extraction DESC
                ''')
                recent_articles = dict(cursor.fetchall())
                
                # Catégories les plus fréquentes
                cursor.execute("SELECT categories_ia FROM articles WHERE categories_ia IS NOT NULL")
                all_categories = []
                for row in cursor.fetchall():
                    try:
                        cats = json.loads(row[0])
                        all_categories.extend(cats)
                    except:
                        continue
                
                from collections import Counter
                top_categories = dict(Counter(all_categories).most_common(10))
                
                # Synthèses récentes
                cursor.execute('''
                    SELECT date_synthese, newsletter_type, nb_articles 
                    FROM syntheses 
                    ORDER BY created_at DESC 
                    LIMIT 10
                ''')
                recent_syntheses = cursor.fetchall()
                
                # Taille de la base
                db_size_mb = self.db_path.stat().st_size / (1024 * 1024)
                
                return {
                    'total_articles': total_articles,
                    'total_syntheses': total_syntheses,
                    'total_rapports': total_rapports,
                    'articles_by_type': articles_by_type,
                    'recent_articles': recent_articles,
                    'top_categories': top_categories,
                    'recent_syntheses': recent_syntheses,
                    'db_size_mb': round(db_size_mb, 2),
                    'db_path': str(self.db_path)
                }
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération statistiques: {e}")
            return {}
    
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
                
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    # Parser les catégories JSON
                    try:
                        result['categories_ia'] = json.loads(result['categories_ia']) if result['categories_ia'] else []
                    except:
                        result['categories_ia'] = []
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return []
    
    def get_articles_by_date(self, date_str: str) -> List[Dict]:
        """Récupère tous les articles d'une date donnée"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM articles 
                    WHERE date_extraction = ? 
                    ORDER BY created_at
                ''', (date_str,))
                
                results = []
                for row in cursor.fetchall():
                    result = dict(row)
                    try:
                        result['categories_ia'] = json.loads(result['categories_ia']) if result['categories_ia'] else []
                    except:
                        result['categories_ia'] = []
                    results.append(result)
                
                return results
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération articles par date: {e}")
            return []
    
    def get_synthesis_by_date(self, date_str: str) -> Dict:
        """Récupère la synthèse d'une date donnée"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM syntheses 
                    WHERE date_synthese = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (date_str,))
                
                row = cursor.fetchone()
                return dict(row) if row else {}
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération synthèse: {e}")
            return {}
    
    def export_to_json(self, output_file: str = None) -> str:
        """Exporte toute la base en JSON"""
        if not output_file:
            output_file = f"tldr_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Récupérer toutes les données
                cursor.execute("SELECT * FROM articles ORDER BY created_at")
                articles = []
                for row in cursor.fetchall():
                    article = dict(row)
                    try:
                        article['categories_ia'] = json.loads(article['categories_ia']) if article['categories_ia'] else []
                    except:
                        article['categories_ia'] = []
                    articles.append(article)
                
                cursor.execute("SELECT * FROM syntheses ORDER BY created_at")
                syntheses = [dict(row) for row in cursor.fetchall()]
                
                cursor.execute("SELECT * FROM rapports ORDER BY created_at")
                rapports = []
                for row in cursor.fetchall():
                    rapport = dict(row)
                    try:
                        rapport['erreurs'] = json.loads(rapport['erreurs']) if rapport['erreurs'] else []
                    except:
                        rapport['erreurs'] = []
                    rapports.append(rapport)
                
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
                logger.info(f"📊 Contenu: {len(articles)} articles, {len(syntheses)} synthèses, {len(rapports)} rapports")
                return str(export_path)
                
        except Exception as e:
            logger.error(f"❌ Erreur export JSON: {e}")
            return ""
    
    def export_articles_to_csv(self, output_file: str = None) -> str:
        """Exporte les articles en CSV"""
        if not output_file:
            output_file = f"tldr_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM articles ORDER BY created_at")
                
                export_path = Path(output_file)
                with open(export_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # En-têtes
                    writer.writerow([
                        'ID', 'Titre', 'URL', 'Résumé', 'État', 'Catégories', 
                        'Durée Lecture', 'Date Extraction', 'Source', 'Newsletter Type', 'Date Création'
                    ])
                    
                    # Données
                    for row in cursor.fetchall():
                        try:
                            categories = json.loads(row['categories_ia']) if row['categories_ia'] else []
                            categories_str = ', '.join(categories)
                        except:
                            categories_str = ''
                        
                        writer.writerow([
                            row['id'],
                            row['titre'],
                            row['url'],
                            row['resume_tldr'],
                            row['etat'],
                            categories_str,
                            row['duree_lecture'],
                            row['date_extraction'],
                            row['source'],
                            row['newsletter_type'],
                            row['created_at']
                        ])
                
                logger.info(f"✅ Export CSV créé: {export_path}")
                return str(export_path)
                
        except Exception as e:
            logger.error(f"❌ Erreur export CSV: {e}")
            return ""
    
    def display_statistics(self):
        """Affiche les statistiques de manière formatée"""
        stats = self.get_statistics()
        
        if not stats:
            print("❌ Impossible de récupérer les statistiques")
            return
        
        print("📊 STATISTIQUES DE LA BASE TLDR")
        print("=" * 60)
        print(f"📁 Base de données: {stats['db_path']}")
        print(f"💾 Taille: {stats['db_size_mb']} MB")
        print()
        
        print("📈 TOTAUX:")
        print(f"   📰 Articles: {stats['total_articles']}")
        print(f"   📊 Synthèses: {stats['total_syntheses']}")
        print(f"   📋 Rapports: {stats['total_rapports']}")
        print()
        
        if stats['articles_by_type']:
            print("📰 ARTICLES PAR TYPE:")
            for newsletter_type, count in stats['articles_by_type'].items():
                print(f"   {newsletter_type}: {count}")
            print()
        
        if stats['top_categories']:
            print("🏷️ TOP CATÉGORIES:")
            for category, count in list(stats['top_categories'].items())[:5]:
                print(f"   {category}: {count}")
            print()
        
        if stats['recent_articles']:
            print("📅 ARTICLES RÉCENTS (par date):")
            for date_str, count in list(stats['recent_articles'].items())[:7]:
                print(f"   {date_str}: {count} articles")
            print()
        
        if stats['recent_syntheses']:
            print("📊 SYNTHÈSES RÉCENTES:")
            for date_synthese, newsletter_type, nb_articles in stats['recent_syntheses'][:5]:
                print(f"   {date_synthese} ({newsletter_type}): {nb_articles} articles")
        
        print("=" * 60)
    
    def interactive_search(self):
        """Interface de recherche interactive"""
        print("\n🔍 RECHERCHE INTERACTIVE")
        print("Tapez votre requête (ou 'quit' pour quitter):")
        
        while True:
            try:
                query = input("\n🔍 Recherche> ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not query:
                    continue
                
                results = self.search_articles(query, limit=10)
                
                if results:
                    print(f"\n✅ {len(results)} résultat(s) trouvé(s):")
                    print("-" * 80)
                    
                    for i, article in enumerate(results, 1):
                        categories = ', '.join(article['categories_ia']) if article['categories_ia'] else 'Aucune'
                        print(f"{i}. {article['titre'][:60]}...")
                        print(f"   📅 {article['date_extraction']} | 🏷️ {categories}")
                        print(f"   🔗 {article['url'][:60]}...")
                        if article['resume_tldr']:
                            print(f"   📝 {article['resume_tldr'][:100]}...")
                        print()
                else:
                    print("❌ Aucun résultat trouvé")
                    
            except KeyboardInterrupt:
                break
        
        print("👋 Recherche terminée")
    
    def show_daily_summary(self, date_str: str):
        """Affiche le résumé d'une journée"""
        print(f"\n📅 RÉSUMÉ DU {date_str}")
        print("=" * 60)
        
        # Articles
        articles = self.get_articles_by_date(date_str)
        if articles:
            print(f"📰 {len(articles)} articles trouvés:")
            for i, article in enumerate(articles, 1):
                categories = ', '.join(article['categories_ia']) if article['categories_ia'] else 'Aucune'
                print(f"   {i}. {article['titre'][:50]}...")
                print(f"      🏷️ {categories} | 🔗 {article['url'][:40]}...")
            print()
        else:
            print("❌ Aucun article trouvé pour cette date")
        
        # Synthèse
        synthesis = self.get_synthesis_by_date(date_str)
        if synthesis:
            print("📊 SYNTHÈSE DU JOUR:")
            print(f"   📝 {synthesis['contenu'][:200]}...")
            print(f"   ⏱️ Temps de traitement: {synthesis.get('temps_traitement', 0)}s")
            print()
        else:
            print("❌ Aucune synthèse trouvée pour cette date")
        
        print("=" * 60)


def main():
    """Interface en ligne de commande"""
    import sys
    
    print("🚀 TLDR SQLite Viewer & Export Tool")
    print("=" * 50)
    
    # Chemin de la base
    db_path = "data/tldr_database.db"
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    
    try:
        viewer = TLDRSQLiteViewer(db_path)
        
        if len(sys.argv) == 1:
            # Mode interactif
            print("Mode interactif - Choisissez une option:")
            print("1. Afficher les statistiques")
            print("2. Recherche interactive")
            print("3. Exporter en JSON")
            print("4. Exporter articles en CSV")
            print("5. Résumé d'une journée")
            
            choice = input("\nVotre choix (1-5): ").strip()
            
            if choice == "1":
                viewer.display_statistics()
            
            elif choice == "2":
                viewer.interactive_search()
            
            elif choice == "3":
                output = input("Nom du fichier JSON (ou Entrée pour auto): ").strip()
                file_path = viewer.export_to_json(output if output else None)
                if file_path:
                    print(f"✅ Export créé: {file_path}")
            
            elif choice == "4":
                output = input("Nom du fichier CSV (ou Entrée pour auto): ").strip()
                file_path = viewer.export_articles_to_csv(output if output else None)
                if file_path:
                    print(f"✅ Export créé: {file_path}")
            
            elif choice == "5":
                date_str = input("Date (YYYY-MM-DD): ").strip()
                viewer.show_daily_summary(date_str)
            
            else:
                print("❌ Choix invalide")
        
        else:
            # Mode commande
            command = sys.argv[2] if len(sys.argv) > 2 else "stats"
            
            if command == "stats":
                viewer.display_statistics()
            
            elif command == "search":
                query = sys.argv[3] if len(sys.argv) > 3 else ""
                if query:
                    results = viewer.search_articles(query)
                    print(f"🔍 Résultats pour '{query}': {len(results)} articles")
                    for article in results[:5]:
                        print(f"• {article['titre']}")
                else:
                    print("❌ Requête manquante")
            
            elif command == "export-json":
                output = sys.argv[3] if len(sys.argv) > 3 else None
                file_path = viewer.export_to_json(output)
                if file_path:
                    print(f"✅ Export JSON: {file_path}")
            
            elif command == "export-csv":
                output = sys.argv[3] if len(sys.argv) > 3 else None
                file_path = viewer.export_articles_to_csv(output)
                if file_path:
                    print(f"✅ Export CSV: {file_path}")
            
            elif command == "day":
                date_str = sys.argv[3] if len(sys.argv) > 3 else datetime.now().strftime('%Y-%m-%d')
                viewer.show_daily_summary(date_str)
            
            else:
                print("❌ Commande inconnue")
                print("Commandes disponibles: stats, search, export-json, export-csv, day")
    
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("💡 Assurez-vous que l'automatisation a été exécutée au moins une fois")
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    print("Usage:")
    print("  python sqlite_viewer.py                           # Mode interactif")
    print("  python sqlite_viewer.py [db_path] stats           # Statistiques")
    print("  python sqlite_viewer.py [db_path] search [query]  # Recherche")
    print("  python sqlite_viewer.py [db_path] export-json     # Export JSON")
    print("  python sqlite_viewer.py [db_path] export-csv      # Export CSV")
    print("  python sqlite_viewer.py [db_path] day [date]      # Résumé journée")
    print()
    
    main()