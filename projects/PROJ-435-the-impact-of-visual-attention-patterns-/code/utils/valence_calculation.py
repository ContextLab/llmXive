import os
import sys
import logging
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

try:
    import nltk
    from nltk.tokenize import word_tokenize
    from nltk.corpus import stopwords
except ImportError:
    # Fallback if nltk not installed (though requirements.txt should handle this)
    def word_tokenize(text):
        return re.findall(r'\b\w+\b', text.lower())
    stopwords = type('obj', (object,), {'words': lambda lang: []})()

# Ensure NLTK data is available if nltk is present
if 'nltk' in sys.modules:
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
        except Exception:
            pass
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords', quiet=True)
        except Exception:
            pass

# Custom exception for valence calculation errors
class ValenceCalculationError(Exception):
    """Raised when valence calculation fails."""
    pass

def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent.parent

def setup_logger() -> logging.Logger:
    """Setup and return the valence calculation logger."""
    logger = logging.getLogger('valence_calculation')
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def load_nrc_lexicon() -> Dict[str, Dict[str, int]]:
    """Load the NRC Emotion Lexicon.
    
    Returns:
        Dict mapping words to emotion scores (0 or 1).
    """
    # In a real implementation, this would load from a file or dataset
    # For now, we return a minimal mock structure that matches the expected API
    # The actual data loading would happen in the real pipeline
    logger = setup_logger()
    logger.info("Loading NRC Lexicon (mock structure for testing)")
    return {
        'happy': {'joy': 1, 'sadness': 0},
        'sad': {'joy': 0, 'sadness': 1},
        'angry': {'anger': 1},
        'love': {'joy': 1, 'trust': 1}
    }

def load_vader_lexicon() -> Dict[str, float]:
    """Load the VADER Sentiment Lexicon.
    
    Returns:
        Dict mapping words to sentiment scores.
    """
    logger = setup_logger()
    logger.info("Loading VADER Lexicon (mock structure for testing)")
    return {
        'happy': 0.8,
        'sad': -0.6,
        'angry': -0.7,
        'love': 0.9
    }

def tokenize(text: str) -> List[str]:
    """Tokenize text into words.
    
    Args:
        text: Input text string.
        
    Returns:
        List of lowercase tokens.
    """
    if 'nltk' in sys.modules:
        try:
            return word_tokenize(text.lower())
        except Exception:
            pass
    # Fallback to regex tokenization
    return re.findall(r'\b\w+\b', text.lower())

def calculate_nrc_coverage(text: str, nrc_lexicon: Dict[str, Dict[str, int]]) -> float:
    """Calculate the coverage of NRC lexicon in text.
    
    Args:
        text: Input text string.
        nrc_lexicon: NRC lexicon dictionary.
        
    Returns:
        Float between 0 and 1 representing coverage.
    """
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    
    covered = sum(1 for token in tokens if token in nrc_lexicon)
    return covered / len(tokens)

def get_nrc_valence(text: str, nrc_lexicon: Dict[str, Dict[str, int]]) -> float:
    """Calculate NRC-based valence for text.
    
    Args:
        text: Input text string.
        nrc_lexicon: NRC lexicon dictionary.
        
    Returns:
        Float representing valence score.
    """
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    
    # Simple valence calculation: average of joy - sadness
    scores = []
    for token in tokens:
        if token in nrc_lexicon:
            emotions = nrc_lexicon[token]
            joy = emotions.get('joy', 0)
            sadness = emotions.get('sadness', 0)
            scores.append(joy - sadness)
    
    if not scores:
        return 0.0
    return sum(scores) / len(scores)

def get_vader_valence(text: str, vader_lexicon: Dict[str, float]) -> float:
    """Calculate VADER-based valence for text.
    
    Args:
        text: Input text string.
        vader_lexicon: VADER lexicon dictionary.
        
    Returns:
        Float representing valence score.
    """
    tokens = tokenize(text)
    if not tokens:
        return 0.0
    
    scores = []
    for token in tokens:
        if token in vader_lexicon:
            scores.append(vader_lexicon[token])
    
    if not scores:
        return 0.0
    return sum(scores) / len(scores)

def log_lexicon_switch(from_lexicon: str, to_lexicon: str, coverage: float) -> None:
    """Log a lexicon switch event.
    
    Args:
        from_lexicon: Name of the original lexicon.
        to_lexicon: Name of the fallback lexicon.
        coverage: The coverage that triggered the switch.
    """
    logger = setup_logger()
    logger.info(f"Lexicon switch: {from_lexicon} -> {to_lexicon} (coverage: {coverage:.2f})")
    
    # Log to runtime events
    project_root = get_project_root()
    state_dir = project_root / 'state'
    state_dir.mkdir(exist_ok=True)
    
    events_file = state_dir / 'runtime_events.json'
    events = []
    if events_file.exists():
        try:
            with open(events_file, 'r') as f:
                events = json.load(f)
        except (json.JSONDecodeError, IOError):
            events = []
    
    events.append({
        'event': 'lexicon_switch',
        'from': from_lexicon,
        'to': to_lexicon,
        'coverage': coverage
    })
    
    with open(events_file, 'w') as f:
        json.dump(events, f, indent=2)

def main():
    """Main function for valence calculation."""
    logger = setup_logger()
    logger.info("Valence calculation module loaded successfully")
    
    # Example usage
    sample_text = "This is a happy and loving headline"
    nrc_lex = load_nrc_lexicon()
    vader_lex = load_vader_lexicon()
    
    coverage = calculate_nrc_coverage(sample_text, nrc_lex)
    logger.info(f"NRC coverage: {coverage:.2f}")
    
    if coverage < 0.5:
        log_lexicon_switch("NRC", "VADER", coverage)
        valence = get_vader_valence(sample_text, vader_lex)
        logger.info(f"Using VADER valence: {valence:.2f}")
    else:
        valence = get_nrc_valence(sample_text, nrc_lex)
        logger.info(f"Using NRC valence: {valence:.2f}")

if __name__ == "__main__":
    main()
