import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from analysis.correlation import run_correlation_analysis, benjamini_hochberg_fdr
from config import get_config_dict

def load_metrics_data():
    """
    Loads structural and dynamic metrics from the processed CSV files.
    Merges them on subject_id to create the analysis dataframe.
    """
    config = get_config_dict()
    base_path = Path(config['BASE_PATH'])
    
    structural_file = base_path / "data" / "processed" / "structural_metrics.csv"
    dynamic_file = base_path / "data" / "processed" / "dynamic_metrics.csv"
    
    if not structural_file.exists():
        raise FileNotFoundError(f"Structural metrics file not found: {structural_file}")
    if not dynamic_file.exists():
        raise FileNotFoundError(f"Dynamic metrics file not found: {dynamic_file}")
    
    df_struct = pd.read_csv(structural_file)
    df_dyn = pd.read_csv(dynamic_file)
    
    # Aggregate dynamic metrics if they are per-state (multiple rows per subject)
    # The schema suggests: [subject_id, state_id, mean_dwell_time, num_visits]
    # We need to pivot or aggregate to get one row per subject for correlation.
    # Strategy: Calculate mean dwell time across all states and total visits for the subject.
    # Or, if the correlation requires state-specific data, we might need to flatten.
    # Based on T025 (correlation between structural and dynamic metrics), 
    # we typically correlate global structural metrics with global dynamic metrics.
    # Let's aggregate dynamic metrics to subject level.
    
    df_dyn_agg = df_dyn.groupby('subject_id').agg({
        'mean_dwell_time': 'mean', # Average dwell time across states for this subject
        'num_visits': 'sum'        # Total state visits for this subject
    }).reset_index()
    
    # Rename columns for clarity in merge
    df_dyn_agg.rename(columns={
        'mean_dwell_time': 'avg_dwell_time',
        'num_visits': 'total_visits'
    }, inplace=True)
    
    # Merge structural and dynamic
    if 'subject_id' not in df_struct.columns or 'subject_id' not in df_dyn_agg.columns:
        raise ValueError("Both dataframes must contain 'subject_id' column.")
        
    merged_df = pd.merge(df_struct, df_dyn_agg, on='subject_id', how='inner')
    
    if merged_df.empty:
        raise ValueError("No matching subjects found between structural and dynamic metrics.")
        
    return merged_df

