import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from utils.logger import get_logger
from utils.validators import load_schema, validate_json_against_schema

# Configure logger for this module
logger = get_logger(__name__)

def validate_imputed_data(input_path: Path) -> Dict[str, Any]:
    """
    Verify that the imputed data file exists and contains the required columns
    with no remaining missing values in critical fields.

    Args:
        input_path: Path to data/processed/imputed_data.csv

    Returns:
        Dict containing validation status, success flag, and timestamp.
    """
    result = {
        "status": "fail",
        "imputation_success": False,
        "timestamp": datetime.utcnow().isoformat(),
        "errors": []
    }

    if not input_path.exists():
        msg = f"Imputed data file not found at {input_path}"
        logger.error(msg)
        result["errors"].append(msg)
        return result

    try:
        import pandas as pd
        df = pd.read_csv(input_path)
    except Exception as e:
        msg = f"Failed to read imputed data: {str(e)}"
        logger.error(msg)
        result["errors"].append(msg)
        return result

    required_cols = [
        "participant_id",
        "pre_self_esteem",
        "post_self_esteem",
        "comparison_tendency",
        "avatar_condition"
    ]

    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        msg = f"Missing required columns: {missing_cols}"
        logger.error(msg)
        result["errors"].append(msg)
        return result

    # Check for any remaining NaN in required columns
    nan_counts = df[required_cols].isna().sum()
    if nan_counts.any():
        cols_with_nan = nan_counts[nan_counts > 0].index.tolist()
        msg = f"Remaining missing values in columns: {cols_with_nan}"
        logger.error(msg)
        result["errors"].append(msg)
        return result

    if len(df) == 0:
        msg = "Imputed data file is empty"
        logger.error(msg)
        result["errors"].append(msg)
        return result

    # All checks passed
    result["status"] = "pass"
    result["imputation_success"] = True
    result["row_count"] = len(df)
    logger.info(f"Imputation validation passed. Rows: {len(df)}")
    return result

def save_validation_result(result: Dict[str, Any], output_path: Path) -> None:
    """
    Save the validation result to a JSON file.

    Args:
        result: Validation result dictionary.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Validation result saved to {output_path}")

def run_validation(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Main entry point for running the post-imputation validation.

    Args:
        input_path: Optional override for input file path.
        output_path: Optional override for output file path.

    Returns:
        The validation result dictionary.
    """
    from data.config import get_config
    config = get_config()

    if input_path is None:
        input_path = config.paths.get("imputed_data_path", config.project_root / "data" / "processed" / "imputed_data.csv")
    if output_path is None:
        output_path = config.paths.get("post_imputation_validation_path", config.project_root / "data" / "processed" / "post_imputation_validation.json")

    logger.info(f"Starting post-imputation validation for {input_path}")
    result = validate_imputed_data(input_path)
    save_validation_result(result, output_path)
    return result

def main():
    """Script entry point."""
    logging.basicConfig(level=logging.INFO)
    run_validation()

if __name__ == "__main__":
    main()
