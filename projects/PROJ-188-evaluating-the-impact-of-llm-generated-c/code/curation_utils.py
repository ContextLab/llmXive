import re
import logging

logger = logging.getLogger(__name__)

def calculate_cyclomatic_complexity(code: str) -> float:
    """
    Calculate cyclomatic complexity score for a code snippet.
    Counts decision points: if, elif, for, while, except, and, or.
    Returns a float score.
    """
    if not code or not isinstance(code, str):
        return 0.0
    
    # Base complexity is 1
    complexity = 1.0
    
    # Decision point patterns
    patterns = [
        r'\bif\b',
        r'\belif\b',
        r'\bfor\b',
        r'\bwhile\b',
        r'\bexcept\b',
        r'\band\b',
        r'\bor\b'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, code)
        complexity += len(matches)
    
    return complexity

def label_complexity(score: float) -> str:
    """
    Label complexity based on raw score.
    low: score < 5
    medium: 5 <= score <= 10
    high: score > 10
    """
    if score < 5:
        return "low"
    elif score <= 10:
        return "medium"
    else:
        return "high"
