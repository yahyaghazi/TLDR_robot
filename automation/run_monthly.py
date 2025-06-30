#!/usr/bin/env python3
"""
Interface utilisateur simplifiée pour l'automatisation mensuelle TLDR
Structure réorganisée avec chemins absolus
"""

import subprocess
import sys
import calendar
from datetime import datetime, date
from pathlib import Path

# Ajouter les chemins pour les imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def show_welcome():
    """Affiche l'écran d'accueil"""
    print("🤖 TLDR Monthly Automation - Interface Simplifiée")
    print("=" * 60)
    print("📁 Projet organisé et prêt à l'emploi!")
    print(f"📂 Dossier: {project_root}")
    
    # Vérifier la structure
    required_dirs = ['core', 'automation', 'data/audio_summaries', 'data/json_results']
    missing_dirs = [d for d in required_dirs if not (project_root / d).exists()]
    
    if missing_dirs:
        print(f"⚠️ Dossiers manquants: {missing_dirs}")
        return False
    
    print("✅ Structure vérifiée et prête")
    return True


def show_menu():
    """Affiche le menu interactif"""
    print("\n📰 NEWSLETTERS TLDR DISPONIBLES:")
    newsletters = {
        '1': ('tech', 'Technologie générale'),
        '2': ('ai', 'Intelligence Artificielle'), 
        '3': ('crypto', 'Cryptomonnaies & Web3'),
        '4': ('marketing', 'Marketing digital'),
        '5': ('design', 'Design & UX'),
        '6': ('webdev', 'Développement Web')
    }
    
    for key, (value, description) in newsletters.items():
        print(f"  {key}. TLDR {value.upper():<10} - {description}")
    
    print("\n📅 PÉRIODES POPULAIRES:")
    periods = {
        'a': ('2025', '6', 'Juin 2025 (recommandé)'),
        'b': ('2025', '5', 'Mai 2025'),
        'c': ('2025', '4', 'Avril 2025'),
        'd': ('custom', 'custom', 'Période personnalisée')
    }
    
    for key, (year, month, description) in periods.items():
        print(f"  {key}. {description}")
    
    return newsletters, periods


def get_user_choices():
    """Récupère les choix de l'utilisateur"""
    newsletters, periods = show_menu()
    
    # Choix de la newsletter
    print(f"\n🎯 Choisissez la newsletter (1-{len(newsletters)}):")
    while True:
        try:
            choice = input("Newsletter> ").strip()
            if choice in newsletters:
                newsletter_type, newsletter_desc = newsletters[choice]
                print(f"✅ Sélectionné: TLDR {newsletter_type.upper()} - {newsletter_desc}")
                break
            else:
                print(f"❌ Choix invalide. Entrez un nombre entre 1 et {len(newsletters)}")
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            sys.exit(0)
    
    # Choix de la période
    print(f"\n📅 Choisissez la période:")
    while True:
        try:
            choice = input("Période> ").strip().lower()
            if choice in periods:
                year_str, month_str, period_desc = periods[choice]
                if year_str == 'custom':
                    year, month = get_custom_period()
                else:
                    year, month = int(year_str), int(month_str)
                print(f"✅ Sélectionné: {period_desc}")
                break
            else:
                print(f"❌ Choix invalide. Entrez a, b, c ou d")
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            sys.exit(0)
    
    return newsletter_type, year, month


def get_custom_period():
    """Récupère une période personnalisée"""
    # Année
    current_year = datetime.now().year
    print(f"\n📅 Année (défaut: {current_year}):")
    year_input = input(f"Année [{current_year}]> ").strip()
    year = int(year_input) if year_input else current_year
    
    # Mois
    current_month = datetime.now().month
    print(f"\n📅 Mois (1-12, défaut: {current_month}):")
    
    # Afficher les mois
    for i in range(1, 13):
        month_name = calendar.month_name[i]
        print(f"  {i:2d}. {month_name}")
    
    month_input = input(f"\nMois [{current_month}]> ").strip()
    month = int(month_input) if month_input else current_month
    
    return year, month


def show_month_preview(newsletter_type: str, year: int, month: int):
    """Affiche un aperçu du mois à traiter"""
    month_name = calendar.month_name[month]
    
    print(f"\n📊 APERÇU - TLDR {newsletter_type.upper()} {month_name} {year}")
    print("-" * 50)
    
    # Calculer les jours ouvrables approximatifs (sans jours fériés pour simplifier)
    cal = calendar.monthcalendar(year, month)
    business_days = 0
    weekends = 0
    
    for week in cal:
        for day in week:
            if day != 0:  # Jour valide
                weekday = date(year, month, day).weekday()
                if weekday < 5:  # Lundi=0 à Vendredi=4
                    business_days += 1
                else:
                    weekends += 1
    
    total_days = business_days + weekends
    
    print(f"📅 Jours total: {total_days}")
    print(f"💼 Jours ouvrables (approx): {business_days}")
    print(f"🏖️ Week-ends: {weekends}")
    print(f"🎵 Fichiers audio à générer: ~{business_days}")
    
    # Estimation du temps
    estimated_minutes = business_days * 0.5  # 30s par jour en moyenne
    print(f"⏱️ Temps estimé: ~{estimated_minutes:.1f} minutes")
    
    # Dossiers de sortie
    audio_dir = project_root / 'data' / 'audio_summaries'
    json_dir = project_root / 'data' / 'json_results'
    
    print(f"\n📁 Fichiers générés dans:")
    print(f"   🎵 Audio: {audio_dir}")
    print(f"   📊 JSON:  {json_dir}")


