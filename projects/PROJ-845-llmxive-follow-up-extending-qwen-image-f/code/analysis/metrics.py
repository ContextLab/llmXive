import math
from collections import Counter
from typing import List, Dict, Any, Tuple

def compute_entropy(tokens: List[str]) -> float:
    """
    Compute Shannon entropy of a list of tokens.
    
    Args:
        tokens: List of string tokens.
    
    Returns:
        Shannon entropy as a float.
    """
    if not tokens:
        return 0.0
    
    counts = Counter(tokens)
    total = len(tokens)
    entropy = 0.0
    
    for count in counts.values():
        if count > 0:
            prob = count / total
            entropy -= prob * math.log2(prob)
    
    return entropy

def compute_trace_entropy(problem: Dict[str, Any], trace: List[str]) -> float:
    """
    Compute Shannon entropy of token-level probabilities from a teacher trace.
    
    The trace is expected to be a list of strings where each string represents
    a step or token in the Chain-of-Thought. If the trace contains probability
    strings (e.g., "0.85"), they are parsed. Otherwise, the entropy of the 
    token distribution (frequency-based) is returned as a proxy for uncertainty.
    
    Args:
        problem: The SyntheticProblem dictionary (used to validate context if needed).
        trace: List of tokens or probability strings from the teacher trace.
    
    Returns:
        Shannon entropy as a float.
    """
    if not trace:
        return 0.0
    
    # Attempt to parse probabilities if the trace looks like it contains them
    # If the trace contains floats/strings representing probabilities, we calculate entropy
    # based on the distribution of those probabilities relative to the max possible (1.0)
    # or simply treat the frequency of tokens as the distribution if not.
    
    # Strategy: 
    # 1. Check if trace items look like probabilities (0.0 to 1.0 floats).
    # 2. If so, normalize them to sum to 1.0 and compute entropy.
    # 3. If not, treat them as categorical tokens and compute frequency entropy.
    
    probs = []
    is_prob_trace = True
    
    for item in trace:
        try:
            val = float(item)
            if 0.0 <= val <= 1.0:
                probs.append(val)
            else:
                is_prob_trace = False
                break
        except (ValueError, TypeError):
            is_prob_trace = False
            break
    
    if is_prob_trace and len(probs) > 0:
        total_prob = sum(probs)
        if total_prob == 0:
            return 0.0
        
        # Normalize to form a valid probability distribution
        normalized_probs = [p / total_prob for p in probs]
        
        entropy = 0.0
        for p in normalized_probs:
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    # Fallback: Compute frequency-based entropy (Shannon entropy of token distribution)
    return compute_entropy(trace)

def compute_entropy_statistics(
    high_entropy_scores: List[float],
    low_entropy_scores: List[float]
) -> Dict[str, Any]:
    """
    Compute statistics for two groups of entropy scores.
    
    Performs a two-sample t-test (approximate) and returns means, stds, and p-value.
    
    Args:
        high_entropy_scores: List of entropy scores for the high entropy group.
        low_entropy_scores: List of entropy scores for the low entropy group.
    
    Returns:
        Dictionary with mean, std, and p-value.
    """
    if not high_entropy_scores or not low_entropy_scores:
        return {
            "high_mean": None,
            "high_std": None,
            "low_mean": None,
            "low_std": None,
            "p_value": None,
            "conclusion": "Insufficient data for t-test"
        }

    n1 = len(high_entropy_scores)
    n2 = len(low_entropy_scores)
    
    mean1 = sum(high_entropy_scores) / n1
    mean2 = sum(low_entropy_scores) / n2
    
    var1 = sum((x - mean1) ** 2 for x in high_entropy_scores) / (n1 - 1) if n1 > 1 else 0
    var2 = sum((x - mean2) ** 2 for x in low_entropy_scores) / (n2 - 1) if n2 > 1 else 0
    
    std1 = math.sqrt(var1)
    std2 = math.sqrt(var2)
    
    # Welch's t-test approximation
    se = math.sqrt((var1 / n1) + (var2 / n2))
    if se == 0:
        t_stat = 0.0
    else:
        t_stat = (mean1 - mean2) / se
    
    try:
        from scipy import stats
        t_stat, p_val = stats.ttest_ind(high_entropy_scores, low_entropy_scores, equal_var=False)
    except ImportError:
        # Fallback: Z-test approximation for large N
        p_val = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
    
    return {
        "high_mean": mean1,
        "high_std": std1,
        "low_mean": mean2,
        "low_std": std2,
        "p_value": p_val,
        "conclusion": "Significant" if p_val < 0.05 else "Not Significant"
    }