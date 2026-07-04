import os
import sys
import logging
import csv
import math
import random
from pathlib import Path

# Local imports
from utils.logger import get_logger

logger = get_logger(__name__)

def load_correlation_sequence(csv_path: str) -> list:
    """
    Load the sequence of Spearman rho values from drift_metrics.csv.
    Returns a list of floats.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Correlation sequence file not found: {csv_path}")

    rhos = []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Handle potential NaN or empty strings if logic changed, though spec implies floats
                val = float(row['rho'])
                if not math.isnan(val):
                    rhos.append(val)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid rho value in row: {row}, error: {e}")
                continue
    
    logger.info(f"Loaded {len(rhos)} correlation values from {csv_path}")
    return rhos

def mann_kendall_test(data: list) -> tuple:
    """
    Perform the Mann-Kendall trend test on a sequence of data.
    Returns (tau, p_value).
    
    Handles small sample sizes (n < 10) by returning a placeholder 
    or specific handling if the standard approximation is invalid, 
    though the exact p-value calculation for small n often requires 
    exact tables or permutation which we simulate here via the 
    block_permutation logic if n is very small, or standard 
    approximation otherwise.
    
    Note: For n < 10, the normal approximation for p-value is often 
    inaccurate. This implementation calculates the S statistic and 
    variance, but for the p-value, it defers to the block permutation 
    result if n is small, or returns a conservative estimate.
    """
    n = len(data)
    if n < 2:
        logger.warning("Sample size too small for Mann-Kendall test (n < 2)")
        return 0.0, 1.0

    # Calculate S statistic
    s = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            diff = data[j] - data[i]
            if diff > 0:
                s += 1
            elif diff < 0:
                s -= 1

    # Calculate Variance of S
    # Var(S) = n(n-1)(2n+5) / 18  (assuming no ties for simplicity in this context)
    # If ties exist, the formula is more complex, but for correlation sequences, 
    # exact ties are rare unless constant.
    var_s = (n * (n - 1) * (2 * n + 5)) / 18.0

    # Calculate Tau
    tau = s / math.sqrt(var_s) if var_s > 0 else 0.0

    # P-value calculation
    # For small samples (n < 10), the normal approximation is poor.
    # We return the Tau statistic. The p-value will be handled by 
    # the block_permutation_test function in the main flow as per FR-008.
    # Here we return a dummy p-value or 1.0 to indicate "rely on permutation".
    if n < 10:
        logger.info(f"Small sample size (n={n}) detected. Mann-Kendall p-value approx unreliable. Rely on permutation test.")
        p_value = 1.0 # Placeholder, actual significance determined by permutation
    else:
        # Normal approximation for larger n
        # Z = (S - 1) / sqrt(Var(S)) if S > 0, (S + 1) / sqrt(Var(S)) if S < 0, 0 if S=0
        if s > 0:
            z = (s - 1) / math.sqrt(var_s)
        elif s < 0:
            z = (s + 1) / math.sqrt(var_s)
        else:
            z = 0
        
        # Two-tailed p-value from standard normal distribution
        # Using error function approximation
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))

    return tau, p_value

def block_permutation_test(data: list, n_permutations: int = 1000, block_size: int = 2) -> float:
    """
    Perform a block permutation test to assess the significance of the trend.
    This is robust for small sample sizes and time-series data.
    
    Args:
        data: List of rho values.
        n_permutations: Number of permutations to run.
        block_size: Size of blocks to shuffle (to preserve some autocorrelation).
    
    Returns:
        p-value (float).
    """
    n = len(data)
    if n < 2:
        return 1.0

    # Calculate observed S statistic (or a trend metric)
    # We can use the sum of signed differences as the test statistic
    def calc_stat(seq):
        s = 0
        for i in range(len(seq) - 1):
            for j in range(i + 1, len(seq)):
                if seq[j] > seq[i]:
                    s += 1
                elif seq[j] < seq[i]:
                    s -= 1
        return s

    observed_stat = calc_stat(data)
    
    count_extreme = 0
    
    # Create a list of indices to permute
    indices = list(range(n))
    
    for _ in range(n_permutations):
        # Block permutation: split into blocks and shuffle blocks
        # Simple approach for small n: shuffle indices, but respecting blocks if possible
        # If n is small, full permutation might be too expensive or not applicable 
        # if n_permutations > n!.
        # Here we implement a simple block shuffle:
        blocks = [indices[i:i+block_size] for i in range(0, n, block_size)]
        random.shuffle(blocks)
        permuted_indices = [i for block in blocks for i in block]
        
        # Truncate or pad if block_size doesn't divide n perfectly (rare in small n logic)
        permuted_indices = permuted_indices[:n]
        
        permuted_data = [data[i] for i in permuted_indices]
        
        perm_stat = calc_stat(permuted_data)
        
        # Two-tailed test
        if abs(perm_stat) >= abs(observed_stat):
            count_extreme += 1

    p_value = (count_extreme + 1) / (n_permutations + 1)
    logger.debug(f"Block permutation test completed. P-value: {p_value}")
    return p_value

def run_significance_tests(rho_csv_path: str, output_json_path: str = None) -> dict:
    """
    Orchestrates the Mann-Kendall test and Block Permutation test.
    Handles small sample size constraints (n < 10) by relying on 
    permutation p-values as per FR-008.
    
    Args:
        rho_csv_path: Path to drift_metrics.csv
        output_json_path: Optional path to save results.
    
    Returns:
        Dictionary containing test results.
    """
    logger.info(f"Running significance tests on {rho_csv_path}")
    rhos = load_correlation_sequence(rho_csv_path)
    n = len(rhos)
    
    results = {
        "n_samples": n,
        "mean_rho": sum(rhos) / n if n > 0 else 0.0,
        "mann_kendall": {},
        "block_permutation": {}
    }

    # Handle small sample size logic
    if n < 10:
        logger.warning(f"Small sample size (n={n}). Relying on block permutation p-value for significance.")
        # Run block permutation with sufficient resamples
        p_val_perm = block_permutation_test(rhos, n_permutations=5000) # Increase permutations for small n reliability
        results["block_permutation"]["p_value"] = p_val_perm
        results["block_permutation"]["note"] = "Used for significance due to small sample size"
        
        # Still run MK to get Tau, but p-value from MK is not trusted
        tau, _ = mann_kendall_test(rhos)
        results["mann_kendall"]["tau"] = tau
        results["mann_kendall"]["p_value"] = None # Not reliable
        results["mann_kendall"]["reliability"] = "Low"
    else:
        # Normal path
        tau, p_val_mk = mann_kendall_test(rhos)
        results["mann_kendall"]["tau"] = tau
        results["mann_kendall"]["p_value"] = p_val_mk
        
        # Run block permutation as a robustness check
        p_val_perm = block_permutation_test(rhos, n_permutations=1000)
        results["block_permutation"]["p_value"] = p_val_perm
        results["block_permutation"]["note"] = "Robustness check"

    # Determine trend direction
    tau = results["mann_kendall"].get("tau", 0)
    if tau < -0.1:
        results["trend_direction"] = "monotonic decrease"
    elif tau > 0.1:
        results["trend_direction"] = "monotonic increase"
    else:
        results["trend_direction"] = "no clear trend"

    # Select final p-value based on sample size
    if n < 10:
        results["final_p_value"] = results["block_permutation"]["p_value"]
    else:
        # Prefer MK p-value if n is large enough, or average? 
        # Spec says "rely on permutation p-values" for small n.
        # For larger n, we can use MK, but let's store both.
        # For the "final" decision in T018, we use the block permutation if n<10.
        # Let's set final to MK for n>=10 for now, or we can use the more conservative one.
        results["final_p_value"] = min(results["mann_kendall"]["p_value"], results["block_permutation"]["p_value"])

    if output_json_path:
        with open(output_json_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved significance results to {output_json_path}")

    return results

def main():
    """Entry point for running significance tests."""
    # Default paths based on project structure
    project_root = Path(__file__).parent.parent
    rho_csv = project_root / "outputs" / "drift_metrics.csv"
    output_json = project_root / "outputs" / "significance_results.json"

    if not rho_csv.exists():
        logger.error(f"Input file not found: {rho_csv}. Run drift analysis first.")
        sys.exit(1)

    results = run_significance_tests(str(rho_csv), str(output_json))
    print(f"Significance Test Results: {results}")

if __name__ == "__main__":
    main()