import requests
import ollama
from typing import List, Dict, Any
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIProcessor:
    """Niveau 3 - Résumé par IA: Traitement avec LLM local Ollama"""
    
    def __init__(self, model: str = 'nous-hermes2:latest', base_url: str = 'http://localhost:11434'):
        self.model = model
        self.base_url = base_url
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
        """Envoie une requête à Ollama"""
        try:
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
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama query error: {e}")
            return "Erreur lors de la requête LLM local"
    
    def categorize_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Catégorise les articles avec Ollama"""
        categorized_articles = []
        
        # Optimisation : traitement par lots pour Ollama
        if len(articles) > 3:
            return self._batch_categorize_articles(articles)
        
        for article in articles:
            try:
                prompt = f"""Tu es un expert en veille technologique. Analyse cet article et assigne-lui exactement 2-3 catégories pertinentes.

Article à analyser:
Titre: {article['titre']}
Résumé: {article['resume_tldr']}

Catégories disponibles: SEO, Marketing, Product, AI/IA, B2B, SaaS, Strategy, Analytics, Social Media, Content, E-commerce, Growth, Tech, Design, UX, Data, Security, DevOps, Mobile, Web3, Blockchain

Instructions:
- Choisis 2-3 catégories maximum
- Base-toi sur le contenu réel de l'article
- Réponds UNIQUEMENT par la liste des catégories séparées par des virgules
- Exemple de réponse: Marketing, AI/IA, Strategy

Catégories:"""
                
                result = self._query_ollama(prompt, max_tokens=50)
                categories = [cat.strip() for cat in result.split(',') if cat.strip()]
                
                # Validation et nettoyage
                valid_categories = [
                    "SEO", "Marketing", "Product", "AI/IA", "B2B", "SaaS", 
                    "Strategy", "Analytics", "Social Media", "Content", 
                    "E-commerce", "Growth", "Tech", "Design", "UX", 
                    "Data", "Security", "DevOps", "Mobile", "Web3", "Blockchain"
                ]
                
                filtered_categories = [cat for cat in categories if cat in valid_categories]
                if not filtered_categories:
                    filtered_categories = ["Tech"]  # Catégorie par défaut
                
                article['categories_ia'] = filtered_categories[:3]  # Max 3 catégories
                categorized_articles.append(article)
                
                logger.info(f"Article categorized: {article['titre'][:50]}... -> {filtered_categories}")
                
            except Exception as e:
                logger.error(f"Error categorizing article: {e}")
                article['categories_ia'] = ["Tech"]
                categorized_articles.append(article)
        
        return categorized_articles
    
    def _batch_categorize_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Catégorisation en lot pour optimiser les performances avec Ollama"""
        try:
            articles_text = "\n\n".join([
                f"#{i+1}. Titre: {article['titre']}\n   Résumé: {article['resume_tldr']}"
                for i, article in enumerate(articles)
            ])
            
            prompt = f"""Tu es un expert en veille technologique. Catégorise ces {len(articles)} articles.

Articles à analyser:
{articles_text}

Catégories disponibles: SEO, Marketing, Product, AI/IA, B2B, SaaS, Strategy, Analytics, Social Media, Content, E-commerce, Growth, Tech, Design, UX, Data, Security, DevOps, Mobile, Web3, Blockchain

Instructions:
- Assigne 2-3 catégories à chaque article
- Format de réponse EXACTEMENT comme ceci:
#1: Marketing, AI/IA
#2: Product, UX, Design
#3: SEO, Content

Réponse:"""
            
            result = self._query_ollama(prompt, max_tokens=200)
            
            # Parser la réponse
            lines = result.strip().split('\n')
            for i, article in enumerate(articles):
                try:
                    # Chercher la ligne correspondante
                    line = next((l for l in lines if l.startswith(f"#{i+1}:")), None)
                    if line:
                        categories_str = line.split(':', 1)[1].strip()
                        categories = [cat.strip() for cat in categories_str.split(',')]
                        article['categories_ia'] = categories[:3]
                    else:
                        article['categories_ia'] = ["Tech"]
                except:
                    article['categories_ia'] = ["Tech"]
            
            return articles
            
        except Exception as e:
            logger.error(f"Batch categorization error: {e}")
            # Fallback : catégorisation individuelle
            return self.categorize_articles(articles)
    
    def synthesize_articles(self, articles: List[Dict[str, Any]]) -> str:
        """Synthétise tous les articles en un résumé global"""
        try:
            articles_text = "\n\n".join([
                f"• {article['titre']}\n  Catégories: {', '.join(article.get('categories_ia', []))}\n  Résumé: {article['resume_tldr']}"
                for article in articles
            ])
            
            prompt = f"""Tu es un analyste en veille technologique. Crée un résumé exécutif professionnel de ces {len(articles)} articles.

Articles de veille:
{articles_text}

Instructions:
1. **Identifie les 3-5 tendances principales** qui émergent de ces articles
2. **Synthétise les insights clés** en 2-3 paragraphes structurés
3. **Propose 2-3 recommandations actionables** concrètes

Format attendu:
## 🔍 Tendances Principales
[Liste des tendances identifiées]

## 📊 Insights Clés  
[Synthèse en 2-3 paragraphes]

## 💡 Recommandations
[2-3 actions concrètes à entreprendre]

Ton de voix: Professionnel, synthétique, orienté action. Maximum 400 mots.

Résumé exécutif:"""
            
            synthesis = self._query_ollama(prompt, max_tokens=500)
            logger.info("Articles synthesis completed with local LLM")
            return synthesis
            
        except Exception as e:
            logger.error(f"Error synthesizing articles: {e}")
            return "Erreur lors de la synthèse des articles avec le LLM local."
