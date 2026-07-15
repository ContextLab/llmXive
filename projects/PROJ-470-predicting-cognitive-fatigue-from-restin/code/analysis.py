import os
import sys
import json
import yaml
import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path

# Import from local modules as per API surface
from utils.logging import get_logger
from models.complexity_metric import MetricType

logger = get_logger(__name__)

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def validate_metadata(metadata_df):
    """
    Validate metadata dataframe for required columns.
    Implements T018 logic: check for paired or baseline data availability.
    Returns (mode, metadata_df) where mode is 'paired' or 'cross-sectional'.
    """
    required_paired = ['pre_fatigue', 'post_fatigue', 'pre_eeg_id', 'post_eeg_id']
    required_baseline = ['pre_fatigue', 'pre_eeg_id'] # Baseline fatigue and baseline EEG

    has_paired = all(col in metadata_df.columns for col in required_paired)
    has_baseline = all(col in metadata_df.columns for col in required_baseline)

    if has_paired:
        logger.info("Paired data detected. Running paired analysis (delta vs delta).")
        return 'paired', metadata_df
    elif has_baseline:
        logger.info("Baseline data detected. Running cross-sectional analysis (Baseline Complexity vs Baseline Fatigue).")
        return 'cross-sectional', metadata_df
    else:
        logger.error("Neither paired nor baseline data found.")
        report = {
            "error": "Missing required columns for analysis",
            "available_columns": list(metadata_df.columns),
            "required_paired": required_paired,
            "required_baseline": required_baseline
        }
        with open('data/analysis/validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        raise ValueError("Validation failed: Missing required data columns. See data/analysis/validation_report.json")

def run_benjamini_hochberg(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg correction for multiple comparisons.
    Input: list/array of p-values.
    Output: dict with 'significant' (bool), 'adjusted_p' (float).
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return []

    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # Calculate BH critical values
    ranks = np.arange(1, n + 1)
    critical_values = (ranks / n) * alpha

    # Find the largest k such that p_(k) <= critical_(k)
    # We iterate from largest to smallest
    significant_indices = []
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= critical_values[i]:
            # All p-values up to this index (in sorted order) are significant
            significant_indices = sorted_indices[:i+1]
            break

    # Create a mask for significance
    sig_mask = np.zeros(n, dtype=bool)
    sig_mask[significant_indices] = True

    # Calculate adjusted p-values (q-values)
    # q_i = min( (n / rank_i) * p_i, 1 )
    # But we need to ensure monotonicity: q_i = min( q_{i+1}, (n / rank_i) * p_i )
    adjusted_p = np.zeros(n)
    min_val = 1.0
    for i in range(n - 1, -1, -1):
        rank = i + 1
        adj = min(1.0, (n / rank) * sorted_p[i])
        min_val = min(min_val, adj)
        adjusted_p[sorted_indices[i]] = min_val

    return {
        'significant': sig_mask,
        'adjusted_p': adjusted_p
    }

def run_correlation_analysis(complexity_metrics_df, metadata_df):
    """
    Perform correlation analysis based on data mode (paired or cross-sectional).
    Returns a DataFrame with correlation results.
    """
    mode, meta = validate_metadata(metadata_df)
    results = []

    # Merge complexity metrics with metadata
    # Complexity metrics should have columns: subject_id, channel, metric_type, value
    # We need to join on subject_id and potentially timepoint (pre/post)

    if mode == 'paired':
        logger.info("Processing paired analysis...")
        # Calculate deltas
        # We assume complexity_metrics_df has a 'timepoint' column or we infer from metadata join
        # Let's assume complexity_metrics_df has 'subject_id', 'channel', 'metric_type', 'value', 'timepoint'
        # If not, we might need to pivot or merge carefully.
        # For now, let's assume the input df has been prepared with 'timepoint' (pre/post)
        
        # Merge to get fatigue scores
        merged = meta.merge(complexity_metrics_df, left_on='pre_eeg_id', right_on='eeg_id', suffixes=('_meta', '_comp'))
        # This is tricky without a clear schema. Let's assume a simpler join:
        # We need to calculate delta complexity and delta fatigue.
        
        # Strategy:
        # 1. Pivot complexity metrics to have pre/post columns per subject/channel/metric
        # 2. Join with metadata to get pre/post fatigue
        # 3. Calculate deltas
        
        # Pivot complexity
        try:
            pivot_cols = ['subject_id', 'channel', 'metric_type', 'timepoint', 'value']
            if not all(c in complexity_metrics_df.columns for c in pivot_cols):
                # Fallback: assume 'timepoint' is part of the ID or derived?
                # For robustness, let's assume the input data structure is:
                # subject_id, channel, metric_type, value, timepoint
                raise KeyError("Missing required columns for complexity metrics pivot")
            
            pivot_df = complexity_metrics_df.pivot_table(
                index=['subject_id', 'channel', 'metric_type'],
                columns='timepoint',
                values='value',
                aggfunc='first'
            ).reset_index()
            
            # Flatten column names
            pivot_df.columns = ['subject_id', 'channel', 'metric_type'] + [f"comp_{c}" for c in pivot_df.columns[3:]]
            
            # Merge with metadata
            # Metadata has pre_fatigue, post_fatigue, subject_id
            final_df = pivot_df.merge(meta[['subject_id', 'pre_fatigue', 'post_fatigue']], on='subject_id')
            
            # Calculate deltas
            final_df['delta_fatigue'] = final_df['post_fatigue'] - final_df['pre_fatigue']
            # Assume columns are named comp_pre, comp_post
            final_df['delta_complexity'] = final_df['comp_post'] - final_df['comp_pre']
            
            # Filter out rows with NaN
            valid_df = final_df.dropna(subset=['delta_fatigue', 'delta_complexity'])
            
            if len(valid_df) < 2:
                logger.warning("Not enough data points for correlation in paired mode.")
                return pd.DataFrame()

            # Run correlations
            for metric_type in valid_df['metric_type'].unique():
                for channel in valid_df['channel'].unique():
                    subset = valid_df[(valid_df['metric_type'] == metric_type) & (valid_df['channel'] == channel)]
                    if len(subset) < 2:
                        continue
                    
                    # Pearson and Spearman
                    pearson_r, pearson_p = stats.pearsonr(subset['delta_complexity'], subset['delta_fatigue'])
                    spearman_r, spearman_p = stats.spearmanr(subset['delta_complexity'], subset['delta_fatigue'])
                    
                    results.append({
                        'mode': 'paired',
                        'metric_type': metric_type,
                        'channel': channel,
                        'correlation_type': 'pearson',
                        'r': pearson_r,
                        'p': pearson_p,
                        'n': len(subset)
                    })
                    results.append({
                        'mode': 'paired',
                        'metric_type': metric_type,
                        'channel': channel,
                        'correlation_type': 'spearman',
                        'r': spearman_r,
                        'p': spearman_p,
                        'n': len(subset)
                    })

        except Exception as e:
            logger.error(f"Error in paired analysis: {e}")
            raise

    elif mode == 'cross-sectional':
        logger.info("Processing cross-sectional analysis...")
        # Use baseline complexity vs baseline fatigue
        # Filter complexity metrics for 'pre' or 'baseline' timepoint
        baseline_comp = complexity_metrics_df[complexity_metrics_df['timepoint'].isin(['pre', 'baseline'])].copy()
        
        # Merge with metadata
        merged = meta.merge(baseline_comp, left_on='pre_eeg_id', right_on='eeg_id', suffixes=('_meta', '_comp'))
        # Or simpler: merge on subject_id if timepoint is handled in pivot
        
        # Pivot to get one row per subject/channel/metric
        pivot_cols = ['subject_id', 'channel', 'metric_type', 'value']
        if 'timepoint' in merged.columns:
            # Filter again to be sure
            pivot_df = merged[merged['timepoint'].isin(['pre', 'baseline'])]
            pivot_df = pivot_df.pivot_table(
                index=['subject_id', 'channel', 'metric_type'],
                values='value',
                aggfunc='first'
            ).reset_index()
            pivot_df.columns = ['subject_id', 'channel', 'metric_type', 'baseline_complexity']
            
            final_df = pivot_df.merge(meta[['subject_id', 'pre_fatigue']], on='subject_id')
            final_df = final_df.rename(columns={'pre_fatigue': 'baseline_fatigue'})
            
            valid_df = final_df.dropna(subset=['baseline_complexity', 'baseline_fatigue'])
            
            if len(valid_df) < 2:
                logger.warning("Not enough data points for correlation in cross-sectional mode.")
                return pd.DataFrame()

            for metric_type in valid_df['metric_type'].unique():
                for channel in valid_df['channel'].unique():
                    subset = valid_df[(valid_df['metric_type'] == metric_type) & (valid_df['channel'] == channel)]
                    if len(subset) < 2:
                        continue
                    
                    pearson_r, pearson_p = stats.pearsonr(subset['baseline_complexity'], subset['baseline_fatigue'])
                    spearman_r, spearman_p = stats.spearmanr(subset['baseline_complexity'], subset['baseline_fatigue'])
                    
                    results.append({
                        'mode': 'cross-sectional',
                        'metric_type': metric_type,
                        'channel': channel,
                        'correlation_type': 'pearson',
                        'r': pearson_r,
                        'p': pearson_p,
                        'n': len(subset)
                    })
                    results.append({
                        'mode': 'cross-sectional',
                        'metric_type': metric_type,
                        'channel': channel,
                        'correlation_type': 'spearman',
                        'r': spearman_r,
                        'p': spearman_p,
                        'n': len(subset)
                    })
    else:
        raise ValueError(f"Unknown analysis mode: {mode}")

    return pd.DataFrame(results)

def main():
    """Main entry point for analysis."""
    logger.info("Starting correlation analysis (T019).")
    
    config = load_config()
    
    # Load complexity metrics
    complexity_path = Path("data/processed/complexity_metrics.csv")
    if not complexity_path.exists():
        logger.error(f"Complexity metrics file not found: {complexity_path}")
        sys.exit(1)
    
    complexity_df = pd.read_csv(complexity_path)
    
    # Load metadata (assuming it's in the same file or a separate one? 
    # T018 mentions 'metadata dataframe'. Usually this is combined or separate.
    # Let's assume a separate metadata file or a merged one. 
    # If not present, we might need to derive from complexity_df if it has subject info.
    # For T019, we need fatigue scores. Let's assume they are in a 'metadata.csv' or similar.
    metadata_path = Path("data/processed/metadata.csv")
    if not metadata_path.exists():
        # Fallback: check if complexity_df has fatigue columns? Unlikely.
        # Or maybe it's in the same file if the pipeline merged them earlier.
        # Let's try to find a file with 'fatigue' in the name or column.
        possible_paths = [
            Path("data/processed/participants.csv"),
            Path("data/processed/subject_data.csv"),
            Path("data/analysis/metadata.csv")
        ]
        found = False
        for p in possible_paths:
            if p.exists():
                metadata_df = pd.read_csv(p)
                if any('fatigue' in str(col).lower() for col in metadata_df.columns):
                    found = True
                    break
        if not found:
            logger.error("Metadata file with fatigue scores not found.")
            sys.exit(1)
    else:
        metadata_df = pd.read_csv(metadata_path)

    # Run analysis
    results_df = run_correlation_analysis(complexity_df, metadata_df)
    
    if results_df.empty:
        logger.warning("No results generated.")
        # Still write an empty file to satisfy the contract
        results_df.to_csv("data/analysis/correlation_results.csv", index=False)
        return

    # Apply Benjamini-Hochberg correction
    # Group by mode and correlation_type, then correct p-values
    corrected_results = []
    for (mode, corr_type), group in results_df.groupby(['mode', 'correlation_type']):
        p_values = group['p'].values
        bh_result = run_benjamini_hochberg(p_values)
        
        group['adjusted_p'] = bh_result['adjusted_p']
        group['significant'] = bh_result['significant']
        corrected_results.append(group)
    
    final_results = pd.concat(corrected_results, ignore_index=True)
    
    # Save results
    output_path = Path("data/analysis/correlation_results.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    final_results.to_csv(output_path, index=False)
    
    logger.info(f"Correlation analysis complete. Results saved to {output_path}")

if __name__ == "__main__":
    main()