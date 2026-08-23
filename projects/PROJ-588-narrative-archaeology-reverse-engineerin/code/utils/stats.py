import numpy as np
from statsmodels.stats.multitest import fdrcorrection
import json
import logging
from pathlib import Path
import code.config as config
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

def apply_fdr_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        alpha: Significance threshold (q-value).
        
    Returns:
        Tuple of (adjusted p-values, boolean list indicating significance).
    """
    if not p_values:
        return [], []
        
    try:
        reject, pvals_corrected, _, _ = fdrcorrection(np.array(p_values), alpha=alpha, method='indep')
        return pvals_corrected.tolist(), reject.tolist()
    except Exception as e:
        logger.error(f"FDR correction failed: {e}")
        # Return original p-values and False for all if correction fails
        return p_values, [False] * len(p_values)

def permutation_test(
    data_early: np.ndarray,
    data_late: np.ndarray,
    n_iterations: int = 1000,
    random_seed: Optional[int] = None
) -> float:
    """
    Perform a permutation test to compare Early vs Late event patterns.
    
    Computes the observed dissimilarity between Early and Late means,
    then builds a null distribution by shuffling labels.
    
    Args:
        data_early: Array of shape (n_samples_early, n_features) for Early events.
        data_late: Array of shape (n_samples_late, n_features) for Late events.
        n_iterations: Number of permutations (default 1000).
        random_seed: Random seed for reproducibility.
        
    Returns:
        Two-tailed p-value.
    """
    if random_seed is not None:
        np.random.seed(random_seed)
        
    if data_early.shape[0] < 2 or data_late.shape[0] < 2:
        logger.warning("Insufficient samples for permutation test. Returning p=1.0.")
        return 1.0
        
    # Observed statistic: distance between group means (Euclidean)
    mean_early = np.mean(data_early, axis=0)
    mean_late = np.mean(data_late, axis=0)
    observed_dist = np.linalg.norm(mean_early - mean_late)
    
    # Combine data
    combined = np.vstack([data_early, data_late])
    n_early = data_early.shape[0]
    n_total = combined.shape[0]
    
    # Permutation loop
    count_extreme = 0
    for i in range(n_iterations):
        # Shuffle indices
        perm_indices = np.random.permutation(n_total)
        shuffled_early = combined[perm_indices[:n_early]]
        shuffled_late = combined[perm_indices[n_early:]]
        
        # Compute permuted statistic
        perm_mean_early = np.mean(shuffled_early, axis=0)
        perm_mean_late = np.mean(shuffled_late, axis=0)
        perm_dist = np.linalg.norm(perm_mean_early - perm_mean_late)
        
        # Two-tailed: check if permuted dist is as extreme or more extreme
        if perm_dist >= observed_dist:
            count_extreme += 1
            
    p_value = (count_extreme + 1) / (n_iterations + 1)
    return p_value

def run_group_permutation_analysis(
    roi_data: Dict[str, Dict[str, np.ndarray]],
    n_iterations: int = 1000,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run permutation testing across multiple ROIs and phases.
    
    Args:
        roi_data: Dictionary mapping ROI names to dicts containing 'early' and 'late' arrays.
                 Structure: { 'roi_name': { 'early': np.ndarray, 'late': np.ndarray } }
        n_iterations: Number of permutations.
        output_path: Path to write results JSON.
        
    Returns:
        Dictionary with p-values and significance flags for each ROI.
    """
    results = {
        "n_iterations": n_iterations,
        "rois": {},
        "raw_p_values": [],
        "adj_p_values": [],
        "significant": []
    }
    
    p_values = []
    roi_names = sorted(roi_data.keys())
    
    logger.info(f"Running permutation test ({n_iterations} iterations) for {len(roi_names)} ROIs...")
    
    for roi_name in roi_names:
        data = roi_data[roi_name]
        if 'early' not in data or 'late' not in data:
            logger.warning(f"Skipping ROI {roi_name}: missing 'early' or 'late' data.")
            continue
            
        p_val = permutation_test(
            data['early'],
            data['late'],
            n_iterations=n_iterations,
            random_seed=config.get_config().get('random_seed', 42)
        )
        
        results["rois"][roi_name] = {
            "p_value": p_val,
            "significant_raw": p_val < 0.05
        }
        p_values.append(p_val)
        logger.info(f"ROI {roi_name}: p = {p_val:.4f}")
        
    # Apply FDR correction
    if p_values:
        adj_p, significant = apply_fdr_correction(p_values, alpha=0.05)
        results["adj_p_values"] = adj_p
        results["significant"] = significant
        
        # Update ROI results with corrected significance
        for i, roi_name in enumerate(roi_names):
            if roi_name in results["rois"]:
                results["rois"][roi_name]["adj_p_value"] = adj_p[i]
                results["rois"][roi_name]["significant_fdr"] = significant[i]
    else:
        logger.warning("No valid p-values computed for FDR correction.")
        
    # Write output if path provided
    if output_path:
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Permutation results written to {output_path}")
        
    return results

def main():
    """
    Main entry point for T022: Permutation testing and FDR correction.
    Loads ROI timecourses (mocked here for structure, assumes real data exists),
    runs permutation tests, applies FDR, and writes results.
    """
    # Load config
    cfg = config.get_config()
    output_path = config.get_output_path("permutation_pvalues.json")
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Load ROI data
    # Expected structure: data/processed/roi_timecourses.h5
    # This loader assumes the file exists from T013. 
    # If not, it will raise an error (fail loudly).
    try:
        import h5py
        h5_path = config.get_data_path("processed/roi_timecourses.h5")
        if not Path(h5_path).exists():
            raise FileNotFoundError(f"ROI timecourses file not found at {h5_path}")
            
        with h5py.File(h5_path, 'r') as f:
            roi_data = {}
            for roi_name in f.keys():
                group = f[roi_name]
                if 'early' in group and 'late' in group:
                    roi_data[roi_name] = {
                        'early': group['early'][()],
                        'late': group['late'][()]
                    }
                    logger.info(f"Loaded ROI {roi_name}: early={roi_data[roi_name]['early'].shape}, late={roi_data[roi_name]['late'].shape}")
    except FileNotFoundError as e:
        logger.error(f"CRITICAL: Required data missing. {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading ROI data: {e}")
        raise

    if not roi_data:
        raise ValueError("No ROI data loaded. Cannot proceed with permutation test.")

    # Run analysis
    results = run_group_permutation_analysis(
        roi_data,
        n_iterations=1000,
        output_path=output_path
    )
    
    print(f"Analysis complete. Results saved to {output_path}")
    return results

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
