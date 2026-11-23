"""
Permutation Test Implementation.
Replaces ANOVA as per Amendment 001.
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from statsmodels.stats.power import TTestIndPower
import logging
import json
from pathlib import Path

from config import get_project_root, get_data_path

logger = logging.getLogger(__name__)


def run_permutation_test(
    group1: np.ndarray,
    group2: np.ndarray,
    n_permutations: int = 1000,
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Perform a permutation test to compare two groups.
    
    Args:
        group1: Array of values for group 1 (Low complexity).
        group2: Array of values for group 2 (High complexity).
        n_permutations: Number of permutations to run.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (p_value, effect_size, observed_cohen_d).
    """
    np.random.seed(seed)
    
    # Observed statistic: mean difference
    obs_diff = np.mean(group1) - np.mean(group2)
    
    # Combine groups
    combined = np.concatenate([group1, group2])
    n1 = len(group1)
    n2 = len(group2)
    n_total = n1 + n2
    
    # Permutation distribution
    perm_diffs = np.zeros(n_permutations)
    for i in range(n_permutations):
        np.random.shuffle(combined)
        perm_diffs[i] = np.mean(combined[:n1]) - np.mean(combined[n1:])
    
    # Calculate p-value (two-tailed)
    # Proportion of permuted diffs as extreme or more extreme than observed
    extreme_count = np.sum(np.abs(perm_diffs) >= np.abs(obs_diff))
    p_value = extreme_count / n_permutations
    
    # Effect size: Cohen's d
    # pooled SD
    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)
    n1_float = float(n1)
    n2_float = float(n2)
    
    pooled_sd = np.sqrt(((n1_float - 1) * var1 + (n2_float - 1) * var2) / (n1_float + n2_float - 2))
    
    if pooled_sd == 0:
        cohens_d = 0.0
    else:
        cohens_d = obs_diff / pooled_sd
        
    # Effect size metric from permutation distribution
    # Standardized mean difference relative to null distribution
    # We can use the observed t-statistic relative to the null distribution
    # Or simply report Cohen's d as the effect size.
    # The task asks for 'effect_size' and 'observed_cohen_d'.
    # We'll use Cohen's d for both for simplicity, or calculate a permutation-based effect size.
    # Let's calculate the effect size as the observed difference divided by the SD of the null distribution.
    null_sd = np.std(perm_diffs)
    if null_sd == 0:
        perm_effect_size = 0.0
    else:
        perm_effect_size = obs_diff / null_sd
        
    # Return p_value, effect_size (perm based), observed_cohen_d
    return p_value, perm_effect_size, cohens_d


def calculate_effect_size(
    group1: np.ndarray,
    group2: np.ndarray
) -> float:
    """
    Calculate Cohen's d for two groups.
    
    Args:
        group1: Array of values for group 1.
        group2: Array of values for group 2.
        
    Returns:
        Cohen's d value.
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1 = np.var(group1, ddof=1)
    var2 = np.var(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    
    pooled_sd = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_sd == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_sd


def save_permutation_results(
    p_value: float,
    effect_size: float,
    observed_cohen_d: float,
    n_permutations: int = 1000,
    status: str = "valid",
    methodology: str = "Permutation Test (n=1000) as per Amendment 001",
    output_path: Optional[Path] = None
) -> None:
    """
    Save permutation test results to a JSON file.
    
    Args:
        p_value: The calculated p-value.
        effect_size: The calculated effect size.
        observed_cohen_d: The observed Cohen's d.
        n_permutations: Number of permutations.
        status: Status of the test.
        methodology: Description of the methodology.
        output_path: Path to save the JSON file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "results" / "permutation_results.json"
        
    results = {
        "p_value": p_value,
        "effect_size": effect_size,
        "observed_cohen_d": observed_cohen_d,
        "n_permutations": n_permutations,
        "status": status,
        "methodology": methodology
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Permutation results saved to {output_path}")


def main() -> None:
    """
    Main entry point for T033 (Permutation Test).
    This script loads data, runs the test, and saves results.
    """
    project_root = get_project_root()
    d_scores_path = project_root / "data" / "processed" / "aggregated_d_scores.csv"
    
    if not d_scores_path.exists():
        logger.error("Aggregated D-scores not found. Run T026b-3 first.")
        return
        
    import pandas as pd
    df = pd.read_csv(d_scores_path)
    
    # Filter for valid D-scores
    df = df.dropna(subset=['d_score'])
    
    # Split by complexity condition
    low = df[df['complexity_condition'] == 'Low']['d_score'].values
    high = df[df['complexity_condition'] == 'High']['d_score'].values
    
    if len(low) < 10 or len(high) < 10:
        logger.error("Insufficient data for permutation test.")
        return
        
    p_val, eff_size, coh_d = run_permutation_test(low, high)
    
    save_permutation_results(p_val, eff_size, coh_d)
    
    logger.info(f"Permutation test complete. p={p_val:.4f}, d={coh_d:.4f}")


if __name__ == "__main__":
    main()
