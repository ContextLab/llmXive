import os
import csv
import logging
import math
from typing import List, Dict, Tuple, Optional, Any
from utils import setup_logger, ensure_directory, set_random_seed

class ReplicationError(Exception):
    """Custom exception for replication analysis errors."""
    pass

def solve_linear_system(A: List[List[float]], b: List[float]) -> List[float]:
    """
    Solves the linear system Ax = b using Gaussian elimination with partial pivoting.
    Returns the solution vector x.
    """
    n = len(A)
    # Create augmented matrix
    M = [row[:] + [val] for row, val in zip(A, b)]

    # Forward elimination
    for i in range(n):
        # Find pivot
        max_row = i
        for k in range(i + 1, n):
            if abs(M[k][i]) > abs(M[max_row][i]):
                max_row = k
        M[i], M[max_row] = M[max_row], M[i]

        if abs(M[i][i]) < 1e-10:
            raise ReplicationError("Matrix is singular or near-singular.")

        for k in range(i + 1, n):
            factor = M[k][i] / M[i][i]
            for j in range(i, n + 1):
                M[k][j] -= factor * M[i][j]

    # Back substitution
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        s = M[i][n]
        for j in range(i + 1, n):
            s -= M[i][j] * x[j]
        x[i] = s / M[i][i]
    return x

def invert_matrix(M: List[List[float]]) -> List[List[float]]:
    """
    Inverts a square matrix using Gauss-Jordan elimination.
    """
    n = len(M)
    # Augment with identity
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(M)]

    for i in range(n):
        # Pivot
        max_row = i
        for k in range(i + 1, n):
            if abs(aug[k][i]) > abs(aug[max_row][i]):
                max_row = k
        aug[i], aug[max_row] = aug[max_row], aug[i]

        if abs(aug[i][i]) < 1e-10:
            raise ReplicationError("Matrix is singular and cannot be inverted.")

        # Scale pivot row
        div = aug[i][i]
        for j in range(2 * n):
            aug[i][j] /= div

        # Eliminate column
        for k in range(n):
            if k != i:
                factor = aug[k][i]
                for j in range(2 * n):
                    aug[k][j] -= factor * aug[i][j]

    # Extract inverse
    return [row[n:] for row in aug]

