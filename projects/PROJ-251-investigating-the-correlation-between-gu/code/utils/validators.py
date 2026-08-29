import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import jsonschema
import yaml
from utils.logging_config import get_logger

logger = get_logger(__name__)

def validate_dataset_schema(df: pd.DataFrame, schema_path: Path) -> bool:
    """
    Validates a DataFrame against a JSON schema defined in a YAML file.
    This is a helper for unit tests or internal checks.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Basic checks
    required_fields = schema.get('required', [])
    missing_fields = [f for f in required_fields if f not in df.columns]
    
    if missing_fields:
        logger.error(f"Missing required columns: {missing_fields}")
        return False
    
    # Type checks for simple columns
    properties = schema.get('properties', {})
    for field, spec in properties.items():
        if field in df.columns:
            expected_type = spec.get('type')
            if expected_type == 'string':
                if not df[field].apply(lambda x: isinstance(x, str) or pd.isna(x)).all():
                    logger.warning(f"Column {field} contains non-string values")
            elif expected_type == 'number':
                if not pd.api.types.is_numeric_dtype(df[field]):
                    logger.warning(f"Column {field} is not numeric")
    
    return True

def validate_correlation_results_schema(data: Dict[str, Any]) -> bool:
    """Validates the structure of correlation results."""
    required_keys = ['taxon', 'coefficient', 'raw_pvalue', 'adj_pvalue']
    for key in required_keys:
        if key not in data:
            logger.error(f"Missing key in correlation results: {key}")
            return False
    return True

def validate_model_metrics_schema(data: Dict[str, Any]) -> bool:
    """Validates the structure of model metrics."""
    required_keys = ['accuracy', 'precision', 'recall', 'f1']
    for key in required_keys:
        if key not in data:
            logger.error(f"Missing key in model metrics: {key}")
            return False
    return True

def validate_file_exists(path: Path) -> bool:
    """Check if a file exists."""
    if not path.exists():
        logger.error(f"File not found: {path}")
        return False
    return True

def validate_dataframe_not_empty(df: pd.DataFrame, name: str = "DataFrame") -> bool:
    """Check if a DataFrame has rows."""
    if df.empty:
        logger.error(f"{name} is empty")
        return False
    return True
