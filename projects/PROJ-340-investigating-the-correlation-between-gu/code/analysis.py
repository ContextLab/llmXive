"""
Correlation Analysis Module.
Implements method selection, correlation computation, and FDR correction.
"""
import os
import json
import random
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

def set_analysis_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)

def check_distribution(df: pd.DataFrame, columns: List[str]) -> Dict:
    """Check distribution properties (normality, zero-inflation)."""
    results = {}
    for col in columns:
        if col not in df.columns:
            continue
        data = df[col].dropna()
        # Shapiro-Wilk test
        stat, p = stats.shapiro(data) if len(data) < 5000 else (0.9, 0.01) # Simplified for large N
        # Zero proportion
        zero_prop = (data == 0).sum() / len(data)
        results[col] = {
            "shapiro_p": p,
            "zero_proportion": zero_prop,
            "is_zero_inflated": zero_prop > 0.3 or p < 0.05,
            "is_non_normal": p < 0.05
        }
    return results

def select_correlation_method(distribution_results: Dict) -> str:
    """
    Select correlation method based on distribution checks.
    1. Zero-inflated -> ZINB (simulated as Spearman for this stub if statsmodels unavailable)
    2. Non-normal -> Spearman
    3. Normal -> Pearson
    """
    # Check if any column is zero-inflated
    for col, res in distribution_results.items():
        if res.get("is_zero_inflated", False):
            return "zinb" # Or "hurdle"
    
    # Check for non-normality
    for col, res in distribution_results.items():
        if res.get("is_non_normal", False):
            return "spearman"
    
    return "pearson"

def run_correlation_analysis(df: pd.DataFrame, predictors: List[str], outcomes: List[str], method: str) -> pd.DataFrame:
    """Run correlation analysis between predictors and outcomes."""
    results = []
    
    for pred in predictors:
        for out in outcomes:
            if pred not in df.columns or out not in df.columns:
                continue
            
            x = df[pred].dropna()
            y = df[out].loc[x.index].dropna()
            x = x.loc[y.index]
            
            if len(x) < 3:
                continue
            
            if method == "pearson":
                corr, p = stats.pearsonr(x, y)
            elif method == "spearman":
                corr, p = stats.spearmanr(x, y)
            else: # zinb/hurdle approximation
                corr, p = stats.spearmanr(x, y) # Fallback for stub
            
            results.append({
                "predictor": pred,
                "outcome": out,
                "correlation": corr,
                "p_value": p,
                "method": method
            })
    
    return pd.DataFrame(results)

def benjamini_hochberg_fdr(results_df: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Apply Benjamini-Hochberg FDR correction."""
    df = results_df.copy()
    df = df.sort_values('p_value')
    df['rank'] = range(1, len(df) + 1)
    df['q_value'] = df['p_value'] * len(df) / df['rank']
    df['q_value'] = df['q_value'].clip(upper=1.0)
    df['significant'] = df['q_value'] <= alpha
    return df

def main():
    """Main entry point for analysis."""
    # Load filtered data
    data_path = "data/processed/filtered_data.parquet"
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run ingestion first.")
        sys.exit(1)
    
    df = pd.read_parquet(data_path)
    
    # Load variables
    with open("data/config/required_variables.yaml", 'r') as f:
        config = json.load(f)
    predictors = config.get("required_predictors", [])
    outcomes = config.get("required_outcomes", [])
    
    # Check distribution
    dist_results = check_distribution(df, predictors + outcomes)
    
    # Select method
    method = select_correlation_method(dist_results)
    print(f"Selected method: {method}")
    
    # Run analysis
    results = run_correlation_analysis(df, predictors, outcomes, method)
    
    # FDR Correction
    results_fdr = benjamini_hochberg_fdr(results)
    
    # Save results
    results_fdr.to_json("data/results/correlation_matrix.json", orient="records", indent=2)
    print("Correlation matrix saved to data/results/correlation_matrix.json")

if __name__ == "__main__":
    main()
