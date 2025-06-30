#!/usr/bin/env python3
"""
Script de lancement simplifié pour l'automatisation mensuelle TLDR
Usage simple avec configurations prédéfinies
"""

import subprocess
import sys
from datetime import datetime, date
import calendar

def show_menu():
    """Affiche le menu interactif"""
    print("🤖 TLDR Monthly Automation - Lancement Simplifié")
    print("=" * 55)
    
    print("\n📰 NEWSLETTERS DISPONIBLES:")
    newsletters = {
        '1': 'tech',
        '2': 'ai', 
        '3': 'crypto',
        '4': 'marketing',
        '5': 'design',
        '6': 'webdev'
    }
    
    for key, value in newsletters.items():
        print(f"  {key}. TLDR {value.upper()}")
    
    print("\n📅 MOIS DISPONIBLES:")
    months = {
        '1': 'Janvier', '2': 'Février', '3': 'Mars', '4': 'Avril',
        '5': 'Mai', '6': 'Juin', '7': 'Juillet', '8': 'Août', 
        '9': 'Septembre', '10': 'Octobre', '11': 'Novembre', '12': 'Décembre'
    }
    
    for key, value in months.items():
        print(f"  {key:2s}. {value}")
    
    return newsletters, months

def get_user_choices():
    """Récupère les choix de l'utilisateur"""
    newsletters, months = show_menu()
    
    # Choix de la newsletter
    print(f"\n🎯 Choisissez la newsletter (1-{len(newsletters)}):")
    while True:
        try:
            choice = input("Newsletter> ").strip()
            if choice in newsletters:
                newsletter = newsletters[choice]
                break
            else:
                print(f"❌ Choix invalide. Entrez un nombre entre 1 et {len(newsletters)}")
        except KeyboardInterrupt:
            print("\n👋 Au revoir!")
            sys.exit(0)
    
    # Année
    current_year = datetime.now().year
    print(f"\n📅 Année (défaut: {current_year}):")
    year_input = input(f"Année [{current_year}]> ").strip()
    year = int(year_input) if year_input else current_year
    
    # Mois
    current_month = datetime.now().month
    print(f"\n📅 Mois (1-12, défaut: {current_month}):")
    month_input = input(f"Mois [{current_month}]> ").strip()
    month = int(month_input) if month_input else current_month
    
    return newsletter, year, month

def show_month_preview(year: int, month: int):
    """Affiche un aperçu du mois à traiter"""
    month_name = calendar.month_name[month]
    
    print(f"\n📊 APERÇU - {month_name} {year}")
    print("-" * 40)
    
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

def run_automation(newsletter: str, year: int, month: int):
    """Lance l'automatisation"""
    print(f"\n🚀 LANCEMENT DE L'AUTOMATISATION")
    print(f"📰 Newsletter: TLDR {newsletter.upper()}")
    print(f"📅 Période: {calendar.month_name[month]} {year}")
    print("-" * 50)
    
    # Commande à exécuter
    cmd = [
        sys.executable,  # Python executable
        "monthly_automation.py",
        str(year),
        str(month),
        newsletter
    ]
    
    print(f"💻 Commande: {' '.join(cmd)}")
    print(f"📁 Logs: monthly_automation.log")
    print("\n⚡ Démarrage...")
    
    try:
        # Lancement avec affichage en temps réel
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Affichage en temps réel
        for line in process.stdout:
            print(line, end='')
        
        # Attendre la fin
        return_code = process.wait()
        
        if return_code == 0:
            print(f"\n✅ AUTOMATISATION TERMINÉE AVEC SUCCÈS!")
            print(f"🎵 Vérifiez le dossier './audio_summaries' pour les fichiers audio")
            print(f"📊 Vérifiez le dossier './json_results' pour les données")
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
    """Modes rapides prédéfinis"""
    print("\n⚡ MODES RAPIDES:")
    print("  1. TLDR Tech - Juin 2025 (recommandé)")
    print("  2. TLDR AI - Juin 2025") 
    print("  3. TLDR Tech - Mois courant")
    print("  4. Mode personnalisé")
    
    choice = input("\nMode rapide (1-4)> ").strip()
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    if choice == '1':
        return 'tech', 2025, 6
    elif choice == '2':
        return 'ai', 2025, 6
    elif choice == '3':
        return 'tech', current_year, current_month
    elif choice == '4':
        return get_user_choices()
    else:
        print("❌ Choix invalide, mode personnalisé...")
        return get_user_choices()

def main():
    """Fonction principale"""
    try:
        print("🔥 Bienvenue dans TLDR Monthly Automation!")
        
        # Vérifications préliminaires
        print("\n🔍 VÉRIFICATIONS:")
        
        # Vérifier Ollama
        try:
            import ollama
            print("✅ Module Ollama installé")
            
            # Test de connexion
            try:
                ollama.list()
                print("✅ Ollama connecté")
            except:
                print("⚠️ Ollama non connecté - assurez-vous qu'il fonctionne: ollama serve")
        except ImportError:
            print("❌ Module Ollama manquant - installez avec: pip install ollama")
            return
        
        # Vérifier les autres modules
        required_modules = ['requests', 'beautifulsoup4', 'pyttsx3']
        for module in required_modules:
            try:
                __import__(module.replace('-', '_'))
                print(f"✅ {module} installé")
            except ImportError:
                print(f"❌ {module} manquant - installez avec: pip install {module}")
        
        print("\n" + "="*50)
        
        # Choix de la configuration
        newsletter, year, month = quick_modes()
        
        # Aperçu
        show_month_preview(year, month)
        
        # Confirmation
        print(f"\n❓ Voulez-vous continuer avec TLDR {newsletter.upper()} pour {calendar.month_name[month]} {year}?")
        confirm = input("Continuer? (o/N)> ").strip().lower()
        
        if confirm in ['o', 'oui', 'y', 'yes']:
            success = run_automation(newsletter, year, month)
            
            if success:
                print(f"\n🎉 MISSION ACCOMPLIE!")
                print(f"🎵 Vos résumés audio TLDR sont prêts!")
            else:
                print(f"\n😞 Il y a eu des problèmes...")
        else:
            print("\n👋 Annulé par l'utilisateur")
    
    except KeyboardInterrupt:
        print(f"\n👋 Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")

if __name__ == "__main__":
    main()