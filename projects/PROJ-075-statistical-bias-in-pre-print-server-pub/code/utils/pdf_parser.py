"""
PDF Parser Module for Statistical Bias Analysis.

This module provides robust regex and NLP extraction logic for p-values and effect sizes
from PDF text, including handling of LaTeX formatting and interval-censored data.
"""

import re
from typing import List, Tuple, Optional, Dict, Any
import numpy as np

# Constants for regex patterns
# Matches LaTeX math mode p-values: p < 0.05, p = 0.03, p > 0.1, etc.
# Also handles common variations like "P-value", "p-value", "p value"
P_VALUE_PATTERN = re.compile(
    r'\b[pP]\s*(?:-value)?\s*(?:=\s*|<\s*|>\s*|≤\s*|≥\s*|!=\s*)\s*'
    r'(\d+(?:\.\d+)?(?:e[+-]?\d+)?)',
    re.IGNORECASE
)

# Matches interval-censored p-values: p < .05, p < 0.001, p > 0.1
P_INEQUALITY_PATTERN = re.compile(
    r'\b[pP]\s*(?:-value)?\s*(<|>|≤|≥|!=)\s*(\d+(?:\.\d+)?)',
    re.IGNORECASE
)

# Effect size patterns: Cohen's d, Hedges' g, eta-squared, etc.
EFFECT_SIZE_PATTERN = re.compile(
    r'\b(?:Cohen\'?s?\s*d|Hedges\'?\s*g|eta\s*[-\s]*squared|η²|r|omega\s*[-\s]*squared)\s*'
    r'[=:]\s*(-?\d+(?:\.\d+)?)',
    re.IGNORECASE
)

# Confidence interval pattern: 95% CI [0.5, 1.2]
CI_PATTERN = re.compile(
    r'\b(\d+)%\s*CI\s*(?:\(|\[)\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*(?:\)|\])',
    re.IGNORECASE
)

# LaTeX math delimiters
LATEX_MATH_PATTERN = re.compile(r'\$(.*?)\$')

def extract_latex_math(text: str) -> List[str]:
    """
    Extract all content within LaTeX math delimiters ($...$).

    Args:
        text: The input text containing LaTeX formatting.

    Returns:
        List of extracted math strings.
    """
    return LATEX_MATH_PATTERN.findall(text)

def clean_latex_formatting(text: str) -> str:
    """
    Remove LaTeX formatting characters from text for easier regex matching.

    Args:
        text: Text potentially containing LaTeX markup.

    Returns:
        Cleaned text with LaTeX markup removed.
    """
    # Remove common LaTeX math delimiters and commands
    text = re.sub(r'\$+', ' ', text)
    text = re.sub(r'\\[a-zA-Z]+', ' ', text)  # Remove LaTeX commands like \alpha
    text = re.sub(r'\\[{}]', ' ', text)  # Remove braces and backslashes
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text.strip()

