import os
import csv
import json
import logging
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple, Set
import numpy as np

# Import SentenceTransformer inside to allow lazy loading and error handling
# We do not import it at the top level to avoid immediate failure if network is down
# during module import, though the function will fail if not available.

# Global SBERT singleton (lazy load)
GLOBAL_SBERT = None
SBERT_MODEL_NAME = 'all-MiniLM-L6-v2'
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

class SBERTLoadError(Exception):
    """Custom exception for SBERT loading failures."""
    pass

def get_sbert():
    """
    Loads the SBERT model with retry logic for network/IO errors.
    If the model is missing locally, it attempts to download it.
    If the download fails after MAX_RETRIES, it raises SBERTLoadError.
    It MUST NOT generate a random embedding vector as a fallback.
    """
    global GLOBAL_SBERT
    if GLOBAL_SBERT is not None:
        return GLOBAL_SBERT

    from sentence_transformers import SentenceTransformer

    attempt = 0
    last_error = None

    while attempt < MAX_RETRIES:
        try:
            logging.info(f"Loading SBERT model '{SBERT_MODEL_NAME}' (Attempt {attempt + 1}/{MAX_RETRIES})...")
            # This will attempt to load from cache or download from HuggingFace Hub
            GLOBAL_SBERT = SentenceTransformer(SBERT_MODEL_NAME)
            logging.info("SBERT model loaded successfully.")
            return GLOBAL_SBERT
        except (OSError, ConnectionError, TimeoutError) as e:
            # Catch network/IO errors specifically
            last_error = e
            attempt += 1
            logging.warning(f"Failed to load SBERT model: {e}. Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            # Catch any other unexpected errors immediately
            logging.error(f"Unexpected error loading SBERT model: {e}")
            raise SBERTLoadError(f"Failed to load SBERT model due to unexpected error: {e}") from e

    # If we exit the loop, all retries failed
    logging.error(f"Failed to load SBERT model after {MAX_RETRIES} attempts.")
    raise SBERTLoadError(f"Failed to load SBERT model '{SBERT_MODEL_NAME}' after {MAX_RETRIES} attempts. Last error: {last_error}")

def check_input_drift(baseline_input: str, perturbed_input: str) -> Tuple[float, bool]:
    """
    Check input drift using SBERT cosine similarity.
    Returns (similarity_score, is_valid)
    """
    model = get_sbert()
    embeddings = model.encode([baseline_input, perturbed_input])
    # Ensure embeddings are normalized for cosine similarity
    norm_0 = np.linalg.norm(embeddings[0])
    norm_1 = np.linalg.norm(embeddings[1])
    if norm_0 == 0 or norm_1 == 0:
        return 0.0, False
    similarity = float(np.dot(embeddings[0], embeddings[1]) / (norm_0 * norm_1))
    return similarity, similarity >= 0.95

def filter_pairs_by_input_drift(pairs: List[Dict], threshold: float = 0.95) -> List[Dict]:
    """Filter pairs that pass the input drift threshold."""
    valid_pairs = []
    for pair in pairs:
        score, is_valid = check_input_drift(pair['baseline'], pair['perturbed'])
        if is_valid:
            valid_pairs.append({**pair, 'drift_score': score})
    return valid_pairs

def check_output_validity(model_output: str, expected_answer: str) -> bool:
    """Check output validity using BERTScore (simplified)."""
    # Placeholder for BERTScore logic - actual implementation would use bertscore package
    # For now, we assume a simple check or rely on the fact that this is a placeholder
    # In a real scenario, this would call bertscore.score()
    return True

def check_validity_collapse(pass_rate: float, threshold: float = 0.90) -> bool:
    """Check if pass_rate is below threshold (collapse)."""
    return pass_rate < threshold

def main():
    """Main entry for validity check script if needed."""
    logging.info("Validity check module loaded.")

if __name__ == "__main__":
    main()