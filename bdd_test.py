import requests
import logging
from typing import Dict, Optional, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotionIntegrator:
    def __init__(self, token: str, database_id: str):
        self.token = token
        self.database_id = database_id
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.properties_cache = None
    
    def get_database_properties(self) -> Optional[Dict]:
        """Récupère les propriétés de la base de données"""
        if self.properties_cache:
            return self.properties_cache
            
        url = f"https://api.notion.com/v1/databases/{self.database_id}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            database_info = response.json()
            self.properties_cache = database_info.get('properties', {})
            
            logger.info(f"Propriétés récupérées: {list(self.properties_cache.keys())}")
            return self.properties_cache
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération des propriétés: {e}")
            return None
    
    def format_value_for_notion(self, value: Any, property_type: str, property_name: str = "") -> Optional[Dict]:
        """Formate une valeur selon le type de propriété Notion"""
        
        if not value:
            return None
        
        if property_type == 'title':
            return {
                "title": [
                    {
                        "text": {
                            "content": str(value)
                        }
                    }
                ]
            }
        
        elif property_type == 'rich_text':
            return {
                "rich_text": [
                    {
                        "text": {
                            "content": str(value)
                        }
                    }
                ]
            }
        
        elif property_type == 'url':
            return {"url": str(value)}
        
        elif property_type == 'select':
            return {"select": {"name": str(value)}}
        
        elif property_type == 'multi_select':
            # Si c'est une liste, on l'utilise directement, sinon on split par virgules
            if isinstance(value, list):
                options = value
            else:
                options = [opt.strip() for opt in str(value).split(',')]
            
            return {
                "multi_select": [{"name": opt} for opt in options if opt]
            }
                        
        elif property_type == 'number':
            try:
                return {"number": float(value)}
            except (ValueError, TypeError):
                return None
        
        elif property_type == 'checkbox':
            return {"checkbox": bool(value)}
        
        else:
            logger.warning(f"Type de propriété non supporté: {property_type}")
            return None
    
    def add_article_to_notion(self, article: Dict) -> bool:
        """Ajoute un article à la base de données Notion"""
        
        properties = self.get_database_properties()
        if not properties:
            logger.error("Impossible de récupérer les propriétés de la base")
            return False
        
        notion_properties = {}
        
        # Mapping direct basé sur les noms exacts des propriétés
        property_mapping = {
            'titre': 'titre',
            'url': 'url', 
            'resume_tldr': 'resume_tldr',
            'etat': 'etat',
            'categories_ia': 'categories_ia'
            }
        
        print(f"✅ Article: {article}")
        print(f"✅ Mapping: {property_mapping}")
        
        for article_key, notion_key in property_mapping.items():
            if article_key in article and notion_key in properties:
                property_type = properties[notion_key]['type']
                
                formatted_value = self.format_value_for_notion(
                    article[article_key], 
                    property_type,
                    notion_key
                )
                
                if formatted_value:
                    notion_properties[notion_key] = formatted_value
                    logger.info(f"✅ Mappé '{article_key}' -> '{notion_key}' ({property_type})")
                else:
                    logger.warning(f"⚠️  Impossible de formater '{article_key}' pour '{notion_key}' ({property_type})")
        
        if not notion_properties:
            logger.error("Aucune propriété valide trouvée pour l'article")
            return False
        
        # Préparer les données pour l'API Notion
        data = {
            "parent": {"database_id": self.database_id},
            "properties": notion_properties
        }
        
        logger.info(f"Envoi des données: {list(notion_properties.keys())}")
        
        try:
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=self.headers,
                json=data
            )
            
            if response.status_code == 200:
                logger.info("✅ Article ajouté avec succès à Notion")
                return True
            else:
                error_info = response.json()
                error_msg = error_info.get('message', 'Erreur inconnue')
                logger.error(f"❌ Erreur API Notion: {error_msg}")
                logger.error(f"Détails: {error_info}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur de requête: {e}")
            return False

# Test avec vos données exactes
if __name__ == "__main__":
    
    # Test de connexion
    notion = NotionIntegrator(
        token="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", 
        database_id="21e7d425746b80a0a867e9adfbcbff26"
    )
    
    # Article de test adapté à votre structure
    test_article = {
        'titre': 'Test de connexion TLDR Robot',
        'url': 'https://example.com',
        'resume_tldr': 'Article de test pour vérifier la connexion avec la base Notion',
        'etat': 'Test',
        'categories_ia': ['Test', 'Connexion']
        }
    
    print("🚀 Test d'ajout d'article à Notion...")
    print(f"📊 Base de données: TLDR Articles")
    print(f"🔑 Database ID: {notion.database_id}")
    
    if notion.add_article_to_notion(test_article):
        print("🎉 SUCCESS: Article ajouté avec succès à Notion!")
    else:
        print("💥 FAILED: Erreur lors de l'ajout de l'article à Notion.")
