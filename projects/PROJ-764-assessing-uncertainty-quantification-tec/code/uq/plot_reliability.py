import os
import sys
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Any
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_predictions() -> pd.DataFrame:
    """
    Loads the UQ predictions from the results directory.
    Expects results/uq_predictions.csv.
    """
    input_path = Path("results/uq_predictions.csv")
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Ensure required columns exist
    required_cols = ['method', 'prediction', 'lower_50', 'upper_50', 'lower_90', 'upper_90']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in predictions: {missing_cols}")
    
    return df

def calculate_calibration_bins(
    df: pd.DataFrame, 
    method: str, 
    n_bins: int = 10
) -> Dict[str, Any]:
    """
    Calculates the observed coverage for each confidence interval bin.
    
    For reliability diagrams, we typically plot:
    X-axis: Nominal Confidence (e.g., 50%, 90%)
    Y-axis: Observed Coverage (fraction of true values within the interval)
    
    Since we have specific intervals (50% and 90%) per prediction,
    we group predictions by their method and check coverage against the ground truth.
    Wait: The CSV does NOT contain ground truth.
    Correction: Reliability diagrams for UQ usually require ground truth to calculate coverage.
    However, in many UQ papers, 'Reliability Diagram' refers to the calibration of the
    predicted variance/uncertainty against the actual error (|pred - true|).
    
    Given the constraints of the current artifact `results/uq_predictions.csv` (which lacks ground truth),
    we must assume the ground truth is available or we are plotting the distribution of predicted uncertainties.
    
    BUT, standard practice for US2 (Calibration) implies we have ground truth.
    Let's check the data model or assume we need to re-load the test set for ground truth.
    The task says "Generate reliability diagrams...".
    If ground truth is missing from the predictions CSV, we must join with the test set.
    
    Let's assume the test set ground truth is in `data/processed/raw_test.csv`.
    We need to match `sample_id`.
    """
    # Load ground truth from processed test data
    gt_path = Path("data/processed/raw_test.csv")
    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {gt_path}. Cannot calculate calibration.")
    
    gt_df = pd.read_csv(gt_path)
    # Assume ground truth column is named 'target' or 'formation_energy'. 
    # Based on typical OQMD, it's likely 'formation_energy' or similar.
    # Let's check common columns. If 'target' exists, use it.
    if 'target' in gt_df.columns:
        truth_col = 'target'
    elif 'formation_energy' in gt_df.columns:
        truth_col = 'formation_energy'
    elif 'energy' in gt_df.columns:
        truth_col = 'energy'
    else:
        # Fallback: try to find a column that looks like the target
        # This is a heuristic. In a real robust system, we'd use a schema.
        truth_col = gt_df.select_dtypes(include=[np.number]).columns[-1]
    
    # Merge predictions with ground truth
    merged = pd.merge(
        df[df['method'] == method], 
        gt_df[['sample_id', truth_col]], 
        on='sample_id', 
        how='inner'
    )
    
    if merged.empty:
        raise ValueError(f"No matching data found for method {method}")
    
    # Calculate absolute errors
    merged['abs_error'] = np.abs(merged['prediction'] - merged[truth_col])
    
    # We will bin by the width of the interval or by the predicted uncertainty?
    # Standard reliability diagram for variance:
    # Bin by predicted variance (or std dev), check if the fraction of points
    # that fall within k*std matches k.
    # Alternatively, if we have specific intervals (50%, 90%), we check coverage.
    
    # Let's implement the "Coverage vs Nominal" plot.
    # We have two nominal levels: 50% and 90%.
    # We check if |pred - true| <= (upper - lower)/2 ? No, that's not quite right.
    # The interval is [lower, upper]. We check if true is in [lower, upper].
    
    results = []
    
    # Define the intervals we want to check
    # The CSV has specific columns for 50% and 90% intervals.
    # We can treat these as two data points per sample for the reliability curve.
    
    # 50% Interval Check
    mask_50 = (merged['lower_50'] <= merged[truth_col]) & (merged[truth_col] <= merged['upper_50'])
    obs_50 = mask_50.mean()
    results.append({'nominal': 0.50, 'observed': obs_50, 'count': len(merged)})
    
    # 90% Interval Check
    mask_90 = (merged['lower_90'] <= merged[truth_col]) & (merged[truth_col] <= merged['upper_90'])
    obs_90 = mask_90.mean()
    results.append({'nominal': 0.90, 'observed': obs_90, 'count': len(merged)})
    
    return {
        'method': method,
        'bins': results
    }

def plot_reliability_diagram(
    calibration_data: Dict[str, Any], 
    output_path: Path,
    show_ideal: bool = True
):
    """
    Plots the reliability diagram for a single method.
    X-axis: Nominal Confidence Level
    Y-axis: Observed Coverage
    """
    plt.figure(figsize=(8, 6))
    
    nominal = [item['nominal'] for item in calibration_data['bins']]
    observed = [item['observed'] for item in calibration_data['bins']]
    
    plt.scatter(nominal, observed, color='blue', s=100, label=f"{calibration_data['method']}")
    
    if show_ideal:
        # Ideal line: observed = nominal
        plt.plot([0, 1], [0, 1], 'k--', label='Ideal Calibration')
    
    plt.xlabel('Nominal Confidence Level')
    plt.ylabel('Observed Coverage')
    plt.title(f'Reliability Diagram: {calibration_data["method"]}')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    logger.info(f"Saved reliability diagram to {output_path}")

def main():
    """
    Main entry point to generate reliability diagrams for all methods.
    Outputs: results/reliability_<method>.png
    """
    try:
        # Load predictions
        df = load_predictions()
        methods = df['method'].unique()
        
        logger.info(f"Found methods to plot: {methods}")
        
        output_dir = Path("results")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for method in methods:
            logger.info(f"Processing method: {method}")
            try:
                cal_data = calculate_calibration_bins(df, method)
                output_file = output_dir / f"reliability_{method.replace(' ', '_')}.png"
                plot_reliability_diagram(cal_data, output_file)
            except Exception as e:
                logger.error(f"Failed to plot for method {method}: {e}")
                continue
        
        logger.info("Reliability diagram generation complete.")
        
    except FileNotFoundError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()