import os
import sys
import json
import logging
import numpy as np
import pandas as pd

from utils import get_logger, safe_read_json, safe_write_json, PipelineError
from config import ensure_dirs

# Ensure logger is available
logger = get_logger()

def identify_significant_motifs(results):
    """
    Filter motifs with corrected p < 0.05 from the Bonferroni-corrected results.
    
    Args:
        results (dict): Dictionary containing correlation results with Bonferroni correction.
                        Expected schema: 
                        {
                            'motif_id': {
                                'r': float, 
                                'p_raw': float, 
                                'p_corrected': float, 
                                ...
                            },
                            ...
                        }
    
    Returns:
        list: List of motif_ids (strings) that have p_corrected < 0.05.
    
    Note:
        If no significant motifs are found, returns an empty list. The caller 
        (T032c) should handle the edge case of skipping the permutation test 
        if this list is empty.
    """
    if not results:
        logger.warning("No results provided to identify_significant_motifs.")
        return []

    significant_motifs = []
    threshold = 0.05

    for motif_id, metrics in results.items():
        # Skip metadata keys if any
        if not isinstance(metrics, dict):
            continue
        
        p_corrected = metrics.get('p_corrected')
        if p_corrected is None:
            logger.warning(f"Missing 'p_corrected' for motif {motif_id}, skipping.")
            continue

        if p_corrected < threshold:
            significant_motifs.append(motif_id)
            logger.info(f"Motif {motif_id} is significant (p_corrected={p_corrected:.4f} < {threshold}).")
        else:
            logger.debug(f"Motif {motif_id} is not significant (p_corrected={p_corrected:.4f}).")

    logger.info(f"Identified {len(significant_motifs)} significant motifs out of {len(results)}.")
    return significant_motifs

def run_permutation_test(motif_data, n_perm=1000):
    """
    Run a permutation test for a single significant motif to assess the 
    significance of the observed correlation against the null hypothesis 
    of no correlation.
    
    Null Hypothesis: There is no correlation between the motif z-score 
                     and the rsFC metric.
    Test Statistic:  Pearson correlation coefficient (r).
    
    Args:
        motif_data (dict): Dictionary containing the data for the motif.
                           Expected keys:
                           - 'motif_z_scores': list of float (z-scores across subjects)
                           - 'rsfc_values': list of float (rsFC values across subjects)
                           - 'observed_r': float (the original Pearson r from partial correlation)
        n_perm (int): Number of permutations to run (default 1000).
    
    Returns:
        dict: A dictionary containing the permutation test results:
              {
                  'motif_id': str,
                  'observed_r': float,
                  'empirical_p_value': float,
                  'n_permutations': int,
                  'null_distribution': list of float (optional, for debugging)
              }
    
    Raises:
        PipelineError: If the input data is missing required keys or has inconsistent lengths.
        ValueError: If n_perm is less than 1.
    """
    if n_perm < 1:
        raise ValueError("Number of permutations (n_perm) must be at least 1.")

    # Extract data
    z_scores = motif_data.get('motif_z_scores')
    rsfc_values = motif_data.get('rsfc_values')
    observed_r = motif_data.get('observed_r')
    motif_id = motif_data.get('motif_id', 'unknown')

    if z_scores is None or rsfc_values is None:
        raise PipelineError(f"Missing required data keys for motif {motif_id}. "
                            "Expected 'motif_z_scores' and 'rsfc_values'.")
    
    if observed_r is None:
        raise PipelineError(f"Missing 'observed_r' for motif {motif_id}.")

    # Convert to numpy arrays for efficient shuffling
    x = np.array(z_scores)
    y = np.array(rsfc_values)

    if len(x) != len(y):
        raise PipelineError(f"Data length mismatch for motif {motif_id}: "
                            f"z_scores ({len(x)}) vs rsfc_values ({len(y)}).")

    if len(x) < 2:
        # Cannot compute correlation with less than 2 points
        logger.warning(f"Insufficient data points ({len(x)}) for motif {motif_id}. "
                       "Returning p=1.0.")
        return {
            'motif_id': motif_id,
            'observed_r': observed_r,
            'empirical_p_value': 1.0,
            'n_permutations': n_perm,
            'null_distribution': []
        }

    # Calculate observed statistic (should match observed_r, but recompute for consistency)
    # Using numpy's corrcoef
    with np.errstate(all='ignore'):
        obs_corr = np.corrcoef(x, y)[0, 1]
        if np.isnan(obs_corr):
            obs_corr = 0.0 # Handle case of zero variance in one variable

    # Generate null distribution by shuffling y
    null_stats = np.zeros(n_perm)
    for i in range(n_perm):
        y_shuffled = np.random.permutation(y)
        with np.errstate(all='ignore'):
            r_shuffled = np.corrcoef(x, y_shuffled)[0, 1]
            if np.isnan(r_shuffled):
                r_shuffled = 0.0
        null_stats[i] = r_shuffled

    # Calculate empirical p-value (two-tailed test)
    # p = (count of |null_stat| >= |obs_stat| + 1) / (n_perm + 1)
    abs_obs = np.abs(obs_corr)
    abs_null = np.abs(null_stats)
    count_extreme = np.sum(abs_null >= abs_obs)
    p_value = (count_extreme + 1) / (n_perm + 1)

    logger.info(f"Permutation test for motif {motif_id}: "
                f"obs_r={obs_corr:.4f}, emp_p={p_value:.4f} ({n_perm} perms)")

    return {
        'motif_id': motif_id,
        'observed_r': float(obs_corr),
        'empirical_p_value': float(p_value),
        'n_permutations': n_perm,
        'null_distribution': null_stats.tolist() # Include for debugging/verification
    }

