# TLDR_robot

TLDR_robot est un système d’automatisation avancé pour la collecte, l’analyse, la traduction et la synthèse vocale d’articles issus des newsletters TLDR (Tech, AI, etc.). Il intègre des modules de scraping intelligent, de gestion de dates, de traduction automatique (DeepL), de génération audio, et de visualisation via un dashboard Streamlit.

## Fonctionnalités principales

- **Scraping intelligent** des newsletters TLDR (Tech, AI, etc.) avec gestion des jours ouvrés et des jours fériés.
- **Traduction automatique** des articles (DeepL, multilingue).
- **Synthèse vocale** : génération de fichiers audio à partir des résumés d’articles.
- **Automatisation mensuelle** : scripts pour collecter, stocker et traiter les newsletters sur une période donnée.
- **Stockage** dans une base SQLite, avec outils de migration et de visualisation.
- **Dashboard interactif** via Streamlit pour explorer les articles et les résumés audio.
- **Tests unitaires** pour la robustesse du scraping, de l’automatisation et de la migration de base de données.

## Structure du projet

```
TLDR_robot/
│
├── core/                  # Modules principaux (scraping, intégration, TTS, etc.)
│   ├── tdlrscraper.py
│   ├── aiprocessor.py
│   ├── sqlite_integrator.py
│   └── ...
│
├── automation/            # Scripts d’automatisation mensuelle
│   ├── monthly_automation.py
│   └── run_monthly.py
│
├── utils/                 # Utilitaires (gestion de dates, etc.)
│   └── smartdatehandler.py
│
├── data/                  # Données persistantes
│   ├── tldr_database.db
│   ├── audio_summaries/
│   └── ...
│
├── audio_summaries/       # Fichiers audio générés
│
├── config/                # Fichiers de configuration (YAML)
│
├── scripts/               # Scripts divers
│
├── run_dashboard.py       # Lancement du dashboard Streamlit
├── streamlit_dashboard.py # Code du dashboard
├── requirements.txt       # Dépendances Python
├── setup.py               # Installation du package
└── README.md              # Ce fichier
```

## Installation

1. **Cloner le dépôt** :
   ```sh
   git clone <url_du_repo>
   cd TLDR_robot
   ```

2. **Créer un environnement virtuel** (optionnel mais recommandé) :
   ```sh
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Installer les dépendances** :
   ```sh
   pip install -r requirements.txt
   ```

4. **Configurer les clés API** (ex : DeepL) dans `config/config.yaml` ou via variables d’environnement.

## Utilisation

### 1. Scraper les articles TLDR

Exemple d’utilisation du scraper :
```python
from core.tdlrscraper import TLDRScraper

scraper = TLDRScraper(newsletter_type="tech", target_language="FR", deepl_api_key="VOTRE_CLE_DEEPL")
articles = scraper.scrape_articles()
```

### 2. Automatisation mensuelle

Lancer l’automatisation pour collecter et stocker les newsletters :
```sh
python automation/run_monthly.py
```

### 3. Générer des résumés audio

Les fichiers audio sont générés automatiquement et stockés dans `audio_summaries/` ou `data/audio_summaries/`.

### 4. Visualiser via le dashboard

Lancer le dashboard Streamlit :
```sh
streamlit run streamlit_dashboard.py
```

### 5. Visualiser la base SQLite

Utiliser le script dédié :
```sh
python sqlite_viewer.py
```

## Configuration

- Modifier `config/config.yaml` pour :
  - Les clés API (DeepL, etc.)
  - Les paramètres de scraping (type de newsletter, langue, etc.)
  - Les chemins de stockage


## Dépendances principales

- `requests`, `beautifulsoup4` : scraping web
- `deepl` : traduction automatique
- `streamlit` : dashboard interactif
- `sqlite3` : base de données
- `gtts` ou équivalent : synthèse vocale
- `PyYAML` : gestion de la configuration

## Personnalisation

- Ajouter de nouveaux types de newsletters en modifiant les paramètres du scraper.
- Adapter les scripts d’automatisation pour d’autres périodicités ou sources.
- Étendre la traduction à d’autres langues via DeepL.

## Auteurs

- Yahya GHAZI

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus d’informations.