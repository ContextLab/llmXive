import os
import csv
import logging
import math
from typing import List, Dict, Tuple, Optional, Any
from utils import setup_logger, ensure_directory, set_random_seed

# Custom exceptions
class AssociationError(Exception):
    """Custom exception for association analysis errors."""
    pass

# --- Data Loading Helpers ---

def load_expression_data(filepath: str) -> Dict[str, List[float]]:
    """
    Load gene expression TPM matrix from CSV.
    Returns: { gene_id: [line1_tpm, line2_tpm, ...] }
    """
    data = {}
    if not os.path.exists(filepath):
        raise AssociationError(f"Expression data file not found: {filepath}")
    
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        if 'gene_id' not in reader.fieldnames:
            raise AssociationError("Expression CSV missing 'gene_id' column")
        
        # Assume remaining columns are line IDs (sample names)
        lines = [col for col in reader.fieldnames if col != 'gene_id']
        
        for row in reader:
            gene_id = row['gene_id']
            vals = []
            for line in lines:
                val_str = row.get(line, '0')
                try:
                    vals.append(float(val_str))
                except ValueError:
                    vals.append(0.0)
            data[gene_id] = vals
    return data

def load_te_presence_data(filepath: str) -> Dict[str, List[int]]:
    """
    Load TE presence/absence matrix from CSV.
    Returns: { te_id: [line1_present, line2_present, ...] }
    """
    data = {}
    if not os.path.exists(filepath):
        raise AssociationError(f"TE presence data file not found: {filepath}")
    
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        if 'te_id' not in reader.fieldnames:
            raise AssociationError("TE presence CSV missing 'te_id' column")
        
        lines = [col for col in reader.fieldnames if col != 'te_id']
        
        for row in reader:
            te_id = row['te_id']
            vals = []
            for line in lines:
                val_str = row.get(line, '0')
                try:
                    # Ensure binary 0/1
                    vals.append(1 if int(float(val_str)) > 0 else 0)
                except ValueError:
                    vals.append(0)
            data[te_id] = vals
    return data

def load_pcs_data(filepath: str) -> Dict[str, List[float]]:
    """
    Load population PCs from CSV.
    Returns: { pc_name: [line1_val, line2_val, ...] }
    """
    data = {}
    if not os.path.exists(filepath):
        raise AssociationError(f"PCs data file not found: {filepath}")
    
    # Re-implementation for standard row-per-sample format
    pc_names = []
    pcs = {}
    
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or 'sample_id' not in reader.fieldnames:
            raise AssociationError("PCs CSV must contain 'sample_id' column")
        
        pc_names = [col for col in reader.fieldnames if col != 'sample_id']
        
        for row in reader:
            for pc in pc_names:
                val_str = row.get(pc, '0')
                try:
                    val = float(val_str)
                except ValueError:
                    val = 0.0
                if pc not in pcs:
                    pcs[pc] = []
                pcs[pc].append(val)
    
    return pcs

# --- Math Helpers ---

def solve_linear_system(X: List[List[float]], y: List[float]) -> Optional[List[float]]:
    """
    Solve (X^T X) beta = X^T y using Gaussian elimination.
    X is list of rows.
    """
    n = len(y)
    k = len(X[0]) if X else 0
    
    # Construct X^T X (k x k)
    XtX = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            sum_val = 0.0
            for m in range(n):
                sum_val += X[m][i] * X[m][j]
            XtX[i][j] = sum_val
    
    # Construct X^T y (k x 1)
    Xty = [0.0] * k
    for i in range(k):
        sum_val = 0.0
        for m in range(n):
            sum_val += X[m][i] * y[m]
        Xty[i] = sum_val
    
    # Augmented matrix
    aug = [XtX[i] + [Xty[i]] for i in range(k)]
    
    # Gaussian elimination with partial pivoting
    for i in range(k):
        # Pivot
        max_row = i
        for r in range(i + 1, k):
            if abs(aug[r][i]) > abs(aug[max_row][i]):
                max_row = r
        aug[i], aug[max_row] = aug[max_row], aug[i]
        
        if abs(aug[i][i]) < 1e-10:
            # Singular matrix
            return None
        
        # Eliminate
        for r in range(i + 1, k):
            factor = aug[r][i] / aug[i][i]
            for c in range(i, k + 1):
                aug[r][c] -= factor * aug[i][c]
    
    # Back substitution
    beta = [0.0] * k
    for i in range(k - 1, -1, -1):
        sum_val = aug[i][k]
        for j in range(i + 1, k):
            sum_val -= aug[i][j] * beta[j]
        beta[i] = sum_val / aug[i][i]
    
    return beta