def main():
    """
    Main entry point for T032b.
    This function is designed to be called by T032c (the orchestrator).
    It reads the significant motifs list, loads the necessary data for each,
    and runs the permutation test.
    
    Note: This main() acts as a standalone runner for testing T032b in isolation
    if the data files exist, but its primary role is to be the function 
    implementation for the orchestrator.
    """
    ensure_dirs()
    
    # Paths for T032b execution (typically called by T032c, but runnable here for validation)
    significant_path = 'results/significant_motifs.json'
    metrics_path = 'data/processed/subject_metrics.csv'
    correlation_results_path = 'results/correlation_results.json'
    
    if not os.path.exists(significant_path):
        logger.error(f"Significant motifs file not found: {significant_path}. "
                     "Run T032a first.")
        return

    if not os.path.exists(metrics_path):
        logger.error(f"Subject metrics file not found: {metrics_path}. "
                     "Run T039 first.")
        return

    if not os.path.exists(correlation_results_path):
        logger.error(f"Correlation results file not found: {correlation_results_path}. "
                     "Run T030c first.")
        return

    try:
        # Load significant motifs
        sig_data = safe_read_json(significant_path)
        significant_motifs = sig_data.get('significant_motifs', [])
        
        if not significant_motifs:
            logger.info("No significant motifs found. Skipping permutation tests.")
            # Write empty results file to satisfy downstream tasks
            safe_write_json('results/permutation_results.json', {
                'permutations': [],
                'count': 0,
                'message': 'No significant motifs to test.'
            })
            return

        # Load correlation results to get observed_r
        corr_results = safe_read_json(correlation_results_path)
        
        # Load subject metrics to get z-scores and rsfc values
        df = pd.read_csv(metrics_path)
        
        # Ensure required columns exist
        required_cols = ['subject_id', 'rsfc_mean', 'network_density'] 
        # Note: motif z-scores are stored in separate columns or we need to reconstruct
        # Based on T039 logic, motif z-scores are likely in columns like 'motif_123_z'
        # We will assume the CSV has columns named 'motif_{id}_z' for z-scores
        # and 'rsfc_mean' for the rsFC metric.
        
        permutation_results = []
        
        for motif_id in significant_motifs:
            logger.info(f"Running permutation test for motif: {motif_id}")
            
            # Check if motif exists in correlation results
            if motif_id not in corr_results:
                logger.warning(f"Motif {motif_id} not found in correlation results, skipping.")
                continue
            
            motif_corr_data = corr_results[motif_id]
            observed_r = motif_corr_data.get('r')
            
            # Construct column name for z-scores
            z_col_name = f'motif_{motif_id}_z'
            
            if z_col_name not in df.columns:
                logger.error(f"Column '{z_col_name}' not found in subject_metrics.csv. "
                             f"Available columns: {list(df.columns)}")
                raise PipelineError(f"Missing z-score column for motif {motif_id}")
            
            z_scores = df[z_col_name].dropna().tolist()
            rsfc_values = df['rsfc_mean'].dropna().tolist()
            
            # Align indices (dropna returns different indices, need to sync)
            # Re-load and filter by valid indices
            valid_idx = df[z_col_name].notna() & df['rsfc_mean'].notna()
            z_scores = df.loc[valid_idx, z_col_name].tolist()
            rsfc_values = df.loc[valid_idx, 'rsfc_mean'].tolist()
            
            if len(z_scores) != len(rsfc_values):
                logger.error(f"Data alignment failed for {motif_id}.")
                continue

            motif_input_data = {
                'motif_id': motif_id,
                'motif_z_scores': z_scores,
                'rsfc_values': rsfc_values,
                'observed_r': observed_r
            }
            
            result = run_permutation_test(motif_input_data, n_perm=1000)
            permutation_results.append(result)
            
        # Save results
        output_data = {
            'permutations': permutation_results,
            'total_tested': len(permutation_results),
            'n_permutations': 1000
        }
        
        safe_write_json('results/permutation_results.json', output_data)
        logger.info(f"Saved permutation results to results/permutation_results.json")
        
    except Exception as e:
        logger.error(f"Error in main permutation test execution: {e}")
        raise

if __name__ == "__main__":
    main()