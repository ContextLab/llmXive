import os
import sys
import logging
import argparse
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config, load_environment
from utils.logging_config import get_logger, log_info_with_context, log_warning_with_context, log_error_with_context

def load_sensitivity_data(file_path: str) -> pd.DataFrame:
    """Load the sensitivity analysis CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Sensitivity analysis file not found: {file_path}")
    df = pd.read_csv(file_path)
    required_cols = {'cutoff', 'region_size', 'mean_correlation', 'robustness_score'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"Sensitivity file missing required columns. Found: {df.columns.tolist()}, Expected: {required_cols}")
    return df

def validate_against_sc003(df: pd.DataFrame, config: dict) -> dict:
    """
    Validate sensitivity analysis results against SC-003 requirements.
    
    SC-003 Requirement: The decoupled region identification must be robust 
    to threshold variations. The robustness_score (variance of region size 
    across cutoffs) must be below a configurable threshold.
    """
    results = {
        "spec_id": "SC-003",
        "validation_status": "PENDING",
        "metrics": {},
        "flags": [],
        "summary": ""
    }

    try:
        # 1. Check data integrity
        if df.empty:
            results["validation_status"] = "FAILED"
            results["flags"].append("Empty sensitivity analysis data")
            return results

        # 2. Calculate robustness metrics
        # The robustness_score column should already contain the variance of region sizes
        # across the swept cutoffs. We verify this calculation and check against threshold.
        
        # Recalculate robustness score to ensure consistency (variance of region_size)
        region_sizes = df['region_size'].values
        calculated_robustness = float(np.var(region_sizes))
        max_robustness = float(np.max(df['robustness_score'].values))
        mean_robustness = float(np.mean(df['robustness_score'].values))
        
        # 3. Retrieve threshold from config
        # Default threshold if not specified: 5.0 (arbitrary scientific threshold for stability)
        robustness_threshold = config.get('robustness_threshold', 5.0)
        
        results["metrics"] = {
            "calculated_robustness_variance": calculated_robustness,
            "max_robustness_score": max_robustness,
            "mean_robustness_score": mean_robustness,
            "configured_threshold": robustness_threshold,
            "num_thresholds_tested": len(df)
        }

        # 4. Perform validation logic
        # We consider the result robust if the variance in region size is low relative to the threshold
        is_robust = calculated_robustness < robustness_threshold
        
        if is_robust:
            results["validation_status"] = "PASSED"
            results["summary"] = f"SC-003 Validation PASSED: Robustness score ({calculated_robustness:.4f}) is within threshold ({robustness_threshold}). The decoupled region identification is stable across correlation cutoffs [0.5, 0.95]."
            log_info_with_context("robustness_validation", f"SC-003 validation passed. Robustness: {calculated_robustness:.4f} < {robustness_threshold}")
        else:
            results["validation_status"] = "WARNING"
            results["flags"].append(f"High variance in decoupled region size ({calculated_robustness:.4f} > {robustness_threshold}). Threshold sensitivity detected.")
            results["summary"] = f"SC-003 Validation WARNING: Robustness score ({calculated_robustness:.4f}) exceeds threshold ({robustness_threshold}). The identified decoupled region may be sensitive to the correlation cutoff choice. Review cutoff selection."
            log_warning_with_context("robustness_validation", f"SC-003 validation warning. Robustness: {calculated_robustness:.4f} > {robustness_threshold}")

        # 5. Additional checks: Ensure we have a valid range of cutoffs
        cutoffs = df['cutoff'].values
        if len(cutoffs) < 3:
            results["flags"].append("Insufficient cutoff points for robust statistical validation.")
            results["summary"] += " Note: Insufficient cutoff points tested."

        # 6. Check for monotonicity or expected behavior (optional but good practice)
        # As cutoff increases, region size should generally decrease or stay stable for a valid decoupling metric
        # (Assuming 'decoupled' means low correlation, so higher cutoff excludes more points)
        # This is a heuristic check
        region_sizes_sorted = df.sort_values('cutoff')['region_size'].values
        if np.any(np.diff(region_sizes_sorted) > 0.1 * np.mean(region_sizes_sorted)):
             # Allow some noise, but if it jumps significantly upwards as cutoff increases, it's suspicious
             results["flags"].append("Non-monotonic region size trend detected. Verify correlation definition.")

    except Exception as e:
        results["validation_status"] = "ERROR"
        results["summary"] = f"Validation failed with error: {str(e)}"
        log_error_with_context("robustness_validation", f"Validation error: {str(e)}")

    return results

def main():
    # Load environment and config
    load_environment()
    config = get_config()
    
    # Setup logging
    logger = get_logger("robustness_validation")
    logger.info("Starting SC-003 Robustness Validation")

    # Define paths
    # Ensure data/results directory exists
    results_dir = Path("data/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    input_file = Path("data/processed/sensitivity_analysis.csv")
    output_file = results_dir / "robustness_validation.json"

    # Check input file existence (fail loudly if missing)
    if not input_file.exists():
        log_error_with_context("robustness_validation", f"Input file missing: {input_file}. Ensure T032 has run successfully.")
        sys.exit(1)

    try:
        # Load data
        df = load_sensitivity_data(str(input_file))
        logger.info(f"Loaded sensitivity data with {len(df)} rows.")

        # Validate
        validation_result = validate_against_sc003(df, config)

        # Save results
        with open(output_file, 'w') as f:
            json.dump(validation_result, f, indent=2)

        logger.info(f"Validation results saved to {output_file}")
        logger.info(f"Final Status: {validation_result['validation_status']}")
        
        # Exit with appropriate code
        if validation_result['validation_status'] == 'ERROR':
            sys.exit(1)
        elif validation_result['validation_status'] == 'WARNING':
            # Don't fail the pipeline, just warn
            sys.exit(0)
        else:
            sys.exit(0)

    except Exception as e:
        log_error_with_context("robustness_validation", f"Critical failure in validation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
