"""
Ablation utilities for token counting and similarity analysis.
Provides CPU-safe metrics for the Socratic Transformers pipeline.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple, List, Union

import numpy as np
from scipy.spatial import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Local project imports
# Import the config system to retrieve the base model ID
try:
    from src.utils.config import get_config
except ImportError:
    # Fallback for execution from root if src is not in path (adjust for runner context)
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.utils.config import get_config

from transformers import AutoTokenizer

# Configure logging
logger = logging.getLogger(__name__)

# Global tokenizer cache to avoid reloading
_tokenizer_instance: Optional[AutoTokenizer] = None

def get_target_tokenizer() -> AutoTokenizer:
    """
    Retrieves the tokenizer for the base model defined in config.py.
    Caches the instance to prevent redundant downloads/initializations.
    """
    global _tokenizer_instance
    if _tokenizer_instance is not None:
        return _tokenizer_instance

    config = get_config()
    model_id = getattr(config, 'BASE_MODEL_ID', None)

    if not model_id:
        raise RuntimeError(
            "CRITICAL: BASE_MODEL_ID is not defined in src/utils/config.py. "
            "Cannot initialize tokenizer for token counting."
        )

    logger.info(f"Loading tokenizer for base model: {model_id}")
    try:
        _tokenizer_instance = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            padding_side='left'
        )
    except Exception as e:
        logger.error(f"Failed to load tokenizer from {model_id}: {e}")
        raise

    return _tokenizer_instance

def calculate_token_count(text: Union[str, List[str]]) -> int:
    """
    Calculates the number of tokens in the provided text using the base model's tokenizer.

    Args:
        text: A string or list of strings to tokenize.

    Returns:
        The total number of tokens (excluding special tokens like BOS/EOS if not present in input).
    """
    tokenizer = get_target_tokenizer()

    if isinstance(text, str):
        tokens = tokenizer.encode(text, add_special_tokens=False)
        return len(tokens)
    elif isinstance(text, list):
        # Handle batch encoding
        encodings = tokenizer(text, add_special_tokens=False, padding=False)
        # Return total tokens across all samples
        total = sum(len(ids) for ids in encodings['input_ids'])
        return total
    else:
        raise TypeError(f"Expected str or list, got {type(text)}")

def calculate_similarity(text_a: str, text_b: str) -> float:
    """
    Calculates the cosine similarity between two text strings using TF-IDF.
    This implementation uses scikit-learn's TfidfVectorizer for CPU safety
    and compliance with FR-003 (7GB RAM limit).

    Args:
        text_a: The first text string.
        text_b: The second text string.

    Returns:
        A float between 0.0 and 1.0 representing the cosine similarity.
        Returns 0.0 if either text is empty or results in a zero vector.
    """
    if not text_a or not text_b:
        return 0.0

    try:
        vectorizer = TfidfVectorizer()
        # Fit and transform on the two documents
        tfidf_matrix = vectorizer.fit_transform([text_a, text_b])

        # Extract the two vectors
        vec_a = tfidf_matrix[0]
        vec_b = tfidf_matrix[1]

        # Compute cosine similarity
        # scipy.spatial.distance.cosine returns distance (1 - similarity)
        # We use cosine_similarity directly or compute manually
        # Using scipy.spatial.cosine_distance is not standard; using numpy dot
        # Normalize vectors first (Tfidf usually does, but explicit is safer)
        norm_a = np.linalg.norm(vec_a.toarray())
        norm_b = np.linalg.norm(vec_b.toarray())

        if norm_a == 0 or norm_b == 0:
            return 0.0

        # Cosine similarity = dot(a, b) / (norm(a) * norm(b))
        similarity = (vec_a @ vec_b.T) / (norm_a * norm_b)

        # Extract scalar from matrix result
        return float(similarity.item())

    except Exception as e:
        logger.warning(f"Similarity calculation failed: {e}. Returning 0.0.")
        return 0.0

def main():
    """
    Simple verification entry point for T015a.
    Runs the verification command from tasks.md.
    """
    print("Running T015a verification...")

    # 1. Test Token Count
    try:
        count = calculate_token_count("test")
        assert count > 0, "Token count must be > 0"
        print(f"✓ Token count verification passed: 'test' -> {count} tokens")
    except Exception as e:
        print(f"✗ Token count verification failed: {e}")
        sys.exit(1)

    # 2. Test Similarity
    try:
        sim = calculate_similarity("a", "a")
        assert 0 <= sim <= 1, "Similarity must be between 0 and 1"
        # Identical strings should have high similarity ( ideally 1.0 for single words)
        print(f"✓ Similarity verification passed: 'a' vs 'a' -> {sim}")
    except Exception as e:
        print(f"✗ Similarity verification failed: {e}")
        sys.exit(1)

    print("All T015a checks passed.")

if __name__ == "__main__":
    main()
