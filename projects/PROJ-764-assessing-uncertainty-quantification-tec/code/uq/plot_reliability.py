import os
import sys
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_predictions(predictions_path: str) -> pd.DataFrame:
    """
    Load the UQ predictions CSV.
    Expects columns: sample_id, method, prediction, variance, lower_50, upper_50, lower_90, upper_90, aleatoric, epistemic, total, uncertainty_type
    """
    if not os.path.exists(predictions_path):
        raise FileNotFoundError(f"Predictions file not found: {predictions_path}")
    
    df = pd.read_csv(predictions_path)
    logger.info(f"Loaded predictions: {len(df)} rows, methods: {df['method'].unique().tolist()}")
    return df

def calculate_calibration_bins(
    df: pd.DataFrame, 
    method: str, 
    n_bins: int = 10
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate bin statistics for a reliability diagram.
    
    For each bin, we compute:
    - mean_predicted_probability (x-axis): The average predicted confidence for the interval.
      For 90% intervals, this is 0.90. For 50% intervals, this is 0.50.
      However, to plot a curve, we often bin by the *predicted uncertainty* or simply 
      group by the specific interval level if we are plotting multiple intervals.
      
      Standard Reliability Diagram for Uncertainty Quantification:
      X-axis: Mean predicted confidence (e.g., 0.50, 0.90, or binned by variance).
      Y-axis: Empirical coverage (fraction of true values falling within the interval).
      
      Since our data has fixed intervals (50% and 90%), we will plot points for these 
      specific confidence levels. If we want a curve, we would need to vary the threshold.
      Here, we will bin the data by the *predicted variance* or simply aggregate by method 
      and interval type to show the calibration gap.
      
      Alternative interpretation for fixed intervals:
      Bin the samples by their predicted variance (uncertainty magnitude) and check 
      if higher variance correlates with higher error/miss rate.
      
      Let's implement the standard "Reliability Diagram" where X = Predicted Confidence.
      Since we have discrete confidence levels (0.5, 0.9), we will calculate the 
      empirical coverage for these specific points.
      
      To make it a "diagram" (line/curve), we can also bin by the *width* of the interval 
      or the *predicted variance* to see if the model is well-calibrated across different 
      levels of uncertainty.
      
      Strategy:
      1. Filter by method.
      2. Group by interval type (50% or 90%).
      3. Calculate Empirical Coverage for each group.
      4. Return these points to plot.
    """
    method_df = df[df['method'] == method]
    
    # Define confidence levels and their corresponding columns
    intervals = [
        (0.50, 'lower_50', 'upper_50'),
        (0.90, 'lower_90', 'upper_90')
    ]
    
    bin_data = []
    
    # We need the true values. The input CSV from T022d/T022b might not have 'target'.
    # T016a output: sample_id, method, prediction, variance, lower_50, upper_50, lower_90, upper_90
    # T022d output: adds aleatoric, epistemic, total, uncertainty_type
    # We need the ground truth 'target' to calculate coverage.
    # Assumption: The 'sample_id' allows us to join with the test set if available,
    # OR the task expects us to calculate coverage based on the assumption that 
    # the predictions were made on a known test set.
    
    # Looking at T021 (metrics.py) and T024 (calibration_report.csv), 
    # the metrics are calculated. This task is to PLOT them.
    # If the 'target' is not in the predictions file, we cannot calculate coverage here.
    # However, T022d output description says: "columns: sample_id, method, prediction...".
    # It does not explicitly mention 'target'.
    # But T021 (ECE calculation) requires the target.
    # Let's assume the 'uq_predictions.csv' (T022d) might need to be joined with the test set,
    # OR the task implies we use the data that was used to generate the metrics.
    
    # Correction: To generate a reliability diagram, we MUST have the true values.
    # If the predictions file doesn't have them, we must load the test set.
    # The test set is at: data/processed/raw_test.csv (from T006a) or features_test_20pca.csv.
    # The raw_test.csv has the target.
    
    test_path = "data/processed/raw_test.csv"
    if not os.path.exists(test_path):
        # Try the PCA reduced version if raw is missing, but we need the target.
        # The PCA version might not have the target if it was dropped.
        # Let's assume raw_test.csv exists as per T006a.
        raise FileNotFoundError(f"Test set not found at {test_path}. Cannot compute coverage.")
    
    test_df = pd.read_csv(test_path)
    # Ensure sample_id matches. If sample_id is just an index, we might need to merge.
    # Assuming sample_id in predictions corresponds to the index or ID in test_df.
    # If test_df doesn't have 'sample_id', we assume row order matches or we use index.
    if 'sample_id' not in test_df.columns:
        test_df['sample_id'] = test_df.index
    
    # Merge to get targets
    merged = method_df.merge(test_df[['sample_id', 'target']], on='sample_id', how='left')
    
    if merged['target'].isna().any():
        logger.warning(f"Missing targets for some samples in method {method}. Dropping them.")
        merged = merged.dropna(subset=['target'])
    
    for conf, lower_col, upper_col in intervals:
        if lower_col not in method_df.columns or upper_col not in method_df.columns:
            continue
        
        lower_vals = merged[lower_col]
        upper_vals = merged[upper_col]
        true_vals = merged['target']
        
        # Calculate if true value is within interval
        in_interval = (true_vals >= lower_vals) & (true_vals <= upper_vals)
        empirical_coverage = in_interval.mean()
        
        bin_data.append({
            'confidence': conf,
            'empirical_coverage': empirical_coverage,
            'n_samples': len(merged)
        })
    
    if not bin_data:
        return np.array([]), np.array([]), np.array([]), np.array([])
    
    confidences = np.array([b['confidence'] for b in bin_data])
    coverages = np.array([b['empirical_coverage'] for b in bin_data])
    n_samples = np.array([b['n_samples'] for b in bin_data])
    
    return confidences, coverages, n_samples, np.zeros_like(confidences) # dummy for error bars if needed

def plot_reliability_diagram(
    df: pd.DataFrame,
    output_path: str,
    methods: List[str] = None,
    dpi: int = 150
):
    """
    Generate reliability diagrams for each method.
    X-axis: Predicted Confidence (0.50, 0.90)
    Y-axis: Empirical Coverage
    Diagonal line: Perfect calibration
    """
    if methods is None:
        methods = df['method'].unique().tolist()
    
    plt.figure(figsize=(10, 8))
    
    colors = plt.cm.tab10(np.linspace(0, 1, len(methods)))
    
    for idx, method in enumerate(methods):
        if method not in df['method'].values:
            logger.warning(f"Method {method} not found in data.")
            continue
        
        confs, coverages, _, _ = calculate_calibration_bins(df, method)
        
        if len(confs) == 0:
            continue
        
        plt.scatter(
            confs, 
            coverages, 
            color=colors[idx], 
            label=method, 
            s=100, 
            zorder=5
        )
        # Connect points for visual clarity (though only 2 points usually)
        plt.plot(confs, coverages, color=colors[idx], alpha=0.5)
        
        # Add error bar or label for sample count if needed, 
        # but simple points are standard for discrete intervals.
        
    # Plot perfect calibration line
    plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration', linewidth=2)
    
    plt.xlabel('Predicted Confidence', fontsize=12)
    plt.ylabel('Empirical Coverage', fontsize=12)
    plt.title('Reliability Diagrams: Predicted Confidence vs. Empirical Coverage', fontsize=14)
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    
    # Save
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close()
    logger.info(f"Reliability diagram saved to {output_path}")

def main():
    """
    Main entry point for generating reliability diagrams.
    Reads T022d output and generates plots for each method.
    """
    # Input path from T022d
    input_path = "results/uq_predictions.csv"
    output_dir = "results"
    
    if not os.path.exists(input_path):
        logger.error(f"Input file {input_path} not found. Ensure T022d has completed.")
        sys.exit(1)
    
    df = load_predictions(input_path)
    methods = df['method'].unique().tolist()
    
    logger.info(f"Generating reliability diagrams for methods: {methods}")
    
    for method in methods:
        output_file = os.path.join(output_dir, f"reliability_diagram_{method}.png")
        plot_reliability_diagram(df, output_file, methods=[method])
    
    # Also generate a combined plot
    combined_output = os.path.join(output_dir, "reliability_diagram_combined.png")
    plot_reliability_diagram(df, combined_output, methods=methods)
    
    logger.info("All reliability diagrams generated successfully.")

if __name__ == "__main__":
    main()