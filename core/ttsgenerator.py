import pyttsx3
from pathlib import Path
from typing import List, Dict, Any
import logging
import re
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSGenerator:
    """Niveau 4 - Génération audio avec TTS"""
    
    def __init__(self, output_dir: str = "audio_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.engine = pyttsx3.init()
        self._configure_voice()
    
    def _configure_voice(self):
        """Configure la voix TTS"""
        voices = self.engine.getProperty('voices')
        # Recherche d'une voix française si disponible
        for voice in voices:
            if 'french' in voice.name.lower() or 'fr' in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        self.engine.setProperty('rate', 180)  # Vitesse de lecture
        self.engine.setProperty('volume', 0.9)  # Volume
    
    def generate_audio_summary(self, synthesis: str, articles: List[Dict[str, Any]]) -> str:
        """Génère un fichier audio du résumé"""
        try:
            # Prépare le texte complet
            date_str = datetime.now().strftime("%d %B %Y")
            intro = f"Résumé de veille technologique du {date_str}."
            
            full_text = f"{intro}\n\n{synthesis}"
            
            # Génère le fichier audio
            filename = f"veille_tldr_{datetime.now().strftime('%Y%m%d')}.wav"
            filepath = self.output_dir / filename
            
            self.engine.save_to_file(full_text, str(filepath))
            self.engine.runAndWait()
            
            logger.info(f"Audio file generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            return None
    
    def generate_individual_article_audio(self, article: Dict[str, Any]) -> str:
        """Génère un audio pour un article individuel"""
        try:
            text = f"Article: {article['titre']}. Résumé: {article['resume_tldr']}"
            
            safe_title = re.sub(r'[^\w\s-]', '', article['titre'][:50])
            filename = f"article_{safe_title.replace(' ', '_')}.wav"
            filepath = self.output_dir / filename
            
            self.engine.save_to_file(text, str(filepath))
            self.engine.runAndWait()
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error generating individual audio: {e}")
            return None
