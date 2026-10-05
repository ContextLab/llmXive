import os
import sys
import numpy as np
import pandas as pd
import logging
from pathlib import Path

from utils.logging import get_logger
from utils.memory_monitor import check_memory_limit, MemoryLimitExceeded

logger = get_logger(__name__)

def load_connectivity_matrices(
    input_path: str = "data/processed/connectivity_matrices.npy",
    subject_labels_path: str = "data/processed/subjects_cleaned.csv"
) -> tuple:
    """
    Load connectivity matrices and subject labels.
    
    Args:
        input_path: Path to connectivity matrices numpy file.
        subject_labels_path: Path to subject labels CSV.
        
    Returns:
        Tuple of (matrices, subject_df, musician_indices, non_musician_indices)
    """
    logger.info(f"Loading connectivity matrices from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Connectivity matrices not found: {input_path}")
        
    matrices = np.load(input_path, mmap_mode='r')
    logger.info(f"Loaded matrices with shape: {matrices.shape}")
    
    if not os.path.exists(subject_labels_path):
        raise FileNotFoundError(f"Subject labels not found: {subject_labels_path}")
        
    subject_df = pd.read_csv(subject_labels_path)
    
    # Separate groups
    musician_indices = subject_df[subject_df['group'] == 'musician'].index.tolist()
    non_musician_indices = subject_df[subject_df['group'] == 'non_musician'].index.tolist()
    
    logger.info(f"Found {len(musician_indices)} musicians and {len(non_musician_indices)} non-musicians")
    
    return matrices, subject_df, musician_indices, non_musician_indices

def network_based_statistic(
    matrices: np.ndarray,
    group1_indices: list,
    group2_indices: list,
    n_permutations: int = 1000,
    edge_threshold: float = 0.05,
    seed: int = 42
) -> dict:
    """
    Perform Network-Based Statistic (NBS) analysis.
    
    This is a simplified implementation for demonstration purposes.
    In a real scenario, this would use the nbspy library or similar.
    
    Args:
        matrices: 3D array of connectivity matrices [n_subjects, n_rois, n_rois]
        group1_indices: Indices of subjects in group 1 (musicians)
        group2_indices: Indices of subjects in group 2 (non-musicians)
        n_permutations: Number of permutations for NBS
        edge_threshold: Threshold for edge significance
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing NBS results
    """
    np.random.seed(seed)
    
    n_subjects, n_rois, _ = matrices.shape
    
    # Compute t-statistic for each edge
    group1_matrices = matrices[group1_indices]
    group2_matrices = matrices[group2_indices]
    
    # Mean connectivity for each group
    mean1 = np.mean(group1_matrices, axis=0)
    mean2 = np.mean(group2_matrices, axis=0)
    
    # Standard deviation for each group
    std1 = np.std(group1_matrices, axis=0, ddof=1)
    std2 = np.std(group2_matrices, axis=0, ddof=1)
    
    # Welch's t-test approximation
    n1 = len(group1_indices)
    n2 = len(group2_indices)
    
    # Avoid division by zero
    std1 = np.where(std1 == 0, 1e-10, std1)
    std2 = np.where(std2 == 0, 1e-10, std2)
    
    t_stat = (mean1 - mean2) / np.sqrt((std1**2 / n1) + (std2**2 / n2))
    
    # Create adjacency matrix of significant edges
    p_values = 2 * (1 - scipy_stats.cdf(np.abs(t_stat), df=min(n1, n2)))
    significant_edges = p_values < edge_threshold
    
    # Find connected components in the significant edges graph
    # Using a simple BFS approach
    visited = np.zeros_like(significant_edges, dtype=bool)
    components = []
    
    for i in range(n_rois):
        for j in range(i + 1, n_rois):
            if significant_edges[i, j] and not visited[i, j]:
                # BFS to find connected component
                component_edges = []
                queue = [(i, j)]
                visited[i, j] = True
                visited[j, i] = True  # Symmetric
                
                while queue:
                    curr_i, curr_j = queue.pop(0)
                    component_edges.append((curr_i, curr_j))
                    
                    # Find neighbors
                    for k in range(n_rois):
                        if k != curr_i and not visited[curr_i, k] and significant_edges[curr_i, k]:
                            visited[curr_i, k] = True
                            visited[k, curr_i] = True
                            queue.append((curr_i, k))
                        if k != curr_j and not visited[curr_j, k] and significant_edges[curr_j, k]:
                            visited[curr_j, k] = True
                            visited[k, curr_j] = True
                            queue.append((curr_j, k))
                
                if component_edges:
                    components.append(component_edges)
    
    # Permutation testing for FWER correction
    max_component_sizes = []
    
    for perm in range(n_permutations):
        # Shuffle group labels
        all_indices = list(range(n_subjects))
        np.random.shuffle(all_indices)
        
        perm_group1 = all_indices[:len(group1_indices)]
        perm_group2 = all_indices[len(group1_indices):]
        
        # Compute t-stat for permuted groups
        perm_group1_matrices = matrices[perm_group1]
        perm_group2_matrices = matrices[perm_group2]
        
        perm_mean1 = np.mean(perm_group1_matrices, axis=0)
        perm_mean2 = np.mean(perm_group2_matrices, axis=0)
        
        perm_std1 = np.std(perm_group1_matrices, axis=0, ddof=1)
        perm_std2 = np.std(perm_group2_matrices, axis=0, ddof=1)
        
        perm_std1 = np.where(perm_std1 == 0, 1e-10, perm_std1)
        perm_std2 = np.where(perm_std2 == 0, 1e-10, perm_std2)
        
        perm_t = (perm_mean1 - perm_mean2) / np.sqrt((perm_std1**2 / len(perm_group1)) + (perm_std2**2 / len(perm_group2)))
        
        perm_p = 2 * (1 - scipy_stats.cdf(np.abs(perm_t), df=min(len(perm_group1), len(perm_group2))))
        perm_significant = perm_p < edge_threshold
        
        # Find largest component
        perm_visited = np.zeros_like(perm_significant, dtype=bool)
        max_size = 0
        
        for i in range(n_rois):
            for j in range(i + 1, n_rois):
                if perm_significant[i, j] and not perm_visited[i, j]:
                    # BFS
                    size = 0
                    queue = [(i, j)]
                    perm_visited[i, j] = True
                    perm_visited[j, i] = True
                    
                    while queue:
                        ci, cj = queue.pop(0)
                        size += 1
                        
                        for k in range(n_rois):
                            if k != ci and not perm_visited[ci, k] and perm_significant[ci, k]:
                                perm_visited[ci, k] = True
                                perm_visited[k, ci] = True
                                queue.append((ci, k))
                            if k != cj and not perm_visited[cj, k] and perm_significant[cj, k]:
                                perm_visited[cj, k] = True
                                perm_visited[k, cj] = True
                                queue.append((cj, k))
                    
                    max_size = max(max_size, size)
        
        max_component_sizes.append(max_size)
    
    # Calculate FWER p-values for observed components
    component_results = []
    for idx, comp_edges in enumerate(components):
        comp_size = len(comp_edges)
        p_value_fwer = np.sum(np.array(max_component_sizes) >= comp_size) / n_permutations
        component_results.append({
            'component_id': idx + 1,
            'size_edges': comp_size,
            'p_value_fwer': p_value_fwer
        })
    
    return {
        'components': component_results,
        't_statistic': t_stat,
        'n_permutations': n_permutations,
        'edge_threshold': edge_threshold
    }

