import spacy
from typing import Optional, Dict, Any, List
from langdetect import detect, LangDetectException
import re
import json
import os
import logging

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load spaCy model (ensure 'en_core_web_sm' is installed)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.error("spaCy 'en_core_web_sm' model not found. Run: python -m spacy download en_core_web_sm")
    raise

# Pronoun sets for extraction
PRONOUNS_1ST = {"i", "me", "my", "mine", "myself", "we", "us", "our", "ours", "ourselves"}
PRONOUNS_2ND = {"you", "your", "yours", "yourself", "yourselves"}
PRONOUNS_3RD = {"he", "she", "it", "they", "him", "her", "them", "his", "hers", "its", "their", "theirs", "himself", "herself", "itself", "themselves", "he's", "she's", "they're"}

def calculate_pronoun_density(text: str) -> Dict[str, float]:
    """
    Calculate the density of 1st, 2nd, and 3rd person pronouns in the text.
    Returns a dictionary with densities per total word count.
    """
    if not text or not isinstance(text, str):
        return {"pronoun_density_1st": 0.0, "pronoun_density_2nd": 0.0, "pronoun_density_3rd": 0.0}

    doc = nlp(text.lower())
    words = [token.text for token in doc if token.is_alpha and not token.is_space]
    total_words = len(words) if words else 1  # Avoid division by zero

    counts = {"1st": 0, "2nd": 0, "3rd": 0}

    for token in doc:
        if token.text.lower() in PRONOUNS_1ST:
            counts["1st"] += 1
        elif token.text.lower() in PRONOUNS_2ND:
            counts["2nd"] += 1
        elif token.text.lower() in PRONOUNS_3RD:
            counts["3rd"] += 1

    return {
        "pronoun_density_1st": counts["1st"] / total_words,
        "pronoun_density_2nd": counts["2nd"] / total_words,
        "pronoun_density_3rd": counts["3rd"] / total_words
    }

def calculate_narrator_distance_score(text: str) -> float:
    """
    Calculate a narrator distance score.
    Lower score indicates closer proximity (more 1st person).
    Higher score indicates distance (more 3rd person).
    Formula: (3rd_density - 1st_density)
    """
    densities = calculate_pronoun_density(text)
    return densities["pronoun_density_3rd"] - densities["pronoun_density_1st"]

def extract_perspective_features(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract perspective features from a text file.
    Returns a dictionary with story_id, features, and quality flags.
    """
    logger.info(f"Processing file: {file_path}")

    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

    if not text or len(text.strip()) < 50:
        logger.warning(f"File {file_path} is too short (<50 words) or empty. Skipping.")
        return None

    # Language detection
    try:
        lang = detect(text[:200]) # Detect on first 200 chars for speed
        if lang != 'en':
            logger.warning(f"File {file_path} detected as non-English ({lang}). Skipping.")
            return None
    except LangDetectException:
        logger.warning(f"Could not detect language for {file_path}. Skipping.")
        return None

    # Extract features
    pronoun_densities = calculate_pronoun_density(text)
    narrator_distance = calculate_narrator_distance_score(text)
    word_count = len([t for t in nlp(text) if t.is_alpha])

    # Quality Check: Data Quality Warning (T018)
    # Flag if the text is too short for reliable statistics or has insufficient pronoun data
    data_quality_insufficient = False
    if word_count < 100:
        data_quality_insufficient = True
        logger.warning(f"data_quality_insufficient: File {file_path} has only {word_count} words, which may be insufficient for robust perspective analysis.")
    elif pronoun_densities["pronoun_density_1st"] == 0.0 and pronoun_densities["pronoun_density_3rd"] == 0.0:
        data_quality_insufficient = True
        logger.warning(f"data_quality_insufficient: File {file_path} contains no detected personal pronouns, making perspective classification unreliable.")

    # Flag for neutral/omniscient (T017 requirement, implemented here as part of extraction)
    is_neutral_omniscient = False
    if pronoun_densities["pronoun_density_1st"] == 0.0:
        is_neutral_omniscient = True
        logger.info(f"Neutral/Omniscient flag set for {file_path} (1st person density is 0.0).")

    story_id = os.path.basename(file_path)

    return {
        "story_id": story_id,
        "file_path": file_path,
        "word_count": word_count,
        "perspective_features": {
            "pronoun_density_1st": pronoun_densities["pronoun_density_1st"],
            "pronoun_density_2nd": pronoun_densities["pronoun_density_2nd"],
            "pronoun_density_3rd": pronoun_densities["pronoun_density_3rd"],
            "narrator_distance_score": narrator_distance
        },
        "quality_flags": {
            "data_quality_insufficient": data_quality_insufficient,
            "is_neutral_omniscient": is_neutral_omniscient
        }
    }
