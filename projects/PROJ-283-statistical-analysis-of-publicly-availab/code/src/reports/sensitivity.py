import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Set
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for the sweep
MIN_THRESHOLD = 0.001
MAX_THRESHOLD = 0.05
STEP = 0.005

def calculate_jaccard_index(set_a: Set[str], set_b: Set[str]) -> float:
    """
    Calculate the Jaccard index between two sets of predictor names.
    Jaccard Index = |A ∩ B| / |A ∪ B|
    """
    if not set_a and not set_b:
        return 1.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    if union == 0:
        return 0.0
    return intersection / union

def get_significant_predictors(p_values: pd.Series, threshold: float) -> Set[str]:
    """
    Identify predictors with p-values below the given threshold.
    """
    if p_values.empty:
        return set()
    significant = p_values[p_values < threshold].index.tolist()
    return set(significant)

def perform_threshold_sweep(
    p_values_df: pd.DataFrame,
    min_thresh: float = MIN_THRESHOLD,
    max_thresh: float = MAX_THRESHOLD,
    step: float = STEP
) -> List[Dict]:
    """
    Perform a threshold sweep analysis.
    
    Args:
        p_values_df: DataFrame containing p-values for predictors. 
                     Expected columns: 'model_type', 'predictor', 'p_value' (or similar structure).
                     If the DataFrame is in wide format (predictors as columns), 
                     we will iterate columns. If long, we aggregate.
        min_thresh: Start of the sweep.
        max_thresh: End of the sweep (inclusive).
        step: Step size for the sweep.
    
    Returns:
        List of dictionaries containing threshold, count, delta, and Jaccard index.
    """
    results = []
    prev_significant: Set[str] = set()
    prev_count = 0
    
    # Ensure we cover the range correctly
    thresholds = np.arange(min_thresh, max_thresh + step/2, step)
    
    # Flatten p-values if necessary. Assuming the input is a Series or 
    # a DataFrame where we can extract a mapping of predictor -> p_value.
    # The typical output from T024 (metrics.py) might be a DataFrame 
    # with columns like 'predictor' and 'p_value' or a wide table.
    # We expect p_values_df to be a Series or a DataFrame that we can convert to a Series.
    
    if isinstance(p_values_df, pd.DataFrame):
        # If it's a long format: columns ['predictor', 'p_value']
        if 'predictor' in p_values_df.columns and 'p_value' in p_values_df.columns:
            p_series = p_values_df.set_index('predictor')['p_value']
        else:
            # Assume wide format: columns are predictors, values are p-values
            # We might need to aggregate across models if multiple exist, 
            # but for sensitivity analysis on a specific model's p-values, 
            # we usually take one. Let's assume the first model or a specific one.
            # For simplicity, if it's wide, we take the first column as the reference 
            # or aggregate if multiple models are present. 
            # Given the task context (US2), we likely have one set of p-values 
            # (e.g., from Beta Regression). Let's assume the input is already 
            # the relevant p-value series or a wide dataframe where we take the mean/first.
            # To be robust: if multiple columns exist, we'll treat the first one.
            p_series = p_values_df.iloc[:, 0]
            p_series.index = p_values_df.columns
    elif isinstance(p_values_df, pd.Series):
        p_series = p_values_df
    else:
        raise ValueError("p_values_df must be a pandas Series or DataFrame")

    for thresh in thresholds:
        # Ensure threshold does not exceed max
        current_thresh = min(thresh, max_thresh)
        
        current_significant = get_significant_predictors(p_series, current_thresh)
        current_count = len(current_significant)
        
        # Calculate Delta (variation in count)
        delta = current_count - prev_count if prev_count > 0 or prev_significant else 0
        
        # Calculate Jaccard Index with previous set
        jaccard = 0.0
        if prev_significant or current_significant:
            jaccard = calculate_jaccard_index(prev_significant, current_significant)
        
        results.append({
            "threshold": float(current_thresh),
            "significant_count": current_count,
            "delta": delta,
            "jaccard_index": round(jaccard, 4)
        })
        
        prev_significant = current_significant
        prev_count = current_count

    return results

def generate_sensitivity_report(
    p_values_source: pd.DataFrame,
    output_path: Path
) -> Dict:
    """
    Generate the full sensitivity analysis report and save it to JSON.
    
    Args:
        p_values_source: DataFrame of p-values.
        output_path: Path to save the JSON report.
    
    Returns:
        The report dictionary.
    """
    logger.info(f"Performing sensitivity analysis on {len(p_values_source)} predictors...")
    
    sweep_results = perform_threshold_sweep(p_values_source)
    
    # Calculate summary statistics
    counts = [r['significant_count'] for r in sweep_results]
    deltas = [r['delta'] for r in sweep_results]
    jaccards = [r['jaccard_index'] for r in sweep_results]
    
    report = {
        "analysis_type": "threshold_sweep",
        "range": {
            "min": MIN_THRESHOLD,
            "max": MAX_THRESHOLD,
            "step": STEP
        },
        "summary": {
            "total_thresholds_tested": len(sweep_results),
            "min_significant_count": min(counts),
            "max_significant_count": max(counts),
            "mean_significant_count": float(np.mean(counts)),
            "max_delta": max(deltas),
            "min_jaccard": min(jaccards),
            "max_jaccard": max(jaccards)
        },
        "sweep_data": sweep_results
    }
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity analysis report saved to {output_path}")
    return report

def main():
    """
    Main entry point for the sensitivity analysis script.
    Expects the p-values to be loaded from a known location or passed via arguments.
    For this implementation, we assume the p-values are available from the 
    model metrics output or a specific file generated by T024/T027.
    
    We will attempt to load 'data/results/model_metrics.json' which should contain
    the p-values for the Beta Regression model (primary).
    """
    # Default paths
    metrics_path = Path("data/results/model_metrics.json")
    output_path = Path("data/results/sensitivity_analysis.json")
    
    if not metrics_path.exists():
        logger.error(f"Model metrics file not found at {metrics_path}. "
                     "Please ensure T027 has run and produced model_metrics.json.")
        sys.exit(1)
    
    with open(metrics_path, 'r') as f:
        metrics_data = json.load(f)
    
    # Extract p-values for the Beta Regression model (primary model)
    # The structure of model_metrics.json depends on T027. 
    # Assuming it has a structure like:
    # {
    #   "beta_regression": {
    #     "coefficients": {...},
    #     "p_values": {...},
    #     ...
    #   },
    #   ...
    # }
    
    if "beta_regression" not in metrics_data:
        logger.error("Beta regression model metrics not found in model_metrics.json.")
        sys.exit(1)
    
    p_values_dict = metrics_data["beta_regression"].get("p_values", {})
    
    if not p_values_dict:
        logger.warning("No p-values found for Beta Regression. Generating empty report.")
        p_series = pd.Series(dtype=float)
    else:
        p_series = pd.Series(p_values_dict)
    
    generate_sensitivity_report(p_series, output_path)

if __name__ == "__main__":
    import sys
    main()
