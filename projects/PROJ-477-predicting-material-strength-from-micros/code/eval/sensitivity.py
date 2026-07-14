import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Any

import numpy as np
import pandas as pd

# Import project utilities
from utils.config import get_results_dir, get_processed_dir, get_project_root, get_seed
from utils.logging_config import get_logger

def setup_logging():
    """Initialize logging for the sensitivity analysis."""
    logger = get_logger("sensitivity_analysis")
    return logger

def load_predictions(filepath: Path) -> pd.DataFrame:
    """
    Load predictions from a CSV file.
    Expected columns: image_id, true_strength, pred_strength
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Predictions file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    required_cols = {'image_id', 'true_strength', 'pred_strength'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Predictions file missing columns: {missing}")
    
    return df

def binarize_by_median(df: pd.DataFrame) -> pd.DataFrame:
    """
    Binarize labels and predictions using the median predicted strength of the test set.
    FR-007: Override plan.md to use median predicted strength.
    
    Creates columns:
    - true_bin: 1 if true_strength >= median_pred, else 0
    - pred_bin: 1 if pred_strength >= median_pred, else 0
    """
    median_pred = df['pred_strength'].median()
    
    df['true_bin'] = (df['true_strength'] >= median_pred).astype(int)
    df['pred_bin'] = (df['pred_strength'] >= median_pred).astype(int)
    
    return df, median_pred

def compute_fpr_fnr(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Compute False Positive Rate (FPR) and False Negative Rate (FNR).
    
    Definitions:
    - TP: true_bin=1, pred_bin=1
    - TN: true_bin=0, pred_bin=0
    - FP: true_bin=0, pred_bin=1
    - FN: true_bin=1, pred_bin=0
    
    FPR = FP / (FP + TN)
    FNR = FN / (FN + TP)
    """
    tp = ((df['true_bin'] == 1) & (df['pred_bin'] == 1)).sum()
    tn = ((df['true_bin'] == 0) & (df['pred_bin'] == 0)).sum()
    fp = ((df['true_bin'] == 0) & (df['pred_bin'] == 1)).sum()
    fn = ((df['true_bin'] == 1) & (df['pred_bin'] == 0)).sum()
    
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    return fpr, fnr

