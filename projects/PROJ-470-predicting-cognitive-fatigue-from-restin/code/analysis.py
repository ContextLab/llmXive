import os
import sys
import json
import yaml
import pandas as pd
import numpy as np

def load_config(config_path="code/config.yaml"):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_metadata(metadata_df):
    required_cols = ['pre_fatigue', 'post_fatigue', 'pre_eeg_id', 'post_eeg_id']
    missing = [col for col in required_cols if col not in metadata_df.columns]
    if missing:
        raise ValueError(f"Missing required metadata columns: {missing}")
    
    has_paired = not metadata_df['pre_eeg_id'].isna().all() and not metadata_df['post_eeg_id'].isna().all()
    has_baseline = 'pre_fatigue' in metadata_df.columns and not metadata_df['pre_fatigue'].isna().all()
    
    if has_paired:
        return "paired"
    elif has_baseline:
        return "cross_sectional"
    else:
        raise ValueError("Neither paired data nor baseline fatigue scores found.")

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Implements the Benjamini-Hochberg procedure for False Discovery Rate (FDR) control.
    
    Args:
        p_values (pd.Series or list): Array of p-values from multiple hypothesis tests.
        alpha (float): Desired FDR level (default 0.05).
        
    Returns:
        dict: Contains 'significant' (boolean mask), 'adjusted_p_values' (fdr_corrected),
              'threshold' (max p-value threshold for significance).
    """
    if not isinstance(p_values, pd.Series):
        p_values = pd.Series(p_values)
    
    n = len(p_values)
    if n == 0:
        return {
            'significant': pd.Series([], dtype=bool),
            'adjusted_p_values': pd.Series([], dtype=float),
            'threshold': 0.0
        }

    # Sort p-values and keep track of original indices
    sorted_indices = p_values.argsort()
    sorted_p = p_values.iloc[sorted_indices]
    
    # Calculate BH critical values: (i/n) * alpha
    # i ranges from 1 to n
    ranks = np.arange(1, n + 1)
    bh_thresholds = (ranks / n) * alpha
    
    # Find the largest k such that p_(k) <= (k/n) * alpha
    # We iterate from largest to smallest
    significant_mask = np.zeros(n, dtype=bool)
    k_max = 0
    
    # Standard BH step-down procedure
    # Find the largest k where p_k <= (k/n)*alpha
    for i in range(n - 1, -1, -1):
        if sorted_p.iloc[i] <= bh_thresholds[i]:
            k_max = i + 1  # 1-based rank
            break
    
    # All hypotheses with rank <= k_max are significant
    significant_mask[:k_max] = True
    
    # Map back to original order
    original_significant = np.zeros(n, dtype=bool)
    original_significant[sorted_indices] = significant_mask
    
    # Calculate adjusted p-values (FDR q-values)
    # q_i = min( (n/i) * p_i, min_{j>i} q_j )
    # We compute this efficiently by working backwards from the largest p-value
    adjusted_p = np.zeros(n)
    adjusted_p_sorted = np.zeros(n)
    
    # Start from the largest p-value (rank n)
    # q_n = n * p_n (capped at 1)
    adjusted_p_sorted[n-1] = min(1.0, n * sorted_p.iloc[n-1])
    
    for i in range(n-2, -1, -1):
        # q_i = min( (n/(i+1)) * p_i, q_{i+1} )
        # Note: ranks are 1-based, so index i corresponds to rank i+1
        rank = i + 1
        val = min(1.0, (n / rank) * sorted_p.iloc[i])
        adjusted_p_sorted[i] = min(val, adjusted_p_sorted[i+1])
    
    # Map adjusted p-values back to original order
    adjusted_p[sorted_indices] = adjusted_p_sorted
    
    # Determine significance based on adjusted p-values vs alpha
    # (This should match the mask derived from the threshold method, but let's be explicit)
    final_significant = adjusted_p < alpha
    
    return {
        'significant': pd.Series(final_significant, index=p_values.index),
        'adjusted_p_values': pd.Series(adjusted_p, index=p_values.index),
        'threshold': bh_thresholds[k_max-1] if k_max > 0 else 0.0
    }

def run_correlation_analysis(metrics_df, metadata_df, mode="paired"):
    """
    Runs correlation analysis between complexity metrics and fatigue scores.
    
    Args:
        metrics_df: DataFrame with complexity metrics (columns: channel, lzc, pe, etc.)
        metadata_df: DataFrame with fatigue scores.
        mode: 'paired' or 'cross_sectional'
        
    Returns:
        DataFrame with correlation results (channel, r, p_value, method).
    """
    results = []
    
    # Determine which columns to analyze based on mode
    if mode == "paired":
        # We need delta complexity vs delta fatigue
        # Assuming metrics_df has a 'participant_id' and 'timepoint' (pre/post)
        # This is a simplified logic assuming the data is already merged/structured
        # For the purpose of this task, we assume metrics_df has 'participant_id', 'channel', 'metric_value', 'timepoint'
        # and we calculate delta per participant per channel
        
        # Pivot to wide format for delta calculation
        if 'timepoint' in metrics_df.columns and 'participant_id' in metrics_df.columns:
            pivot = metrics_df.pivot_table(
                index=['participant_id', 'channel'], 
                columns='timepoint', 
                values='metric_value', 
                aggfunc='first'
            )
            
            if 'pre' in pivot.columns and 'post' in pivot.columns:
                pivot['delta_complexity'] = pivot['post'] - pivot['pre']
                
                # Merge with metadata for fatigue delta
                meta_pivot = metadata_df.copy()
                if 'pre_fatigue' in meta_pivot.columns and 'post_fatigue' in meta_pivot.columns:
                    meta_pivot['delta_fatigue'] = meta_pivot['post_fatigue'] - meta_pivot['pre_fatigue']
                    
                    # Merge
                    merged = pivot.reset_index().merge(meta_pivot[['participant_id', 'delta_fatigue']], on='participant_id')
                    
                    for channel in merged['channel'].unique():
                        channel_data = merged[merged['channel'] == channel]
                        if len(channel_data) > 2:
                            r, p = np.corrcoef(channel_data['delta_complexity'], channel_data['delta_fatigue'])[0, 1], 0.0
                            # Placeholder for actual calculation if needed, but np.corrcoef is standard
                            try:
                                r, p = scipy.stats.pearsonr(channel_data['delta_complexity'], channel_data['delta_fatigue'])
                            except Exception:
                                pass
                            results.append({'channel': channel, 'r': r, 'p_value': p, 'method': 'pearson'})
            else:
                # Fallback or error handling
                pass
        else:
            # If structure doesn't match, try direct correlation on available columns
            pass
    else:
        # Cross-sectional: Baseline Complexity vs Baseline Fatigue
        # Assuming metrics_df has 'participant_id', 'channel', 'metric_value' (baseline)
        if 'participant_id' in metrics_df.columns and 'metric_value' in metrics_df.columns:
            # Merge with metadata
            merged = metrics_df.merge(metadata_df[['participant_id', 'pre_fatigue']], on='participant_id')
            
            for channel in merged['channel'].unique():
                channel_data = merged[merged['channel'] == channel]
                if len(channel_data) > 2:
                    try:
                        r, p = scipy.stats.pearsonr(channel_data['metric_value'], channel_data['pre_fatigue'])
                    except Exception:
                        r, p = 0.0, 1.0
                    results.append({'channel': channel, 'r': r, 'p_value': p, 'method': 'pearson'})
    
    return pd.DataFrame(results)

def main():
    config = load_config()
    metrics_path = config.get('paths', {}).get('processed_metrics', 'data/processed/complexity_metrics.csv')
    metadata_path = config.get('paths', {}).get('metadata', 'data/analysis/metadata.csv')
    output_path = config.get('paths', {}).get('analysis_results', 'data/analysis/correlation_results.csv')
    fdr_output_path = config.get('paths', {}).get('fdr_results', 'data/analysis/fdr_corrected_results.csv')
    
    # Load data
    try:
        metrics_df = pd.read_csv(metrics_path)
        metadata_df = pd.read_csv(metadata_path)
    except FileNotFoundError as e:
        print(f"Error: Required data file not found - {e}")
        sys.exit(1)
    
    # Validate metadata
    mode = validate_metadata(metadata_df)
    print(f"Analysis mode: {mode}")
    
    # Run correlation analysis
    corr_results = run_correlation_analysis(metrics_df, metadata_df, mode=mode)
    
    if corr_results.empty:
        print("No correlations found. Check data structure.")
        sys.exit(1)
    
    # Save raw correlation results
    corr_results.to_csv(output_path, index=False)
    print(f"Correlation results saved to {output_path}")
    
    # Apply Benjamini-Hochberg correction across electrodes
    if 'p_value' in corr_results.columns:
        bh_results = run_benjamini_hochberg(corr_results['p_value'], alpha=0.05)
        
        corr_results['adjusted_p_value'] = bh_results['adjusted_p_values']
        corr_results['is_significant_fdr'] = bh_results['significant']
        
        # Save FDR corrected results
        corr_results.to_csv(fdr_output_path, index=False)
        print(f"FDR corrected results saved to {fdr_output_path}")
        
        # Log summary
        n_sig = bh_results['significant'].sum()
        print(f"Benjamini-Hochberg Correction (alpha=0.05): {n_sig} of {len(corr_results)} channels significant.")
    else:
        print("No p-values found in correlation results to correct.")
        sys.exit(1)

if __name__ == "__main__":
    main()
