"""
code/main.py: CLI entry point and orchestration.
Orchestrates the analysis pipeline: runs T026a, T026b, T027a, T027b and aggregates results into data/model_fits.json.
"""
import argparse
import json
import logging
import sys
import os
from typing import Optional
from config import load_config

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Main entry point for smooth number analysis")
    parser.add_argument("--task", type=str, choices=["sieve", "smoothness", "analysis", "viz", "aggregate"],
                        help="Task to run")
    parser.add_argument("--config", type=str, help="Path to config file")
    return parser.parse_args()

def run_aggregation():
    """
    Orchestrates the analysis tasks (T026a, T026b, T027a, T027b) and writes the final JSON report.
    """
    logging.info("Starting analysis aggregation pipeline...")

    # Import analysis functions dynamically to ensure they are available
    from analysis import (
        run_plan_primary_analysis,
        run_spec_mandatory_analysis,
        run_chi_square_goodness_of_fit,
        load_density_data
    )

    output_path = "data/model_fits.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    result = {
        "plan_beta": None,
        "plan_beta_se": None,
        "plan_r_squared": None,
        "plan_ks_p": None,
        "spec_beta": None,
        "spec_beta_se": None,
        "spec_r_squared": None,
        "spec_chi2_p": None
    }

    try:
        # --- Plan-Primary Analysis (T026a & T027a) ---
        logging.info("Running Plan-Primary Analysis (Deviation Ratio Regression & KS Test)...")
        plan_results = run_plan_primary_analysis()
        
        if plan_results:
            result["plan_beta"] = plan_results.get("beta")
            result["plan_beta_se"] = plan_results.get("se")
            result["plan_r_squared"] = plan_results.get("r_squared")
            result["plan_ks_p"] = plan_results.get("ks_p_value")
            logging.info(f"Plan Analysis Complete: beta={result['plan_beta']}, p={result['plan_ks_p']}")
        else:
            logging.warning("Plan-Primary analysis returned no results (non-convergence or data error).")

    except Exception as e:
        logging.error(f"Error during Plan-Primary analysis: {e}", exc_info=True)
        # Values remain null

    try:
        # --- Spec-Mandatory Analysis (T026b) ---
        logging.info("Running Spec-Mandatory Analysis (Raw Density Regression)...")
        spec_results = run_spec_mandatory_analysis()
        
        if spec_results:
            result["spec_beta"] = spec_results.get("beta")
            result["spec_beta_se"] = spec_results.get("se")
            result["spec_r_squared"] = spec_results.get("r_squared")
            logging.info(f"Spec Analysis Complete: beta={result['spec_beta']}")
        else:
            logging.warning("Spec-Mandatory analysis returned no results (non-convergence or data error).")

    except Exception as e:
        logging.error(f"Error during Spec-Mandatory analysis: {e}", exc_info=True)
        # Values remain null

    try:
        # --- Spec-Mandatory Chi-Square Test (T027b) ---
        logging.info("Running Spec-Mandatory Chi-Square Goodness-of-Fit Test...")
        chi2_results = run_chi_square_goodness_of_fit()
        
        if chi2_results:
            result["spec_chi2_p"] = chi2_results.get("p_value")
            logging.info(f"Chi-Square Test Complete: p={result['spec_chi2_p']}")
        else:
            logging.warning("Chi-Square test returned no results (data error or sparse bins).")

    except Exception as e:
        logging.error(f"Error during Chi-Square analysis: {e}", exc_info=True)
        # Values remain null

    # Write final results
    try:
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        logging.info(f"Successfully wrote aggregated results to {output_path}")
    except IOError as e:
        logging.error(f"Failed to write output file {output_path}: {e}")
        sys.exit(1)

    return result

def main():
    """Main entry point."""
    args = parse_args()
    config = load_config(args.config)

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if args.task == "sieve":
        from sieve import main as sieve_main
        sieve_main()
    elif args.task == "smoothness":
        from smoothness import main as smoothness_main
        smoothness_main()
    elif args.task == "analysis":
        from analysis import main as analysis_main
        analysis_main()
    elif args.task == "viz":
        from viz import main as viz_main
        viz_main()
    elif args.task == "aggregate":
        # New task for T029 orchestration
        run_aggregation()
    else:
        print("Usage: python code/main.py --task {sieve,smoothness,analysis,viz,aggregate}")
        sys.exit(1)

if __name__ == "__main__":
    main()