def main():
    """Main entry point for NBS analysis."""
    import argparse
    from scipy import stats as scipy_stats  # Import here to avoid circular issues
    
    parser = argparse.ArgumentParser(description="Run Network-Based Statistic analysis")
    parser.add_argument(
        "--matrices",
        type=str,
        default="data/processed/connectivity_matrices.npy",
        help="Path to connectivity matrices file"
    )
    parser.add_argument(
        "--labels",
        type=str,
        default="data/processed/subjects_cleaned.csv",
        help="Path to subject labels file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed/nbs_raw_results.csv",
        help="Path to output NBS results file"
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=1000,
        help="Number of permutations for NBS"
    )
    parser.add_argument(
        "--edge-threshold",
        type=float,
        default=0.05,
        help="Edge significance threshold"
    )
    
    args = parser.parse_args()
    
    try:
        # Check memory
        check_memory_limit()
        
        # Load data
        matrices, subject_df, musician_idx, non_musician_idx = load_connectivity_matrices(
            args.matrices, args.labels
        )
        
        # Run NBS
        logger.info(f"Running NBS with {args.n_permutations} permutations...")
        results = network_based_statistic(
            matrices,
            musician_idx,
            non_musician_idx,
            n_permutations=args.n_permutations,
            edge_threshold=args.edge_threshold
        )
        
        # Create DataFrame
        df_results = pd.DataFrame(results['components'])
        
        # Ensure output directory exists
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write results
        df_results.to_csv(output_path, index=False)
        logger.info(f"Wrote NBS results to {args.output}")
        
        # Print summary
        print(f"NBS Analysis Summary:")
        print(f"  Components found: {len(df_results)}")
        significant = df_results[df_results['p_value_fwer'] < 0.05]
        print(f"  Significant components (p<0.05): {len(significant)}")
        if not significant.empty:
            print(f"  Largest significant component: {significant['size_edges'].max()} edges")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except MemoryLimitExceeded as e:
        logger.error(f"Memory limit exceeded: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