def check_prerequisites():
    """Vérifie les prérequis avant lancement - VERSION CORRIGÉE"""
    print("\n🔍 VÉRIFICATION DES PRÉREQUIS:")
    print("-" * 40)
    
    all_good = True
    
    # Vérifier Ollama
    try:
        import ollama
        print("✅ Module Ollama installé")
        
        # Test de connexion
        try:
            ollama.list()
            print("✅ Ollama connecté et opérationnel")
        except Exception as e:
            print(f"❌ Ollama non connecté: {e}")
            print("   💡 Solution: Lancez 'ollama serve' dans un autre terminal")
            all_good = False
    except ImportError:
        print("❌ Module Ollama manquant")
        print("   💡 Solution: pip install ollama")
        all_good = False
    
    # Vérifier les autres modules avec les bons noms d'import
    required_modules = [
        ('requests', 'requests', 'pip install requests'),
        ('bs4', 'beautifulsoup4', 'pip install beautifulsoup4'),  # Le module s'importe comme 'bs4'
        ('pyttsx3', 'pyttsx3', 'pip install pyttsx3'),
        ('dateutil', 'python-dateutil', 'pip install python-dateutil')
    ]
    
    for import_name, package_name, install_cmd in required_modules:
        try:
            __import__(import_name)
            print(f"✅ {package_name} installé")
        except ImportError:
            print(f"❌ {package_name} manquant")
            print(f"   💡 Solution: {install_cmd}")
            all_good = False
    
    # Vérifier l'espace disque
    try:
        import shutil
        free_space = shutil.disk_usage(project_root).free / (1024**3)  # GB
        if free_space > 1.0:
            print(f"✅ Espace disque: {free_space:.1f} GB disponible")
        else:
            print(f"⚠️ Espace disque faible: {free_space:.1f} GB")
    except:
        print("⚠️ Impossible de vérifier l'espace disque")
    
    return all_good


def run_automation(newsletter_type: str, year: int, month: int):
    """Lance l'automatisation"""
    print(f"\n🚀 LANCEMENT DE L'AUTOMATISATION")
    print(f"📰 Newsletter: TLDR {newsletter_type.upper()}")
    print(f"📅 Période: {calendar.month_name[month]} {year}")
    print("-" * 50)
    
    # Chemin vers le script d'automatisation
    automation_script = project_root / 'automation' / 'monthly_automation.py'
    
    if not automation_script.exists():
        print(f"❌ Script d'automatisation non trouvé: {automation_script}")
        return False
    
    # Commande à exécuter
    cmd = [
        sys.executable,  # Python executable
        str(automation_script),
        str(year),
        str(month),
        newsletter_type
    ]
    
    print(f"💻 Commande: {' '.join(cmd[1:])}")  # Masquer le chemin Python complet
    print(f"📁 Logs: data/logs/monthly_automation.log")
    print("\n⚡ Démarrage...")
    
    try:
        # Lancement avec affichage en temps réel
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            cwd=str(project_root)  # Définir le dossier de travail
        )
        
        # Affichage en temps réel
        for line in process.stdout:
            print(line, end='')
        
        # Attendre la fin
        return_code = process.wait()
        
        if return_code == 0:
            print(f"\n✅ AUTOMATISATION TERMINÉE AVEC SUCCÈS!")
            
            # Afficher les résultats
            audio_dir = project_root / 'data' / 'audio_summaries'
            json_dir = project_root / 'data' / 'json_results'
            
            # Compter les fichiers générés
            audio_files = list(audio_dir.glob(f"tldr_{newsletter_type}_*.wav"))
            json_files = list(json_dir.glob(f"tldr_{newsletter_type}_*.json"))
            
            print(f"🎵 {len(audio_files)} fichiers audio dans: {audio_dir}")
            print(f"📊 {len(json_files)} fichiers JSON dans: {json_dir}")
            
            # Afficher quelques exemples
            if audio_files:
                print(f"\n🎵 Exemples de fichiers audio:")
                for audio_file in sorted(audio_files)[-3:]:  # 3 derniers fichiers
                    print(f"   🎵 {audio_file.name}")
        else:
            print(f"\n❌ ERREUR - Code de retour: {return_code}")
            print(f"📋 Consultez les logs pour plus de détails")
        
        return return_code == 0
        
    except KeyboardInterrupt:
        print(f"\n🛑 ARRÊT DEMANDÉ PAR L'UTILISATEUR")
        try:
            process.terminate()
        except:
            pass
        return False
    except Exception as e:
        print(f"\n❌ ERREUR LORS DU LANCEMENT: {e}")
        return False


