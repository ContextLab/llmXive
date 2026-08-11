import json
import logging
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from scipy import stats
from scipy.stats import ks_2samp

# Import local utilities
from utils.simulation import RNGWrapper
from utils.exceptions import HighDimensionalInstabilityError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_seed_map(seed_map_path: str) -> Dict[str, List[int]]:
    """Load the seed map from JSON file."""
    path = Path(seed_map_path)
    if not path.exists():
        raise FileNotFoundError(f"Seed map not found at {seed_map_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    # Convert keys from string tuples back to tuples if necessary
    # The file stores keys as strings like "(n, p, rho, dist)"
    return data

def load_params(params_path: str) -> List[Dict[str, Any]]:
    """Load parameter sweep CSV into a list of dicts."""
    import csv
    path = Path(params_path)
    if not path.exists():
        raise FileNotFoundError(f"Params file not found at {params_path}")
    
    params_list = []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert types
            row['n'] = int(row['n'])
            row['p'] = int(row['p'])
            row['rho'] = float(row['rho'])
            row['seed'] = int(row['seed'])
            row['iteration'] = int(row['iteration'])
            params_list.append(row)
    
    return params_list

def generate_correlated_data_with_rng(
    n: int, 
    p: int, 
    rho: float, 
    distribution_type: str, 
    rng: np.random.Generator
) -> np.ndarray:
    """
    Generate a high-dimensional dataset with controlled correlation using a provided RNG.
    
    Args:
        n: Number of samples
        p: Number of features
        rho: Correlation coefficient
        distribution_type: 'normal', 't', or 'skew_normal'
        rng: A numpy random Generator instance (not the global state)
    
    Returns:
        np.ndarray of shape (n, p)
    """
    # 1. Generate base independent variables
    if distribution_type == 'normal':
        Z = rng.standard_normal(size=(n, p))
    elif distribution_type == 't':
        # Low degrees of freedom for heavy tails
        Z = rng.standard_t(df=3, size=(n, p))
    elif distribution_type == 'skew_normal':
        # Skew normal approximation
        Z = rng.standard_normal(size=(n, p))
        # Apply skew: X = Z + skew * |Z| (simplified)
        Z = Z + 1.5 * np.abs(Z)
    else:
        raise ValueError(f"Unknown distribution type: {distribution_type}")
    
    # 2. Construct correlation matrix (simple AR(1) or constant correlation)
    # For efficiency in high dimensions, we use a low-rank approximation or 
    # a specific structure. Here we use a constant correlation structure:
    # Sigma = (1-rho)I + rho*J
    # We can generate this by: X = sqrt(1-rho)*Z_ind + sqrt(rho)*Z_common
    if p > 1 and rho > 0:
        # Common factor
        common = rng.standard_normal(size=(n, 1))
        # Ensure rho is within valid range for this construction
        safe_rho = max(0.0, min(rho, 0.99)) 
        Z = np.sqrt(1 - safe_rho) * Z + np.sqrt(safe_rho) * common
    
    return Z

def generate_permutation_reference(
    data: np.ndarray, 
    n_permutations: int = 1000, 
    rng: np.random.Generator = None
) -> np.ndarray:
    """
    Generate a permutation-based Gold Standard p-value distribution.
    
    This breaks the null hypothesis structure while preserving the correlation
    structure of the original data by permuting rows (samples).
    
    Args:
        data: Input data matrix (n, p)
        n_permutations: Number of permutations to run
        rng: Random generator for reproducibility
    
    Returns:
        Array of p-values from the permutation tests.
    """
    if rng is None:
        rng = np.random.default_rng()
    
    n, p = data.shape
    pvalues = np.zeros(n_permutations)
    
    # Standard test statistic calculation (t-test on mean = 0 vs != 0)
    # We will compare the observed t-stat to the permuted t-stats
    
    # Calculate observed t-statistic for each feature
    # H0: mean = 0
    means = np.mean(data, axis=0)
    stds = np.std(data, axis=0, ddof=1)
    # Avoid division by zero
    stds[stds == 0] = 1e-10
    t_obs = means * np.sqrt(n) / stds
    
    # Permutation loop
    for i in range(n_permutations):
        # Shuffle rows
        perm_indices = rng.permutation(n)
        perm_data = data[perm_indices, :]
        
        # Calculate t-stat for permuted data
        perm_means = np.mean(perm_data, axis=0)
        perm_stds = np.std(perm_data, axis=0, ddof=1)
        perm_stds[perm_stds == 0] = 1e-10
        t_perm = perm_means * np.sqrt(n) / perm_stds
        
        # Two-sided p-value: proportion of |t_perm| >= |t_obs|
        # Note: In a true permutation test for p-value distribution under H0,
        # we usually re-center or permute residuals. Here, since we are testing
        # the distribution of p-values under the null (where mean is truly 0),
        # permuting rows of a zero-mean matrix should yield a uniform distribution.
        # However, to simulate the "Gold Standard" that accounts for correlation,
        # we calculate the p-value for the *original* t_obs against the *permuted*
        # distribution of t-stats.
        
        # Actually, the task asks for the "permutation reference p-values".
        # This implies we want the distribution of p-values we would get if we
        # ran the test on permuted data.
        # Let's calculate the p-value for the observed t_obs relative to the 
        # distribution of t_perm? No, that's not right for a reference distribution.
        
        # Correct approach for "Gold Standard" in this context:
        # We want to see what p-values the standard test produces when the data
        # is permuted (breaking any real signal, but keeping correlation).
        # Since the data is generated under the null (mean=0), the standard test
        # p-values should be uniform. The permutation test is the "Gold Standard"
        # because it empirically estimates the null distribution given the correlation.
        
        # Let's calculate the p-value for the *permuted* t-stats assuming a standard normal?
        # No, the task says "permutation reference".
        # Let's interpret this as: For each feature, calculate the p-value using
        # the empirical distribution of permuted t-statistics.
        
        # For each feature j:
        # p_val[j] = (1 + count(|t_perm[:, j]| >= |t_obs[j]|)) / (1 + n_perm)
        # But t_obs is the original.
        
        # Let's re-read: "compare standard tests to the permutation reference".
        # Standard test: uses theoretical t-distribution.
        # Permutation reference: uses the empirical distribution of t-stats from permuted data.
        
        # So for the output, we want the p-values calculated via the permutation method.
        # Since we are under the null, t_obs ~ t_perm.
        # The p-value for feature j is the fraction of permuted t-stats (absolute) 
        # that are more extreme than the observed t-stat (absolute).
        
        abs_t_obs = np.abs(t_obs)
        abs_t_perm = np.abs(t_perm)
        
        # Vectorized count
        counts = np.sum(abs_t_perm >= abs_t_obs, axis=0)
        pvalues[i] = (1 + counts) / (1 + n_perm)
        
        # Wait, this gives one p-value per feature per permutation?
        # The task asks for "the full array of permutation reference p-values".
        # Usually, we aggregate this.
        # Let's store the p-values for the CURRENT permutation iteration for all features.
        # But the output format says "each entry must contain ... the full array of permutation reference p-values".
        # This likely means the array of p-values for all features in this iteration.
        
        # Actually, let's simplify: The "Gold Standard" is the distribution of p-values
        # obtained when we run the permutation test.
        # We will return the array of p-values for all features from the permutation test.
        # To be robust, we might average or just take one representative?
        # The prompt says "full array". So we return the array of p-values for all p features.
        
        # However, running a full permutation test for every feature in every iteration
        # is expensive.
        # Let's assume the "permutation reference p-values" are the p-values derived
        # from the permutation distribution for the current data.
        
        # Let's calculate the p-value for each feature based on the permutation distribution.
        # p_val = (1 + sum(|t_perm| >= |t_obs|)) / (1 + n_perm)
        # We already did this for one permutation step? No, we need the full distribution.
        
        # Re-think: We need to generate a distribution of t-stats under H0 via permutation.
        # Then calculate p-values.
        # Since we are in a loop, maybe we accumulate?
        # No, the function should return the result for the given data.
        
        # Let's do a single pass accumulation for efficiency?
        # Or just run the permutations and compute the final p-values.
        pass
    
    # Let's restart the logic for clarity and correctness.
    # We want the p-values for the features in `data` using the permutation method.
    # 1. Calculate observed t-stats.
    # 2. Generate distribution of t-stats under H0 by permuting rows N times.
    # 3. For each feature, count how many permuted t-stats are >= observed.
    
    # We need to store all permuted t-stats? That's memory heavy.
    # We can compute the p-value incrementally.
    
    # Re-initialize
    t_obs = np.abs(means * np.sqrt(n) / stds)
    p_vals = np.zeros(p)
    
    # We need to run permutations to build the null distribution
    # For each feature, p_val = (1 + count(|t_perm| >= t_obs)) / (1 + n_perm)
    # We can do this in a loop over permutations, updating counts.
    
    counts = np.zeros(p)
    for _ in range(n_permutations):
        perm_indices = rng.permutation(n)
        perm_data = data[perm_indices, :]
        perm_means = np.mean(perm_data, axis=0)
        perm_stds = np.std(perm_data, axis=0, ddof=1)
        perm_stds[perm_stds == 0] = 1e-10
        t_perm = np.abs(perm_means * np.sqrt(n) / perm_stds)
        
        counts += (t_perm >= t_obs)
    
    p_vals = (1 + counts) / (1 + n_permutations)
    return p_vals

def calculate_ks_statistic(observed_pvalues: np.ndarray, reference: np.ndarray = None) -> Tuple[float, np.ndarray]:
    """
    Calculate the KS statistic comparing observed p-values to Uniform(0,1).
    
    Args:
        observed_pvalues: Array of p-values from standard tests.
        reference: Optional array of permutation reference p-values. 
                   If provided, we might compare observed vs reference?
                   The task says "comparing standard tests to the permutation reference".
                   This implies KS(observed, uniform) AND KS(reference, uniform)?
                   Or KS(observed, reference)?
                   "comparing standard tests to the permutation reference" -> 
                   Usually we compare the distribution of standard p-values to the 
                   distribution of permutation p-values.
                   But permutation p-values should be uniform under H0.
                   So we compare standard p-values to Uniform(0,1).
                   And we store the permutation p-values as the "reference".
    
    Returns:
        KS statistic value.
    """
    # KS test against Uniform(0,1)
    ks_stat, _ = stats.kstest(observed_pvalues, 'uniform')
    return ks_stat

def run_analysis_on_iteration(
    params: Dict[str, Any],
    seed_map: Dict[str, List[int]],
    params_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run the full analysis for a single iteration.
    1. Load/Generate data.
    2. Run standard hypothesis tests.
    3. Run permutation reference.
    4. Calculate KS statistic.
    5. Return results.
    """
    seed = params['seed']
    n = params['n']
    p = params['p']
    rho = params['rho']
    dist_type = params['distribution_type']
    
    # Initialize RNG
    rng = RNGWrapper()
    rng.reset(seed)
    np_rng = rng.get_generator() # Get a numpy Generator instance
    
    # Generate data
    data = generate_correlated_data_with_rng(n, p, rho, dist_type, np_rng)
    
    # Standard Hypothesis Tests (t-test against mean=0)
    # We need p p-values.
    # Use scipy.stats.ttest_1samp
    from scipy import stats as scipy_stats
    t_stats, standard_pvalues = scipy_stats.ttest_1samp(data, popmean=0, axis=0)
    
    # Ensure no NaNs or Infs
    standard_pvalues = np.nan_to_num(standard_pvalues, nan=1.0, posinf=1.0, neginf=1.0)
    standard_pvalues = np.clip(standard_pvalues, 0, 1)
    
    # Generate Permutation Reference
    # Use a different seed for permutations to avoid bias? 
    # Or continue the stream? The task says "using the same seed map" for regeneration.
    # But for the permutation itself, we need internal randomness.
    # Let's use the same rng stream to be deterministic.
    perm_pvalues = generate_permutation_reference(data, n_permutations=100, rng=np_rng)
    
    # Calculate KS statistic for standard p-values against Uniform
    ks_stat = calculate_ks_statistic(standard_pvalues)
    
    return {
        'seed': seed,
        'n': n,
        'p': p,
        'rho': rho,
        'distribution_type': dist_type,
        'ks_statistic': ks_stat,
        'standard_pvalues': standard_pvalues.tolist(),
        'permutation_pvalues': perm_pvalues.tolist()
    }

def main():
    """Main entry point for T029."""
    logger.info("Starting KS Statistic Calculation (T029)")
    
    # Paths
    base_dir = Path(__file__).parent.parent
    seed_map_path = base_dir / 'data' / 'sweep' / 'seed_map.json'
    params_path = base_dir / 'data' / 'sweep' / 'params.csv'
    output_path = base_dir / 'data' / 'results' / 'ks_stats.json'
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load inputs
    try:
        seed_map = load_seed_map(str(seed_map_path))
        params_list = load_params(str(params_path))
    except FileNotFoundError as e:
        logger.error(f"Missing required input files: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(params_list)} parameter combinations.")
    
    results = []
    
    for params in params_list:
        try:
            logger.info(f"Processing seed={params['seed']}, n={params['n']}, p={params['p']}")
            result = run_analysis_on_iteration(params, seed_map, params_list)
            results.append(result)
            
            # Save intermediate results to avoid losing progress on long runs?
            # The task asks for a single JSON file at the end.
            # We can save periodically if needed, but for now, just append.
            
        except Exception as e:
            logger.error(f"Error processing seed {params['seed']}: {e}")
            # Continue or fail? Let's log and continue.
            continue
    
    # Write results
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results written to {output_path}")

if __name__ == '__main__':
    main()
