import os
import sys
import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

# Attempt to import NRC and VADER lexicons
# NRC: often available via nltk or as a standalone file in data/
# VADER: via nltk.sentiment.vader
try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    from nltk.tokenize import word_tokenize
    nltk.download('vader_lexicon', quiet=True)
    nltk.download('punkt', quiet=True)
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

# Custom exception for valence calculation errors
class ValenceCalculationError(Exception):
    """Raised when valence calculation fails."""
    pass

def get_project_root() -> Path:
    """Get the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger for this module."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_nrc_lexicon() -> Dict[str, Dict[str, int]]:
    """
    Load the NRC Emotion Lexicon.
    Tries to load from a standard location or a local file.
    Returns a dict: {word: {emotion: count, ...}}
    """
    nrc_path = get_project_root() / 'data' / 'raw' / 'nrc_emotion_lexicon.txt'
    lexicon = {}
    
    if not nrc_path.exists():
        # Fallback to a known public URL if local file missing, but we must fail loudly if we can't get it
        # For this implementation, we assume the user has placed the NRC lexicon in data/raw/
        # or we try to load from nltk if available (though NRC isn't standard nltk)
        logger = logging.getLogger(__name__)
        logger.warning("NRC lexicon file not found at data/raw/nrc_emotion_lexicon.txt. "
                       "Attempting to proceed without NRC coverage calculation (will force VADER).")
        return {}

    with open(nrc_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                word, emotion, count = parts[0].lower(), parts[1], int(parts[2])
                if word not in lexicon:
                    lexicon[word] = {}
                lexicon[word][emotion] = count
    
    return lexicon

def load_vader_lexicon() -> Dict[str, float]:
    """
    Load VADER lexicon via NLTK.
    Returns a dict: {word: sentiment_score}
    """
    if not HAS_NLTK:
        raise ValenceCalculationError("NLTK is required for VADER lexicon.")
    
    analyzer = SentimentIntensityAnalyzer()
    # VADER lexicon is internal to the analyzer, we extract it if possible,
    # but for coverage calculation we usually just check if words are in the lexicon.
    # We'll return the analyzer instance to be used for scoring.
    return analyzer

def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase words."""
    if not HAS_NLTK:
        # Fallback to simple regex tokenization if NLTK missing
        return re.findall(r'\b\w+\b', text.lower())
    return word_tokenize(text.lower())

def calculate_nrc_coverage(text: str, nrc_lexicon: Dict[str, Dict[str, int]]) -> Tuple[float, int, int]:
    """
    Calculate the percentage of words in text that are in the NRC lexicon.
    Returns: (coverage_percentage, words_in_lexicon, total_words)
    """
    if not nrc_lexicon:
        return 0.0, 0, 0
    
    words = tokenize(text)
    if not words:
        return 0.0, 0, 0
    
    matched = sum(1 for w in words if w in nrc_lexicon)
    coverage = (matched / len(words)) * 100.0
    return coverage, matched, len(words)

def get_nrc_valence(text: str, nrc_lexicon: Dict[str, Dict[str, int]]) -> float:
    """
    Calculate a simple valence score using NRC lexicon.
    We map emotions to valence: Joy=1, Trust=1, Surprise=0, Fear=-1, etc.
    Returns a score between -1 and 1.
    """
    if not nrc_lexicon:
        return 0.0
    
    # Simple mapping for valence based on NRC emotions
    # This is a heuristic; real NRC valence might be pre-computed
    emotion_valence = {
        'joy': 1.0, 'trust': 0.8, 'anticipation': 0.5, 'surprise': 0.0,
        'sadness': -0.8, 'disgust': -0.9, 'fear': -0.9, 'anger': -0.8
    }
    
    words = tokenize(text)
    scores = []
    for w in words:
        if w in nrc_lexicon:
            for emotion, count in nrc_lexicon[w].items():
                if emotion in emotion_valence:
                    scores.append(emotion_valence[emotion] * count)
    
    if not scores:
        return 0.0
    return np.mean(scores)

def get_vader_valence(text: str, vader_analyzer) -> float:
    """
    Calculate valence using VADER.
    Returns the compound score.
    """
    if not HAS_NLTK:
        raise ValenceCalculationError("NLTK required for VADER.")
    scores = vader_analyzer.polarity_scores(text)
    return scores['compound']

def log_lexicon_switch(coverage: float, from_lexicon: str, to_lexicon: str, runtime_events_path: Path):
    """Log the lexicon switch event to runtime_events.json."""
    events = []
    if runtime_events_path.exists():
        try:
            with open(runtime_events_path, 'r', encoding='utf-8') as f:
                events = json.load(f)
        except json.JSONDecodeError:
            events = []
    
    events.append({
        "event": "lexicon_switch",
        "from": from_lexicon,
        "to": to_lexicon,
        "coverage": coverage,
        "timestamp": pd.Timestamp.now().isoformat(),
        "reason": "Average NRC coverage below 50% threshold."
    })
    
    with open(runtime_events_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)

def main():
    logger = setup_logger("valence_calculation")
    logger.info("Starting Valence Calculation (T021)")

    project_root = get_project_root()
    input_path = project_root / 'data' / 'derived' / 'empirical_outcomes.csv'
    output_path = project_root / 'data' / 'derived' / 'valence_scores.csv'
    runtime_events_path = project_root / 'state' / 'runtime_events.json'

    # Ensure state directory exists
    runtime_events_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load data
    df = pd.read_csv(input_path)
    
    if 'headline_text' not in df.columns:
        raise ValenceCalculationError("Input file missing 'headline_text' column.")

    # Load Lexicons
    nrc_lexicon = load_nrc_lexicon()
    vader_analyzer = load_vader_lexicon() if HAS_NLTK else None

    if not vader_analyzer:
        raise ValenceCalculationError("VADER lexicon could not be loaded (NLTK missing).")

    # Calculate NRC coverage for each headline
    coverages = []
    for text in df['headline_text']:
        cov, _, _ = calculate_nrc_coverage(text, nrc_lexicon)
        coverages.append(cov)

    avg_coverage = np.mean(coverages)
    logger.info(f"Average NRC lexical coverage: {avg_coverage:.2f}%")

    use_nrc = avg_coverage >= 50.0
    lexicon_used = "NRC" if use_nrc else "VADER"

    if not use_nrc:
        logger.warning("Average NRC coverage < 50%. Switching to VADER for all headlines.")
        log_lexicon_switch(avg_coverage, "NRC", "VADER", runtime_events_path)
        # Log warning about systematic confound
        warning_msg = f"Systematic confound warning: Lexicon switched to VADER for all items due to low NRC coverage ({avg_coverage:.2f}%). This may introduce bias if NRC and VADER valence scales differ systematically."
        logger.warning(warning_msg)

    # Calculate valence scores
    valence_scores = []
    for text in df['headline_text']:
        if use_nrc:
            score = get_nrc_valence(text, nrc_lexicon)
        else:
            score = get_vader_valence(text, vader_analyzer)
        valence_scores.append(score)

    # Create output dataframe
    output_df = pd.DataFrame({
        'participant_id': df['participant_id'],
        'headline_id': df['headline_id'],
        'headline_text': df['headline_text'],
        'belief_rating': df['belief_rating'],
        'valence_score': valence_scores,
        'lexicon_used': lexicon_used
    })

    # Write output
    output_df.to_csv(output_path, index=False)
    logger.info(f"Valence scores written to {output_path}")
    logger.info(f"Used lexicon: {lexicon_used}")

if __name__ == "__main__":
    main()
