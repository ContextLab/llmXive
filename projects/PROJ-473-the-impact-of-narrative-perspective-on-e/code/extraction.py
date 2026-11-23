import spacy
from typing import Optional, Dict, Any, List
from langdetect import detect, LangDetectException
import re
import json
import os
import hashlib
import logging

# Configure logging for the module
logger = logging.getLogger(__name__)

# Pronoun lists as defined in T013
FIRST_PERSON_PRONOUNS = {'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'}
THIRD_PERSON_PRONOUNS = {'he', 'him', 'his', 'she', 'her', 'hers', 'they', 'them', 'their', 'theirs'}

class DataQualityError(Exception):
    """Custom exception for data quality issues (e.g., too short, wrong language)."""
    pass

def _load_spacy_model():
    """
    Load the spaCy English model.
    Handles the case where the model might not be installed by attempting to download it.
    """
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        # Attempt to download the model if not found
        logger.warning("en_core_web_sm not found. Attempting to download...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
            return spacy.load("en_core_web_sm")
        except subprocess.CalledProcessError as e:
            logger.error("Failed to download en_core_web_sm. Please install it manually: python -m spacy download en_core_web_sm")
            raise RuntimeError("spaCy model 'en_core_web_sm' is required but could not be loaded or downloaded.") from e

def calculate_pronoun_density(text: str) -> Dict[str, float]:
    """
    Calculate the density of first-person and third-person pronouns in the text.
    
    Args:
        text: The input text string.
        
    Returns:
        A dictionary with keys 'first_person_density' and 'third_person_density'.
    """
    nlp = _load_spacy_model()
    doc = nlp(text)
    
    total_tokens = len([token for token in doc if not token.is_space and not token.is_punct])
    if total_tokens == 0:
        return {'first_person_density': 0.0, 'third_person_density': 0.0}
    
    count_1st = 0
    count_3rd = 0
    
    for token in doc:
        lower_token = token.text.lower()
        if lower_token in FIRST_PERSON_PRONOUNS:
            count_1st += 1
        elif lower_token in THIRD_PERSON_PRONOUNS:
            count_3rd += 1
            
    return {
        'first_person_density': count_1st / total_tokens,
        'third_person_density': count_3rd / total_tokens
    }

def calculate_narrator_distance_score(text: str) -> float:
    """
    Calculate a score based on the ratio of first-person to total personal pronouns.
    Formula: score = count_1st / (count_1st + count_3rd).
    If both are 0, score is 0.5.
    
    Args:
        text: The input text string.
        
    Returns:
        A float score in [0.0, 1.0].
    """
    nlp = _load_spacy_model()
    doc = nlp(text)
    
    count_1st = 0
    count_3rd = 0
    
    for token in doc:
        lower_token = token.text.lower()
        if lower_token in FIRST_PERSON_PRONOUNS:
            count_1st += 1
        elif lower_token in THIRD_PERSON_PRONOUNS:
            count_3rd += 1
            
    total_personal = count_1st + count_3rd
    if total_personal == 0:
        return 0.5
    
    score = count_1st / total_personal
    # Assert score is in [0.0, 1.0] as per spec
    assert 0.0 <= score <= 1.0, f"Calculated score {score} is out of bounds."
    return score

def extract_perspective_features(input_dir: str, output_path: str) -> None:
    """
    Iterate over all .txt files in input_dir, extract perspective features,
    handle edge cases, and write results to output_path as JSON.
    
    Logic:
    1. Ensure data/logs/ directory exists.
    2. Iterate over .txt files.
    3. If text < 50 words, log "data_quality_insufficient" and skip.
    4. If non-English, log "language_not_english" and skip.
    5. Otherwise, calculate pronoun density and narrator distance.
    6. Append results to list and write to output_path as JSON.
    
    Args:
        input_dir: Path to directory containing .txt story files.
        output_path: Path to the output JSON file.
    """
    # 1. Ensure log directory exists
    log_dir = 'data/logs'
    os.makedirs(log_dir, exist_ok=True)
    
    # Setup logging to file
    log_file_path = os.path.join(log_dir, 'extraction.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file_path),
            logging.StreamHandler()
        ]
    )
    file_logger = logging.getLogger('extraction_file')
    file_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates if called multiple times in same session
    file_logger.handlers = []
    file_logger.addHandler(logging.FileHandler(log_file_path))
    
    if not os.path.isdir(input_dir):
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    
    results = []
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    
    if not txt_files:
        logger.warning(f"No .txt files found in {input_dir}")
        # Write empty list if no files
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
        return

    logger.info(f"Processing {len(txt_files)} files from {input_dir}")

    for filename in txt_files:
        file_path = os.path.join(input_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            file_logger.error(f"Could not decode file {filename} as UTF-8. Skipping.")
            continue
        except Exception as e:
            file_logger.error(f"Error reading file {filename}: {e}. Skipping.")
            continue

        # Check word count
        words = text.split()
        word_count = len(words)
        if word_count < 50:
            file_logger.info(f"data_quality_insufficient: {filename} (words: {word_count})")
            continue

        # Check language
        try:
            lang = detect(text)
            if lang != 'en':
                file_logger.info(f"language_not_english: {filename} (detected: {lang})")
                continue
        except LangDetectException:
            file_logger.warning(f"Could not detect language for {filename}. Skipping.")
            continue

        # Extract features
        try:
            pronoun_stats = calculate_pronoun_density(text)
            narrator_score = calculate_narrator_distance_score(text)
            
            # Determine confidence flag
            confidence_flag = "normal"
            if pronoun_stats['first_person_density'] == 0.0:
                confidence_flag = "neutral/omniscient"
            
            # Create story_id (SHA-256 of text)
            story_id = hashlib.sha256(text.encode('utf-8')).hexdigest()
            
            record = {
                'story_id': story_id,
                'raw_text': text, # Storing full text as per T016 schema requirement
                'pronoun_density_1st': pronoun_stats['first_person_density'],
                'pronoun_density_3rd': pronoun_stats['third_person_density'],
                'narrator_distance_score': narrator_score,
                'confidence_flag': confidence_flag
            }
            results.append(record)
            
        except Exception as e:
            file_logger.error(f"Error processing {filename}: {e}. Skipping.")
            continue

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Extraction complete. Wrote {len(results)} records to {output_path}")