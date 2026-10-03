"""
Power analysis module (T032, T036, T051).
"""
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from statsmodels.stats.power import tt_ind_solve_power
from scipy import stats


def calculate_power(effect_size: float, nobs1: float, nobs2: float, alpha: float = 0.05) -> float:
    """
    Calculate statistical power for a t-test.
    """
    power = tt_ind_solve_power(
        effect_size=effect_size,
        nobs1=nobs1,
        ratio=nobs2/nobs1,
        alpha=alpha,
        alternative='two-sided'
    )
    return float(power)


def analyze_bias_power(bias_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform power analysis on the bias data.
    Compares best vs worst method.
    """
    methods = bias_df['method'].unique()
    if len(methods) < 2:
        return {"power": 0.0, "effect_size": 0.0, "flag": "insufficient_data"}
    
    # Calculate mean and std for best and worst
    # Assume lower bias is better
    method_stats = {}
    for m in methods:
        subset = bias_df[bias_df['method'] == m]['bias'].dropna()
        if len(subset) > 1:
            method_stats[m] = {
                'mean': subset.mean(),
                'std': subset.std(),
                'n': len(subset)
            }
    
    if len(method_stats) < 2:
        return {"power": 0.0, "effect_size": 0.0, "flag": "insufficient_data"}
    
    sorted_methods = sorted(method_stats.keys(), key=lambda m: method_stats[m]['mean'])
    best = sorted_methods[0]
    worst = sorted_methods[-1]
    
    m1, s1, n1 = method_stats[best]['mean'], method_stats[best]['std'], method_stats[best]['n']
    m2, s2, n2 = method_stats[worst]['mean'], method_stats[worst]['std'], method_stats[worst]['n']
    
    # Cohen's d
    pooled_std = np.sqrt(((n1-1)*s1**2 + (n2-1)*s2**2) / (n1+n2-2))
    if pooled_std == 0:
        effect_size = 0.0
    else:
        effect_size = abs(m2 - m1) / pooled_std
    
    # Calculate power
    power = calculate_power(effect_size, n1, n2)
    
    flag = "normal" if power >= 0.8 else "underpowered"
    
    return {
        "best_method": best,
        "worst_method": worst,
        "effect_size": float(effect_size),
        "power": float(power),
        "n_best": n1,
        "n_worst": n2,
        "flag": flag
    }


def interpret_effect_size(effect_size: float) -> str:
    """
    Interpret Cohen's d.
    """
    if effect_size < 0.2:
        return "negligible"
    elif effect_size < 0.5:
        return "small"
    elif effect_size < 0.8:
        return "medium"
    else:
        return "large"


def save_power_analysis(results: Dict[str, Any], filepath: str):
    """
    Save power analysis results to JSON.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)


def main():
    """
    CLI entry point for power analysis.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Perform power analysis on simulation results")
    parser.add_argument("--input", required=True, help="Path to simulation_summary.csv")
    parser.add_argument("--output", default="data/results/power_analysis.json", help="Output JSON path")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        return 1
    
    try:
        df = pd.read_csv(args.input)
        results = analyze_bias_power(df)
        results['effect_size_interpretation'] = interpret_effect_size(results['effect_size'])
        save_power_analysis(results, args.output)
        print(f"Power analysis saved to {args.output}")
        print(f"Flag: {results['flag']}")
        return 0
    except Exception as e:
        print(f"Error running power analysis: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
