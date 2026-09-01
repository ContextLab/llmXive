import logging
import json
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import numpy as np
from radon.raw import analyze as radon_analyze


def compute_radon_metrics_safe(code: str) -> Dict[str, Any]:
    """
    Safely compute radon metrics. Returns default values on error.
    """
    try:
        result = radon_analyze(code)
        return {
            "loc": result.loc,
            "cyclomatic_complexity": result.complexity,
            "nesting_depth": result.max_nesting
        }
    except Exception as e:
        logging.getLogger(__name__).warning(f"Radon analysis failed: {e}")
        return {"loc": 0, "cyclomatic_complexity": 0, "nesting_depth": 0}


def validate_dataset_completeness(df: pd.DataFrame, required_columns: List[str]) -> float:
    """
    Validate that a dataset has all required columns and calculate completeness.
    """
    if not all(col in df.columns for col in required_columns):
        return 0.0

    completeness = df.dropna(subset=required_columns).shape[0] / df.shape[0]
    return completeness


def safe_json_parse(json_str: str) -> Optional[Any]:
    """
    Safely parse JSON string. Returns None on error.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def calculate_statistics(values: List[float]) -> Dict[str, float]:
    """
    Calculate basic statistics for a list of values.
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
    Parse comma-separated smell labels string into a list.
    """
    if not labels_str or labels_str == "":
        return []
    return [label.strip() for label in labels_str.split(",") if label.strip()]


def create_detection_matrix(df: pd.DataFrame, smell_category: str) -> Dict[str, int]:
    """
    Create a 2x2 detection matrix for a specific smell category.
    Returns: {"both": int, "static_only": int, "llm_only": int, "neither": int}
    """
    # Parse static and LLM labels
    static_detected = df["static_smell_labels"].apply(lambda x: smell_category in parse_smell_labels(x))
    llm_detected = df["llm_smell_labels"].apply(lambda x: smell_category in parse_smell_labels(x))

    both = ((static_detected) & (llm_detected)).sum()
    static_only = ((static_detected) & (~llm_detected)).sum()
    llm_only = ((~static_detected) & (llm_detected)).sum()
    neither = ((~static_detected) & (~llm_detected)).sum()

    return {
        "both": int(both),
        "static_only": int(static_only),
        "llm_only": int(llm_only),
        "neither": int(neither)
    }
