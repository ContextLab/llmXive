import os
import sys
import logging
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

import pandas as pd
import nltk
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk import download
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Attempt to download necessary NLTK data
try:
    download('punkt', quiet=True)
    download('wordnet', quiet=True)
    download('averaged_perceptron_tagger', quiet=True)
except Exception:
    pass

class ValenceCalculationError(Exception):
    """Custom exception for valence calculation errors."""
    pass

def get_project_root() -> Path:
    """Returns the project root directory."""
    current_file = Path(__file__).resolve()
    # Assuming standard structure: code/03_valence_calculation.py
    # Project root is parent of 'code'
    return current_file.parent.parent

def setup_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Sets up a logger with console and optional file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

def load_nrc_lexicon() -> Dict[str, Dict[str, int]]:
    """
    Loads the NRC Emotion Lexicon.
    Since we cannot rely on external files not in the repo, we construct a minimal
    representative lexicon or attempt to download it via NLTK if available in the environment.
    For this implementation, we will use a robust fallback strategy:
    1. Try to load from a local file if it exists (as per typical pipeline setup).
    2. If not, we will construct a small, deterministic subset of NRC-like mappings
       to demonstrate the logic, but primarily rely on VADER if the "real" NRC
       is not present. However, the task requires calculating coverage against NRC.
    
    To satisfy the "Real Data" constraint without a specific file path in the prompt:
    We will attempt to load 'NRC-Emotion-Lexicon-Wordlevel-v0.92.txt' from data/raw or similar.
    If that fails, we will simulate the *structure* but mark coverage as low to trigger VADER,
    UNLESS we can find a pip-installable source.
    
    Since no specific NRC file is provided in the 'Existing project API surface' or 'Full contents',
    and we cannot fabricate data, we will implement the loader to expect the file at:
    data/raw/NRC-Emotion-Lexicon-Wordlevel-v0.92.txt
    If it's missing, we raise an error or return an empty lexicon (which triggers VADER).
    
    However, the prompt says "Use NRC... with fallback".
    Let's try to load it. If not found, we return an empty dict, which results in 0% coverage,
    triggering the VADER fallback immediately. This is a valid execution path.
    """
    project_root = get_project_root()
    # Common locations for NRC
    possible_paths = [
        project_root / "data" / "raw" / "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt",
        project_root / "data" / "raw" / "nrc_lexicon.txt",
        project_root / "code" / "data" / "NRC-Emotion-Lexicon-Wordlevel-v0.92.txt",
    ]

    lexicon = {}
    found = False

    for path in possible_paths:
        if path.exists():
            found = True
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        word = parts[0].lower()
                        # NRC format: word, emotion, value (0 or 1)
                        # We want valence: positive/negative.
                        # NRC has "positive" and "negative" columns effectively.
                        # We'll store valence: 1 for positive, -1 for negative, 0 for neutral
                        # But for coverage, we just need to know if the word is in the lexicon.
                        lexicon[word] = lexicon.get(word, {})
                        if len(parts) >= 3:
                            val = int(parts[2])
                            emotion = parts[1].lower()
                            lexicon[word][emotion] = val
            break
    
    if not found:
        logging.warning("NRC Lexicon file not found. Coverage will be 0%. Falling back to VADER.")
        return {}

    return lexicon

def load_vader_lexicon() -> SentimentIntensityAnalyzer:
    """Initializes the VADER sentiment analyzer."""
    return SentimentIntensityAnalyzer()

def tokenize(text: str) -> List[str]:
    """Tokenizes text into words, lowercasing and removing punctuation."""
    text = text.lower()
    # Simple regex tokenization
    tokens = re.findall(r'\b[a-z]+\b', text)
    return tokens

def calculate_nrc_coverage(headlines: List[str], nrc_lexicon: Dict[str, Dict]) -> Tuple[float, List[float]]:
    """
    Calculates the percentage of unique words in headlines that match the NRC lexicon.
    Returns global average coverage and list of individual coverages.
    """
    if not nrc_lexicon:
        return 0.0, [0.0] * len(headlines)

    total_coverage = 0.0
    individual_coverages = []

    for headline in headlines:
        tokens = tokenize(headline)
        if not tokens:
            individual_coverages.append(0.0)
            continue

        unique_words = set(tokens)
        matched_words = sum(1 for word in unique_words if word in nrc_lexicon)
        coverage = (matched_words / len(unique_words)) * 100.0
        individual_coverages.append(coverage)
        total_coverage += coverage

    global_avg = total_coverage / len(headlines) if headlines else 0.0
    return global_avg, individual_coverages

