import json
import logging
import os
import sys
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import existing utilities from the project's API surface
from utils.exceptions import HighDimensionalInstabilityError
from utils.regularization import regularize_covariance, is_condition_number_acceptable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"
WORST_CASE_FILE = DATA_RESULTS_DIR / "worst_case_summary.json"

def load_worst_case_scenario() -> Dict[str, Any]:
    """
    Load the worst-case scenario summary from the JSON file.
    
    Returns:
        Dict containing seed, n, p, rho, distribution_type, and ks_stat.
        
    Raises:
        FileNotFoundError: If the worst_case_summary.json file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not WORST_CASE_FILE.exists():
        raise FileNotFoundError(
            f"Worst case summary file not found at {WORST_CASE_FILE}. "
            "Please ensure T049 has been executed successfully."
        )
    
    with open(WORST_CASE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_pvalues_for_seed(seed: int) -> np.ndarray:
    """
    Load p-values for a specific seed from the CSV file.
    
    Args:
        seed: The seed integer used to generate the data.
        
    Returns:
        numpy array of p-values.
        
    Raises:
        FileNotFoundError: If the p-values CSV file does not exist.
    """
    pvalues_file = DATA_RESULTS_DIR / f"pvalues_{seed}.csv"
    if not pvalues_file.exists():
        raise FileNotFoundError(
            f"P-values file not found for seed {seed} at {pvalues_file}. "
            "Please ensure T022c has been executed successfully."
        )
    
    pvalues = []
    with open(pvalues_file, 'r', encoding='utf-8') as f:
        # Skip header
        next(f)
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                try:
                    pval = float(parts[1])
                    pvalues.append(pval)
                except ValueError:
                    continue
    
    return np.array(pvalues)

def load_permutation_reference(seed: int) -> np.ndarray:
    """
    Load the permutation-based reference p-values for a specific seed.
    
    Args:
        seed: The seed integer.
        
    Returns:
        numpy array of permutation p-values.
        
    Raises:
        FileNotFoundError: If the permutation p-values file does not exist.
    """
    perm_file = DATA_RESULTS_DIR / f"permutation_pvalues_{seed}.npz"
    if not perm_file.exists():
        raise FileNotFoundError(
            f"Permutation reference file not found for seed {seed} at {perm_file}. "
            "Please ensure T028a-raw has been executed successfully."
        )
    
    with np.load(perm_file) as data:
        # Assuming the array is stored under the key 'arr_0' or similar
        keys = list(data.keys())
        if not keys:
            raise ValueError(f"No arrays found in {perm_file}")
        return data[keys[0]]

def generate_correlated_data(n: int, p: int, rho: float, seed: int) -> np.ndarray:
    """
    Generate a high-dimensional dataset with a specific correlation structure.
    
    Args:
        n: Number of samples.
        p: Number of features.
        rho: Correlation coefficient for the equicorrelation matrix.
        seed: Random seed for reproducibility.
        
    Returns:
        numpy array of shape (n, p) with the specified correlation structure.
        
    Raises:
        HighDimensionalInstabilityError: If p/n > 10 or if the covariance matrix is singular.
    """
    np.random.seed(seed)
    
    # Check p/n ratio
    if p / n > 10:
        raise HighDimensionalInstabilityError(
            f"p/n ratio ({p/n:.2f}) exceeds threshold of 10. "
            "This configuration is too high-dimensional for reliable estimation."
        )
    
    # Construct the correlation matrix
    # Equicorrelation matrix: 1 on diagonal, rho elsewhere
    # This is a valid correlation matrix if -1/(p-1) <= rho <= 1
    if rho < -1/(p-1) or rho > 1:
        raise ValueError(f"Invalid correlation coefficient rho={rho} for p={p}. "
                       f"Must be in [{-1/(p-1):.4f}, 1.0]")
    
    # Generate the correlation matrix
    R = np.full((p, p), rho)
    np.fill_diagonal(R, 1.0)
    
    # Check condition number
    cond_num = np.linalg.cond(R)
    if cond_num > 1e12:
        raise HighDimensionalInstabilityError(
            f"Covariance matrix condition number ({cond_num:.2e}) exceeds 1e12. "
            "Matrix is near-singular and regularization failed."
        )
    
    # Cholesky decomposition to generate correlated data
    # X = Z @ L.T where Z is standard normal and L is lower triangular Cholesky factor
    try:
        L = np.linalg.cholesky(R)
    except np.linalg.LinAlgError:
        # Try regularization if Cholesky fails
        logger.warning("Cholesky decomposition failed. Attempting regularization.")
        R_reg = regularize_covariance(R, epsilon=1e-6)
        L = np.linalg.cholesky(R_reg)
    
    # Generate standard normal data
    Z = np.random.randn(n, p)
    
    # Generate correlated data
    X = Z @ L.T
    
    return X

def calculate_vif_and_effective_dof(n: int, p: int, rho: float) -> Tuple[float, float]:
    """
    Calculate the Variance Inflation Factor (VIF) and effective degrees of freedom.
    
    For an equicorrelation matrix with correlation rho:
    - VIF = 1 + (p-1)*rho (approximate for large p)
    - Effective DOF = n / VIF (approximate)
    
    Args:
        n: Number of samples.
        p: Number of features.
        rho: Correlation coefficient.
        
    Returns:
        Tuple of (VIF, effective_dof).
    """
    # Exact VIF for equicorrelation:
    # The variance of the mean of p correlated variables is:
    # Var(mean) = (1/p^2) * [p*Var(X) + p*(p-1)*Cov(Xi, Xj)]
    #           = (1/p^2) * [p*1 + p*(p-1)*rho]  (assuming Var(X)=1)
    #           = (1 + (p-1)*rho) / p
    #
    # The VIF is the ratio of the variance of the mean under correlation
    # to the variance under independence (which is 1/p).
    # VIF = [(1 + (p-1)*rho) / p] / (1/p) = 1 + (p-1)*rho
    
    vif = 1.0 + (p - 1) * rho
    
    # Effective degrees of freedom
    # In the context of hypothesis testing, the effective sample size is reduced
    # by the correlation. A common approximation is n_eff = n / VIF.
    effective_dof = n / vif if vif > 0 else n
    
    return vif, effective_dof

def analyze_failure_mechanism(worst_case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze the failure mechanism for the worst-case scenario.
    
    This function calculates the Variance Inflation Factor (VIF) and effective
    degrees of freedom for the correlation matrix of the worst-case scenario.
    It compares the theoretical variance (assuming independence) with the
    actual variance (due to correlation) to explain why the standard p-value
    theory fails.
    
    Args:
        worst_case: Dictionary containing the worst-case scenario parameters
                    (seed, n, p, rho, distribution_type, ks_stat).
                    
    Returns:
        Dictionary containing the analysis results:
            - vif: Variance Inflation Factor
            - effective_dof: Effective degrees of freedom
            - theoretical_variance: Variance assuming independence (1/n)
            - actual_variance: Variance under correlation (VIF/n)
            - inflation_factor: Ratio of actual to theoretical variance (equals VIF)
            - explanation: Text explanation of the failure mechanism.
    """
    n = worst_case['n']
    p = worst_case['p']
    rho = worst_case['rho']
    ks_stat = worst_case['ks_stat']
    
    # Calculate VIF and effective DOF
    vif, effective_dof = calculate_vif_and_effective_dof(n, p, rho)
    
    # Theoretical variance of the mean under independence: 1/n
    # (assuming unit variance for individual variables)
    theoretical_variance = 1.0 / n
    
    # Actual variance under correlation: VIF / n
    actual_variance = vif / n
    
    # Inflation factor (should equal VIF)
    inflation_factor = actual_variance / theoretical_variance if theoretical_variance > 0 else np.inf
    
    # Generate explanation
    explanation = (
        f"The theory fails because correlation ρ={rho:.2f} inflates the variance "
        f"of the test statistic by a factor of {vif:.2f}, causing the p-values to "
        f"cluster near 0 instead of being uniform. The 'ritual' assumes independence, "
        f"but the 'mess' of high-dimensional noise violates this. "
        f"With n={n} samples and p={p} features, the effective degrees of freedom "
        f"are reduced from {n} to {effective_dof:.2f}, severely compromising the "
        f"validity of the standard t-test p-values."
    )
    
    return {
        'vif': vif,
        'effective_dof': effective_dof,
        'theoretical_variance': theoretical_variance,
        'actual_variance': actual_variance,
        'inflation_factor': inflation_factor,
        'explanation': explanation,
        'worst_case_params': {
            'seed': worst_case['seed'],
            'n': n,
            'p': p,
            'rho': rho,
            'distribution_type': worst_case['distribution_type'],
            'ks_stat': ks_stat
        }
    }

