#!/usr/bin/env python3
"""
🚀 Lanceur pour le Dashboard Streamlit TLDR
"""

import subprocess
import sys
import os
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_streamlit_installation():
    """Vérifie si Streamlit est installé"""
    try:
        import streamlit
        logger.info(f"✅ Streamlit {streamlit.__version__} installé")
        return True
    except ImportError:
        logger.error("❌ Streamlit non installé")
        return False

def install_requirements():
    """Installe les dépendances Streamlit"""
    logger.info("📦 Installation des dépendances Streamlit...")
    
    try:
        # Installer depuis requirements-streamlit.txt si disponible
        req_file = Path("requirements-streamlit.txt")
        if req_file.exists():
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        else:
            # Installation manuelle des packages essentiels
            packages = ["streamlit>=1.28.0", "plotly>=5.17.0", "pandas>=2.0.0"]
            for package in packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        logger.info("✅ Dépendances installées avec succès")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erreur installation: {e}")
        return False

def check_database():
    """Vérifie si la base de données SQLite existe"""
    db_path = Path("data/tldr_database.db")
    
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ Base de données trouvée: {size_mb:.2f} MB")
        return True
    else:
        logger.warning("⚠️ Base de données non trouvée")
        logger.info("💡 Lancez d'abord l'automatisation TLDR pour créer des données")
        return False

def launch_dashboard():
    """Lance le dashboard Streamlit"""
    dashboard_file = Path("streamlit_dashboard.py")
    
    if not dashboard_file.exists():
        logger.error(f"❌ Fichier dashboard non trouvé: {dashboard_file}")
        return False
    
    logger.info("🚀 Lancement du dashboard Streamlit...")
    logger.info("🌐 Le dashboard va s'ouvrir dans votre navigateur")
    
    try:
        # Lancer Streamlit
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_file),
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ]
        
        subprocess.run(cmd)
        return True
        
    except KeyboardInterrupt:
        logger.info("🛑 Dashboard arrêté par l'utilisateur")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lancement: {e}")
        return False

def show_welcome():
    """Affiche l'écran d'accueil"""
    print("🚀 TLDR Dashboard Launcher")
    print("=" * 50)
    print("📊 Votre tableau de bord TLDR interactif")
    print()

def show_features():
    """Affiche les fonctionnalités du dashboard"""
    print("🎯 FONCTIONNALITÉS:")
    print("   📈 Statistiques en temps réel")
    print("   🔍 Explorateur d'articles interactif")
    print("   📊 Visualisation des synthèses")
    print("   ⚙️ Contrôle de l'automatisation")
    print("   📈 Analytics avancées")
    print("   📤 Export des données (CSV/JSON)")
    print("   🔄 Actualisation automatique")
    print()

def main():
    """Fonction principale"""
    show_welcome()
    show_features()
    
    print("🔍 VÉRIFICATIONS PRÉLIMINAIRES:")
    print("-" * 30)
    
    # 1. Vérifier Streamlit
    if not check_streamlit_installation():
        print("❓ Installer Streamlit? (o/N)")
        install = input("> ").strip().lower()
        
        if install in ['o', 'oui', 'y', 'yes']:
            if not install_requirements():
                print("💥 Échec de l'installation")
                return
        else:
            print("👋 Installation annulée")
            return
    
    # 2. Vérifier la base de données
    db_exists = check_database()
    
    if not db_exists:
        print("\n❓ Voulez-vous continuer sans données? (o/N)")
        print("💡 Le dashboard fonctionnera mais sera vide")
        continue_empty = input("> ").strip().lower()
        
        if continue_empty not in ['o', 'oui', 'y', 'yes']:
            print("💡 Lancez d'abord: python automation/run_monthly.py")
            return
    
    # 3. Lancer le dashboard
    print("\n" + "=" * 50)
    print("🚀 LANCEMENT DU DASHBOARD")
    print("=" * 50)
    print("🌐 URL: http://localhost:8501")
    print("⚠️ Laissez cette fenêtre ouverte")
    print("🛑 Appuyez sur Ctrl+C pour arrêter")
    print("-" * 50)
    
    # Petite pause pour que l'utilisateur lise
    import time
    time.sleep(2)
    
    # Lancement
    if launch_dashboard():
        print("✅ Dashboard fermé proprement")
    else:
        print("❌ Erreur lors du lancement")

def quick_launch():
    """Lancement rapide sans vérifications"""
    print("⚡ LANCEMENT RAPIDE")
    print("-" * 20)
    
    if not check_streamlit_installation():
        print("❌ Streamlit requis: pip install streamlit plotly pandas")
        return
    
    launch_dashboard()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        quick_launch()
    else:
        main()

# Instructions d'utilisation en bas du fichier
print("""
📋 USAGE:
  python run_dashboard.py           # Lancement avec vérifications
  python run_dashboard.py --quick   # Lancement rapide
  
📚 AIDE:
  - Dashboard URL: http://localhost:8501
  - Port par défaut: 8501
  - Arrêt: Ctrl+C dans ce terminal
  
🔧 DÉPENDANCES:
  pip install streamlit plotly pandas
""")
