"""
Benjamini-Hochberg Correction for Multiple Comparisons.

This module implements the Benjamini-Hochberg (BH) procedure to control the
False Discovery Rate (FDR) when performing multiple hypothesis tests across
EEG electrodes.

It reads raw p-values from the analysis results, applies the BH correction,
and saves the adjusted p-values and significance status to a CSV file.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import os
import sys
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/bh_correction.log')
    ]
)
logger = logging.getLogger(__name__)

def load_config(config_path='code/config.yaml'):
    """Load pipeline configuration."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML: {e}")
        return {}

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Apply the Benjamini-Hochberg correction to a list of p-values.

    Parameters
    ----------
    p_values : list or np.array
        Raw p-values from hypothesis tests.
    alpha : float
        Desired FDR level (default 0.05).

    Returns
    -------
    pd.DataFrame
        DataFrame containing original p-values, adjusted p-values (q-values),
        and a boolean indicating significance.
    """
    p_values = np.array(p_values)
    n = len(p_values)

    if n == 0:
        logger.warning("No p-values provided for BH correction.")
        return pd.DataFrame(columns=['p_value', 'adj_p_value', 'significant'])

    # Create a DataFrame to track indices
    df = pd.DataFrame({
        'original_p': p_values,
        'rank': np.arange(1, n + 1)
    })

    # Sort by p-value
    df = df.sort_values('original_p').reset_index(drop=True)

    # Calculate BH adjusted p-values (q-values)
    # q_i = min( (n/i) * p_i, q_{i+1} ) working backwards
    # Standard formula: p_adj[i] = p[i] * n / rank[i]
    # Then enforce monotonicity: p_adj[i] = min(p_adj[i], p_adj[i+1])
    
    # Calculate raw adjusted values
    df['adj_p_value'] = df['original_p'] * n / df['rank']

    # Enforce monotonicity (ensure p_adj[i] <= p_adj[i+1])
    # We iterate backwards from the largest rank to the smallest
    for i in range(n - 2, -1, -1):
        df.loc[i, 'adj_p_value'] = min(
            df.loc[i, 'adj_p_value'], 
            df.loc[i + 1, 'adj_p_value']
        )

    # Cap values at 1.0
    df['adj_p_value'] = df['adj_p_value'].clip(upper=1.0)

    # Determine significance
    df['significant'] = df['adj_p_value'] <= alpha

    # Sort back to original order (optional, but good for consistency)
    # However, usually we want to return in the order of the input or sorted by p-value.
    # Let's return sorted by original p-value for clarity in the report.
    
    return df[['original_p', 'adj_p_value', 'significant']]

def main():
    """
    Main execution flow:
    1. Load configuration.
    2. Load analysis results (p-values).
    3. Apply BH correction.
    4. Save results to data/analysis/bh_correction_results.csv.
    """
    logger.info("Starting Benjamini-Hochberg correction pipeline.")
    
    config = load_config()
    alpha = config.get('alpha', 0.05)
    
    # Define input and output paths
    # The analysis.py task (T019) should produce a file with p-values.
    # Based on the schema in T018/T019, we expect a file like data/analysis/correlation_results.csv
    # containing columns: channel, r_value, p_value, etc.
    input_path = Path('data/analysis/correlation_results.csv')
    output_dir = Path('data/analysis')
    output_path = output_dir / 'bh_correction_results.csv'
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Cannot proceed without correlation results. Ensure T019/analysis.py has run successfully.")
        sys.exit(1)

    try:
        # Load the correlation results
        results_df = pd.read_csv(input_path)
        
        required_cols = ['channel', 'p_value']
        missing_cols = [c for c in required_cols if c not in results_df.columns]
        if missing_cols:
            logger.error(f"Missing required columns in {input_path}: {missing_cols}")
            sys.exit(1)

        logger.info(f"Loaded {len(results_df)} p-values from {input_path}")
        
        # Extract p-values
        p_values = results_df['p_value'].values
        channels = results_df['channel'].values

        # Run BH correction
        bh_results = run_benjamini_hochberg(p_values, alpha=alpha)
        
        # Merge channel info back
        bh_results['channel'] = channels
        
        # Reorder columns for the final output
        final_df = bh_results[['channel', 'original_p', 'adj_p_value', 'significant']]
        
        # Save to CSV
        final_df.to_csv(output_path, index=False)
        
        logger.info(f"Saved BH correction results to {output_path}")
        logger.info(f"Significant findings at alpha={alpha}: {final_df['significant'].sum()}")
        
        # Optional: Print summary
        significant_channels = final_df[final_df['significant']]['channel'].tolist()
        if significant_channels:
            logger.info(f"Significant electrodes: {significant_channels}")
        else:
            logger.info("No significant electrodes found after correction.")

    except Exception as e:
        logger.error(f"Error during BH correction: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