def parse_inequality(inequality_str: str) -> Tuple[float, float, str]:
    """
    Parse inequality strings into bounds and type.

    Args:
        inequality_str: String like "p < 0.05" or "p > 0.1".

    Returns:
        Tuple of (lower_bound, upper_bound, inequality_type).
        For "p < 0.05": returns (0.0, 0.05, "left_censored")
        For "p > 0.1": returns (0.1, 1.0, "right_censored")
    """
    match = re.search(r'([<>=!≤≥]+)\s*(\d+(?:\.\d+)?)', inequality_str, re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not parse inequality: {inequality_str}")

    operator = match.group(1)
    value = float(match.group(2))

    if operator in ['<', '≤']:
        return (0.0, value, "left_censored")
    elif operator in ['>', '≥']:
        return (value, 1.0, "right_censored")
    elif operator in ['!=']:
        return (0.0, 1.0, "exclusion")
    else:
        return (value, value, "exact")

def extract_p_values(text: str) -> List[Dict[str, Any]]:
    """
    Extract p-values from text, handling both exact values and inequalities.

    Args:
        text: The text to search for p-values.

    Returns:
        List of dictionaries with p-value information:
        - value: The numeric value (or None for inequalities)
        - inequality: The inequality operator (if any)
        - raw: The original matched string
        - type: "exact" or "inequality"
    """
    results = []

    # First, try to extract exact p-values
    for match in P_VALUE_PATTERN.finditer(text):
        try:
            value = float(match.group(1))
            if 0.0 <= value <= 1.0:
                results.append({
                    'value': value,
                    'inequality': None,
                    'raw': match.group(0),
                    'type': 'exact'
                })
        except ValueError:
            continue

    # Then, extract inequality p-values
    for match in P_INEQUALITY_PATTERN.finditer(text):
        operator = match.group(1)
        value = float(match.group(2))
        results.append({
            'value': None,
            'inequality': operator,
            'raw': match.group(0),
            'type': 'inequality',
            'bounds': parse_inequality(match.group(0))
        })

    return results

def extract_effect_sizes(text: str) -> List[Dict[str, Any]]:
    """
    Extract effect sizes from text.

    Args:
        text: The text to search for effect sizes.

    Returns:
        List of dictionaries with effect size information:
        - type: The type of effect size (e.g., "Cohen's d", "Hedges' g")
        - value: The numeric value
        - raw: The original matched string
    """
    results = []

    for match in EFFECT_SIZE_PATTERN.finditer(text):
        # Determine effect size type from the matched text
        full_match = match.group(0)
        if 'Cohen' in full_match:
            es_type = 'Cohen\'s d'
        elif 'Hedges' in full_match:
            es_type = "Hedges' g"
        elif 'eta' in full_match.lower() or 'η' in full_match:
            es_type = 'eta-squared'
        elif 'r' in full_match.lower():
            es_type = 'correlation r'
        elif 'omega' in full_match.lower():
            es_type = 'omega-squared'
        else:
            es_type = 'unknown'

        try:
            value = float(match.group(1))
            results.append({
                'type': es_type,
                'value': value,
                'raw': match.group(0)
            })
        except ValueError:
            continue

    return results

def extract_confidence_intervals(text: str) -> List[Dict[str, Any]]:
    """
    Extract confidence intervals from text.

    Args:
        text: The text to search for confidence intervals.

    Returns:
        List of dictionaries with CI information:
        - confidence_level: The percentage (e.g., 95)
        - lower: Lower bound
        - upper: Upper bound
        - raw: The original matched string
    """
    results = []

    for match in CI_PATTERN.finditer(text):
        try:
            confidence_level = int(match.group(1))
            lower = float(match.group(2))
            upper = float(match.group(3))
            results.append({
                'confidence_level': confidence_level,
                'lower': lower,
                'upper': upper,
                'raw': match.group(0)
            })
        except ValueError:
            continue

    return results

def extract_statistics_from_pdf_text(text: str) -> Dict[str, Any]:
    """
    Main extraction function that combines all statistical extractions.

    Args:
        text: The full text extracted from a PDF.

    Returns:
        Dictionary containing all extracted statistics:
        - p_values: List of extracted p-values
        - effect_sizes: List of extracted effect sizes
        - confidence_intervals: List of extracted confidence intervals
        - raw_text_snippets: Snippets of text where statistics were found
    """
    # Clean LaTeX formatting for better matching
    cleaned_text = clean_latex_formatting(text)

    # Also extract from raw LaTeX math if present
    latex_math_sections = extract_latex_math(text)
    if latex_math_sections:
        cleaned_text += ' ' + ' '.join(latex_math_sections)

    p_values = extract_p_values(cleaned_text)
    effect_sizes = extract_effect_sizes(cleaned_text)
    confidence_intervals = extract_confidence_intervals(cleaned_text)

    return {
        'p_values': p_values,
        'effect_sizes': effect_sizes,
        'confidence_intervals': confidence_intervals,
        'total_p_values': len(p_values),
        'exact_p_values': len([p for p in p_values if p['type'] == 'exact']),
        'censored_p_values': len([p for p in p_values if p['type'] == 'inequality']),
        'total_effect_sizes': len(effect_sizes)
    }

def filter_p_values_for_analysis(p_values: List[Dict[str, Any]], exclude_inequalities: bool = True) -> List[float]:
    """
    Filter p-values for specific analysis requirements.

    Args:
        p_values: List of extracted p-value dictionaries.
        exclude_inequalities: If True, exclude interval-censored values (for p-curve).

    Returns:
        List of numeric p-values suitable for analysis.
    """
    if exclude_inequalities:
        return [p['value'] for p in p_values if p['type'] == 'exact' and p['value'] is not None]
    else:
        # For general reporting, we might want to keep inequalities as their bounds
        # For now, return only exact values
        return [p['value'] for p in p_values if p['value'] is not None]

def get_effect_size_by_type(effect_sizes: List[Dict[str, Any]], es_type: str) -> Optional[float]:
    """
    Get the first effect size of a specific type.

    Args:
        effect_sizes: List of extracted effect size dictionaries.
        es_type: The type of effect size to retrieve (e.g., "Cohen's d").

    Returns:
        The numeric value of the first matching effect size, or None if not found.
    """
    for es in effect_sizes:
        if es['type'].lower() == es_type.lower():
            return es['value']
    return None

def is_valid_p_value_range(p_values: List[Dict[str, Any]], min_p: float = 0.0, max_p: float = 1.0) -> bool:
    """
    Validate that all p-values fall within a valid range.

    Args:
        p_values: List of extracted p-value dictionaries.
        min_p: Minimum allowed p-value.
        max_p: Maximum allowed p-value.

    Returns:
        True if all p-values are valid, False otherwise.
    """
    for p in p_values:
        if p['value'] is not None:
            if not (min_p <= p['value'] <= max_p):
                return False
    return True