import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Tuple, Optional, Dict, Any
import logging
from pathlib import Path
import networkx as nx
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

logger = logging.getLogger(__name__)

def welch_t_test(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    """
    Perform Welch's t-test between two independent groups.
    Returns (t_statistic, p_value).
    """
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
    return float(t_stat), float(p_val)

def fdr_correction_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    Returns list of q-values (adjusted p-values).
    """
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    ranks = np.arange(1, n + 1)
    q_values = np.zeros(n)
    
    # Calculate BH q-values
    for i in range(n):
        q_values[sorted_indices[i]] = sorted_p_values[i] * n / ranks[i]
    
    # Ensure monotonicity (cumulative min from right to left)
    for i in range(n - 2, -1, -1):
        q_values[sorted_indices[i]] = min(q_values[sorted_indices[i]], q_values[sorted_indices[i + 1]])
    
    # Cap at 1.0
    q_values = np.minimum(q_values, 1.0)
    
    return q_values.tolist()

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size.
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return float((mean1 - mean2) / pooled_std)

def calculate_confidence_interval(effect_size: float, group1: np.ndarray, group2: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for Cohen's d using bootstrapping.
    """
    n_boot = 1000
    n1, n2 = len(group1), len(group2)
    boot_dists = []
    
    for _ in range(n_boot):
        sample1 = np.random.choice(group1, n1, replace=True)
        sample2 = np.random.choice(group2, n2, replace=True)
        d = calculate_cohens_d(sample1, sample2)
        boot_dists.append(d)
    
    lower = np.percentile(boot_dists, (1 - confidence) / 2 * 100)
    upper = np.percentile(boot_dists, (1 + confidence) / 2 * 100)
    
    return float(lower), float(upper)

def network_based_statistic(
    connectivity_data: np.ndarray,
    group_labels: np.ndarray,
    edge_threshold: float = 0.05,
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform Network-Based Statistic (NBS) analysis.
    
    Parameters:
    - connectivity_data: np.ndarray of shape (n_subjects, n_rois, n_rois)
    - group_labels: np.ndarray of shape (n_subjects,) with 0/1 labels
    - edge_threshold: p-value threshold for edge selection (default 0.05)
    - n_permutations: number of permutations (default 1000)
    - seed: random seed for reproducibility
    
    Returns:
    - Dictionary containing:
      - 'component_size': size (number of edges) of the largest connected component
      - 'p_value': family-wise error rate corrected p-value
      - 'component_edges': list of (i, j) tuples representing edges in the component
    """
    if seed is not None:
        np.random.seed(seed)
    
    n_subjects, n_rois, _ = connectivity_data.shape
    group_labels = np.array(group_labels)
    
    # Flatten connectivity matrices to edge list (upper triangle only)
    triu_indices = np.triu_indices(n_rois, k=1)
    n_edges = len(triu_indices[0])
    
    # Reshape to (n_subjects, n_edges)
    edges_data = connectivity_data[:, triu_indices[0], triu_indices[1]]
    
    # Calculate t-statistic for each edge
    group0 = edges_data[group_labels == 0]
    group1 = edges_data[group_labels == 1]
    
    t_stats = np.zeros(n_edges)
    for i in range(n_edges):
        t_stat, _ = welch_t_test(group1[:, i], group0[:, i])
        t_stats[i] = t_stat
    
    # Select edges above threshold (absolute t-statistic)
    # We need to determine the critical t-value for the threshold
    # For simplicity, we use the p-value threshold directly on the t-stats
    # Convert p-value threshold to t-stat threshold using degrees of freedom
    df = n_subjects - 2
    t_threshold = stats.t.ppf(1 - edge_threshold / 2, df)
    
    # Select suprathreshold edges
    suprathreshold_mask = np.abs(t_stats) > t_threshold
    suprathreshold_indices = np.where(suprathreshold_mask)[0]
    
    # Build adjacency matrix of suprathreshold edges
    adj_matrix = np.zeros((n_rois, n_rois), dtype=bool)
    for idx in suprathreshold_indices:
        i, j = triu_indices[0][idx], triu_indices[1][idx]
        adj_matrix[i, j] = True
        adj_matrix[j, i] = True
    
    # Find connected components
    num_components, labels, component_sizes = connected_components(
        csr_matrix(adj_matrix.astype(int)), directed=False, return_labels=True
    )
    
    if num_components == 0:
        return {
            'component_size': 0,
            'p_value': 1.0,
            'component_edges': []
        }
    
    # Find largest component
    largest_component_label = np.argmax(np.bincount(labels))
    largest_component_mask = labels == largest_component_label
    
    # Get edges in largest component
    component_edges = []
    for idx in suprathreshold_indices:
        i, j = triu_indices[0][idx], triu_indices[1][idx]
        # Check if both nodes are in the largest component
        if labels[i] == largest_component_label and labels[j] == largest_component_label:
            component_edges.append((int(i), int(j)))
    
    observed_component_size = len(component_edges)
    
    # Permutation test
    max_component_sizes = []
    for perm in range(n_permutations):
        # Shuffle group labels
        shuffled_labels = np.random.permutation(group_labels)
        shuffled_group0 = edges_data[shuffled_labels == 0]
        shuffled_group1 = edges_data[shuffled_labels == 1]
        
        # Calculate t-stats for permuted data
        perm_t_stats = np.zeros(n_edges)
        for i in range(n_edges):
            t_stat, _ = welch_t_test(shuffled_group1[:, i], shuffled_group0[:, i])
            perm_t_stats[i] = t_stat
        
        # Select suprathreshold edges
        perm_suprathreshold_mask = np.abs(perm_t_stats) > t_threshold
        perm_suprathreshold_indices = np.where(perm_suprathreshold_mask)[0]
        
        if len(perm_suprathreshold_indices) == 0:
            max_component_sizes.append(0)
            continue
        
        # Build adjacency matrix
        perm_adj_matrix = np.zeros((n_rois, n_rois), dtype=bool)
        for idx in perm_suprathreshold_indices:
            i, j = triu_indices[0][idx], triu_indices[1][idx]
            perm_adj_matrix[i, j] = True
            perm_adj_matrix[j, i] = True
        
        # Find connected components
        perm_num_components, perm_labels, _ = connected_components(
            csr_matrix(perm_adj_matrix.astype(int)), directed=False, return_labels=True
        )
        
        if perm_num_components == 0:
            max_component_sizes.append(0)
            continue
        
        # Find largest component size
        perm_largest_label = np.argmax(np.bincount(perm_labels))
        perm_largest_size = np.sum(perm_labels == perm_largest_label)
        max_component_sizes.append(perm_largest_size)
    
    # Calculate p-value
    max_component_sizes = np.array(max_component_sizes)
    p_value = np.mean(max_component_sizes >= observed_component_size)
    
    return {
        'component_size': observed_component_size,
        'p_value': float(p_value),
        'component_edges': component_edges
    }

def process_connectivity_statistics(
    metrics_path: Path,
    output_path: Path,
    nbs_path: Optional[Path] = None,
    nbs_output_path: Optional[Path] = None
) -> None:
    """
    Process connectivity statistics: t-tests, FDR, effect sizes, and NBS.
    
    Parameters:
    - metrics_path: Path to network_metrics.csv
    - output_path: Path to write connectivity_results.csv
    - nbs_path: Path to connectivity_matrices.npy (for NBS)
    - nbs_output_path: Path to write nbs_results.csv
    """
    logger.info(f"Loading network metrics from {metrics_path}")
    df = pd.read_csv(metrics_path)
    
    # Load group labels from the data
    # Assuming the data has a 'group' column with 'musician' and 'non_musician'
    # We need to map these to 0/1
    group_map = {'non_musician': 0, 'musician': 1}
    df['group_numeric'] = df['group'].map(group_map)
    
    results = []
    p_values = []
    
    # Perform Welch's t-test for each connection
    for _, row in df.iterrows():
        connection_id = row['connection_id']
        group0_values = df[(df['group'] == 'non_musician') & (df['connection_id'] == connection_id)]['value'].values
        group1_values = df[(df['group'] == 'musician') & (df['connection_id'] == connection_id)]['value'].values
        
        if len(group0_values) == 0 or len(group1_values) == 0:
            continue
        
        t_stat, p_val = welch_t_test(group1_values, group0_values)
        cohens_d = calculate_cohens_d(group1_values, group0_values)
        ci_lower, ci_upper = calculate_confidence_interval(cohens_d, group1_values, group0_values)
        
        results.append({
            'connection_id': connection_id,
            't_stat': t_stat,
            'p_value': p_val,
            'effect_size': cohens_d,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        })
        p_values.append(p_val)
    
    # Apply FDR correction
    q_values = fdr_correction_benjamini_hochberg(p_values)
    for i, q_val in enumerate(q_values):
        results[i]['q_value'] = q_val
    
    # Write results
    results_df = pd.DataFrame(results)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Wrote connectivity results to {output_path}")
    
    # Run NBS if matrices are provided
    if nbs_path and nbs_output_path:
        logger.info(f"Running NBS on {nbs_path}")
        # Load connectivity matrices
        conn_matrices = np.load(nbs_path)
        
        # Get group labels
        group_labels = df['group_numeric'].values
        
        # Run NBS
        nbs_results = network_based_statistic(
            conn_matrices,
            group_labels,
            edge_threshold=0.05,
            n_permutations=1000
        )
        
        # Write NBS results
        nbs_df = pd.DataFrame([nbs_results])
        nbs_df.to_csv(nbs_output_path, index=False)
        logger.info(f"Wrote NBS results to {nbs_output_path}")

def main():
    """Main entry point for stats analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Perform connectivity statistics and NBS")
    parser.add_argument("--metrics", type=str, required=True, help="Path to network_metrics.csv")
    parser.add_argument("--output", type=str, required=True, help="Path to output connectivity_results.csv")
    parser.add_argument("--matrices", type=str, default=None, help="Path to connectivity_matrices.npy")
    parser.add_argument("--nbs-output", type=str, default=None, help="Path to output nbs_results.csv")
    
    args = parser.parse_args()
    
    metrics_path = Path(args.metrics)
    output_path = Path(args.output)
    nbs_path = Path(args.matrices) if args.matrices else None
    nbs_output_path = Path(args.nbs_output) if args.nbs_output else None
    
    process_connectivity_statistics(metrics_path, output_path, nbs_path, nbs_output_path)

if __name__ == "__main__":
    main()
