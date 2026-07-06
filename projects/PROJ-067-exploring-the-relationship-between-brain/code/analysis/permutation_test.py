"""
Permutation test implementation for statistical significance of correlations.

This module implements a non-parametric permutation test to generate a null
distribution for the correlation coefficient between network metrics and
dream recall frequency.

FR-007: Implement permutation test with exactly 1000 iterations.
SC-003: Ensure robust statistical inference via permutation testing.
"""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from scipy.stats import rankdata

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.stats import load_metrics_and_dream_recall

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PERMUTATION_ITERATIONS = 1000
RANDOM_SEED = 42

def calculate_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate Spearman correlation coefficient between two arrays.
    
    Args:
        x: First array of values
        y: Second array of values
        
    Returns:
        Spearman correlation coefficient
    """
    if len(x) != len(y):
        raise ValueError(f"Array lengths must match: {len(x)} vs {len(y)}")
    
    # Handle constant arrays (edge case)
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    
    rho, _ = stats.spearmanr(x, y)
    return float(rho)

def run_permutation_test(
    x: np.ndarray,
    y: np.ndarray,
    n_iterations: int = PERMUTATION_ITERATIONS,
    seed: int = RANDOM_SEED
) -> Tuple[float, np.ndarray, float]:
    """
    Run a permutation test to assess the significance of the observed correlation.
    
    The test works by randomly shuffling the y-values (dream recall frequency)
    relative to the x-values (network metrics) many times, calculating the
    correlation for each shuffled dataset to build a null distribution.
    
    Args:
        x: Network metric values (independent variable)
        y: Dream recall frequency values (dependent variable)
        n_iterations: Number of permutation iterations (default: 1000)
        seed: Random seed for reproducibility
        
    Returns:
        Tuple containing:
            - observed_rho: The observed Spearman correlation coefficient
            - null_distribution: Array of correlation coefficients from permutations
            - permutation_p_value: Two-tailed p-value from the permutation test
    """
    if len(x) != len(y):
        raise ValueError(f"Input arrays must have the same length: {len(x)} vs {len(y)}")
    
    if len(x) < 5:
        raise ValueError(f"Insufficient samples for permutation test: {len(x)}")
    
    # Set random seed for reproducibility
    rng = np.random.default_rng(seed)
    
    # Calculate observed correlation
    observed_rho = calculate_correlation(x, y)
    logger.info(f"Observed Spearman correlation: {observed_rho:.4f}")
    
    # Generate null distribution
    null_distribution = np.zeros(n_iterations)
    
    logger.info(f"Running permutation test with {n_iterations} iterations...")
    
    for i in range(n_iterations):
        # Shuffle y values while keeping x fixed
        shuffled_y = rng.permutation(y)
        null_rho = calculate_correlation(x, shuffled_y)
        null_distribution[i] = null_rho
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Completed {i + 1}/{n_iterations} permutations")
    
    # Calculate two-tailed p-value
    # Count how many permuted correlations are as extreme or more extreme than observed
    # For two-tailed test, we consider both tails
    extreme_count = np.sum(np.abs(null_distribution) >= np.abs(observed_rho))
    permutation_p_value = (extreme_count + 1) / (n_iterations + 1)
    
    logger.info(f"Permutation test completed. P-value: {permutation_p_value:.4f}")
    logger.info(f"Null distribution: mean={np.mean(null_distribution):.4f}, "
               f"std={np.std(null_distribution):.4f}")
    
    return observed_rho, null_distribution, permutation_p_value

def run_permutation_tests_for_all_metrics(
    metrics: Dict[str, List[Dict[str, Any]]],
    dream_recall_values: Dict[str, float]
) -> Dict[str, Dict[str, Any]]:
    """
    Run permutation tests for all network metrics against dream recall frequency.
    
    Args:
        metrics: Dictionary mapping network names to lists of metric dictionaries
                (from load_metrics_and_dream_recall)
        dream_recall_values: Dictionary mapping subject IDs to dream recall frequency
        
    Returns:
        Dictionary containing results for each metric network:
            - observed_rho: Observed correlation coefficient
            - null_distribution: Array of permuted correlations
            - permutation_p_value: Permutation test p-value
            - n_iterations: Number of iterations performed
            - n_subjects: Number of subjects analyzed
    """
    results = {}
    
    # Identify which metrics are available (flexibility and stability for each network)
    # Expected networks: DMN, Salience, Hippocampal-Memory
    # Expected metric types: flexibility, stability
    
    # Extract metric names from the data
    metric_names = set()
    for network_name, subjects in metrics.items():
        if subjects:
            for key in subjects[0].keys():
                if key not in ['subject_id', 'dream_recall_frequency']:
                    metric_names.add(f"{network_name}_{key}")
    
    logger.info(f"Found {len(metric_names)} metric combinations to test: {metric_names}")
    
    for metric_name in metric_names:
        try:
            # Extract metric values and corresponding dream recall
            x_values = []
            y_values = []
            subject_ids = []
            
            for network_name, subjects in metrics.items():
                metric_type = metric_name.split('_')[-1]
                prefix = f"{network_name}_{metric_type}"
                
                for subject in subjects:
                    if prefix in subject and subject.get('dream_recall_frequency') is not None:
                        x_values.append(subject[prefix])
                        y_values.append(subject['dream_recall_frequency'])
                        subject_ids.append(subject['subject_id'])
            
            if len(x_values) < 5:
                logger.warning(f"Insufficient data for {metric_name}: {len(x_values)} subjects")
                results[metric_name] = {
                    'observed_rho': None,
                    'null_distribution': None,
                    'permutation_p_value': None,
                    'n_iterations': 0,
                    'n_subjects': len(x_values),
                    'error': 'Insufficient subjects'
                }
                continue
            
            x_array = np.array(x_values)
            y_array = np.array(y_values)
            
            # Run permutation test
            observed_rho, null_dist, p_value = run_permutation_test(
                x_array, y_array,
                n_iterations=PERMUTATION_ITERATIONS,
                seed=RANDOM_SEED
            )
            
            results[metric_name] = {
                'observed_rho': observed_rho,
                'null_distribution': null_dist.tolist(),  # Convert to list for JSON serialization
                'permutation_p_value': p_value,
                'n_iterations': PERMUTATION_ITERATIONS,
                'n_subjects': len(x_values),
                'subject_ids': subject_ids
            }
            
            logger.info(f"Completed {metric_name}: rho={observed_rho:.4f}, p={p_value:.4f}")
            
        except Exception as e:
            logger.error(f"Error processing {metric_name}: {str(e)}")
            results[metric_name] = {
                'observed_rho': None,
                'null_distribution': None,
                'permutation_p_value': None,
                'n_iterations': 0,
                'n_subjects': 0,
                'error': str(e)
            }
    
    return results

def save_results(results: Dict[str, Dict[str, Any]], output_path: str) -> None:
    """
    Save permutation test results to a JSON file.
    
    Args:
        results: Dictionary of test results
        output_path: Path to output JSON file
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare results for JSON serialization (convert numpy arrays to lists)
    serializable_results = {}
    for metric_name, metric_results in results.items():
        serializable_results[metric_name] = {
            k: (v.tolist() if isinstance(v, np.ndarray) else v)
            for k, v in metric_results.items()
        }
    
    with open(output_path, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")

def main() -> None:
    """
    Main entry point for running permutation tests.
    
    This function:
    1. Loads metrics and dream recall data
    2. Runs permutation tests for all metric networks
    3. Saves results to results/permutation_results.json
    """
    logger.info("Starting permutation test analysis (T040)")
    
    try:
        # Load data
        metrics, dream_recall_values = load_metrics_and_dream_recall()
        
        if not metrics:
            logger.error("No metrics data loaded. Cannot proceed with permutation test.")
            sys.exit(1)
        
        if not dream_recall_values:
            logger.error("No dream recall data loaded. Cannot proceed with permutation test.")
            sys.exit(1)
        
        logger.info(f"Loaded data for {len(dream_recall_values)} subjects")
        
        # Run permutation tests
        results = run_permutation_tests_for_all_metrics(metrics, dream_recall_values)
        
        # Save results
        output_path = str(Path(__file__).parent.parent.parent / "results" / "permutation_results.json")
        save_results(results, output_path)
        
        # Also update the main stats.json if it exists
        stats_path = str(Path(__file__).parent.parent.parent / "results" / "stats.json")
        if os.path.exists(stats_path):
            try:
                with open(stats_path, 'r') as f:
                    stats_data = json.load(f)
                
                # Add permutation results to stats data
                stats_data['permutation_tests'] = {
                    k: {
                        'observed_rho': v.get('observed_rho'),
                        'permutation_p_value': v.get('permutation_p_value'),
                        'n_iterations': v.get('n_iterations'),
                        'n_subjects': v.get('n_subjects')
                    }
                    for k, v in results.items()
                    if v.get('observed_rho') is not None
                }
                
                with open(stats_path, 'w') as f:
                    json.dump(stats_data, f, indent=2)
                
                logger.info(f"Updated {stats_path} with permutation test results")
            except Exception as e:
                logger.warning(f"Could not update stats.json: {e}")
        
        logger.info("Permutation test analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Permutation test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
