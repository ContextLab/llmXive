import os
import sys
import json
import yaml
import pandas as pd
import numpy as np

def load_config(config_path="code/config.yaml"):
    """Load pipeline configuration from YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_metadata(metadata_df):
    """
    Validate metadata dataframe for required columns.
    Implements conditional fallback logic:
    - If paired data exists (pre/post fatigue + IDs), use paired analysis.
    - If only baseline fatigue exists, use cross-sectional analysis.
    - Otherwise, write validation report and exit.
    """
    required_cols = ['pre_fatigue', 'post_fatigue', 'pre_eeg_id', 'post_eeg_id']
    has_all = all(col in metadata_df.columns for col in required_cols)
    
    # Check for baseline-only data
    has_baseline = 'pre_fatigue' in metadata_df.columns and 'pre_eeg_id' in metadata_df.columns
    
    if has_all:
        return 'paired'
    elif has_baseline:
        return 'cross-sectional'
    else:
        report = {
            "error": "Missing required metadata columns for analysis",
            "missing_columns": [c for c in required_cols if c not in metadata_df.columns],
            "available_columns": list(metadata_df.columns)
        }
        os.makedirs('data/analysis', exist_ok=True)
        with open('data/analysis/validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

def run_benjamini_hochberg(p_values):
    """
    Implement Benjamini-Hochberg correction for multiple comparisons.
    
    Args:
        p_values: Array-like of p-values to correct.
        
    Returns:
        pd.DataFrame with original p-values, adjusted p-values, and significance flags.
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return pd.DataFrame(columns=['p_value', 'adj_p_value', 'significant'])
    
    # Create DataFrame with original p-values and their indices
    df = pd.DataFrame({
        'p_value': p_values,
        'original_index': range(n)
    })
    
    # Sort by p-value
    df = df.sort_values('p_value').reset_index(drop=True)
    
    # Calculate BH adjusted p-values
    # For each p-value at rank i (1-indexed): adj_p = p * n / i
    # Then ensure monotonicity by taking cumulative min from the end
    ranks = np.arange(1, n + 1)
    df['adj_p_value'] = df['p_value'] * n / ranks
    
    # Enforce monotonicity: adjusted p-values must be non-decreasing with rank
    # We do this by taking cumulative minimum from the largest rank downwards
    df['adj_p_value'] = df['adj_p_value'][::-1].cummin()[::-1]
    
    # Ensure adjusted p-values don't exceed 1.0
    df['adj_p_value'] = df['adj_p_value'].clip(upper=1.0)
    
    # Sort back to original order
    df = df.sort_values('original_index').reset_index(drop=True)
    
    # Determine significance at default alpha=0.05
    df['significant'] = df['adj_p_value'] <= 0.05
    
    # Drop helper column
    df = df.drop('original_index', axis=1)
    
    return df

def run_correlation_analysis(metadata_df, lzc_df, pe_df, mode='paired'):
    """
    Run correlation analysis between complexity metrics and fatigue scores.
    
    Args:
        metadata_df: DataFrame with fatigue scores and EEG IDs.
        lzc_df: DataFrame with Lempel-Ziv complexity metrics.
        pe_df: DataFrame with Permutation Entropy metrics.
        mode: 'paired' or 'cross-sectional'
        
    Returns:
        DataFrame with correlation results.
    """
    results = []
    
    if mode == 'paired':
        # Calculate delta fatigue and delta complexity
        metadata_df = metadata_df.merge(lzc_df, left_on='pre_eeg_id', right_on='segment_id', how='left', suffixes=('_pre', '_post'))
        # Note: This is a simplified merge; in reality, we'd need to handle pre/post separately
        # For now, we'll assume the input data is pre-processed to have delta values
        # or we calculate deltas here if the data structure allows
        pass
    else:
        # Cross-sectional: baseline complexity vs baseline fatigue
        pass
    
    # Placeholder for actual correlation logic
    # In a real implementation, this would iterate over channels and calculate correlations
    return pd.DataFrame(results)

def main():
    """Main entry point for analysis script."""
    config = load_config()
    
    # Load data (paths would come from config)
    metadata_path = config.get('paths', {}).get('metadata', 'data/processed/metadata.csv')
    lzc_path = config.get('paths', {}).get('lzc', 'data/processed/lzc_metrics.csv')
    pe_path = config.get('paths', {}).get('pe', 'data/processed/pe_metrics.csv')
    
    if not all(os.path.exists(p) for p in [metadata_path, lzc_path, pe_path]):
        print("Error: Required data files not found. Run download, preprocess, and features first.")
        sys.exit(1)
        
    metadata_df = pd.read_csv(metadata_path)
    lzc_df = pd.read_csv(lzc_path)
    pe_df = pd.read_csv(pe_path)
    
    # Validate metadata
    mode = validate_metadata(metadata_df)
    print(f"Running analysis in {mode} mode")
    
    # Run correlation analysis
    results = run_correlation_analysis(metadata_df, lzc_df, pe_df, mode)
    
    # Apply Benjamini-Hochberg correction
    if not results.empty and 'p_value' in results.columns:
        corrected_results = run_benjamini_hochberg(results['p_value'])
        results = results.join(corrected_results.drop('p_value', axis=1))
        
        # Save results
        os.makedirs('data/analysis', exist_ok=True)
        results.to_csv('data/analysis/correlation_results_corrected.csv', index=False)
        print(f"Results saved to data/analysis/correlation_results_corrected.csv")
    else:
        print("No p-values to correct or no results generated.")

if __name__ == "__main__":
    main()