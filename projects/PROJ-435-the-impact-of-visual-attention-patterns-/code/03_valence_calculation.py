import os
import sys
import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import pandas as pd
import numpy as np

# Import NLTK data handling
try:
    import nltk
    from nltk.corpus import sentiwordnet as swn
    from nltk.sentiment import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize
    from nltk.corpus import words
    nltk_available = True
except ImportError:
    nltk_available = False

# Import VADER if available (bundled with nltk.sentiment)
try:
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

# Constants
NRC_LEXICON_URL = "https://saifmohammad.com/WebDocs/NRC-Emotion-Lexicon-Wordlevel-v8.zip"
NRC_LEXICON_NAME = "NRC-Emotion-Lexicon-Wordlevel-v8.txt"
NRC_LEXICON_LOCAL = "nrc_lexicon.txt"

logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def setup_logger(name: str = "valence_calc") -> logging.Logger:
    """Setup a logger for this module."""
    log_path = get_project_root() / "output" / "valence_calc.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(name)

def load_nrc_lexicon() -> Optional[Dict[str, Dict[str, int]]]:
    """
    Load the NRC Emotion Lexicon.
    Returns a dict: {word: {emotion: score}}
    Scores are typically 0 or 1.
    """
    # Try to load from local cache first
    local_path = get_project_root() / "data" / "raw" / NRC_LEXICON_LOCAL
    if local_path.exists():
        logger.info(f"Loading NRC lexicon from local cache: {local_path}")
        lexicon = {}
        with open(local_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 3:
                    word, emotion, score = parts[0].lower(), parts[1], int(parts[2])
                    if word not in lexicon:
                        lexicon[word] = {}
                    lexicon[word][emotion] = score
        return lexicon
    
    # If not local, we assume it was downloaded in a previous step or will be downloaded
    # For this implementation, we attempt to load a standard NRC format if available
    # In a real pipeline, T005 would ensure this file exists.
    logger.warning("NRC lexicon not found locally. Attempting to load from standard location if available.")
    return None

def load_vader_lexicon() -> bool:
    """
    Verify VADER is available.
    """
    return VADER_AVAILABLE and nltk_available

def tokenize(text: str) -> List[str]:
    """
    Tokenize text into lowercase words, removing punctuation.
    """
    if not nltk_available:
        # Fallback simple tokenization
        text = text.lower()
        words = re.findall(r'\b[a-z]+\b', text)
        return words
    
    try:
        # Ensure punkt is downloaded
        try:
            word_tokenize("test")
        except LookupError:
            nltk.download('punkt', quiet=True)
        return word_tokenize(text.lower())
    except Exception as e:
        logger.warning(f"NLTK tokenization failed: {e}. Using regex fallback.")
        text = text.lower()
        return re.findall(r'\b[a-z]+\b', text)

def calculate_nrc_coverage(text: str, lexicon: Dict[str, Dict[str, int]]) -> float:
    """
    Calculate NRC coverage: percentage of unique words in headline matching the lexicon.
    """
    if not lexicon:
        return 0.0
    
    words = set(tokenize(text))
    if not words:
        return 0.0
    
    matching_words = sum(1 for word in words if word in lexicon)
    return (matching_words / len(words)) * 100.0

def get_nrc_valence(text: str, lexicon: Dict[str, Dict[str, int]]) -> float:
    """
    Calculate NRC valence score for a text.
    NRC doesn't have a direct 'valence' column in all versions, but often 'positive' and 'negative' are present.
    We compute valence as (positive_count - negative_count) / total_matches.
    """
    if not lexicon:
        return 0.0
    
    words = tokenize(text)
    pos_scores = []
    neg_scores = []
    
    for word in words:
        if word in lexicon:
            emotions = lexicon[word]
            if 'positive' in emotions:
                pos_scores.append(emotions['positive'])
            if 'negative' in emotions:
                neg_scores.append(emotions['negative'])
    
    if not pos_scores and not neg_scores:
        return 0.0
    
    total_pos = sum(pos_scores)
    total_neg = sum(neg_scores)
    total = total_pos + total_neg
    
    if total == 0:
        return 0.0
    
    return (total_pos - total_neg) / total

def get_vader_valence(text: str) -> float:
    """
    Calculate VADER compound score.
    Returns a value between -1 (most negative) and 1 (most positive).
    """
    if not VADER_AVAILABLE or not nltk_available:
        raise RuntimeError("VADER not available")
    
    try:
        sia = SentimentIntensityAnalyzer()
        scores = sia.polarity_scores(text)
        return scores['compound']
    except Exception as e:
        logger.error(f"VADER scoring failed: {e}")
        return 0.0

def log_lexicon_switch(coverage: float, from_lexicon: str, to_lexicon: str) -> None:
    """
    Log a lexicon switch event to state/runtime_events.json.
    """
    project_root = get_project_root()
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    events_file = state_dir / "runtime_events.json"
    
    event_record = {
        "event": "lexicon_switch",
        "from": from_lexicon,
        "to": to_lexicon,
        "coverage": coverage
    }
    
    existing_events = []
    if events_file.exists():
        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    # Handle JSON array or single object (though spec implies appending objects)
                    # Spec says: "append a single JSON object". This usually implies a list of events.
                    # If it's a single object, we might need to parse and convert to list.
                    # Assuming it's a list of events for robustness.
                    existing_events = json.loads(content)
                    if not isinstance(existing_events, list):
                        existing_events = [existing_events]
        except json.JSONDecodeError:
            logger.warning("Existing runtime_events.json is not valid JSON. Starting fresh.")
            existing_events = []
    
    existing_events.append(event_record)
    
    with open(events_file, 'w', encoding='utf-8') as f:
        json.dump(existing_events, f, indent=2)
    
    logger.info(f"Logged lexicon switch event: {event_record}")

def main():
    """
    Main entry point for valence calculation.
    Input: data/derived/empirical_outcomes.csv
    Output: data/derived/valence_scores.csv
    """
    logger.info("Starting valence calculation pipeline.")
    
    project_root = get_project_root()
    input_path = project_root / "data" / "derived" / "empirical_outcomes.csv"
    output_path = project_root / "data" / "derived" / "valence_scores.csv"
    
    # Verify input exists
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load data
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)
    
    required_cols = ['headline_text']
    for col in required_cols:
        if col not in df.columns:
            logger.error(f"Missing required column in input: {col}")
            sys.exit(1)
    
    # Load NRC Lexicon
    nrc_lexicon = load_nrc_lexicon()
    
    # Calculate coverage for each headline
    logger.info("Calculating NRC coverage for all headlines.")
    df['nrc_coverage'] = df['headline_text'].apply(
        lambda x: calculate_nrc_coverage(str(x), nrc_lexicon) if pd.notna(x) else 0.0
    )
    
    # Calculate global average coverage
    global_avg_coverage = df['nrc_coverage'].mean()
    logger.info(f"Global average NRC coverage: {global_avg_coverage:.2f}%")
    
    # Determine which lexicon to use
    use_vader = False
    if nrc_lexicon is None or global_avg_coverage < 50.0:
        use_vader = True
        logger.warning(f"Global coverage ({global_avg_coverage:.2f}%) < 50% or NRC missing. Switching to VADER.")
        
        if not load_vader_lexicon():
            logger.error("VADER is not available and NRC coverage is insufficient. Cannot proceed.")
            sys.exit(1)
        
        # Log the switch
        log_lexicon_switch(global_avg_coverage, "NRC", "VADER")
    
    # Calculate valence scores
    logger.info("Calculating valence scores.")
    valence_scores = []
    
    for idx, row in df.iterrows():
        text = str(row['headline_text']) if pd.notna(row['headline_text']) else ""
        if not text.strip():
            valence_scores.append(0.0)
            continue
        
        if use_vader:
            try:
                score = get_vader_valence(text)
            except Exception as e:
                logger.warning(f"VADER failed for row {idx}: {e}. Setting to 0.")
                score = 0.0
        else:
            # Use NRC
            score = get_nrc_valence(text, nrc_lexicon)
        
        valence_scores.append(score)
    
    df['valence_score'] = valence_scores
    
    # Prepare output
    # Select relevant columns: participant_id, headline_id (if present), headline_text, valence_score
    output_cols = [c for c in df.columns if c in ['participant_id', 'headline_id', 'headline_text', 'valence_score']]
    # Ensure valence_score is last
    if 'valence_score' in output_cols:
        output_cols.remove('valence_score')
        output_cols.append('valence_score')
    
    output_df = df[output_cols]
    
    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    logger.info(f"Valence calculation complete. Output written to: {output_path}")
    logger.info(f"Lexicon used: {'VADER' if use_vader else 'NRC'}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
