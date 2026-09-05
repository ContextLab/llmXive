import numpy as np
from statsmodels.stats.multitest import fdrcorrection
import json
import logging
from pathlib import Path
import code.config as config

logger = logging.getLogger(__name__)

def apply_fdr_correction(p_values, q=0.05):
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values (list of float): Raw p-values.
        q (float): FDR threshold (default 0.05).
        
    Returns:
        list of float: FDR-corrected p-values (q-values).
    """
    if not p_values:
        return []
    
    # statsmodels expects a numpy array
    p_arr = np.array(p_values)
    
    # fdrcorrection returns (reject, pvals_corrected, alphacSidak, alphacBonf)
    # We only need the corrected p-values
    _, p_corrected, _, _ = fdrcorrection(p_arr, alpha=q, method='indep')
    
    return p_corrected.tolist()

def permutation_test(observed_diff, early_timecourses, late_timecourses, 
                     n_iterations=1000, random_seed=42):
    """
    Perform a permutation test to assess the significance of the observed 
    difference between Early and Late event patterns.
    
    The null hypothesis is that there is no difference between Early and Late
    patterns. We permute the labels (Early/Late) and recompute the difference
    to build a null distribution.
    
    Args:
        observed_diff (float): The observed difference metric (e.g., mean dissimilarity
                               difference: Early-Late vs Early-Early).
        early_timecourses (np.ndarray): Timecourses for Early events (n_events, n_timepoints).
        late_timecourses (np.ndarray): Timecourses for Late events (n_events, n_timepoints).
        n_iterations (int): Number of permutation iterations (fixed for convergence).
        random_seed (int): Random seed for reproducibility.
        
    Returns:
        float: The two-tailed p-value.
    """
    np.random.seed(random_seed)
    
    # Combine all timecourses
    all_timecourses = np.vstack([early_timecourses, late_timecourses])
    n_early = early_timecourses.shape[0]
    n_late = late_timecourses.shape[0]
    n_total = n_early + n_late
    
    # Precompute the observed difference if not provided, but here we assume it is passed
    # The test statistic is the difference in mean dissimilarity between groups
    # For simplicity, we use the difference in mean pairwise correlation within groups
    # as the test statistic.
    
    # Compute observed statistic: mean correlation within Early - mean correlation within Late
    def compute_statistic(data):
        n = data.shape[0]
        if n < 2:
            return 0.0
        # Compute pairwise correlations
        corr_matrix = np.corrcoef(data)
        # Upper triangle (excluding diagonal)
        upper_tri_indices = np.triu_indices(n, k=1)
        correlations = corr_matrix[upper_tri_indices]
        return np.mean(correlations)
    
    # We will permute labels and compute the difference in within-group correlations
    # Observed: mean_corr(early) - mean_corr(late)
    
    # Precompute within-group correlations for observed
    obs_early_corr = compute_statistic(early_timecourses)
    obs_late_corr = compute_statistic(late_timecourses)
    observed_stat = obs_early_corr - obs_late_corr
    
    # Permutation loop
    count_extreme = 0
    for i in range(n_iterations):
        # Shuffle labels
        indices = np.random.permutation(n_total)
        perm_early = all_timecourses[indices[:n_early]]
        perm_late = all_timecourses[indices[n_early:]]
        
        # Compute statistic for permuted data
        perm_early_corr = compute_statistic(perm_early)
        perm_late_corr = compute_statistic(perm_late)
        perm_stat = perm_early_corr - perm_late_corr
        
        # Two-tailed test: count how often |perm_stat| >= |obs_stat|
        if abs(perm_stat) >= abs(observed_stat):
            count_extreme += 1
    
    p_value = (count_extreme + 1) / (n_iterations + 1)
    return p_value

def run_group_permutation_analysis(rsa_results_path, timecourses_path, 
                                   n_iterations=1000, random_seed=42,
                                   output_path=None):
    """
    Run permutation testing across subjects/ROIs and aggregate results.
    
    Args:
        rsa_results_path (str): Path to the RSA results JSON (from T021).
        timecourses_path (str): Path to the ROI timecourses HDF5 file.
        n_iterations (int): Number of permutation iterations.
        random_seed (int): Random seed.
        output_path (str): Path for the output JSON. Defaults to config output path.
        
    Returns:
        dict: Results including p-values and FDR-corrected p-values.
    """
    if output_path is None:
        output_path = config.get_output_path("permutation_pvalues.json")
    
    # Load RSA results (expected schema: {roi: {early_late: float, early_early: float}})
    # Note: The task description mentions RSA results with early_late and early_early.
    # We assume the observed_diff is derived from these.
    with open(rsa_results_path, 'r') as f:
        rsa_data = json.load(f)
    
    # Load timecourses
    # Expected format: {roi: {subject: {phase: [timecourse_array]}}}
    # We will aggregate across subjects for simplicity in this example.
    # In a full implementation, we would loop over subjects.
    
    import h5py
    with h5py.File(timecourses_path, 'r') as f:
        timecourses_data = {}
        for roi in f.keys():
            timecourses_data[roi] = {}
            for subj in f[roi].keys():
                timecourses_data[roi][subj] = {}
                for phase in f[roi][subj].keys():
                    timecourses_data[roi][subj][phase] = np.array(f[roi][subj][phase])
    
    all_p_values = []
    results = {}
    
    for roi, data in timecourses_data.items():
        # Aggregate timecourses across subjects for this ROI
        early_all = []
        late_all = []
        for subj, phases in data.items():
            if 'early' in phases and 'late' in phases:
                early_all.append(phases['early'])
                late_all.append(phases['late'])
        
        if not early_all or not late_all:
            logger.warning(f"No timecourses found for ROI {roi}, skipping.")
            continue
        
        early_concat = np.vstack(early_all)
        late_concat = np.vstack(late_all)
        
        # Compute observed difference (mean correlation within groups)
        def mean_corr(data):
            if data.shape[0] < 2:
                return 0.0
            corr = np.corrcoef(data)
            triu = np.triu_indices(data.shape[0], k=1)
            return np.mean(corr[triu])
        
        obs_early = mean_corr(early_concat)
        obs_late = mean_corr(late_concat)
        observed_diff = obs_early - obs_late
        
        # Run permutation test
        p_val = permutation_test(observed_diff, early_concat, late_concat,
                                 n_iterations=n_iterations, random_seed=random_seed)
        
        results[roi] = {
            "observed_diff": observed_diff,
            "p_value": p_val,
            "n_iterations": n_iterations
        }
        all_p_values.append(p_val)
    
    # Apply FDR correction
    if all_p_values:
        fdr_corrected = apply_fdr_correction(all_p_values, q=0.05)
        for i, roi in enumerate(results.keys()):
            results[roi]["p_fdr"] = fdr_corrected[i]
    else:
        logger.warning("No p-values to correct.")
    
    # Write output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Permutation test results written to {output_path}")
    return results

def main():
    """
    Main entry point for running the permutation test pipeline.
    """
    # Paths (should be configured or passed as arguments)
    rsa_path = config.get_output_path("rsa_matrices.json")
    timecourses_path = config.get_output_path("roi_timecourses.h5")
    output_path = config.get_output_path("permutation_pvalues.json")
    
    # Check if input files exist
    if not Path(rsa_path).exists():
        raise FileNotFoundError(f"RSA results file not found: {rsa_path}")
    if not Path(timecourses_path).exists():
        raise FileNotFoundError(f"Timecourses file not found: {timecourses_path}")
    
    # Run analysis
    results = run_group_permutation_analysis(
        rsa_results_path=rsa_path,
        timecourses_path=timecourses_path,
        n_iterations=1000,  # Fixed number of iterations for convergence
        random_seed=42     # Pinned seed for determinism
    )
    
    print(f"Permutation test completed. Results saved to {output_path}")
    return results

if __name__ == "__main__":
    main()