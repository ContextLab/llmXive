"""
Permutation Test Implementation.

Implements the Permutation Test logic as ratified by T033a (replacing ANOVA).
Includes functions for running the test, calculating effect sizes, and power analysis.
"""
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from statsmodels.stats.power import TTestIndPower
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

def run_permutation_test(
    group_a: np.ndarray, 
    group_b: np.ndarray, 
    n_permutations: int = 10000, 
    seed: int = 42
) -> Tuple[float, float, float]:
    """
    Perform a permutation test to compare two groups.
    
    Returns:
      p_value: Two-tailed p-value.
      effect_size: Cohen's d.
      observed_diff: The observed mean difference.
    """
    np.random.seed(seed)
    
    # Calculate observed statistic
    obs_diff = np.mean(group_b) - np.mean(group_a)
    obs_diff = abs(obs_diff) # Two-tailed, so absolute difference
    
    # Combine groups
    combined = np.concatenate([group_a, group_b])
    n_a = len(group_a)
    n_b = len(group_b)
    n_total = n_a + n_b
    
    # Permutation distribution
    count_extreme = 0
    
    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_a = combined[:n_a]
        perm_b = combined[n_a:]
        
        perm_diff = abs(np.mean(perm_b) - np.mean(perm_a))
        
        if perm_diff >= obs_diff:
            count_extreme += 1
    
    p_value = count_extreme / n_permutations
    
    # Calculate Cohen's d for observed difference
    effect_size = calculate_effect_size(group_a, group_b)
    
    return p_value, effect_size, obs_diff

def calculate_effect_size(group_a: np.ndarray, group_b: np.ndarray) -> float:
    """Calculate Cohen's d."""
    n1, n2 = len(group_a), len(group_b)
    mean1, mean2 = np.mean(group_a), np.mean(group_b)
    var1, var2 = np.var(group_a, ddof=1), np.var(group_b, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return (mean2 - mean1) / pooled_std

def run_post_hoc_power_analysis(
    observed_cohen_d: float, 
    n_per_group: int, 
    alpha: float = 0.05, 
    target_power: float = 0.80
) -> Dict[str, Any]:
    """
    Perform post-hoc power calculation using statsmodels.
    """
    power_analysis = TTestIndPower()
    
    try:
        power = power_analysis.solve_power(
            effect_size=abs(observed_cohen_d),
            nobs1=n_per_group,
            alpha=alpha,
            power=None,
            ratio=1.0
        )
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}")
        power = 0.0
    
    status = "pass" if power >= target_power else "fail"
    
    return {
        "power_value": float(power),
        "target": target_power,
        "status": status
    }

def calculate_power(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> float:
    """Helper to calculate power given effect size and sample sizes."""
    power_analysis = TTestIndPower()
    try:
        power = power_analysis.solve_power(
            effect_size=abs(effect_size),
            nobs1=n1,
            alpha=alpha,
            power=None,
            ratio=n2/n1
        )
        return float(power)
    except Exception:
        return 0.0

def run_sensitivity_analysis():
    """
    Placeholder for sensitivity analysis logic.
    The actual implementation is moved to sensitivity.py to keep this file focused.
    """
    pass

def run_loio_analysis(
    d_scores_df: 'pd.DataFrame', 
    complexity_df: 'pd.DataFrame',
    n_permutations: int = 10000,
    seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Perform Leave-One-Image-Out (LOIO) sensitivity analysis.
    
    For each unique image in the dataset, exclude all trials associated with that
    image, re-run the permutation test, and record the resulting p-value.
    
    Args:
        d_scores_df: DataFrame with columns ['participant_id', 'session_id', 'complexity_condition', 'd_score']
        complexity_df: DataFrame with columns ['filename', 'complexity_category']
        n_permutations: Number of permutations for the test.
        seed: Random seed for reproducibility.
        
    Returns:
        List of dicts containing 'image_excluded', 'p_value', 'n_trials_remaining'.
    """
    import pandas as pd
    
    results = []
    
    # Get unique images (filenames) from complexity_df
    # Note: complexity_condition in d_scores_df maps to the category derived from filename
    unique_images = complexity_df['filename'].unique()
    
    # Merge d_scores with complexity to get the specific image used for each session
    # Assuming 'complexity_condition' in d_scores matches 'complexity_category' in complexity_df
    # and we need to map back to the specific image filename.
    # Since multiple images might map to the same category, we need a mapping.
    # However, the task implies excluding "one image at a time".
    # We assume d_scores_df has a way to link to the specific image, or we iterate categories.
    # Given the schema in T026b, 'complexity_condition' is Low/High.
    # To support LOIO on *images*, we assume the experimental design links specific images to sessions.
    # If d_scores_df doesn't have 'image_filename', we cannot do strict image-level LOIO.
    # We will assume the 'complexity_condition' represents the image used in that session for this analysis
    # (or that the dataset is small enough that each condition is a specific image, or we iterate unique conditions).
    # STRICT INTERPRETATION: Iterate over unique values in 'complexity_condition' if 'image_filename' is missing,
    # but the prompt says "Exclude one image at a time".
    # Let's assume the d_scores_df actually contains an 'image_id' or 'filename' column derived from the join in T026b/T035a.
    # If not, we fallback to iterating unique categories as a proxy, but log a warning.
    
    if 'image_filename' not in d_scores_df.columns:
        logger.warning("d_scores_df missing 'image_filename'. Iterating over unique complexity_condition values instead.")
        unique_exclusions = complexity_df['complexity_category'].unique()
        # We will use the category name as the exclusion key
        exclusion_key = 'complexity_condition'
    else:
        unique_exclusions = d_scores_df['image_filename'].unique()
        exclusion_key = 'image_filename'
        
    for exclusion_val in unique_exclusions:
        # Filter out trials associated with the excluded image
        if exclusion_key == 'complexity_condition':
            mask = d_scores_df[exclusion_key] != exclusion_val
        else:
            mask = d_scores_df[exclusion_key] != exclusion_val
        
        subset_df = d_scores_df[mask]
        
        n_trials = len(subset_df)
        
        # Need at least some data to run the test
        if n_trials < 4: # Minimum 2 per group ideally
            results.append({
                "image_excluded": str(exclusion_val),
                "p_value": None,
                "n_trials_remaining": n_trials,
                "status": "insufficient_data"
            })
            continue
        
        # Split into groups
        group_low = subset_df[subset_df['complexity_condition'] == 'Low']['d_score'].values
        group_high = subset_df[subset_df['complexity_condition'] == 'High']['d_score'].values
        
        if len(group_low) == 0 or len(group_high) == 0:
            results.append({
                "image_excluded": str(exclusion_val),
                "p_value": None,
                "n_trials_remaining": n_trials,
                "status": "missing_group"
            })
            continue
        
        p_val, _, _ = run_permutation_test(
            group_low, 
            group_high, 
            n_permutations=n_permutations, 
            seed=seed
        )
        
        results.append({
            "image_excluded": str(exclusion_val),
            "p_value": float(p_val),
            "n_trials_remaining": int(n_trials),
            "status": "valid"
        })
        
    return results

def main():
    """CLI entry point for permutation test."""
    # Example usage
    logger.info("Permutation test module loaded.")

if __name__ == "__main__":
    main()