def normal_cdf(x: float) -> float:
    """Approximation of the standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def load_replication_expression_data(filepath: str) -> Dict[str, Dict[str, float]]:
    """
    Loads expression data from a CSV file.
    Returns: { gene_id: { line_id: tpm_value } }
    """
    data = {}
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            gene_id = row['gene_id']
            if gene_id not in data:
                data[gene_id] = {}
            for key, val in row.items():
                if key != 'gene_id':
                    try:
                        data[gene_id][key] = float(val)
                    except ValueError:
                        pass
    return data

def load_replication_te_presence_data(filepath: str) -> Dict[str, Dict[str, int]]:
    """
    Loads TE presence data from a CSV file.
    Returns: { te_id: { line_id: presence (0/1) } }
    """
    data = {}
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            te_id = row['te_id']
            if te_id not in data:
                data[te_id] = {}
            for key, val in row.items():
                if key != 'te_id':
                    try:
                        data[te_id][key] = int(float(val))
                    except ValueError:
                        pass
    return data

def load_replication_pcs_data(filepath: str) -> Dict[str, List[float]]:
    """
    Loads PC data from a CSV file.
    Returns: { line_id: [pc1, pc2, pc3] }
    """
    data = {}
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            line_id = row['line_id']
            pcs = []
            for i in range(1, 4):
                key = f'PC{i}'
                if key in row:
                    pcs.append(float(row[key]))
            data[line_id] = pcs
    return data

def get_common_lines(
    expr_data: Dict[str, Dict[str, float]],
    te_data: Dict[str, Dict[str, int]],
    pc_data: Dict[str, List[float]]
) -> List[str]:
    """
    Identifies lines present in all three datasets.
    """
    expr_lines = set()
    for gene in expr_data.values():
        expr_lines.update(gene.keys())

    te_lines = set()
    for te in te_data.values():
        te_lines.update(te.keys())

    pc_lines = set(pc_data.keys())

    common = expr_lines.intersection(te_lines).intersection(pc_lines)
    return sorted(list(common))

def fit_replication_model(
    expr: List[float],
    te: List[int],
    pcs: List[List[float]]
) -> Tuple[float, float, float]:
    """
    Fits the model: expr ~ TE + PC1 + PC2 + PC3
    Returns: (beta_TE, se_TE, t_stat)
    """
    n = len(expr)
    if n == 0:
        raise ReplicationError("No data points for fitting.")

    # Design matrix X: [1, TE, PC1, PC2, PC3]
    X = []
    for i in range(n):
        row = [1.0, float(te[i])] + pcs[i]
        X.append(row)

    # Solve for coefficients: (X'X)^-1 X'y
    # Compute X'X
    XtX = [[0.0] * 5 for _ in range(5)]
    for i in range(5):
        for j in range(5):
            s = 0.0
            for k in range(n):
                s += X[k][i] * X[k][j]
            XtX[i][j] = s

    # Compute X'y
    Xty = [0.0] * 5
    for i in range(5):
        s = 0.0
        for k in range(n):
            s += X[k][i] * expr[k]
        Xty[i] = s

    try:
        XtX_inv = invert_matrix(XtX)
    except ReplicationError:
        raise ReplicationError("Design matrix is singular.")

    beta = solve_linear_system(XtX, Xty)
    # beta_TE is beta[1]

    # Residuals
    residuals = []
    for k in range(n):
        pred = sum(X[k][j] * beta[j] for j in range(5))
        residuals.append(expr[k] - pred)

    # Residual Sum of Squares
    rss = sum(r * r for r in residuals)
    df = n - 5
    if df <= 0:
        raise ReplicationError("Insufficient degrees of freedom.")

    sigma2 = rss / df

    # Variance of beta_TE: sigma2 * (X'X)^-1[1,1]
    var_beta_te = sigma2 * XtX_inv[1][1]
    if var_beta_te < 0:
        var_beta_te = 0.0
    se_beta_te = math.sqrt(var_beta_te)

    if se_beta_te < 1e-10:
        t_stat = float('inf') if beta[1] > 0 else float('-inf')
    else:
        t_stat = beta[1] / se_beta_te

    return beta[1], se_beta_te, t_stat

def load_significant_pairs(filepath: str) -> List[Dict[str, Any]]:
    """
    Loads the list of significant TE-Gene pairs from the US1 results.
    """
    pairs = []
    if not os.path.exists(filepath):
        raise ReplicationError(f"Significant pairs file not found: {filepath}")

    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric strings to floats
            try:
                row['effect_size'] = float(row['effect_size'])
                row['p_value'] = float(row['p_value'])
                row['adj_p_value'] = float(row['adj_p_value'])
            except (ValueError, KeyError):
                continue
            pairs.append(row)
    return pairs

def filter_significant_pairs_for_replication(
    pairs: List[Dict[str, Any]],
    te_data: Dict[str, Dict[str, int]],
    expr_data: Dict[str, Dict[str, float]],
    common_lines: List[str]
) -> List[Dict[str, Any]]:
    """
    Filters pairs that have sufficient data (non-missing) in the replication set.
    """
    valid_pairs = []
    for pair in pairs:
        te_id = pair['te_id']
        gene_id = pair['gene_id']

        # Check if TE and Gene exist in replication data
        if te_id not in te_data or gene_id not in expr_data:
            continue

        # Check if there are enough common lines with data
        te_vals = te_data[te_id]
        expr_vals = expr_data[gene_id]

        valid_lines = [
            line for line in common_lines
            if line in te_vals and line in expr_vals
        ]

        if len(valid_lines) >= 10: # Minimum sample size for replication
            pair['_valid_lines'] = valid_lines
            valid_pairs.append(pair)

    return valid_pairs

def calculate_concordance(
    original_beta: float,
    replication_beta: float,
    original_se: float,
    replication_se: float
) -> Tuple[bool, float]:
    """
    Calculates direction concordance and performs a binomial test logic.
    Returns: (is_concordant, z_score_for_binomial_approx)
    """
    # Direction concordance
    is_concordant = (original_beta > 0 and replication_beta > 0) or \
                    (original_beta < 0 and replication_beta < 0)

    # For the binomial test against null (p=0.5), we just count successes later.
    # This function returns the boolean flag for the individual pair.
    return is_concordant, 0.0

def generate_comparison_table(
    original_pairs: List[Dict[str, Any]],
    replication_results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Generates the final comparison table CSV.
    """
    ensure_directory(output_path)
    headers = [
        'te_id', 'gene_id', 'original_effect_size', 'original_p_value',
        'replication_effect_size', 'replication_p_value',
        'concordance_flag', 'replication_t_stat'
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for orig, rep in zip(original_pairs, replication_results):
            row = {
                'te_id': orig['te_id'],
                'gene_id': orig['gene_id'],
                'original_effect_size': orig['effect_size'],
                'original_p_value': orig['p_value'],
                'replication_effect_size': rep['beta'],
                'replication_p_value': rep['p_value'],
                'concordance_flag': rep['concordance'],
                'replication_t_stat': rep['t_stat']
            }
            writer.writerow(row)

def run_replication_analysis(
    replication_expr_path: str,
    replication_te_path: str,
    replication_pc_path: str,
    significant_pairs_path: str,
    output_table_path: str,
    output_concordance_path: str
) -> Dict[str, Any]:
    """
    Orchestrates the full replication analysis:
    1. Load replication data.
    2. Load significant pairs from US1.
    3. Filter pairs for valid data.
    4. Fit models for each pair.
    5. Calculate concordance.
    6. Write comparison table.
    7. Compute overall concordance rate and binomial test.
    """
    logger = setup_logger(__name__)
    logger.info("Starting replication analysis...")

    # 1. Load Data
    expr_data = load_replication_expression_data(replication_expr_path)
    te_data = load_replication_te_presence_data(replication_te_path)
    pc_data = load_replication_pcs_data(replication_pc_path)

    common_lines = get_common_lines(expr_data, te_data, pc_data)
    logger.info(f"Found {len(common_lines)} common lines.")

    # 2. Load Significant Pairs
    significant_pairs = load_significant_pairs(significant_pairs_path)
    logger.info(f"Loaded {len(significant_pairs)} significant pairs from US1.")

    if not significant_pairs:
        logger.warning("No significant pairs found to replicate.")
        # Write empty results
        ensure_directory(output_table_path)
        with open(output_table_path, 'w', newline='') as f:
            f.write("te_id,gene_id,original_effect_size,original_p_value,replication_effect_size,replication_p_value,concordance_flag,replication_t_stat\n")
        ensure_directory(output_concordance_path)
        with open(output_concordance_path, 'w') as f:
            f.write("concordance_rate,concordance_count,total_count,p_value_binomial\n0.0,0,0,1.0\n")
        return {"concordance_rate": 0.0, "count": 0}

    # 3. Filter for valid data
    valid_pairs = filter_significant_pairs_for_replication(
        significant_pairs, te_data, expr_data, common_lines
    )
    logger.info(f"Filtered to {len(valid_pairs)} pairs with sufficient replication data.")

    replication_results = []
    concordance_count = 0

    # 4. Fit Models & 5. Calculate Concordance
    for pair in valid_pairs:
        te_id = pair['te_id']
        gene_id = pair['gene_id']
        valid_lines = pair['_valid_lines']

        # Prepare vectors
        expr_vec = [expr_data[gene_id][line] for line in valid_lines]
        te_vec = [te_data[te_id][line] for line in valid_lines]
        pc_vec = [pc_data[line] for line in valid_lines]

        try:
            beta, se, t_stat = fit_replication_model(expr_vec, te_vec, pc_vec)
            
            # Calculate p-value from t-stat (two-tailed approximation)
            # Using normal approximation for large N, or t-dist if we had df
            # For simplicity in this mock context, using normal CDF
            p_val = 2 * (1 - normal_cdf(abs(t_stat)))

            # Check concordance
            is_concordant, _ = calculate_concordance(pair['effect_size'], beta, 0, 0)
            if is_concordant:
                concordance_count += 1

            replication_results.append({
                'beta': beta,
                'p_value': p_val,
                't_stat': t_stat,
                'concordance': is_concordant
            })
        except Exception as e:
            logger.warning(f"Failed to fit model for {te_id}-{gene_id}: {e}")
            replication_results.append({
                'beta': float('nan'),
                'p_value': float('nan'),
                't_stat': float('nan'),
                'concordance': False
            })

    # 6. Write Comparison Table
    generate_comparison_table(valid_pairs, replication_results, output_table_path)
    logger.info(f"Comparison table written to {output_table_path}")

    # 7. Compute Overall Concordance Rate and Binomial Test
    total_count = len(replication_results)
    concordance_rate = concordance_count / total_count if total_count > 0 else 0.0

    # Binomial test against null hypothesis p=0.5
    # We approximate using Normal approximation to Binomial:
    # Z = (k - n*p) / sqrt(n * p * (1-p))
    # p_val = 2 * (1 - Phi(|Z|))
    n = total_count
    p_null = 0.5
    if n > 0:
        expected = n * p_null
        std_dev = math.sqrt(n * p_null * (1 - p_null))
        if std_dev > 0:
            z_score = (concordance_count - expected) / std_dev
            binomial_p_val = 2 * (1 - normal_cdf(abs(z_score)))
        else:
            binomial_p_val = 1.0
    else:
        binomial_p_val = 1.0

    # Write Concordance Summary
    ensure_directory(output_concordance_path)
    with open(output_concordance_path, 'w') as f:
        f.write("concordance_rate,concordance_count,total_count,p_value_binomial\n")
        f.write(f"{concordance_rate},{concordance_count},{total_count},{binomial_p_val}\n")
    
    logger.info(f"Concordance rate: {concordance_rate:.4f} ({concordance_count}/{total_count})")
    logger.info(f"Binomial test p-value: {binomial_p_val:.4f}")

    return {
        "concordance_rate": concordance_rate,
        "concordance_count": concordance_count,
        "total_count": total_count,
        "p_value_binomial": binomial_p_val
    }

def main():
    """
    Main entry point for replication analysis.
    Assumes paths are configured or passed via arguments.
    For this task, we use hardcoded paths relative to the project structure
    as per the project's standard data layout.
    """
    logger = setup_logger(__name__)
    set_random_seed(42)

    # Define paths
    replication_expr_path = "data/mock_expression_replication.csv"
    replication_te_path = "data/mock_te_presence_replication.csv"
    replication_pc_path = "data/mock_pcs_replication.csv"
    significant_pairs_path = "data/results/association_results_fdr0.05.csv"
    
    output_table_path = "data/results/replication_comparison_table.csv"
    output_concordance_path = "data/results/replication_concordance_summary.csv"

    # Ensure input files exist (they should be generated by T031-T035 or data_generator)
    if not os.path.exists(replication_expr_path):
        logger.error(f"Replication expression data not found: {replication_expr_path}")
        return
    if not os.path.exists(replication_te_path):
        logger.error(f"Replication TE data not found: {replication_te_path}")
        return
    if not os.path.exists(significant_pairs_path):
        logger.error(f"Significant pairs file not found: {significant_pairs_path}")
        return

    try:
        results = run_replication_analysis(
            replication_expr_path,
            replication_te_path,
            replication_pc_path,
            significant_pairs_path,
            output_table_path,
            output_concordance_path
        )
        logger.info("Replication analysis completed successfully.")
        logger.info(f"Final Concordance Rate: {results['concordance_rate']}")
        logger.info(f"Binomial Test P-Value: {results['p_value_binomial']}")
    except ReplicationError as e:
        logger.error(f"Replication analysis failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()