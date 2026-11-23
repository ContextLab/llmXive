import logging
import json
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from radon.raw import analyze as radon_analyze
from radon.complexity import cc_visit
from radon.visitors import ComplexityVisitor

logger = logging.getLogger(__name__)

def compute_radon_metrics_safe(code: str) -> Dict[str, Any]:
    """
    Safely computes radon metrics, returning defaults on failure.
    
    Calculates:
    - loc: Lines of code
    - cyclomatic_complexity: Cyclomatic complexity
    - nesting_depth: Maximum nesting depth of control structures
    
    Args:
        code: The source code string to analyze.
    
    Returns:
        Dictionary with 'loc', 'cyclomatic_complexity', and 'nesting_depth' keys.
    """
    try:
        result = radon_analyze(code)
        
        # Calculate nesting depth by visiting the AST
        max_nesting = 0
        try:
            visitor = ComplexityVisitor.from_code(code)
            # ComplexityVisitor doesn't directly give nesting depth, so we need a custom approach
            # We'll parse the AST manually for nesting depth
            import ast
            tree = ast.parse(code)
            
            def get_max_nesting(node, current_depth=0):
                nonlocal max_nesting
                max_nesting = max(max_nesting, current_depth)
                
                # Control flow nodes that increase nesting
                nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, 
                               ast.ExceptHandler, ast.AsyncFor, ast.AsyncWith)
                
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, nesting_nodes):
                        get_max_nesting(child, current_depth + 1)
                    else:
                        get_max_nesting(child, current_depth)
            
            get_max_nesting(tree)
        except Exception as e:
            logger.debug(f"Could not compute nesting depth: {e}")
            max_nesting = 0
        
        return {
            "loc": result.loc,
            "cyclomatic_complexity": result.complexity,
            "nesting_depth": max_nesting
        }
    except Exception as e:
        logger.warning(f"Radon analysis failed: {e}")
        return {"loc": 0, "cyclomatic_complexity": 0, "nesting_depth": 0}

def validate_dataset_completeness(df: pd.DataFrame, required_cols: List[str], threshold: float = 0.95) -> bool:
    """
    Validates that a dataset has the required columns and sufficient completeness.
    
    Args:
        df: DataFrame to validate.
        required_cols: List of column names that must be present and non-null.
        threshold: Minimum fraction of rows that must have all required columns.
    
    Returns:
        True if dataset meets completeness threshold, False otherwise.
    """
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        logger.error(f"Missing required columns: {missing}")
        return False
    
    non_null_count = df.dropna(subset=required_cols).shape[0]
    completeness = non_null_count / len(df) if len(df) > 0 else 0.0
    
    if completeness < threshold:
        logger.warning(f"Dataset completeness {completeness:.2f} is below threshold {threshold}")
        return False
    
    return True

def safe_json_parse(json_str: str) -> Optional[Any]:
    """
    Safely parses a JSON string, returning None on failure.
    
    Args:
        json_str: String containing JSON data.
    
    Returns:
        Parsed JSON object or None if parsing fails.
    """
    if not json_str or not isinstance(json_str, str):
        return None
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parsing failed: {e}")
        return None

def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculates basic statistics for a list of values.
    
    Args:
        values: List of numeric values.
    
    Returns:
        Dictionary with 'mean', 'std', 'min', 'max' keys.
    """
    if not values:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
        
    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr))
    }

def parse_smell_labels(labels_str: str) -> List[str]:
    """
    Parses a pipe-separated or comma-separated string of smell labels into a list.
    
    Args:
        labels_str: String containing smell labels separated by pipes or commas.
    
    Returns:
        List of cleaned smell label strings.
    """
    if not labels_str or labels_str == "":
        return []
    
    # Handle both pipe and comma separators
    if '|' in labels_str:
        separators = ['|']
    else:
        separators = [',']
        
    labels = []
    for sep in separators:
        parts = labels_str.split(sep)
        labels.extend([s.strip() for s in parts if s.strip()])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_labels = []
    for label in labels:
        if label not in seen:
            seen.add(label)
            unique_labels.append(label)
    
    return unique_labels

def create_detection_matrix(static_labels: List[str], llm_labels: List[str]) -> Dict[str, int]:
    """
    Creates a detection matrix for static vs LLM labels.
    
    Calculates overlap and unique detections between static analysis and LLM analysis.
    
    Args:
        static_labels: List of smell labels from static analysis.
        llm_labels: List of smell labels from LLM analysis.
    
    Returns:
        Dictionary with counts for 'both', 'static_only', 'llm_only', and 'neither'.
    """
    static_set = set(static_labels)
    llm_set = set(llm_labels)
    
    return {
        "both": len(static_set & llm_set),
        "static_only": len(static_set - llm_set),
        "llm_only": len(llm_set - static_set),
        "neither": 0 # Context dependent, usually not calculated per function
    }

def calculate_vif(features: pd.DataFrame) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) for each feature.
    
    VIF measures multicollinearity in regression analysis.
    VIF = 1 / (1 - R^2) where R^2 is from regressing one feature against others.
    
    Args:
        features: DataFrame with numeric features (no target variable).
    
    Returns:
        Dictionary mapping feature names to their VIF scores.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    if features.empty:
        return {}
    
    # Add constant for intercept
    features_with_const = sm.add_constant(features)
    
    vif_data = {}
    for i, col in enumerate(features.columns):
        vif = variance_inflation_factor(features_with_const.values, i + 1) # +1 because of constant
        vif_data[col] = float(vif)
    
    return vif_data

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divides two numbers, returning a default value on division by zero.
    
    Args:
        numerator: Numerator value.
        denominator: Denominator value.
        default: Value to return if denominator is zero.
    
    Returns:
        Result of division or default value.
    """
    if denominator == 0:
        return default
    return numerator / denominator
