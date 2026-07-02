import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import pairwise_distances
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_project_root, load_config
from seed_manager import get_seed, get_random_state
from logging_config import get_analysis_logger, save_analysis_results

# Constants
PSEUDOCOUNT = 0.5
FDR_Q = 0.1
TOP_N_TAXA = 20
PERMUTATIONS = 1000  # Reduced for demo/runtime; standard is 1000-5000
CONFIDENCE_LEVEL = 0.95

logger = get_analysis_logger(__name__)

def clr_transform(data: Union[pd.DataFrame, np.ndarray], pseudocount: float = PSEUDOCOUNT) -> np.ndarray:
    """
    Apply Centered Log-Ratio (CLR) transformation to composition data.
    Adds pseudocount to handle zeros, then computes log(x / gmean(x)).
    """
    if isinstance(data, pd.DataFrame):
        data = data.values

    # Ensure float64
    data = data.astype(np.float64)

    # Add pseudocount
    data_safe = data + pseudocount

    # Calculate geometric mean for each row (subject)
    # Avoid log(0) by ensuring data_safe > 0
    log_data = np.log(data_safe)
    geom_mean = np.exp(np.mean(log_data, axis=1, keepdims=True))

    # CLR: log(x_i) - log(gmean(x))
    clr_data = log_data - np.log(geom_mean)

    return clr_data

def load_matched_pairs() -> pd.DataFrame:
    """Load matched pairs from data/processed/matched_pairs.csv"""
    root = get_project_root()
    path = root / "data" / "processed" / "matched_pairs.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)

def load_distribution_groups() -> pd.DataFrame:
    """Load distribution groups from data/processed/distribution_groups.csv"""
    root = get_project_root()
    path = root / "data" / "processed" / "distribution_groups.csv"
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return pd.read_csv(path)

