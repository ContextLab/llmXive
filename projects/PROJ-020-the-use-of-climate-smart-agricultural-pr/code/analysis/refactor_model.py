"""
Refactored model utilities for cleaner, more maintainable statistical analysis code.
Provides helper functions for model specification and diagnostics.
"""
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
from typing import List, Dict, Optional, Tuple, Any
import logging
import re

logger = logging.getLogger(__name__)


def create_interaction_formula(
    base_predictors: List[str],
    interaction_predictors: List[str],
    outcome: str
) -> str:
    """
    Create a statsmodels formula string with interaction terms.
    
    Args:
        base_predictors: List of main effect predictor names
        interaction_predictors: List of predictor names to include in interactions
        outcome: Name of the outcome variable
        
    Returns:
        Formula string suitable for statsmodels
    """
    # Build main effects
    main_effects = " + ".join(base_predictors)
    
    # Build interaction terms (all pairwise combinations)
    interactions = []
    for i, p1 in enumerate(interaction_predictors):
        for p2 in interaction_predictors[i+1:]:
            interactions.append(f"{p1}:{p2}")
    
    # Combine
    if interactions:
        full_predictors = f"{main_effects} + {' + '.join(interactions)}"
    else:
        full_predictors = main_effects
    
    return f"{outcome} ~ {full_predictors}"


def create_formula_with_controls(
    outcome: str,
    primary_predictor: str,
    control_predictors: List[str],
    interaction_terms: Optional[List[str]] = None,
    random_effects: Optional[List[str]] = None
) -> str:
    """
    Create a flexible formula string for mixed effects models.
    
    Args:
        outcome: Name of the outcome variable
        primary_predictor: Main predictor of interest
        control_predictors: List of control variable names
        interaction_terms: List of variables to interact with primary predictor
        random_effects: List of grouping variables for random effects
        
    Returns:
        Formula string
    """
    # Start with outcome
    formula = f"{outcome} ~ {primary_predictor}"
    
    # Add control predictors
    if control_predictors:
        formula += " + " + " + ".join(control_predictors)
    
    # Add interaction terms
    if interaction_terms:
        for term in interaction_terms:
            formula += f" + {primary_predictor}:{term}"
    
    # Add random effects if specified (for mixed models)
    if random_effects:
        # For statsmodels mixedlm, random effects are specified separately
        # This returns the fixed effects formula
        pass
    
    return formula


def sanitize_formula_string(formula: str) -> str:
    """
    Sanitize a formula string to ensure it's valid for statsmodels.
    
    Args:
        formula: Raw formula string
        
    Returns:
        Sanitized formula string
    """
    # Remove extra whitespace
    formula = re.sub(r'\s+', ' ', formula).strip()
    
    # Ensure no trailing operators
    formula = re.sub(r'[+\-*\/]\s*$', '', formula)
    
    # Ensure no leading operators after ~
    formula = re.sub(r'~\s*([+\-*\/])', r'~ \1', formula)
    
    return formula


def check_formula_validity(formula: str) -> Tuple[bool, List[str]]:
    """
    Check if a formula string is valid and return any issues.
    
    Args:
        formula: Formula string to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check for empty formula
    if not formula.strip():
        issues.append("Formula is empty")
        return False, issues
    
    # Check for missing outcome
    if '~' not in formula:
        issues.append("Formula missing '~' separator")
        return False, issues
    
    parts = formula.split('~')
    if len(parts) != 2:
        issues.append(f"Formula has multiple '~' separators: {formula}")
        return False, issues
    
    outcome, predictors = parts
    if not outcome.strip():
        issues.append("Missing outcome variable")
    
    if not predictors.strip():
        issues.append("Missing predictor variables")
    
    # Check for invalid characters
    invalid_chars = re.findall(r'[^\w\s\+\-\*\/\:\(\)\.\[\]]', predictors)
    if invalid_chars:
        issues.append(f"Invalid characters in predictors: {set(invalid_chars)}")
    
    return len(issues) == 0, issues


def extract_predictor_names(formula: str) -> Dict[str, List[str]]:
    """
    Extract predictor names from a formula string.
    
    Args:
        formula: Formula string
        
    Returns:
        Dictionary with 'main_effects', 'interactions', and 'all' keys
    """
    if '~' not in formula:
        return {'main_effects': [], 'interactions': [], 'all': []}
    
    parts = formula.split('~')
    if len(parts) != 2:
        return {'main_effects': [], 'interactions': [], 'all': []}
    
    predictors = parts[1]
    
    # Split by +
    terms = [t.strip() for t in predictors.split('+')]
    
    main_effects = []
    interactions = []
    
    for term in terms:
        if ':' in term:
            interactions.append(term)
        else:
            # Remove any function calls like log(x) or I(x)
            clean_term = re.sub(r'\w+\(([^)]+)\)', r'\1', term)
            main_effects.append(clean_term.strip())
    
    all_predictors = main_effects + interactions
    
    return {
        'main_effects': main_effects,
        'interactions': interactions,
        'all': all_predictors
    }


def format_model_summary(summary_text: str, max_lines: int = 20) -> str:
    """
    Format model summary text for logging, truncating if too long.
    
    Args:
        summary_text: Raw summary string from model
        max_lines: Maximum number of lines to include
        
    Returns:
        Formatted summary string
    """
    lines = summary_text.split('\n')
    
    if len(lines) <= max_lines:
        return summary_text
    
    # Keep header and last few lines
    header_lines = lines[:5]
    footer_lines = lines[-5:]
    ellipsis = ["...", "...", "..."]
    
    return '\n'.join(header_lines + ellipsis + footer_lines)


def safe_model_fit(
    model_func: callable,
    data: pd.DataFrame,
    formula: str,
    max_attempts: int = 3,
    **kwargs
) -> Optional[Any]:
    """
    Safely fit a model with retry logic and error handling.
    
    Args:
        model_func: Function to fit the model (e.g., smf.ols)
        data: DataFrame with data
        formula: Model formula
        max_attempts: Maximum number of retry attempts
        **kwargs: Additional arguments to pass to model_func
        
    Returns:
        Fitted model results or None if all attempts fail
    """
    last_error = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Fitting model (attempt {attempt}/{max_attempts})")
            model = model_func(formula, data=data, **kwargs)
            results = model.fit()
            logger.info("Model fitted successfully")
            return results
        except Exception as e:
            last_error = e
            logger.warning(f"Model fitting failed (attempt {attempt}): {str(e)}")
            if attempt < max_attempts:
                import time
                time.sleep(1)  # Brief pause before retry
    
    logger.error(f"All {max_attempts} attempts to fit model failed")
    return None
