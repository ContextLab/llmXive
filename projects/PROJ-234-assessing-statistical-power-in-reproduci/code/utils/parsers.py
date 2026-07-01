"""
Parsers for extracting statistical parameters from publication text.

Exposes:
- extract_sample_size(text: str) -> int
- extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]
"""
import re
from typing import Tuple, Optional, List

# Regex patterns for statistical parameters
# Matches patterns like "N=100", "N = 100", "sample size = 50", "n=200"
SAMPLE_SIZE_PATTERN = re.compile(
    r'\b(?:N|n|sample\s*size|participants|subjects)\s*[=:]\s*(\d+)\b',
    re.IGNORECASE
)

# Matches Cohen's d: "Cohen's d = 0.5", "d = 0.5", "cohen's d=0.5"
COHENS_D_PATTERN = re.compile(
    r"(?:Cohen[''']?\s*s\s*d|d)\s*[=:]\s*(\d+\.?\d*)",
    re.IGNORECASE
)

# Matches F-statistic: "F(1, 20) = 4.5", "F(1,20)=4.5", "F( 1 , 20 ) = 4.5"
F_STATISTIC_PATTERN = re.compile(
    r"F\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*[=:]\s*(\d+\.?\d*)",
    re.IGNORECASE
)

def extract_sample_size(text: str) -> int:
    """
    Extract the sample size (N) from the given text.
    
    Args:
        text: The text content (abstract or full-text) to parse.
        
    Returns:
        The extracted sample size as an integer. Returns 0 if no match is found.
    """
    if not text:
        return 0
        
    matches = SAMPLE_SIZE_PATTERN.findall(text)
    if matches:
        # Return the first valid integer found (usually the most prominent N)
        try:
            return int(matches[0])
        except ValueError:
            return 0
    return 0

def extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]:
    """
    Extract effect size metrics from the given text.
    
    Priority:
    1. F-statistic (returns metric_type="F", includes degrees_of_freedom)
    2. Cohen's d (returns metric_type="Cohen's d", degrees_of_freedom=None)
    
    Args:
        text: The text content to parse.
        
    Returns:
        A tuple of (value, metric_type, degrees_of_freedom):
        - value: float (the numeric value of the effect size)
        - metric_type: str ("Cohen's d" or "F")
        - degrees_of_freedom: Optional[Tuple[int, int]] (df1, df2) if metric is "F", else None.
        
        If no effect size is found, returns (0.0, "None", None).
    """
    if not text:
        return (0.0, "None", None)

    # Try F-statistic first
    f_matches = F_STATISTIC_PATTERN.findall(text)
    if f_matches:
        # f_matches is a list of tuples (df1, df2, value)
        # We take the first occurrence
        df1, df2, value_str = f_matches[0]
        try:
            value = float(value_str)
            return (value, "F", (int(df1), int(df2)))
        except ValueError:
            pass

    # Try Cohen's d
    d_matches = COHENS_D_PATTERN.findall(text)
    if d_matches:
        try:
            value = float(d_matches[0])
            return (value, "Cohen's d", None)
        except ValueError:
            pass

    return (0.0, "None", None)
