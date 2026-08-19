"""
Validators.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import jsonschema

def validate_dataset_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    return True

def validate_correlation_results_schema(df: pd.DataFrame) -> bool:
    return True

def validate_model_metrics_schema(metrics: Dict[str, Any]) -> bool:
    return True

def validate_file_exists(path: Path) -> bool:
    return path.exists()

def validate_dataframe_not_empty(df: pd.DataFrame) -> bool:
    return not df.empty
