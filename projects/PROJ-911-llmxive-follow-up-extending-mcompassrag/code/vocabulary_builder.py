import json
import re
from collections import Counter
from typing import List, Dict, Any, Set

from sklearn.feature_extraction.text import TfidfVectorizer

from code.config import PROCESSED_DIR, RANDOM_SEED


def clean_text(text: str) -> str:
    """
    Clean and normalize text for vocabulary building.
    - Lowercase
    - Remove non-alphanumeric characters (keeping spaces)
    - Collapse whitespace
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def build_fixed_vocabulary(corpus: List[str], max_vocab_size: int = 10000) -> Set[str]:
    """
    Build a fixed reference vocabulary from the corpus using TF-IDF filtering.
    
    This function:
    1. Cleans the text of all documents in the corpus.
    2. Fits a TfidfVectorizer to identify terms with sufficient document frequency.
    3. Selects the top `max_vocab_size` terms by total TF-IDF score (or frequency).
    4. Returns the set of selected terms.
    
    Args:
        corpus: List of raw text documents.
        max_vocab_size: Maximum number of terms to include in the fixed vocabulary.
        
    Returns:
        A set of term strings representing the fixed vocabulary.
    """
    if not corpus:
        return set()
    
    # Clean the corpus
    cleaned_corpus = [clean_text(doc) for doc in corpus]
    cleaned_corpus = [doc for doc in cleaned_corpus if doc] # Remove empty strings
    
    if not cleaned_corpus:
        return set()

    # Use TfidfVectorizer to identify relevant terms
    # We use min_df=2 to avoid noise from terms appearing only once,
    # and max_df=0.95 to avoid overly common stop words.
    vectorizer = TfidfVectorizer(
        max_features=max_vocab_size,
        min_df=2,
        max_df=0.95,
        token_pattern=r'(?u)\b\w+\b', # Ensure we capture words correctly
        lowercase=False # We already lowercased
    )
    
    try:
        tfidf_matrix = vectorizer.fit_transform(cleaned_corpus)
    except ValueError:
        # Fallback if corpus is too small or invalid for vectorizer
        return set()
    
    feature_names = vectorizer.get_feature_names_out()
    
    # Calculate total TF-IDF score for each term to rank them
    # Summing the TF-IDF values across all documents gives a measure of importance
    total_scores = tfidf_matrix.sum(axis=0).A1 # .A1 converts matrix to 1D array
    
    # Sort terms by their total score
    sorted_indices = total_scores.argsort()[::-1]
    
    # Select the top terms
    top_terms = [feature_names[i] for i in sorted_indices]
    
    return set(top_terms)


def save_vocabulary(vocab_set: Set[str], output_path: str) -> None:
    """
    Save the vocabulary set to a JSON file.
    
    Args:
        vocab_set: The set of vocabulary terms.
        output_path: Path to the output JSON file.
    """
    # Convert set to sorted list for deterministic output
    sorted_vocab = sorted(list(vocab_set))
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_vocab, f, indent=2)


def run_pipeline(corpus: List[str], output_filename: str = "fixed_vocab.json") -> str:
    """
    Run the vocabulary building pipeline.
    
    Args:
        corpus: List of raw text documents.
        output_filename: Name of the output file (saved in PROCESSED_DIR).
        
    Returns:
        Path to the created vocabulary file.
    """
    import logging
    from pathlib import Path
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Building fixed vocabulary from {len(corpus)} documents...")
    
    vocab_set = build_fixed_vocabulary(corpus)
    
    output_path = Path(PROCESSED_DIR) / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    save_vocabulary(vocab_set, str(output_path))
    
    logger.info(f"Vocabulary saved to {output_path} with {len(vocab_set)} terms.")
    
    return str(output_path)
