import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import pandas as pd
import numpy as np
from scipy import stats

def setup_logging(log_file: str = "data/processed/correlation.log") -> logging.Logger:
    """Configure logging for the correlation analysis module."""
    logger = logging.getLogger("correlation_analysis")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def load_roi_betas(filepath: str = "data/processed/roi_betas.csv") -> pd.DataFrame:
    """
    Load auditory cortex activation (beta values) from the ROI extraction output.
    
    Expected columns: subject_id, mean_beta (or similar numeric column).
    Raises FileNotFoundError if the file does not exist.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Required ROI beta file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    # Ensure subject_id is string for merging
    if 'subject_id' in df.columns:
        df['subject_id'] = df['subject_id'].astype(str)
    return df

def load_learning_rate_slopes(filepath: str = "data/processed/learning_rates.csv") -> pd.DataFrame:
    """
    Load global learning rate proxy (slope) from the behavioral analysis output.
    
    Expected columns: subject_id, slope (or similar numeric column).
    Raises FileNotFoundError if the file does not exist.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Required learning rate file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    if 'subject_id' in df.columns:
        df['subject_id'] = df['subject_id'].astype(str)
    return df

def calculate_pearson_correlation(
    roi_betas: pd.DataFrame, 
    learning_rates: pd.DataFrame,
    roi_col: str = 'mean_beta',
    slope_col: str = 'slope'
) -> Tuple[float, float, pd.DataFrame]:
    """
    Calculate Pearson correlation between auditory cortex activation and learning rate.
    
    Args:
        roi_betas: DataFrame with subject_id and beta values.
        learning_rates: DataFrame with subject_id and slope values.
        roi_col: Column name in roi_betas containing the beta values.
        slope_col: Column name in learning_rates containing the slope values.
        
    Returns:
        Tuple of (correlation_coefficient, p_value, merged_dataframe).
        
    Raises:
        ValueError: If there are fewer than 2 valid pairs of data points.
    """
    # Merge on subject_id
    merged = pd.merge(
        roi_betas[['subject_id', roi_col]],
        learning_rates[['subject_id', slope_col]],
        on='subject_id',
        how='inner'
    )
    
    if len(merged) < 2:
        raise ValueError(f"Insufficient data points for correlation (n={len(merged)}). "
                         "Need at least 2 subjects with both ROI beta and learning rate data.")
    
    x = merged[roi_col].values
    y = merged[slope_col].values
    
    # Remove NaNs if any exist in the merged columns
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) < 2:
        raise ValueError(f"Insufficient valid data points after NaN removal (n={len(x_clean)}).")
    
    r, p_value = stats.pearsonr(x_clean, y_clean)
    
    return r, p_value, merged

def generate_scatter_plot(
    data: pd.DataFrame,
    roi_col: str = 'mean_beta',
    slope_col: str = 'slope',
    output_path: str = "figures/correlation_scatter.png",
    correlation_val: float = None,
    p_value: float = None
) -> None:
    """
    Generate a scatter plot of ROI beta vs. learning rate slope.
    
    Args:
        data: Merged DataFrame containing subject data.
        roi_col: Column name for x-axis (ROI beta).
        slope_col: Column name for y-axis (Learning rate slope).
        output_path: Path to save the plot.
        correlation_val: Optional correlation coefficient to display on plot.
        p_value: Optional p-value to display on plot.
    """
    import matplotlib.pyplot as plt
    
    plt.figure(figsize=(10, 6))
    plt.scatter(data[roi_col], data[slope_col], alpha=0.7, edgecolors='k')
    
    plt.xlabel('Auditory Cortex Activation (Mean Beta)')
    plt.ylabel('Global Learning Rate Slope (ms/trial)')
    plt.title('Brain-Behavior Correlation: Auditory Activation vs. Learning Rate')
    
    if correlation_val is not None and p_value is not None:
        annotation = f'r = {correlation_val:.3f}, p = {p_value:.3f}'
        plt.text(0.05, 0.95, annotation, transform=plt.gca().transAxes,
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()

def main():
    """
    Main entry point for Task T033: Calculate Pearson correlation between
    auditory cortex activation and learning rate proxy.
    
    Reads:
      - data/processed/roi_betas.csv
      - data/processed/learning_rates.csv
    
    Writes:
      - figures/correlation_scatter.png
      - data/processed/correlation_results.json
      - data/processed/correlation_data.csv (merged data)
    """
    logger = setup_logging()
    logger.info("Starting Task T033: Pearson Correlation Analysis")
    
    # File paths
    roi_betas_path = "data/processed/roi_betas.csv"
    learning_rates_path = "data/processed/learning_rates.csv"
    output_plot = "figures/correlation_scatter.png"
    output_json = "data/processed/correlation_results.json"
    output_csv = "data/processed/correlation_data.csv"
    
    try:
        # Load data
        logger.info(f"Loading ROI betas from {roi_betas_path}")
        roi_betas = load_roi_betas(roi_betas_path)
        logger.info(f"Loaded {len(roi_betas)} ROI beta records")
        
        logger.info(f"Loading learning rates from {learning_rates_path}")
        learning_rates = load_learning_rate_slopes(learning_rates_path)
        logger.info(f"Loaded {len(learning_rates)} learning rate records")
        
        # Determine column names dynamically if standard names differ
        # Look for the first numeric column that isn't subject_id
        roi_col = None
        for col in roi_betas.columns:
            if col != 'subject_id' and pd.api.types.is_numeric_dtype(roi_betas[col]):
                roi_col = col
                break
        
        slope_col = None
        for col in learning_rates.columns:
            if col != 'subject_id' and pd.api.types.is_numeric_dtype(learning_rates[col]):
                slope_col = col
                break
        
        if not roi_col or not slope_col:
            raise ValueError("Could not identify numeric columns for ROI beta or learning rate slope.")
        
        logger.info(f"Using columns: ROI='{roi_col}', Slope='{slope_col}'")
        
        # Calculate correlation
        logger.info("Calculating Pearson correlation...")
        r, p_val, merged_data = calculate_pearson_correlation(
            roi_betas, learning_rates, roi_col=roi_col, slope_col=slope_col
        )
        
        logger.info(f"Correlation Results: r = {r:.4f}, p = {p_val:.4f}")
        
        # Save results to JSON
        results = {
            "task_id": "T033",
            "correlation_coefficient": float(r),
            "p_value": float(p_val),
            "n_subjects": len(merged_data),
            "roi_column": roi_col,
            "slope_column": slope_col
        }
        
        with open(output_json, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved correlation results to {output_json}")
        
        # Save merged data to CSV
        merged_data.to_csv(output_csv, index=False)
        logger.info(f"Saved merged data to {output_csv}")
        
        # Generate plot
        logger.info(f"Generating scatter plot at {output_plot}")
        generate_scatter_plot(
            merged_data, 
            roi_col=roi_col, 
            slope_col=slope_col,
            output_path=output_plot,
            correlation_val=r,
            p_value=p_val
        )
        logger.info(f"Saved scatter plot to {output_plot}")
        
        logger.info("Task T033 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        logger.error("Ensure T028 (roi_betas.csv) and T032 (learning_rates.csv) have been run successfully.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
