"""
Main entry point for the Energy Inequity Causal Analysis Pipeline.

Orchestrates the full pipeline: Ingestion -> Preprocessing -> PSM -> Balance Check -> Causal Estimation -> Sensitivity -> Report.
"""
import argparse
import sys
import json
from pathlib import Path

import pandas as pd
import yaml

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, set_seed
from src.data.ingest import fetch_eia_rec, fetch_acs
from src.data.preprocess import preprocess_pipeline, PowerError
from src.analysis.psm import iterative_matching
from src.analysis.balance import run_placebo_test, check_placebo_significance, generate_placebo_report
from src.analysis.causal import run_ols, run_did, DataUnavailableError
from src.analysis.sensitivity import sweep_caliper
from src.models.output import save_analysis_result
from src.report.generator import generate_full_report

logger = get_logger(__name__)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_pipeline(config: dict) -> dict:
    """
    Execute the full causal inference pipeline.

    Returns:
        dict: Analysis results including ATT, p-values, and metadata.
    """
    # Set seeds for reproducibility
    set_seed(config.get('seeds', {}).get('random', 42))

    logger.info("Starting Energy Inequity Analysis Pipeline")

    # 1. Data Ingestion
    logger.info("Step 1: Ingesting data...")
    try:
        eia_df = fetch_eia_rec(config['paths']['eia_url'])
        acs_df = fetch_acs(config['paths']['acs_api_key'])
        raw_df = pd.merge(eia_df, acs_df, on='tract_id', how='inner')
        logger.info(f"Ingested {len(raw_df)} households.")
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise

    # 2. Preprocessing
    logger.info("Step 2: Preprocessing data...")
    try:
        processed_df = preprocess_pipeline(
            raw_df,
            income_threshold=config['thresholds']['income_fpl_ratio'],
            winsorize_bounds=config['thresholds']['winsorize_percentiles']
        )
        logger.info(f"Preprocessed {len(processed_df)} households.")
    except PowerError as e:
        logger.error(f"Power check failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        raise

    # 3. Propensity Score Matching & Balance
    logger.info("Step 3: Running PSM and balance checks...")
    matched_df, balance_status = iterative_matching(
        processed_df,
        caliper=config['thresholds']['caliper'],
        max_attempts=config['params']['max_matching_attempts']
    )

    if balance_status == 'FAIL':
        logger.warning("PSM balance check failed. Checking for DiD fallback...")
        # Check for longitudinal data availability
        required_cols = ['pre_treatment_outcome', 'post_treatment_outcome']
        if not all(col in matched_df.columns for col in required_cols):
            logger.error("Balance failed and longitudinal data missing. Cannot proceed with DiD.")
            raise ValueError("BalanceFailureError: PSM failed and longitudinal data unavailable for DiD fallback.")
        # If longitudinal data exists, we might run DiD later, but for now flag status
        # The main logic for switching to DiD happens in causal estimation if balance_status is FAIL
        pass

    # 4. Placebo Gate
    logger.info("Step 4: Running placebo gate...")
    try:
        placebo_passed = check_placebo_significance(matched_df)
        if not placebo_passed:
            logger.error("Placebo test failed. Unconfoundedness assumption violated.")
            raise ValueError("PlaceboGateError: Placebo test failed.")
    except Exception as e:
        logger.error(f"Placebo gate check failed: {e}")
        raise

    # 5. Causal Estimation
    logger.info("Step 5: Estimating causal effects...")
    try:
        if balance_status == 'FAIL' and 'pre_treatment_outcome' in matched_df.columns:
            logger.info("Running DiD due to PSM failure and longitudinal data availability.")
            results = run_did(matched_df)
            method = "DiD"
        else:
            logger.info("Running OLS.")
            results = run_ols(matched_df)
            method = "OLS"
        
        att_estimate = results['att']
        p_value = results['p_value']
        ci = results['confidence_interval']
    except Exception as e:
        logger.error(f"Causal estimation failed: {e}")
        raise

    # 6. Sensitivity Analysis
    logger.info("Step 6: Running sensitivity analysis...")
    try:
        sensitivity_results = sweep_caliper(
            processed_df,
            calipers=config['params']['sensitivity_calipers']
        )
    except Exception as e:
        logger.warning(f"Sensitivity analysis failed: {e}")
        sensitivity_results = []

    # 7. Compile Results
    analysis_result = {
        "att_estimate": float(att_estimate),
        "p_value": float(p_value),
        "confidence_interval": [float(ci[0]), float(ci[1])],
        "methodology": method,
        "balance_status": balance_status,
        "sensitivity_analysis": sensitivity_results,
        "timestamp": pd.Timestamp.now().isoformat()
    }

    return analysis_result


def main():
    parser = argparse.ArgumentParser(description="Run Energy Inequity Causal Analysis Pipeline")
    parser.add_argument("--config", type=str, default="code/src/config.yaml", help="Path to config YAML")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
        results = run_pipeline(config)
        
        # Save results
        output_path = Path(config['paths']['output_json'])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_analysis_result(results, output_path)
        
        logger.info(f"Pipeline completed successfully. Results saved to {output_path}")
        
        # Generate report
        generate_full_report(results, config['paths']['report_output'])
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
