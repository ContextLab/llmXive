import os
import csv
import logging
import math
from typing import List, Dict, Tuple, Optional, Any
from utils import setup_logger, ensure_directory, set_random_seed

class ReplicationError(Exception):
    """Custom exception for replication analysis errors."""
    pass

def solve_linear_system(A: List[List[float]], b: List[float]) -> Optional[List[float]]:
    """
    Solve a linear system Ax = b using Gaussian elimination with partial pivoting.
    Returns None if the system is singular.
    """
    n = len(A)
    if n == 0:
        return None
    m = len(A[0])
    
    # Create augmented matrix
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    
    # Forward elimination
    for i in range(n):
        # Find pivot
        max_row = i
        for k in range(i + 1, n):
            if abs(M[k][i]) > abs(M[max_row][i]):
                max_row = k
        M[i], M[max_row] = M[max_row], M[i]
        
        if abs(M[i][i]) < 1e-12:
            return None  # Singular matrix
        
        for k in range(i + 1, n):
            factor = M[k][i] / M[i][i]
            for j in range(i, m + 1):
                M[k][j] -= factor * M[i][j]
    
    # Back substitution
    x = [0.0] * m
    for i in range(n - 1, -1, -1):
        x[i] = M[i][n]
        for j in range(i + 1, m):
            x[i] -= M[i][j] * x[j]
        x[i] /= M[i][i]
    
    return x

def invert_matrix(M: List[List[float]]) -> Optional[List[List[float]]]:
    """
    Invert a square matrix using Gauss-Jordan elimination.
    Returns None if the matrix is singular.
    """
    n = len(M)
    if n == 0:
        return None
    if any(len(row) != n for row in M):
        return None
        
    # Create augmented matrix [M | I]
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(M)]
    
    for i in range(n):
        # Find pivot
        max_row = i
        for k in range(i + 1, n):
            if abs(aug[k][i]) > abs(aug[max_row][i]):
                max_row = k
        aug[i], aug[max_row] = aug[max_row], aug[i]
        
        if abs(aug[i][i]) < 1e-12:
            return None  # Singular matrix
        
        # Scale pivot row
        pivot = aug[i][i]
        for j in range(2 * n):
            aug[i][j] /= pivot
        
        # Eliminate column
        for k in range(n):
            if k != i:
                factor = aug[k][i]
                for j in range(2 * n):
                    aug[k][j] -= factor * aug[i][j]
    
    # Extract inverse
    return [row[n:] for row in aug]

def normal_cdf(x: float) -> float:
    """
    Approximate the cumulative distribution function for the standard normal distribution.
    Uses the error function approximation.
    """
    # Approximation of erf using Abramowitz and Stegun formula
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    d = 0.3989423 * math.exp(-x * x / 2.0)
    p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
    if x > 0:
        return 1.0 - p
    else:
        return p

def load_replication_expression_data(filepath: str) -> Dict[str, Dict[str, float]]:
    """
    Load gene expression data from a CSV file.
    Returns a dict: { gene_id: { line_id: tpm_value } }
    """
    data = {}
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            gene_id = row['gene_id']
            if gene_id not in data:
                data[gene_id] = {}
            for key, val in row.items():
                if key != 'gene_id' and val:
                    try:
                        data[gene_id][key] = float(val)
                    except ValueError:
                        pass
    return data

def load_replication_te_presence_data(filepath: str) -> Dict[str, Dict[str, int]]:
    """
    Load TE presence/absence data from a CSV file.
    Returns a dict: { te_id: { line_id: presence (0/1) } }
    """
    data = {}
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            te_id = row['te_id']
            if te_id not in data:
                data[te_id] = {}
            for key, val in row.items():
                if key != 'te_id' and val:
                    try:
                        data[te_id][key] = int(val)
                    except ValueError:
                        pass
    return data

def load_replication_pcs_data(filepath: str) -> Dict[str, List[float]]:
    """
    Load population structure PCs from a CSV file.
    Returns a dict: { line_id: [pc1, pc2, pc3, ...] }
    """
    data = {}
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            line_id = row['line_id']
            pcs = []
            for key in row:
                if key.startswith('pc') and key != 'line_id':
                    try:
                        pcs.append(float(row[key]))
                    except ValueError:
                        pcs.append(0.0)
            data[line_id] = pcs
    return data

