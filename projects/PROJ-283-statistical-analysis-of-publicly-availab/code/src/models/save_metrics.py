import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import numpy as np

from src.config import ensure_directories
from src.validation.validate_contracts import validate_dataframe_against_contract, load_schema

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.bool_, np.bool)):
        return bool(obj)
    return obj

def save_single_model_metrics(
    model_type: str,
    coefficients: Dict[str, float],
    p_values: Dict[str, float],
    r_squared: float,
    aic: float,
    cv_scores: List[float],
    output_path: Path
) -> None:
    """
    Save metrics for a single model to the output JSON file.
    
    Args:
        model_type: Name of the model type
        coefficients: Dictionary of feature -> coefficient
        p_values: Dictionary of feature -> p-value
        r_squared: R-squared value
        aic: Akaike Information Criterion
        cv_scores: List of cross-validation scores
        output_path: Path to the output JSON file
    """
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    # Convert numpy types to native Python types
    clean_coefficients = convert_numpy_types(coefficients)
    clean_p_values = convert_numpy_types(p_values)
    clean_cv_scores = convert_numpy_types(cv_scores)
    clean_r_squared = float(r_squared)
    clean_aic = float(aic)
    
    model_record = {
        "model_type": model_type,
        "coefficients": clean_coefficients,
        "p_values": clean_p_values,
        "r_squared": clean_r_squared,
        "aic": clean_aic,
        "cross_validation_scores": clean_cv_scores
    }
    
    # Load existing data if file exists
    if output_path.exists():
        with open(output_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Existing file {output_path} is not valid JSON, overwriting.")
                data = []
        
        if not isinstance(data, list):
            logger.warning(f"Existing file {output_path} does not contain a list, overwriting.")
            data = []
    else:
        data = []
    
    data.append(model_record)
    
    # Write back to file
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Saved metrics for model '{model_type}' to {output_path}")

def save_model_metrics(
    results: Dict[str, Dict[str, Any]],
    output_path: Optional[Path] = None
) -> None:
    """
    Save metrics for multiple models to the output JSON file.
    
    Args:
        results: Dictionary mapping model_type to a dict containing:
            - coefficients: Dict[str, float]
            - p_values: Dict[str, float]
            - r_squared: float
            - aic: float
            - cv_scores: List[float]
        output_path: Path to the output JSON file. Defaults to data/results/model_metrics.json
    """
    if output_path is None:
        output_path = Path("data/results/model_metrics.json")
    
    # Ensure output directory exists
    ensure_directories([output_path.parent])
    
    # Convert all numpy types
    clean_results = []
    for model_type, metrics in results.items():
        clean_entry = {
            "model_type": model_type,
            "coefficients": convert_numpy_types(metrics.get("coefficients", {})),
            "p_values": convert_numpy_types(metrics.get("p_values", {})),
            "r_squared": float(metrics.get("r_squared", 0.0)),
            "aic": float(metrics.get("aic", 0.0)),
            "cross_validation_scores": convert_numpy_types(metrics.get("cv_scores", []))
        }
        clean_results.append(clean_entry)
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(clean_results, f, indent=2)
    
    logger.info(f"Saved metrics for {len(clean_results)} models to {output_path}")
    
    # Validate against schema
    try:
        schema_path = Path("specs/contracts/model_output.schema.yaml")
        if schema_path.exists():
            schema = load_schema(schema_path)
            # Convert list of dicts to a DataFrame for validation
            import pandas as pd
            df = pd.DataFrame(clean_results)
            validate_dataframe_against_contract(df, schema)
            logger.info(f"Successfully validated output against {schema_path}")
        else:
            logger.warning(f"Schema file not found at {schema_path}, skipping validation.")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

def main():
    """
    Main entry point for saving model metrics.
    This function is intended to be called after model fitting and validation.
    For demonstration, it creates dummy data if no arguments are provided.
    In a real pipeline, this would receive results from the fitting/validation steps.
    """
    # Example usage with dummy data to demonstrate the function works
    # In a real scenario, 'results' would come from fit.py and validate.py
    dummy_results = {
        "Gaussian GLM": {
            "coefficients": {
                "intercept": 0.5,
                "eco_family_King's Pawn": 0.1,
                "avg_move_time_white": 0.02,
                "material_imbalance_move5": -0.05
            },
            "p_values": {
                "intercept": 0.001,
                "eco_family_King's Pawn": 0.04,
                "avg_move_time_white": 0.03,
                "material_imbalance_move5": 0.12
            },
            "r_squared": 0.65,
            "aic": 1250.4,
            "cv_scores": [0.62, 0.64, 0.66, 0.63, 0.65]
        },
        "Ridge Regression": {
            "coefficients": {
                "intercept": 0.48,
                "eco_family_King's Pawn": 0.11,
                "avg_move_time_white": 0.018,
                "material_imbalance_move5": -0.045
            },
            "p_values": {
                "intercept": 0.002,
                "eco_family_King's Pawn": 0.045,
                "avg_move_time_white": 0.035,
                "material_imbalance_move5": 0.11
            },
            "r_squared": 0.64,
            "aic": 1255.2,
            "cv_scores": [0.61, 0.63, 0.65, 0.62, 0.64]
        }
    }
    
    output_path = Path("data/results/model_metrics.json")
    save_model_metrics(dummy_results, output_path)
    
    # Verify file exists and is valid JSON
    if output_path.exists():
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        logger.info(f"Verification: Loaded {len(loaded)} model records from {output_path}")
    else:
        raise RuntimeError(f"Failed to create output file at {output_path}")

if __name__ == "__main__":
    main()
