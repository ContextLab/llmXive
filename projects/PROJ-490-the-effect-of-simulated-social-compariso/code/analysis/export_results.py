import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd

from data.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)

def export_coefficients_to_csv(coefficients: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Export regression coefficients to a CSV file.

    Args:
        coefficients: List of dictionaries containing coefficient data.
                      Expected keys: 'name', 'estimate', 'std_err', 'p_value', 'conf_int_low', 'conf_int_high'.
        output_path: Path where the CSV file will be saved.
    """
    logger.info(f"Exporting regression coefficients to {output_path}")
    
    if not coefficients:
        logger.warning("No coefficients to export. Creating empty CSV with headers.")
        df = pd.DataFrame(columns=['name', 'estimate', 'std_err', 'p_value', 'conf_int_low', 'conf_int_high'])
    else:
        df = pd.DataFrame(coefficients)
        # Ensure consistent column order
        expected_cols = ['name', 'estimate', 'std_err', 'p_value', 'conf_int_low', 'conf_int_high']
        existing_cols = [c for c in expected_cols if c in df.columns]
        df = df[existing_cols]

    df.to_csv(output_path, index=False)
    logger.info(f"Successfully exported {len(df)} coefficients to {output_path}")

def export_diagnostics_to_json(diagnostics: Dict[str, Any], output_path: Path) -> None:
    """
    Export model diagnostics to a JSON file.

    Args:
        diagnostics: Dictionary containing diagnostic metrics.
                     Expected structure:
                     {
                         "shapiro_p": float,
                         "breusch_pagan_p": float,
                         "vif_max": float,
                         "vif_details": List[Dict],
                         "collinearity_warning": bool (optional),
                         "assumptions_passed": bool
                     }
        output_path: Path where the JSON file will be saved.
    """
    logger.info(f"Exporting model diagnostics to {output_path}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(diagnostics, f, indent=2)
    
    logger.info(f"Successfully exported diagnostics to {output_path}")

def run_export(
    coefficients: List[Dict[str, Any]],
    diagnostics: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> None:
    """
    Run the full export process for regression results.

    Args:
        coefficients: List of coefficient dictionaries.
        diagnostics: Dictionary of diagnostic metrics.
        output_dir: Directory to save output files. Defaults to config output path.
    """
    config = get_config()
    if output_dir is None:
        output_dir = Path(config['output_dir'])
    
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "regression_coefficients.csv"
    json_path = output_dir / "model_diagnostics.json"

    export_coefficients_to_csv(coefficients, csv_path)
    export_diagnostics_to_json(diagnostics, json_path)

def run_main() -> None:
    """
    Main entry point for exporting results.
    This function is intended to be called after regression analysis is complete.
    It loads the necessary data from the regression module and exports it.
    """
    from analysis.regression import get_coefficients, validate_model_assumptions
    
    logger.info("Starting result export process...")
    
    config = get_config()
    output_dir = Path(config['output_dir'])
    
    # Get coefficients from the fitted model
    coefficients = get_coefficients()
    
    # Get diagnostics from assumption validation
    diagnostics = validate_model_assumptions()
    
    # Export results
    run_export(coefficients, diagnostics, output_dir)
    
    logger.info("Result export process completed successfully.")

if __name__ == "__main__":
    run_main()