def aggregate_alpha_power_path_a(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate alpha power for Path A (matched pairs).
    Assumes df already has 'alpha_power' column or computes it if raw data provided.
    For this task, we assume the CSV already contains the aggregated alpha_power.
    """
    # Ensure we have the necessary columns
    required = ['subject_id', 'alpha_power']
    if not all(c in df.columns for c in required):
        raise ValueError(f"DataFrame missing required columns: {required}")
    return df

def aggregate_alpha_power_path_b(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate alpha power for Path B (distribution groups).
    Groups by 'group' (High/Low) and computes mean alpha power.
    """
    if 'group' not in df.columns or 'alpha_power' not in df.columns:
        raise ValueError("DataFrame must have 'group' and 'alpha_power' columns for Path B")
    return df.groupby('group')['alpha_power'].mean().reset_index()

def calculate_correlation_path_a(microbiome_df: pd.DataFrame, eeg_df: pd.DataFrame) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    """
    Path A: Spearman correlation between top N taxa and alpha power.
    Returns: correlations, p_values, q_values (FDR corrected)
    """
    # Merge on subject_id
    merged = pd.merge(microbiome_df, eeg_df[['subject_id', 'alpha_power']], on='subject_id', how='inner')
    if len(merged) < 10:
        raise ValueError("Insufficient matched pairs for correlation analysis")

    # Identify top N taxa by mean abundance
    taxon_cols = [c for c in merged.columns if c not in ['subject_id', 'alpha_power']]
    if not taxon_cols:
        raise ValueError("No taxon columns found in microbiome data")

    mean_abundances = merged[taxon_cols].mean()
    top_taxa = mean_abundances.nlargest(TOP_N_TAXA).index.tolist()

    # CLR transform the top taxa
    taxon_data = merged[top_taxa].values
    clr_data = clr_transform(taxon_data)
    alpha_power = merged['alpha_power'].values

    correlations = {}
    p_values = {}

    for i, taxon in enumerate(top_taxa):
        rho, p_val = stats.spearmanr(clr_data[:, i], alpha_power)
        correlations[taxon] = rho
        p_values[taxon] = p_val

    # FDR Correction (Benjamini-Hochberg)
    p_vals = list(p_values.values())
    if len(p_vals) == 0:
        q_values = {}
    else:
        sorted_indices = np.argsort(p_vals)
        sorted_p = np.array(p_vals)[sorted_indices]
        n = len(sorted_p)
        q_vals = sorted_p * n / (np.arange(1, n + 1))
        # Ensure monotonicity
        for i in range(n - 2, -1, -1):
            q_vals[i] = min(q_vals[i], q_vals[i + 1])
        # Clip to 1.0
        q_vals = np.minimum(q_vals, 1.0)
        
        q_values = {top_taxa[sorted_indices[i]]: q_vals[i] for i in range(n)}

    return correlations, p_values, q_values

def calculate_correlation_path_b(groups_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Path B: Mann-Whitney U test between High and Low groups.
    """
    if 'group' not in groups_df.columns or 'alpha_power' not in groups_df.columns:
        raise ValueError("Invalid DataFrame for Path B analysis")

    high_group = groups_df[groups_df['group'] == 'High']['alpha_power']
    low_group = groups_df[groups_df['group'] == 'Low']['alpha_power']

    if len(high_group) == 0 or len(low_group) == 0:
        raise ValueError("One of the groups is empty")

    u_stat, p_val = stats.mannwhitneyu(high_group, low_group, alternative='two-sided')
    
    # Effect size (rank-biserial correlation)
    n1, n2 = len(high_group), len(low_group)
    r = 1 - (2 * u_stat) / (n1 * n2)

    return {
        "test_statistic": u_stat,
        "p_value": p_val,
        "effect_size_r": r,
        "n_high": n1,
        "n_low": n2
    }

def calculate_vif(microbiome_df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor for top 20 taxa (Path A only).
    """
    taxon_cols = [c for c in microbiome_df.columns if c not in ['subject_id', 'alpha_power', 'group']]
    if len(taxon_cols) == 0:
        return {}
    
    # Select top 20 by mean abundance
    mean_abundances = microbiome_df[taxon_cols].mean()
    top_taxa = mean_abundances.nlargest(TOP_N_TAXA).index.tolist()
    
    X = microbiome_df[top_taxa].values
    # Add constant for intercept
    X_with_const = np.column_stack([np.ones(X.shape[0]), X])
    
    vif_data = {}
    for i, taxon in enumerate(top_taxa):
        try:
            vif = variance_inflation_factor(X_with_const, i + 1)
            vif_data[taxon] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {taxon}: {e}")
            vif_data[taxon] = np.nan
    
    return vif_data

def run_permutation_test(
    microbiome_df: pd.DataFrame,
    eeg_df: pd.DataFrame,
    path: str = 'A',
    n_permutations: int = PERMUTATIONS,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform permutation testing to generate null distribution.
    
    Path A: Shuffle subject labels in matched pairs.
    Path B: Shuffle group labels in distribution groups.
    
    Returns dict with null distribution stats and pass/fail flag.
    """
    if random_state is None:
        random_state = get_seed()
    
    rng = np.random.default_rng(random_state)
    
    logger.info(f"Running permutation test: {n_permutations} iterations, seed={random_state}")

    if path == 'A':
        # Path A: Spearman correlation
        # 1. Compute observed statistic
        correlations, p_values, q_values = calculate_correlation_path_a(microbiome_df, eeg_df)
        
        # Use the maximum absolute correlation as the test statistic
        observed_stats = [abs(v) for v in correlations.values()]
        max_observed_stat = max(observed_stats) if observed_stats else 0.0
        
        # 2. Permute labels
        null_stats = []
        alpha_power = eeg_df['alpha_power'].values
        taxon_cols = [c for c in microbiome_df.columns if c not in ['subject_id', 'alpha_power', 'group']]
        top_taxa = microbiome_df[taxon_cols].mean().nlargest(TOP_N_TAXA).index.tolist()
        
        for i in range(n_permutations):
            # Shuffle alpha power labels
            shuffled_alpha = rng.permutation(alpha_power)
            
            # Compute correlation with shuffled data
            # We only need the max correlation for the null distribution
            max_perm_stat = 0.0
            for taxon in top_taxa:
                taxon_data = microbiome_df[taxon].values
                # CLR transform single column (pseudocount applied internally if needed, but here we assume pre-processed or simple log)
                # For simplicity in permutation, we use the original values if not CLR, but task says CLR.
                # Let's assume microbiome_df is raw, so we CLR it here.
                # Actually, to be consistent with calculate_correlation_path_a, we need to CLR the top taxa.
                # But doing full CLR for every permutation is expensive.
                # Optimization: Pre-Calculate CLR for all top taxa once.
                pass 
            
            # Optimized approach: Pre-Calculate CLR for top taxa
            # (Moved pre-calculation outside loop for performance)
            pass

        # Pre-calculate CLR for top taxa
        taxon_data = microbiome_df[top_taxa].values
        clr_data = clr_transform(taxon_data)
        
        null_stats = []
        for i in range(n_permutations):
            shuffled_alpha = rng.permutation(alpha_power)
            max_perm_stat = 0.0
            for j in range(len(top_taxa)):
                rho, _ = stats.spearmanr(clr_data[:, j], shuffled_alpha)
                if abs(rho) > max_perm_stat:
                    max_perm_stat = abs(rho)
            null_stats.append(max_perm_stat)
        
        null_stats = np.array(null_stats)
        threshold = np.percentile(null_stats, CONFIDENCE_LEVEL * 100)
        passed = max_observed_stat > threshold
        
        return {
            "path": "A",
            "observed_statistic": max_observed_stat,
            "null_distribution_mean": float(np.mean(null_stats)),
            "null_distribution_std": float(np.std(null_stats)),
            "threshold_95": float(threshold),
            "perm_test_passed": bool(passed),
            "p_permutation": float((np.sum(null_stats >= max_observed_stat) + 1) / (n_permutations + 1))
        }

    elif path == 'B':
        # Path B: Mann-Whitney U
        # 1. Compute observed statistic
        results = calculate_correlation_path_b(eeg_df) # eeg_df here actually holds the group data
        observed_stat = results['test_statistic']
        
        # 2. Permute group labels
        null_stats = []
        groups = eeg_df['group'].values
        alpha_power = eeg_df['alpha_power'].values
        
        for i in range(n_permutations):
            shuffled_groups = rng.permutation(groups)
            high_group = alpha_power[shuffled_groups == 'High']
            low_group = alpha_power[shuffled_groups == 'Low']
            
            if len(high_group) > 0 and len(low_group) > 0:
                u_stat, _ = stats.mannwhitneyu(high_group, low_group, alternative='two-sided')
                null_stats.append(u_stat)
            else:
                null_stats.append(0)
        
        null_stats = np.array(null_stats)
        # Two-tailed: check if observed is in top 2.5% or bottom 2.5%
        threshold_high = np.percentile(null_stats, 97.5)
        threshold_low = np.percentile(null_stats, 2.5)
        
        passed = (observed_stat > threshold_high) or (observed_stat < threshold_low)
        
        return {
            "path": "B",
            "observed_statistic": float(observed_stat),
            "null_distribution_mean": float(np.mean(null_stats)),
            "null_distribution_std": float(np.std(null_stats)),
            "threshold_975": float(threshold_high),
            "threshold_25": float(threshold_low),
            "perm_test_passed": bool(passed),
            "p_permutation": float((np.sum(np.abs(null_stats - np.median(null_stats)) >= np.abs(observed_stat - np.median(null_stats))) + 1) / (n_permutations + 1))
        }
    else:
        raise ValueError(f"Unknown path: {path}. Must be 'A' or 'B'.")

def save_analysis_results(results: Dict[str, Any], output_path: Optional[Path] = None):
    """
    Save analysis results to artifacts/analysis_results.json.
    Ensures the associational disclaimer is included.
    """
    if output_path is None:
        root = get_project_root()
        output_path = root / "artifacts" / "analysis_results.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    disclaimer = "Note: This analysis is associational only; no causal inference is made."
    
    final_results = {
        "disclaimer": disclaimer,
        "analysis_results": results,
        "metadata": {
            "timestamp": str(pd.Timestamp.now()),
            "random_seed": get_seed()
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Analysis results saved to {output_path}")

def main():
    """
    Main entry point for correlation analysis and permutation testing.
    Detects path (A or B) based on available files and runs appropriate analysis.
    """
    root = get_project_root()
    
    # Determine path
    path_a_file = root / "data" / "processed" / "matched_pairs.csv"
    path_b_file = root / "data" / "processed" / "distribution_groups.csv"
    
    path = 'A' if path_a_file.exists() else 'B'
    logger.info(f"Detected analysis path: {path}")
    
    try:
        if path == 'A':
            microbiome_df = load_matched_pairs()
            eeg_df = microbiome_df # Matched pairs usually merged
            
            # Calculate correlations
            correlations, p_values, q_values = calculate_correlation_path_a(microbiome_df, eeg_df)
            vif_values = calculate_vif(microbiome_df)
            
            # Run permutation test
            perm_results = run_permutation_test(microbiome_df, eeg_df, path='A')
            
            results = {
                "path": "A",
                "correlations": correlations,
                "p_values": p_values,
                "q_values": q_values,
                "vif": vif_values,
                "permutation_test": perm_results
            }
            
        else:
            # Path B
            groups_df = load_distribution_groups()
            
            # Calculate group stats
            group_results = calculate_correlation_path_b(groups_df)
            
            # Run permutation test
            perm_results = run_permutation_test(groups_df, groups_df, path='B')
            
            results = {
                "path": "B",
                "group_statistics": group_results,
                "permutation_test": perm_results
            }
        
        # Save results
        save_analysis_results(results)
        logger.info("Analysis completed successfully.")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()