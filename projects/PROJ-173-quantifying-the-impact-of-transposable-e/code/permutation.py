"""
Permutation testing module for TE-Gene association analysis.

Implements residual-based permutation (Freedman-Lane procedure) to generate
a valid null distribution while preserving the correlation structure of
population PCs.

FR-006: Explicitly do NOT shuffle TE labels directly. Instead, shuffle
residuals of the null model (gene_expression ~ PC1 + PC2 + PC3).
"""
import os
import csv
import logging
import math
import random
import time
from typing import List, Dict, Tuple, Optional, Any

from utils import setup_logger, ensure_directory, set_random_seed

logger = setup_logger(__name__)

class PermutationError(Exception):
    """Custom exception for permutation-related errors."""
    pass

def solve_linear_system(A: List[List[float]], b: List[float]) -> List[float]:
    """
    Solve linear system Ax = b using Gaussian elimination with partial pivoting.
    
    Args:
        A: Coefficient matrix (n x n)
        b: Constant vector (n)
        
    Returns:
        Solution vector x (n)
        
    Raises:
        PermutationError: If matrix is singular or system is inconsistent
    """
    n = len(A)
    # Create augmented matrix
    aug = [row[:] + [b[i]] for i, row in enumerate(A)]
    
    # Forward elimination with partial pivoting
    for col in range(n):
        # Find pivot
        max_row = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > abs(aug[max_row][col]):
                max_row = row
        aug[col], aug[max_row] = aug[max_row], aug[col]
        
        # Check for singular matrix
        if abs(aug[col][col]) < 1e-12:
            raise PermutationError(f"Singular matrix detected at column {col}")
        
        # Eliminate
        for row in range(col + 1, n):
            factor = aug[row][col] / aug[col][col]
            for j in range(col, n + 1):
                aug[row][j] -= factor * aug[col][j]
    
    # Back substitution
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = aug[i][n]
        for j in range(i + 1, n):
            x[i] -= aug[i][j] * x[j]
        x[i] /= aug[i][i]
        
    return x

def invert_matrix(M: List[List[float]]) -> List[List[float]]:
    """
    Compute the inverse of a square matrix using Gauss-Jordan elimination.
    
    Args:
        M: Square matrix to invert
        
    Returns:
        Inverse matrix
        
    Raises:
        PermutationError: If matrix is singular
    """
    n = len(M)
    # Create augmented matrix [M | I]
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] 
           for i, row in enumerate(M)]
    
    # Forward elimination with partial pivoting
    for col in range(n):
        # Find pivot
        max_row = col
        for row in range(col + 1, n):
            if abs(aug[row][col]) > abs(aug[max_row][col]):
                max_row = row
        aug[col], aug[max_row] = aug[max_row], aug[col]
        
        if abs(aug[col][col]) < 1e-12:
            raise PermutationError("Matrix is singular, cannot invert")
        
        # Scale pivot row
        pivot = aug[col][col]
        for j in range(2 * n):
            aug[col][j] /= pivot
        
        # Eliminate column
        for row in range(n):
            if row != col:
                factor = aug[row][col]
                for j in range(2 * n):
                    aug[row][j] -= factor * aug[col][j]
    
    # Extract inverse
    return [row[n:] for row in aug]

def compute_residuals(y: List[float], X: List[List[float]]) -> List[float]:
    """
    Compute residuals from linear regression y ~ X.
    
    This implements the null model: gene_expression ~ PC1 + PC2 + PC3
    
    Args:
        y: Dependent variable (gene expression)
        X: Design matrix (including intercept column of 1s)
        
    Returns:
        Residuals vector
        
    Raises:
        PermutationError: If linear system cannot be solved
    """
    n = len(y)
    if n == 0:
        raise PermutationError("Empty input data for residual computation")
    
    p = len(X[0])
    if p == 0:
        raise PermutationError("Empty design matrix")
    
    # Compute X'X
    XtX = [[0.0] * p for _ in range(p)]
    for i in range(n):
        for j in range(p):
            for k in range(p):
                XtX[j][k] += X[i][j] * X[i][k]
    
    # Compute X'y
    Xty = [0.0] * p
    for i in range(n):
        for j in range(p):
            Xty[j] += X[i][j] * y[i]
    
    # Solve (X'X) * beta = X'y
    try:
        beta = solve_linear_system(XtX, Xty)
    except PermutationError:
        raise PermutationError("Failed to solve linear system for residuals")
    
    # Compute fitted values and residuals
    residuals = []
    for i in range(n):
        fitted = sum(X[i][j] * beta[j] for j in range(p))
        residuals.append(y[i] - fitted)
    
    return residuals

