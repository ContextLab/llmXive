"""
Generate correlation results CSV from processed structural and dynamic metrics.

This script loads the aggregated metrics from T019, runs the correlation analysis
defined in T024-T026, and writes the final results to data/processed/correlation_results.csv.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Import from existing API surface
from analysis.correlation import run_correlation_analysis, benjamini_hochberg_fdr
from config import get_config_dict

def load_metrics_data() -> pd.DataFrame:
    """
    Load the aggregated metrics CSV produced by T019.
    
    Expects: data/processed/structural_metrics.csv and data/processed/dynamic_metrics.csv
    Merges them on subject_id.
    """
    config = get_config_dict()
    processed_dir = Path(config['paths']['processed'])
    
    structural_path = processed_dir / 'structural_metrics.csv'
    dynamic_path = processed_dir / 'dynamic_metrics.csv'
    
    if not structural_path.exists():
        raise FileNotFoundError(f"Structural metrics file not found: {structural_path}")
    if not dynamic_path.exists():
        raise FileNotFoundError(f"Dynamic metrics file not found: {dynamic_path}")
        
    df_struct = pd.read_csv(structural_path)
    df_dyn = pd.read_csv(dynamic_path)
    
    # Ensure subject_id is consistent for merge
    if 'subject_id' not in df_struct.columns or 'subject_id' not in df_dyn.columns:
        raise ValueError("Both CSVs must contain 'subject_id' column for merging.")
        
    # Merge on subject_id
    merged_df = pd.merge(df_struct, df_dyn, on='subject_id', how='inner')
    
    if merged_df.empty:
        raise ValueError("Merged dataframe is empty. Check subject_id consistency.")
        
    return merged_df

def generate_correlation_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run correlation analysis and FDR correction, returning a results DataFrame.
    
    Input: Merged metrics DataFrame
    Output: DataFrame with columns: metric_pair, r_value, p_value_raw, p_value_fdr, is_significant
    """
    # Identify structural and dynamic columns
    # Structural metrics (from T015): global_efficiency, avg_clustering, modularity
    # Dynamic metrics (from T018): visited_states, mean_dwell_time
    # We exclude 'subject_id' and any non-numeric columns
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Define pairs to correlate based on task scope (US2)
    # Correlate each structural metric with each dynamic metric
    structural_metrics = ['global_efficiency', 'avg_clustering', 'modularity']
    dynamic_metrics = ['visited_states', 'mean_dwell_time']
    
    # Filter to ensure only existing columns are used
    structural_metrics = [m for m in structural_metrics if m in numeric_cols]
    dynamic_metrics = [m for m in dynamic_metrics if m in numeric_cols]
    
    if not structural_metrics or not dynamic_metrics:
        raise ValueError("No valid structural or dynamic metrics found to correlate.")
        
    results = []
    
    for s_metric in structural_metrics:
        for d_metric in dynamic_metrics:
            # Extract vectors
            x = df[s_metric].dropna()
            y = df[d_metric].dropna()
            
            # Align indices for paired analysis
            common_idx = x.index.intersection(y.index)
            x_aligned = x.loc[common_idx]
            y_aligned = y.loc[common_idx]
            
            if len(x_aligned) < 3:
                # Not enough data points for correlation
                results.append({
                    'metric_pair': f"{s_metric} vs {d_metric}",
                    'r_value': np.nan,
                    'p_value_raw': np.nan,
                    'p_value_fdr': np.nan,
                    'is_significant': False
                })
                continue
                
            # Run correlation analysis (T024-T025)
            # This function handles normality check and selects Pearson/Spearman
            r_val, p_val = run_correlation_analysis(x_aligned, y_aligned)
            
            results.append({
                'metric_pair': f"{s_metric} vs {d_metric}",
                'r_value': r_val,
                'p_value_raw': p_val,
                'p_value_fdr': np.nan, # Will be filled after FDR
                'is_significant': False
            })
    
    if not results:
        raise ValueError("No correlation results generated.")
        
    results_df = pd.DataFrame(results)
    
    # Apply FDR correction (T026)
    p_values = results_df['p_value_raw'].values
    # Handle NaNs in p-values for FDR calculation
    valid_mask = ~np.isnan(p_values)
    if np.any(valid_mask):
        fdr_corrected = benjamini_hochberg_fdr(p_values[valid_mask])
        results_df.loc[valid_mask, 'p_value_fdr'] = fdr_corrected
    else:
        results_df['p_value_fdr'] = np.nan
        
    # Determine significance (FDR < 0.05)
    results_df['is_significant'] = results_df['p_value_fdr'] < 0.05
    
    return results_df

def main():
    """
    Main entry point to generate and save correlation results.
    """
    print("Loading processed metrics...")
    df = load_metrics_data()
    print(f"Loaded {len(df)} subjects.")
    
    print("Generating correlation results...")
    results_df = generate_correlation_results(df)
    
    # Define output path
    config = get_config_dict()
    processed_dir = Path(config['paths']['processed'])
    output_path = processed_dir / 'correlation_results.csv'
    
    print(f"Saving results to {output_path}...")
    results_df.to_csv(output_path, index=False)
    
    # Log summary
    significant_count = results_df['is_significant'].sum()
    total_count = len(results_df)
    print(f"Analysis complete. {significant_count}/{total_count} significant findings (FDR q < 0.05).")
    
    if significant_count == 0:
        print("NOTE: No significant findings after FDR correction. This will be noted in the final report (T028).")
        
    return output_path

if __name__ == "__main__":
    main()