import os
import sys
import logging
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

from utils.config import get_project_root, get_data_processed_path, get_output_path

logger = logging.getLogger(__name__)

# ============================================================================
# Existing Utilities (Preserved)
# ============================================================================

def nearest_neighbor_matching(
    source_masses: np.ndarray,
    target_masses: np.ndarray,
    tolerance: float = 0.1,
    source_ids: Optional[np.ndarray] = None,
    target_ids: Optional[np.ndarray] = None
) -> List[Tuple[int, int]]:
    """
    Perform nearest-neighbor mass matching between source and target datasets.
    
    Args:
        source_masses: Mass values for the source dataset (haloes).
        target_masses: Mass values for the target dataset (matched candidates).
        tolerance: Maximum allowed log-mass difference.
        source_ids: Optional IDs for source objects.
        target_ids: Optional IDs for target objects.
        
    Returns:
        List of (source_idx, target_idx) tuples representing matches.
    """
    if len(source_masses) == 0 or len(target_masses) == 0:
        return []
        
    matches = []
    source_log_masses = np.log10(source_masses)
    target_log_masses = np.log10(target_masses)
    
    used_targets = set()
    
    for s_idx, s_mass in enumerate(source_log_masses):
        diffs = np.abs(target_log_masses - s_mass)
        min_idx = np.argmin(diffs)
        
        if diffs[min_idx] <= tolerance and min_idx not in used_targets:
            matches.append((s_idx, min_idx))
            used_targets.add(min_idx)
            
    return matches