def generate_null_distribution(
    y: List[float],
    X_null: List[List[float]],
    X_TE: List[float],
    n_permutations: int,
    seed: Optional[int] = None
) -> List[float]:
    """
    Generate null distribution using residual-based permutation (Freedman-Lane).
    
    This is the core of FR-006: we do NOT shuffle TE labels directly.
    Instead:
    1. Fit null model: y ~ X_null (PCs)
    2. Compute residuals: r = y - y_hat
    3. Shuffle residuals: r_perm = shuffle(r)
    4. Create permuted response: y_perm = y_hat + r_perm
    5. Fit full model: y_perm ~ X_null + X_TE
    6. Record t-statistic for X_TE
    
    Args:
        y: Original gene expression values
        X_null: Null model design matrix (intercept + PCs)
        X_TE: TE presence vector
        n_permutations: Number of permutations to perform
        seed: Random seed for reproducibility
        
    Returns:
        List of t-statistics from permuted models
        
    Raises:
        PermutationError: If computation fails
    """
    if seed is not None:
        set_random_seed(seed)
    
    n = len(y)
    if n == 0:
        raise PermutationError("Empty input for null distribution generation")
    
    p_null = len(X_null[0])
    if p_null == 0:
        raise PermutationError("Empty null design matrix")
    
    logger.info(f"Generating null distribution with {n_permutations} permutations")
    logger.info(f"Sample size: {n}, Null predictors: {p_null}")
    
    # Step 1: Fit null model and get residuals
    try:
        residuals = compute_residuals(y, X_null)
    except PermutationError as e:
        raise PermutationError(f"Failed to compute residuals: {e}")
    
    # Compute fitted values from null model
    XtX = [[0.0] * p_null for _ in range(p_null)]
    Xty = [0.0] * p_null
    for i in range(n):
        for j in range(p_null):
            for k in range(p_null):
                XtX[j][k] += X_null[i][j] * X_null[i][k]
            Xty[j] += X_null[i][j] * y[i]
    
    beta_null = solve_linear_system(XtX, Xty)
    y_hat = [sum(X_null[i][j] * beta_null[j] for j in range(p_null)) for i in range(n)]
    
    null_stats = []
    
    for perm_idx in range(n_permutations):
        # Step 3: Shuffle residuals
        shuffled_residuals = residuals[:]
        random.shuffle(shuffled_residuals)
        
        # Step 4: Create permuted response
        y_perm = [y_hat[i] + shuffled_residuals[i] for i in range(n)]
        
        # Step 5: Fit full model (y_perm ~ X_null + X_TE)
        # Build full design matrix
        X_full = [X_null[i][:] + [X_TE[i]] for i in range(n)]
        p_full = p_null + 1
        
        try:
            # Compute X'X and X'y for full model
            XtX_full = [[0.0] * p_full for _ in range(p_full)]
            Xty_full = [0.0] * p_full
            
            for i in range(n):
                for j in range(p_full):
                    for k in range(p_full):
                        XtX_full[j][k] += X_full[i][j] * X_full[i][k]
                    Xty_full[j] += X_full[i][j] * y_perm[i]
            
            # Solve for beta
            beta_full = solve_linear_system(XtX_full, Xty_full)
            
            # Compute residuals for full model
            fitted_full = [sum(X_full[i][j] * beta_full[j] for j in range(p_full)) 
                           for i in range(n)]
            res_full = [y_perm[i] - fitted_full[i] for i in range(n)]
            
            # Compute residual sum of squares
            rss_full = sum(r * r for r in res_full)
            
            # Compute standard error of TE coefficient
            # Var(beta_TE) = sigma^2 * (X'X)^{-1}_{TE,TE}
            # sigma^2 = RSS / (n - p)
            sigma2 = rss_full / (n - p_full) if (n - p_full) > 0 else 1e-10
            
            # Compute inverse of X'X
            inv_XtX = invert_matrix(XtX_full)
            se_TE = math.sqrt(sigma2 * inv_XtX[-1][-1])
            
            # Compute t-statistic for TE
            t_stat = beta_full[-1] / se_TE if se_TE > 1e-12 else 0.0
            
            null_stats.append(t_stat)
            
        except PermutationError as e:
            logger.warning(f"Permutation {perm_idx} failed: {e}, skipping")
            continue
        
        if (perm_idx + 1) % 100 == 0:
            logger.info(f"Completed {perm_idx + 1}/{n_permutations} permutations")
    
    logger.info(f"Null distribution generated with {len(null_stats)} valid statistics")
    return null_stats

