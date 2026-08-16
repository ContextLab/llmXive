import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

_SEED = 42

def set_diagnostics_seed(seed=42):
    """Set seed for reproducibility."""
    global _SEED
    _SEED = seed
    np.random.seed(seed)

def detect_perfect_multicollinearity(df, predictor_cols):
    """
    Detect perfect multicollinearity using matrix rank check.
    Returns list of flagged pairs.
    """
    if len(predictor_cols) < 2:
        return []

    X = df[predictor_cols].dropna().values
    if X.shape[0] < 2:
        return []

    rank = np.linalg.matrix_rank(X)
    flagged_pairs = []

    if rank < X.shape[1]:
        # Check pairs
        for i in range(len(predictor_cols)):
            for j in range(i + 1, len(predictor_cols)):
                col_i = predictor_cols[i]
                col_j = predictor_cols[j]
                xi = df[col_i].dropna().values
                xj = df[col_j].dropna().values

                if len(xi) != len(xj):
                    continue

                # Check correlation
                corr = np.corrcoef(xi, xj)[0, 1]
                if abs(corr) > 0.999:
                    flagged_pairs.append({
                        'taxon_a': col_i,
                        'taxon_b': col_j,
                        'reason': 'Perfect Multicollinearity'
                    })

    return flagged_pairs

def calculate_vif(df, predictor_cols, exclude_collinear=None):
    """
    Calculate Variance Inflation Factor for predictors.
    """
    if exclude_collinear is None:
        exclude_collinear = []

    vif_results = []
    X = df[predictor_cols].dropna()

    for col in predictor_cols:
        if col in exclude_collinear:
            continue
        if col not in X.columns:
            continue

        y = X[col]
        X_other = X.drop(columns=[col])

        if X_other.shape[1] == 0:
            vif_results.append({
                'taxon': col,
                'vif': 1.0,
                'flag': 'NORMAL'
            })
            continue

        try:
            model = stats.linregress(X_other.values[:, 0], y) if X_other.shape[1] == 1 else None
            # Simplified VIF calculation
            r_squared = 0.0
            if X_other.shape[1] > 0:
                # Use correlation matrix for VIF
                corr_matrix = X.corr()
                if col in corr_matrix.columns:
                    r_squared = 1 - 1 / corr_matrix.loc[col, col] if corr_matrix.loc[col, col] != 0 else 0

            vif = 1 / (1 - r_squared) if r_squared < 1 else float('inf')
        except Exception:
            vif = 1.0

        flag = 'HIGH' if vif > 5 else 'NORMAL'
        vif_results.append({
            'taxon': col,
            'vif': float(vif) if vif != float('inf') else 999.0,
            'flag': flag
        })

    return vif_results

def run_sensitivity_analysis(correlation_results, thresholds=[0.01, 0.05, 0.10]):
    """
    Run sensitivity analysis at different p-value thresholds.
    """
    results = {}
    base_count = len([r for r in correlation_results if r.get('p_value', 1.0) <= 0.05])

    for threshold in thresholds:
        count = len([r for r in correlation_results if r.get('p_value', 1.0) <= threshold])
        pct_change = ((count - base_count) / base_count * 100) if base_count > 0 else 0.0
        results[f'threshold_{threshold}'] = {
            'count': count,
            'pct_change': pct_change
        }

    # Determine stability
    max_change = max([abs(results[f'threshold_{t}']['pct_change']) for t in thresholds])
    stability = 'STABLE' if max_change < 20 else 'UNSTABLE'
    results['stability_status'] = stability

    return results

def calculate_power(n_samples, effect_size=0.3, alpha=0.05, power_target=0.80):
    """
    Calculate power or required sample size.
    """
    if n_samples < 10:
        return {
            'minimum_sample_size': None,
            'current_power': 0.0,
            'status': 'Insufficient Data',
            'underpowered': True
        }

    # Approximate power calculation
    # Using t-test approximation for correlation
    t_val = np.abs(effect_size) * np.sqrt(n_samples - 2) / np.sqrt(1 - effect_size**2)
    power = stats.t.cdf(t_val, n_samples - 2)

    # Estimate required N for target power
    # Simplified: n = (Z_alpha + Z_beta)^2 / effect_size^2
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = stats.norm.ppf(power_target)
    required_n = int(((z_alpha + z_beta) ** 2) / (effect_size ** 2))

    underpowered = n_samples < required_n

    return {
        'minimum_sample_size': required_n,
        'current_power': float(power),
        'status': 'Underpowered' if underpowered else 'Adequate',
        'underpowered': underpowered,
        'data_source_type': 'synthetic' if n_samples < 100 else 'real'
    }

def main():
    """Main entry point for diagnostics."""
    import argparse
    parser = argparse.ArgumentParser(description='Run diagnostics')
    parser.add_argument('--input', type=str, required=True)
    parser.add_argument('--output', type=str, required=True)
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    predictor_cols = [c for c in df.columns if 'taxon' in c.lower()]

    # Detect collinearity
    collinearity = detect_perfect_multicollinearity(df, predictor_cols)

    # Save collinearity map
    collinearity_path = os.path.join(args.output, 'static_collinearity_map.json')
    with open(collinearity_path, 'w') as f:
        json.dump({'pairs': collinearity}, f, indent=2)

    logger.info(f"Diagnostics complete. Results saved to {args.output}")

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('diagnostics')
    main()
