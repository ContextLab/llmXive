"""
Script to run Network-Based Statistic (NBS) on connectivity data.

This script loads preprocessed connectivity matrices and runs NBS
to identify significant connected components between musicians and non-musicians.
"""
import os
import sys
import numpy as np
import pandas as pd
import logging
from pathlib import Path
from typing import List, Optional

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger
from analysis.stats import network_based_statistic
from data.download import load_data

logger = get_logger(__name__)

def load_connectivity_matrices(
    data_dir: str,
    subject_csv: str,
    group_col: str = 'group'
) -> tuple[List[np.ndarray], List[np.ndarray]]:
    """
    Load connectivity matrices for each subject and split by group.
    
    Args:
        data_dir: Directory containing connectivity matrix files
        subject_csv: Path to CSV with subject metadata and group labels
        group_col: Column name for group labels
        
    Returns:
        Tuple of (group1_matrices, group2_matrices)
    """
    logger.info(f"Loading connectivity matrices from {data_dir}")
    logger.info(f"Using subject metadata from {subject_csv}")
    
    # Load subject metadata
    if not os.path.exists(subject_csv):
        raise FileNotFoundError(f"Subject CSV not found: {subject_csv}")
        
    subjects_df = pd.read_csv(subject_csv)
    
    # Check if we have group information
    if group_col not in subjects_df.columns:
        raise ValueError(f"Group column '{group_col}' not found in {subject_csv}")
    
    # Identify musicians and non-musicians
    musician_ids = subjects_df[subjects_df[group_col] == 'musician']['subject_id'].tolist()
    non_musician_ids = subjects_df[subjects_df[group_col] == 'non_musician']['subject_id'].tolist()
    
    logger.info(f"Found {len(musician_ids)} musicians and {len(non_musician_ids)} non-musicians")
    
    group1_matrices = []
    group2_matrices = []
    
    # Load matrices for each subject
    for subject_id in musician_ids:
        matrix_path = os.path.join(data_dir, f"{subject_id}_connectivity.npy")
        if os.path.exists(matrix_path):
            mat = np.load(matrix_path)
            group1_matrices.append(mat)
            logger.debug(f"Loaded matrix for musician {subject_id}")
        else:
            logger.warning(f"Matrix not found for musician {subject_id}: {matrix_path}")
    
    for subject_id in non_musician_ids:
        matrix_path = os.path.join(data_dir, f"{subject_id}_connectivity.npy")
        if os.path.exists(matrix_path):
            mat = np.load(matrix_path)
            group2_matrices.append(mat)
            logger.debug(f"Loaded matrix for non-musician {subject_id}")
        else:
            logger.warning(f"Matrix not found for non-musician {subject_id}: {matrix_path}")
    
    if not group1_matrices or not group2_matrices:
        raise ValueError("Insufficient data: Need at least one matrix per group")
    
    logger.info(f"Loaded {len(group1_matrices)} musician matrices and {len(group2_matrices)} non-musician matrices")
    return group1_matrices, group2_matrices

def run_nbs_analysis(
    data_dir: str,
    subject_csv: str,
    output_dir: str,
    edge_threshold: float = 0.05,
    n_permutations: int = 1000,
    seed: Optional[int] = None
):
    """
    Run full NBS analysis pipeline.
    
    Args:
        data_dir: Directory containing connectivity matrix files
        subject_csv: Path to subject metadata CSV
        output_dir: Directory to save results
        edge_threshold: Primary edge threshold for NBS
        n_permutations: Number of permutations
        seed: Random seed
    """
    logger.info("Starting NBS analysis")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load matrices
    group1_matrices, group2_matrices = load_connectivity_matrices(
        data_dir, subject_csv
    )
    
    # Run NBS
    logger.info(f"Running NBS with threshold={edge_threshold}, permutations={n_permutations}")
    result = network_based_statistic(
        group1_matrices,
        group2_matrices,
        edge_threshold=edge_threshold,
        n_permutations=n_permutations,
        seed=seed
    )
    
    # Save results
    results_path = os.path.join(output_dir, "nbs_results.csv")
    
    # Prepare results for CSV
    results_data = []
    for i, (size, p_val) in enumerate(zip(result['component_sizes'], result['component_p_values'])):
        results_data.append({
            'component_id': i + 1,
            'size_edges': size,
            'p_value_fwer': p_val,
            'significant': p_val < 0.05
        })
    
    results_df = pd.DataFrame(results_data)
    results_df.to_csv(results_path, index=False)
    
    logger.info(f"NBS results saved to {results_path}")
    logger.info(f"Total components found: {len(result['component_sizes'])}")
    logger.info(f"Largest component size: {result['largest_component_size']} edges")
    logger.info(f"Largest component p-value: {result['largest_component_p_value']}")
    
    # Print summary
    print("\n" + "="*50)
    print("NBS ANALYSIS SUMMARY")
    print("="*50)
    print(f"Edge threshold: {result['edge_threshold']}")
    print(f"Permutations: {result['n_permutations']}")
    print(f"Total components: {len(result['component_sizes'])}")
    print(f"Largest component size: {result['largest_component_size']} edges")
    print(f"Largest component p-value: {result['largest_component_p_value']:.4f}")
    
    significant = [c for c in result['significant_components'] if c[1] < 0.05]
    print(f"Significant components (p < 0.05): {len(significant)}")
    for i, (size, p_val) in enumerate(significant):
        print(f"  Component {i+1}: {size} edges, p = {p_val:.4f}")
    print("="*50)
    
    return result

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Network-Based Statistic analysis")
    parser.add_argument("--data-dir", type=str, required=True, 
                      help="Directory containing connectivity matrices")
    parser.add_argument("--subject-csv", type=str, required=True,
                      help="Path to subject metadata CSV")
    parser.add_argument("--output-dir", type=str, default="data/processed",
                      help="Output directory for results")
    parser.add_argument("--threshold", type=float, default=0.05,
                      help="Edge threshold for NBS")
    parser.add_argument("--permutations", type=int, default=1000,
                      help="Number of permutations")
    parser.add_argument("--seed", type=int, default=None,
                      help="Random seed")
    
    args = parser.parse_args()
    
    run_nbs_analysis(
        data_dir=args.data_dir,
        subject_csv=args.subject_csv,
        output_dir=args.output_dir,
        edge_threshold=args.threshold,
        n_permutations=args.permutations,
        seed=args.seed
    )

if __name__ == "__main__":
    main()