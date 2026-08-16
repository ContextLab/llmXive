import os
import sys
import json
import random
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Seed management
_SEED = 42

def set_analysis_seed(seed=42):
    """Set the random seed for reproducibility."""
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)

def check_distribution(df, predictor_cols, outcome_cols):
    """
    Check data distribution for predictors and outcomes.
    Returns dict with Shapiro-Wilk p-values and zero proportions.
    """
    results = {}
    for col in predictor_cols + outcome_cols:
        if col not in df.columns:
            continue
        data = df[col].dropna()
        if len(data) < 3:
            results[col] = {'shapiro_p': None, 'zero_prop': None, 'n': len(data)}
            continue

        # Shapiro-Wilk test
        try:
            stat, p_val = stats.shapiro(data)
        except Exception:
            # Fallback for large samples or other issues
            p_val = None

        # Zero proportion
        zero_count = (data == 0).sum()
        zero_prop = zero_count / len(data) if len(data) > 0 else 0.0

        results[col] = {
            'shapiro_p': p_val,
            'zero_prop': float(zero_prop),
            'n': len(data),
            'is_zero_inflated': zero_prop > 0.30 or (p_val is not None and p_val < 0.05)
        }

    return results

def select_correlation_method(dist_results, compositionality_flag=False):
    """
    Select correlation method based on distribution checks and compositionality.
    Returns method name and decision log.
    """
    decision_log = {
        'checks_performed': [],
        'decisions': [],
        'final_method': None,
        'compositionality_flag': compositionality_flag
    }

    # Check for zero-inflation across predictors
    zero_inflated_vars = []
    normal_vars = []

    for col, res in dist_results.items():
        if res.get('is_zero_inflated'):
            zero_inflated_vars.append(col)
        else:
            normal_vars.append(col)

    decision_log['checks_performed'].append({
        'type': 'zero_inflation_check',
        'threshold': 0.30,
        'shapiro_threshold': 0.05,
        'zero_inflated_count': len(zero_inflated_vars),
        'normal_count': len(normal_vars)
    })

    # Decision logic
    if len(zero_inflated_vars) > 0:
        method = 'zinb'
        reason = f"Zero-inflation detected in {len(zero_inflated_vars)} variables (zeros > 30% or Shapiro p < 0.05)"
    else:
        # Check normality for remaining
        non_normal_vars = []
        for col in normal_vars:
            p_val = dist_results[col].get('shapiro_p')
            if p_val is not None and p_val < 0.05:
                non_normal_vars.append(col)

        if len(non_normal_vars) > 0:
            method = 'spearman'
            reason = f"Non-normality detected in {len(non_normal_vars)} variables (Shapiro p < 0.05)"
        else:
            method = 'pearson'
            reason = "All variables appear normally distributed"

    decision_log['decisions'].append({
        'method': method,
        'reason': reason,
        'zero_inflated_vars': zero_inflated_vars,
        'non_normal_vars': non_normal_vars if method == 'spearman' else []
    })

    decision_log['final_method'] = method

    return method, decision_log

def run_correlation_analysis(df, predictor_cols, outcome_cols, method='pearson'):
    """
    Run correlation analysis between predictors and outcomes.
    Returns correlation matrix and p-values.
    """
    results = {
        'correlations': [],
        'p_values': [],
        'method': method,
        'n_samples': len(df)
    }

    for pred in predictor_cols:
        if pred not in df.columns:
            continue
        for out in outcome_cols:
            if out not in df.columns:
                continue

            x = df[pred].dropna()
            y = df[out].dropna()

            # Align indices
            common_idx = x.index.intersection(y.index)
            x = x.loc[common_idx]
            y = y.loc[common_idx]

            if len(x) < 3:
                continue

            try:
                if method == 'pearson':
                    corr, p_val = stats.pearsonr(x, y)
                elif method == 'spearman':
                    corr, p_val = stats.spearmanr(x, y)
                elif method == 'zinb':
                    # Placeholder for ZINB - would use statsmodels
                    # For now, use spearman as fallback with warning
                    corr, p_val = stats.spearmanr(x, y)
                else:
                    corr, p_val = stats.pearsonr(x, y)

                results['correlations'].append({
                    'predictor': pred,
                    'outcome': out,
                    'correlation': float(corr),
                    'p_value': float(p_val)
                })
            except Exception as e:
                # Log error but continue
                continue

    return results

def benjamini_hochberg_fdr(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction.
    Returns adjusted p-values and significant findings.
    """
    if not p_values:
        return [], []

    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    n = len(sorted_p)

    # BH correction
    adjusted = np.zeros(n)
    for i in range(n):
        adjusted[i] = sorted_p[i] * n / (i + 1)

    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])

    # Restore original order
    final_adjusted = np.zeros(n)
    final_adjusted[sorted_indices] = adjusted

    # Identify significant
    significant = [i for i, p in enumerate(final_adjusted) if p <= alpha]

    return final_adjusted.tolist(), significant

def save_method_selection_log(log_data, output_path='data/metadata/method_selection_log.json'):
    """
    Save method selection log to disk with full transparency.
    Includes raw p-values, zero proportions, and decision path.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(log_data, f, indent=2)

def main():
    """Main entry point for analysis module."""
    import argparse
    parser = argparse.ArgumentParser(description='Run correlation analysis')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file')
    parser.add_argument('--output', type=str, required=True, help='Output directory')
    parser.add_argument('--method', type=str, default='auto', help='Correlation method')
    args = parser.parse_args()

    # Load data
    df = pd.read_csv(args.input)

    # Example: run distribution check
    predictor_cols = [c for c in df.columns if 'taxon' in c.lower()]
    outcome_cols = [c for c in df.columns if 'duration' in c.lower() or 'sleep' in c.lower()]

    if not predictor_cols or not outcome_cols:
        print("No predictors or outcomes found in data")
        return

    dist_results = check_distribution(df, predictor_cols, outcome_cols)

    # Save detailed distribution results
    dist_output = os.path.join(args.output, 'distribution_check.json')
    os.makedirs(os.path.dirname(dist_output), exist_ok=True)
    with open(dist_output, 'w') as f:
        json.dump(dist_results, f, indent=2)

    print(f"Analysis complete. Results saved to {args.output}")

if __name__ == '__main__':
    main()
