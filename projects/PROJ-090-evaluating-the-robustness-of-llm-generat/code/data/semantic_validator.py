"""
Semantic Similarity Validation
Uses sentence-transformers to ensure perturbed prompts are semantically similar
to the original.
"""

import torch
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer, util
from config import ensure_directories
from utils.logging import get_perturbation_logger

logger = get_perturbation_logger()
MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def get_model() -> SentenceTransformer:
    """
    Lazy loads the sentence transformer model.
    """
    global _model
    if _model is None:
        logger.info(f"Loading model: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        _model.eval()
        logger.info("Model loaded successfully.")
    return _model

def compute_similarity(text1: str, text2: str, model: Optional[SentenceTransformer] = None) -> float:
    """
    Computes cosine similarity between two texts.
    """
    if model is None:
        model = get_model()
    
    try:
        embedding1 = model.encode(text1, convert_to_tensor=True)
        embedding2 = model.encode(text2, convert_to_tensor=True)
        
        # Ensure same device
        device = next(model.parameters()).device
        if embedding1.device != device:
            embedding1 = embedding1.to(device)
        if embedding2.device != device:
            embedding2 = embedding2.to(device)

        similarity = util.cos_sim(embedding1, embedding2)
        return float(similarity.item())
    except Exception as e:
        logger.error(f"Error computing similarity: {e}")
        return 0.0

def validate_perturbation(
    original: str, 
    perturbed: str, 
    threshold: float = 0.95
) -> Tuple[bool, float]:
    """
    Validates a single perturbation against the threshold.
    Returns (is_valid, score).
    """
    score = compute_similarity(original, perturbed)
    return score > threshold, score

def validate_perturbation_batch(
    original: str, 
    candidates: List[str], 
    threshold: float = 0.95
) -> List[Tuple[str, float, bool]]:
    """
    Validates a batch of candidates.
    Returns list of (candidate, score, is_valid).
    """
    results = []
    for cand in candidates:
        is_valid, score = validate_perturbation(original, cand, threshold)
        results.append((cand, score, is_valid))
    return results

def main():
    """CLI test for the validator."""
    ensure_directories()
    model = get_model()
    t1 = "The quick brown fox jumps over the lazy dog."
    t2 = "A fast brown fox leaped over the sleepy dog."
    t3 = "This is completely different text."
    
    s1 = compute_similarity(t1, t2, model)
    s2 = compute_similarity(t1, t3, model)
    
    print(f"Similarity (t1, t2): {s1:.4f}")
    print(f"Similarity (t1, t3): {s2:.4f}")

if __name__ == "__main__":
    main()