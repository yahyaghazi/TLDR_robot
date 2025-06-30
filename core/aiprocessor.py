import requests
import ollama
from typing import List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIProcessor:
    """Niveau 3 - Résumé par IA: Traitement avec LLM local Ollama (SÉCURISÉ)"""
    
    def __init__(self, model: str = 'nous-hermes2:latest', base_url: str = 'http://localhost:11434', max_articles_per_batch=15):
        self.model = model
        self.base_url = base_url
        self.max_articles_per_batch = max_articles_per_batch  
        self._verify_ollama_connection()
        
        logger.info(f"AI Processor initialized with Ollama using model {self.model}")
    
    def _verify_ollama_connection(self):
        """Vérifie la connexion à Ollama et le modèle"""
        try:
            # Vérifier si Ollama est accessible
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model not in model_names:
                    logger.warning(f"Model {self.model} not found. Available models: {model_names}")
                    logger.info("To install the model, run: ollama pull nous-hermes2:latest")
                else:
                    logger.info(f"✅ Ollama connected successfully with {self.model}")
            else:
                logger.error("❌ Cannot connect to Ollama. Make sure it's running: ollama serve")
        except Exception as e:
            logger.error(f"❌ Ollama connection error: {e}")
            logger.info("Install Ollama: https://ollama.ai/ and run: ollama serve")
    
    def _query_ollama(self, prompt: str, max_tokens: int = 500) -> str:
        """Envoie une requête à Ollama avec protection"""
        try:
            
            if len(prompt) > 8000:  # Limite de sécurité
                logger.warning(f"Prompt trop long ({len(prompt)} chars), troncature à 8000")
                prompt = prompt[:8000] + "..."
            
            logger.info(f"Envoi prompt à Ollama ({len(prompt)} caractères)")
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                options={
                    'num_predict': max_tokens,
                    'temperature': 0.3,
                    'top_p': 0.9,
                }
            )
            
            result = response['message']['content']
            logger.info(f"Réponse Ollama reçue ({len(result)} caractères)")
            return result
            
        except Exception as e:
            logger.error(f"Ollama query error: {e}")
            return "Erreur lors de la requête LLM local"
    
    def categorize_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Catégorise les articles avec Ollama (SÉCURISÉ)"""

        if len(articles) > self.max_articles_per_batch:
            logger.warning(f"Trop d'articles ({len(articles)}), limitation à {self.max_articles_per_batch}")
            articles = articles[:self.max_articles_per_batch]
        
        if len(articles) == 0:
            logger.warning("Aucun article à catégoriser")
            return []
        
        categorized_articles = []

        if len(articles) > 5:
            logger.info(f"Traitement par lots de {len(articles)} articles")
            return self._batch_categorize_articles(articles)
        else:
            logger.info(f"Traitement individuel de {len(articles)} articles")
        
        # Traitement individuel pour les petits nombres
        for i, article in enumerate(articles, 1):
            try:
                logger.info(f"Catégorisation article {i}/{len(articles)}")

                prompt = f"""Catégorise cet article tech en 2-3 mots max:

Titre: {article['titre'][:100]}
Résumé: {article.get('resume_tldr', '')[:200]}

Catégories: AI/IA, Tech, Data, Security, Mobile, Web3, Product, Dev, Design, Business