def get_nrc_valence(text: str, nrc_lexicon: Dict[str, Dict]) -> float:
    """
    Calculates valence score based on NRC lexicon.
    Returns a score between -1 (negative) and 1 (positive).
    """
    if not nrc_lexicon:
        return 0.0

    tokens = tokenize(text)
    pos_count = 0
    neg_count = 0

    for token in tokens:
        if token in nrc_lexicon:
            # NRC has 'positive' and 'negative' keys usually
            entry = nrc_lexicon[token]
            if entry.get('positive', 0) == 1:
                pos_count += 1
            if entry.get('negative', 0) == 1:
                neg_count += 1

    total = pos_count + neg_count
    if total == 0:
        return 0.0
    
    return (pos_count - neg_count) / total

def get_vader_valence(text: str, analyzer: SentimentIntensityAnalyzer) -> float:
    """
    Calculates valence score using VADER.
    Returns compound score between -1 and 1.
    """
    scores = analyzer.polarity_scores(text)
    return scores['compound']

def log_lexicon_switch(from_lex: str, to_lex: str, coverage: float, state_dir: Path):
    """
    Logs a lexicon switch event to state/runtime_events.json.
    """
    events_file = state_dir / "runtime_events.json"
    
    events = []
    if events_file.exists():
        try:
            with open(events_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    events = json.loads(content)
                if not isinstance(events, list):
                    events = [events]
        except json.JSONDecodeError:
            events = []

    events.append({
        "event": "lexicon_switch",
        "from": from_lex,
        "to": to_lex,
        "coverage": round(coverage, 4)
    })

    state_dir.mkdir(parents=True, exist_ok=True)
    with open(events_file, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2)

def main():
    """Main execution function for T021."""
    logger = setup_logger("valence_calculation")
    project_root = get_project_root()

    # Paths
    input_path = project_root / "data" / "derived" / "empirical_outcomes.csv"
    output_path = project_root / "data" / "derived" / "valence_scores.csv"
    state_dir = project_root / "state"

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T004b has completed successfully.")

    logger.info(f"Loading empirical outcomes from {input_path}")
    df = pd.read_csv(input_path)

    required_cols = ['headline_text']
    for col in required_cols:
        if col not in df.columns:
            raise ValenceCalculationError(f"Required column '{col}' missing in {input_path}")

    logger.info(f"Loaded {len(df)} rows.")

    # Load Lexicons
    logger.info("Loading NRC Lexicon...")
    nrc_lexicon = load_nrc_lexicon()
    
    logger.info("Loading VADER Analyzer...")
    vader_analyzer = load_vader_lexicon()

    # Calculate Coverage
    logger.info("Calculating NRC coverage...")
    headlines = df['headline_text'].tolist()
    global_coverage, _ = calculate_nrc_coverage(headlines, nrc_lexicon)
    logger.info(f"Global NRC Coverage: {global_coverage:.2f}%")

    use_vader = False
    if global_coverage < 50.0:
        logger.warning(f"Coverage ({global_coverage:.2f}%) is below 50%. Switching to VADER for all headlines.")
        use_vader = True
        log_lexicon_switch("NRC", "VADER", global_coverage, state_dir)
    else:
        logger.info("Coverage is sufficient. Using NRC.")

    # Calculate Valence
    valence_scores = []
    for text in headlines:
        if use_vader:
            score = get_vader_valence(text, vader_analyzer)
        else:
            score = get_nrc_valence(text, nrc_lexicon)
        valence_scores.append(score)

    # Create Output DataFrame
    # Schema: headline_id, valence_score (based on T023 requirements)
    # Note: empirical_outcomes.csv has participant_id, headline_id, belief_rating, headline_text
    # We need to output valence per headline_id. If multiple rows per headline_id exist,
    # we should probably take the mean or just map it.
    # T023 expects: valence_scores.csv (headline_id, valence_score)
    
    output_df = pd.DataFrame({
        'headline_id': df['headline_id'],
        'valence_score': valence_scores
    })

    # If there are duplicate headline_ids, we might need to aggregate or keep unique.
    # T023 expects a merge on headline_id. Usually valence is per stimulus (headline), not per participant.
    # So we should deduplicate by headline_id, taking the mean score if multiple participants saw the same headline.
    if output_df['headline_id'].duplicated().any():
        logger.info("Deduplicating valence scores by headline_id (taking mean).")
        output_df = output_df.groupby('headline_id', as_index=False)['valence_score'].mean()

    output_df = output_df.sort_values('headline_id').reset_index(drop=True)

    # Write Output
    state_dir.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Valence scores written to {output_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
