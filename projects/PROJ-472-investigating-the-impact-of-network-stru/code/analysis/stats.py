import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_data_root
from utils.logger import get_logger

logger = get_logger(__name__)

def load_metrics_data(data_root: Path) -> pd.DataFrame:
    """
    Load structural and avalanche metrics from the unified export file.
    The file is produced by code/analysis/export_metrics.py (T017).
    """
    metrics_file = data_root / "processed" / "metrics.csv"
    if not metrics_file.exists():
        logger.error(f"Metrics file not found: {metrics_file}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(metrics_file)
        logger.info(f"Loaded {len(df)} participants from {metrics_file}")
        return df
    except Exception as e:
        logger.error(f"Failed to load metrics: {e}")
        return pd.DataFrame()

def compute_spearman_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Spearman rank correlation between structural metrics and avalanche exponents.
    
    Expected columns in df:
    - structural columns: 'degree_centrality_mean', 'clustering_coeff_mean', 'rich_club_mean'
    - avalanche columns: 'exponent', 'duration_mean', 'size_mean'
    
    Returns a DataFrame with correlation coefficients and p-values.
    """
    if df.empty:
        return pd.DataFrame()

    # Define the columns to correlate based on T014 and T015c outputs
    structural_cols = [col for col in df.columns if col in ['degree_centrality_mean', 'clustering_coeff_mean', 'rich_club_mean']]
    avalanche_cols = [col for col in df.columns if col in ['exponent', 'duration_mean', 'size_mean']]

    if not structural_cols or not avalanche_cols:
        logger.warning(f"Missing expected columns. Structural: {structural_cols}, Avalanche: {avalanche_cols}")
        return pd.DataFrame()

    results = []
    
    for s_col in structural_cols:
        for a_col in avalanche_cols:
            # Drop rows where either variable is NaN
            valid_data = df[[s_col, a_col]].dropna()
            if len(valid_data) < 3:
                logger.warning(f"Not enough data points for {s_col} vs {a_col} (n={len(valid_data)})")
                continue

            corr, p_value = stats.spearmanr(valid_data[s_col], valid_data[a_col])
            
            results.append({
                "structural_metric": s_col,
                "avalanche_metric": a_col,
                "rho": corr,
                "p_value": p_value,
                "n_samples": len(valid_data)
            })

    return pd.DataFrame(results)

def run_permutation_test(df: pd.DataFrame, n_permutations: int = 1000, seed: int = 42) -> Dict[str, Any]:
    """
    Perform a non-parametric permutation test to assess the significance of the 
    observed correlation against the null hypothesis of no association.
    
    Uses max-t method logic: for each permutation, compute the max |t| (or rho)
    across all tested pairs to control family-wise error rate.
    """
    if df.empty:
        return {"max_p_value": 1.0, "observed_stats": {}, "permuted_stats": []}

    structural_cols = [col for col in df.columns if col in ['degree_centrality_mean', 'clustering_coeff_mean', 'rich_club_mean']]
    avalanche_cols = [col for col in df.columns if col in ['exponent', 'duration_mean', 'size_mean']]

    if not structural_cols or not avalanche_cols:
        return {"max_p_value": 1.0, "observed_stats": {}, "permuted_stats": []}

    rng = np.random.default_rng(seed)
    
    # Store observed statistics
    observed_stats = {}
    for s_col in structural_cols:
        for a_col in avalanche_cols:
            valid_data = df[[s_col, a_col]].dropna()
            if len(valid_data) >= 3:
                corr, _ = stats.spearmanr(valid_data[s_col], valid_data[a_col])
                observed_stats[f"{s_col}_{a_col}"] = corr

    # Permutation loop
    max_rhos = []
    
    # We need to align the indices for permutation
    # Identify common subjects across all relevant columns
    relevant_cols = structural_cols + avalanche_cols
    common_df = df[relevant_cols].dropna()
    
    if len(common_df) < 3:
        logger.warning("Insufficient common data for permutation test")
        return {"max_p_value": 1.0, "observed_stats": observed_stats, "permuted_stats": []}

    for i in range(n_permutations):
        # Shuffle the avalanche columns relative to structural columns
        # We permute the rows of the common_df to break association
        permuted_df = common_df.copy()
        # Shuffle only the avalanche columns to preserve internal structure of avalanche data
        for a_col in avalanche_cols:
            permuted_df[a_col] = rng.permutation(permuted_df[a_col].values)
        
        # Calculate max |rho| for this permutation
        max_rho = 0.0
        for s_col in structural_cols:
            for a_col in avalanche_cols:
                corr, _ = stats.spearmanr(permuted_df[s_col], permuted_df[a_col])
                max_rho = max(max_rho, abs(corr))
        max_rhos.append(max_rho)

    # Calculate p-value for each observed stat
    p_values = {}
    for key, obs_val in observed_stats.items():
        # Two-tailed: count how many permuted max_rhos >= |observed|
        count = sum(1 for m in max_rhos if m >= abs(obs_val))
        p_values[key] = (count + 1) / (n_permutations + 1)

    return {
        "observed_stats": observed_stats,
        "p_values": p_values,
        "n_permutations": n_permutations
    }

def apply_holm_bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Holm-Bonferroni correction to a list of p-values.
    Returns (is_significant, corrected_p_values).
    """
    if not p_values:
        return [], []

    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = [p_values[i] for i in sorted_indices]
    
    corrected_p = []
    is_sig = []
    
    for i, p in enumerate(sorted_p):
        # Holm's step-down procedure
        adjusted = p * (n - i)
        if adjusted > 1.0:
            adjusted = 1.0
        corrected_p.append(adjusted)
        is_sig.append(adjusted < alpha)

    # Reorder to original indices
    final_sig = [False] * n
    final_corr = [0.0] * n
    for idx, sig in enumerate(is_sig):
        original_idx = sorted_indices[idx]
        final_sig[original_idx] = sig
        final_corr[original_idx] = corrected_p[idx]
        
    return final_sig, final_corr

def calculate_vif(df: pd.DataFrame, features: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for structural metrics.
    Used to detect multicollinearity.
    """
    if df.empty:
        return {}

    if features is None:
        features = [col for col in df.columns if col in ['degree_centrality_mean', 'clustering_coeff_mean', 'rich_club_mean']]
    
    if len(features) < 2:
        return {f: 1.0 for f in features}

    # Add a constant for intercept
    X = df[features].dropna()
    if X.empty or len(X) < len(features) + 1:
        return {f: float('nan') for f in features}

    try:
        vif_data = {}
        for i, feature in enumerate(features):
            vif = variance_inflation_factor(X.values, i)
            vif_data[feature] = float(vif)
        return vif_data
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        return {f: float('nan') for f in features}

def run_collinearity_diagnostics(data_root: Path) -> Dict[str, Any]:
    """
    Run VIF analysis and save status to data/results/collinearity_status.json.
    Returns the status dict.
    """
    df = load_metrics_data(data_root)
    if df.empty:
        return {"high_collinearity": False, "vif_value": 0.0, "vif_details": {}}

    vif_results = calculate_vif(df)
    
    max_vif = max(vif_results.values()) if vif_results else 0.0
    high_collinearity = any(v >= 5.0 for v in vif_results.values())
    
    status = {
        "high_collinearity": high_collinearity,
        "vif_value": float(max_vif),
        "vif_details": vif_results
    }
    
    # Save to file for T023/T021
    status_file = data_root / "results" / "collinearity_status.json"
    status_file.parent.mkdir(parents=True, exist_ok=True)
    with open(status_file, 'w') as f:
        json.dump(status, f, indent=2)
    
    logger.info(f"Saved collinearity status to {status_file}")
    return status

def run_robustness_analysis(data_root: Path):
    """
    Placeholder for robustness analysis (e.g., removing outliers).
    Currently handled by T022 (Sensitivity Sweep).
    """
    logger.info("Robustness analysis delegated to sensitivity sweep (T022).")

def run_correlation_analysis(data_root: Path):
    """
    Main entry point for T019.
    1. Check routing state (T029c).
    2. Load metrics.
    3. Compute Spearman correlations.
    4. Run permutation test.
    5. Apply Holm-Bonferroni correction.
    6. Run collinearity diagnostics.
    7. Save results.
    """
    # 1. Check Routing State
    routing_file = data_root / "processed" / "routing_state.json"
    if not routing_file.exists():
        logger.error(f"Routing state not found: {routing_file}. Ensure T029c has run.")
        return
    
    with open(routing_file, 'r') as f:
        routing_state = json.load(f)
    
    if routing_state.get('status') == 'halt':
        logger.warning("Pipeline halted due to sample size gate. Skipping correlation analysis.")
        return

    logger.info("Starting Correlation Analysis (T019)...")
    
    # 2. Load Metrics
    df = load_metrics_data(data_root)
    if df.empty:
        logger.error("No metrics data found for correlation analysis.")
        return

    # 3. Compute Spearman Correlations
    corr_df = compute_spearman_correlations(df)
    
    # 4. Run Permutation Test
    perm_results = run_permutation_test(df, n_permutations=1000)
    
    # 5. Apply Holm-Bonferroni Correction
    p_values = list(perm_results['p_values'].values())
    is_sig, corrected_p = apply_holm_bonferroni_correction(p_values)
    
    # Merge results into a report
    report_data = []
    for i, (key, obs_val) in enumerate(perm_results['observed_stats'].items()):
        parts = key.split('_')
        if len(parts) >= 2:
            s_col = '_'.join(parts[:-1]) # Rejoin in case of underscores in names
            a_col = parts[-1]
            report_data.append({
                "structural_metric": s_col,
                "avalanche_metric": a_col,
                "rho": obs_val,
                "p_value_raw": perm_results['p_values'][key],
                "p_value_corrected": corrected_p[i],
                "significant_holm": is_sig[i]
            })
    
    report_df = pd.DataFrame(report_data)
    
    # 6. Collinearity Diagnostics
    collin_status = run_collinearity_diagnostics(data_root)
    
    # 7. Save Results
    results_dir = data_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = results_dir / "correlation_report.csv"
    report_df.to_csv(report_file, index=False)
    logger.info(f"Saved correlation report to {report_file}")
    
    # Save full permutation stats
    perm_file = results_dir / "permutation_results.json"
    with open(perm_file, 'w') as f:
        json.dump(perm_results, f, indent=2)
    logger.info(f"Saved permutation results to {perm_file}")

def main():
    data_root = get_data_root()
    run_correlation_analysis(data_root)

if __name__ == "__main__":
    main()