def compute_permutation_pvalue(
    observed_t: float,
    null_distribution: List[float],
    alternative: str = "two-sided"
) -> float:
    """
    Compute permutation p-value by comparing observed statistic to null distribution.
    
    Args:
        observed_t: Observed t-statistic from real data
        null_distribution: List of t-statistics from permuted data
        alternative: "two-sided", "greater", or "less"
        
    Returns:
        Permutation p-value
    """
    if not null_distribution:
        raise PermutationError("Empty null distribution")
    
    n_perm = len(null_distribution)
    
    if alternative == "two-sided":
        # Count how many null stats have |t| >= |observed_t|
        count = sum(1 for t in null_distribution if abs(t) >= abs(observed_t))
    elif alternative == "greater":
        # Count how many null stats >= observed_t
        count = sum(1 for t in null_distribution if t >= observed_t)
    elif alternative == "less":
        # Count how many null stats <= observed_t
        count = sum(1 for t in null_distribution if t <= observed_t)
    else:
        raise PermutationError(f"Unknown alternative: {alternative}")
    
    # P-value = (count + 1) / (n_perm + 1) to avoid p=0
    p_value = (count + 1) / (n_perm + 1)
    
    return p_value

def main():
    """
    Main function to demonstrate permutation testing on mock data.
    
    This function:
    1. Loads mock data generated by data_generator.py
    2. Runs association tests to get observed t-statistics
    3. Performs residual-based permutation testing
    4. Computes permutation p-values
    5. Saves results to data/results/
    """
    logger.info("Starting permutation testing module")
    
    # Set random seed for reproducibility
    set_random_seed(42)
    
    # Ensure output directory exists
    ensure_directory("data/results")
    
    # Load mock data
    try:
        # Load expression data
        expr_file = "data/mock_expression.csv"
        if not os.path.exists(expr_file):
            raise PermutationError(f"Expression data not found: {expr_file}")
        
        with open(expr_file, 'r') as f:
            reader = csv.DictReader(f)
            gene_ids = []
            line_ids = []
            expression_data = {}
            for row in reader:
                gene_id = row['gene_id']
                line_id = row['line_id']
                gene_ids.append(gene_id)
                line_ids.append(line_id)
                if gene_id not in expression_data:
                    expression_data[gene_id] = {}
                expression_data[gene_id][line_id] = float(row['expression_tpm'])
        
        # Load TE presence data
        te_file = "data/mock_te_genotypes.csv"
        if not os.path.exists(te_file):
            raise PermutationError(f"TE genotypes not found: {te_file}")
        
        with open(te_file, 'r') as f:
            reader = csv.DictReader(f)
            te_ids = []
            te_data = {}
            for row in reader:
                te_id = row['te_id']
                line_id = row['line_id']
                te_ids.append(te_id)
                if te_id not in te_data:
                    te_data[te_id] = {}
                te_data[te_id][line_id] = int(row['presence'])
        
        # Load PC data
        pc_file = "data/mock_population_pcs.csv"
        if not os.path.exists(pc_file):
            raise PermutationError(f"Population PCs not found: {pc_file}")
        
        with open(pc_file, 'r') as f:
            reader = csv.DictReader(f)
            pc_data = {}
            all_line_ids = set()
            for row in reader:
                line_id = row['line_id']
                all_line_ids.add(line_id)
                pc_data[line_id] = {
                    'PC1': float(row['PC1']),
                    'PC2': float(row['PC2']),
                    'PC3': float(row['PC3'])
                }
        
        # Get common lines
        common_lines = set(line_ids) & set(all_line_ids)
        if len(common_lines) < 10:
            raise PermutationError("Not enough common lines between datasets")
        
        common_lines = sorted(common_lines)
        logger.info(f"Using {len(common_lines)} common lines for analysis")
        
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise PermutationError(f"Data loading failed: {e}")
    
    # Select a few TE-gene pairs for demonstration
    # In a real scenario, this would come from association.py results
    test_pairs = []
    
    # Find some TE-gene pairs that exist in the data
    gene_ids_unique = list(set(gene_ids))
    te_ids_unique = list(set(te_ids))
    
    # Take first 5 pairs for demonstration
    for i in range(min(5, len(gene_ids_unique))):
        for j in range(min(5, len(te_ids_unique))):
            gene_id = gene_ids_unique[i]
            te_id = te_ids_unique[j]
            
            # Check if both have data for all common lines
            if (gene_id in expression_data and 
                te_id in te_data and
                all(line in expression_data[gene_id] and line in te_data[te_id] 
                    for line in common_lines)):
                test_pairs.append((gene_id, te_id))
    
    if not test_pairs:
        logger.warning("No valid TE-gene pairs found for permutation testing")
        # Write empty results
        with open("data/results/permutation_results.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['gene_id', 'te_id', 'observed_t', 'p_permutation', 'n_permutations'])
        return
    
    logger.info(f"Testing {len(test_pairs)} TE-gene pairs with permutation")
    
    # Run permutation testing for each pair
    results = []
    n_permutations = 1000  # Reduced for demo; should be higher in production
    
    for gene_id, te_id in test_pairs:
        logger.info(f"Processing {gene_id} - {te_id}")
        
        # Extract data for common lines
        y = [expression_data[gene_id][line] for line in common_lines]
        te_vec = [te_data[te_id][line] for line in common_lines]
        pcs = [[pc_data[line]['PC1'], pc_data[line]['PC2'], pc_data[line]['PC3']] 
               for line in common_lines]
        
        # Build design matrices
        # Null model: intercept + PCs
        X_null = [[1.0] + pcs[i] for i in range(len(common_lines))]
        
        # Compute observed t-statistic
        try:
            # Fit full model: y ~ intercept + PCs + TE
            X_full = [X_null[i][:] + [te_vec[i]] for i in range(len(common_lines))]
            p_full = len(X_full[0])
            
            # Compute X'X and X'y
            n = len(y)
            XtX = [[0.0] * p_full for _ in range(p_full)]
            Xty = [0.0] * p_full
            
            for i in range(n):
                for j in range(p_full):
                    for k in range(p_full):
                        XtX[j][k] += X_full[i][j] * X_full[i][k]
                    Xty[j] += X_full[i][j] * y[i]
            
            beta = solve_linear_system(XtX, Xty)
            
            # Compute residuals
            fitted = [sum(X_full[i][j] * beta[j] for j in range(p_full)) for i in range(n)]
            residuals = [y[i] - fitted[i] for i in range(n)]
            rss = sum(r * r for r in residuals)
            
            # Standard error
            sigma2 = rss / (n - p_full) if (n - p_full) > 0 else 1e-10
            inv_XtX = invert_matrix(XtX)
            se_TE = math.sqrt(sigma2 * inv_XtX[-1][-1])
            
            observed_t = beta[-1] / se_TE if se_TE > 1e-12 else 0.0
            
            # Generate null distribution
            null_dist = generate_null_distribution(
                y, X_null, te_vec, n_permutations, seed=42
            )
            
            # Compute permutation p-value
            p_perm = compute_permutation_pvalue(observed_t, null_dist, "two-sided")
            
            results.append({
                'gene_id': gene_id,
                'te_id': te_id,
                'observed_t': observed_t,
                'p_permutation': p_perm,
                'n_permutations': len(null_dist)
            })
            
            logger.info(f"  Observed t={observed_t:.4f}, p_perm={p_perm:.4f}")
            
        except Exception as e:
            logger.warning(f"Failed to process pair {gene_id}-{te_id}: {e}")
            continue
    
    # Write results
    output_file = "data/results/permutation_results.csv"
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['gene_id', 'te_id', 'observed_t', 'p_permutation', 'n_permutations'])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Permutation results written to {output_file}")
    
    # Also save null distribution for the first pair for visualization
    if results:
        first_pair = results[0]
        gene_id, te_id = first_pair['gene_id'], first_pair['te_id']
        
        # Re-compute null distribution for saving
        y = [expression_data[gene_id][line] for line in common_lines]
        te_vec = [te_data[te_id][line] for line in common_lines]
        pcs = [[pc_data[line]['PC1'], pc_data[line]['PC2'], pc_data[line]['PC3']] 
               for line in common_lines]
        X_null = [[1.0] + pcs[i] for i in range(len(common_lines))]
        
        null_dist = generate_null_distribution(y, X_null, te_vec, n_permutations, seed=42)
        
        # Save null distribution
        null_dist_file = "data/results/null_distribution_values.csv"
        with open(null_dist_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['t_statistic'])
            for t in null_dist:
                writer.writerow([t])
        
        logger.info(f"Null distribution saved to {null_dist_file}")

if __name__ == "__main__":
    main()