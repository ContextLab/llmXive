import spacy
from typing import Optional, Dict, Any
from langdetect import detect, LangDetectException
import re
import json
import os
import logging
import config

# Configure logging for the extraction module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load spaCy model once
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("en_core_web_sm not found. Attempting to download...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
    nlp = spacy.load("en_core_web_sm")

def calculate_pronoun_density(text: str) -> Dict[str, float]:
    """
    Calculate the density of first-person and third-person pronouns in the text.
    
    Args:
        text: The input text string.
        
    Returns:
        A dictionary containing:
            - 'first_person_density': float (count of 1st person pronouns / total tokens)
            - 'third_person_density': float (count of 3rd person pronouns / total tokens)
            - 'total_tokens': int
    """
    doc = nlp(text)
    total_tokens = len([token for token in doc if not token.is_space and not token.is_punct])
    
    if total_tokens == 0:
        return {
            'first_person_density': 0.0,
            'third_person_density': 0.0,
            'total_tokens': 0
        }
    
    # Define pronoun sets
    first_person = {'i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our', 'ours', 'ourselves'}
    third_person = {'he', 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'they', 'them', 'their', 'theirs', 'himself', 'herself', 'itself', 'themselves'}
    
    first_count = 0
    third_count = 0
    
    for token in doc:
        text_lower = token.text.lower()
        if text_lower in first_person:
            first_count += 1
        elif text_lower in third_person:
            third_count += 1
    
    return {
        'first_person_density': first_count / total_tokens,
        'third_person_density': third_count / total_tokens,
        'total_tokens': total_tokens
    }

def calculate_narrator_distance_score(text: str) -> float:
    """
    Calculate a narrator distance score based on pronoun usage.
    Lower scores indicate closer (first-person) perspective, higher scores indicate distant (third-person).
    
    Args:
        text: The input text string.
        
    Returns:
        A float score between 0.0 and 1.0.
    """
    pronouns = calculate_pronoun_density(text)
    first = pronouns['first_person_density']
    third = pronouns['third_person_density']
    total = first + third
    
    if total == 0:
        return 0.5  # Neutral/unknown
    
    # Score formula: ratio of third-person to total pronouns
    # 0.0 = purely first-person, 1.0 = purely third-person
    return third / total

def extract_perspective_features(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract perspective features from a single text file.
    Includes quality checks and logging for insufficient data quality.
    
    Args:
        file_path: Path to the text file.
        
    Returns:
        A dictionary with extracted features or None if extraction fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

    # Strip whitespace
    text = text.strip()
    
    # Check for empty content
    if not text:
        logger.warning(f"File {file_path} is empty. Skipping.")
        return None

    # Check minimum length (50 words)
    word_count = len(text.split())
    if word_count < 50:
        logger.warning(f"File {file_path} has fewer than 50 words ({word_count}). Skipping.")
        return None

    # Language detection
    try:
        lang = detect(text)
        if lang != 'en':
            logger.warning(f"File {file_path} detected as language '{lang}', skipping non-English text.")
            return None
    except LangDetectException:
        logger.warning(f"Could not detect language for {file_path}. Skipping.")
        return None

    # Calculate metrics
    pronoun_metrics = calculate_pronoun_density(text)
    distance_score = calculate_narrator_distance_score(text)
    
    # Quality Warning: Data Quality Insufficient
    # If pronoun density is extremely low (e.g., < 0.01), the text might be dialogue-heavy,
    # technical, or otherwise lacking narrative markers, making perspective analysis unreliable.
    total_pronoun_density = pronoun_metrics['first_person_density'] + pronoun_metrics['third_person_density']
    if total_pronoun_density < 0.01:
        logger.warning(f"data_quality_insufficient: Low pronoun density ({total_pronoun_density:.4f}) in {file_path}. "
                     "Perspective metrics may be unreliable.")
    
    # Quality Warning: Neutral/Omniscient
    if pronoun_metrics['first_person_density'] == 0.0 and pronoun_metrics['third_person_density'] == 0.0:
        logger.warning(f"Neutral/Omniscient text detected in {file_path}: No personal pronouns found.")

    return {
        'file_path': file_path,
        'word_count': word_count,
        'language': 'en',
        'first_person_density': pronoun_metrics['first_person_density'],
        'third_person_density': pronoun_metrics['third_person_density'],
        'narrator_distance_score': distance_score,
        'total_pronoun_density': total_pronoun_density,
        'quality_warnings': [] if total_pronoun_density >= 0.01 else ['low_pronoun_density']
    }