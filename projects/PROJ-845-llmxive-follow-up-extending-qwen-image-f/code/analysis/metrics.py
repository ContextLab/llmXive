import math
from collections import Counter
from typing import List, Dict, Any, Tuple
import statistics

# Add project root to path
import os
import sys
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from models.synthetic_problem import SyntheticProblem
from utils.logger import get_logger

logger = get_logger("metrics")

def compute_entropy(text: str) -> float:
    """
    Compute Shannon entropy of a string.
    
    Args:
        text: Input string
        
    Returns:
        Entropy value (float)
    """
    if not text:
        return 0.0
    
    # Count character frequencies
    freq = Counter(text)
    total_chars = len(text)
    
    # Compute entropy
    entropy = 0.0
    for count in freq.values():
        if count > 0:
            prob = count / total_chars
            entropy -= prob * math.log2(prob)
    
    return entropy

def compute_trace_entropy(problem: SyntheticProblem, trace: List[str]) -> float:
    """
    Measure Shannon entropy of token-level probabilities from the teacher trace.
    
    Args:
        problem: The synthetic problem
        trace: List of trace steps
        
    Returns:
        Entropy value (float)
    """
    if not trace:
        return 0.0
    
    # Combine all trace steps into one text
    full_trace = " ".join(trace)
    
    # Compute entropy based on word frequencies
    words = full_trace.split()
    if not words:
        return 0.0
    
    word_freq = Counter(words)
    total_words = len(words)
    
    entropy = 0.0
    for count in word_freq.values():
        if count > 0:
            prob = count / total_words
            entropy -= prob * math.log2(prob)
    
    return entropy

def compute_entropy_statistics(
    problems: List[SyntheticProblem]
) -> Dict[str, Any]:
    """
    Calculate per-sample entropy scores and perform statistical tests.
    
    Args:
        problems: List of synthetic problems
        
    Returns:
        Dictionary with statistics and test results
    """
    if not problems:
        return {
            "mean": 0.0,
            "std": 0.0,
            "high_vs_low_p_value": None,
            "sample_size": 0
        }
    
    # Compute entropy for each problem
    entropies = []
    high_entropies = []
    low_entropies = []
    
    for problem in problems:
        # Combine premises and operators for entropy calculation
        text = " ".join(problem.premises + problem.operators)
        entropy = compute_entropy(text)
        entropies.append(entropy)
        
        if problem.entropy_level == "high":
            high_entropies.append(entropy)
        elif problem.entropy_level == "low":
            low_entropies.append(entropy)
    
    # Compute basic statistics
    mean_entropy = statistics.mean(entropies)
    std_entropy = statistics.stdev(entropies) if len(entropies) > 1 else 0.0
    
    # Perform t-test (high vs low)
    p_value = None
    if len(high_entropies) > 1 and len(low_entropies) > 1:
        # Simple t-test implementation
        mean_high = statistics.mean(high_entropies)
        mean_low = statistics.mean(low_entropies)
        
        var_high = statistics.variance(high_entropies)
        var_low = statistics.variance(low_entropies)
        
        n_high = len(high_entropies)
        n_low = len(low_entropies)
        
        # Pooled standard error
        se = math.sqrt((var_high / n_high) + (var_low / n_low))
        
        if se > 0:
            t_stat = (mean_high - mean_low) / se
            # Approximate p-value using normal distribution (for large samples)
            # In production, use scipy.stats.ttest_ind
            p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    
    result = {
        "mean": mean_entropy,
        "std": std_entropy,
        "high_vs_low_p_value": p_value,
        "sample_size": len(problems),
        "high_entropy_count": len(high_entropies),
        "low_entropy_count": len(low_entropies),
        "high_mean": statistics.mean(high_entropies) if high_entropies else 0.0,
        "low_mean": statistics.mean(low_entropies) if low_entropies else 0.0
    }
    
    logger.info(f"Entropy statistics: mean={mean_entropy:.4f}, std={std_entropy:.4f}, p-value={p_value}")
    
    return result
