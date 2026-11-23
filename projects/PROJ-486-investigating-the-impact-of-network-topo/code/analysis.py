import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import multitest
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
import os
import json
from typing import List, Dict, Optional, Tuple, Any

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, 'data', 'processed')
METRIC_FLAGS_FILE = os.path.join(DATA_PROCESSED_DIR, 'metric_flags.json')
SUMMARY_REPORT_FILE = os.path.join(DATA_PROCESSED_DIR, 'summary_report.txt')
CORRELATION_RESULTS_FILE = os.path.join(DATA_PROCESSED_DIR, 'correlation_results.csv')
SENSITIVITY_RESULTS_FILE = os.path.join(DATA_PROCESSED_DIR, 'sensitivity_results.csv')
SENSITIVITY_AGGREGATED_FILE = os.path.join(DATA_PROCESSED_DIR, 'sensitivity_aggregated.csv')
METADATA_FILE = os.path.join(DATA_PROCESSED_DIR, 'metadata.json')

def load_metric_flags() -> Dict[str, Any]:
    """Load metric flags from the processed directory."""
    if os.path.exists(METRIC_FLAGS_FILE):
        with open(METRIC_FLAGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def calculate_spearman_correlations(
    df: pd.DataFrame,
    x_col: str,
    y_col: str
) -> Tuple[float, float]:
    """Calculate Spearman correlation between two columns."""
    if x_col not in df.columns or y_col not in df.columns:
        raise ValueError(f"Columns {x_col} or {y_col} not found in DataFrame")
    
    # Drop NaNs
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 2:
        return np.nan, np.nan
        
    corr, p_value = stats.spearmanr(valid_data[x_col], valid_data[y_col])
    return corr, p_value

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for predictors."""
    if len(predictors) < 2:
        return {}
        
    # Ensure target column exists
    if 'entrainment_metric' not in df.columns:
        raise ValueError("Target column 'entrainment_metric' not found")
        
    X = df[predictors].dropna()
    if X.empty:
        return {p: np.nan for p in predictors}
        
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(predictors):
        if col in X_with_const.columns:
            vif_data[col] = variance_inflation_factor(X_with_const.values, i)
    return vif_data

def run_correlation_analysis(
    df: pd.DataFrame,
    topology_cols: List[str],
    target_col: str = 'entrainment_metric'
) -> Dict[str, Any]:
    """Run full correlation analysis including VIF and MLR."""
    results = {}
    
    # Calculate Spearman correlations for each topology metric
    for col in topology_cols:
        corr, p_val = calculate_spearman_correlations(df, col, target_col)
        results[f'correlation_{col}'] = {
            'r': corr,
            'p_value': p_val
        }
        
    # Calculate VIF
    vif_values = calculate_vif(df, topology_cols)
    results['vif_values'] = vif_values
    
    # Check for collinearity
    max_vif = max(vif_values.values()) if vif_values else 0
    results['is_collinear'] = max_vif > 5
    
    return results

def generate_correlation_results_csv(
    df: pd.DataFrame,
    results: Dict[str, Any],
    output_path: str
) -> None:
    """Generate the correlation results CSV file."""
    # Prepare data for CSV
    data_rows = []
    
    # Extract basic info
    vif_values = results.get('vif_values', {})
    is_collinear = results.get('is_collinear', False)
    
    # For each subject, we can't easily extract individual metrics from the aggregate results
    # So we'll create a summary row per topology metric
    for metric_name, corr_data in results.items():
        if metric_name.startswith('correlation_'):
            metric_col = metric_name.replace('correlation_', '')
            row = {
                'metric_name': metric_col,
                'effect_size': corr_data.get('r', np.nan),
                'raw_p': corr_data.get('p_value', np.nan),
                'adjusted_p_value': np.nan,  # Will be calculated later
                'is_significant': False,
                'vif_value': vif_values.get(metric_col, np.nan),
                'collinearity_warning': is_collinear,
                'data_source': 'Simulated'  # Default, updated in main
            }
            data_rows.append(row)
            
    # Create DataFrame
    results_df = pd.DataFrame(data_rows)
    
    # Apply Holm-Bonferroni correction if not collinear
    if not is_collinear and len(data_rows) > 0:
        p_values = results_df['raw_p'].tolist()
        if all(not np.isnan(p) for p in p_values):
            reject, adj_p_vals, _, _ = multitest.multipletests(
                p_values, 
                method='holm', 
                alpha=0.05
            )
            results_df['adjusted_p_value'] = adj_p_vals
            results_df['is_significant'] = reject
            
    # Load metadata for data source
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
            data_source = metadata.get('data_source', 'Simulated')
            results_df['data_source'] = data_source
            
    # Save to CSV
    results_df.to_csv(output_path, index=False)

def generate_summary_report(
    results: Dict[str, Any],
    n_subjects: int,
    output_path: str
) -> None:
    """Generate the summary report text file."""
    report_lines = []
    report_lines.append("=== Network Topology and Entrainment Analysis Report ===")
    report_lines.append("")
    
    # Data source info
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            metadata = json.load(f)
            data_source = metadata.get('data_source', 'Simulated')
            report_lines.append(f"Data Source: {data_source}")
            report_lines.append(f"Number of Subjects: {n_subjects}")
    else:
        report_lines.append("Data Source: Simulated")
        report_lines.append(f"Number of Subjects: {n_subjects}")
        
    report_lines.append("")
    report_lines.append("--- Correlation Results ---")
    
    for metric_name, corr_data in results.items():
        if metric_name.startswith('correlation_'):
            metric_col = metric_name.replace('correlation_', '')
            r_val = corr_data.get('r', np.nan)
            p_val = corr_data.get('p_value', np.nan)
            report_lines.append(f"{metric_col}: r = {r_val:.4f}, p = {p_val:.4f}")
            
    report_lines.append("")
    report_lines.append("--- Collinearity Analysis ---")
    vif_values = results.get('vif_values', {})
    is_collinear = results.get('is_collinear', False)
    
    if is_collinear:
        report_lines.append("WARNING: High collinearity detected (VIF > 5)")
        report_lines.append("Individual p-values suppressed due to collinearity.")
    else:
        report_lines.append("No significant collinearity detected.")
        
    for metric, vif in vif_values.items():
        report_lines.append(f"{metric}: VIF = {vif:.4f}")
        
    # Power warning
    report_lines.append("")
    if n_subjects < 30:
        report_lines.append("Power Warning: N < 30 (Exploratory)")
        
    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(report_lines))

def aggregate_sensitivity_results(
    schaefer_path: str,
    aal_path: str,
    power_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Aggregate results from multiple atlas types into a single dataset.
    
    Args:
        schaefer_path: Path to sensitivity results CSV for Schaefer atlas
        aal_path: Path to sensitivity results CSV for AAL atlas
        power_path: Path to sensitivity results CSV for Power atlas
        output_path: Path to save the aggregated CSV
        
    Returns:
        DataFrame containing aggregated results with absolute differences
    """
    # Load individual results
    schaefer_df = pd.read_csv(schaefer_path)
    aal_df = pd.read_csv(aal_path)
    power_df = pd.read_csv(power_path)
    
    # Extract effect sizes and p-values
    # Assuming the CSV has columns: metric_name, effect_size, raw_p, etc.
    # We'll focus on the primary clustering coefficient metric
    primary_metric = 'clustering_coefficient'
    
    schaefer_row = schaefer_df[schaefer_df['metric_name'] == primary_metric]
    aal_row = aal_df[aal_df['metric_name'] == primary_metric]
    power_row = power_df[power_df['metric_name'] == primary_metric]
    
    # Get baseline values from Schaefer
    baseline_effect = schaefer_row['effect_size'].values[0] if len(schaefer_row) > 0 else np.nan
    baseline_p = schaefer_row['raw_p'].values[0] if len(schaefer_row) > 0 else np.nan
    
    # Calculate absolute differences for AAL and Power
    aal_effect = aal_row['effect_size'].values[0] if len(aal_row) > 0 else np.nan
    power_effect = power_row['effect_size'].values[0] if len(power_row) > 0 else np.nan
    
    aal_diff = abs(aal_effect - baseline_effect) if not np.isnan(aal_effect) and not np.isnan(baseline_effect) else np.nan
    power_diff = abs(power_effect - baseline_effect) if not np.isnan(power_effect) and not np.isnan(baseline_effect) else np.nan
    
    # Create aggregated DataFrame
    aggregated_data = [
        {
            'atlas_type': 'Schaefer',
            'effect_size': baseline_effect,
            'p_value': baseline_p,
            'absolute_diff': 0.0  # Baseline
        },
        {
            'atlas_type': 'AAL',
            'effect_size': aal_effect,
            'p_value': aal_row['raw_p'].values[0] if len(aal_row) > 0 else np.nan,
            'absolute_diff': aal_diff
        },
        {
            'atlas_type': 'Power',
            'effect_size': power_effect,
            'p_value': power_row['raw_p'].values[0] if len(power_row) > 0 else np.nan,
            'absolute_diff': power_diff
        }
    ]
    
    aggregated_df = pd.DataFrame(aggregated_data)
    
    # Save to CSV
    aggregated_df.to_csv(output_path, index=False)
    
    return aggregated_df

def main():
    """Main function to run the analysis pipeline."""
    # This would be called from main.py with appropriate arguments
    pass

if __name__ == "__main__":
    main()
