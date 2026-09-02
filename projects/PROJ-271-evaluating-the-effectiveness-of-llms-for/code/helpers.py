import logging
import json
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from radon.raw import analyze as radon_analyze

logger = logging.getLogger(__name__)

def compute_radon_metrics_safe(code: str) -> Dict[str, Any]:
    """
    Safely computes radon metrics, returning defaults on failure.
    """
    try:
        result = radon_analyze(code)
        return {
            "loc": result.loc,
            "cyclomatic_complexity": result.complexity
        }
    except Exception as e:
        logger.warning(f"Radon analysis failed: {e}")
        return {"loc": 0, "cyclomatic_complexity": 0}

def validate_dataset_completeness(df: pd.DataFrame, required_cols: List[str], threshold: float = 0.95) -> bool:
    """
    Validates that a dataset has the required columns and sufficient completeness.
    """
    if not all(col in df.columns for col in required_cols):
        return False
    
    non_null_count = df.dropna(subset=required_cols).shape[0]
    completeness = non_null_count / len(df)
    
    if completeness < threshold:
        logger.warning(f"Dataset completeness {completeness:.2f} is below threshold {threshold}")
        return False
    
    return True

def safe_json_parse(json_str: str) -> Optional[Any]:
    """
    Safely parses a JSON string, returning None on failure.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None

def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculates basic statistics for a list of values.
    """
    arr = np.array(values)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr))
    }

def parse_smell_labels(labels_str: str) -> List[str]:
    """
    Parses a comma-separated string of smell labels into a list.
    """
    if not labels_str or labels_str == "":
        return []
    return [s.strip() for s in labels_str.split(",") if s.strip()]

def create_detection_matrix(static_labels: List[str], llm_labels: List[str]) -> Dict[str, int]:
    """
    Creates a detection matrix for static vs LLM labels.
    """
    static_set = set(static_labels)
    llm_set = set(llm_labels)
    
    return {
        "both": len(static_set & llm_set),
        "static_only": len(static_set - llm_set),
        "llm_only": len(llm_set - static_set),
        "neither": 0 # Context dependent
    }
