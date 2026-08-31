import logging
import json
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from radon.raw import analyze as radon_analyze

logger = logging.getLogger(__name__)

def compute_radon_metrics_safe(code: str) -> Dict[str, Any]:
    """
    Safely compute Radon metrics, returning defaults on error.
    """
    try:
        result = radon_analyze(code)
        return {
            "loc": result.loc,
            "lloc": result.lloc,
            "sloc": result.sloc,
            "complexity": result.complexity
        }
    except Exception as e:
        logger.warning(f"Radon analysis failed: {e}")
        return {"loc": 0, "lloc": 0, "sloc": 0, "complexity": 0}

def validate_dataset_completeness(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that a DataFrame has all required columns and no missing values.
    """
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing columns: {missing_cols}")
        return False
    
    if df.isnull().any().any():
        logger.warning("Dataset contains missing values")
        return False
    
    return True

def safe_json_parse(text: str) -> Optional[Dict[str, Any]]:
    """
    Safely parse JSON, returning None on failure.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None

def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of values.
    """
    if not values:
        return {"mean": 0, "std": 0, "min": 0, "max": 0}
    
    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr))
    }

def parse_smell_labels(labels_str: str) -> List[str]:
    """
    Parse a string of smell labels (e.g., "['LongMethod', 'ComplexCondition']")
    into a list of strings.
    """
    if not labels_str or labels_str == "None":
        return []
    try:
        # Handle string representation of list
        return json.loads(labels_str.replace("'", '"'))
    except Exception:
        return labels_str.split(",")

def create_detection_matrix(static_labels: List[str], semantic_labels: List[str]) -> Dict[str, int]:
    """
    Create a detection matrix counting overlaps.
    """
    static_set = set(static_labels)
    semantic_set = set(semantic_labels)
    
    return {
        "both": len(static_set & semantic_set),
        "static_only": len(static_set - semantic_set),
        "semantic_only": len(semantic_set - static_set),
        "neither": 0 # Calculated based on total
    }