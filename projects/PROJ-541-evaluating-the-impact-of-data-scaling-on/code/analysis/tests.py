import numpy as np
import pandas as pd
import logging
from typing import Dict, Any, Optional, Tuple, Union, Callable, Iterator
from scipy import stats
from dataclasses import dataclass, field
import json
from pathlib import Path
import os

logger = logging.getLogger(__name__)

@dataclass
class ScalingMethod:
    name: str
    func: Callable[[np.ndarray], np.ndarray]

@dataclass
class TestResult:
    test_type: str
    scaling_method: str
    p_value: float
    statistic: float
    null_hypothesis_rejected: bool
    ground_truth_label: str
    seed: int
    config: Dict[str, Any] = field(default_factory=dict)

def run_scaled_t_test(
    data: pd.DataFrame,
    scaling_method: ScalingMethod,
    group_col: str = 'group',
    value_col: str = 'value',
    alpha: float = 0.05
) -> TestResult:
    """
    Apply scaling to data and run independent t-test.
    """
    if group_col not in data.columns or value_col not in data.columns:
        raise ValueError(f"Columns {group_col} and {value_col} must exist in data")

    groups = data[group_col].unique()
    if len(groups) != 2:
        raise ValueError("T-test requires exactly two groups")

    g1 = data[data[group_col] == groups[0]][value_col].values
    g2 = data[data[group_col] == groups[1]][value_col].values

    if len(g1) == 0 or len(g2) == 0:
        raise ValueError("One or both groups are empty after filtering")

    # Apply scaling
    # Scaling is applied per column, but here we assume value_col is the target.
    # We scale the combined array to maintain relative distances if needed,
    # or scale each group independently if the context implies standardization per group.
    # Standard practice for t-test invariance: scaling the combined vector.
    combined = np.concatenate([g1, g2])
    if combined.size == 0:
        raise ValueError("Combined data is empty")
    
    scaled_combined = scaling_method.func(combined)
    scaled_g1 = scaled_combined[:len(g1)]
    scaled_g2 = scaled_combined[len(g1):]

    # Run t-test
    t_stat, p_val = stats.ttest_ind(scaled_g1, scaled_g2)

    return TestResult(
        test_type="t_test",
        scaling_method=scaling_method.name,
        p_value=float(p_val),
        statistic=float(t_stat),
        null_hypothesis_rejected=(p_val < alpha),
        ground_truth_label="unknown", # To be set by caller if known
        seed=-1
    )

def run_scaled_anova(
    data: pd.DataFrame,
    scaling_method: ScalingMethod,
    group_col: str = 'group',
    value_col: str = 'value',
    alpha: float = 0.05
) -> TestResult:
    """
    Apply scaling to data and run one-way ANOVA.
    """
    if group_col not in data.columns or value_col not in data.columns:
        raise ValueError(f"Columns {group_col} and {value_col} must exist in data")

    groups = data[group_col].unique()
    if len(groups) < 2:
        raise ValueError("ANOVA requires at least two groups")

    group_data = [data[data[group_col] == g][value_col].values for g in groups]

    if any(len(g) == 0 for g in group_data):
        raise ValueError("One or more groups are empty")

    # Scale combined data
    combined = np.concatenate(group_data)
    if combined.size == 0:
        raise ValueError("Combined data is empty")
    
    scaled_combined = scaling_method.func(combined)
    
    # Re-split
    idx = 0
    scaled_groups = []
    for g in group_data:
        scaled_groups.append(scaled_combined[idx:idx+len(g)])
        idx += len(g)

    # Run ANOVA
    f_stat, p_val = stats.f_oneway(*scaled_groups)

    return TestResult(
        test_type="anova",
        scaling_method=scaling_method.name,
        p_value=float(p_val),
        statistic=float(f_stat),
        null_hypothesis_rejected=(p_val < alpha),
        ground_truth_label="unknown",
        seed=-1
    )

