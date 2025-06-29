from gtts import gTTS
import os
from io import BytesIO

def synthesize_text_to_file(text, output_file="audio_output.mp3", lang='fr', slow=False):
    """
    Synthétise du texte en français et sauvegarde dans un fichier
    
    Args:
        text (str): Texte à synthétiser
        output_file (str): Nom du fichier de sortie
        lang (str): Langue ('fr' pour français)
        slow (bool): Vitesse lente si True
    """
    try:
        print(f"🎤 Synthèse vocale en cours...")
        
        # Créer l'objet gTTS
        tts = gTTS(text=text, lang=lang, slow=slow)
        
        # Sauvegarder dans un fichier
        tts.save(output_file)
        
        abs_path = os.path.abspath(output_file)
        print(f"✅ Fichier audio généré : {abs_path}")
        
        return abs_path
        
    except Exception as e:
        print(f"❌ Erreur lors de la synthèse : {e}")
        return None

        
    except Exception as e:
        print(f"❌ Erreur : {e}")

def main():
    """Fonction principale avec ton texte"""
    
    # Ton texte long
    text_long = """Les centres de données géants et les progrès dans l'IA robotique sont des tendances importantes.
    L'utilisation d'IA dans la création de logiciels de productivité et le développement de modèles visuels sont en pleine expansion.
    Les discussions sur les questions juridiques et éthiques liées à l'IA continuent de se développer.
    
    INSIGHTS : Les tendances actuelles dans le secteur technologique montrent que l'utilisation d'IA est en plein essor, 
    avec des progrès significatifs dans la conception de centres de données géants et des modèles visuels avancés. 
    Cependant, ces progrès sont accompagnés de questions juridiques et éthiques importantes qui doivent être abordées 
    pour assurer un développement responsable de l'IA dans l'avenir.
    
    ACTIONS : Les entreprises devraient se concentrer sur l'intégration de l'IA dans leurs opérations, 
    en particulier dans les domaines des centres de données et du développement visuel."""
    
    print("🇫🇷 Synthèse vocale française avec gTTS")
    print("=" * 50)
    
    # Option 1: Sauvegarder dans un fichier
    print("\n1️⃣ Génération du fichier audio...")
    audio_file = synthesize_text_to_file(text_long, "rapport_ia.mp3")
    
    if audio_file:
        print(f"📁 Fichier créé : {audio_file}")
        
        # Demander si l'utilisateur veut jouer le fichier
            
    # Option 2: Test avec des textes plus courts
    print("\n2️⃣ Test avec des phrases courtes...")
    
    test_sentences = [
        "Bonjour ! Comment allez-vous aujourd'hui ?",
        "L'intelligence artificielle progresse rapidement.",
        "Les centres de données sont essentiels pour l'IA moderne.",
        "Merci d'avoir écouté ce rapport sur l'intelligence artificielle."
    ]
    
    for i, sentence in enumerate(test_sentences, 1):
        print(f"\n📝 Test {i}: {sentence}")
        file_name = f"test_{i}.mp3"
        synthesize_text_to_file(sentence, file_name)
    
    print("\n✅ Tous les fichiers audio ont été générés !")
    print("💡 Tu peux maintenant les écouter avec n'importe quel lecteur audio.")

if __name__ == "__main__":
    main()