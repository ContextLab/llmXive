import os
import json
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from config import get_processed_path, get_event_window_days, get_control_window_days, get_random_seed
from utils.logging import get_logger

logger = get_logger(__name__)

# --- Data Loading ---

def load_master_dataset() -> pd.DataFrame:
    """Load the master dataset from the processed directory."""
    path = get_processed_path() / "master_dataset.csv"
    if not path.exists():
        raise FileNotFoundError(f"Master dataset not found at {path}")
    return pd.read_csv(path)

# --- Statistical Tests ---

def perform_ks_test(event_anomalies: np.ndarray, control_anomalies: np.ndarray) -> Tuple[float, float]:
    """
    Perform two-sample Kolmogorov-Smirnov test.
    Returns (statistic, p_value).
    """
    from scipy import stats
    stat, p_val = stats.ks_2samp(event_anomalies, control_anomalies)
    return float(stat), float(p_val)

def perform_permutation_test(
    event_anomalies: np.ndarray,
    control_anomalies: np.ndarray,
    n_iterations: int = 1000,
    random_seed: Optional[int] = None
) -> np.ndarray:
    """
    Perform permutation test to generate null distribution of the test statistic.
    Returns array of permuted statistics.
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    combined = np.concatenate([event_anomalies, control_anomalies])
    n_event = len(event_anomalies)
    n_control = len(control_anomalies)
    
    observed_stat = np.abs(np.mean(event_anomalies) - np.mean(control_anomalies))
    
    null_stats = np.zeros(n_iterations)
    
    for i in range(n_iterations):
        np.random.shuffle(combined)
        perm_event = combined[:n_event]
        perm_control = combined[n_event:]
        null_stats[i] = np.abs(np.mean(perm_event) - np.mean(perm_control))
    
    return null_stats

def calculate_p_value_permutation(observed_stat: float, null_stats: np.ndarray) -> float:
    """
    Calculate p-value by comparing observed statistic to the 95th percentile of the null distribution.
    """
    # P-value is the proportion of null stats >= observed stat
    p_val = np.mean(null_stats >= observed_stat)
    return float(p_val)

def calculate_cohen_d(event_anomalies: np.ndarray, control_anomalies: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size.
    """
    mean1 = np.mean(event_anomalies)
    mean2 = np.mean(control_anomalies)
    std1 = np.std(event_anomalies, ddof=1)
    std2 = np.std(control_anomalies, ddof=1)
    
    # Pooled standard deviation
    n1 = len(event_anomalies)
    n2 = len(control_anomalies)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return float((mean1 - mean2) / pooled_std)

# --- Stratification Helpers ---

def is_pacific_ring_of_fire(lat: float, lon: float) -> bool:
    """
    Simple heuristic to check if a location is in the Pacific Ring of Fire.
    This is a simplified bounding box approach for demonstration.
    """
    # Rough approximation of the Ring of Fire
    # This is a simplified check; a real implementation would use a shapefile or more complex logic
    if lat < 0:
        return False  # Simplified: mostly Northern Hemisphere for this heuristic
    
    # Check if it's around the Pacific rim
    # West Coast Americas
    if 10 < lat < 60 and -130 < lon < -60:
        return True
    # Asia/East Asia
    if 20 < lat < 60 and 120 < lon < 150:
        return True
    # Japan/Kurils
    if 30 < lat < 55 and 130 < lon < 145:
        return True
    # New Zealand
    if -50 < lat < -35 and 165 < lon < 180:
        return True
    
    return False