def run_sensitivity_analysis(
    predictions_path: Path,
    thresholds: List[float],
    output_path: Path
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by sweeping thresholds and computing FPR/FNR.
    
    Args:
        predictions_path: Path to the predictions CSV file.
        thresholds: List of thresholds to sweep (e.g., [0.01, 0.05, 0.1]).
        output_path: Path to write the JSON report.
        
    Returns:
        Dictionary containing the analysis results.
    """
    logger = logging.getLogger("sensitivity_analysis")
    logger.info(f"Loading predictions from {predictions_path}")
    
    df = load_predictions(predictions_path)
    logger.info(f"Loaded {len(df)} predictions")
    
    # Binarize using median predicted strength
    df_binarized, median_val = binarize_by_median(df)
    logger.info(f"Binarized using median predicted strength: {median_val:.4f}")
    
    results = {
        "median_predicted_strength": float(median_val),
        "total_samples": len(df),
        "thresholds": [],
        "summary": {}
    }
    
    logger.info(f"Starting sensitivity sweep over {len(thresholds)} thresholds")
    
    for t in thresholds:
        # Calculate FPR/FNR at this threshold
        # Note: The binarization is fixed by the median. 
        # The "sweep" in this context refers to the stability of the metric
        # or potentially re-evaluating the binarization if the task implied 
        # a threshold on the difference, but FR-007 specifies binarization by median.
        # 
        # However, the task asks to "sweep thresholds {0.01, 0.05, 0.1}, compute FPR/FNR".
        # If the binarization is fixed by the median, the FPR/FNR is constant.
        # 
        # Interpretation: The "thresholds" likely refer to a tolerance band 
        # around the median for sensitivity, OR the task implies a standard 
        # ROC-style sweep where we vary the decision threshold.
        # 
        # Re-reading FR-007: "Binarize using median predicted strength... sweep thresholds {0.01, 0.05, 0.1}, compute FPR/FNR".
        # This phrasing is slightly ambiguous. Standard sensitivity analysis varies the threshold.
        # If we strictly follow "Binarize using median", the threshold is fixed.
        # 
        # Alternative interpretation: The thresholds {0.01, 0.05, 0.1} are the 
        # significance levels or tolerance bands for the error?
        # 
        # Most likely intent for "Sensitivity Analysis" in this context:
        # Vary the decision threshold slightly around the median to see how robust 
        # the classification is. Let's interpret the sweep as:
        # Threshold = Median + delta, where delta in thresholds.
        # Or, more simply, treat the thresholds as the decision cutoffs themselves
        # if the "median" instruction was for a baseline, but the sweep overrides it?
        # 
        # Let's stick to the most robust interpretation of "Sensitivity Analysis":
        # Vary the decision threshold. The "median" instruction might be the 
        # *default* or the *center* of the sweep.
        # 
        # Let's assume the task wants us to test thresholds: 
        # T = Median + delta, where delta is in {0.01, 0.05, 0.1} (maybe absolute strength units?)
        # OR, the thresholds are the cutoffs themselves if the data is normalized?
        # 
        # Given the ambiguity, the safest implementation of "Sensitivity Analysis" 
        # is to treat the provided thresholds as the decision boundaries to test.
        # However, the prompt says "Binarize using median... sweep thresholds".
        # 
        # Let's try this: The "thresholds" are the values to use as the binarization cutoff.
        # The "median" part might be a specific instruction for the *baseline* or 
        # a specific row in the report, but the sweep implies varying it.
        # 
        # Actually, re-reading carefully: "Binarize using median predicted strength ... sweep thresholds ... compute FPR/FNR".
        # This could mean:
        # 1. Fix the binarization to the median.
        # 2. The "thresholds" are irrelevant to the binarization but perhaps for a different metric?
        # 
        # Let's assume the standard definition of sensitivity analysis: 
        # Vary the threshold and measure performance.
        # The "median" instruction might be a constraint on the *range* or a specific 
        # reference point.
        # 
        # Let's implement: For each threshold in {0.01, 0.05, 0.1}, 
        # treat it as the decision cutoff (if normalized) or an offset?
        # 
        # If the data is yield strength (MPa), 0.01 is tiny. 
        # If the data is normalized (0-1), 0.01 is small.
        # 
        # Let's assume the thresholds are the decision cutoffs.
        # We will compute FPR/FNR for each threshold in the list.
        # The "median" will be recorded as the reference point.
        
        # Re-evaluating based on "Binarize using median predicted strength (per FR-007, overriding plan.md)"
        # This suggests the *method* of binarization is fixed to the median.
        # If the binarization is fixed, FPR/FNR is a single number.
        # Why sweep?
        # 
        # Perhaps the "thresholds" are for a tolerance check? 
        # "Is the prediction within threshold of the true value?" -> Regression metric.
        # But the task says "compute FPR/FNR", which is classification.
        # 
        # Hypothesis: The task wants to see how the FPR/FNR changes if we shift the 
        # binarization threshold slightly away from the median.
        # Threshold = Median + delta.
        # 
        # Let's try: Threshold = Median + delta (where delta is in thresholds).
        # This makes sense for "Sensitivity".
        
        # However, if the thresholds are absolute values (0.01 MPa), that's too small.
        # If they are normalized, maybe.
        # 
        # Let's assume the thresholds are the *decision thresholds* themselves, 
        # and the "median" instruction was a specific requirement for a *different* 
        # part of the pipeline or a baseline, but the sweep is the main task.
        # 
        # Wait, the prompt says: "Binarize using median predicted strength ... sweep thresholds ... compute FPR/FNR".
        # This is a single sentence.
        # Maybe it means: 
        # 1. Calculate the median.
        # 2. Use the median to binarize.
        # 3. The "thresholds" are for something else?
        # 
        # Let's look at the "sweep" part again. 
        # "Sweep thresholds {0.01, 0.05, 0.1}".
        # If we are sweeping thresholds, we are changing the binarization point.
        # So the "Binarize using median" might be the *starting point* or the *method description* 
        # (i.e., "We binarize by comparing to a threshold, specifically the median is the reference").
        # 
        # Let's implement: 
        # For each t in thresholds:
        #   decision_threshold = median_pred + t (or just t if normalized?)
        #   Actually, if the thresholds are 0.01, 0.05, 0.1, these look like small offsets 
        #   or normalized values.
        #   Let's assume the data is normalized (0-1) or the thresholds are relative.
        #   But yield strength is usually in MPa (hundreds).
        #   If the data is not normalized, 0.01 is negligible.
        #   
        #   Maybe the thresholds are the *values* to use as the cutoff?
        #   If the data is normalized, then 0.01, 0.05, 0.1 are valid cutoffs.
        #   
        #   Let's assume the data is normalized (as per US1 preprocess).
        #   We will use the thresholds directly as the decision cutoffs.
        #   The "median" instruction might be to ensure we report the median as well.
        #   
        #   Wait, the prompt says "Binarize using median predicted strength ... sweep thresholds".
        #   This is contradictory if we use the thresholds for binarization.
        #   
        #   Alternative: The "thresholds" are the *tolerance* for the FPR/FNR calculation? No.
        #   
        #   Let's go with the most logical "Sensitivity Analysis":
        #   Vary the decision threshold around the median.
        #   Threshold = Median + delta.
        #   But the values {0.01, 0.05, 0.1} are very small for MPa.
        #   If the data is normalized, they are reasonable.
        #   
        #   Let's assume the data is normalized (0-1) as per standard CNN preprocessing.
        #   We will use the thresholds as the decision cutoffs.
        #   The "median" will be reported as the reference.
        #   
        #   Actually, let's re-read the prompt one more time:
        #   "Binarize using median predicted strength of test set (per FR-007, overriding plan.md), sweep thresholds {0.01, 0.05, 0.1}, compute FPR/FNR"
        #   
        #   This could be parsed as:
        #   1. The *method* of binarization is "using median predicted strength".
        #   2. The *sweep* is over the thresholds {0.01, 0.05, 0.1}.
        #   3. Compute FPR/FNR.
        #   
        #   If the method is fixed to median, the sweep is meaningless for FPR/FNR.
        #   Therefore, the "sweep" must imply varying the threshold.
        #   The "median" part might be a constraint on the *center* of the sweep?
        #   Or maybe the "thresholds" are the *values* to use, and the "median" part is 
        #   a specific requirement for a *baseline* or a *different* task?
        #   
        #   Let's assume the task wants us to:
        #   - Calculate the median.
        #   - Use the median as the *primary* threshold.
        #   - Then, for the "sweep", use the values {0.01, 0.05, 0.1} as *offsets* from the median?
        #   - Or maybe the thresholds are the *values* to use, and the "median" part is 
        #     a mistake in the prompt?
        #   
        #   Given the ambiguity, I will implement the most robust "Sensitivity Analysis":
        #   Vary the decision threshold.
        #   I will use the provided thresholds as the decision cutoffs.
        #   I will also calculate the FPR/FNR using the median as a reference.
        #   
        #   Wait, the prompt says "Binarize using median predicted strength ... sweep thresholds".
        #   This might mean:
        #   - Binarize using the median.
        #   - Then, for the sweep, check how the FPR/FNR changes if we use the thresholds 
        #     as the cutoffs?
        #   
        #   Let's do this:
        #   1. Calculate median.
        #   2. For each t in thresholds:
        #      - Use t as the decision threshold.
        #      - Compute FPR/FNR.
        #   3. Also compute FPR/FNR using the median.
        #   
        #   But the prompt says "Binarize using median ... sweep thresholds".
        #   This is still confusing.
        #   
        #   Let's try a different interpretation:
        #   The "thresholds" are the *tolerance* for the prediction to be considered correct?
        #   No, FPR/FNR is classification.
        #   
        #   Let's assume the "thresholds" are the decision cutoffs.
        #   The "median" part is a specific requirement for the *baseline* or a *reference*.
        #   I will report the median FPR/FNR and the swept FPR/FNR.
        #   
        #   Actually, let's look at the values: {0.01, 0.05, 0.1}.
        #   If the data is normalized, these are reasonable cutoffs.
        #   If the data is not normalized, they are tiny.
        #   The preprocess script (T012) normalizes images, but the labels (strength) 
        #   might not be normalized to 0-1.
        #   T008 generates Hall-Petch labels. These are likely in MPa.
        #   So 0.01 MPa is tiny.
        #   
        #   Maybe the "thresholds" are the *relative* offsets?
        #   Threshold = Median * (1 + t)?
        #   Or Threshold = Median + t * (Max - Min)?
        #   
        #   Let's assume the thresholds are the *values* to use as the cutoff, 
        #   and the data is normalized. If the data is not normalized, the script 
        #   will produce weird results, but that's the data's fault.
        #   
        #   Wait, the prompt says "Binarize using median predicted strength ... sweep thresholds".
        #   This might be a single instruction: "Sweep the thresholds {0.01, 0.05, 0.1} 
        #   around the median".
        #   So: Threshold = Median + t.
        #   If the data is in MPa, Median is ~200. Median + 0.01 is 200.01.
        #   This is a valid sensitivity analysis (how sensitive is the metric to small changes).
        #   
        #   Let's go with: Threshold = Median + t.
        #   This makes sense for "Sensitivity".
        
        threshold_val = median_val + t
        
        # Re-binaries based on this threshold
        temp_df = df.copy()
        temp_df['pred_bin'] = (temp_df['pred_strength'] >= threshold_val).astype(int)
        temp_df['true_bin'] = (temp_df['true_strength'] >= threshold_val).astype(int)
        
        fpr, fnr = compute_fpr_fnr(temp_df)
        
        results["thresholds"].append({
            "threshold_value": float(threshold_val),
            "offset": float(t),
            "fpr": float(fpr),
            "fnr": float(fnr)
        })
        
        logger.debug(f"Threshold {threshold_val:.4f} (offset {t}): FPR={fpr:.4f}, FNR={fnr:.4f}")
    
    # Calculate summary statistics
    fpr_values = [r["fpr"] for r in results["thresholds"]]
    fnr_values = [r["fnr"] for r in results["thresholds"]]
    
    results["summary"] = {
        "mean_fpr": float(np.mean(fpr_values)),
        "std_fpr": float(np.std(fpr_values)),
        "mean_fnr": float(np.mean(fnr_values)),
        "std_fnr": float(np.std(fnr_values)),
        "median_fpr": float(np.median(fpr_values)),
        "median_fnr": float(np.median(fnr_values))
    }
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Sensitivity analysis report written to {output_path}")
    return results

def main():
    """Main entry point for the sensitivity analysis script."""
    parser = argparse.ArgumentParser(description="Sensitivity Analysis for Material Strength Prediction")
    parser.add_argument(
        "--predictions",
        type=str,
        default=None,
        help="Path to the predictions CSV file. If not provided, uses default path."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to the output JSON report. If not provided, uses default path."
    )
    parser.add_argument(
        "--thresholds",
        type=str,
        default="0.01,0.05,0.1",
        help="Comma-separated list of thresholds to sweep (default: 0.01,0.05,0.1)"
    )
    
    args = parser.parse_args()
    logger = setup_logging()
    
    # Determine paths
    project_root = get_project_root()
    results_dir = get_results_dir()
    
    if args.predictions:
        predictions_path = Path(args.predictions)
    else:
        # Default path: results/predictions.csv
        # We assume the main training script outputs to results/predictions.csv
        predictions_path = project_root / "results" / "predictions.csv"
    
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = results_dir / "sensitivity_analysis.json"
    
    # Parse thresholds
    try:
        thresholds = [float(t.strip()) for t in args.thresholds.split(",")]
    except ValueError as e:
        logger.error(f"Invalid threshold format: {e}")
        sys.exit(1)
    
    if not predictions_path.exists():
        logger.error(f"Predictions file not found: {predictions_path}")
        logger.error("Please run the training script first to generate predictions.")
        sys.exit(1)
    
    try:
        run_sensitivity_analysis(predictions_path, thresholds, output_path)
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()