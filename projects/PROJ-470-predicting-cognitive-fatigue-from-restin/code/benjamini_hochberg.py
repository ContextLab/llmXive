"""
Benjamini-Hochberg Correction Implementation for Multiple Comparisons.

This module implements the Benjamini-Hochberg (BH) procedure to control the
False Discovery Rate (FDR) across multiple statistical tests (e.g., across electrodes).
It reads p-values from the analysis results, applies the correction, and saves
the adjusted p-values to a CSV file.

Dependencies:
    - pandas
    - numpy
    - pathlib
    - logging
    - os
    - yaml (for config)
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_path="code/config.yaml"):
    """Load pipeline configuration from YAML file."""
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Apply the Benjamini-Hochberg correction to a list/array of p-values.

    The BH procedure controls the False Discovery Rate (FDR).
    Steps:
    1. Sort p-values in ascending order.
    2. Calculate the critical value for each rank: (i / m) * alpha
    3. Find the largest k such that p_(k) <= (k / m) * alpha.
    4. Reject all hypotheses for ranks 1 to k.
    5. Adjusted p-values are calculated as: p_adj[i] = min(p_adj[j] for j >= i)

    Parameters:
        p_values (pd.Series or list): Array of raw p-values.
        alpha (float): Significance level (default 0.05).

    Returns:
        pd.DataFrame: DataFrame containing original p-values, adjusted p-values,
                      and significance status (True/False).
    """
    if not isinstance(p_values, pd.Series):
        p_values = pd.Series(p_values)

    if p_values.isna().any():
        logger.warning("Input p-values contain NaN. Dropping them for calculation.")
        p_values = p_values.dropna()

    if len(p_values) == 0:
        logger.warning("No valid p-values provided for BH correction.")
        return pd.DataFrame(columns=['p_value', 'p_adj', 'significant'])

    m = len(p_values)
    sorted_indices = p_values.argsort()
    sorted_p = p_values.iloc[sorted_indices]

    # Calculate BH adjusted p-values
    # Formula: p_adj[i] = min( (m/j) * p[j] for j >= i )
    # We compute the raw multiplier first, then take the cumulative minimum from the end
    ranks = np.arange(1, m + 1)
    raw_adj = (m / ranks) * sorted_p.values

    # Ensure monotonicity: p_adj[i] <= p_adj[i+1]
    # We iterate backwards to ensure the cumulative minimum
    adjusted = np.empty(m)
    adjusted[-1] = raw_adj[-1]
    for i in range(m - 2, -1, -1):
        adjusted[i] = min(raw_adj[i], adjusted[i + 1])

    # Cap values at 1.0
    adjusted = np.minimum(adjusted, 1.0)

    # Map back to original order
    p_adj = pd.Series(adjusted, index=sorted_indices)
    p_adj = p_adj.sort_index()

    # Determine significance
    significant = p_adj <= alpha

    result_df = pd.DataFrame({
        'p_value': p_values,
        'p_adj': p_adj,
        'significant': significant
    })

    return result_df

def main():
    """
    Main execution function for BH correction.
    Reads complexity metrics and analysis results (if available),
    performs BH correction on correlation p-values per electrode,
    and saves the results to data/analysis/bh_corrected_results.csv.
    """
    logger.info("Starting Benjamini-Hochberg correction pipeline.")

    # Load config
    config = load_config()
    alpha = config.get('analysis', {}).get('alpha', 0.05)

    # Define input/output paths
    # The analysis step (T019) should have generated a file with correlations per channel.
    # We expect a file like data/analysis/correlation_results.csv or similar.
    # Since T019 implementation details might vary, we look for the most likely output.
    # Based on T019 description: "Output to data/analysis/correlation_results.csv" (implied).
    # If T019 output is missing, we check for a generic analysis result.

    # Let's assume the analysis stage produced a file with columns:
    # ['channel', 'correlation', 'p_value', 'method']
    input_path = Path("data/analysis/correlation_results.csv")

    if not input_path.exists():
        # Fallback: Try to construct a dummy result for verification if the file is missing
        # BUT per strict constraints, we must fail loudly if real data is missing.
        # However, T020 is a verification task. If the upstream analysis failed (as per execution log),
        # we cannot proceed with real data.
        # The execution log says: "code/analysis.py -> rc=1 ... Complexity metrics file not found".
        # Therefore, correlation_results.csv does not exist.
        # We must exit with an error to prevent fabrication.
        logger.error("Input file not found: data/analysis/correlation_results.csv")
        logger.error("Upstream analysis (T019) failed to produce results. Cannot perform BH correction.")
        sys.exit(1)

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to read input file {input_path}: {e}")
        sys.exit(1)

    # Validate required columns
    required_cols = ['p_value']
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Input file missing required columns: {required_cols}. Found: {df.columns.tolist()}")
        sys.exit(1)

    # Extract p-values
    p_values = df['p_value']

    # Run BH correction
    logger.info(f"Applying BH correction to {len(p_values)} p-values with alpha={alpha}.")
    corrected_df = run_benjamini_hochberg(p_values, alpha=alpha)

    # Merge back with original dataframe (assuming index alignment or merge on channel if present)
    # If the input had 'channel' or other identifiers, we need to preserve them.
    # The run_benjamini_hochberg function returns a DataFrame with the same index as input.
    # We assume the input index corresponds to the rows.
    final_result = df.copy()
    final_result['p_adj'] = corrected_df['p_adj']
    final_result['significant_bh'] = corrected_df['significant']

    # Ensure output directory exists
    output_dir = Path("data/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "bh_corrected_results.csv"

    # Save results
    final_result.to_csv(output_path, index=False)
    logger.info(f"BH correction complete. Results saved to {output_path}")

    # Print summary
    n_sig = final_result['significant_bh'].sum()
    logger.info(f"Significant electrodes after BH correction: {n_sig}/{len(final_result)}")

if __name__ == "__main__":
    main()
