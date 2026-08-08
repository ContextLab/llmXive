import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

def load_graph_metrics(csv_path: Path) -> pd.DataFrame:
    """Load graph metrics from CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {csv_path}")
    return pd.read_csv(csv_path)

def load_behavioral_scores() -> pd.DataFrame:
    """Load behavioral scores from JSON or CSV (assuming structure from download/validate)."""
    # Assuming behavioral data is stored in data/processed/aggregated_subjects.json or similar
    # Based on T014a/b, we expect validated data.
    # Let's look for the standard location or derive from the download logic.
    # For this implementation, we assume a file `data/processed/behavioral_scores.csv` exists
    # or we read from the aggregated subjects JSON if CSV is not present.
    # Given the task context, we'll assume a CSV with subject_id and score_value.
    
    data_dir = Path(__file__).parent.parent / "data" / "processed"
    csv_path = data_dir / "behavioral_scores.csv"
    
    if csv_path.exists():
        return pd.read_csv(csv_path)
    
    # Fallback to JSON if CSV not found (as per potential T014 output)
    json_path = data_dir / "aggregated_subjects.json"
    if json_path.exists():
        with open(json_path, 'r') as f:
            data = json.load(f)
        # Convert to DF
        records = []
        for subj in data:
            if 'fluid_intelligence_score' in subj:
                records.append({
                    'subject_id': subj.get('subject_id'),
                    'score_value': subj['fluid_intelligence_score'],
                    'age': subj.get('age'),
                    'gender': subj.get('gender')
                })
        return pd.DataFrame(records)
    
    raise FileNotFoundError("No behavioral scores found in expected locations.")

def merge_metrics_with_scores(metrics_df: pd.DataFrame, behavioral_df: pd.DataFrame) -> pd.DataFrame:
    """Merge graph metrics with behavioral scores on subject_id."""
    if metrics_df.empty or behavioral_df.empty:
        return pd.DataFrame()
    
    # Ensure subject_id is string for consistent merging
    metrics_df['subject_id'] = metrics_df['subject_id'].astype(str)
    behavioral_df['subject_id'] = behavioral_df['subject_id'].astype(str)
    
    merged = pd.merge(metrics_df, behavioral_df, on='subject_id', how='inner')
    
    if merged.empty:
        raise ValueError("No matching subjects found between metrics and behavioral scores.")
    
    return merged

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """Apply Bonferroni correction to a list of p-values."""
    k = len(p_values)
    if k == 0:
        return []
    adjusted_alpha = alpha / k
    return [p < adjusted_alpha for p in p_values]

def compute_correlation(x: List[float], y: List[float]) -> Tuple[float, float]:
    """Compute Pearson correlation and p-value."""
    if len(x) < 3 or len(y) < 3:
        return 0.0, 1.0
    corr, p_val = scipy_stats.pearsonr(x, y)
    return corr, p_val

def analyze_correlations(merged_data: pd.DataFrame) -> List[Dict[str, Any]]:
    """Analyze correlations between each metric and Fluid Intelligence."""
    results = []
    metrics = merged_data['metric_name'].unique()
    
    for metric in metrics:
        subset = merged_data[merged_data['metric_name'] == metric]
        if subset.empty:
            continue
        
        x = subset['value'].tolist()
        y = subset['score_value'].tolist()
        
        corr, p_val = compute_correlation(x, y)
        results.append({
            'metric_name': metric,
            'correlation': corr,
            'p_value': p_val
        })
    
    return results

def run_multiple_linear_regression(merged_data: pd.DataFrame, target_metric: str) -> Dict[str, Any]:
    """Run multiple linear regression for a specific metric controlling for age/gender."""
    subset = merged_data[merged_data['metric_name'] == target_metric]
    if subset.empty:
        return {}
    
    # Prepare data
    X = subset[['age', 'gender']].copy()
    # Encode gender if necessary (assuming 'M', 'F' -> 0, 1)
    if 'gender' in X.columns:
        X['gender'] = X['gender'].map({'M': 0, 'F': 1, 'Male': 0, 'Female': 1}).fillna(0)
    
    y = subset['value']
    
    if X.empty or y.empty:
        return {}
    
    # Simple OLS
    # Using numpy for simplicity as sklearn might not be strictly required if we just want coefficients
    # But for robust stats, we can use scipy or statsmodels. Assuming numpy here for minimal deps.
    # Add intercept
    X_with_intercept = np.column_stack([np.ones(len(X)), X['age'].values, X['gender'].values])
    y_vals = y.values
    
    try:
        coeffs, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y_vals, rcond=None)
        # coeffs[0] is intercept, coeffs[1] is age, coeffs[2] is gender
        return {
            'metric_name': target_metric,
            'age_coeff': coeffs[1],
            'gender_coeff': coeffs[2],
            'intercept': coeffs[0]
        }
    except Exception:
        return {}

def main():
    """Main entry point for stats analysis."""
    project_root = Path(__file__).parent.parent
    metrics_path = project_root / "data" / "processed" / "graph_metrics.csv"
    
    if not metrics_path.exists():
        print(f"Error: {metrics_path} not found.")
        sys.exit(1)
    
    metrics_df = load_graph_metrics(metrics_path)
    behavioral_df = load_behavioral_scores()
    
    if metrics_df.empty or behavioral_df.empty:
        print("Error: No data to analyze.")
        sys.exit(1)
    
    merged = merge_metrics_with_scores(metrics_df, behavioral_df)
    
    # Analyze correlations
    corr_results = analyze_correlations(merged)
    
    # Apply Bonferroni
    p_values = [r['p_value'] for r in corr_results]
    significant = bonferroni_correction(p_values)
    
    for i, res in enumerate(corr_results):
        res['is_significant'] = significant[i]
    
    # Print results
    for res in corr_results:
        print(f"Metric: {res['metric_name']}, Corr: {res['correlation']:.3f}, P: {res['p_value']:.3f}, Sig: {res['is_significant']}")

if __name__ == "__main__":
    main()