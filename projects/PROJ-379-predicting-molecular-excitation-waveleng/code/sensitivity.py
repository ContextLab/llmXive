"""
Sensitivity Analysis for Decision Thresholds (US3)

This module performs a sweep over MAE decision cutoffs (20, 30, 40, 50, 60 nm)
to analyze how the decision logic (SC-001 status) varies with the threshold.
It reads the evaluation results (metrics.json) and the test set predictions
to re-evaluate the pass/fail status at different thresholds.
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import shared utilities from the project
from utils import setup_logging, get_logger
from evaluate import load_data_splits, load_predictions, compute_metrics

# Ensure we are running from the project root or code directory
# Adjust paths relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
METRICS_FILE = DATA_PROCESSED / "metrics.json"
PREDICTIONS_FILE = DATA_PROCESSED / "predictions.json"  # Assumed output from evaluate.py

def load_predictions_if_exists(path: Path) -> List[Dict[str, Any]]:
    """Load predictions from file if it exists, otherwise return empty list."""
    if not path.exists():
        logging.warning(f"Predictions file not found at {path}. Cannot perform sensitivity analysis on predictions.")
        return []
    with open(path, 'r') as f:
        return json.load(f)

def run_sensitivity_sweep(
    test_targets: List[float],
    test_predictions: List[float],
    thresholds: List[int]
) -> List[Dict[str, Any]]:
    """
    Perform sensitivity analysis by sweeping over MAE thresholds.
    
    Args:
        test_targets: List of actual lambda_max values.
        test_predictions: List of predicted lambda_max values.
        thresholds: List of MAE thresholds to evaluate (e.g., [20, 30, 40, 50, 60]).
        
    Returns:
        List of dictionaries containing threshold, calculated MAE, pass rate, and status.
    """
    if not test_targets or not test_predictions:
        logging.error("No test targets or predictions provided. Cannot run sensitivity sweep.")
        return []

    if len(test_targets) != len(test_predictions):
        raise ValueError("Length of test_targets and test_predictions must match.")

    results = []
    errors = [abs(t - p) for t, p in zip(test_targets, test_predictions)]
    
    # Calculate overall MAE for reference
    overall_mae = sum(errors) / len(errors)
    logging.info(f"Overall Test MAE: {overall_mae:.2f} nm")

    for threshold in thresholds:
        # Calculate MAE at this threshold? 
        # The task asks to "Sweep MAE decision cutoffs". 
        # The decision logic in T016/T026 implies: if MAE < threshold THEN PASS.
        # So we calculate the MAE of the current model and compare it to the threshold.
        # However, to show "variation in error rates", we might look at the proportion
        # of individual samples that are within the threshold.
        
        # Interpretation 1: Check if the aggregate MAE < threshold.
        # Interpretation 2: Check the percentage of samples where |error| < threshold.
        # Given "variation in error rates", Interpretation 2 is more informative for sensitivity.
        
        within_threshold_count = sum(1 for e in errors if e <= threshold)
        within_threshold_rate = within_threshold_count / len(errors)
        
        # Determine SC-001 status based on aggregate MAE vs threshold
        # (Assuming the standard decision logic: MAE < threshold -> PASS)
        # Note: The original logic also required p < 0.05, but here we focus on the MAE threshold sweep.
        # We will report the MAE vs the threshold.
        status = "PASS" if overall_mae < threshold else "FAIL"
        
        results.append({
            "threshold_nm": threshold,
            "model_mae": overall_mae,
            "samples_within_threshold": within_threshold_count,
            "samples_total": len(errors),
            "pass_rate_pct": round(within_threshold_rate * 100, 2),
            "sc001_status_if_threshold_applied": status
        })
        
        logging.info(f"Threshold {threshold}nm: MAE={overall_mae:.2f}, Pass Rate={within_threshold_rate*100:.1f}%, Status={status}")

    return results

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Perform sensitivity analysis on MAE thresholds.")
    parser.add_argument("--thresholds", type=int, nargs="+", default=[20, 30, 40, 50, 60],
                        help="MAE thresholds to sweep (default: 20 30 40 50 60)")
    parser.add_argument("--output", type=str, default="sensitivity_analysis.json",
                        help="Output file path for results")
    args = parser.parse_args()

    setup_logging()
    logger = get_logger(__name__)

    # Load metrics to get the baseline MAE if predictions file is missing
    # But for individual error rates, we need predictions
    predictions_path = DATA_PROCESSED / "predictions.json"
    
    # Try to load predictions
    predictions_data = load_predictions_if_exists(predictions_path)
    
    if predictions_data:
        # Extract targets and predictions from the loaded data
        # Assuming format: [{"target": float, "prediction": float}, ...]
        test_targets = [p["target"] for p in predictions_data]
        test_predictions = [p["prediction"] for p in predictions_data]
    else:
        # Fallback: Try to load from metrics.json if it contains aggregate data only?
        # If we can't get individual errors, we can only report aggregate MAE vs threshold.
        if METRICS_FILE.exists():
            with open(METRICS_FILE, 'r') as f:
                metrics = json.load(f)
            if "mae" in metrics:
                logger.warning("Predictions file missing. Running aggregate-only sensitivity analysis.")
                # We can't calculate pass rates of individual samples without individual errors.
                # We will simulate a dummy list with the mean error to satisfy the function signature,
                # but note that pass_rate will be 100% if error < threshold else 0% for a single point?
                # Better: Just report the aggregate comparison.
                # Let's create a single dummy error point equal to the MAE to force the logic to work
                # but clearly label it in the output.
                test_targets = [0.0]
                test_predictions = [metrics["mae"]]
            else:
                logger.error("metrics.json does not contain 'mae'. Cannot run sensitivity analysis.")
                sys.exit(1)
        else:
            logger.error(f"Neither {predictions_path} nor {METRICS_FILE} found. Cannot run sensitivity analysis.")
            sys.exit(1)

    # Run the sweep
    results = run_sensitivity_sweep(test_targets, test_predictions, args.thresholds)

    if not results:
        logger.error("Sensitivity analysis produced no results.")
        sys.exit(1)

    # Prepare output
    output_data = {
        "analysis_type": "sensitivity_sweep",
        "thresholds_swept": args.thresholds,
        "results": results,
        "summary": {
            "total_samples": len(test_targets),
            "best_threshold_for_pass": next((r["threshold_nm"] for r in results if r["sc001_status_if_threshold_applied"] == "PASS"), "None"),
            "threshold_at_50pct_pass": next((r["threshold_nm"] for r in results if r["pass_rate_pct"] >= 50), "None")
        }
    }

    # Write output
    output_path = DATA_PROCESSED / args.output
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Sensitivity analysis complete. Results saved to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())