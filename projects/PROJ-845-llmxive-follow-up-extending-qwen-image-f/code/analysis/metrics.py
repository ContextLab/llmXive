import math
import sys
from typing import List, Dict, Any, Optional
from collections import Counter

from utils.logger import get_logger

logger = get_logger(__name__)

def compute_entropy(text: str) -> float:
    """
    Compute the Shannon entropy of a given string (tokenized by characters).
    
    Args:
        text (str): The input text string.
        
    Returns:
        float: The calculated entropy value.
    """
    if not text:
        return 0.0
    
    freq = Counter(text)
    length = len(text)
    entropy = 0.0
    
    for count in freq.values():
        if count > 0:
            prob = count / length
            entropy -= prob * math.log2(prob)
            
    return float(entropy)

def compute_entropy_statistics(
    high_entropy_scores: List[float],
    low_entropy_scores: List[float]
) -> Dict[str, Any]:
    """
    Calculate mean, std, and perform a two-sample t-test between high and low entropy groups.
    Logs the results and enforces the controlled-entropy requirement (T015-ENFORCE).
    
    Args:
        high_entropy_scores (List[float]): Entropy scores for the high entropy group.
        low_entropy_scores (List[float]): Entropy scores for the low entropy group.
        
    Returns:
        Dict[str, Any]: Dictionary containing mean, std, t-statistic, and p-value.
        
    Raises:
        SystemExit: If the t-test p-value >= 0.05, indicating failure to separate entropy groups.
    """
    import statistics
    from scipy import stats

    if not high_entropy_scores or not low_entropy_scores:
        logger.warning("One or both entropy score lists are empty. Cannot compute statistics.")
        result = {
            "mean_high": 0.0,
            "std_high": 0.0,
            "mean_low": 0.0,
            "std_low": 0.0,
            "t_statistic": 0.0,
            "p_value": 1.0
        }
        logger.error(f"Entropy Statistics Validation FAILED: Missing data. Stats: {result}")
        sys.exit(1)

    mean_high = statistics.mean(high_entropy_scores)
    std_high = statistics.stdev(high_entropy_scores) if len(high_entropy_scores) > 1 else 0.0
    
    mean_low = statistics.mean(low_entropy_scores)
    std_low = statistics.stdev(low_entropy_scores) if len(low_entropy_scores) > 1 else 0.0

    # Perform two-sample t-test (assuming unequal variances)
    t_stat, p_val = stats.ttest_ind(high_entropy_scores, low_entropy_scores, equal_var=False)

    result = {
        "mean_high": float(mean_high),
        "std_high": float(std_high),
        "mean_low": float(mean_low),
        "std_low": float(std_low),
        "t_statistic": float(t_stat),
        "p_value": float(p_val)
    }

    # Log results
    logger.info(f"Entropy Statistics: High (mean={mean_high:.4f}, std={std_high:.4f}), "
                f"Low (mean={mean_low:.4f}, std={std_low:.4f})")
    logger.info(f"T-test Result: t={t_stat:.4f}, p-value={p_val:.4f}")

    # T015-ENFORCE: Fail if p-value >= 0.05
    if p_val >= 0.05:
        logger.error(f"ENTROPY SEPARATION FAILED: p-value ({p_val:.4f}) >= 0.05. "
                     f"The generated high and low entropy groups are not statistically distinct.")
        sys.exit(1)
    
    logger.info("Entropy separation validation PASSED (p-value < 0.05).")
    return result