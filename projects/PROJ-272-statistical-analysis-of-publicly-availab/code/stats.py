"""
Statistical testing module.
Performs Mann-Whitney U tests and calculates effect sizes.
"""
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

logger = logging.getLogger(__name__)

def load_feature_matrix(input_path: Path) -> pd.DataFrame:
    return pd.read_csv(input_path)

def prepare_group_data(df: pd.DataFrame, group_col: str = 'label', feature_cols: List[str] = None) -> Dict[str, np.ndarray]:
    """Prepare data for group comparisons."""
    groups = df.groupby(group_col)
    data = {}
    for name, group in groups:
        if feature_cols:
            data[name] = group[feature_cols].values
        else:
            # Exclude non-feature columns
            exclude_cols = [group_col, 'participant_id']
            feature_cols = [c for c in df.columns if c not in exclude_cols]
            data[name] = group[feature_cols].values
    return data

def run_mann_whitney_u(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    """Run Mann-Whitney U test."""
    stat, p_value = mannwhitneyu(group1, group2, alternative='two-sided')
    return stat, p_value

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """Calculate Cohen's d effect size."""
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1), np.std(group2)
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return (mean1 - mean2) / pooled_std

def run_group_comparisons(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Dict[str, Any]]:
    """Run group comparisons for all features."""
    groups = df['label'].unique()
    results = {}
    
    if 'Control' not in groups or 'AD' not in groups:
        logger.warning("Control or AD group not found.")
        return results
    
    control_data = df[df['label'] == 'Control']
    ad_data = df[df['label'] == 'AD']
    
    for col in feature_cols:
        if col in ['label', 'participant_id']:
            continue
        
        g1 = control_data[col].values
        g2 = ad_data[col].values
        
        stat, p_val = run_mann_whitney_u(g1, g2)
        cohens_d = calculate_cohens_d(g1, g2)
        
        results[col] = {
            "statistic": stat,
            "p_value": p_val,
            "cohens_d": cohens_d
        }
    
    return results

def apply_bonferroni_correction(results: Dict[str, Dict[str, Any]], alpha: float = 0.05) -> Dict[str, Dict[str, Any]]:
    """Apply Bonferroni correction to p-values."""
    n_tests = len(results)
    for col in results:
        raw_p = results[col]['p_value']
        adj_p = raw_p * n_tests
        results[col]['adjusted_p_value'] = min(adj_p, 1.0)
        results[col]['significant'] = results[col]['adjusted_p_value'] < alpha
    return results

def check_sample_sizes(df: pd.DataFrame) -> Dict[str, int]:
    """Check sample sizes for each group."""
    return df['label'].value_counts().to_dict()

def save_results(results: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Statistical testing")
    parser.add_argument("--input", required=True, help="Input features CSV")
    parser.add_argument("--output", required=True, help="Output stats JSON")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    df = load_feature_matrix(input_path)
    feature_cols = [c for c in df.columns if c not in ['label', 'participant_id']]
    
    results = run_group_comparisons(df, feature_cols)
    results = apply_bonferroni_correction(results)
    
    # Save raw and adjusted p-values
    p_values = {col: {"raw": r["p_value"], "adjusted": r["adjusted_p_value"]} for col, r in results.items()}
    save_results(p_values, output_path.parent / "stats_p_values.json")
    
    # Save Cohen's d
    cohens_d = {col: r["cohens_d"] for col, r in results.items()}
    save_results(cohens_d, output_path.parent / "stats_cohens_d.json")
    
    # Save Rank-Biserial (placeholder)
    rank_biserial = {col: 0.0 for col in results.keys()} # Placeholder
    save_results(rank_biserial, output_path.parent / "stats_rank_biserial.json")
    
    # Merge into statistical_metrics.json
    merged = {
        "p_values": p_values,
        "cohens_d": cohens_d,
        "rank_biserial": rank_biserial
    }
    save_results(merged, output_path.parent / "statistical_metrics.json")
    
    logger.info("Statistical testing completed.")

if __name__ == "__main__":
    main()
