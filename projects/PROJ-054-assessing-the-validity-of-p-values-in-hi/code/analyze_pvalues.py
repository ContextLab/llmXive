import logging
from typing import Dict, List, Tuple, Any, Optional, Union
import numpy as np
from scipy import stats
from utils.exceptions import AnalysisError

logger = logging.getLogger(__name__)

def generate_permutation_reference(
    data_group1: np.ndarray,
    data_group2: np.ndarray,
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Generate a reference distribution of p-values using permutation testing.
    
    This respects the actual correlation structure of the data by permuting
    group labels within each feature (column) independently, then re-running
    the t-test to build an empirical null distribution.
    
    Args:
        data_group1: Array of shape (n_samples1, p_features)
        data_group2: Array of shape (n_samples2, p_features)
        n_permutations: Number of permutation iterations
        seed: Random seed for reproducibility
        
    Returns:
        Array of shape (n_permutations, p_features) containing p-values
        for each permutation and feature.
    """
    if seed is not None:
        np.random.seed(seed)
        
    n1, p = data_group1.shape
    n2 = data_group2.shape[0]
    total_n = n1 + n2
    
    # Combine data
    combined = np.vstack([data_group1, data_group2])
    
    # Pre-allocate results
    perm_pvalues = np.zeros((n_permutations, p))
    
    logger.info(f"Generating permutation reference with {n_permutations} iterations for {p} features")
    
    for i in range(n_permutations):
        # Shuffle indices
        shuffled_indices = np.random.permutation(total_n)
        shuffled_data = combined[shuffled_indices]
        
        # Split back
        perm_group1 = shuffled_data[:n1]
        perm_group2 = shuffled_data[n1:]
        
        # Run t-test for each feature
        # scipy.stats.ttest_ind returns statistic and p-value arrays
        _, pvals = stats.ttest_ind(perm_group1, perm_group2, axis=0, equal_var=False)
        
        # Handle potential NaNs if variance is zero
        pvals = np.nan_to_num(pvals, nan=1.0)
        perm_pvalues[i, :] = pvals
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Permutation {i+1}/{n_permutations} completed")
    
    return perm_pvalues

def calculate_ks_statistic(
    observed_pvalues: Union[np.ndarray, List[float]],
    reference_pvalues: Optional[Union[np.ndarray, List[float]]] = None,
    reference_type: str = 'uniform'
) -> Dict[str, float]:
    """
    Calculate the Kolmogorov-Smirnov statistic comparing observed p-values
    against a reference distribution.
    
    Args:
        observed_pvalues: Array of observed p-values from standard tests
        reference_pvalues: Optional array of reference p-values (e.g., from permutation test)
        reference_type: Either 'uniform' (theoretical null) or 'permutation' (empirical null)
        
    Returns:
        Dictionary containing:
            - 'KS_statistic': The maximum distance between CDFs
            - 'p_value': The p-value of the KS test (only meaningful for uniform reference)
            - 'reference_type': Type of reference used
            - 'n_observed': Number of observed p-values
            - 'mean_observed': Mean of observed p-values
            - 'min_observed': Minimum observed p-value
            - 'max_observed': Maximum observed p-value
    """
    observed = np.asarray(observed_pvalues).flatten()
    
    # Filter out NaNs and infinities
    valid_mask = np.isfinite(observed)
    observed = observed[valid_mask]
    
    if len(observed) == 0:
        raise AnalysisError("No valid p-values found in observed data")
    
    result = {
        'n_observed': len(observed),
        'mean_observed': float(np.mean(observed)),
        'min_observed': float(np.min(observed)),
        'max_observed': float(np.max(observed)),
        'reference_type': reference_type
    }
    
    if reference_type == 'uniform':
        # Compare against theoretical uniform distribution [0, 1]
        # For uniform reference, we use scipy's kstest with cdf='uniform'
        ks_stat, p_val = stats.kstest(observed, 'uniform')
        
        result['KS_statistic'] = float(ks_stat)
        result['p_value'] = float(p_val)
        
        logger.info(
            f"KS test vs Uniform: KS={ks_stat:.4f}, p={p_val:.4f}, "
            f"n={len(observed)}, mean={np.mean(observed):.4f}"
        )
        
    elif reference_type == 'permutation':
        if reference_pvalues is None:
            raise AnalysisError(
                "reference_pvalues must be provided when reference_type='permutation'"
            )
        
        reference = np.asarray(reference_pvalues).flatten()
        valid_ref_mask = np.isfinite(reference)
        reference = reference[valid_ref_mask]
        
        if len(reference) == 0:
            raise AnalysisError("No valid p-values found in reference data")
        
        # Compare empirical CDF of observed vs empirical CDF of reference
        ks_stat, p_val = stats.ks_2samp(observed, reference)
        
        result['KS_statistic'] = float(ks_stat)
        result['p_value'] = float(p_val)
        
        logger.info(
            f"KS test vs Permutation: KS={ks_stat:.4f}, p={p_val:.4f}, "
            f"n_obs={len(observed)}, n_ref={len(reference)}, "
            f"mean_obs={np.mean(observed):.4f}, mean_ref={np.mean(reference):.4f}"
        )
        
    else:
        raise AnalysisError(
            f"Unknown reference_type: {reference_type}. "
            "Must be 'uniform' or 'permutation'."
        )
        
    return result

def main():
    """
    Main entry point for running KS statistic analysis.
    
    This function demonstrates the workflow:
    1. Generate permutation reference from sample data
    2. Calculate KS statistic comparing standard test p-values to reference
    3. Output results
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (in real scenario, data would come from T022/T026 outputs)
    logger.info("KS Statistic Analysis Module Ready")
    logger.info("Use calculate_ks_statistic() with observed and reference p-values")
    
    # Example: Create dummy data for demonstration
    np.random.seed(42)
    n_samples = 100
    n_features = 50
    
    dummy_group1 = np.random.randn(n_samples, n_features)
    dummy_group2 = np.random.randn(n_samples, n_features)
    
    # Generate permutation reference
    perm_refs = generate_permutation_reference(
        dummy_group1, dummy_group2, 
        n_permutations=100, 
        seed=42
    )
    
    # Flatten to single distribution for example
    perm_flat = perm_refs.flatten()
    
    # Generate some observed p-values (simulating standard t-tests on null data)
    observed_pvals = np.random.uniform(0, 1, n_features)
    
    # Calculate KS against permutation reference
    ks_result = calculate_ks_statistic(
        observed_pvals, 
        reference_pvalues=perm_flat,
        reference_type='permutation'
    )
    
    print("KS Analysis Results:")
    for key, value in ks_result.items():
        print(f"  {key}: {value}")
        
    return ks_result

if __name__ == "__main__":
    main()