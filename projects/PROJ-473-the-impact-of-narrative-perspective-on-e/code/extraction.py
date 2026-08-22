import spacy
from typing import Optional, Dict, Any, List
from langdetect import detect, LangDetectException
import re
import json
import os
import logging
import hashlib

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    import subprocess
    subprocess.check_call(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

class DataQualityError(Exception):
    """Custom exception for data quality issues."""
    pass

def calculate_pronoun_density(text: str) -> Dict[str, float]:
    """
    Calculate pronoun density using spaCy.
    Counts first-person and third-person pronouns, normalized by total token count.
    """
    doc = nlp(text)
    tokens = [token.text.lower() for token in doc if not token.is_space]
    
    if len(tokens) == 0:
        return {'pronoun_density_1st': 0.0, 'pronoun_density_3rd': 0.0}
    
    first_person = {'i', 'me', 'my', 'mine', 'we', 'us', 'our', 'ours'}
    third_person = {'he', 'him', 'his', 'she', 'her', 'hers', 'they', 'them', 'their', 'theirs'}
    
    first_count = sum(1 for token in tokens if token in first_person)
    third_count = sum(1 for token in tokens if token in third_person)
    
    return {
        'pronoun_density_1st': first_count / len(tokens),
        'pronoun_density_3rd': third_count / len(tokens)
    }

def calculate_narrator_distance_score(text: str) -> float:
    """
    Calculate a score based on the ratio of first-person to total personal pronouns.
    1.0 = pure first-person, 0.0 = pure third-person, 0.5 = mix.
    """
    densities = calculate_pronoun_density(text)
    first = densities['pronoun_density_1st']
    third = densities['pronoun_density_3rd']
    
    total = first + third
    if total == 0:
        return 0.5  # Neutral if no pronouns found
    
    return first / total

def extract_perspective_features(input_dir: str, output_path: str) -> List[Dict[str, Any]]:
    """
    Extract perspective features from all stories in input_dir.
    Handles edge cases: <50 words, non-English text.
    
    If text length < 50 words, skip the record, log a "data_quality_insufficient" 
    warning to data/logs/extraction.log, and continue processing.
    If langdetect detects non-English, skip and log.
    Otherwise, call calculate_pronoun_density and calculate_narrator_distance_score.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Extracting perspective features from {input_dir} to {output_path}")
    
    results = []
    log_file = 'data/logs/extraction.log'
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure file handler for extraction log
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    
    for filename in os.listdir(input_dir):
        if not filename.endswith('.txt'):
            continue
        
        file_path = os.path.join(input_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
            # Check text length (edge case: <50 words)
            words = text.split()
            if len(words) < 50:
                logger.warning(f"data_quality_insufficient: Skipping {filename} ({len(words)} words)")
                continue
            
            # Check language (edge case: non-English)
            try:
                lang = detect(text[:200])  # Detect from first 200 chars
                if lang != 'en':
                    logger.warning(f"Skipping {filename}: non-English language detected ({lang})")
                    continue
            except LangDetectException:
                logger.warning(f"Skipping {filename}: language detection failed")
                continue
            
            # Calculate features
            densities = calculate_pronoun_density(text)
            distance_score = calculate_narrator_distance_score(text)
            
            # Generate story_id (SHA-256 hash of text)
            story_id = hashlib.sha256(text.encode()).hexdigest()
            
            # Determine confidence flag
            if densities['pronoun_density_1st'] == 0.0:
                confidence_flag = "neutral/omniscient"
            else:
                confidence_flag = "high"
            
            record = {
                'story_id': story_id,
                'raw_text': text[:500],  # Truncate for JSON size
                'pronoun_density_1st': densities['pronoun_density_1st'],
                'pronoun_density_3rd': densities['pronoun_density_3rd'],
                'narrator_distance_score': distance_score,
                'confidence_flag': confidence_flag
            }
            
            results.append(record)
            
        except Exception as e:
            logger.error(f"Error processing {filename}: {e}")
            continue
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Extracted {len(results)} stories to {output_path}")
    return results