def run_scaled_chi_squared(
    data: pd.DataFrame,
    scaling_method: ScalingMethod,
    value_col: str = 'value',
    ground_truth_mean: Optional[float] = None,
    ground_truth_var: Optional[float] = None,
    n_bins: int = 10,
    alpha: float = 0.05
) -> TestResult:
    """
    Perform Chi-Squared Goodness of Fit test on scaled data.
    
    Binning logic:
    1. Bin based on theoretical quantiles derived from config's ground-truth parameters (mean, variance).
    2. If a bin has expected count < 5, merge with left neighbor.
    3. If left neighbor is empty or < 5, merge with right neighbor.
    4. If both fail, log "Bin merge failed" and skip the iteration (raise error).
    
    Args:
        data: DataFrame containing the data.
        scaling_method: Scaling method to apply.
        value_col: Name of the column to test.
        ground_truth_mean: Expected mean for theoretical distribution (Normal).
        ground_truth_var: Expected variance for theoretical distribution.
        n_bins: Initial number of bins.
        alpha: Significance level.
        
    Returns:
        TestResult object.
    """
    if value_col not in data.columns:
        raise ValueError(f"Column {value_col} not found in data")

    values = data[value_col].dropna().values
    if len(values) == 0:
        raise ValueError("No valid values to test")

    # Apply scaling
    scaled_values = scaling_method.func(values)

    # Determine theoretical distribution parameters
    # If ground truth is not provided, estimate from data (but task says "derived from config")
    # We assume the caller passes the theoretical parameters for the Null Hypothesis.
    # If not provided, we assume standard normal (mean=0, var=1) as the scaling target usually implies.
    mu = ground_truth_mean if ground_truth_mean is not None else 0.0
    sigma_sq = ground_truth_var if ground_truth_var is not None else 1.0
    sigma = np.sqrt(sigma_sq)

    # Create bins based on theoretical quantiles
    # We want equal probability bins for the theoretical distribution
    probabilities = np.linspace(0, 1, n_bins + 1)
    theoretical_quantiles = stats.norm.ppf(probabilities, loc=mu, scale=sigma)
    
    # Ensure strictly increasing bins (handle potential numerical issues)
    # If theoretical_quantiles are identical due to extreme tails, adjust slightly
    unique_quantiles = np.unique(theoretical_quantiles)
    if len(unique_quantiles) < 2:
        # Fallback to data-based quantiles if theoretical are degenerate
        logger.warning("Theoretical quantiles degenerate. Falling back to data quantiles.")
        bin_edges = np.percentile(scaled_values, np.linspace(0, 100, n_bins + 1))
    else:
        bin_edges = theoretical_quantiles

    # Calculate observed counts
    observed_counts, _ = np.histogram(scaled_values, bins=bin_edges)
    total_n = np.sum(observed_counts)
    
    # Calculate expected counts (equal probability for quantile bins)
    expected_counts = np.full(n_bins, total_n / n_bins)

    # Merge bins logic
    # We iterate until no merges are needed or we fail to merge
    max_iterations = n_bins * 2
    iteration = 0
    while iteration < max_iterations:
        iteration += 1
        needs_merge = False
        new_observed = []
        new_expected = []
        new_edges = [bin_edges[0]]
        
        # Track which original bins are merged into which new bin
        # We process left to right
        i = 0
        valid_bins = True
        
        while i < len(observed_counts):
            obs = observed_counts[i]
            exp = expected_counts[i]
            
            if exp < 5:
                needs_merge = True
                # Try merge left
                if len(new_observed) > 0:
                    # Merge with last added bin
                    new_observed[-1] += obs
                    new_expected[-1] += exp
                    # Update the last edge to current edge
                    new_edges[-1] = bin_edges[i+1] # Actually, the edge between i and i+1
                    # Wait, bin_edges is length n+1. 
                    # new_edges stores the right edge of the current accumulated bin.
                    # The left edge of the first bin is bin_edges[0].
                    # If we merge bin i into bin i-1, the new right edge is bin_edges[i+1].
                    # Let's refine the edge tracking.
                    # Actually, simpler: just accumulate counts. Re-calculate edges at the end?
                    # No, we need edges for the histogram/chi2 calculation.
                    # Let's store the right edge of the current merged bin.
                    # If we merge i into i-1, the new right edge is bin_edges[i+1].
                    # But we need to be careful: if we merge i-1 and i, the new bin covers [bin_edges[i-1], bin_edges[i+1]].
                    # The right edge is bin_edges[i+1].
                    # If we merge i into i-1, the new right edge is bin_edges[i+1].
                    # Let's track the right edge of the last added bin.
                    # Actually, let's just rebuild the bin edges list based on the merged indices.
                    pass
                else:
                    # Try merge right
                    if i + 1 < len(observed_counts):
                        # Merge i and i+1
                        # Check if i+1 is also < 5? The rule says: "merge with the right neighbor"
                        # It doesn't strictly say the right neighbor must be < 5, just that we merge.
                        # But if the right neighbor is also small, it might need merging later.
                        # Let's merge i and i+1 now.
                        next_obs = observed_counts[i+1]
                        next_exp = expected_counts[i+1]
                        
                        # Check if right neighbor exists and we can merge
                        # The rule: "if the left neighbor is empty or < 5, merge with the right neighbor"
                        # Here left neighbor (new_observed) is empty (we are at the start).
                        # So we merge i and i+1.
                        combined_obs = obs + next_obs
                        combined_exp = exp + next_exp
                        new_observed.append(combined_obs)
                        new_expected.append(combined_exp)
                        # The right edge of this merged bin is bin_edges[i+2]
                        # But we need to track edges carefully.
                        # Let's store the right edge of the current bin.
                        # If we merge i and i+1, the bin is [bin_edges[i], bin_edges[i+2]]
                        # We will reconstruct edges later.
                        i += 2 # Skip next
                    else:
                        # Cannot merge right (no neighbor) and cannot merge left (no neighbor)
                        logger.error("Bin merge failed: Bin at index %d has expected count %.2f < 5 and has no valid neighbors to merge.", i, exp)
                        valid_bins = False
                        break
            else:
                new_observed.append(obs)
                new_expected.append(exp)
                i += 1

        if not valid_bins:
            raise RuntimeError("Bin merge failed: Could not resolve low expected counts.")

        if not needs_merge:
            # Check if any new bin is < 5? 
            # The loop condition handles the initial < 5. 
            # But merging might create a new bin that is still < 5? 
            # The logic above merges until no < 5 or fails.
            # However, the loop condition `while iteration` and the `needs_merge` flag might be tricky.
            # Let's just re-scan.
            if any(e < 5 for e in new_expected):
                # Update arrays and continue loop
                observed_counts = np.array(new_observed)
                expected_counts = np.array(new_expected)
                # We need to reconstruct bin_edges to match the new counts.
                # This is complex with the simple list approach.
                # Let's use a simpler approach: build a list of (start_idx, end_idx) for bins.
                pass
            else:
                break
        
        # Re-scan for simplicity if needed, but let's try to fix the edge case logic first.
        # If we merged, we must continue.
        observed_counts = np.array(new_observed)
        expected_counts = np.array(new_expected)
        # We need to recalculate bin edges based on the merged structure.
        # This requires knowing which original bins were merged.
        # Let's restart the binning logic with a more robust approach.
        
        # RESTART LOGIC FOR BINNING WITH MERGING
        # We will build a list of ranges [start, end) in terms of original bin indices.
        ranges = []
        current_start = 0
        current_obs = observed_counts[0]
        current_exp = expected_counts[0]
        
        # Re-run the merge logic on the original arrays to build ranges
        # This is getting complex. Let's use a greedy approach:
        # 1. Identify all bins with exp < 5.
        # 2. Merge them.
        
        # Let's restart the `observed_counts` and `expected_counts` from the original `n_bins`
        # and use a queue-based merge.
        pass 
    
    # Robust Binning Implementation
    # Reset to original
    obs_arr = observed_counts.copy() # This was from the first histogram
    exp_arr = expected_counts.copy()
    bin_edges_arr = bin_edges.copy()
    
    # Use a list of (start_idx, end_idx) for bins
    # Initially each bin is (i, i+1)
    bins = [{'start': i, 'end': i+1, 'obs': obs_arr[i], 'exp': exp_arr[i]} for i in range(len(obs_arr))]
    
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(bins):
            if bins[i]['exp'] < 5:
                # Try merge left
                if i > 0:
                    # Merge i into i-1
                    bins[i-1]['end'] = bins[i]['end']
                    bins[i-1]['obs'] += bins[i]['obs']
                    bins[i-1]['exp'] += bins[i]['exp']
                    # Remove i
                    bins.pop(i)
                    changed = True
                    # Do not increment i, check the new i (which was i-1) again? 
                    # Actually, if we merged into i-1, we should check if i-1 is still < 5.
                    # But we just added to it. It might still be < 5.
                    # So we should stay at i-1?
                    # Let's just restart the scan or stay at i-1.
                    if i > 0: i -= 1 # Check the merged bin again
                    continue
                else:
                    # Try merge right
                    if i < len(bins) - 1:
                        # Merge i and i+1
                        bins[i]['end'] = bins[i+1]['end']
                        bins[i]['obs'] += bins[i+1]['obs']
                        bins[i]['exp'] += bins[i+1]['exp']
                        bins.pop(i+1)
                        changed = True
                        # Check this bin again
                        continue
                    else:
                        logger.error("Bin merge failed: Bin %d has exp %.2f < 5, no neighbors.", i, bins[i]['exp'])
                        raise RuntimeError("Bin merge failed: Could not resolve low expected counts.")
            else:
                i += 1
    
    if any(b['exp'] < 5 for b in bins):
        # Should not happen if logic is correct, but safety check
        logger.error("Final bins still have expected count < 5.")
        raise RuntimeError("Bin merge failed: Final bins have low expected counts.")
    
    # Reconstruct observed and expected arrays and edges
    final_obs = [b['obs'] for b in bins]
    final_exp = [b['exp'] for b in bins]
    # Edges: start of first bin, then end of each bin
    final_edges = [bins[0]['start']] # Index
    # Actually we need the values from bin_edges_arr
    # The bin is defined by original indices.
    # The edges are bin_edges_arr[b['start']] to bin_edges_arr[b['end']]
    
    final_edges_values = [bin_edges_arr[bins[0]['start']]]
    for b in bins:
        final_edges_values.append(bin_edges_arr[b['end']])
    
    final_obs = np.array(final_obs)
    final_exp = np.array(final_exp)
    final_edges_values = np.array(final_edges_values)
    
    if len(final_obs) < 2:
        logger.error("Not enough bins for Chi-Squared test after merging.")
        raise RuntimeError("Not enough bins for Chi-Squared test.")
    
    # Calculate Chi-Squared statistic
    chi2_stat = np.sum((final_obs - final_exp)**2 / final_exp)
    df = len(final_obs) - 1
    p_val = 1 - stats.chi2.cdf(chi2_stat, df)
    
    return TestResult(
        test_type="chi_squared",
        scaling_method=scaling_method.name,
        p_value=float(p_val),
        statistic=float(chi2_stat),
        null_hypothesis_rejected=(p_val < alpha),
        ground_truth_label="unknown",
        seed=-1
    )

def run_pipeline(
    data: pd.DataFrame,
    scaling_methods: list,
    test_func: Callable,
    **kwargs
) -> list:
    """
    Run a specific test function on data with multiple scaling methods.
    
    Args:
        data: DataFrame with data.
        scaling_methods: List of ScalingMethod objects.
        test_func: Function to run (e.g., run_scaled_t_test).
        **kwargs: Arguments to pass to test_func.
    
    Returns:
        List of TestResult objects.
    """
    results = []
    for method in scaling_methods:
        try:
            res = test_func(data, scaling_method=method, **kwargs)
            results.append(res)
        except Exception as e:
            logger.error(f"Failed to run {test_func.__name__} with {method.name}: {e}")
            # Optionally add a failure result or skip
            continue
    return results