def stratify_by_magnitude(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Stratify dataset by magnitude thresholds."""
    return {
        "m4_0_5_0": df[(df['magnitude'] >= 4.0) & (df['magnitude'] <= 5.0)],
        "m_gt_5_0": df[df['magnitude'] > 5.0]
    }

def stratify_by_region(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Stratify dataset by geographic region."""
    df['is_ring'] = df.apply(lambda row: is_pacific_ring_of_fire(row['lat'], row['lon']), axis=1)
    return {
        "ring_of_fire": df[df['is_ring']],
        "other": df[~df['is_ring']]
    }

def stratify_control_windows(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Stratify control windows by matching month/day across non-event years."""
    # Implementation for stratifying control windows
    # For now, return the full dataframe as a single group
    return {"all_controls": df}

# --- Robustness and Sensitivity ---

def run_robustness_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Run robustness checks across magnitude and region strata."""
    results = {}
    
    # Magnitude stratification
    mag_strata = stratify_by_magnitude(df)
    for name, subset in mag_strata.items():
        if len(subset) < 2:
            continue
        event_anom = subset[subset['is_event'] == 1]['pressure_anomaly'].values
        control_anom = subset[subset['is_event'] == 0]['pressure_anomaly'].values
        if len(event_anom) == 0 or len(control_anom) == 0:
            continue
        
        stat, p_val = perform_ks_test(event_anom, control_anom)
        d = calculate_cohen_d(event_anom, control_anom)
        results[f"ks_magnitude_{name}"] = {"stat": stat, "p_value": p_val, "effect_size": d}
    
    # Region stratification
    reg_strata = stratify_by_region(df)
    for name, subset in reg_strata.items():
        if len(subset) < 2:
            continue
        event_anom = subset[subset['is_event'] == 1]['pressure_anomaly'].values
        control_anom = subset[subset['is_event'] == 0]['pressure_anomaly'].values
        if len(event_anom) == 0 or len(control_anom) == 0:
            continue
        
        stat, p_val = perform_ks_test(event_anom, control_anom)
        d = calculate_cohen_d(event_anom, control_anom)
        results[f"ks_region_{name}"] = {"stat": stat, "p_value": p_val, "effect_size": d}
    
    return results

def run_sensitivity_analysis(df: pd.DataFrame, cutoffs: List[float]) -> Dict[str, Any]:
    """Run sensitivity analysis over different anomaly cutoffs."""
    results = {}
    for cutoff in cutoffs:
        # Filter based on cutoff (example logic)
        subset = df[df['pressure_anomaly'].abs() > cutoff]
        if len(subset) < 2:
            results[f"sensitivity_cutoff_{cutoff}"] = {"error": "insufficient_data"}
            continue
        
        event_anom = subset[subset['is_event'] == 1]['pressure_anomaly'].values
        control_anom = subset[subset['is_event'] == 0]['pressure_anomaly'].values
        if len(event_anom) == 0 or len(control_anom) == 0:
            results[f"sensitivity_cutoff_{cutoff}"] = {"error": "no_events_or_controls"}
            continue
        
        stat, p_val = perform_ks_test(event_anom, control_anom)
        d = calculate_cohen_d(event_anom, control_anom)
        results[f"sensitivity_cutoff_{cutoff}"] = {"stat": stat, "p_value": p_val, "effect_size": d}
    
    return results

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Benjamini-Hochberg False Discovery Rate correction.
    Returns list of booleans indicating which hypotheses are rejected.
    """
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    ranks = np.arange(1, n + 1)
    threshold = (ranks / n) * alpha
    
    rejected = np.zeros(n, dtype=bool)
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= threshold[i]:
            rejected[i:] = True
            break
    
    # Reorder to original indices
    final_rejected = np.zeros(n, dtype=bool)
    final_rejected[sorted_indices] = rejected
    return final_rejected.tolist()

def apply_fdr_correction(results_dict: Dict[str, Any], alpha: float = 0.05) -> Dict[str, Any]:
    """Apply FDR correction to a dictionary of results containing p-values."""
    p_vals = []
    keys = []
    for k, v in results_dict.items():
        if 'p_value' in v:
            p_vals.append(v['p_value'])
            keys.append(k)
    
    if not p_vals:
        return results_dict
    
    significant = benjamini_hochberg_fdr(p_vals, alpha)
    
    for i, k in enumerate(keys):
        results_dict[k]['is_significant_after_fdr'] = significant[i]
    
    return results_dict

# --- Interpretation and Reporting ---

def interpret_effect_size(d: float) -> str:
    """Interpret Cohen's d effect size."""
    abs_d = abs(d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def generate_conclusion(p_value: float, effect_size: float) -> str:
    """Generate a textual conclusion based on p-value and effect size."""
    sig = "significant" if p_value < 0.05 else "not significant"
    eff_interpretation = interpret_effect_size(effect_size)
    return f"Result is {sig} (p={p_value:.4f}) with {eff_interpretation} effect size (d={effect_size:.4f})."

def save_results(results: Dict[str, Any], output_path: Path):
    """Save results to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

# --- Main Execution ---

def run_analysis() -> Dict[str, Any]:
    """Main function to run the full analysis pipeline."""
    df = load_master_dataset()
    
    # Filter for events and controls
    event_data = df[df['is_event'] == 1]['pressure_anomaly'].values
    control_data = df[df['is_event'] == 0]['pressure_anomaly'].values
    
    if len(event_data) == 0 or len(control_data) == 0:
        logger.error("No event or control data found.")
        return {}
    
    # KS Test
    ks_stat, ks_p = perform_ks_test(event_data, control_data)
    
    # Permutation Test
    seed = get_random_seed()
    null_dist = perform_permutation_test(event_data, control_data, n_iterations=1000, random_seed=seed)
    observed_stat = np.abs(np.mean(event_data) - np.mean(control_data))
    perm_p = calculate_p_value_permutation(observed_stat, null_dist)
    
    # Effect Size
    cohens_d = calculate_cohen_d(event_data, control_data)
    
    results = {
        "ks_test": {"statistic": ks_stat, "p_value": ks_p},
        "permutation_test": {"observed_statistic": observed_stat, "p_value": perm_p},
        "effect_size": {"cohens_d": cohens_d, "interpretation": interpret_effect_size(cohens_d)},
        "conclusion": generate_conclusion(perm_p, cohens_d)
    }
    
    # Robustness
    robust_results = run_robustness_analysis(df)
    results["robustness"] = robust_results
    
    # Sensitivity
    sensitivity_results = run_sensitivity_analysis(df, cutoffs=[0.5, 1.0, 1.5])
    results["sensitivity"] = sensitivity_results
    
    # FDR Correction
    apply_fdr_correction(results["robustness"])
    apply_fdr_correction(results["sensitivity"])
    
    return results

def main():
    """Entry point for the analysis script."""
    logger.info("Starting analysis pipeline.")
    results = run_analysis()
    
    output_path = get_processed_path() / "statistical_results.json"
    save_results(results, output_path)
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()