#!/usr/bin/env python3
"""
Script de réorganisation automatique du projet TLDR_robot
Réorganise les fichiers selon l'architecture recommandée
"""

import os
import shutil
from pathlib import Path
import json
from datetime import datetime

class ProjectReorganizer:
    """Réorganise automatiquement la structure du projet"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            project_root = Path.cwd()
        self.root = Path(project_root)
        
        # Structure cible
        self.target_structure = {
            'core/': {
                'description': '🤖 Modules principaux',
                'files': [
                    'tdlrscraper.py',
                    'notionintegrator.py', 
                    'aiprocessor.py',
                    'ttsgenerator.py'
                ]
            },
            'automation/': {
                'description': '🎯 Systèmes d\'orchestration',
                'files': [
                    'tdlrautomationsystem.py',
                    'monthly_automation.py',
                    'run_monthly.py'
                ]
            },
            'utils/': {
                'description': '🛠️ Utilitaires et helpers',
                'files': [
                    'smartdatehandler.py',
                    'config.py'
                ]
            },
            'tests/': {
                'description': '🧪 Tests et diagnostics',
                'files': [
                    'main.py'
                ]
            },
            'data/': {
                'description': '📊 Données et résultats',
                'subdirs': ['audio_summaries/', 'json_results/', 'logs/']
            },
            'config/': {
                'description': '🔧 Configuration',
                'files': [
                    'config.yaml',
                    '.env.example'
                ]
            },
            'docs/': {
                'description': '📚 Documentation',
                'files': []
            },
            'scripts/': {
                'description': '⚙️ Scripts utilitaires',
                'files': []
            }
        }
        
        print(f"🎯 Réorganisation du projet dans: {self.root}")
    
    def backup_current_state(self):
        """Crée une sauvegarde avant réorganisation"""
        backup_dir = self.root / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"💾 Création de la sauvegarde: {backup_dir}")
        
        # Copier tous les fichiers Python
        backup_dir.mkdir(exist_ok=True)
        
        for file_path in self.root.glob("*.py"):
            if file_path.is_file():
                shutil.copy2(file_path, backup_dir / file_path.name)
        
        # Copier les fichiers de config
        for file_path in self.root.glob("*.yaml"):
            if file_path.is_file():
                shutil.copy2(file_path, backup_dir / file_path.name)
        
        print(f"✅ Sauvegarde créée dans: {backup_dir}")
        return backup_dir
    
    def create_directory_structure(self):
        """Crée la structure de dossiers cible"""
        print("📁 Création de la structure de dossiers...")
        
        for dir_name, info in self.target_structure.items():
            dir_path = self.root / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"✅ {dir_name:<15} - {info['description']}")
            
            # Créer les sous-dossiers si nécessaire
            if 'subdirs' in info:
                for subdir in info['subdirs']:
                    (dir_path / subdir).mkdir(exist_ok=True)
                    print(f"   📂 {subdir}")
        
        # Dossiers spéciaux
        special_dirs = ['data/audio_summaries', 'data/json_results', 'data/logs']
        for special_dir in special_dirs:
            (self.root / special_dir).mkdir(parents=True, exist_ok=True)
    
    def move_files(self):
        """Déplace les fichiers selon la nouvelle structure"""
        print("\n🔄 Déplacement des fichiers...")
        
        moved_files = []
        
        for target_dir, info in self.target_structure.items():
            if 'files' not in info:
                continue
                
            for filename in info['files']:
                source_path = self.root / filename
                target_path = self.root / target_dir / filename
                
                if source_path.exists() and source_path.is_file():
                    # Déplacer le fichier
                    shutil.move(str(source_path), str(target_path))
                    moved_files.append((filename, target_dir))
                    print(f"📦 {filename:<25} → {target_dir}")
                else:
                    print(f"⚠️ {filename:<25} → Non trouvé")
        
        return moved_files
    
    def handle_data_directories(self):
        """Gère les dossiers de données existants"""
        print("\n📊 Gestion des dossiers de données...")
        
        # Déplacer audio_summaries si existe
        old_audio = self.root / "audio_summaries"
        new_audio = self.root / "data" / "audio_summaries"
        
        if old_audio.exists() and old_audio != new_audio:
            if new_audio.exists():
                # Fusionner les contenus
                for file_path in old_audio.glob("*"):
                    if file_path.is_file():
                        shutil.move(str(file_path), str(new_audio / file_path.name))
                old_audio.rmdir()
            else:
                shutil.move(str(old_audio), str(new_audio))
            print(f"📁 audio_summaries → data/audio_summaries")
        
        # Déplacer les fichiers JSON de résultats
        json_files = list(self.root.glob("tldr_*.json"))
        if json_files:
            json_dir = self.root / "data" / "json_results"
            json_dir.mkdir(exist_ok=True)
            
            for json_file in json_files:
                target = json_dir / json_file.name
                shutil.move(str(json_file), str(target))
                print(f"📊 {json_file.name} → data/json_results/")
    
    def create_init_files(self):
        """Crée les fichiers __init__.py pour faire des packages Python"""
        print("\n🐍 Création des packages Python...")
        
        packages = ['core', 'automation', 'utils', 'tests']
        
        for package in packages:
            init_file = self.root / package / "__init__.py"
            
            init_content = f'''"""
{self.target_structure[package + "/"]["description"]} Package
"""

__version__ = "1.0.0"
__author__ = "TLDR_robot"
'''
            
            with open(init_file, 'w', encoding='utf-8') as f:
                f.write(init_content)
            
            print(f"🐍 {package}/__init__.py créé")
    
    def create_main_entry_points(self):
        """Crée les points d'entrée principaux dans le dossier racine"""
        print("\n🚀 Création des points d'entrée...")
        
        # Point d'entrée principal
        main_entry = self.root / "tldr_automation.py"
        main_content = '''#!/usr/bin/env python3
"""
Point d'entrée principal pour TLDR_robot
"""

import sys
from pathlib import Path

# Ajouter les dossiers au PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core"))
sys.path.insert(0, str(project_root / "automation"))
sys.path.insert(0, str(project_root / "utils"))

from automation.run_monthly import main

if __name__ == "__main__":
    main()
'''
        
        with open(main_entry, 'w', encoding='utf-8') as f:
            f.write(main_content)
        
        print("🚀 tldr_automation.py créé (point d'entrée principal)")
        
        # Script de test rapide
        test_entry = self.root / "test_system.py"
        test_content = '''#!/usr/bin/env python3
"""
Test rapide du système TLDR
"""

import sys
from pathlib import Path

# Ajouter les dossiers au PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tests"))

from tests.main import diagnostic_complet

if __name__ == "__main__":
    diagnostic_complet()
'''
        
        with open(test_entry, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print("🧪 test_system.py créé (tests rapides)")
    
    def update_imports(self):
        """Met à jour les imports dans les fichiers déplacés"""
        print("\n🔧 Mise à jour des imports...")
        
        # Mapping des nouveaux chemins
        import_updates = {
            'core/': {
                'from tdlrscraper import': 'from core.tdlrscraper import',
                'from notionintegrator import': 'from core.notionintegrator import',
                'from aiprocessor import': 'from core.aiprocessor import',
                'from ttsgenerator import': 'from core.ttsgenerator import'
            },
            'automation/': {
                'from tdlrscraper import': 'from core.tdlrscraper import',
                'from notionintegrator import': 'from core.notionintegrator import',
                'from aiprocessor import': 'from core.aiprocessor import',
                'from ttsgenerator import': 'from core.ttsgenerator import',
                'from smartdatehandler import': 'from utils.smartdatehandler import'
            },
            'utils/': {},
            'tests/': {
                'from tdlrscraper import': 'from core.tdlrscraper import',
                'from smartdatehandler import': 'from utils.smartdatehandler import'
            }
        }
        
        for folder, updates in import_updates.items():
            folder_path = self.root / folder
            
            for py_file in folder_path.glob("*.py"):
                if py_file.name == "__init__.py":
                    continue
                
                # Lire le contenu
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Appliquer les mises à jour
                    original_content = content
                    for old_import, new_import in updates.items():
                        content = content.replace(old_import, new_import)
                    
                    # Sauvegarder si changements
                    if content != original_content:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"🔧 Imports mis à jour dans: {py_file.relative_to(self.root)}")
                
                except Exception as e:
                    print(f"⚠️ Erreur mise à jour imports {py_file}: {e}")
    
    def create_requirements_dev(self):
        """Crée un requirements-dev.txt pour le développement"""
        dev_requirements = """# requirements-dev.txt
# Dépendances de développement pour TLDR_robot

# === PRODUCTION REQUIREMENTS ===
-r requirements.txt

# === DEVELOPMENT TOOLS ===
pytest>=7.0.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.950

# === DOCUMENTATION ===
sphinx>=4.0.0
sphinx-rtd-theme>=1.0.0

# === TESTING ===
coverage>=6.0.0
pytest-cov>=3.0.0
pytest-mock>=3.7.0

# === UTILITIES ===
ipython>=8.0.0
jupyter>=1.0.0
"""
        
        dev_req_path = self.root / "requirements-dev.txt"
        with open(dev_req_path, 'w', encoding='utf-8') as f:
            f.write(dev_requirements)
        
        print("📝 requirements-dev.txt créé")
    
    def create_setup_script(self):
        """Crée un script d'installation automatique"""
        setup_script = self.root / "setup.py"
        setup_content = '''#!/usr/bin/env python3
"""
Setup script pour TLDR_robot
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="tldr-robot",
    version="1.0.0",
    author="yahyaghazi",
    description="Automatisation de veille technologique TLDR avec IA locale",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "tldr-automation=tldr_automation:main",
            "tldr-test=test_system:main",
        ],
    },
)
'''
        
        with open(setup_script, 'w', encoding='utf-8') as f:
            f.write(setup_content)
        
        print("⚙️ setup.py créé")
    
    def generate_report(self, moved_files, backup_dir):
        """Génère un rapport de la réorganisation"""
        report = {
            "reorganization_date": datetime.now().isoformat(),
            "backup_location": str(backup_dir),
            "moved_files": moved_files,
            "new_structure": dict(self.target_structure),
            "status": "completed"
        }
        
        report_path = self.root / "reorganization_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report_path
    
    def reorganize(self):
        """Lance la réorganisation complète"""
        print("🚀 DÉBUT DE LA RÉORGANISATION TLDR_robot")
        print("=" * 60)
        
        try:
            # 1. Sauvegarde
            backup_dir = self.backup_current_state()
            
            # 2. Création de la structure
            self.create_directory_structure()
            
            # 3. Déplacement des fichiers
            moved_files = self.move_files()
            
            # 4. Gestion des données
            self.handle_data_directories()
            
            # 5. Création des packages Python
            self.create_init_files()
            
            # 6. Points d'entrée
            self.create_main_entry_points()
            
            # 7. Mise à jour des imports
            self.update_imports()
            
            # 8. Fichiers de développement
            self.create_requirements_dev()
            self.create_setup_script()
            
            # 9. Rapport final
            report_path = self.generate_report(moved_files, backup_dir)
            
            print("\n" + "=" * 60)
            print("✅ RÉORGANISATION TERMINÉE AVEC SUCCÈS!")
            print("=" * 60)
            print(f"📊 {len(moved_files)} fichiers déplacés")
            print(f"💾 Sauvegarde: {backup_dir}")
            print(f"📋 Rapport: {report_path}")
            
            print("\n🚀 NOUVEAUX POINTS D'ENTRÉE:")
            print("   python tldr_automation.py    # Interface principale")
            print("   python test_system.py        # Tests du système")
            
            print("\n📁 NOUVELLE STRUCTURE:")
            for dir_name, info in self.target_structure.items():
                print(f"   {dir_name:<15} - {info['description']}")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERREUR LORS DE LA RÉORGANISATION: {e}")
            print(f"💾 Restaurez depuis: {backup_dir}")
            return False


