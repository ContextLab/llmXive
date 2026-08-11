import spacy
from typing import Optional, Dict, Any, List
from langdetect import detect, LangDetectException
import re
import json
import os
import logging

# Load model lazily to avoid import-time failure if not installed
_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger = logging.getLogger(__name__)
            logger.critical("en_core_web_sm model not found. Please run: python -m spacy download en_core_web_sm")
            raise
    return _nlp

def calculate_pronoun_density(text: str) -> Dict[str, float]:
    """
    Calculate the density of first-person and third-person pronouns in the text.
    Returns a dict with keys: 'pronoun_density_1st', 'pronoun_density_3rd'.
    """
    nlp = _get_nlp()
    doc = nlp(text)
    
    first_person_pronouns = {'i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our', 'ours', 'ourselves'}
    third_person_pronouns = {'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 
                             'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves'}
    
    total_tokens = len(doc)
    if total_tokens == 0:
        return {'pronoun_density_1st': 0.0, 'pronoun_density_3rd': 0.0}
    
    count_1st = 0
    count_3rd = 0
    
    for token in doc:
        lower = token.text.lower()
        if lower in first_person_pronouns:
            count_1st += 1
        elif lower in third_person_pronouns:
            count_3rd += 1
    
    return {
        'pronoun_density_1st': count_1st / total_tokens,
        'pronoun_density_3rd': count_3rd / total_tokens
    }

def calculate_narrator_distance_score(text: str) -> float:
    """
    Calculate a narrator distance score.
    Lower score = closer (more first-person), Higher score = more distant (more third-person).
    Simple heuristic: ratio of 3rd person to (1st + 3rd) pronouns.
    """
    densities = calculate_pronoun_density(text)
    p1 = densities['pronoun_density_1st']
    p3 = densities['pronoun_density_3rd']
    
    total = p1 + p3
    if total == 0:
        return 0.5 # Neutral/Omniscient default
    
    return p3 / total

def extract_perspective_features(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract all perspective features from a single text file.
    Returns a dictionary with:
      - story_id: filename without extension
      - text_length: number of characters
      - word_count: number of words
      - pronoun_density_1st
      - pronoun_density_3rd
      - narrator_distance_score
      - language_detected
      - confidence_flag: "neutral/omniscient" if 1st person density is 0.0
      - data_quality_insufficient: True if < 50 words
    """
    logger = logging.getLogger(__name__)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        logger.error(f"Could not read file {file_path}: {e}")
        return None
    
    # Basic stats
    word_count = len(text.split())
    text_length = len(text)
    
    # Edge case: too short
    if word_count < 50:
        logger.warning(f"File {file_path} has fewer than 50 words. Skipping.")
        return None
    
    # Language detection
    try:
        lang = detect(text[:1000]) # Detect on first 1000 chars for speed
        if lang != 'en':
            logger.info(f"File {file_path} detected as language {lang}. Skipping non-English.")
            return None
    except LangDetectException:
        logger.warning(f"Could not detect language for {file_path}. Skipping.")
        return None
    
    # Calculate features
    pronoun_data = calculate_pronoun_density(text)
    distance_score = calculate_narrator_distance_score(text)
    
    # Confidence flag
    confidence_flag = "normal"
    if pronoun_data['pronoun_density_1st'] == 0.0:
        confidence_flag = "neutral/omniscient"
    
    story_id = os.path.splitext(os.path.basename(file_path))[0]
    
    return {
        'story_id': story_id,
        'file_path': file_path,
        'text_length': text_length,
        'word_count': word_count,
        'pronoun_density_1st': pronoun_data['pronoun_density_1st'],
        'pronoun_density_3rd': pronoun_data['pronoun_density_3rd'],
        'narrator_distance_score': distance_score,
        'language_detected': lang,
        'confidence_flag': confidence_flag,
        'data_quality_insufficient': False
    }
