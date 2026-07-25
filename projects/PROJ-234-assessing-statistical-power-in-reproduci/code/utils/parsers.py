"""
Text parsers for extracting statistical parameters from publication text.
"""
import re
from typing import Tuple, Optional, List

# Regex patterns
SAMPLE_SIZE_PATTERN = re.compile(r'\bN\s*=\s*(\d+)\b', re.IGNORECASE)
# Patterns for Cohen's d and F-statistic
COHENS_D_PATTERN = re.compile(r"Cohen['']?\s*d\s*=\s*([\d.]+)", re.IGNORECASE)
F_STAT_PATTERN = re.compile(r"F\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*=\s*([\d.]+)", re.IGNORECASE)

def extract_sample_size(text: str) -> int:
    """
    Extract sample size (N) from text.
    
    Args:
        text: The text to parse.
        
    Returns:
        The sample size as an integer, or 0 if not found.
    """
    match = SAMPLE_SIZE_PATTERN.search(text)
    if match:
        return int(match.group(1))
    return 0

def extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]:
    """
    Extract effect size (Cohen's d or F-statistic) from text.
    
    Args:
        text: The text to parse.
        
    Returns:
        A tuple: (value, metric_type, degrees_of_freedom).
        - value: The numeric value of the effect size.
        - metric_type: "Cohen's d" or "F".
        - degrees_of_freedom: Tuple (df1, df2) if F-statistic, else None.
    """
    # Check for F-statistic first
    f_match = F_STAT_PATTERN.search(text)
    if f_match:
        df1 = int(f_match.group(1))
        df2 = int(f_match.group(2))
        value = float(f_match.group(3))
        return (value, "F", (df1, df2))

    # Check for Cohen's d
    d_match = COHENS_D_PATTERN.search(text)
    if d_match:
        value = float(d_match.group(1))
        return (value, "Cohen's d", None)

    return (0.0, "", None)
