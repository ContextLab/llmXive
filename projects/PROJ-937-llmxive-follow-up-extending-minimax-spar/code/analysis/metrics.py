import re
import logging
from typing import Tuple, Dict, Any, Optional

# Configure logging for the module
logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Normalize text for comparison by lowercasing and removing extra whitespace.
    """
    if not text:
        return ""
    text = text.lower()
    # Remove punctuation and extra whitespace
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def calculate_exact_match(pred: str, gold: str) -> float:
    """
    Calculate Exact Match score between prediction and gold standard.
    Returns 1.0 if normalized strings are identical, 0.0 otherwise.
    """
    norm_pred = normalize_text(pred)
    norm_gold = normalize_text(gold)
    return 1.0 if norm_pred == norm_gold else 0.0

def calculate_f1(pred: str, gold: str) -> float:
    """
    Calculate F1 score based on token overlap between prediction and gold.
    """
    norm_pred = normalize_text(pred)
    norm_gold = normalize_text(gold)
    
    if not norm_pred or not norm_gold:
        return 0.0

    pred_tokens = set(norm_pred.split())
    gold_tokens = set(norm_gold.split())

    if not pred_tokens or not gold_tokens:
        return 0.0

    intersection = pred_tokens.intersection(gold_tokens)
    precision = len(intersection) / len(pred_tokens)
    recall = len(intersection) / len(gold_tokens)

    if precision + recall == 0:
        return 0.0
    
    f1 = 2 * (precision * recall) / (precision + recall)
    return f1

def validate_threshold(value: float, threshold: float, tolerance: float = 0.02) -> Tuple[bool, float]:
    """
    Validate if a value is within a tolerance threshold of an expected value.
    
    Args:
        value: The measured value.
        threshold: The reference/expected value.
        tolerance: The maximum allowed relative difference (default 2%).
    
    Returns:
        Tuple of (is_valid, measured_delta)
        is_valid: True if |value - threshold| <= tolerance * threshold
        measured_delta: The actual relative difference
    """
    if threshold == 0:
        # If threshold is 0, any non-zero value fails unless value is also 0
        is_valid = (value == 0)
        measured_delta = 0.0 if is_valid else float('inf')
    else:
        measured_delta = abs(value - threshold) / abs(threshold)
        is_valid = measured_delta <= tolerance
    
    return is_valid, measured_delta

def validate_accuracy_delta(
    baseline_score: float, 
    heuristic_score: float, 
    tolerance: float = 0.02
) -> Dict[str, Any]:
    """
    Validate if the accuracy delta between baseline and heuristic exceeds tolerance.
    
    This function implements the validation logic for US1 to ensure the heuristic
    approximation stays within the 2% tolerance threshold.
    
    Args:
        baseline_score: The accuracy score from the dense baseline.
        heuristic_score: The accuracy score from the heuristic method.
        tolerance: The maximum allowed relative difference (default 0.02 for 2%).
    
    Returns:
        Dictionary containing:
            - 'is_within_tolerance': Boolean indicating if delta <= tolerance
            - 'measured_delta': The calculated relative difference
            - 'delta_percentage': Delta expressed as a percentage string
            - 'baseline_score': The input baseline score
            - 'heuristic_score': The input heuristic score
            - 'status': 'PASS' or 'FAIL'
    """
    is_valid, measured_delta = validate_threshold(
        heuristic_score, baseline_score, tolerance
    )
    
    delta_percentage = measured_delta * 100
    status = "PASS" if is_valid else "FAIL"
    
    result = {
        "is_within_tolerance": is_valid,
        "measured_delta": measured_delta,
        "delta_percentage": f"{delta_percentage:.2f}%",
        "baseline_score": baseline_score,
        "heuristic_score": heuristic_score,
        "status": status
    }
    
    logger.info(
        f"Validation Result: {status} | Baseline: {baseline_score:.4f}, "
        f"Heuristic: {heuristic_score:.4f}, Delta: {delta_percentage:.2f}%"
    )
    
    return result

def calculate_metrics(pred: str, gold: str) -> Dict[str, float]:
    """
    Calculate all relevant metrics for a single prediction.
    
    Args:
        pred: Model prediction string.
        gold: Gold standard string.
    
    Returns:
        Dictionary with 'exact_match' and 'f1' scores.
    """
    return {
        "exact_match": calculate_exact_match(pred, gold),
        "f1": calculate_f1(pred, gold)
    }