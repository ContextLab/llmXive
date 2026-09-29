"""
Module to write regression results to a JSON file adhering to the contract schema.

This module is responsible for formatting the output of the regression analysis
(T032, T033) into `data/derived/regression_results.json`.

It ensures that:
1. The output structure matches `specs/contracts/regression_results.schema.yaml`.
2. `sample_size_category` is not included in the results (enforced by caller).
3. VIF diagnostics are included.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def write_regression_results(
    results: Dict[str, Any],
    output_path: Path,
    input_file: str,
    excluded_predictors: Optional[List[str]] = None
) -> None:
    """
    Write regression results to a JSON file.
    
    Args:
        results: Dictionary containing 'model_summary', 'coefficients', 'vif_diagnostics'.
        output_path: Path to the output JSON file.
        input_file: Path to the input file used for the analysis.
        excluded_predictors: List of predictors that were excluded from the model.
    """
    if excluded_predictors is None:
        excluded_predictors = []

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Construct the final payload
    payload = {
        "model_summary": results.get("model_summary", {}),
        "coefficients": results.get("coefficients", []),
        "vif_diagnostics": results.get("vif_diagnostics", []),
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "input_file": str(input_file),
            "excluded_predictors": excluded_predictors,
            "version": "1.0.0"
        },
        "warnings": results.get("warnings", [])
    }

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        logger.info(f"Regression results written to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write regression results: {e}")
        raise

def main():
    """
    Standalone entry point for testing the writer.
    Generates a dummy results structure to verify the writer works.
    """
    # Mock data for testing the writer structure
    mock_results = {
        "model_summary": {
            "r_squared": 0.15,
            "adj_r_squared": 0.12,
            "f_statistic": 4.5,
            "f_statistic_pvalue": 0.003,
            "n_obs": 50,
            "n_params": 5,
            "formula": "power_gap ~ C(field) + effect_size_domain",
            "model_type": "OLS"
        },
        "coefficients": [
            {
                "term": "Intercept",
                "estimate": 0.1,
                "std_err": 0.05,
                "p_value": 0.04,
                "conf_int": [0.0, 0.2]
            },
            {
                "term": "C(field)[T.Psychology]",
                "estimate": -0.05,
                "std_err": 0.02,
                "p_value": 0.01,
                "conf_int": [-0.09, -0.01]
            },
            {
                "term": "effect_size_domain",
                "estimate": 0.02,
                "std_err": 0.01,
                "p_value": 0.08,
                "conf_int": [-0.001, 0.04]
            }
        ],
        "vif_diagnostics": [
            {"term": "C(field)[T.Psychology]", "vif_factor": 1.2},
            {"term": "effect_size_domain", "vif_factor": 1.1}
        ],
        "warnings": []
    }

    # Determine paths
    project_root = Path(__file__).resolve().parent.parent
    output_file = project_root / "data" / "derived" / "regression_results.json"
    input_file = "data/derived/power_analysis.csv"
    excluded = ["sample_size_category"]

    write_regression_results(
        mock_results,
        output_file,
        input_file,
        excluded_predictors=excluded
    )

    # Verify file exists
    if output_file.exists():
        logger.info("Verification: File created successfully.")
        # Print summary
        with open(output_file, 'r') as f:
            data = json.load(f)
            logger.info(f"Keys in output: {list(data.keys())}")
    else:
        logger.error("Verification failed: File not found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