def main():
    """Point d'entrée principal"""
    print("🤖 TLDR_robot - Script de Réorganisation")
    print("Réorganise automatiquement votre projet selon l'architecture recommandée")
    
    # Détection automatique du dossier
    current_dir = Path.cwd()
    print(f"\n📁 Dossier actuel: {current_dir}")
    
    # Vérifier qu'on est dans le bon dossier
    required_files = ['tdlrscraper.py', 'aiprocessor.py', 'requirements.txt']
    missing_files = [f for f in required_files if not (current_dir / f).exists()]
    
    if missing_files:
        print(f"❌ Fichiers manquants: {missing_files}")
        print("❌ Assurez-vous d'être dans le dossier du projet TLDR_robot")
        return
    
    # Confirmation
    print(f"\n⚠️ Cette opération va réorganiser tous vos fichiers.")
    print(f"⚠️ Une sauvegarde sera créée automatiquement.")
    
    confirm = input("\n❓ Continuer la réorganisation? (o/N): ").strip().lower()
    
    if confirm in ['o', 'oui', 'y', 'yes']:
        reorganizer = ProjectReorganizer(current_dir)
        success = reorganizer.reorganize()
        
        if success:
            print(f"\n🎉 Votre projet TLDR_robot est maintenant parfaitement organisé!")
            print(f"🚀 Testez avec: python test_system.py")
        else:
            print(f"\n😞 La réorganisation a échoué. Consultez les logs ci-dessus.")
    else:
        print("👋 Réorganisation annulée")


if __name__ == "__main__":
    main()
