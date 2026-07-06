import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Tuple, Optional, Dict, Any
import logging
from utils.logging import get_logger

logger = get_logger(__name__)

def welch_t_test(group1: np.ndarray, group2: np.ndarray) -> Tuple[float, float]:
    """
    Perform Welch's t-test between two independent groups.
    
    Args:
        group1: Array of values for group 1 (e.g., musicians)
        group2: Array of values for group 2 (e.g., non-musicians)
        
    Returns:
        Tuple of (t_statistic, p_value)
    """
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
    return float(t_stat), float(p_val)

def fdr_correction_benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default 0.05)
        
    Returns:
        List of adjusted q-values
    """
    p_values = np.array(p_values)
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]
    
    # Calculate BH critical values
    rank = np.arange(1, n + 1)
    bh_thresholds = (rank / n) * alpha
    
    # Find the largest k where p_(k) <= threshold_(k)
    # and set all p-values with rank <= k to their adjusted values
    adjusted_p_values = np.zeros(n)
    for i in range(n - 1, -1, -1):
        adjusted_p_values[sorted_indices[i]] = min(
            (n / (i + 1)) * sorted_p_values[i],
            1.0
        )
    
    # Ensure monotonicity (adjusted p-values should be non-decreasing with rank)
    for i in range(1, n):
        adjusted_p_values[sorted_indices[i]] = min(
            adjusted_p_values[sorted_indices[i]],
            adjusted_p_values[sorted_indices[i-1]]
        )
        
    return adjusted_p_values.tolist()

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: Array of values for group 1
        group2: Array of values for group 2
        
    Returns:
        Cohen's d value
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return float((mean1 - mean2) / pooled_std)

def calculate_confidence_interval(effect_size: float, group1: np.ndarray, group2: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% confidence interval for Cohen's d.
    
    Args:
        effect_size: Cohen's d value
        group1: Array of values for group 1
        group2: Array of values for group 2
        confidence: Confidence level (default 0.95)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    n1, n2 = len(group1), len(group2)
    h = (n1 + n2) / (n1 * n2)
    d = effect_size
    
    # Approximate standard error of Cohen's d
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2 - 2)))
    
    # Critical t-value
    df = n1 + n2 - 2
    t_crit = stats.t.ppf((1 + confidence) / 2, df)
    
    lower = d - t_crit * se_d
    upper = d + t_crit * se_d
    
    return float(lower), float(upper)

def network_based_statistic(
    group1_matrices: List[np.ndarray],
    group2_matrices: List[np.ndarray],
    edge_threshold: float = 0.05,
    n_permutations: int = 1000,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform Network-Based Statistic (NBS) to identify connected components
    of edges showing significant group differences.
    
    This is a permutation-based method that controls the family-wise error
    rate at the component level rather than the edge level.
    
    Args:
        group1_matrices: List of connectivity matrices for group 1 (musicians)
        group2_matrices: List of connectivity matrices for group 2 (non-musicians)
        edge_threshold: Primary edge threshold for forming components (default 0.05)
        n_permutations: Number of permutations to run (default 1000)
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing:
            - 'component_sizes': List of sizes (number of edges) for each component
            - 'component_p_values': List of p-values for each component
            - 'largest_component_size': Size of the largest connected component
            - 'largest_component_p_value': P-value for the largest component
            - 'edge_threshold': The threshold used
            - 'n_permutations': Number of permutations run
    """
    if seed is not None:
        np.random.seed(seed)
        
    n1 = len(group1_matrices)
    n2 = len(group2_matrices)
    
    if n1 == 0 or n2 == 0:
        raise ValueError("Both groups must have at least one subject")
        
    if not group1_matrices or not group2_matrices:
        raise ValueError("Connectivity matrices cannot be empty")
        
    # Verify matrices are square and of same size
    n_rois = group1_matrices[0].shape[0]
    for mat in group1_matrices + group2_matrices:
        if mat.shape != (n_rois, n_rois):
            raise ValueError(f"All matrices must be {n_rois}x{n_rois}")
    
    logger.info(f"Running NBS with {n1} subjects in group 1, {n2} in group 2")
    logger.info(f"Edge threshold: {edge_threshold}, Permutations: {n_permutations}")
    
    # Stack all matrices
    all_matrices = group1_matrices + group2_matrices
    n_subjects = len(all_matrices)
    
    # Compute the test statistic for each edge (t-statistic)
    # We use the absolute difference of means divided by pooled std (similar to t-stat)
    # For NBS, we typically use the t-statistic directly
    
    # Reshape to (n_subjects, n_edges) where n_edges = n_rois * (n_rois - 1) / 2
    n_edges = n_rois * (n_rois - 1) // 2
    edge_indices = np.triu_indices(n_rois, k=1)
    
    # Flatten matrices to edge vectors
    subject_edge_vectors = []
    for mat in all_matrices:
        # Extract upper triangle (excluding diagonal)
        edge_vec = mat[edge_indices]
        subject_edge_vectors.append(edge_vec)
        
    subject_edge_vectors = np.array(subject_edge_vectors)  # Shape: (n_subjects, n_edges)
    
    # Split into groups
    group1_edges = subject_edge_vectors[:n1]
    group2_edges = subject_edge_vectors[n1:]
    
    # Compute observed t-statistics for each edge
    observed_t_stats = np.zeros(n_edges)
    for i in range(n_edges):
        t_stat, _ = welch_t_test(group1_edges[:, i], group2_edges[:, i])
        observed_t_stats[i] = t_stat
        
    # Threshold the observed statistics
    # We use the absolute value for thresholding
    thresholded_obs = np.abs(observed_t_stats) > np.abs(stats.t.ppf(edge_threshold / 2, n1 + n2 - 2))
    
    # Find connected components in the thresholded graph
    # We'll use a simple BFS to find components
    def find_components(thresholded_adj, n_nodes):
        """Find connected components in a thresholded adjacency matrix."""
        # thresholded_adj is a boolean mask of significant edges
        visited = np.zeros(n_nodes, dtype=bool)
        components = []
        
        for start_node in range(n_nodes):
            if visited[start_node]:
                continue
                
            # BFS to find all nodes in this component
            component_nodes = []
            queue = [start_node]
            visited[start_node] = True
            
            while queue:
                node = queue.pop(0)
                component_nodes.append(node)
                
                # Find all connected nodes
                for neighbor in range(n_nodes):
                    if neighbor != node and not visited[neighbor]:
                        # Check if edge exists (in either direction)
                        edge_idx = np.where((edge_indices[0] == min(node, neighbor)) & 
                                            (edge_indices[1] == max(node, neighbor)))[0]
                        if len(edge_idx) > 0 and thresholded_adj[edge_idx[0]]:
                            visited[neighbor] = True
                            queue.append(neighbor)
            
            if len(component_nodes) > 0:
                # Count edges in this component
                edge_count = 0
                for i, node1 in enumerate(component_nodes):
                    for node2 in component_nodes[i+1:]:
                        edge_idx = np.where((edge_indices[0] == min(node1, node2)) & 
                                            (edge_indices[1] == max(node1, node2)))[0]
                        if len(edge_idx) > 0 and thresholded_adj[edge_idx[0]]:
                            edge_count += 1
                
                if edge_count > 0:
                    components.append(edge_count)
                    
        return components
    
    # Find components in observed data
    observed_components = find_components(thresholded_obs, n_rois)
    observed_max_component_size = max(observed_components) if observed_components else 0
    
    logger.info(f"Observed largest component size: {observed_max_component_size}")
    
    # Permutation testing
    perm_max_component_sizes = np.zeros(n_permutations)
    
    for perm in range(n_permutations):
        if (perm + 1) % 100 == 0:
            logger.info(f"Permutation {perm + 1}/{n_permutations}")
            
        # Randomly shuffle group labels
        shuffled_indices = np.random.permutation(n_subjects)
        shuffled_group1_edges = subject_edge_vectors[shuffled_indices[:n1]]
        shuffled_group2_edges = subject_edge_vectors[shuffled_indices[n1:]]
        
        # Compute t-statistics for permuted data
        perm_t_stats = np.zeros(n_edges)
        for i in range(n_edges):
            t_stat, _ = welch_t_test(shuffled_group1_edges[:, i], shuffled_group2_edges[:, i])
            perm_t_stats[i] = t_stat
            
        # Threshold
        perm_thresholded = np.abs(perm_t_stats) > np.abs(stats.t.ppf(edge_threshold / 2, n1 + n2 - 2))
        
        # Find components
        perm_components = find_components(perm_thresholded, n_rois)
        perm_max_component_sizes[perm] = max(perm_components) if perm_components else 0
        
    # Calculate p-values for observed components
    # For each observed component size, calculate the proportion of permuted
    # max component sizes that are >= the observed size
    component_p_values = []
    for comp_size in observed_components:
        p_val = (np.sum(perm_max_component_sizes >= comp_size) + 1) / (n_permutations + 1)
        component_p_values.append(float(p_val))
        
    # Identify significant components (p < 0.05)
    significant_components = [
        (size, p_val) for size, p_val in zip(observed_components, component_p_values)
        if p_val < 0.05
    ]
    
    largest_component_size = observed_max_component_size
    largest_component_p_value = component_p_values[0] if component_p_values else 1.0
    
    # If there are multiple components, find the largest significant one
    if significant_components:
        largest_sig_component = max(significant_components, key=lambda x: x[0])
        largest_component_size = largest_sig_component[0]
        largest_component_p_value = largest_sig_component[1]
    
    logger.info(f"NBS completed. Largest component size: {largest_component_size}, p-value: {largest_component_p_value}")
    
    return {
        'component_sizes': observed_components,
        'component_p_values': component_p_values,
        'largest_component_size': largest_component_size,
        'largest_component_p_value': largest_component_p_value,
        'edge_threshold': edge_threshold,
        'n_permutations': n_permutations,
        'significant_components': significant_components
    }