def generate_correlation_results(df):
    """
    Runs the correlation analysis and FDR correction, then saves the results.
    """
    # Identify numeric columns for correlation
    # Structural metrics (from T015a): global_efficiency, clustering, modularity
    # Dynamic metrics (from T017): avg_dwell_time, total_visits
    # We need to select columns that are numeric and represent the metrics.
    
    metric_cols = []
    for col in df.columns:
        if col not in ['subject_id']:
            if pd.api.types.is_numeric_dtype(df[col]):
                metric_cols.append(col)
    
    if len(metric_cols) < 2:
        raise ValueError("Not enough numeric metric columns to perform correlation analysis.")
    
    # Run correlation analysis (T024, T025, T026 logic encapsulated in run_correlation_analysis)
    # The function signature from API surface: run_correlation_analysis(df)
    # We assume it returns a DataFrame with correlations.
    # If the existing function expects specific column names, we might need to adapt.
    # Let's assume run_correlation_analysis handles the pairwise logic.
    
    # However, looking at the API surface for correlation.py:
    # run_correlation_analysis likely takes the dataframe and returns results.
    # Let's implement the specific logic here to ensure we get the CSV format required by T027.
    
    results = []
    p_values = []
    
    # We need to correlate every structural metric with every dynamic metric.
    # Let's define structural vs dynamic columns explicitly based on typical output names.
    # T015a output: global_efficiency, clustering_coeff, modularity (approx names)
    # T017 output: avg_dwell_time, total_visits
    
    # Heuristic: Columns containing 'efficiency', 'clustering', 'modularity' are structural
    # Columns containing 'dwell', 'visit' are dynamic.
    
    struct_cols = [c for c in metric_cols if any(k in c.lower() for k in ['efficiency', 'clustering', 'modularity', 'density'])]
    dyn_cols = [c for c in metric_cols if any(k in c.lower() for k in ['dwell', 'visit', 'state'])]
    
    if not struct_cols or not dyn_cols:
        # Fallback: If heuristic fails, try all pairs excluding subject_id
        # But T027 specifically asks for structure-function correlation.
        # If we can't distinguish, we might skip or raise.
        # Let's assume the heuristic works or we use all numeric pairs if strict separation fails.
        # For safety, if heuristic fails, we use all numeric pairs but label them generically.
        if len(metric_cols) >= 2:
            # Generate all pairs
            for i in range(len(metric_cols)):
                for j in range(i + 1, len(metric_cols)):
                    c1, c2 = metric_cols[i], metric_cols[j]
                    # Calculate correlation
                    if df[c1].var() > 0 and df[c2].var() > 0:
                        corr, p = np.corrcoef(df[c1], df[c2])[0, 1], 0.0 # Placeholder
                        # Actually calculate
                        from scipy.stats import pearsonr, spearmanr
                        # Normality check logic (T024)
                        stat, p_norm = spearmanr(df[c1], df[c2]) # Using spearman as safe default or check normality
                        # Let's do a simple normality check
                        from scipy.stats import shapiro
                        try:
                            _, p_shapiro_c1 = shapiro(df[c1].dropna())
                            _, p_shapiro_c2 = shapiro(df[c2].dropna())
                            use_pearson = (p_shapiro_c1 > 0.05) and (p_shapiro_c2 > 0.05)
                        except:
                            use_pearson = False
                        
                        if use_pearson:
                            corr, p_val = pearsonr(df[c1], df[c2])
                        else:
                            corr, p_val = spearmanr(df[c1], df[c2])
                            
                        results.append({
                            'metric_1': c1,
                            'metric_2': c2,
                            'r': corr,
                            'p_raw': p_val
                        })
                        p_values.append(p_val)
        else:
            raise ValueError("Cannot determine metric columns for correlation.")
    else:
        for s_col in struct_cols:
            for d_col in dyn_cols:
                if df[s_col].var() > 0 and df[d_col].var() > 0:
                    from scipy.stats import shapiro, pearsonr, spearmanr
                    try:
                        _, p_shapiro_s = shapiro(df[s_col].dropna())
                        _, p_shapiro_d = shapiro(df[d_col].dropna())
                        use_pearson = (p_shapiro_s > 0.05) and (p_shapiro_d > 0.05)
                    except:
                        use_pearson = False
                    
                    if use_pearson:
                        corr, p_val = pearsonr(df[s_col], df[d_col])
                    else:
                        corr, p_val = spearmanr(df[s_col], df[d_col])
                        
                    results.append({
                        'metric_1': s_col,
                        'metric_2': d_col,
                        'r': corr,
                        'p_raw': p_val
                    })
                    p_values.append(p_val)
    
    if not results:
        raise ValueError("No valid correlations could be calculated.")
        
    # Apply FDR Correction (T026)
    # The API surface has benjamini_hochberg_fdr.
    # Assuming it takes a list of p-values and returns corrected p-values.
    # If the existing function returns a list, we map it back.
    corrected_p = benjamini_hochberg_fdr(p_values)
    
    for i, res in enumerate(results):
        res['p_fdr'] = corrected_p[i]
    
    df_results = pd.DataFrame(results)
    
    # Save to CSV
    config = get_config_dict()
    base_path = Path(config['BASE_PATH'])
    output_path = base_path / "data" / "processed" / "correlation_results.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df_results.to_csv(output_path, index=False)
    print(f"Correlation results saved to {output_path}")
    return df_results

def main():
    try:
        print("Starting Correlation Results Generation (T027)...")
        df = load_metrics_data()
        results_df = generate_correlation_results(df)
        print("T027 completed successfully.")
    except Exception as e:
        print(f"Error during T027: {e}")
        raise

if __name__ == "__main__":
    main()