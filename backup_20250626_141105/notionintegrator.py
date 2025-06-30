import logging
from typing import List, Dict, Any
from notion_client import Client

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionIntegrator:
    """Niveau 2 - Intégration: Stockage dans Notion"""
    
    def __init__(self, token: str, database_id: str):
        self.notion = Client(auth=token)
        self.database_id = database_id
    
    def create_database_if_not_exists(self):
        """Crée la base de données Notion si elle n'existe pas"""
        try:
            # Vérification de l'existence de la base
            self.notion.databases.retrieve(database_id=self.database_id)
            logger.info("Database exists")
        except:
            logger.warning("Database creation should be done manually in Notion")
    
    def add_article_to_notion(self, article: Dict[str, Any]) -> str:
        """Ajoute un article à la base Notion"""
        try:
            properties = {
                "Titre": {
                    "title": [
                        {
                            "text": {
                                "content": article['titre'][:100]  # Limitation Notion
                            }
                        }
                    ]
                },
                "URL": {
                    "url": article['url']
                },
                "État": {
                    "select": {
                        "name": "Pas commencé"
                    }
                },
                "Résumé": {
                    "rich_text": [
                        {
                            "text": {
                                "content": article['resume_tldr']
                            }
                        }
                    ]
                }
            }
            
            if article.get('duree_lecture'):
                properties["Durée"] = {
                    "rich_text": [
                        {
                            "text": {
                                "content": article['duree_lecture']
                            }
                        }
                    ]
                }
            
            response = self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"Article added to Notion: {article['titre']}")
            return response['id']
            
        except Exception as e:
            logger.error(f"Error adding article to Notion: {e}")
            return None
    
    def bulk_add_articles(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Ajoute plusieurs articles en lot"""
        page_ids = []
        for article in articles:
            page_id = self.add_article_to_notion(article)
            if page_id:
                page_ids.append(page_id)
        return page_ids
