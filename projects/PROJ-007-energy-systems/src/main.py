"""
Main entry point for the Energy Systems Causal Inference Pipeline.

This script orchestrates the full pipeline:
1. Ingest EIA RECS and ACS data
2. Preprocess data (filter, construct treatment, handle missing values, winsorize)
3. Propensity Score Matching (PSM) with balance validation
4. Causal effect estimation (OLS or DiD fallback)
5. Sensitivity analysis (caliper sweep)
6. Save results to data/outputs/analysis_result.json
"""

import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import yaml

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, set_seed
from src.data.preprocess import preprocess_pipeline, PowerError
from src.data.ingest import fetch_eia_rec, fetch_acs
from src.analysis.psm import iterative_matching
from src.analysis.balance import run_placebo_test, check_placebo_significance
from src.analysis.causal import run_ols, run_did, DataUnavailableError
from src.analysis.sensitivity import sweep_caliper
from src.models.output import save_analysis_result, AnalysisResult
from src.report.generator import generate_full_report

logger = get_logger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Run the full causal inference pipeline for energy inequity analysis."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="src/config.yaml",
        help="Path to the configuration file (default: src/config.yaml)"
    )
    args = parser.parse_args()

    logger.info(f"Starting pipeline with config: {args.config}")

    # Load configuration
    config = load_config(args.config)

    # Set random seeds for reproducibility
    set_seed(config.get('seeds', {}).get('random_seed', 42))

    # --- Step 1: Data Ingestion ---
    logger.info("Step 1: Ingesting data...")
    try:
        eia_data = fetch_eia_rec(config['data']['eia_rec_url'])
        acs_data = fetch_acs(config['data']['acs_url'])
        logger.info(f"Ingested {len(eia_data)} EIA records and {len(acs_data)} ACS records.")
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise

    # --- Step 2: Preprocessing ---
    logger.info("Step 2: Preprocessing data...")
    try:
        processed_df = preprocess_pipeline(
            eia_data,
            acs_data,
            low_income_threshold=config['preprocessing']['low_income_threshold'],
            winsorize_bounds=config['preprocessing']['winsorize_bounds'],
            missing_value_strategy=config['preprocessing']['missing_value_strategy']
        )
        logger.info(f"Preprocessing complete. Final shape: {processed_df.shape}")
    except PowerError as e:
        logger.error(f"Power check failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

    # --- Step 3: Propensity Score Matching & Balance Validation ---
    logger.info("Step 3: Running PSM and balance validation...")
    try:
        matched_df, balance_status, caliper_used = iterative_matching(
            processed_df,
            treatment_col='treatment',
            outcome_col='log_energy_cost',
            covariates=config['psm']['covariates'],
            caliper_initial=config['psm']['initial_caliper'],
            caliper_min=config['psm']['min_caliper'],
            max_iterations=config['psm']['max_iterations'],
            smd_threshold=config['psm']['smd_threshold']
        )
        logger.info(f"PSM complete. Balance status: {balance_status}, Caliper used: {caliper_used}")
    except Exception as e:
        logger.error(f"PSM failed: {e}")
        raise

    # --- Step 4: Placebo Test ---
    logger.info("Step 4: Running placebo test...")
    try:
        placebo_p_value = run_placebo_test(matched_df)
        placebo_passed = check_placebo_significance(placebo_p_value, alpha=0.05)
        logger.info(f"Placebo test p-value: {placebo_p_value:.4f}, Passed: {placebo_passed}")
    except Exception as e:
        logger.error(f"Placebo test failed: {e}")
        raise

    # --- Step 5: Causal Estimation ---
    logger.info("Step 5: Estimating causal effect...")
    causal_result = None
    methodology = None

    if not placebo_passed:
        logger.warning("Placebo test failed. Unconfoundedness assumption likely violated.")
        # Even if placebo fails, we proceed but flag it in the result
        # Or we could halt here depending on strictness. For now, we proceed with a warning.

    if balance_status == "FAIL":
        logger.info("PSM balance failed. Checking for longitudinal data for DiD fallback...")
        try:
            # Check for longitudinal data availability
            if 'pre_treatment_outcome' in matched_df.columns and 'post_treatment_outcome' in matched_df.columns:
                logger.info("Longitudinal data found. Running DiD fallback.")
                did_result = run_did(matched_df)
                causal_result = {
                    "att_estimate": did_result.params.get('treatment', 0.0),
                    "std_error": did_result.bse.get('treatment', 0.0),
                    "p_value": did_result.pvalues.get('treatment', 1.0),
                    "confidence_interval": {
                        "lower": did_result.conf_int().loc['treatment', 0],
                        "upper": did_result.conf_int().loc['treatment', 1]
                    }
                }
                methodology = "DiD"
            else:
                raise DataUnavailableError(
                    "Longitudinal data required for DiD but columns 'pre_treatment_outcome' and 'post_treatment_outcome' are missing."
                )
        except DataUnavailableError as e:
            logger.error(f"DiD fallback failed: {e}")
            raise
        except Exception as e:
            logger.error(f"DiD execution failed: {e}")
            raise
    else:
        logger.info("PSM balance passed. Running OLS.")
        try:
            ols_result = run_ols(
                matched_df,
                treatment_col='treatment',
                outcome_col='log_energy_cost',
                cluster_col='pair_id'
            )
            causal_result = {
                "att_estimate": ols_result.params.get('treatment', 0.0),
                "std_error": ols_result.bse.get('treatment', 0.0),
                "p_value": ols_result.pvalues.get('treatment', 1.0),
                "confidence_interval": {
                    "lower": ols_result.conf_int().loc['treatment', 0],
                    "upper": ols_result.conf_int().loc['treatment', 1]
                }
            }
            methodology = "OLS"
        except Exception as e:
            logger.error(f"OLS execution failed: {e}")
            raise

    # --- Step 6: Sensitivity Analysis ---
    logger.info("Step 6: Running sensitivity analysis (caliper sweep)...")
    try:
        sensitivity_results = sweep_caliper(
            processed_df,
            treatment_col='treatment',
            outcome_col='log_energy_cost',
            covariates=config['psm']['covariates'],
            caliper_range=config['sensitivity']['caliper_range'],
            smd_threshold=config['psm']['smd_threshold']
        )
        logger.info(f"Sensitivity analysis complete. {len(sensitivity_results)} calipers tested.")
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sensitivity_results = [] # Fallback to empty list if sweep fails

    # --- Step 7: Save Results ---
    logger.info("Step 7: Saving analysis results...")
    try:
        analysis_result = AnalysisResult(
          causal_estimation={
              "methodology": methodology,
              "att_estimate": causal_result["att_estimate"],
              "std_error": causal_result["std_error"],
              "p_value": causal_result["p_value"],
              "confidence_interval": causal_result["confidence_interval"],
              "n_treated": int(matched_df['treatment'].sum()),
              "n_control": int(len(matched_df) - matched_df['treatment'].sum()),
              "covariates_used": config['psm']['covariates']
          },
          balance_validation={
              "max_smd": float(matched_df.attrs.get('max_smd', 0.0)), # Assuming this is set during matching
              "balance_status": balance_status,
              "placebo_test": {
                  "p_value": float(placebo_p_value),
                  "passed": bool(placebo_passed)
              },
              "caliper_used": float(caliper_used)
          },
          sensitivity_analysis=sensitivity_results,
          data_summary={
              "total_observations": int(len(processed_df)),
              "treated_observations": int(processed_df['treatment'].sum()),
              "control_observations": int(len(processed_df) - processed_df['treatment'].sum()),
              "matched_pairs": int(len(matched_df) / 2)
          }
        )
        save_analysis_result(analysis_result, "data/outputs/analysis_result.json")
        logger.info("Results saved to data/outputs/analysis_result.json")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        raise

    # --- Step 8: Generate Report (Optional but recommended) ---
    logger.info("Step 8: Generating final report...")
    try:
        generate_full_report(analysis_result, output_path="data/outputs/final_report.md")
        logger.info("Final report generated at data/outputs/final_report.md")
    except Exception as e:
        logger.warning(f"Report generation failed (non-fatal): {e}")

    logger.info("Pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
