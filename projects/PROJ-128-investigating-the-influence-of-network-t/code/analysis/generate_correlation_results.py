import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

from analysis.correlation import run_correlation_analysis, benjamini_hochberg_fdr
from config import get_config_dict

def load_metrics_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the aggregated structural and dynamic metrics from CSV files.
    
    Returns:
        Tuple of (structural_metrics_df, dynamic_metrics_df)
    """
    config = get_config_dict()
    processed_dir = Path(config['paths']['processed'])
    
    structural_path = processed_dir / 'structural_metrics.csv'
    dynamic_path = processed_dir / 'dynamic_metrics.csv'
    
    if not structural_path.exists():
        raise FileNotFoundError(f"Structural metrics file not found: {structural_path}")
    if not dynamic_path.exists():
        raise FileNotFoundError(f"Dynamic metrics file not found: {dynamic_path}")
    
    structural_df = pd.read_csv(structural_path)
    dynamic_df = pd.read_csv(dynamic_path)
    
    # Merge on subject_id to create a unified analysis dataframe
    # Ensure consistent column names for merging
    if 'subject_id' in structural_df.columns and 'subject_id' in dynamic_df.columns:
        merged_df = pd.merge(structural_df, dynamic_df, on='subject_id', how='inner')
    else:
        # Fallback if column names differ slightly, assuming first column is ID
        # In a robust system, we would check schema, but here we assume valid output from T019
        raise ValueError("Missing 'subject_id' column in one of the metric files.")
    
    return merged_df, structural_df, dynamic_df

def generate_correlation_results(output_path: str = None) -> pd.DataFrame:
    """
    Generate the correlation results CSV file containing r-values, raw p-values,
    and FDR-corrected p-values.
    
    This function:
    1. Loads the merged metrics data.
    2. Identifies structural and dynamic metric columns.
    3. Runs the correlation analysis (normality check, correlation calculation).
    4. Applies Benjamini-Hochberg FDR correction.
    5. Saves the results to `data/processed/correlation_results.csv`.
    
    Args:
        output_path: Optional path to save the results. Defaults to config path.
    
    Returns:
        The generated correlation results DataFrame.
    """
    config = get_config_dict()
    processed_dir = Path(config['paths']['processed'])
    
    if output_path is None:
        output_path = processed_dir / 'correlation_results.csv'
    else:
        output_path = Path(output_path)
    
    # Load data
    merged_df, struct_df, dyn_df = load_metrics_data()
    
    # Identify metric columns (exclude subject_id and potentially non-metric cols)
    # Structural metrics typically: global_efficiency, avg_clustering, modularity
    # Dynamic metrics typically: dwell_time_mean, visited_states_count
    # We assume the merged_df contains these specific columns based on T015-T018 implementation
    # We filter out 'subject_id'
    metric_cols = [col for col in merged_df.columns if col != 'subject_id']
    
    if len(metric_cols) < 2:
        raise ValueError("Not enough metric columns found to perform correlation analysis.")
    
    # Separate structural and dynamic metrics for correlation
    # Heuristic: columns containing 'efficiency', 'clustering', 'modularity' are structural
    # Columns containing 'dwell', 'visited', 'state' are dynamic
    # A more robust approach would use a schema, but we proceed with column name inference
    # as per the pipeline design.
    
    # Define expected structural and dynamic columns based on task descriptions
    structural_metrics = ['global_efficiency', 'avg_clustering', 'modularity']
    dynamic_metrics = ['dwell_time_mean', 'visited_states_count']
    
    # Filter to only those that exist in the dataframe
    struct_cols = [c for c in structural_metrics if c in merged_df.columns]
    dyn_cols = [c for c in dynamic_metrics if c in merged_df.columns]
    
    if not struct_cols or not dyn_cols:
        # Fallback: if explicit names aren't found, try to infer from all columns
        # This handles cases where column names might differ slightly
        struct_cols = [c for c in metric_cols if any(k in c.lower() for k in ['efficiency', 'clustering', 'modularity', 'path'])]
        dyn_cols = [c for c in metric_cols if any(k in c.lower() for k in ['dwell', 'visited', 'state', 'switch'])]
        
        # If still empty, take all remaining as dynamic against all structural?
        # No, that's ambiguous. Raise error if we can't identify them.
        if not struct_cols or not dyn_cols:
            raise ValueError(f"Could not identify structural or dynamic metrics. Found: {metric_cols}")

    results_data = []
    
    for s_col in struct_cols:
        for d_col in dyn_cols:
            # Extract series
            s_series = merged_df[s_col].dropna()
            d_series = merged_df[d_col].dropna()
            
            # Align indices
            common_idx = s_series.index.intersection(d_series.index)
            s_vals = s_series.loc[common_idx]
            d_vals = d_series.loc[common_idx]
            
            if len(common_idx) < 3:
                # Not enough data points for correlation
                results_data.append({
                    'structural_metric': s_col,
                    'dynamic_metric': d_col,
                    'n': len(common_idx),
                    'r': np.nan,
                    'p_raw': np.nan,
                    'fdr_corrected': np.nan,
                    'significant': False
                })
                continue
            
            # Run correlation analysis (normality check + correlation)
            # We reuse the logic from analysis.correlation but inline the specific pair calculation
            # to avoid overhead of running the full batch analysis function if it's not designed for pairs.
            # However, run_correlation_analysis is designed to take the full data.
            # Let's use the helper functions directly.
            
            from scipy.stats import shapiro, pearsonr, spearmanr
            from analysis.correlation import check_normality, calculate_correlation
            
            # Check normality
            _, s_p = shapiro(s_vals)
            _, d_p = shapiro(d_vals)
            is_normal = (s_p > 0.05) and (d_p > 0.05)
            
            # Calculate correlation
            r, p_raw = calculate_correlation(s_vals, d_vals, normal=is_normal)
            
            results_data.append({
                'structural_metric': s_col,
                'dynamic_metric': d_col,
                'n': len(common_idx),
                'r': r,
                'p_raw': p_raw,
                'fdr_corrected': np.nan, # To be filled
                'significant': False     # To be filled
            })
    
    if not results_data:
        raise ValueError("No correlation pairs were generated.")
    
    results_df = pd.DataFrame(results_data)
    
    # Apply FDR correction
    p_values = results_df['p_raw'].values
    if np.any(~np.isnan(p_values)):
        # Filter out NaNs for FDR calculation
        valid_indices = ~np.isnan(p_values)
        valid_p = p_values[valid_indices]
        
        # Apply Benjamini-Hochberg
        fdr_p = benjamini_hochberg_fdr(valid_p)
        
        # Map back to dataframe
        results_df.loc[valid_indices, 'fdr_corrected'] = fdr_p
    else:
        results_df['fdr_corrected'] = np.nan
    
    # Determine significance (FDR < 0.05)
    results_df['significant'] = results_df['fdr_corrected'] < 0.05
    
    # Save to CSV
    results_df.to_csv(output_path, index=False)
    
    print(f"Correlation results saved to {output_path}")
    print(f"Total pairs: {len(results_df)}")
    print(f"Significant findings (FDR < 0.05): {results_df['significant'].sum()}")
    
    return results_df

def main():
    """
    Main entry point to generate correlation results.
    """
    try:
        generate_correlation_results()
    except Exception as e:
        print(f"Error generating correlation results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