def write_failure_mechanism_report(analysis_results: Dict[str, Any], output_path: Path) -> None:
    """
    Write the failure mechanism analysis to a markdown report.
    
    Args:
        analysis_results: Dictionary containing the analysis results.
        output_path: Path to the output markdown file.
    """
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    params = analysis_results['worst_case_params']
    
    report_content = f"""# Failure Mechanism Analysis Report

## Worst-Case Scenario Parameters

| Parameter | Value |
|-----------|-------|
| Seed | {params['seed']} |
| Sample Size (n) | {params['n']} |
| Features (p) | {params['p']} |
| Correlation (ρ) | {params['rho']:.2f} |
| Distribution Type | {params['distribution_type']} |
| KS Statistic | {params['ks_stat']:.4f} |

## Variance Inflation Analysis

The standard p-value theory assumes that observations are independent. However, in high-dimensional data with correlation, this assumption is violated, leading to inflated variance of the test statistics.

### Key Metrics

- **Variance Inflation Factor (VIF)**: {analysis_results['vif']:.4f}
- **Effective Degrees of Freedom**: {analysis_results['effective_dof']:.2f}
- **Theoretical Variance (independence)**: {analysis_results['theoretical_variance']:.6f}
- **Actual Variance (correlated)**: {analysis_results['actual_variance']:.6f}
- **Inflation Factor**: {analysis_results['inflation_factor']:.4f}

## Explanation

{analysis_results['explanation']}

## Conclusion

The "ritual" of using standard t-test p-values fails in this high-dimensional, correlated setting because the underlying assumption of independence is violated. The correlation structure inflates the variance of the test statistic, causing p-values to be anti-conservative (clustered near 0). This leads to an inflated false positive rate, where the standard test incorrectly rejects the null hypothesis more often than the nominal significance level (e.g., α=0.05).

The "understanding" comes from recognizing that the effective sample size is reduced due to correlation, and that permutation-based methods (which respect the correlation structure) provide a more valid reference distribution for hypothesis testing.
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"Failure mechanism report written to {output_path}")

def main():
    """
    Main entry point for the failure mechanism analysis.
    
    This function:
    1. Loads the worst-case scenario from data/results/worst_case_summary.json.
    2. Analyzes the failure mechanism (calculates VIF, effective DOF, etc.).
    3. Writes the results to data/results/failure_mechanism_report.md.
    """
    logger.info("Starting failure mechanism analysis...")
    
    try:
        # Load worst-case scenario
        worst_case = load_worst_case_scenario()
        logger.info(f"Loaded worst-case scenario: seed={worst_case['seed']}, "
                   f"n={worst_case['n']}, p={worst_case['p']}, rho={worst_case['rho']:.2f}")
        
        # Analyze failure mechanism
        analysis_results = analyze_failure_mechanism(worst_case)
        
        # Write report
        output_path = DATA_RESULTS_DIR / "failure_mechanism_report.md"
        write_failure_mechanism_report(analysis_results, output_path)
        
        logger.info("Failure mechanism analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in worst-case summary: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()