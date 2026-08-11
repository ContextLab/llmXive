import spacy
from typing import Optional, Dict, Any, List
from langdetect import detect, LangDetectException
import re
import json
import os
import logging

logger = logging.getLogger(__name__)

# Load spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy model 'en_core_web_sm' not found. Please run: python -m spacy download en_core_web_sm")
    raise

class DataQualityError(Exception):
    """Raised when data quality is insufficient for processing."""
    pass

def calculate_pronoun_density(text: str) -> Dict[str, float]:
    """
    Calculate pronoun density using spaCy.
    Logic:
      - Count first-person pronouns: I, me, my, mine, we, us, our, ours
      - Count third-person pronouns: he, him, his, she, her, hers, they, them, their, theirs
      - Normalize by total token count.
    """
    doc = nlp(text)
    tokens = [token.text.lower() for token in doc if token.is_alpha]
    total_tokens = len(tokens)
    
    if total_tokens == 0:
        return {'first': 0.0, 'third': 0.0}

    first_person = {'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'}
    third_person = {'he', 'him', 'his', 'she', 'her', 'hers', 'they', 'them', 'their', 'theirs'}

    count_1st = sum(1 for t in tokens if t in first_person)
    count_3rd = sum(1 for t in tokens if t in third_person)

    return {
        'first': count_1st / total_tokens,
        'third': count_3rd / total_tokens
    }

def calculate_narrator_distance_score(text: str) -> float:
    """
    Calculate a score based on the ratio of first-person to total personal pronouns.
    1.0 = pure first-person, 0.0 = pure third-person, 0.5 = mix.
    """
    densities = calculate_pronoun_density(text)
    total_personal = densities['first'] + densities['third']
    
    if total_personal == 0:
        return 0.5 # Neutral if no pronouns found
    
    # Score = first / (first + third)
    # If first=0.1, third=0.0 -> 1.0
    # If first=0.0, third=0.1 -> 0.0
    return densities['first'] / total_personal

def extract_perspective_features(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract perspective features from a file.
    Logic:
      - If text length < 50 words, raise DataQualityError.
      - If langdetect detects non-English, skip and log.
      - Otherwise, calculate pronoun density and narrator distance.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

    # Check word count
    words = text.split()
    if len(words) < 50:
        error_msg = f"data_quality_insufficient: {file_path} has < 50 words"
        logger.warning(error_msg)
        # Log to extraction.log specifically
        log_path = "data/logs/extraction.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a') as log_file:
            log_file.write(f"{error_msg}\n")
        raise DataQualityError(error_msg)

    # Check language
    try:
        lang = detect(text[:1000]) # Check first 1000 chars for speed
        if lang != 'en':
            logger.warning(f"Skipping non-English file: {file_path} (detected: {lang})")
            return None
    except LangDetectException:
        logger.warning(f"Could not detect language for {file_path}, skipping.")
        return None

    # Calculate features
    densities = calculate_pronoun_density(text)
    distance_score = calculate_narrator_distance_score(text)

    # Determine confidence flag
    confidence_flag = "high"
    if densities['first'] == 0.0 and densities['third'] == 0.0:
        confidence_flag = "neutral/omniscient"

    # Truncate raw text for output
    raw_text_preview = text[:500]

    return {
        'story_id': os.path.splitext(os.path.basename(file_path))[0],
        'raw_text': raw_text_preview,
        'pronoun_density_1st': densities['first'],
        'pronoun_density_3rd': densities['third'],
        'narrator_distance_score': distance_score,
        'confidence_flag': confidence_flag
    }
