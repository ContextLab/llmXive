"""
Text parsing utilities for extracting statistical parameters.
"""
import re
from typing import Tuple, Optional, List

# Regex patterns for extraction
PATTERNS = {
    "sample_size": r"N[=:\s]*(\d+)",
    "cohens_d": r"Cohen['’]s?\s*d[=:\s]*([+-]?\d+\.?\d*)",
    "f_statistic": r"F\([(\s]*(\d+)[,\s]+(\d+)[)\s]*\)[=:\s]*([+-]?\d+\.?\d*)",
}

def extract_sample_size(text: str) -> int:
    """
    Extract sample size (N) from text.
    
    Args:
        text: The text to search.
        
    Returns:
        The sample size as an integer, or 0 if not found.
    """
    if not text:
        return 0
        
    match = re.search(PATTERNS["sample_size"], text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 0

def extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]:
    """
    Extract effect size (Cohen's d or F-statistic) from text.
    
    Args:
        text: The text to search.
        
    Returns:
        A tuple of (effect_value, metric_type, degrees_of_freedom).
        - metric_type is "Cohen's d" or "F".
        - degrees_of_freedom is a tuple (df1, df2) for F, None for Cohen's d.
        - Returns (0.0, "unknown", None) if not found.
    """
    if not text:
        return (0.0, "unknown", None)
        
    # Try Cohen's d first
    d_match = re.search(PATTERNS["cohens_d"], text, re.IGNORECASE)
    if d_match:
        return (float(d_match.group(1)), "Cohen's d", None)
        
    # Try F-statistic
    f_match = re.search(PATTERNS["f_statistic"], text, re.IGNORECASE)
    if f_match:
        df1 = int(f_match.group(1))
        df2 = int(f_match.group(2))
        value = float(f_match.group(3))
        return (value, "F", (df1, df2))
        
    return (0.0, "unknown", None)
