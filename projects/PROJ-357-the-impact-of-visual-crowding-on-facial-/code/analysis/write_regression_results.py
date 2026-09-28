"""
Task T038: Generate regression_results.json containing coefficients, confidence intervals, and p-values.

This script consumes the output of the GLMM analysis (from glmm_model.py) and writes
a structured JSON report to data/processed/regression_results.json.

It relies on the results being available in memory or written to a temporary state
by the run_analysis function in glmm_model.py.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from analysis.glmm_model import run_analysis, load_prepared_data
from config import ensure_directories, get_seed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_regression_results_from_analysis(results_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format the raw results from run_analysis into the standard regression_results.json schema.
    
    Args:
        results_dict: The dictionary returned by run_analysis containing model summary, 
                      coefficients, and diagnostics.
    
    Returns:
        A formatted dictionary ready for JSON serialization.
    """
    if not results_dict:
        raise ValueError("No results provided to format.")

    formatted = {
        "metadata": {
            "model_type": results_dict.get("model_type", "GLMM"),
            "convergence_status": results_dict.get("convergence_status", "unknown"),
            "fallback_used": results_dict.get("fallback_used", False),
            "fdr_applied": results_dict.get("fdr_applied", False),
            "seed": get_seed()
        },
        "fixed_effects": [],
        "random_effects_variance": {},
        "model_diagnostics": {
            "log_likelihood": results_dict.get("log_likelihood", None),
            "aic": results_dict.get("aic", None),
            "bic": results_dict.get("bic", None),
            "n_obs": results_dict.get("n_obs", None),
            "n_groups": results_dict.get("n_groups", {})
        },
        "hypothesis_tests": []
    }

    # Process fixed effects coefficients
    if "coefficients" in results_dict:
        for term, stats in results_dict["coefficients"].items():
          formatted["fixed_effects"].append({
              "term": term,
              "estimate": float(stats.get("estimate", 0.0)),
              "std_error": float(stats.get("std_error", 0.0)),
              "z_value": float(stats.get("z_value", 0.0)),
              "p_value_raw": float(stats.get("p_value_raw", 1.0)),
              "p_value_adj": float(stats.get("p_value_adj", 1.0)),
              "conf_int_lower": float(stats.get("conf_int_lower", 0.0)),
              "conf_int_upper": float(stats.get("conf_int_upper", 0.0)),
              "significant": bool(stats.get("significant", False))
          })

    # Process random effects variance if available
    if "random_effects" in results_dict:
        formatted["random_effects_variance"] = results_dict["random_effects"]

    # Process hypothesis tests summary
    if "hypothesis_tests" in results_dict:
        formatted["hypothesis_tests"] = results_dict["hypothesis_tests"]

    return formatted

def main():
    parser = argparse.ArgumentParser(
        description="Generate regression_results.json from GLMM analysis output."
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/regression_results.json",
        help="Path to save the regression results JSON file."
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/processed/prepared_analysis_data.csv",
        help="Path to the prepared data file for analysis."
    )
    
    args = parser.parse_args()
    output_path = Path(args.output_path)
    data_path = Path(args.data_path)

    # Ensure output directory exists
    ensure_directories([output_path.parent])

    logger.info(f"Loading prepared data from {data_path}...")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}. Please run the data preparation pipeline first.")
        sys.exit(1)

    try:
        # Run the full analysis pipeline (loads data, fits model, applies FDR)
        logger.info("Running GLMM analysis...")
        results = run_analysis(
            data_path=str(data_path),
            verbose=True
        )
        
        if not results:
            logger.error("GLMM analysis returned no results.")
            sys.exit(1)

        logger.info(f"Analysis complete. Convergence: {results.get('convergence_status')}")

        # Format results
        logger.info("Formatting results...")
        formatted_results = load_regression_results_from_analysis(results)

        # Write to JSON
        logger.info(f"Writing results to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(formatted_results, f, indent=2)

        logger.info(f"Successfully generated {output_path}")
        print(f"Output written to: {output_path}")

    except Exception as e:
        logger.error(f"Failed to generate regression results: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()