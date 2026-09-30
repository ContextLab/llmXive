import os
import sys
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_predictions(input_path: str) -> pd.DataFrame:
    """
    Load the aggregated UQ predictions from CSV.
    
    Args:
        input_path: Path to the CSV file (e.g., results/uq_predictions_decomposed.csv)
        
    Returns:
        DataFrame with predictions and uncertainty estimates
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Predictions file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} predictions from {input_path}")
    return df

def calculate_calibration_bins(
    predictions: pd.DataFrame,
    method: str,
    n_bins: int = 10
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculate calibration bins for a specific method.
    
    Groups predictions into bins based on predicted probability/confidence
    and calculates the empirical accuracy (fraction of correct predictions)
    within each bin.
    
    For regression with uncertainty, we use the coverage of prediction intervals.
    
    Args:
        predictions: DataFrame with 'method', 'prediction', 'lower_50', 'upper_50', 
                     'lower_90', 'upper_90', and 'target' (actual value) columns
        method: The UQ method name to filter for
        n_bins: Number of bins to use (default 10)
        
    Returns:
        Tuple of (bin_edges, empirical_coverage, nominal_coverage)
    """
    # Filter for the specific method
    method_df = predictions[predictions['method'] == method].copy()
    
    if len(method_df) == 0:
        raise ValueError(f"No predictions found for method: {method}")
    
    # We need the actual target values to compute coverage
    # Assuming the target column is named 'target' or we need to infer it
    if 'target' not in method_df.columns:
        # Try to find a column that looks like the target
        target_cols = [col for col in method_df.columns if 'target' in col.lower() or 'actual' in col.lower()]
        if target_cols:
            target_col = target_cols[0]
            method_df['target'] = method_df[target_col]
        else:
            raise KeyError("Could not find target column in predictions. Required for calibration.")
    
    # Calculate coverage for 50% and 90% intervals
    # For each sample, check if target falls within the interval
    method_df['covered_50'] = (method_df['target'] >= method_df['lower_50']) & (method_df['target'] <= method_df['upper_50'])
    method_df['covered_90'] = (method_df['target'] >= method_df['lower_90']) & (method_df['target'] <= method_df['upper_90'])
    
    # Sort by prediction uncertainty (variance) to create bins
    # Higher variance = lower confidence, so we bin by variance
    method_df = method_df.sort_values('variance')
    
    # Create bins based on variance quantiles
    method_df['bin'] = pd.qcut(method_df['variance'], q=n_bins, labels=False, duplicates='drop')
    
    # Calculate empirical coverage per bin
    bin_edges = []
    empirical_coverages = []
    nominal_coverages = []
    
    for i in range(n_bins):
        bin_data = method_df[method_df['bin'] == i]
        if len(bin_data) == 0:
            continue
        
        # Get bin edges
        bin_variances = bin_data['variance'].values
        bin_edges.append((bin_variances.min(), bin_variances.max()))
        
        # Calculate empirical coverage
        emp_cov_50 = bin_data['covered_50'].mean()
        emp_cov_90 = bin_data['covered_90'].mean()
        
        # Use average of 50% and 90% for a general reliability measure
        # Or we can plot both separately
        empirical_coverages.append((emp_cov_50 + emp_cov_90) / 2.0)
        nominal_coverages.append(0.7)  # Average nominal coverage (50% and 90%)
    
    # Convert to arrays
    bin_edges = np.array(bin_edges)
    empirical_coverages = np.array(empirical_coverages)
    nominal_coverages = np.array(nominal_coverages)
    
    return bin_edges, empirical_coverages, nominal_coverages

def plot_reliability_diagram(
    bin_edges: np.ndarray,
    empirical_coverages: np.ndarray,
    nominal_coverages: np.ndarray,
    method_name: str,
    output_path: str,
    title: Optional[str] = None
) -> None:
    """
    Create and save a reliability diagram for a single method.
    
    Args:
        bin_edges: Array of (min, max) tuples for each bin
        empirical_coverages: Empirical coverage values for each bin
        nominal_coverages: Nominal coverage values for each bin
        method_name: Name of the UQ method
        output_path: Path to save the plot
        title: Optional custom title
    """
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Plot the reliability curve
    x_centers = [(edge[0] + edge[1]) / 2 for edge in bin_edges]
    ax.plot(x_centers, empirical_coverages, 'bo-', label='Empirical Coverage', linewidth=2, markersize=8)
    
    # Plot the ideal diagonal line
    ax.plot([0, 1], [0, 1], 'r--', label='Ideal Calibration', linewidth=2)
    
    # Fill area between nominal and empirical (optional visualization)
    ax.fill_between(x_centers, nominal_coverages, empirical_coverages, alpha=0.2, color='gray')
    
    # Labels and title
    ax.set_xlabel('Nominal Coverage (Confidence Level)', fontsize=12)
    ax.set_ylabel('Empirical Coverage (Actual Accuracy)', fontsize=12)
    ax.set_title(title or f'Reliability Diagram: {method_name}', fontsize=14)
    ax.legend(loc='upper left')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([0, 1])
    ax.set_ylim([0, 1])
    
    # Add annotations for each point
    for i, (x, y) in enumerate(zip(x_centers, empirical_coverages)):
        ax.annotate(f'{y:.2f}', (x, y), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Reliability diagram saved to {output_path}")

def main():
    """
    Main function to generate reliability diagrams for all UQ methods.
    
    Reads from results/uq_predictions_decomposed.csv and generates
    reliability diagrams for each unique method.
    """
    # Define paths
    input_path = "results/uq_predictions_decomposed.csv"
    output_dir = Path("results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load predictions
    try:
        predictions = load_predictions(input_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading predictions: {e}")
        sys.exit(1)
    
    # Get unique methods
    methods = predictions['method'].unique()
    logger.info(f"Found {len(methods)} methods: {methods}")
    
    # Generate reliability diagram for each method
    for method in methods:
        try:
            logger.info(f"Processing method: {method}")
            
            # Calculate calibration bins
            bin_edges, empirical_coverages, nominal_coverages = calculate_calibration_bins(
                predictions, method, n_bins=10
            )
            
            # Generate output filename
            safe_method_name = method.replace(" ", "_").replace("-", "_").lower()
            output_filename = f"reliability_diagram_{safe_method_name}.png"
            output_path = str(output_dir / output_filename)
            
            # Create and save the plot
            plot_reliability_diagram(
                bin_edges, 
                empirical_coverages, 
                nominal_coverages, 
                method, 
                output_path,
                title=f"Reliability Diagram: {method}"
            )
            
            logger.info(f"Successfully generated {output_filename}")
            
        except Exception as e:
            logger.error(f"Failed to generate reliability diagram for {method}: {e}")
            continue
    
    logger.info("All reliability diagrams generated successfully.")

if __name__ == "__main__":
    main()