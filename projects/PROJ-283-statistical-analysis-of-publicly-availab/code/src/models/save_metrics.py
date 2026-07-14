"""
Module to save model artifacts (coefficients, p-values, R², AIC) to JSON
and validate against the model_output schema.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

import numpy as np
import pandas as pd

from src.config import get_contract_path, get_data_path
from src.validation.validate_contracts import validate_model_output, assert_model_output_valid

logger = logging.getLogger(__name__)


def _convert_numpy_types(obj: Any) -> Any:
    """
    Recursively convert numpy types to native Python types for JSON serialization.
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {k: _convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_numpy_types(i) for i in obj]
    else:
        return obj


def save_model_metrics(
    model_results: List[Dict[str, Any]],
    output_path: Optional[str] = None,
    validate: bool = True
) -> str:
    """
    Save model artifacts to a JSON file and optionally validate against the schema.

    Args:
        model_results: List of dictionaries containing model metrics. Each dict should
            contain keys like 'model_type', 'coefficients', 'p_values', 'r_squared', 'aic',
            'cross_validation_scores'.
        output_path: Path to the output JSON file. If None, uses default path from config.
        validate: If True, validate the output against model_output.schema.yaml.

    Returns:
        The path to the saved JSON file.

    Raises:
        ValueError: If model_results is empty or invalid.
        RuntimeError: If validation fails.
    """
    if not model_results:
        raise ValueError("model_results cannot be empty")

    # Determine output path
    if output_path is None:
        output_path = get_data_path("results/model_metrics.json")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Convert numpy types to native Python types for JSON serialization
    clean_results = _convert_numpy_types(model_results)

    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(clean_results, f, indent=2, default=str)

    logger.info(f"Saved model metrics to {output_file}")

    # Validate against schema if requested
    if validate:
        try:
            # Load the saved data back into a structured format for validation
            # The schema expects a list of records, which matches our structure
            with open(output_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Convert to DataFrame for validation (schema expects DataFrame columns)
            # The schema defines columns: model_type, coefficients, p_values, r_squared, aic, cross_validation_scores
            df = pd.DataFrame(loaded_data)
            
            # Validate using the contract validation function
            assert_model_output_valid(df)
            logger.info(f"Model metrics validated successfully against schema")
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise RuntimeError(f"Model metrics validation failed: {e}")

    return str(output_file)


def save_single_model_metrics(
    model_type: str,
    coefficients: Dict[str, float],
    p_values: Dict[str, float],
    r_squared: float,
    aic: float,
    cross_validation_scores: Optional[List[float]] = None,
    output_path: Optional[str] = None,
    validate: bool = True
) -> str:
    """
    Save metrics for a single model to the metrics file.
    If the file exists, it will append to the existing list.
    If not, it will create a new list.

    Args:
        model_type: Type of model (e.g., 'Gaussian GLM', 'Ridge Regression')
        coefficients: Dictionary of feature names to coefficient values
        p_values: Dictionary of feature names to p-values
        r_squared: R-squared value
        aic: Akaike Information Criterion value
        cross_validation_scores: Optional list of CV scores
        output_path: Path to the output JSON file
        validate: If True, validate after saving

    Returns:
        Path to the saved JSON file.
    """
    if output_path is None:
        output_path = get_data_path("results/model_metrics.json")
    
    output_file = Path(output_path)
    
    # Load existing data if file exists
    existing_results = []
    if output_file.exists():
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                existing_results = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Existing file is not valid JSON, starting fresh")
            existing_results = []

    # Create new record
    new_record = {
        "model_type": model_type,
        "coefficients": coefficients,
        "p_values": p_values,
        "r_squared": float(r_squared),
        "aic": float(aic),
        "cross_validation_scores": cross_validation_scores if cross_validation_scores else []
    }

    # Append to existing results
    existing_results.append(new_record)

    # Save back
    clean_results = _convert_numpy_types(existing_results)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(clean_results, f, indent=2, default=str)

    logger.info(f"Saved {model_type} metrics to {output_file}")

    if validate:
        try:
            df = pd.DataFrame(clean_results)
            assert_model_output_valid(df)
            logger.info(f"Model metrics validated successfully")
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            raise RuntimeError(f"Model metrics validation failed: {e}")

    return str(output_file)
