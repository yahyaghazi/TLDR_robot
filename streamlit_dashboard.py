#!/usr/bin/env python3
"""
🚀 TLDR Dashboard avec TTS intégré - Interface Streamlit Complète
Visualisez, gérez et écoutez vos articles TLDR de manière interactive
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta, date
from pathlib import Path
import logging
from typing import Dict, List, Any
import time
import sys
import traceback
import pyttsx3
import tempfile
import os
import base64

# Configuration Streamlit
st.set_page_config(
    page_title="📰 TLDR Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ajouter les chemins du projet
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core"))

class TTSManager:
    """Gestionnaire TTS pour Streamlit avec support audio"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir()) / "tldr_tts"
        self.temp_dir.mkdir(exist_ok=True)
        
    def _init_tts_engine(self):
        """Initialise le moteur TTS avec gestion d'erreurs robuste"""
        try:
            # Vérifier si pyttsx3 est disponible
            import pyttsx3
            
            # Initialiser le moteur
            engine = pyttsx3.init()
            
            # Configuration de la voix
            voices = engine.getProperty('voices')
            
            if voices:
                # Recherche d'une voix française si disponible
                for voice in voices:
                    if voice and hasattr(voice, 'name') and hasattr(voice, 'id'):
                        if 'french' in voice.name.lower() or 'fr' in voice.id.lower():
                            engine.setProperty('voice', voice.id)
                            break
                        # Fallback pour voix anglaise de qualité
                        elif 'english' in voice.name.lower() and 'microsoft' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
            
            # Configuration optimisée pour Streamlit
            engine.setProperty('rate', 175)  # Vitesse légèrement réduite pour clarté
            engine.setProperty('volume', 0.8)  # Volume modéré
            
            return engine
            
        except ImportError:
            st.error("❌ Module pyttsx3 non installé. Installez avec: pip install pyttsx3")
            return None
        except Exception as e:
            st.error(f"❌ Erreur initialisation TTS: {e}")
            # Suggestion de solutions selon l'OS
            import platform
            os_name = platform.system()
            if os_name == "Linux":
                st.info("💡 Sur Linux, installez: sudo apt install espeak espeak-data")
            elif os_name == "Darwin":
                st.info("💡 Sur macOS, TTS devrait être disponible par défaut")
            elif os_name == "Windows":
                st.info("💡 Sur Windows, vérifiez que SAPI est disponible")
            return None
    
    def generate_audio_file(self, text: str, filename_prefix: str = "tts") -> str:
        """Génère un fichier audio temporaire"""
        try:
            engine = self._init_tts_engine()
            if not engine:
                return None
            
            # Nettoyer le texte
            clean_text = self._clean_text_for_tts(text)
            
            # Créer un nom de fichier unique
            timestamp = int(time.time())
            audio_filename = f"{filename_prefix}_{timestamp}.wav"
            audio_path = self.temp_dir / audio_filename
            
            # Générer l'audio
            engine.save_to_file(clean_text, str(audio_path))
            engine.runAndWait()
            engine.stop()
            
            if audio_path.exists():
                return str(audio_path)
            else:
                st.error("❌ Fichier audio non généré")
                return None
                
        except Exception as e:
            st.error(f"❌ Erreur génération audio: {e}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Nettoie le texte pour une meilleure lecture TTS"""
        # Remplacer les caractères spéciaux
        replacements = {
            '&': ' et ',
            '@': ' arobase ',
            '#': ' hashtag ',
            '$': ' dollar ',
            '%': ' pourcent ',
            '...': ' points de suspension ',
            'AI': 'Intelligence Artificielle',
            'API': 'A P I',
            'URL': 'U R L',
            'HTTP': 'H T T P',
            'iOS': 'i O S',
            'CEO': 'C E O',
            'CTO': 'C T O',
            'GPU': 'G P U',
            'CPU': 'C P U'
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Limiter la longueur pour éviter des fichiers trop longs
        if len(text) > 500:
            text = text[:500] + "... Fin du résumé."
        
        return text
    
    def get_audio_base64(self, audio_path: str) -> str:
        """Convertit un fichier audio en base64 pour Streamlit"""
        try:
            with open(audio_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                return audio_base64
        except Exception as e:
            st.error(f"❌ Erreur conversion audio: {e}")
            return None
    
    def cleanup_old_files(self, max_age_minutes: int = 30):
        """Nettoie les anciens fichiers audio temporaires"""
        try:
            current_time = time.time()
            for file_path in self.temp_dir.glob("*.wav"):
                if current_time - file_path.stat().st_mtime > (max_age_minutes * 60):
                    file_path.unlink()
        except Exception:
            pass  # Ignore les erreurs de nettoyage

def show_tts_controls(text: str, unique_key: str, title: str = ""):
    """Affiche les contrôles TTS pour un texte donné"""
    
    if 'tts_manager' not in st.session_state:
        st.session_state.tts_manager = TTSManager()
    
    tts_manager = st.session_state.tts_manager
    audio_path_key = f"audio_path_{unique_key}"
    
    # Interface utilisateur compacte
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        # Bouton de génération audio
        if st.button(f"🔊 Écouter", key=f"tts_btn_{unique_key}", help="Générer et lire l'audio"):
            with st.spinner("🎵 Génération audio..."):
                # Préparer le texte complet
                full_text = f"{title}. {text}" if title else text
                
                # Générer le fichier audio
                audio_path = tts_manager.generate_audio_file(full_text, f"article_{unique_key}")
                
                if audio_path:
                    # Stocker le chemin dans la session
                    st.session_state[audio_path_key] = audio_path
                    st.success("✅ Audio généré!")
                    # Force le rerun pour afficher le lecteur
                    st.rerun()
                else:
                    st.error("❌ Erreur génération audio")
    
    with col2:
        # Bouton de téléchargement (seulement si fichier existe)
        if audio_path_key in st.session_state and Path(st.session_state[audio_path_key]).exists():
            audio_path = st.session_state[audio_path_key]
            
            try:
                with open(audio_path, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                
                st.download_button(
                    label="💾 Télécharger",
                    data=audio_bytes,
                    file_name=f"tldr_audio_{unique_key}.wav",
                    mime="audio/wav",
                    key=f"download_btn_{unique_key}",
                    help="Télécharger le fichier audio"
                )
            except Exception as e:
                st.error(f"❌ Erreur téléchargement: {e}")
    
    with col3:
        # Lecteur audio intégré (seulement si fichier existe)
        if audio_path_key in st.session_state and Path(st.session_state[audio_path_key]).exists():
            audio_path = st.session_state[audio_path_key]
            
            try:
                # Utiliser le lecteur audio natif de Streamlit (sans paramètre key)
                with open(audio_path, 'rb') as audio_file:
                    audio_bytes = audio_file.read()
                
                st.audio(audio_bytes, format='audio/wav')
                
            except Exception as e:
                st.warning(f"⚠️ Lecteur audio indisponible: {e}")
                # Fallback: proposer seulement le téléchargement
                st.info("💡 Utilisez le bouton 'Télécharger' pour sauvegarder le fichier audio")
        else:
            # Afficher un message d'aide si pas encore d'audio généré
            if audio_path_key not in st.session_state:
                st.info("🎵 Cliquez sur 'Écouter' pour générer l'audio")

class TLDRDashboard:
    """Dashboard principal pour les données TLDR avec TTS intégré"""
    
    def __init__(self, db_path: str = "data/tldr_database.db"):
        self.db_path = Path(db_path)
        self._cache = {}
        self._cache_ttl = 60  # 1 minute de cache
    
    def connect_db(self):
        """Connexion à la base SQLite"""
        if not self.db_path.exists():
            # Créer le dossier data s'il n'existe pas
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            st.warning(f"⚠️ Base de données non trouvée. Création automatique...")
            
            # Initialiser une base vide
            self._init_empty_database()
        
        return sqlite3.connect(self.db_path)
    
    def _init_empty_database(self):
        """Initialise une base de données vide"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Table articles
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
                
                # Table syntheses
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
                
                # Table rapports
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
                st.success("✅ Base de données initialisée")
        except Exception as e:
            st.error(f"❌ Erreur initialisation BDD: {e}")

    def get_filtered_articles(self, limit=100, search="", newsletter_type=None, date_filter="Toutes les dates", date_start=None, date_end=None):
        """Récupère les articles avec filtres avancés"""
        conn = self.connect_db()
        if not conn:
            return pd.DataFrame()
        
        try:
            query = '''
                SELECT 
                    id, titre, url, resume_tldr, etat, categories_ia,
                    duree_lecture, date_extraction, source, newsletter_type, created_at
                FROM articles 
                WHERE 1=1
            '''
            params = []
            
            # Filtre par recherche textuelle
            if search:
                query += " AND (titre LIKE ? OR resume_tldr LIKE ?)"
                params.extend([f'%{search}%', f'%{search}%'])
            
            # Filtre par type de newsletter
            if newsletter_type:
                query += " AND newsletter_type = ?"
                params.append(newsletter_type)
            
            # Filtre par date
            if date_filter == "Aujourd'hui":
                query += " AND date_extraction = date('now')"
            elif date_filter == "7 derniers jours":
                query += " AND date_extraction >= date('now', '-7 days')"
            elif date_filter == "30 derniers jours":
                query += " AND date_extraction >= date('now', '-30 days')"
            elif date_filter == "Personnalisée" and date_start and date_end:
                query += " AND date_extraction BETWEEN ? AND ?"
                params.extend([date_start.strftime('%Y-%m-%d'), date_end.strftime('%Y-%m-%d')])
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            df = pd.read_sql_query(query, conn, params=params)
            
            # Parser les catégories JSON
            if not df.empty and 'categories_ia' in df.columns:
                df['categories_ia'] = df['categories_ia'].apply(
                    lambda x: json.loads(x) if x else []
                )
                df['categories_str'] = df['categories_ia'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else ''
                )
            
            return df
            
        except Exception as e:
            st.error(f"❌ Erreur récupération articles filtrés: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    # Et voici la fonction show_articles_explorer corrigée :

    def show_articles_explorer():
        """Explorateur d'articles avec TTS intégré et filtres avancés"""
        st.title("🔍 Explorateur d'Articles avec Audio")
        
        # Vérification TTS en haut de page
        tts_available = check_tts_availability()
        
        dashboard = get_dashboard()
        
        # Nettoyage automatique des fichiers audio anciens
        if 'tts_manager' in st.session_state:
            st.session_state.tts_manager.cleanup_old_files()
        
        # Section des filtres améliorée
        st.subheader("🎯 Filtres de recherche")
        
        # Première ligne de filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_query = st.text_input("🔍 Rechercher", placeholder="Titre ou contenu...")
        
        with col2:
            # Récupérer les types disponibles depuis la base
            conn = dashboard.connect_db()
            available_types = []
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT DISTINCT newsletter_type FROM articles WHERE newsletter_type IS NOT NULL ORDER BY newsletter_type")
                    available_types = [row[0] for row in cursor.fetchall()]
                    conn.close()
                except Exception:
                    conn.close()
            
            # Filtre par type
            if available_types:
                type_options = ["Tous les types"] + available_types
                selected_type = st.selectbox("📰 Type de newsletter", type_options)
            else:
                selected_type = "Tous les types"
                st.selectbox("📰 Type de newsletter", ["Aucun type disponible"], disabled=True)
        
        with col3:
            limit = st.selectbox("📊 Nombre d'articles", [20, 50, 100, 200], index=1)
        
        # Deuxième ligne de filtres
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtre par période
            date_filter = st.selectbox(
                "📅 Période",
                ["Toutes les dates", "Aujourd'hui", "7 derniers jours", "30 derniers jours", "Personnalisée"]
            )
        
        with col2:
            # Si période personnalisée, afficher les sélecteurs de date
            if date_filter == "Personnalisée":
                date_start = st.date_input("📅 Date début", value=date.today() - timedelta(days=30))
            else:
                date_start = None
        
        with col3:
            if date_filter == "Personnalisée":
                date_end = st.date_input("📅 Date fin", value=date.today())
            else:
                date_end = None
        
        # Récupération des articles avec filtres
        articles_df = dashboard.get_filtered_articles(
            limit=limit, 
            search=search_query,
            newsletter_type=selected_type if selected_type != "Tous les types" else None,
            date_filter=date_filter,
            date_start=date_start,
            date_end=date_end
        )
        
        if articles_df.empty:
            st.warning("⚠️ Aucun article trouvé avec ces critères")
            st.info("💡 Essayez de modifier vos filtres ou lancez un nouveau scraping")
            return
        
        # Affichage du nombre de résultats et bouton de reset
        col1, col2 = st.columns([3, 1])
        with col1:
            st.success(f"✅ {len(articles_df)} article(s) trouvé(s)")
        with col2:
            if st.button("🔄 Reset filtres", help="Réinitialiser tous les filtres"):
                st.rerun()
        
        # Affichage des articles avec TTS
        for idx, article in articles_df.iterrows():
            with st.expander(f"📰 {article['titre'][:80]}..." if len(article['titre']) > 80 else article['titre']):
                
                # Informations de l'article
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**📌 Titre:** {article['titre']}")
                    if article['resume_tldr']:
                        st.markdown(f"**📝 Résumé:** {article['resume_tldr']}")
                    if article['url']:
                        st.markdown(f"**🔗 URL:** [{article['url'][:50]}...]({article['url']})")
                
                with col2:
                    st.write(f"**📅 Date:** {article['date_extraction']}")
                    st.write(f"**📊 Type:** {article['newsletter_type']}")
                    if 'categories_str' in article and article['categories_str']:
                        st.write(f"**🏷️ Catégories:** {article['categories_str']}")
                    if 'duree_lecture' in article and article['duree_lecture']:
                        st.write(f"**⏱️ Lecture:** {article['duree_lecture']}")
                
                # Contrôles TTS (seulement si TTS disponible)
                if tts_available:
                    st.markdown("---")
                    st.markdown("**🎵 Contrôles Audio:**")
                    
                    # Préparer le texte pour TTS
                    resume_text = article['resume_tldr'] if article['resume_tldr'] else "Pas de résumé disponible"
                    
                    # Afficher les contrôles TTS
                    show_tts_controls(
                        text=resume_text,
                        unique_key=f"article_{article['id']}",
                        title=article['titre']
                    )
                else:
                    st.info("💡 Installez pyttsx3 pour activer les fonctionnalités audio")
        
        # Export avec informations sur les filtres appliqués
        if not articles_df.empty:
            st.subheader("📤 Export")
            
            # Informations sur les filtres appliqués
            filters_info = []
            if search_query:
                filters_info.append(f"Recherche: '{search_query}'")
            if selected_type != "Tous les types":
                filters_info.append(f"Type: {selected_type}")
            if date_filter != "Toutes les dates":
                filters_info.append(f"Période: {date_filter}")
            
            if filters_info:
                st.info(f"🎯 Filtres appliqués: {' | '.join(filters_info)}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv = articles_df.to_csv(index=False)
                filename_suffix = f"_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}" if filters_info else f"_{datetime.now().strftime('%Y%m%d')}"
                st.download_button(
                    label="💾 Télécharger CSV",
                    data=csv,
                    file_name=f"tldr_articles{filename_suffix}.csv",
                    mime="text/csv"
                )
            
            with col2:
                json_data = articles_df.to_json(orient='records', indent=2)
                st.download_button(
                    label="💾 Télécharger JSON",
                    data=json_data,
                    file_name=f"tldr_articles{filename_suffix}.json",
                    mime="application/json"
                )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques"""
        conn = self.connect_db()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM syntheses")
            total_syntheses = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM rapports")
            total_rapports = cursor.fetchone()[0]
            
            # Articles par type
            cursor.execute('''
                SELECT newsletter_type, COUNT(*) 
                FROM articles 
                GROUP BY newsletter_type
                ORDER BY COUNT(*) DESC
            ''')
            articles_by_type = dict(cursor.fetchall())
            
            # Articles récents (30 derniers jours)
            cursor.execute('''
                SELECT date_extraction, COUNT(*) 
                FROM articles 
                WHERE date_extraction >= date('now', '-30 days')
                GROUP BY date_extraction 
                ORDER BY date_extraction DESC
            ''')
            recent_articles = cursor.fetchall()
            
            # Taille de la base
            db_size_mb = round(self.db_path.stat().st_size / (1024 * 1024), 2) if self.db_path.exists() else 0
            
            return {
                'total_articles': total_articles,
                'total_syntheses': total_syntheses,
                'total_rapports': total_rapports,
                'articles_by_type': articles_by_type,
                'recent_articles': recent_articles,
                'db_size_mb': db_size_mb
            }
            
        except Exception as e:
            st.error(f"❌ Erreur récupération statistiques: {e}")
            return {}
        finally:
            conn.close()
    
    def get_articles(self, limit: int = 100, search: str = "") -> pd.DataFrame:
        """Récupère les articles"""
        conn = self.connect_db()
        if not conn:
            return pd.DataFrame()
        
        try:
            query = '''
                SELECT 
                    id, titre, url, resume_tldr, etat, categories_ia,
                    duree_lecture, date_extraction, source, newsletter_type, created_at
                FROM articles 
                WHERE 1=1
            '''
            params = []
            
            if search:
                query += " AND (titre LIKE ? OR resume_tldr LIKE ?)"
                params.extend([f'%{search}%', f'%{search}%'])
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            df = pd.read_sql_query(query, conn, params=params)
            
            # Parser les catégories JSON
            if not df.empty and 'categories_ia' in df.columns:
                df['categories_ia'] = df['categories_ia'].apply(
                    lambda x: json.loads(x) if x else []
                )
                df['categories_str'] = df['categories_ia'].apply(
                    lambda x: ', '.join(x) if isinstance(x, list) else ''
                )
            
            return df
            
        except Exception as e:
            st.error(f"❌ Erreur récupération articles: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    
    def get_syntheses(self) -> pd.DataFrame:
        """Récupère les synthèses"""
        conn = self.connect_db()
        if not conn:
            return pd.DataFrame()
        
        try:
            df = pd.read_sql_query('''
                SELECT * FROM syntheses 
                ORDER BY date_synthese DESC
            ''', conn)
            return df
        except Exception as e:
            st.error(f"❌ Erreur récupération synthèses: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

@st.cache_resource
def get_dashboard():
    """Récupère l'instance dashboard"""
    return TLDRDashboard()

def show_main_dashboard():
    """Affichage du dashboard principal"""
    st.title("📰 TLDR Dashboard")
    st.markdown("### 🚀 Votre veille technologique automatisée avec TTS")
    
    dashboard = get_dashboard()
    stats = dashboard.get_statistics()
    
    if not stats:
        st.warning("⚠️ Aucune donnée trouvée")
        st.info("💡 Utilisez la section '⚙️ Automatisation' pour lancer votre premier scraping")
        return
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📰 Articles Total",
            value=stats['total_articles'],
            delta=f"Base: {stats['db_size_mb']} MB"
        )
    
    with col2:
        st.metric(
            label="📊 Synthèses",
            value=stats['total_syntheses'],
            delta="Quotidiennes"
        )
    
    with col3:
        st.metric(
            label="📋 Rapports",
            value=stats['total_rapports'],
            delta="Automatisés"
        )
    
    with col4:
        avg_articles = stats['total_articles'] / max(stats['total_syntheses'], 1)
        st.metric(
            label="📈 Moyenne/Jour",
            value=f"{avg_articles:.1f}",
            delta="Articles"
        )
    
    # Graphiques
    if stats['articles_by_type']:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Articles par Newsletter")
            fig = px.pie(
                values=list(stats['articles_by_type'].values()),
                names=list(stats['articles_by_type'].keys()),
                title="Répartition par type de newsletter"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("📅 Articles récents")
            if stats['recent_articles']:
                dates, counts = zip(*stats['recent_articles'])
                fig = px.bar(
                    x=dates, y=counts,
                    title="Articles par jour (30 derniers jours)"
                )
                st.plotly_chart(fig, use_container_width=True)

def check_tts_availability():
    """Vérifie si le TTS est disponible et affiche un avertissement si nécessaire"""
    try:
        import pyttsx3
        
        # Test rapide d'initialisation
        engine = pyttsx3.init()
        engine.stop()
        return True
        
    except ImportError:
        st.warning("⚠️ TTS non disponible - Module pyttsx3 manquant")
        st.code("pip install pyttsx3")
        return False
    except Exception as e:
        st.warning(f"⚠️ TTS non disponible - {e}")
        return False

def show_articles_explorer():
    """Explorateur d'articles avec TTS intégré et filtres avancés"""
    st.title("🔍 Explorateur d'Articles avec Audio")
    
    # Vérification TTS en haut de page
    tts_available = check_tts_availability()
    
    dashboard = get_dashboard()
    
    # Nettoyage automatique des fichiers audio anciens
    if 'tts_manager' in st.session_state:
        st.session_state.tts_manager.cleanup_old_files()
    
    # Section des filtres améliorée
    st.subheader("🎯 Filtres de recherche")
    
    # Première ligne de filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_query = st.text_input("🔍 Rechercher", placeholder="Titre ou contenu...")
    
    with col2:
        # Récupérer les types disponibles depuis la base
        conn = dashboard.connect_db()
        available_types = []
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT newsletter_type FROM articles WHERE newsletter_type IS NOT NULL ORDER BY newsletter_type")
                available_types = [row[0] for row in cursor.fetchall()]
                conn.close()
            except Exception:
                conn.close()
        
        # Filtre par type
        if available_types:
            type_options = ["Tous les types"] + available_types
            selected_type = st.selectbox("📰 Type de newsletter", type_options)
        else:
            selected_type = "Tous les types"
            st.selectbox("📰 Type de newsletter", ["Aucun type disponible"], disabled=True)
    
    with col3:
        limit = st.selectbox("📊 Nombre d'articles", [20, 50, 100, 200], index=1)
    
    # Deuxième ligne de filtres
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtre par période
        date_filter = st.selectbox(
            "📅 Période",
            ["Toutes les dates", "Aujourd'hui", "7 derniers jours", "30 derniers jours", "Personnalisée"]
        )
    
    with col2:
        # Si période personnalisée, afficher les sélecteurs de date
        if date_filter == "Personnalisée":
            date_start = st.date_input("📅 Date début", value=date.today() - timedelta(days=30))
        else:
            date_start = None
    
    with col3:
        if date_filter == "Personnalisée":
            date_end = st.date_input("📅 Date fin", value=date.today())
        else:
            date_end = None
    
    # Récupération des articles avec filtres
    articles_df = dashboard.get_filtered_articles(
        limit=limit, 
        search=search_query,
        newsletter_type=selected_type if selected_type != "Tous les types" else None,
        date_filter=date_filter,
        date_start=date_start,
        date_end=date_end
    )
    
    if articles_df.empty:
        st.warning("⚠️ Aucun article trouvé avec ces critères")
        st.info("💡 Essayez de modifier vos filtres ou lancez un nouveau scraping")
        return
    
    # Affichage du nombre de résultats et bouton de reset
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success(f"✅ {len(articles_df)} article(s) trouvé(s)")
    with col2:
        if st.button("🔄 Reset filtres", help="Réinitialiser tous les filtres"):
            st.rerun()
    
    # Affichage des articles avec TTS
    for idx, article in articles_df.iterrows():
        with st.expander(f"📰 {article['titre'][:80]}..." if len(article['titre']) > 80 else article['titre']):
            
            # Informations de l'article
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**📌 Titre:** {article['titre']}")
                if article['resume_tldr']:
                    st.markdown(f"**📝 Résumé:** {article['resume_tldr']}")
                if article['url']:
                    st.markdown(f"**🔗 URL:** [{article['url'][:50]}...]({article['url']})")
            
            with col2:
                st.write(f"**📅 Date:** {article['date_extraction']}")
                st.write(f"**📊 Type:** {article['newsletter_type']}")
                if 'categories_str' in article and article['categories_str']:
                    st.write(f"**🏷️ Catégories:** {article['categories_str']}")
                if 'duree_lecture' in article and article['duree_lecture']:
                    st.write(f"**⏱️ Lecture:** {article['duree_lecture']}")
            
            # Contrôles TTS (seulement si TTS disponible)
            if tts_available:
                st.markdown("---")
                st.markdown("**🎵 Contrôles Audio:**")
                
                # Préparer le texte pour TTS
                resume_text = article['resume_tldr'] if article['resume_tldr'] else "Pas de résumé disponible"
                
                # Afficher les contrôles TTS
                show_tts_controls(
                    text=resume_text,
                    unique_key=f"article_{article['id']}",
                    title=article['titre']
                )
            else:
                st.info("💡 Installez pyttsx3 pour activer les fonctionnalités audio")
    
    # Export avec informations sur les filtres appliqués
    if not articles_df.empty:
        st.subheader("📤 Export")
        
        # Informations sur les filtres appliqués
        filters_info = []
        if search_query:
            filters_info.append(f"Recherche: '{search_query}'")
        if selected_type != "Tous les types":
            filters_info.append(f"Type: {selected_type}")
        if date_filter != "Toutes les dates":
            filters_info.append(f"Période: {date_filter}")
        
        if filters_info:
            st.info(f"🎯 Filtres appliqués: {' | '.join(filters_info)}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = articles_df.to_csv(index=False)
            filename_suffix = f"_filtered_{datetime.now().strftime('%Y%m%d_%H%M')}" if filters_info else f"_{datetime.now().strftime('%Y%m%d')}"
            st.download_button(
                label="💾 Télécharger CSV",
                data=csv,
                file_name=f"tldr_articles{filename_suffix}.csv",
                mime="text/csv"
            )
        
        with col2:
            json_data = articles_df.to_json(orient='records', indent=2)
            st.download_button(
                label="💾 Télécharger JSON",
                data=json_data,
                file_name=f"tldr_articles{filename_suffix}.json",
                mime="application/json"
            )

def show_syntheses_viewer():
    """Visualiseur de synthèses avec TTS"""
    st.title("📊 Synthèses Quotidiennes avec Audio")
    
    dashboard = get_dashboard()
    syntheses_df = dashboard.get_syntheses()
    
    if syntheses_df.empty:
        st.warning("⚠️ Aucune synthèse trouvée")
        st.info("💡 Les synthèses sont générées automatiquement lors du scraping")
        return
    
    st.success(f"✅ {len(syntheses_df)} synthèses trouvées")
    
    # Sélection de synthèse
    synthesis_dates = syntheses_df['date_synthese'].tolist()
    selected_date = st.selectbox("📅 Choisir une synthèse", synthesis_dates)
    
    # Affichage de la synthèse sélectionnée
    selected_synthesis = syntheses_df[syntheses_df['date_synthese'] == selected_date].iloc[0]
    
    st.subheader(f"📊 Synthèse du {selected_date}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📰 Articles analysés", selected_synthesis['nb_articles'])
    with col2:
        st.metric("⏱️ Temps de traitement", f"{selected_synthesis['temps_traitement']:.1f}s")
    with col3:
        st.metric("📊 Type", selected_synthesis['newsletter_type'].upper())
    
    # Contenu de la synthèse
    st.subheader("📝 Contenu")
    st.markdown(selected_synthesis['contenu'])
    
    # Contrôles TTS pour la synthèse
    st.markdown("---")
    st.markdown("**🎵 Écouter la synthèse:**")
    show_tts_controls(
        text=selected_synthesis['contenu'],
        unique_key=f"synthesis_{selected_date}",
        title=f"Synthèse TLDR {selected_synthesis['newsletter_type'].upper()} du {selected_date}"
    )

def run_scraping_task(newsletter_type, max_articles, mode_name, year=None, month=None, day=None):
    """Exécute le scraping avec gestion d'erreurs robuste et support période"""
    results = {
        'success': False,
        'articles_count': 0,
        'saved_count': 0,
        'synthesis': '',
        'error': None,
        'articles': []
    }

    try:
        # Imports avec gestion d'erreur
        try:
            from core.tdlrscraper import TLDRScraper
            from core.aiprocessor import AIProcessor
            from core.sqliteintegrator import SQLiteIntegrator
        except ImportError as e:
            results['error'] = f"Module manquant: {e}"
            return results

        # Test Ollama
        try:
            import ollama
            ollama.list()  # Test de connexion
        except Exception as e:
            results['error'] = f"Ollama non disponible: {e}"
            return results

        # Initialisation
        # Ajout des paramètres year, month, day si fournis
        scraper = TLDRScraper(newsletter_type, max_articles=max_articles, country_code='US', year=locals().get('year'), month=locals().get('month'), day=locals().get('day'))
        ai_processor = AIProcessor()
        sqlite = SQLiteIntegrator()

        # Test connexion SQLite
        if not sqlite.test_connection():
            results['error'] = "Connexion SQLite échouée"
            return results

        # Phase 1: Extraction
        articles = scraper.scrape_articles()
        if not articles:
            results['error'] = "Aucun article extrait"
            return results

        results['articles_count'] = len(articles)
        results['articles'] = articles[:3]  # Sample pour affichage

        # Phase 2: Traitement IA
        categorized_articles = ai_processor.categorize_articles(articles)
        synthesis = ai_processor.synthesize_articles(categorized_articles)
        results['synthesis'] = synthesis

        # Phase 3: Sauvegarde GARANTIE
        # Utiliser la date sélectionnée si fournie, sinon aujourd'hui
        year = locals().get('year')
        month = locals().get('month')
        day = locals().get('day')
        from datetime import date
        if year and month:
            if day:
                date_formatted = f"{year:04d}-{month:02d}-{day:02d}"
            else:
                date_formatted = f"{year:04d}-{month:02d}-01"
        else:
            date_formatted = date.today().strftime('%Y-%m-%d')

        daily_results = {
            'date_formatted': date_formatted,
            'newsletter_type': newsletter_type,
            'articles_extracted': len(articles),
            'articles': categorized_articles,
            'synthesis': synthesis,
            'processing_time': 1.0,
            'success': True,
            'errors': []
        }

        # Sauvegarde avec vérification
        saved_ids = sqlite.save_complete_daily_results(daily_results)

        if saved_ids and saved_ids.get('articles'):
            results['saved_count'] = len(saved_ids['articles'])
            results['success'] = True
        else:
            # Tentative de sauvegarde manuelle en cas d'échec
            manual_ids = sqlite.bulk_add_articles(categorized_articles)
            if manual_ids:
                results['saved_count'] = len(manual_ids)
                results['success'] = True
            else:
                results['error'] = "Échec sauvegarde (même manuelle)"

    except Exception as e:
        results['error'] = f"Erreur générale: {str(e)}"

    return results

def show_automation_control():
    """Contrôle de l'automatisation avec scraping RÉEL"""
    st.title("⚙️ Contrôle de l'Automatisation")
    
    st.markdown("### 🚀 Scraping TLDR en temps réel")
    
    # Configuration
    from datetime import date
    import calendar
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        newsletter_type = st.selectbox(
            "📰 Type de newsletter",
            ["tech", "ai", "crypto", "marketing", "design", "webdev"],
            help="Choisir le type de newsletter TLDR à scraper"
        )

    with col2:
        mode = st.selectbox(
            "⚡ Mode de scraping",
            ["🔥 Test rapide (5 articles)", "📊 Standard (15 articles)", "🚀 Complet (25 articles)"],
            help="Test rapide recommandé pour les premiers essais"
        )

    with col3:
        # Extraction du nombre d'articles selon le mode
        if "5 articles" in mode:
            max_articles = 5
        elif "15 articles" in mode:
            max_articles = 15
        else:
            max_articles = 25
        st.metric("📊 Articles à extraire", max_articles)

    with col4:
        st.markdown("**🗓️ Période à scraper**")
        year = st.number_input("Année", min_value=2020, max_value=date.today().year, value=date.today().year, step=1, key="scrape_year")
        month = st.selectbox("Mois", list(range(1, 13)), index=date.today().month-1, key="scrape_month")
        day_mode = st.checkbox("Sélectionner un jour précis", value=False, key="scrape_day_mode")
        if day_mode:
            days_in_month = calendar.monthrange(int(year), int(month))[1]
            day = st.number_input("Jour", min_value=1, max_value=days_in_month, value=min(date.today().day, days_in_month), step=1, key="scrape_day")
        else:
            day = None
    
    # Status des services
    st.markdown("### 🔧 Status des Services")
    
    col1, col2 = st.columns(2)
    
    # Status SQLite
    with col1:
        dashboard = get_dashboard()
        if dashboard.connect_db():
            stats = dashboard.get_statistics()
            st.success("✅ SQLite connectée")
            st.info(f"📊 {stats.get('total_articles', 0)} articles existants")
        else:
            st.error("❌ SQLite non disponible")
    
    # Status Ollama
    with col2:
        try:
            import ollama
            models = ollama.list()
            st.success("✅ Ollama connecté")
            st.info(f"🎯 {len(models.get('models', []))} modèles")
        except Exception:
            st.error("❌ Ollama non disponible")
            # Ne plus afficher la commande à lancer
    
    # Zone de lancement
    st.markdown("---")

    # Bouton principal
    if st.button("🚀 Lancer le Scraping", type="primary", key="main_scraping_btn"):
        # Préparer les paramètres de période à passer au scraping
        scrape_params = {
            'year': int(year),
            'month': int(month),
            'day': int(day) if day else None
        }

        # Conteneurs pour l'affichage
        with st.container():
            st.info(f"🔄 Lancement du scraping {newsletter_type.upper()} pour {scrape_params['year']}-{scrape_params['month']:02d}" + (f"-{scrape_params['day']:02d}" if scrape_params['day'] else "") + "...")

            # Barre de progression
            progress_bar = st.progress(0)
            status_text = st.empty()

            # Phase 1: Préparation
            status_text.text("📦 Initialisation...")
            progress_bar.progress(10)
            time.sleep(0.5)

            # Phase 2: Scraping
            status_text.text(f"🔍 Extraction articles {newsletter_type}...")
            progress_bar.progress(30)

            # Exécution du scraping avec période
            results = run_scraping_task(newsletter_type, max_articles, mode, year=scrape_params['year'], month=scrape_params['month'], day=scrape_params['day'])
            progress_bar.progress(70)

            # Phase 3: Traitement
            if results['success']:
                status_text.text("🤖 Traitement IA et sauvegarde...")
                progress_bar.progress(90)
                time.sleep(0.5)

                progress_bar.progress(100)
                status_text.text("✅ Terminé avec succès!")

                # Résultats
                st.success("🎉 Scraping terminé avec succès!")

                # Métriques
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📰 Articles extraits", results['articles_count'])
                with col2:
                    st.metric("💾 Articles sauvés", results['saved_count'])
                with col3:
                    st.metric("📊 Taux de réussite", "100%")

                # Aperçu des articles
                if results['articles']:
                    st.subheader("📋 Aperçu des articles extraits")
                    for i, article in enumerate(results['articles'], 1):
                        st.write(f"**{i}.** {article.get('titre', 'Sans titre')[:80]}...")

                # Synthèse avec TTS
                if results['synthesis']:
                    st.subheader("📊 Synthèse générée")
                    synthesis_text = results['synthesis'][:300] + "..." if len(results['synthesis']) > 300 else results['synthesis']
                    st.write(synthesis_text)

                    # Contrôles TTS pour la synthèse
                    st.markdown("**🔊 Écouter la synthèse:**")
                    show_tts_controls(results['synthesis'], f"scraping_synthesis_{int(time.time())}")

                # Actions suivantes
                st.subheader("🎯 Prochaines étapes")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("🔄 Actualiser dashboard", key="refresh_btn"):
                        st.cache_resource.clear()
                        st.rerun()

                with col2:
                    if st.button("🔍 Voir les articles", key="view_articles_btn"):
                        st.session_state['goto_page'] = "🔍 Articles"
                        st.rerun()

                with col3:
                    if st.button("📊 Voir les synthèses", key="view_syntheses_btn"):
                        st.session_state['goto_page'] = "📊 Synthèses"
                        st.rerun()

            else:
                # Erreur
                progress_bar.progress(100)
                st.error(f"❌ Erreur: {results['error']}")

                # Debug info
                with st.expander("🔧 Informations de dépannage"):
                    st.write("**Problème détecté:**")
                    st.code(results['error'])

                    st.write("**Solutions suggérées:**")
                    if "Ollama" in results['error']:
                        st.write("• Vérifiez qu'Ollama est démarré: `ollama serve`")
                        st.write("• Installez le modèle: `ollama pull nous-hermes2:latest`")
                    elif "Module" in results['error']:
                        st.write("• Installez les dépendances: `pip install -r requirements.txt`")
                    elif "SQLite" in results['error']:
                        st.write("• Vérifiez les permissions du dossier `data/`")
                    else:
                        st.write("• Vérifiez les logs pour plus de détails")

def show_analytics():
    """Analytics simplifiées"""
    st.title("📈 Analytics")
    
    dashboard = get_dashboard()
    stats = dashboard.get_statistics()
    
    if not stats or stats['total_articles'] == 0:
        st.warning("⚠️ Pas assez de données pour les analytics")
        st.info("💡 Lancez quelques scrapings pour générer des données à analyser")
        return
    
    # Graphiques analytics
    st.subheader("📊 Vue d'ensemble")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Articles par type
        if stats['articles_by_type']:
            fig = px.bar(
                x=list(stats['articles_by_type'].keys()),
                y=list(stats['articles_by_type'].values()),
                title="Articles par type de newsletter"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Timeline
        if stats['recent_articles']:
            dates, counts = zip(*stats['recent_articles'])
            fig = px.line(
                x=dates, y=counts,
                title="Évolution des articles (30 derniers jours)"
            )
            st.plotly_chart(fig, use_container_width=True)


def main():
    """Application principale Streamlit avec TTS"""
    
    # Sidebar
    st.sidebar.title("📰 TLDR Dashboard")
    st.sidebar.markdown("### 🎵 Avec Audio TTS")
    st.sidebar.markdown("---")
    
    # Navigation
    pages = {
        "🏠 Accueil": show_main_dashboard,
        "🔍 Articles": show_articles_explorer,
        "📊 Synthèses": show_syntheses_viewer,
        "⚙️ Automatisation": show_automation_control,
        "📈 Analytics": show_analytics
    }
    
    # Gestion navigation via session state
    if 'goto_page' in st.session_state:
        selected_page = st.session_state['goto_page']
        del st.session_state['goto_page']
    else:
        selected_page = st.sidebar.selectbox("Navigation", list(pages.keys()))
    
    # Informations sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🗄️ Base de données")
    
    dashboard = get_dashboard()
    try:
        stats = dashboard.get_statistics()
        if stats:
            st.sidebar.success("✅ Connectée")
            st.sidebar.info(f"📰 {stats['total_articles']} articles")
            st.sidebar.info(f"💾 {stats['db_size_mb']} MB")
        else:
            st.sidebar.warning("⚠️ Vide")
    except Exception:
        st.sidebar.error("❌ Erreur connexion")
        
    # Raccourcis
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚡ Actions rapides")
    
    if st.sidebar.button("🔄 Actualiser cache"):
        st.cache_resource.clear()
        st.rerun()
    
    if st.sidebar.button("🧪 Test connexions"):
        # Test rapide des connexions
        try:
            import ollama
            ollama.list()
            st.sidebar.success("✅ Ollama OK")
        except:
            st.sidebar.error("❌ Ollama KO")
        
        try:
            dashboard.connect_db()
            st.sidebar.success("✅ SQLite OK")
        except:
            st.sidebar.error("❌ SQLite KO")
        
        try:
            import pyttsx3
            pyttsx3.init()
            st.sidebar.success("✅ TTS OK")
        except:
            st.sidebar.error("❌ TTS KO")
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("🚀 **TLDR Dashboard v2.1**")
    st.sidebar.markdown("🎵 **Audio TTS intégré**")
    st.sidebar.markdown("📱 Scraping + Écoute")
    
    # Affichage de la page
    try:
        pages[selected_page]()
    except Exception as e:
        st.error(f"❌ Erreur page: {e}")
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()