def get_common_lines(
    expr_data: Dict[str, Dict[str, float]],
    te_data: Dict[str, Dict[str, int]],
    pc_data: Dict[str, List[float]]
) -> List[str]:
    """
    Find line IDs that have data in all three datasets.
    """
    expr_lines = set()
    for gene_id, line_dict in expr_data.items():
        expr_lines.update(line_dict.keys())
    
    te_lines = set()
    for te_id, line_dict in te_data.items():
        te_lines.update(line_dict.keys())
    
    common = expr_lines.intersection(te_lines).intersection(pc_data.keys())
    return sorted(list(common))

def fit_replication_model(
    expr_values: List[float],
    te_values: List[int],
    pc_values: List[List[float]]
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """
    Fit the linear model: log2(expr) ~ TE + PC1 + PC2 + PC3
    Returns (effect_size, std_error, t_statistic) or (None, None, None) if fit fails.
    """
    n = len(expr_values)
    if n == 0:
        return None, None, None
    
    # Transform expression: log2(expr + 1e-6)
    y = [math.log2(v + 1e-6) for v in expr_values]
    
    # Design matrix: [1, TE, PC1, PC2, PC3]
    X = []
    for i in range(n):
        row = [1.0, float(te_values[i])]
        # Pad PC values if necessary
        for j in range(3):
            if j < len(pc_values[i]):
                row.append(pc_values[i][j])
            else:
                row.append(0.0)
        X.append(row)
    
    # Solve normal equations: (X'X) * beta = X'y
    XtX = [[0.0] * len(X[0]) for _ in range(len(X[0]))]
    Xty = [0.0] * len(X[0])
    
    for i in range(n):
        for j in range(len(X[0])):
            Xty[j] += X[i][j] * y[i]
            for k in range(len(X[0])):
                XtX[j][k] += X[i][j] * X[i][k]
    
    beta = solve_linear_system(XtX, Xty)
    if beta is None:
        return None, None, None
    
    # Calculate residuals and standard error
    y_pred = [sum(X[i][j] * beta[j] for j in range(len(beta))) for i in range(n)]
    residuals = [y[i] - y_pred[i] for i in range(n)]
    
    ss_res = sum(r * r for r in residuals)
    df = n - len(beta)
    if df <= 0:
        return None, None, None
    
    mse = ss_res / df
    
    # Calculate standard errors from (X'X)^-1
    XtX_inv = invert_matrix(XtX)
    if XtX_inv is None:
        return None, None, None
    
    # Effect size is beta[1] (TE coefficient)
    effect_size = beta[1]
    se_effect = math.sqrt(mse * XtX_inv[1][1]) if XtX_inv[1][1] > 0 else 0.0
    
    if se_effect == 0:
        t_stat = 0.0
    else:
        t_stat = effect_size / se_effect
    
    return effect_size, se_effect, t_stat

def load_significant_pairs(filepath: str) -> List[Dict[str, Any]]:
    """
    Load significant TE-gene pairs from the US1 results file.
    """
    pairs = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pairs.append(row)
    return pairs

def filter_significant_pairs_for_replication(
    pairs: List[Dict[str, Any]],
    expr_data: Dict[str, Dict[str, float]],
    te_data: Dict[str, Dict[str, int]],
    common_lines: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter pairs to those that have sufficient data in the replication dataset.
    """
    filtered = []
    for pair in pairs:
        te_id = pair['te_id']
        gene_id = pair['gene_id']
        
        # Check if TE and Gene exist in replication data
        if te_id not in te_data or gene_id not in expr_data:
            continue
        
        # Check if enough common lines exist
        te_lines = set(te_data[te_id].keys())
        gene_lines = set(expr_data[gene_id].keys())
        valid_lines = te_lines.intersection(gene_lines).intersection(set(common_lines))
        
        if len(valid_lines) >= 5:  # Minimum sample size
            filtered.append(pair)
    
    return filtered

def calculate_concordance(
    original_t: float,
    replication_t: float
) -> Tuple[bool, float]:
    """
    Calculate direction concordance and replication p-value.
    
    Returns:
        (is_concordant, replication_pvalue)
    """
    # Concordance: same sign of effect (t-statistic)
    is_concordant = (original_t > 0 and replication_t > 0) or (original_t < 0 and replication_t < 0)
    
    # Calculate two-tailed p-value for replication t-statistic
    # Assuming large enough df for normal approximation
    abs_t = abs(replication_t)
    # Using normal CDF approximation for p-value
    p_value = 2.0 * (1.0 - normal_cdf(abs_t))
    
    return is_concordant, p_value

def run_replication_analysis(
    original_results_path: str,
    replication_expr_path: str,
    replication_te_path: str,
    replication_pcs_path: str,
    output_path: str
) -> List[Dict[str, Any]]:
    """
    Run the full replication analysis pipeline.
    
    1. Load significant pairs from US1.
    2. Load replication datasets.
    3. Filter pairs with sufficient data.
    4. Fit model for each pair in replication data.
    5. Calculate concordance and p-values.
    6. Write results to output CSV.
    """
    logger = setup_logger('replication')
    logger.info("Starting replication analysis")
    
    # Load significant pairs
    significant_pairs = load_significant_pairs(original_results_path)
    logger.info(f"Loaded {len(significant_pairs)} significant pairs from US1")
    
    # Load replication data
    expr_data = load_replication_expression_data(replication_expr_path)
    te_data = load_replication_te_presence_data(replication_te_path)
    pc_data = load_replication_pcs_data(replication_pcs_path)
    
    common_lines = get_common_lines(expr_data, te_data, pc_data)
    logger.info(f"Found {len(common_lines)} common lines across all datasets")
    
    # Filter pairs
    valid_pairs = filter_significant_pairs_for_replication(
        significant_pairs, expr_data, te_data, common_lines
    )
    logger.info(f"Filtered to {len(valid_pairs)} pairs with sufficient data")
    
    results = []
    for pair in valid_pairs:
        te_id = pair['te_id']
        gene_id = pair['gene_id']
        original_effect = float(pair.get('effect_size', 0.0))
        original_t = float(pair.get('t_statistic', 0.0))
        
        # Extract values for common lines
        expr_vals = []
        te_vals = []
        pc_vals = []
        
        for line_id in common_lines:
            if line_id in te_data[te_id] and line_id in expr_data[gene_id]:
                expr_vals.append(expr_data[gene_id][line_id])
                te_vals.append(te_data[te_id][line_id])
                pc_vals.append(pc_data.get(line_id, [0.0, 0.0, 0.0]))
        
        if len(expr_vals) < 5:
            continue
        
        # Fit replication model
        rep_effect, rep_se, rep_t = fit_replication_model(expr_vals, te_vals, pc_vals)
        
        if rep_effect is None:
            continue
        
        # Calculate concordance and p-value
        is_concordant, rep_pvalue = calculate_concordance(original_t, rep_t)
        
        results.append({
            'te_id': te_id,
            'gene_id': gene_id,
            'original_effect_size': original_effect,
            'replication_effect_size': rep_effect,
            'concordance_flag': 'true' if is_concordant else 'false',
            'replication_p_value': rep_pvalue
        })
    
    # Write output
    ensure_directory(output_path)
    with open(output_path, 'w', newline='') as f:
        if results:
            fieldnames = [
                'te_id', 'gene_id', 'original_effect_size', 
                'replication_effect_size', 'concordance_flag', 'replication_p_value'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
    
    logger.info(f"Wrote {len(results)} replication results to {output_path}")
    return results

def main():
    """
    Main entry point for replication analysis.
    """
    logger = setup_logger('replication')
    set_random_seed(42)
    
    # Define paths (adjust as needed for project structure)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    original_results = os.path.join(project_root, 'data', 'results', 'association_results.csv')
    replication_expr = os.path.join(project_root, 'data', 'replication', 'expression_replication.csv')
    replication_te = os.path.join(project_root, 'data', 'replication', 'te_presence_replication.csv')
    replication_pcs = os.path.join(project_root, 'data', 'replication', 'pcs_replication.csv')
    output_file = os.path.join(project_root, 'data', 'results', 'replication_concordance.csv')
    
    if not os.path.exists(original_results):
        logger.error(f"Original results file not found: {original_results}")
        raise ReplicationError("Original results file not found")
    
    try:
        results = run_replication_analysis(
            original_results,
            replication_expr,
            replication_te,
            replication_pcs,
            output_file
        )
        logger.info(f"Replication analysis complete. {len(results)} pairs tested.")
    except Exception as e:
        logger.error(f"Replication analysis failed: {e}")
        raise ReplicationError(str(e))

if __name__ == '__main__':
    main()