"""
Semantic Similarity Validation
Uses sentence-transformers to ensure perturbed prompts are semantically similar
to the original.

STRICT CONSTRAINT: Primary set retains only perturbations with score > 0.95.
FALLBACK LOGIC: If the valid yield is < 20% of the total task count, the system
MUST re-evaluate the raw candidate pool with a threshold of > 0.90 to ensure
a minimum sample size for feasibility, as authorized by plan.md.

This module provides the core validation logic used by the perturbation pipeline.
It must be integrated with the generation and filtering stages.
"""

import torch
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import SentenceTransformer, util
from config import ensure_directories
from utils.logging import get_perturbation_logger

logger = get_perturbation_logger()
MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def get_model() -> SentenceTransformer:
    """
    Lazy loads the sentence transformer model.
    Raises an error if the model cannot be loaded from the real source.
    """
    global _model
    if _model is None:
        logger.info(f"Loading model: {MODEL_NAME}")
        try:
            # This fetches the model from the Hugging Face Hub (real source)
            _model = SentenceTransformer(MODEL_NAME)
            _model.eval()
            logger.info("Model loaded successfully from real source.")
        except Exception as e:
            # Fail loudly: do not fallback to synthetic or mock
            logger.error(f"CRITICAL: Failed to load real model source {MODEL_NAME}: {e}")
            raise RuntimeError(f"Failed to load required semantic model: {e}")
    return _model

def compute_similarity(text1: str, text2: str, model: Optional[SentenceTransformer] = None) -> float:
    """
    Computes cosine similarity between two texts.
    Returns a float between -1 and 1.
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
        # Fail loudly on computation error
        logger.error(f"Error computing similarity: {e}")
        raise RuntimeError(f"Similarity computation failed: {e}")

def validate_perturbation(
    original: str, 
    perturbed: str, 
    threshold: float = 0.95
) -> Tuple[bool, float]:
    """
    Validates a single perturbation against the strict threshold.
    Returns (is_valid, score).
    
    STRICT CONSTRAINT: Only scores > threshold are considered valid for the primary set.
    """
    score = compute_similarity(original, perturbed)
    is_valid = score > threshold
    if not is_valid:
        logger.debug(f"Perturbation failed semantic check: {score:.4f} <= {threshold}")
    return is_valid, score

def validate_perturbation_batch(
    original: str, 
    candidates: List[str], 
    threshold: float = 0.95
) -> List[Tuple[str, float, bool]]:
    """
    Validates a batch of candidates against the strict threshold.
    Returns list of (candidate, score, is_valid).
    """
    results = []
    for cand in candidates:
        is_valid, score = validate_perturbation(original, cand, threshold)
        results.append((cand, score, is_valid))
    return results

def evaluate_feasibility(
    candidates_with_scores: List[Tuple[str, float, bool]],
    total_tasks: int
) -> Tuple[float, bool]:
    """
    Evaluates if the current threshold yields enough valid candidates.
    
    Args:
        candidates_with_scores: List of (candidate, score, is_valid) tuples.
        total_tasks: Total number of original tasks attempted.
        
    Returns:
        Tuple of (yield_percentage, is_feasible).
        is_feasible is True if yield >= 20%.
    """
    valid_count = sum(1 for _, _, is_valid in candidates_with_scores if is_valid)
    # Calculate yield based on total tasks (assuming max 3 candidates per task)
    # But the constraint says "valid yield < 20% of the total task count"
    # So we compare valid candidates to total tasks.
    yield_percentage = (valid_count / total_tasks) * 100 if total_tasks > 0 else 0.0
    is_feasible = yield_percentage >= 20.0
    
    logger.info(f"Feasibility check: {valid_count} valid / {total_tasks} tasks = {yield_percentage:.2f}%")
    return yield_percentage, is_feasible

def main():
    """CLI test for the validator using real data simulation."""
    ensure_directories()
    model = get_model()
    
    # Real-world style test cases
    t1 = "Write a function to sort a list of integers in ascending order."
    t2 = "Create a function that sorts a list of integers from smallest to largest."
    t3 = "This is completely different text unrelated to sorting."
    
    s1 = compute_similarity(t1, t2, model)
    s2 = compute_similarity(t1, t3, model)
    
    print(f"Similarity (t1, t2 - semantic match): {s1:.4f}")
    print(f"Similarity (t1, t3 - semantic mismatch): {s2:.4f}")
    
    # Validate against strict threshold
    valid1, _ = validate_perturbation(t1, t2, threshold=0.95)
    valid2, _ = validate_perturbation(t1, t3, threshold=0.95)
    
    print(f"t2 passes >0.95 check: {valid1}")
    print(f"t3 passes >0.95 check: {valid2}")

if __name__ == "__main__":
    main()