import re
from typing import List, Union, Dict
import sacrebleu
import logging

logger = logging.getLogger(__name__)

def calculate_bleu(references: List[str], candidate: str) -> float:
    """
    Calculate BLEU score between references and candidate.
    
    Args:
        references: List of reference strings (docstrings).
        candidate: The candidate string (LLM explanation).
        
    Returns:
        BLEU score (0-100).
    """
    if not references or not candidate:
        logger.warning("Empty references or candidate provided to BLEU calculation.")
        return 0.0
    
    try:
        # sacrebleu.sentence_bleu expects references as a list of lists for multiple refs,
        # or a list of strings if treating them as a single list of refs for one sentence.
        # The API signature in the provided stub was: sacrebleu.sentence_bleu(candidate, references)
        # We ensure references is a list of strings.
        bleu_score = sacrebleu.sentence_bleu(candidate, references).score
        return float(bleu_score)
    except Exception as e:
        logger.error(f"Error calculating BLEU score: {e}")
        return 0.0

def parse_latency_to_ms(latency_str: str) -> int:
    """
    Parse latency string to milliseconds.
    
    Args:
        latency_str: String containing a number and a unit (ms, s, min).
        
    Returns:
        Latency in milliseconds.
        
    Raises:
        ValueError: If the format is invalid.
    """
    if not latency_str:
        raise ValueError("Latency string is empty.")
        
    match = re.search(r'(\d+(?:\.\d+)?)\s*(ms|s|min)', latency_str, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid latency format: {latency_str}. Expected format: '123 ms', '1.5 s', etc.")
    
    value = float(match.group(1))
    unit = match.group(2).lower()
    
    if unit == 's':
        return int(value * 1000)
    elif unit == 'min':
        return int(value * 60 * 1000)
    return int(value)

def calculate_latency_stats(latencies: List[int]) -> Dict[str, float]:
    """
    Calculate statistics for a list of latency values (in ms).
    
    Args:
        latencies: List of latency values in milliseconds.
        
    Returns:
        Dictionary with mean, median, std, min, max.
    """
    if not latencies:
        logger.warning("Empty latencies list provided to stats calculation.")
        return {"mean": 0.0, "median": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    
    n = len(latencies)
    mean_val = sum(latencies) / n
    sorted_latencies = sorted(latencies)
    median_val = sorted_latencies[n // 2]
    
    # Population standard deviation
    variance = sum((x - mean_val) ** 2 for x in latencies) / n
    std_val = variance ** 0.5
    
    return {
        "mean": mean_val,
        "median": float(median_val),
        "std": std_val,
        "min": float(min(latencies)),
        "max": float(max(latencies))
    }
