import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import jsonschema

def validate_dataset_schema(df: pd.DataFrame, schema_path: Optional[Path] = None) -> bool:
    """Validates a DataFrame against a JSON schema."""
    # Basic checks
    required_cols = ["subject_id", "titer_baseline", "titer_post"]
    for col in required_cols:
        if col not in df.columns:
            return False
    
    # Check for nulls in required columns
    if df[required_cols].isnull().any().any():
        return False
    
    return True

def validate_correlation_results_schema(results: Dict[str, Any]) -> bool:
    """Validates correlation results dictionary."""
    required_keys = ["taxon", "coefficient", "raw_pvalue", "adj_pvalue"]
    if not isinstance(results, list):
        return False
    
    for item in results:
        if not all(k in item for k in required_keys):
            return False
    return True

def validate_model_metrics_schema(metrics: Dict[str, Any]) -> bool:
    """Validates model metrics dictionary."""
    required_keys = ["accuracy", "precision", "recall", "f1"]
    return all(k in metrics for k in required_keys)

def validate_file_exists(filepath: Path) -> bool:
    """Checks if a file exists."""
    return filepath.exists()

def validate_dataframe_not_empty(df: pd.DataFrame) -> bool:
    """Checks if a DataFrame has rows."""
    return len(df) > 0
