#!/usr/bin/env python3
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
