"""
Utility functions for data curation, specifically complexity calculation and labeling.
This module supports T013 (Complexity Labeling) and is tested by T009.
"""
import re
import logging

logger = logging.getLogger(__name__)

# Thresholds for cyclomatic complexity labeling
# Low: 1-5, Medium: 6-15, High: >15
COMPLEXITY_THRESHOLDS = {
    'low': 5,
    'medium': 15
}

def calculate_cyclomatic_complexity(code_snippet: str) -> int:
    """
    Calculate the cyclomatic complexity of a Python code snippet.
    
    This is a heuristic implementation that counts decision points:
    if, elif, for, while, except, and, or.
    
    Args:
        code_snippet: The Python code string to analyze.
        
    Returns:
        An integer representing the cyclomatic complexity.
    """
    if not code_snippet:
        return 1
        
    # Base complexity is 1
    complexity = 1
    
    # Keywords that increase complexity
    decision_keywords = [
        r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
        r'\bexcept\b', r'\band\b', r'\bor\b'
    ]
    
    for keyword in decision_keywords:
        matches = re.findall(keyword, code_snippet)
        complexity += len(matches)
        
    return complexity

def label_complexity(complexity_score: int) -> str:
    """
    Label the complexity based on the raw cyclomatic complexity score.
    
    Args:
        complexity_score: The raw integer complexity score.
        
    Returns:
        A string label: 'low', 'medium', or 'high'.
    """
    if complexity_score <= COMPLEXITY_THRESHOLDS['low']:
        return 'low'
    elif complexity_score <= COMPLEXITY_THRESHOLDS['medium']:
        return 'medium'
    else:
        return 'high'

def calculate_complexity_label(code_snippet: str) -> str:
    """
    Calculate the cyclomatic complexity of a code snippet and return its label.
    
    This is the primary function used by T009 to verify that the label
    is one of ['low', 'medium', 'high'].
    
    Args:
        code_snippet: The Python code string to analyze.
        
    Returns:
        A string label: 'low', 'medium', or 'high'.
    """
    score = calculate_cyclomatic_complexity(code_snippet)
    return label_complexity(score)
