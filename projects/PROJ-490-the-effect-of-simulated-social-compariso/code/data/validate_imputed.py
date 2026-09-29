import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd

from data.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def validate_imputed_data(input_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Verify that data/processed/imputed_data.csv exists, is non-empty,
    and contains the expected columns after T016.

    Returns a validation dictionary:
    {
        "status": "pass" | "fail",
        "imputation_success": True | False,
        "row_count": int,
        "columns_found": list,
        "timestamp": ISO8601 string
    }
    """
    config = get_config()
    if input_path is None:
        input_path = config.processed_dir / "imputed_data.csv"

    result = {
        "status": "fail",
        "imputation_success": False,
        "row_count": 0,
        "columns_found": [],
        "timestamp": datetime.utcnow().isoformat()
    }

    if not input_path.exists():
        logger.error(f"Imputed data file not found: {input_path}")
        result["reason"] = "File not found"
        return result

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read imputed data: {e}")
        result["reason"] = f"Read error: {e}"
        return result

    if df.empty:
        logger.error("Imputed data file is empty.")
        result["reason"] = "Empty file"
        return result

    required_columns = {
        "participant_id",
        "pre_self_esteem",
        "post_self_esteem",
        "comparison_tendency",
        "avatar_condition"
    }

    found_columns = set(df.columns)
    missing_columns = required_columns - found_columns

    if missing_columns:
        logger.error(f"Missing required columns: {missing_columns}")
        result["reason"] = f"Missing columns: {missing_columns}"
        return result

    # All checks passed
    result["status"] = "pass"
    result["imputation_success"] = True
    result["row_count"] = len(df)
    result["columns_found"] = sorted(list(found_columns))
    logger.info(f"Validation passed: {len(df)} rows, columns: {result['columns_found']}")
    return result

def save_validation_result(result: Dict[str, Any], output_path: Optional[Path] = None) -> None:
    """
    Save the validation result to data/processed/post_imputation_validation.json.
    """
    config = get_config()
    if output_path is None:
        output_path = config.processed_dir / "post_imputation_validation.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Validation result saved to {output_path}")

def run_validation(input_path: Optional[Path] = None, output_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run validation and save the result.
    """
    result = validate_imputed_data(input_path)
    save_validation_result(result, output_path)
    return result

def main() -> None:
    """
    Entry point for the validation script.
    """
    logger.info("Starting post-imputation validation (T013b).")
    result = run_validation()
    if result["status"] == "pass":
        logger.info("Post-imputation validation: PASSED")
    else:
        logger.error(f"Post-imputation validation: FAILED - {result.get('reason', 'Unknown')}")

if __name__ == "__main__":
    main()