def normal_cdf(x: float) -> float:
    """Approximation of the standard normal CDF."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def fit_linear_model_simple(X: List[List[float]], y: List[float]) -> Tuple[Optional[List[float]], float]:
    """
    Fit linear model y = X beta.
    Returns (beta, r_squared) or (None, 0.0) if singular.
    """
    beta = solve_linear_system(X, y)
    if beta is None:
        return None, 0.0
    
    n = len(y)
    # Predictions
    y_pred = []
    for row in X:
        val = sum(b * x for b, x in zip(beta, row))
        y_pred.append(val)
    
    # R-squared
    y_mean = sum(y) / n
    ss_tot = sum((yi - y_mean) ** 2 for yi in y)
    ss_res = sum((yi - yp) ** 2 for yi, yp in zip(y, y_pred))
    
    r_sq = 0.0
    if ss_tot > 1e-10:
        r_sq = 1.0 - (ss_res / ss_tot)
    
    return beta, r_sq

def run_association_test(gene_expr: List[float], te_presence: List[int], pcs: List[List[float]]) -> Dict[str, Any]:
    """
    Run a single association test: log2(expr) ~ TE + PC1 + PC2 + PC3.
    Returns dict with effect_size, p_value, r_squared.
    """
    n = len(gene_expr)
    if n != len(te_presence) or n != len(pcs[0]):
        raise AssociationError("Dimension mismatch in association test inputs")
    
    # Log2 transform (add small constant to avoid log(0))
    y = [math.log2(x + 1e-6) for x in gene_expr]
    
    # Construct design matrix X: [1, TE, PC1, PC2, PC3]
    X = []
    for i in range(n):
        row = [1.0, float(te_presence[i])]
        for pc_vec in pcs:
            row.append(pc_vec[i])
        X.append(row)
    
    beta, r_sq = fit_linear_model_simple(X, y)
    
    if beta is None:
        return {
            'effect_size': 0.0,
            'p_value': 1.0,
            'r_squared': 0.0,
            'success': False
        }
    
    # Calculate t-statistic for TE coefficient (beta[1])
    y_pred = [sum(b * x for b, x in zip(beta, row)) for row in X]
    residuals = [yi - yp for yi, yp in zip(y, y_pred)]
    
    df = n - len(beta)
    if df <= 0:
        return {'effect_size': beta[1], 'p_value': 1.0, 'r_squared': r_sq, 'success': False}
    
    rss = sum(r ** 2 for r in residuals)
    sigma_sq = rss / df
    
    # Compute (X^T X)^-1 element [1][1] via Gauss-Jordan
    k = len(beta)
    XtX = [[0.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(k):
            sum_val = 0.0
            for m in range(n):
                sum_val += X[m][i] * X[m][j]
            XtX[i][j] = sum_val
    
    # Augment with identity
    aug = [XtX[i] + [1.0 if i == j else 0.0 for j in range(k)] for i in range(k)]
    
    # Gauss-Jordan elimination
    for i in range(k):
        max_row = i
        for r in range(i + 1, k):
            if abs(aug[r][i]) > abs(aug[max_row][i]):
                max_row = r
        aug[i], aug[max_row] = aug[max_row], aug[i]
        
        if abs(aug[i][i]) < 1e-12:
            return {'effect_size': beta[1], 'p_value': 1.0, 'r_squared': r_sq, 'success': False}
        
        factor = aug[i][i]
        for c in range(2 * k):
            aug[i][c] /= factor
        
        for r in range(k):
            if r != i:
                factor = aug[r][i]
                for c in range(2 * k):
                    aug[r][c] -= factor * aug[i][c]
    
    XtX_inv = [aug[i][k:] for i in range(k)]
    
    var_beta1 = XtX_inv[1][1] * sigma_sq
    se_beta1 = math.sqrt(var_beta1) if var_beta1 > 0 else 1e-9
    
    t_stat = beta[1] / se_beta1 if se_beta1 > 1e-12 else 0.0
    
    p_val = 2.0 * (1.0 - normal_cdf(abs(t_stat)))
    
    return {
        'effect_size': beta[1],
        'p_value': p_val,
        'r_squared': r_sq,
        't_statistic': t_stat,
        'success': True
    }

# --- Core Task Implementation: T011 ---

def apply_bh_correction(results: List[Dict[str, Any]], threshold: float = 0.05) -> List[Dict[str, Any]]:
    """
    Apply Benjamini-Hochberg correction to a list of results.
    Filters for FDR < threshold.
    
    Input results must contain 'p_value' and 'te_id', 'gene_id'.
    Returns a new list containing only significant pairs, with 'adj_p_value' added.
    """
    if not results:
        return []
    
    indexed_results = [(i, r) for i, r in enumerate(results)]
    sorted_results = sorted(indexed_results, key=lambda x: x[1]['p_value'])
    
    n = len(sorted_results)
    cutoff_idx = -1
    
    for rank, (orig_idx, res) in enumerate(sorted_results, 1):
        p_val = res['p_value']
        if p_val <= (rank / n) * threshold:
            cutoff_idx = rank
    
    if cutoff_idx <= 0:
        return []
    
    # Compute raw adjusted p-values
    adj_p_values = {}
    for rank, (orig_idx, res) in enumerate(sorted_results, 1):
        adj_p = res['p_value'] * n / rank
        adj_p_values[orig_idx] = adj_p
    
    # Enforce monotonicity (backwards)
    monotonic_adj = [0.0] * n
    current_min = 1.0
    for i in range(n - 1, -1, -1):
        orig_idx = sorted_results[i][0]
        raw_adj = adj_p_values[orig_idx]
        current_min = min(current_min, raw_adj)
        monotonic_adj[i] = current_min
    
    output = []
    for i in range(n):
        orig_idx, res = sorted_results[i]
        adj_p = monotonic_adj[i]
        if adj_p < threshold:
            res_copy = res.copy()
            res_copy['adj_p_value'] = adj_p
            output.append(res_copy)
    
    output.sort(key=lambda x: x['adj_p_value'])
    return output

def calculate_vif_for_pair(te_vec: List[int], pcs: List[List[float]]) -> float:
    """
    Calculate VIF for a specific TE against the set of PCs.
    VIF_j = 1 / (1 - R_j^2) where R_j^2 is from regressing TE on PCs.
    """
    n = len(te_vec)
    k = len(pcs)
    
    X = []
    for i in range(n):
        row = [1.0]
        for pc in pcs:
            row.append(pc[i])
        X.append(row)
    
    y = [float(x) for x in te_vec]
    
    beta, r_sq = fit_linear_model_simple(X, y)
    
    if beta is None:
        return float('inf')
    
    if r_sq >= 1.0 - 1e-10:
        return float('inf')
    
    return 1.0 / (1.0 - r_sq)

def run_full_association_analysis(expr_data: Dict[str, List[float]], 
                                  te_data: Dict[str, List[int]], 
                                  pcs: Dict[str, List[float]],
                                  te_gene_pairs: List[Tuple[str, str]]) -> List[Dict[str, Any]]:
    """
    Run association tests for all pairs and apply BH correction.
    """
    logger = setup_logger(__name__)
    results = []
    
    # Extract PC vectors in order
    pc_names = sorted([k for k in pcs.keys() if k.startswith('PC')])
    pc_vectors = [pcs[p] for p in pc_names]
    
    for te_id, gene_id in te_gene_pairs:
        if te_id not in te_data or gene_id not in expr_data:
            continue
        
        te_vec = te_data[te_id]
        expr_vec = expr_data[gene_id]
        
        # Simple missing data check
        valid = True
        for val in expr_vec:
            if val <= 0 or math.isnan(val):
                valid = False
                break
        
        if not valid:
            continue
        
        try:
            res = run_association_test(expr_vec, te_vec, pc_vectors)
            if res['success']:
                res['te_id'] = te_id
                res['gene_id'] = gene_id
                results.append(res)
        except Exception as e:
            logger.warning(f"Association test failed for {te_id}-{gene_id}: {e}")
    
    # Apply BH correction
    significant_results = apply_bh_correction(results, threshold=0.05)
    return significant_results

def generate_empty_output_table() -> List[Dict[str, Any]]:
    """
    Generate an empty list with the correct schema for output.
    """
    return []

# --- New Functionality for T012: Population Structure Control Metrics ---

def compute_population_structure_control_metrics(
    expr_data: Dict[str, List[float]],
    pcs: Dict[str, List[float]]
) -> List[Dict[str, Any]]:
    """
    For each gene, compute R² with PCs (intercept + PC1-3) and without PCs
    (intercept only). Return a list of dictionaries with:
    gene_id, r2_with_pcs, r2_without_pcs, reduction_percent.
    
    reduction_percent is defined as:
        ((r2_with_pcs - r2_without_pcs) / r2_without_pcs) * 100
    with the edge‑case handling that if r2_without_pcs == 0,
    reduction_percent is set to 0.0 to avoid division‑by‑zero.
    """
    metrics = []
    # Prepare PC vectors in deterministic order
    pc_names = sorted([k for k in pcs.keys() if k.startswith('PC')])
    pc_vectors = [pcs[p] for p in pc_names]
    
    for gene_id, expr_vec in expr_data.items():
        n = len(expr_vec)
        
        # Design matrix with PCs
        X_with = []
        for i in range(n):
            row = [1.0]
            for pc_vec in pc_vectors:
                row.append(pc_vec[i])
            X_with.append(row)
        
        _, r2_with = fit_linear_model_simple(X_with, expr_vec)
        
        # Design matrix without PCs (intercept only)
        X_without = [[1.0] for _ in range(n)]
        _, r2_without = fit_linear_model_simple(X_without, expr_vec)
        
        if r2_without == 0.0:
            reduction = 0.0
        else:
            reduction = ((r2_with - r2_without) / r2_without) * 100.0
        
        metrics.append({
            'gene_id': gene_id,
            'r2_with_pcs': r2_with,
            'r2_without_pcs': r2_without,
            'reduction_percent': reduction
        })
    
    return metrics

def main():
    """
    Entry point for association analysis pipeline.
    Loads mock data, runs analysis, applies BH correction, writes results,
    and computes population‑structure control metrics.
    """
    logger = setup_logger(__name__)
    logger.info("Starting Association Analysis Pipeline (T011: BH Correction)")
    
    # Paths
    expr_path = "data/mock_expression.csv"
    te_path = "data/mock_te_presence.csv"
    pc_path = "data/mock/population_pcs.csv"
    pair_path = "data/preprocessed_te_gene_pairs.csv"  # Assumed output of T019
    out_path = "data/results/association_results_bh.csv"
    metrics_path = "data/results/population_structure_control_metrics.csv"
    
    ensure_directory(out_path)
    ensure_directory(metrics_path)
    
    try:
        # Load Data
        logger.info("Loading expression data...")
        expr_data = load_expression_data(expr_path)
        logger.info("Loading TE presence data...")
        te_data = load_te_presence_data(te_path)
        logger.info("Loading PCs...")
        pcs = load_pcs_data(pc_path)
        
        # Load Pairs
        pairs = []
        if os.path.exists(pair_path):
            with open(pair_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pairs.append((row['te_id'], row['gene_id']))
        else:
            logger.warning("Pair file not found. Generating dummy pair for demo.")
            if expr_data and te_data:
                g = list(expr_data.keys())[0]
                t = list(te_data.keys())[0]
                pairs = [(t, g)]
        
        logger.info(f"Running {len(pairs)} association tests...")
        results = run_full_association_analysis(expr_data, te_data, pcs, pairs)
        
        logger.info(f"Found {len(results)} significant pairs (FDR < 0.05)")
        
        # Write Association Results
        if results:
            fieldnames = ['te_id', 'gene_id', 'effect_size', 'p_value',
                         'adj_p_value', 'r_squared', 't_statistic']
            with open(out_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in results:
                    writer.writerow({k: r.get(k, '') for k in fieldnames})
            logger.info(f"Association results written to {out_path}")
        else:
            logger.info("No significant pairs found. Writing empty table.")
            fieldnames = ['te_id', 'gene_id', 'effect_size', 'p_value',
                         'adj_p_value', 'r_squared', 't_statistic']
            with open(out_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        
        # Compute and Write Population Structure Control Metrics
        logger.info("Computing population structure control metrics per gene...")
        metrics = compute_population_structure_control_metrics(expr_data, pcs)
        
        metric_fieldnames = ['gene_id', 'r2_with_pcs', 'r2_without_pcs', 'reduction_percent']
        with open(metrics_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=metric_fieldnames)
            writer.writeheader()
            for m in metrics:
                writer.writerow(m)
        
        logger.info(f"Population structure metrics written to {metrics_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