def quick_modes():
    """Modes rapides prédéfinies"""
    print("\n⚡ MODES RAPIDES:")
    quick_options = {
        '1': ('tech', 2025, 6, 'TLDR Tech - Juin 2025 (recommandé)'),
        '2': ('ai', 2025, 6, 'TLDR AI - Juin 2025'),
        '3': ('tech', datetime.now().year, datetime.now().month, 'TLDR Tech - Mois courant'),
        '4': ('custom', 'custom', 'custom', 'Mode personnalisé')
    }
    
    for key, (newsletter, year, month, description) in quick_options.items():
        print(f"  {key}. {description}")
    
    choice = input("\nMode rapide (1-4)> ").strip()
    
    if choice in quick_options:
        newsletter, year, month, _ = quick_options[choice]
        if newsletter == 'custom':
            return get_user_choices()
        else:
            return newsletter, year, month
    else:
        print("❌ Choix invalide, mode personnalisé...")
        return get_user_choices()


def show_existing_results():
    """Affiche les résultats existants"""
    audio_dir = project_root / 'data' / 'audio_summaries'
    json_dir = project_root / 'data' / 'json_results'
    
    audio_files = list(audio_dir.glob("*.wav")) if audio_dir.exists() else []
    json_files = list(json_dir.glob("*.json")) if json_dir.exists() else []
    
    if audio_files or json_files:
        print("\n📊 RÉSULTATS EXISTANTS:")
        print("-" * 30)
        
        if audio_files:
            print(f"🎵 {len(audio_files)} fichiers audio trouvés:")
            for audio_file in sorted(audio_files)[-5:]:  # 5 derniers
                file_size = audio_file.stat().st_size / 1024  # KB
                print(f"   🎵 {audio_file.name} ({file_size:.1f} KB)")
        
        if json_files:
            print(f"\n📊 {len(json_files)} fichiers JSON trouvés:")
            for json_file in sorted(json_files)[-5:]:  # 5 derniers
                print(f"   📊 {json_file.name}")
        
        # Résumés mensuels
        monthly_files = list(json_dir.glob("*monthly*.json")) if json_dir.exists() else []
        if monthly_files:
            print(f"\n📈 {len(monthly_files)} résumés mensuels:")
            for monthly_file in sorted(monthly_files):
                print(f"   📈 {monthly_file.name}")
    else:
        print("\n📊 Aucun résultat existant trouvé")
        print("   💡 Lancez une automatisation pour générer du contenu!")


def main():
    """Fonction principale"""
    try:
        # Écran d'accueil
        if not show_welcome():
            print("❌ Impossible de continuer - structure incomplète")
            return
        
        # Afficher les résultats existants
        show_existing_results()
        
        # Vérifications préliminaires
        if not check_prerequisites():
            print(f"\n❌ Prérequis manquants - résolvez les problèmes ci-dessus")
            print(f"💡 Pour continuer malgré tout, tapez 'force'")
            
            user_input = input("\nContinuer? (force/N)> ").strip().lower()
            if user_input != 'force':
                print("👋 Installation des prérequis recommandée avant utilisation")
                return
        
        print("\n" + "="*60)
        
        # Choix de la configuration
        newsletter, year, month = quick_modes()
        
        # Aperçu
        show_month_preview(newsletter, year, month)
        
        # Confirmation finale
        month_name = calendar.month_name[month]
        print(f"\n❓ Lancer l'automatisation TLDR {newsletter.upper()} pour {month_name} {year}?")
        print(f"⚠️ Cette opération peut prendre 20-40 minutes selon le mois")
        
        confirm = input("Continuer? (o/N)> ").strip().lower()
        
        if confirm in ['o', 'oui', 'y', 'yes']:
            print(f"\n🎬 C'est parti!")
            success = run_automation(newsletter, year, month)
            
            if success:
                print(f"\n🎉 MISSION ACCOMPLIE!")
                print(f"🎵 Vos résumés audio TLDR {newsletter.upper()} sont prêts!")
                print(f"📁 Consultez le dossier: data/audio_summaries/")
                
                # Proposer d'ouvrir le dossier
                try:
                    import os
                    audio_dir = project_root / 'data' / 'audio_summaries'
                    print(f"\n💡 Ouvrir le dossier des résultats?")
                    open_folder = input("Ouvrir? (o/N)> ").strip().lower()
                    
                    if open_folder in ['o', 'oui', 'y', 'yes']:
                        if os.name == 'nt':  # Windows
                            os.startfile(str(audio_dir))
                        elif os.name == 'posix':  # macOS/Linux
                            os.system(f'open "{audio_dir}"' if sys.platform == 'darwin' else f'xdg-open "{audio_dir}"')
                except Exception as e:
                    print(f"⚠️ Impossible d'ouvrir le dossier automatiquement: {e}")
            else:
                print(f"\n😞 Il y a eu des problèmes...")
                print(f"📋 Consultez les logs: data/logs/monthly_automation.log")
        else:
            print("\n👋 Automatisation annulée")
    
    except KeyboardInterrupt:
        print(f"\n👋 Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()