import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

from utils.logger import get_logger, log_execution_start, log_execution_end
from data.config import get_config

logger = get_logger(__name__)

def export_coefficients_to_csv(coefficients: pd.DataFrame, output_path: Path) -> None:
    """
    Export regression coefficients to a CSV file.

    Args:
        coefficients: DataFrame containing regression results (terms, estimates, std_err, p_values, etc.)
        output_path: Path where the CSV file will be saved.
    """
    if not isinstance(coefficients, pd.DataFrame):
        raise TypeError("coefficients must be a pandas DataFrame")
    
    if coefficients.empty:
        raise ValueError("coefficients DataFrame is empty")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    coefficients.to_csv(output_path, index=False)
    logger.info(f"Coefficients exported to {output_path}")

def export_diagnostics_to_json(diagnostics: Dict[str, Any], output_path: Path) -> None:
    """
    Export model diagnostics (p-values, VIF, CI, assumption test results) to a JSON file.

    Args:
        diagnostics: Dictionary containing diagnostic metrics.
        output_path: Path where the JSON file will be saved.
    """
    if not isinstance(diagnostics, dict):
        raise TypeError("diagnostics must be a dictionary")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(diagnostics, f, indent=4, default=str)
    
    logger.info(f"Diagnostics exported to {output_path}")

def run_export(
    coefficients: pd.DataFrame,
    diagnostics: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> tuple[Path, Path]:
    """
    Main export function that orchestrates saving coefficients and diagnostics.

    Args:
        coefficients: DataFrame of regression coefficients.
        diagnostics: Dictionary of diagnostic metrics.
        output_dir: Optional directory for output files. Defaults to data/processed.

    Returns:
        Tuple of (csv_path, json_path)
    """
    config = get_config()
    if output_dir is None:
        output_dir = Path(config.data_dir) / "processed"

    csv_path = output_dir / "regression_coefficients.csv"
    json_path = output_dir / "model_diagnostics.json"

    export_coefficients_to_csv(coefficients, csv_path)
    export_diagnostics_to_json(diagnostics, json_path)

    return csv_path, json_path

def run_main() -> None:
    """
    Entry point for running the export module directly.
    This is a placeholder for integration; actual data comes from regression.py results.
    """
    log_execution_start("export_results")
    
    try:
        # In a real pipeline, these would be passed from the regression module.
        # For module-level execution testing, we assume the caller populates these
        # or this function is called as part of a larger orchestration script.
        logger.warning("Direct execution of run_main requires populated arguments from upstream.")
    except Exception as e:
        logger.error(f"Export execution failed: {e}")
        raise
    finally:
        log_execution_end("export_results")

if __name__ == "__main__":
    run_main()
