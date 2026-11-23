"""
Export regression coefficients and model diagnostics to disk.
Implements Task T021: Export regression coefficients to CSV and diagnostics to JSON.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
from data.config import get_config
from utils.logger import get_logger

logger = get_logger("export_results")

def export_coefficients_to_csv(coefficients: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export regression coefficients to a CSV file.

    Args:
        coefficients: List of dictionaries containing coefficient data
            (name, estimate, std_err, p_value)
        output_path: Path to the output CSV file
    """
    logger.info(f"Exporting regression coefficients to {output_path}")

    df = pd.DataFrame(coefficients)

    # Ensure the directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully wrote {len(df)} coefficients to {output_path}")

def export_diagnostics_to_json(diagnostics: Dict[str, Any], output_path: str) -> None:
    """
    Export model diagnostics to a JSON file.

    Args:
        diagnostics: Dictionary containing diagnostic metrics
        output_path: Path to the output JSON file
    """
    logger.info(f"Exporting model diagnostics to {output_path}")

    # Ensure the directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to JSON with indentation for readability
    with open(output_path, 'w') as f:
        json.dump(diagnostics, f, indent=2)

    logger.info(f"Successfully wrote diagnostics to {output_path}")

def run_export(coefficients: List[Dict[str, Any]], diagnostics: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> None:
    """
    Main function to orchestrate the export of results.

    This function is called by the main pipeline to write the final
    regression coefficients and diagnostics to disk as required by T021.

    Args:
        coefficients: List of coefficient dictionaries from the regression model
        diagnostics: Dictionary of diagnostic metrics
        config: Optional configuration dictionary
    """
    if config is None:
        config = get_config()

    processed_dir = Path(config['paths']['processed'])
    processed_dir.mkdir(parents=True, exist_ok=True)

    coefficients_path = str(processed_dir / "regression_coefficients.csv")
    diagnostics_path = str(processed_dir / "model_diagnostics.json")

    try:
        export_coefficients_to_csv(coefficients, coefficients_path)
        export_diagnostics_to_json(diagnostics, diagnostics_path)
        logger.info("T021 Export completed successfully.")
    except Exception as e:
        logger.error(f"Failed to export results: {e}")
        raise

def run_main():
    """
    Entry point for running the export module standalone.
    Used for verification or when called directly by main.py.
    """
    logger.info("Running export_results module directly.")
    # This is a placeholder for a standalone run.
    # In the actual pipeline, data is passed from the regression module.
    # We load the imputed data, run the regression to get coefficients,
    # then export them.
    config = get_config()
    imputed_path = Path(config['paths']['processed']) / "imputed_data.csv"

    if not imputed_path.exists():
        logger.error(f"Imputed data not found at {imputed_path}. "
                     "Please run the preprocessing pipeline first.")
        raise FileNotFoundError(f"Imputed data not found: {imputed_path}")

    # Load data
    df = pd.read_csv(imputed_path)

    # Import regression logic to get coefficients and diagnostics
    # We assume the regression module is available and returns the necessary dicts.
    # To avoid circular imports, we import here.
    from analysis.regression import run_regression_analysis

    try:
        coeffs, diags = run_regression_analysis(df)
        run_export(coeffs, diags)
    except Exception as e:
        logger.error(f"Error during regression analysis or export: {e}")
        raise

if __name__ == "__main__":
    run_main()
