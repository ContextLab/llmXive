"""
Permutation testing for Ecological Correlation analysis.

Implements FR-007: Generate null distribution by permuting mean_alpha_power labels
across strata for exactly 1000 iterations.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import from project API
from config import get_project_root
from seed_manager import set_seed, get_seed, load_seed_config
from correlation_analysis import load_stratum_features, compute_spearman_correlations
from logging_config import get_analysis_logger, save_analysis_results

# Constants
DEFAULT_ITERATIONS = 1000
ALPHA = 0.05
OUTPUT_RESULTS_PATH = "artifacts/permutation_results.json"
OUTPUT_NULL_DISTRIBUTION_PATH = "artifacts/null_distribution.npy"

logger = get_analysis_logger(__name__)

def load_correlation_results() -> Dict:
    """Load the correlation results from T022."""
    results_path = Path(get_project_root()) / "artifacts/correlation_results.json"
    if not results_path.exists():
        raise FileNotFoundError(f"Correlation results not found at {results_path}. Run T022 first.")
    
    with open(results_path, 'r') as f:
        return json.load(f)

def load_stratum_data() -> pd.DataFrame:
    """Load stratum features required for permutation."""
    return load_stratum_features()

def run_permutation_test(
    stratum_data: pd.DataFrame,
    top_taxa: List[str],
    n_iterations: int = DEFAULT_ITERATIONS,
    seed: Optional[int] = None
) -> Tuple[np.ndarray, Dict]:
    """
    Run permutation test to generate null distribution.

    Args:
        stratum_data: DataFrame with stratum features including mean_alpha_power and clr_taxa.
        top_taxa: List of top taxa names to test.
        n_iterations: Number of permutation iterations (FR-007: 1000).
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (null_distribution, results_dict)
    """
    if seed is not None:
        set_seed(seed)
        logger.info(f"Permutation test initialized with seed: {seed}")
    
    # Extract observed data
    alpha_power = stratum_data['mean_alpha_power'].values
    n_strata = len(alpha_power)
    
    if n_strata < 3:
        raise ValueError(f"Insufficient strata ({n_strata}) for permutation testing. Need at least 3.")
    
    # Compute observed correlations
    observed_stats = {}
    max_abs_observed = 0.0
    
    for taxon in top_taxa:
        if taxon not in stratum_data.columns:
            logger.warning(f"Taxon {taxon} not found in stratum data, skipping.")
            continue
        
        taxa_abundance = stratum_data[taxon].values
        
        # Compute Spearman correlation
        if len(np.unique(alpha_power)) < 2 or len(np.unique(taxa_abundance)) < 2:
            logger.warning(f"Insufficient variance for {taxon}, skipping.")
            continue
        
        rho, p_val = compute_spearman_correlations(alpha_power, taxa_abundance)
        observed_stats[taxon] = {'rho': rho, 'p_value': p_val}
        
        if abs(rho) > max_abs_observed:
            max_abs_observed = abs(rho)
    
    if not observed_stats:
        raise ValueError("No valid correlations found for permutation testing.")
    
    logger.info(f"Observed max absolute rho: {max_abs_observed:.4f}")
    
    # Run permutation test
    null_distribution = np.zeros((n_iterations, len(top_taxa)))
    
    logger.info(f"Starting permutation test with {n_iterations} iterations...")
    
    for i in range(n_iterations):
        # Permute alpha_power labels
        permuted_alpha = np.random.permutation(alpha_power)
        
        # Compute correlations for permuted data
        for j, taxon in enumerate(top_taxa):
            if taxon not in stratum_data.columns:
                continue
            
            taxa_abundance = stratum_data[taxon].values
            
            if len(np.unique(permuted_alpha)) < 2 or len(np.unique(taxa_abundance)) < 2:
                null_distribution[i, j] = 0.0
                continue
            
            rho, _ = compute_spearman_correlations(permuted_alpha, taxa_abundance)
            null_distribution[i, j] = rho
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Completed {i + 1}/{n_iterations} iterations")
    
    # Compute p-values from null distribution
    results = {
        'observed_stats': observed_stats,
        'null_distribution': null_distribution.tolist(),
        'n_iterations': n_iterations,
        'n_strata': n_strata,
        'top_taxa': top_taxa
    }
    
    # Calculate significance thresholds (95th percentile)
    significance_threshold = np.percentile(np.abs(null_distribution), 95, axis=0)
    results['significance_thresholds'] = significance_threshold.tolist()
    
    # Determine if permutation test passed
    # Passed if observed max |rho| exceeds 95th percentile of null max |rho|
    max_null = np.max(np.abs(null_distribution), axis=1)
    threshold_95 = np.percentile(max_null, 95)
    perm_test_passed = max_abs_observed > threshold_95
    
    results['perm_test_passed'] = perm_test_passed
    results['observed_max_rho'] = max_abs_observed
    results['null_95th_percentile'] = float(threshold_95)
    
    logger.info(f"Permutation test {'PASSED' if perm_test_passed else 'FAILED'}")
    logger.info(f"95th percentile of null max |rho|: {threshold_95:.4f}")
    
    return null_distribution, results

def save_results(results: Dict, null_distribution: np.ndarray):
    """Save permutation test results to artifacts."""
    project_root = get_project_root()
    
    # Save JSON results
    results_path = Path(project_root) / OUTPUT_RESULTS_PATH
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved permutation results to {results_path}")
    
    # Save null distribution
    null_path = Path(project_root) / OUTPUT_NULL_DISTRIBUTION_PATH
    np.save(null_path, null_distribution)
    logger.info(f"Saved null distribution to {null_path}")

def main():
    """Main entry point for permutation testing."""
    try:
        # Load configuration
        seed_config = load_seed_config()
        seed = seed_config.get('seed', 42)
        
        logger.info("Starting permutation test (T024)")
        
        # Load required data
        stratum_data = load_stratum_data()
        correlation_results = load_correlation_results()
        
        # Extract top taxa from correlation results
        if 'top_taxa' in correlation_results:
            top_taxa = correlation_results['top_taxa']
        elif 'significant_taxa' in correlation_results:
            top_taxa = correlation_results['significant_taxa']
        else:
            # Default to top 20 from microbiome features
            microbiome_path = Path(get_project_root()) / "data/processed/microbiome_features.csv"
            if microbiome_path.exists():
                micro_data = pd.read_csv(microbiome_path)
                taxon_cols = [col for col in micro_data.columns if col.startswith('taxon_')]
                top_taxa = sorted(taxon_cols)[:20]
            else:
                raise FileNotFoundError("Cannot determine top taxa. Run T022 first.")
        
        logger.info(f"Testing {len(top_taxa)} taxa: {top_taxa}")
        
        # Run permutation test
        null_dist, results = run_permutation_test(
            stratum_data=stratum_data,
            top_taxa=top_taxa,
            n_iterations=DEFAULT_ITERATIONS,
            seed=seed
        )
        
        # Save results
        save_results(results, null_dist)
        
        # Update main analysis results
        analysis_results_path = Path(get_project_root()) / "artifacts/analysis_results.json"
        if analysis_results_path.exists():
            with open(analysis_results_path, 'r') as f:
                analysis_results = json.load(f)
            
            analysis_results['permutation_test'] = {
                'passed': results['perm_test_passed'],
                'observed_max_rho': results['observed_max_rho'],
                'null_95th_percentile': results['null_95th_percentile'],
                'n_iterations': results['n_iterations']
            }
            
            with open(analysis_results_path, 'w') as f:
                json.dump(analysis_results, f, indent=2)
            logger.info("Updated analysis_results.json with permutation test results")
        
        logger.info("Permutation test completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Permutation test failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