def process_connectivity_statistics(
    connectivity_df: pd.DataFrame,
    group_col: str = 'group',
    subject_col: str = 'subject_id',
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Process connectivity statistics for group comparison.
    
    This function computes t-tests, FDR correction, and effect sizes
    for each connection in the dataset.
    
    Args:
        connectivity_df: DataFrame with connectivity data
        group_col: Name of the column containing group labels
        subject_col: Name of the column containing subject IDs
        output_path: Optional path to save results
        
    Returns:
        DataFrame with statistical results
    """
    logger.info("Processing connectivity statistics")
    
    # Identify musician and non-musician groups
    musicians = connectivity_df[connectivity_df[group_col] == 'musician']
    non_musicians = connectivity_df[connectivity_df[group_col] == 'non_musician']
    
    logger.info(f"Found {len(musicians)} musicians and {len(non_musicians)} non-musicians")
    
    # Initialize results dataframe
    results = []
    
    # Iterate through each connection (assuming columns are connection_1, connection_2, etc.)
    connection_cols = [col for col in connectivity_df.columns if col.startswith('connection_')]
    
    if not connection_cols:
        logger.warning("No connection columns found in the dataframe")
        return pd.DataFrame()
    
    for conn_col in connection_cols:
        group1_vals = musicians[conn_col].values
        group2_vals = non_musicians[conn_col].values
        
        if len(group1_vals) == 0 or len(group2_vals) == 0:
            continue
            
        # Welch's t-test
        t_stat, p_val = welch_t_test(group1_vals, group2_vals)
        
        # Cohen's d
        cohens_d = calculate_cohens_d(group1_vals, group2_vals)
        
        # Confidence interval
        ci_lower, ci_upper = calculate_confidence_interval(cohens_d, group1_vals, group2_vals)
        
        results.append({
            'connection_id': conn_col,
            't_stat': t_stat,
            'p_value': p_val,
            'effect_size': cohens_d,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        })
    
    results_df = pd.DataFrame(results)
    
    if not results_df.empty:
        # FDR correction
        results_df['q_value'] = fdr_correction_benjamini_hochberg(results_df['p_value'].tolist())
    
    if output_path:
        results_df.to_csv(output_path, index=False)
        logger.info(f"Results saved to {output_path}")
        
    return results_df

def main():
    """
    Main entry point for running statistical analysis on connectivity data.
    This function can be extended to run NBS or other advanced analyses.
    """
    logger.info("Starting connectivity statistics analysis")
    
    # Example usage of NBS (requires connectivity matrices, not just summary stats)
    # This would typically be called with actual matrix data from the preprocessing pipeline
    logger.info("NBS implementation ready. Call network_based_statistic() with matrix data.")
    
    if __name__ == "__main__":
        # Example test with synthetic data
        np.random.seed(42)
        n1, n2 = 20, 20
        n_rois = 10
        
        # Generate synthetic connectivity matrices
        group1_mats = [np.random.randn(n_rois, n_rois) * 0.1 for _ in range(n1)]
        group2_mats = [np.random.randn(n_rois, n_rois) * 0.1 for _ in range(n2)]
        
        # Run NBS
        result = network_based_statistic(
            group1_mats, 
            group2_mats, 
            edge_threshold=0.05, 
            n_permutations=100
        )
        
        logger.info(f"NBS Result: Largest component size = {result['largest_component_size']}, p-value = {result['largest_component_p_value']}")

if __name__ == "__main__":
    main()