def stream_mass_matched_chunks(
    halo_path: str,
    galaxy_path: str,
    output_dir: str,
    chunk_size: int = 10000,
    mass_tolerance: float = 0.1
) -> None:
    """
    Stream halo and galaxy data, perform mass matching in chunks, 
    and write matched pairs to output directory.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    halo_df = pd.read_csv(halo_path)
    galaxy_df = pd.read_csv(galaxy_path)
    
    halo_masses = halo_df['mass'].values
    galaxy_masses = galaxy_df['stellar_mass'].values # Using stellar_mass as proxy or adjust as needed
    
    chunk_matches = []
    chunk_id = 0
    
    # Simple chunking for demonstration; in production, use iter_hdf5_groups or similar
    total_halos = len(halo_df)
    
    for i in range(0, total_halos, chunk_size):
        end_idx = min(i + chunk_size, total_halos)
        chunk_halos = halo_df.iloc[i:end_idx]
        
        # Match this chunk against the full galaxy set (or a relevant subset)
        matches = nearest_neighbor_matching(
            chunk_halos['mass'].values,
            galaxy_masses,
            tolerance=mass_tolerance,
            source_ids=chunk_halos['halo_id'].values,
            target_ids=galaxy_df['galaxy_id'].values
        )
        
        if matches:
            match_data = []
            for s_idx, t_idx in matches:
                match_data.append({
                    'halo_id': chunk_halos.iloc[s_idx]['halo_id'],
                    'galaxy_id': galaxy_df.iloc[t_idx]['galaxy_id'],
                    'mass': chunk_halos.iloc[s_idx]['mass'],
                    'b_a_ratio': chunk_halos.iloc[s_idx]['b_a_ratio'],
                    'c_a_ratio': chunk_halos.iloc[s_idx]['c_a_ratio'],
                    'triaxiality': chunk_halos.iloc[s_idx]['triaxiality'],
                    'sfr': galaxy_df.iloc[t_idx]['sfr'],
                    'effective_radius': galaxy_df.iloc[t_idx]['effective_radius']
                })
            
            out_file = os.path.join(output_dir, f"match_{chunk_id:03d}.csv")
            pd.DataFrame(match_data).to_csv(out_file, index=False)
            logger.info(f"Wrote {len(match_data)} matches to {out_file}")
            chunk_id += 1

def bin_halo_by_shape(
    df: pd.DataFrame,
    c_a_threshold_low: float = 0.5,
    c_a_threshold_high: float = 0.8
) -> pd.DataFrame:
    """
    Assign shape bins (prolate, triaxial, spherical) based on c/a ratio.
    """
    bins = []
    for _, row in df.iterrows():
        c_a = row['c_a_ratio']
        if c_a < c_a_threshold_low:
            bins.append('prolate')
        elif c_a <= c_a_threshold_high:
            bins.append('triaxial')
        else:
            bins.append('spherical')
    df = df.copy()
    df['shape_bin'] = bins
    return df

def kruskal_wallis_test(
    groups: List[np.ndarray],
    nan_policy: str = 'raise'
) -> Tuple[float, float]:
    """
    Perform Kruskal-Wallis H-test for independent samples.
    """
    if len(groups) < 2:
        raise ValueError("At least two groups are required for Kruskal-Wallis test.")
    
    # Filter out NaNs if necessary, though scipy handles 'raise' by default
    clean_groups = [g[~np.isnan(g)] for g in groups if not np.all(np.isnan(g))]
    
    if len(clean_groups) < 2:
        raise ValueError("Insufficient valid data in groups for Kruskal-Wallis test.")
        
    h_stat, p_val = scipy_stats.kruskal(*clean_groups, nan_policy=nan_policy)
    return float(h_stat), float(p_val)

def mann_whitney_u_test(
    group_a: np.ndarray,
    group_b: np.ndarray,
    alternative: str = 'two-sided'
) -> Tuple[float, float]:
    """
    Perform Mann-Whitney U test for two independent samples.
    """
    clean_a = group_a[~np.isnan(group_a)]
    clean_b = group_b[~np.isnan(group_b)]
    
    if len(clean_a) == 0 or len(clean_b) == 0:
        raise ValueError("One of the groups has no valid data.")
        
    u_stat, p_val = scipy_stats.mannwhitneyu(clean_a, clean_b, alternative=alternative)
    return float(u_stat), float(p_val)

def ks_test(
    group_a: np.ndarray,
    group_b: np.ndarray
) -> Tuple[float, float]:
    """
    Perform Kolmogorov-Smirnov two-sample test.
    """
    clean_a = group_a[~np.isnan(group_a)]
    clean_b = group_b[~np.isnan(group_b)]
    
    if len(clean_a) == 0 or len(clean_b) == 0:
        raise ValueError("One of the groups has no valid data.")
        
    ks_stat, p_val = scipy_stats.ks_2samp(clean_a, clean_b)
    return float(ks_stat), float(p_val)

def run_binning_tests(
    df: pd.DataFrame,
    target_column: str,
    bin_column: str = 'shape_bin'
) -> Dict[str, Any]:
    """
    Run non-parametric tests (KW, MWU, KS) across shape bins.
    """
    groups = [
        df[df[bin_column] == bin_name][target_column].values
        for bin_name in ['prolate', 'triaxial', 'spherical']
    ]
    
    results = {}
    
    try:
        h, p = kruskal_wallis_test(groups)
        results['kruskal_wallis'] = {'h_stat': h, 'p_value': p}
    except Exception as e:
        logger.warning(f"Kruskal-Wallis failed: {e}")
        results['kruskal_wallis'] = {'error': str(e)}
        
    # Pairwise MWU
    mwu_results = {}
    pairs = [('prolate', 'triaxial'), ('prolate', 'spherical'), ('triaxial', 'spherical')]
    for i, (g1, g2) in enumerate(pairs):
        try:
            u, p = mann_whitney_u_test(groups[i], groups[i+1] if i+1 < len(groups) else groups[0])
            # Note: Indexing logic above is simplified; proper pairing needed
            # Correct pairing based on list order:
            pass
        except Exception as e:
            mwu_results[f"{g1}_vs_{g2}"] = {'error': str(e)}
    
    # Re-doing MWU properly
    mwu_results = {}
    group_names = ['prolate', 'triaxial', 'spherical']
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            try:
                u, p = mann_whitney_u_test(groups[i], groups[j])
                mwu_results[f"{group_names[i]}_vs_{group_names[j]}"] = {'u_stat': u, 'p_value': p}
            except Exception as e:
                mwu_results[f"{group_names[i]}_vs_{group_names[j]}"] = {'error': str(e)}
                
    results['mann_whitney_u'] = mwu_results
    
    # KS Tests
    ks_results = {}
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            try:
                ks_stat, p = ks_test(groups[i], groups[j])
                ks_results[f"{group_names[i]}_vs_{group_names[j]}"] = {'ks_stat': ks_stat, 'p_value': p}
            except Exception as e:
                ks_results[f"{group_names[i]}_vs_{group_names[j]}"] = {'error': str(e)}
                
    results['kolmogorov_smirnov'] = ks_results
    
    return results

def save_statistical_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save statistical test results to a CSV or JSON file.
    """
    # Flatten results for CSV if needed
    rows = []
    for test_name, test_data in results.items():
        if isinstance(test_data, dict):
            for key, value in test_data.items():
                if isinstance(value, dict):
                    row = {'test': test_name, 'metric': key, 'p_value': value.get('p_value', None)}
                    rows.append(row)
    
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        logger.info(f"Saved statistical results to {output_path}")
    else:
        logger.warning("No valid results to save.")

