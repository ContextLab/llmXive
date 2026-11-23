"""
T050 Implementation: Generate "Jagged Line" high-resolution histogram for the worst-case scenario.

This script loads the worst-case scenario identified in T049, regenerates the data
deterministically, runs the permutation test to establish the ground truth, and
generates a high-resolution histogram comparing the observed p-values (standard test)
against the theoretical uniform line.

Output: docs/plots/jagged_line_worst_case_detail.png
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.simulation import RNGWrapper
from utils.regularization import regularize_covariance, HighDimensionalInstabilityError
from scipy import stats
from scipy.stats import ttest_ind, f_oneway

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_worst_case_scenario() -> Dict[str, Any]:
    """Load the worst-case scenario from T049 output."""
    worst_case_path = project_root / "data" / "results" / "worst_case_summary.json"
    
    if not worst_case_path.exists():
        raise FileNotFoundError(
            f"Worst case summary not found at {worst_case_path}. "
            "Please ensure T049 has been completed successfully."
        )
    
    with open(worst_case_path, 'r') as f:
        return json.load(f)

def load_pvalues_for_seed(seed: int) -> np.ndarray:
    """Load p-values for a specific seed from the results."""
    pvalues_path = project_root / "data" / "results" / f"pvalues_{seed}.csv"
    
    if not pvalues_path.exists():
        raise FileNotFoundError(
            f"P-values file not found for seed {seed} at {pvalues_path}. "
            "Please ensure T022 has been completed successfully."
        )
    
    # Read p-values from CSV
    pvalues = []
    with open(pvalues_path, 'r') as f:
        # Skip header if present
        header = f.readline()
        if not header.startswith('pvalue'):
            f.seek(0)
        
        for line in f:
            line = line.strip()
            if line:
                try:
                    pvalues.append(float(line))
                except ValueError:
                    continue
    
    return np.array(pvalues)

def generate_correlated_data_with_rng(params: Dict[str, Any], rng_wrapper: RNGWrapper) -> np.ndarray:
    """
    Generate correlated data using the RNG wrapper for reproducibility.
    
    Args:
        params: Dictionary containing n, p, rho, distribution_type
        rng_wrapper: RNGWrapper instance for deterministic generation
        
    Returns:
        numpy array of shape (n, p)
    """
    n = params['n']
    p = params['p']
    rho = params['rho']
    dist_type = params['distribution_type']
    
    # Create correlation matrix
    # Using a simple AR(1) structure for correlation
    cov_matrix = np.zeros((p, p))
    for i in range(p):
        for j in range(p):
            cov_matrix[i, j] = rho ** abs(i - j)
    
    # Regularize if necessary
    try:
        cov_matrix = regularize_covariance(cov_matrix)
    except HighDimensionalInstabilityError as e:
        logger.warning(f"Regularization failed: {e}. Using identity matrix.")
        cov_matrix = np.eye(p)
    
    # Generate data
    if dist_type == 'normal':
        # Use Cholesky decomposition for correlated normal data
        try:
            L = np.linalg.cholesky(cov_matrix)
            Z = rng_wrapper.standard_normal((n, p))
            data = Z @ L.T
        except np.linalg.LinAlgError:
            # Fallback if Cholesky fails
            L = np.linalg.cholesky(cov_matrix + 1e-6 * np.eye(p))
            Z = rng_wrapper.standard_normal((n, p))
            data = Z @ L.T
            
    elif dist_type == 't':
        # Generate t-distributed data with correlation
        try:
            L = np.linalg.cholesky(cov_matrix)
            Z = rng_wrapper.standard_normal((n, p))
            # Use df=3 for heavy tails
            df = 3
            U = rng_wrapper.standard_gamma(df / 2, (n, p))
            data = Z @ L.T / np.sqrt(U / (df / 2))
        except np.linalg.LinAlgError:
            L = np.linalg.cholesky(cov_matrix + 1e-6 * np.eye(p))
            Z = rng_wrapper.standard_normal((n, p))
            df = 3
            U = rng_wrapper.standard_gamma(df / 2, (n, p))
            data = Z @ L.T / np.sqrt(U / (df / 2))
            
    elif dist_type == 'skew_normal':
        # Generate skewed normal data
        try:
            L = np.linalg.cholesky(cov_matrix)
            Z = rng_wrapper.standard_normal((n, p))
            # Skewness parameter
            alpha = 5
            data = Z @ L.T
            # Apply skew transformation
            U = rng_wrapper.standard_normal((n, p))
            data = np.where(U > 0, data, -data) * np.abs(data)
        except np.linalg.LinAlgError:
            L = np.linalg.cholesky(cov_matrix + 1e-6 * np.eye(p))
            Z = rng_wrapper.standard_normal((n, p))
            alpha = 5
            data = Z @ L.T
            U = rng_wrapper.standard_normal((n, p))
            data = np.where(U > 0, data, -data) * np.abs(data)
    else:
        raise ValueError(f"Unknown distribution type: {dist_type}")
    
    return data

def run_permutation_test(data: np.ndarray, rng_wrapper: RNGWrapper) -> np.ndarray:
    """
    Run permutation test to establish ground truth p-values.
    
    Args:
        data: Input data matrix (n, p)
        rng_wrapper: RNGWrapper for reproducibility
        
    Returns:
        Array of permutation p-values
    """
    n, p = data.shape
    pvalues = []
    
    # Split data into two groups (first half vs second half)
    mid = n // 2
    group1 = data[:mid]
    group2 = data[mid:]
    
    for i in range(p):
        # Observed statistic (t-statistic)
        obs_stat, _ = ttest_ind(group1[:, i], group2[:, i])
        
        # Permutation test
        combined = np.concatenate([group1[:, i], group2[:, i]])
        perm_stats = []
        
        for _ in range(1000):  # 1000 permutations
            rng_wrapper.shuffle(combined)
            perm_group1 = combined[:mid]
            perm_group2 = combined[mid:]
            perm_stat, _ = ttest_ind(perm_group1, perm_group2)
            perm_stats.append(abs(perm_stat))
        
        # Calculate p-value
        pvalue = np.mean(np.array(perm_stats) >= abs(obs_stat))
        pvalues.append(pvalue)
    
    return np.array(pvalues)

def generate_jagged_line_plot(observed_pvalues: np.ndarray, 
                             permutation_pvalues: np.ndarray,
                             params: Dict[str, Any],
                             ks_stat: float,
                             output_path: Path):
    """
    Generate a high-resolution "Jagged Line" histogram plot.
    
    Args:
        observed_pvalues: P-values from standard t-test
        permutation_pvalues: P-values from permutation test (ground truth)
        params: Parameter dictionary
        ks_stat: KS statistic value
        output_path: Path to save the plot
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Set style
    sns.set_style("whitegrid")
    plt.figure(figsize=(14, 10))
    
    # High-resolution histogram with 100 bins
    num_bins = 100
    bin_edges = np.linspace(0, 1, num_bins + 1)
    
    # Plot observed p-values (standard test)
    plt.hist(observed_pvalues, bins=bin_edges, alpha=0.6, label='Observed (Standard Test)', 
             color='red', edgecolor='black', linewidth=0.5)
    
    # Plot permutation p-values (ground truth)
    plt.hist(permutation_pvalues, bins=bin_edges, alpha=0.6, label='Permutation (Ground Truth)', 
             color='blue', edgecolor='black', linewidth=0.5)
    
    # Plot theoretical uniform line
    uniform_height = len(observed_pvalues) / num_bins
    plt.plot([0, 1], [uniform_height, uniform_height], 'g--', linewidth=2, label='Theoretical Uniform')
    
    # Add annotations
    plt.title(f'Jagged Line: High-Resolution Histogram of P-Values\n'
             f'Worst-Case Scenario: ρ={params["rho"]}, p={params["p"]}, n={params["n"]}, '
             f'{params["distribution_type"]}\n'
             f'KS Statistic: {ks_stat:.4f}', fontsize=14, fontweight='bold')
    
    plt.xlabel('P-Value', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.legend(loc='upper right', fontsize=10)
    plt.xlim(0, 1)
    plt.ylim(0, max(len(observed_pvalues), len(permutation_pvalues)) / num_bins * 1.5)
    
    # Add grid
    plt.grid(True, alpha=0.3)
    
    # Add text box with explanation
    explanation = (
        f"This plot reveals the 'jaggedness' of p-value distributions under high-dimensional conditions.\n"
        f"The red histogram shows the standard t-test p-values, which deviate significantly from\n"
        f"the theoretical uniform distribution (green dashed line). The blue histogram shows the\n"
        f"permutation test results, which serve as the ground truth.\n\n"
        f"Key parameters:\n"
        f"- Correlation (ρ): {params['rho']}\n"
        f"- Dimensionality (p): {params['p']}\n"
        f"- Sample size (n): {params['n']}\n"
        f"- Distribution: {params['distribution_type']}\n"
        f"- KS Statistic: {ks_stat:.4f}"
    )
    
    plt.text(0.02, 0.98, explanation, transform=plt.gca().transAxes, 
             fontsize=9, verticalalignment='top', 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Save the plot
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logger.info(f"Jagged line plot saved to {output_path}")

def main():
    """Main function to generate the jagged line plot for the worst-case scenario."""
    logger.info("Starting T050: Generating Jagged Line plot for worst-case scenario")
    
    try:
        # Load worst-case scenario
        worst_case = load_worst_case_scenario()
        logger.info(f"Loaded worst-case scenario: {worst_case}")
        
        seed = worst_case['seed']
        params = {
            'n': worst_case['n'],
            'p': worst_case['p'],
            'rho': worst_case['rho'],
            'distribution_type': worst_case['distribution_type']
        }
        ks_stat = worst_case['ks_stat']
        
        # Initialize RNG wrapper with the seed
        rng_wrapper = RNGWrapper(seed=seed)
        
        # Load observed p-values
        observed_pvalues = load_pvalues_for_seed(seed)
        logger.info(f"Loaded {len(observed_pvalues)} observed p-values for seed {seed}")
        
        # Regenerate data deterministically
        data = generate_correlated_data_with_rng(params, rng_wrapper)
        logger.info(f"Regenerated data with shape {data.shape}")
        
        # Run permutation test to get ground truth
        permutation_pvalues = run_permutation_test(data, rng_wrapper)
        logger.info(f"Generated {len(permutation_pvalues)} permutation p-values")
        
        # Generate the plot
        output_path = project_root / "docs" / "plots" / "jagged_line_worst_case_detail.png"
        generate_jagged_line_plot(observed_pvalues, permutation_pvalues, params, ks_stat, output_path)
        
        logger.info("T050 completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during plot generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