Réponse (juste les catégories):"""
                
                result = self._query_ollama(prompt, max_tokens=30)
                categories = [cat.strip() for cat in result.split(',') if cat.strip()]
                
                # Validation et nettoyage
                valid_categories = [
                    "AI/IA", "Tech", "Data", "Security", "DevOps", 
                    "Mobile", "Web3", "Blockchain", "Product", "Dev", "Design", "Business"
                ]
                
                filtered_categories = [cat for cat in categories if cat in valid_categories]
                if not filtered_categories:
                    filtered_categories = ["Tech"]  # Catégorie par défaut
                
                article['categories_ia'] = filtered_categories[:3]  # Max 3 catégories
                categorized_articles.append(article)
                
                logger.info(f"✅ Article {i} catégorisé: {filtered_categories}")
                
            except Exception as e:
                logger.error(f"❌ Erreur catégorisation article {i}: {e}")
                article['categories_ia'] = ["Tech"]
                categorized_articles.append(article)
        
        return categorized_articles
    
    def _batch_categorize_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Catégorisation en lot pour optimiser les performances avec Ollama (SÉCURISÉ)"""
        try:
            
            if len(articles) > self.max_articles_per_batch:
                articles = articles[:self.max_articles_per_batch]
                logger.info(f"Limitation à {len(articles)} articles pour le batch")

            articles_list = []
            for i, article in enumerate(articles):
                # Troncature pour éviter les prompts trop longs
                title = article['titre'][:80]
                summary = article.get('resume_tldr', '')[:100]
                articles_list.append(f"#{i+1}. {title}")
                if summary:
                    articles_list.append(f"    {summary}")
            
            articles_text = "\n".join(articles_list)

            prompt = f"""Catégorise ces {len(articles)} articles tech.

{articles_text}

Catégories: AI/IA, Tech, Data, Security, Mobile, Web3, Product, Dev, Design, Business

Format réponse exacte:
#1: Tech, AI/IA
#2: Product, Design
...

Réponse:"""

            if len(prompt) > 6000:
                # Réduire le nombre d'articles
                reduced_count = min(8, len(articles))
                logger.warning(f"Prompt trop long, réduction à {reduced_count} articles")
                return self._batch_categorize_articles(articles[:reduced_count])
            
            result = self._query_ollama(prompt, max_tokens=150)
            
            # Parser la réponse
            lines = result.strip().split('\n')
            for i, article in enumerate(articles):
                try:
                    # Chercher la ligne correspondante
                    pattern = f"#{i+1}:"
                    line = next((l for l in lines if l.startswith(pattern)), None)
                    if line:
                        categories_str = line.split(':', 1)[1].strip()
                        categories = [cat.strip() for cat in categories_str.split(',')]
                        article['categories_ia'] = categories[:3]
                        logger.info(f"✅ Article {i+1} catégorisé: {categories}")
                    else:
                        article['categories_ia'] = ["Tech"]
                        logger.warning(f"⚠️ Article {i+1}: catégorie par défaut")
                except Exception as e:
                    logger.error(f"❌ Erreur parsing article {i+1}: {e}")
                    article['categories_ia'] = ["Tech"]
            
            return articles
            
        except Exception as e:
            logger.error(f"Batch categorization error: {e}")
            # Fallback : catégorisation individuelle avec limite
            limited_articles = articles[:5]  # Maximum 5 en individuel
            logger.info(f"Fallback: traitement individuel de {len(limited_articles)} articles")
            return self.categorize_articles(limited_articles)
    
    def synthesize_articles(self, articles: List[Dict[str, Any]]) -> str:
        """Synthétise tous les articles en un résumé global (SÉCURISÉ)"""
        try:
            
            if len(articles) > 15:
                logger.warning(f"Trop d'articles pour synthèse ({len(articles)}), limitation à 15")
                articles = articles[:15]
            
            if len(articles) == 0:
                return "Aucun article à synthétiser."

            articles_summary = []
            for i, article in enumerate(articles[:10], 1):  # Max 10 pour synthèse
                title = article['titre'][:60]  # Titre tronqué
                summary = article.get('resume_tldr', '')[:80]  # Résumé tronqué
                categories = ', '.join(article.get('categories_ia', ['Tech'])[:2])  # Max 2 catégories
                
                articles_summary.append(f"{i}. {title}")
                if summary:
                    articles_summary.append(f"   {summary}")
                articles_summary.append(f"   [{categories}]")
            
            articles_text = "\n".join(articles_summary)

            prompt = f"""Résumé exécutif tech du jour ({len(articles)} articles):

{articles_text}

Crée un résumé en 3 parties courtes:

🔍 TENDANCES (2-3 points):
📊 INSIGHTS (1 paragraphe):  
💡 ACTIONS (2 recommandations):

Max 200 mots total."""

            if len(prompt) > 4000:
                # Réduction drastique si trop long
                articles_mini = []
                for article in articles[:5]:
                    articles_mini.append(f"• {article['titre'][:40]}")
                
                prompt = f"""Résumé tech ({len(articles)} articles):
{chr(10).join(articles_mini)}

3 tendances + 2 actions en 100 mots max."""
            
            logger.info(f"Synthèse de {len(articles)} articles (prompt: {len(prompt)} chars)")
            synthesis = self._query_ollama(prompt, max_tokens=300)
            
            if not synthesis or len(synthesis) < 50:
                # Fallback simple
                synthesis = f"""🔍 TENDANCES: {len(articles)} articles tech analysés
📊 INSIGHTS: Activité tech soutenue avec focus sur l'IA et les nouvelles technologies  
💡 ACTIONS: 1) Surveiller les évolutions IA 2) Evaluer les nouvelles solutions tech"""
            
            logger.info("✅ Synthèse générée avec succès")
            return synthesis
            
        except Exception as e:
            logger.error(f"❌ Erreur synthèse: {e}")
            # Fallback minimal
            return f"""🔍 TENDANCES: {len(articles)} articles tech du jour
📊 INSIGHTS: Veille technologique automatisée
💡 ACTIONS: Consulter les articles individuels pour plus de détails"""