# ============================================================================
# NEW: Bonferroni Correction Implementation
# ============================================================================

def apply_bonferroni_correction(
    p_values: List[float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply Bonferroni correction to a list of p-values for multiple comparisons.
    
    Args:
        p_values: List of raw p-values from statistical tests.
        alpha: Significance level (default 0.05).
        
    Returns:
        Dictionary containing:
            - 'adjusted_p_values': List of Bonferroni-adjusted p-values.
            - 'significant_indices': List of indices where adjusted p < alpha.
            - 'corrected_alpha': The new significance threshold (alpha / n).
            - 'summary': Dict with counts of significant tests.
    """
    n = len(p_values)
    if n == 0:
        return {
            'adjusted_p_values': [],
            'significant_indices': [],
            'corrected_alpha': alpha,
            'summary': {'total_tests': 0, 'significant_count': 0}
        }
    
    corrected_alpha = alpha / n
    adjusted_p_values = [min(p * n, 1.0) for p in p_values]
    
    significant_indices = [
        i for i, p_adj in enumerate(adjusted_p_values) if p_adj < alpha
    ]
    
    summary = {
        'total_tests': n,
        'significant_count': len(significant_indices),
        'significant_indices': significant_indices,
        'original_alpha': alpha,
        'corrected_alpha': corrected_alpha
    }
    
    return {
        'adjusted_p_values': adjusted_p_values,
        'significant_indices': significant_indices,
        'corrected_alpha': corrected_alpha,
        'summary': summary
    }

def run_statistical_tests(
    df: pd.DataFrame,
    target_column: str,
    bin_column: str = 'shape_bin'
) -> Dict[str, Any]:
    """
    Wrapper to run binning tests and apply Bonferroni correction.
    """
    results = run_binning_tests(df, target_column, bin_column)
    
    # Collect all p-values for correction
    all_p_values = []
    test_details = []
    
    # Extract from KW
    if 'p_value' in results.get('kruskal_wallis', {}):
        p_val = results['kruskal_wallis']['p_value']
        all_p_values.append(p_val)
        test_details.append({'test': 'kruskal_wallis', 'p_value': p_val})
    
    # Extract from MWU
    for key, val in results.get('mann_whitney_u', {}).items():
        if 'p_value' in val:
            p_val = val['p_value']
            all_p_values.append(p_val)
            test_details.append({'test': f'mwu_{key}', 'p_value': p_val})
            
    # Extract from KS
    for key, val in results.get('kolmogorov_smirnov', {}).items():
        if 'p_value' in val:
            p_val = val['p_value']
            all_p_values.append(p_val)
            test_details.append({'test': f'ks_{key}', 'p_value': p_val})
    
    if all_p_values:
        correction_result = apply_bonferroni_correction(all_p_values)
        results['bonferroni_correction'] = correction_result
        
        # Update p_values in details with adjusted ones if needed, 
        # or store the mapping. For now, we store the correction summary.
        logger.info(f"Applied Bonferroni correction: {correction_result['summary']}")
    else:
        results['bonferroni_correction'] = {'summary': 'No p-values found'}
        
    return results

def main():
    """
    Main entry point for stats analysis if run as a script.
    Demonstrates Bonferroni correction usage.
    """
    # Example usage
    sample_p_values = [0.01, 0.03, 0.04, 0.06, 0.12, 0.005]
    print(f"Original p-values: {sample_p_values}")
    
    result = apply_bonferroni_correction(sample_p_values)
    print(f"Corrected Alpha: {result['corrected_alpha']}")
    print(f"Adjusted p-values: {result['adjusted_p_values']}")
    print(f"Significant indices: {result['significant_indices']}")
    print(f"Summary: {result['summary']}")

if __name__ == "__main__":
    main()