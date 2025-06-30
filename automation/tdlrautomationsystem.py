import json
import logging
from datetime import datetime
from typing import Dict, Any

from core.tdlrscraper import TLDRScraper
from core.notionintegrator import NotionIntegrator
from core.aiprocessor import AIProcessor
from core.ttsgenerator import TTSGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TLDRAutomationSystem:
    """Système principal d'automatisation avec Ollama uniquement"""
    
    def __init__(self, config: Dict[str, str]):
        self.scraper = TLDRScraper(config.get('newsletter_type', 'marketing'))
        self.notion = NotionIntegrator(config['notion_token'], config['notion_database_id'])
        
        # Configuration du processeur IA avec Ollama
        self.ai_processor = AIProcessor(
            model=config.get('ollama_model', 'nous-hermes2:latest'),
            base_url=config.get('ollama_base_url', 'http://localhost:11434')
        )
        
        self.tts = TTSGenerator(config.get('audio_output_dir', 'audio_output'))
    
    def run_daily_automation(self) -> Dict[str, Any]:
        """Lance le processus complet d'automatisation"""
        logger.info("Starting daily TLDR automation")
        
        results = {
            'date': datetime.now().isoformat(),
            'articles_extracted': 0,
            'articles_stored': 0,
            'synthesis': '',
            'audio_file': None,
            'errors': []
        }
        
        try:
            # Niveau 1: Extraction
            articles = self.scraper.scrape_articles()
            results['articles_extracted'] = len(articles)
            
            if not articles:
                results['errors'].append("No articles extracted")
                return results
            
            # Niveau 3: Traitement IA (avant stockage pour enrichir les données)
            categorized_articles = self.ai_processor.categorize_articles(articles)
            synthesis = self.ai_processor.synthesize_articles(categorized_articles)
            results['synthesis'] = synthesis
            
            # Niveau 2: Stockage Notion
            page_ids = self.notion.bulk_add_articles(categorized_articles)
            results['articles_stored'] = len(page_ids)
            
            # Niveau 4: Génération audio
            audio_file = self.tts.generate_audio_summary(synthesis, categorized_articles)
            results['audio_file'] = audio_file
            
            logger.info("Daily automation completed successfully")
            
        except Exception as e:
            error_msg = f"Automation error: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Sauvegarde les résultats en JSON"""
        if not filename:
            filename = f"tldr_results_{datetime.now().strftime('%Y%m%d')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to {filename}")
