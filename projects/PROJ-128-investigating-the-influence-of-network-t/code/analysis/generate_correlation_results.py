"""
T027 Implementation: Generate correlation_results.csv
Reads aggregated structural and dynamic metrics, computes correlations,
applies FDR, and writes the final results CSV.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from analysis.correlation import run_correlation_analysis, benjamini_hochberg_fdr
from config import get_config_dict

def load_metrics_data():
    """
    Loads the aggregated structural and dynamic metrics CSVs produced by US1.
    Merges them on subject_id to create the analysis dataframe.
    """
    config = get_config_dict()
    data_dir = Path(config['paths']['processed_data'])
    
    struct_path = data_dir / "structural_metrics.csv"
    dyn_path = data_dir / "dynamic_metrics.csv"

    if not struct_path.exists():
        raise FileNotFoundError(f"Structural metrics file not found at {struct_path}. "
                                "Run US1 (T019) first.")
    if not dyn_path.exists():
        raise FileNotFoundError(f"Dynamic metrics file not found at {dyn_path}. "
                                "Run US1 (T019) first.")

    df_struct = pd.read_csv(struct_path)
    df_dyn = pd.read_csv(dyn_path)

    # Merge on subject_id
    # Expected columns in struct: subject_id, global_efficiency, avg_clustering, modularity
    # Expected columns in dyn: subject_id, visited_states, mean_dwell_time
    df_merged = pd.merge(df_struct, df_dyn, on='subject_id', how='inner')
    
    if df_merged.empty:
        raise ValueError("Merged dataframe is empty. Check subject_id consistency.")
        
    return df_merged

def generate_correlation_results():
    """
    Executes the correlation analysis and saves the results to data/processed/correlation_results.csv.
    """
    print("Loading aggregated metrics...")
    df = load_metrics_data()
    
    # Define metric pairs to correlate based on US2 requirements
    # Structural: global_efficiency, avg_clustering, modularity
    # Dynamic: visited_states, mean_dwell_time
    struct_cols = ['global_efficiency', 'avg_clustering', 'modularity']
    dyn_cols = ['visited_states', 'mean_dwell_time']
    
    # Filter columns that actually exist in the dataframe
    available_struct = [c for c in struct_cols if c in df.columns]
    available_dyn = [c for c in dyn_cols if c in df.columns]
    
    if not available_struct or not available_dyn:
        raise ValueError(f"Missing required columns. Found Struct: {list(df.columns)}, Dyn: {list(df.columns)}")

    results = []

    print(f"Running correlations for {len(available_struct)} structural vs {len(available_dyn)} dynamic metrics...")
    
    for s_col in available_struct:
        for d_col in available_dyn:
            # Use the run_correlation_analysis helper which handles normality and selection
            # It returns (r, p_value)
            r, p_val = run_correlation_analysis(df[s_col], df[d_col])
            
            results.append({
                'structural_metric': s_col,
                'dynamic_metric': d_col,
                'r_value': r,
                'p_value_raw': p_val
            })
    
    df_results = pd.DataFrame(results)
    
    if df_results.empty:
        raise RuntimeError("No correlation results generated.")

    # Apply FDR correction
    print("Applying Benjamini-Hochberg FDR correction...")
    p_values = df_results['p_value_raw'].values
    fdr_corrected = benjamini_hochberg_fdr(p_values, q=0.05)
    
    df_results['p_value_fdr'] = fdr_corrected
    
    # Determine significance
    df_results['is_significant_fdr'] = df_results['p_value_fdr'] < 0.05

    # Save to CSV
    config = get_config_dict()
    output_path = Path(config['paths']['processed_data']) / "correlation_results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_results.to_csv(output_path, index=False)
    print(f"Successfully wrote correlation results to {output_path}")
    print(f"Significant findings (FDR < 0.05): {df_results['is_significant_fdr'].sum()}")
    
    return output_path

if __name__ == "__main__":
    generate_correlation_results()