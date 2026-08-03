import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def setup_logger(name, log_file="logs/pipeline.log", level=logging.INFO):
    """Set up a logger that writes to both file and console."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Perform Benjamini-Hochberg correction for multiple comparisons.
    
    Parameters:
    -----------
    p_values : array-like
        Array of raw p-values.
    alpha : float
        False Discovery Rate (FDR) threshold.
        
    Returns:
    --------
    dict
        Dictionary containing:
        - 'adjusted_p_values': array of BH-adjusted p-values
        - 'is_significant': boolean array indicating significance at alpha
        - 'num_significant': count of significant results
    """
    p_values = np.array(p_values)
    n = len(p_values)
    
    if n == 0:
        return {
            'adjusted_p_values': np.array([]),
            'is_significant': np.array([], dtype=bool),
            'num_significant': 0
        }
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH critical values
    # For each p-value at rank i (1-indexed), critical value is (i/n) * alpha
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha
    
    # Find the largest k such that p_(k) <= critical_(k)
    # We work backwards from the largest p-value
    is_significant_sorted = np.zeros(n, dtype=bool)
    found_significant = False
    
    for i in range(n - 1, -1, -1):
        if sorted_p_values[i] <= critical_values[i]:
            # All p-values with rank <= i are significant
            is_significant_sorted[:i+1] = True
            found_significant = True
            break
    
    # Map significance back to original order
    is_significant = np.zeros(n, dtype=bool)
    is_significant[sorted_indices] = is_significant_sorted
    
    # Calculate adjusted p-values
    # adjusted_p[i] = min( (n/i) * p[i], 1.0 ) for sorted p-values
    # We ensure monotonicity by taking cumulative min from the end
    adjusted_sorted = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adjusted_sorted[i] = sorted_p_values[i] * n / rank
    
    # Ensure monotonicity: adjusted p-values must be non-decreasing
    for i in range(n - 2, -1, -1):
        adjusted_sorted[i] = min(adjusted_sorted[i], adjusted_sorted[i+1])
    
    # Clip to [0, 1]
    adjusted_sorted = np.clip(adjusted_sorted, 0, 1)
    
    # Map back to original order
    adjusted_p_values = np.zeros(n)
    adjusted_p_values[sorted_indices] = adjusted_sorted
    
    num_significant = int(np.sum(is_significant))
    
    return {
        'adjusted_p_values': adjusted_p_values,
        'is_significant': is_significant,
        'num_significant': num_significant
    }

def main():
    """Main entry point for Benjamini-Hochberg correction task."""
    logger = setup_logger("benjamini_hochberg")
    logger.info("Starting Benjamini-Hochberg correction pipeline")
    
    try:
        config = load_config()
        alpha = config.get('fdr_threshold', 0.05)
        
        # Load analysis results containing p-values
        # Expected location based on pipeline flow
        analysis_results_path = Path("data/analysis/correlation_results.csv")
        
        if not analysis_results_path.exists():
            logger.error(f"Analysis results file not found: {analysis_results_path}")
            logger.error("Run code/analysis.py first to generate correlation results.")
            sys.exit(1)
        
        df = pd.read_csv(analysis_results_path)
        
        # Identify columns containing p-values
        p_value_cols = [col for col in df.columns if 'p_value' in col.lower()]
        
        if not p_value_cols:
            logger.error("No p-value columns found in analysis results.")
            logger.error(f"Available columns: {list(df.columns)}")
            sys.exit(1)
        
        logger.info(f"Found p-value columns: {p_value_cols}")
        
        # Apply BH correction to each p-value column
        output_rows = []
        
        for col in p_value_cols:
            logger.info(f"Processing {col}")
            p_vals = df[col].dropna().values
            
            if len(p_vals) == 0:
                logger.warning(f"No valid p-values in {col}, skipping")
                continue
            
            result = run_benjamini_hochberg(p_vals, alpha=alpha)
            
            # Add adjusted p-values and significance to dataframe
            df[f"{col}_adjusted"] = result['adjusted_p_values']
            df[f"{col}_significant"] = result['is_significant']
            
            logger.info(f"  Significant results at alpha={alpha}: {result['num_significant']}/{len(p_vals)}")
            
            # Store summary for output
            output_rows.append({
                'metric': col,
                'raw_significant': int(df[col] <= alpha).sum(),
                'bh_adjusted_significant': result['num_significant'],
                'fdr_threshold': alpha
            })
        
        # Save corrected results
        output_path = Path("data/analysis/bh_corrected_results.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved BH-corrected results to {output_path}")
        
        # Save summary
        summary_df = pd.DataFrame(output_rows)
        summary_path = Path("data/analysis/bh_correction_summary.csv")
        summary_df.to_csv(summary_path, index=False)
        logger.info(f"Saved BH correction summary to {summary_path}")
        
        logger.info("Benjamini-Hochberg correction completed successfully")
        
    except Exception as e:
        logger.error(f"Error during BH correction: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
