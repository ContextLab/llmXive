import pandas as pd
import numpy as np
import json
import os
from typing import Dict, Any, List, Optional
from statsmodels.stats.power import tt_ind_solve_power
from scipy import stats
import logging

logger = logging.getLogger(__name__)

def load_simulation_summary(input_path: str) -> pd.DataFrame:
    """Load the simulation summary CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"File not found: {input_path}")
    return pd.read_csv(input_path)

def calculate_effect_size(group1: pd.Series, group2: pd.Series) -> float:
    """Calculate Cohen's d between two groups."""
    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(), group2.std()
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return abs(mean1 - mean2) / pooled_std

def calculate_power(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """Calculate statistical power for a two-sample t-test."""
    power = tt_ind_solve_power(effect_size=effect_size, nobs1=n1, alpha=alpha, ratio=n2/n1)
    return power

def analyze_bias_power(df_summary: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze statistical power for bias comparison between methods.
    Compare the best and worst performing methods at each beta level.
    """
    # Identify bias columns
    bias_cols = [c for c in df_summary.columns if 'bias' in c.lower() and 'mean' not in c.lower()]
    if len(bias_cols) < 2:
        return {'error': 'Not enough bias columns to compare'}
    
    # Group by beta
    results = []
    for beta in df_summary['beta'].unique():
        subset = df_summary[df_summary['beta'] == beta]
        
        # Calculate mean bias per method
        method_betas = {}
        for col in bias_cols:
            method = col.split('_')[0] # Heuristic
            if method not in method_betas:
                method_betas[method] = []
            # Take the mean of the bias column for this beta
            # Note: This is a simplification. Ideally, we have one row per run.
            # Here we assume the subset has multiple rows (runs)
            method_betas[method].append(subset[col].mean())
        
        # Compare best and worst
        if len(method_betas) >= 2:
            methods = list(method_betas.keys())
            best_method = min(methods, key=lambda m: np.mean(method_betas[m]))
            worst_method = max(methods, key=lambda m: np.mean(method_betas[m]))
            
            group1 = subset[[c for c in bias_cols if best_method in c]].mean(axis=1)
            group2 = subset[[c for c in bias_cols if worst_method in c]].mean(axis=1)
            
            if len(group1) > 1 and len(group2) > 1:
                effect_size = calculate_effect_size(group1, group2)
                power = calculate_power(effect_size, len(group1), len(group2))
                
                results.append({
                    'beta': beta,
                    'method1': best_method,
                    'method2': worst_method,
                    'effect_size': float(effect_size),
                    'power': float(power),
                    'flag': 'low_power' if power < 0.8 else 'sufficient_power'
                })
    
    return {
        'analysis_date': str(pd.Timestamp.now()),
        'results': results,
        'target_power': 0.8,
        'effect_size_assumption': 0.5
    }

def generate_power_report(df_summary: pd.DataFrame) -> Dict[str, Any]:
    """Generate a comprehensive power report."""
    report = analyze_bias_power(df_summary)
    return report

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='data/results/simulation_summary.csv')
    parser.add_argument('--output', default='data/results/power_analysis.json')
    args = parser.parse_args()
    
    df = load_simulation_summary(args.input)
    report = generate_power_report(df)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Power report saved to {args.output}")

if __name__ == "__main__":
    main()