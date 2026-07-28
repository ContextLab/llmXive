import os
import csv
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Set
from sentence_transformers import SentenceTransformer

# Global SBERT singleton (lazy load)
GLOBAL_SBERT = None

def get_sbert():
    global GLOBAL_SBERT
    if GLOBAL_SBERT is None:
        logging.info("Loading SBERT model...")
        GLOBAL_SBERT = SentenceTransformer('all-MiniLM-L6-v2')
    return GLOBAL_SBERT

def check_input_drift(baseline_input: str, perturbed_input: str) -> Tuple[float, bool]:
    """
    Check input drift using SBERT cosine similarity.
    Returns (similarity_score, is_valid)
    """
    model = get_sbert()
    embeddings = model.encode([baseline_input, perturbed_input])
    similarity = float(np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])))
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
    # Placeholder for BERTScore logic
    return True

def check_validity_collapse(pass_rate: float, threshold: float = 0.90) -> bool:
    """Check if pass_rate is below threshold (collapse)."""
    return pass_rate < threshold

def main():
    """Main entry for validity check script if needed."""
    logging.info("Validity check module loaded.")

if __name__ == "__main__":
    main()
