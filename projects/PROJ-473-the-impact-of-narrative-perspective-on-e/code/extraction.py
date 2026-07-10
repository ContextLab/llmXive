import spacy
from typing import Optional, Dict, Any
from langdetect import detect, LangDetectException
import re
import json
import os

# Lazy load spaCy model to avoid import overhead in other modules
_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise RuntimeError(
                "spaCy English model 'en_core_web_sm' not found. "
                "Please run: python -m spacy download en_core_web_sm"
            )
    return _nlp

def calculate_pronoun_density(text: str) -> Dict[str, float]:
    """
    Calculate the density of first-person, second-person, and third-person pronouns.
    
    Args:
        text: The input text to analyze.
        
    Returns:
        A dictionary with keys 'first_person', 'second_person', 'third_person'
        containing the density (count / total_words) for each category.
    """
    if not text or not isinstance(text, str):
        return {"first_person": 0.0, "second_person": 0.0, "third_person": 0.0}
    
    nlp = _get_nlp()
    doc = nlp(text)
    
    total_words = len([token for token in doc if not token.is_space and not token.is_punct])
    if total_words == 0:
        return {"first_person": 0.0, "second_person": 0.0, "third_person": 0.0}
    
    first_person = {"I", "me", "my", "mine", "we", "us", "our", "ours"}
    second_person = {"you", "your", "yours"}
    third_person = {"he", "she", "it", "they", "him", "her", "them", "his", "hers", "its", "their"}
    
    counts = {"first_person": 0, "second_person": 0, "third_person": 0}
    
    for token in doc:
        lemma = token.lemma_.lower()
        if lemma in first_person:
            counts["first_person"] += 1
        elif lemma in second_person:
            counts["second_person"] += 1
        elif lemma in third_person:
            counts["third_person"] += 1
            
    return {
        "first_person": counts["first_person"] / total_words,
        "second_person": counts["second_person"] / total_words,
        "third_person": counts["third_person"] / total_words
    }

def calculate_narrator_distance_score(text: str) -> float:
    """
    Calculate a narrator distance score based on pronoun usage.
    Higher scores indicate greater distance (more third-person, less first-person).
    
    Args:
        text: The input text to analyze.
        
    Returns:
        A float between 0.0 (close/first-person) and 1.0 (distant/third-person).
    """
    pronouns = calculate_pronoun_density(text)
    first = pronouns["first_person"]
    third = pronouns["third_person"]
    
    if first + third == 0:
        return 0.5  # Neutral default if no pronouns found
        
    return third / (first + third)

def extract_perspective_features(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract perspective features from a story file.
    
    Args:
        file_path: Path to the story file.
        
    Returns:
        A dictionary containing story_id, perspective features, and metadata.
        Returns None if the file cannot be processed (e.g., non-English, too short).
    """
    if not os.path.exists(file_path):
        return None
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception:
        return None
        
    # Basic validation
    if not text or len(text.split()) < 50:
        return None
        
    # Language detection
    try:
        lang = detect(text[:2048])  # Detect on first chunk
        if lang != 'en':
            return None
    except LangDetectException:
        return None
        
    # Calculate features
    pronoun_densities = calculate_pronoun_density(text)
    narrator_distance = calculate_narrator_distance_score(text)
    
    # T017: Validation logic for neutral/omniscient texts
    is_neutral_omniscient = (pronoun_densities["first_person"] == 0.0)
    
    return {
        "file_path": file_path,
        "story_id": os.path.basename(file_path),
        "word_count": len(text.split()),
        "language": "en",
        "pronoun_density_1st": pronoun_densities["first_person"],
        "pronoun_density_2nd": pronoun_densities["second_person"],
        "pronoun_density_3rd": pronoun_densities["third_person"],
        "narrator_distance_score": narrator_distance,
        "is_neutral_omniscient": is_neutral_omniscient,
        "data_quality_insufficient": False  # Can be set to True by T018 logic
    }
