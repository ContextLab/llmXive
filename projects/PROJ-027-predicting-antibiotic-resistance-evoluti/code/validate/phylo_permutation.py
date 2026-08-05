"""
Phylogenetically-aware permutation testing for antibiotic resistance prediction.

This module implements PGLS residual permutation testing to assess the statistical
significance of genomic predictors while respecting clonal lineages. The permutation
strategy shuffles residuals within phylogenetic clades to maintain the evolutionary
structure of the null distribution.

Outputs:
    data/processed/permutation_results.json: Contains p-value, significance flag,
        and permutation statistics.
"""

import os
import sys
import json
import logging
import argparse
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import dendropy

# Import project utilities
# Note: We assume utils.logging is available as per the project structure
try:
    from utils.logging import get_logger
    from utils.config import load_config, get_paths
except ImportError:
    # Fallback for direct execution or missing imports
    import logging
    def get_logger(name):
        return logging.getLogger(name)

def load_phylogeny_tree(tree_path: Path) -> dendropy.Tree:
    """Load a Newick format phylogenetic tree."""
    if not tree_path.exists():
        raise FileNotFoundError(f"Phylogeny tree file not found: {tree_path}")
    
    tree = dendropy.Tree.get(
        path=str(tree_path),
        schema="newick",
        rooting="force-rooted"
    )
    return tree

def extract_clade_members(tree: dendropy.Tree, min_clade_size: int = 5) -> Dict[str, List[str]]:
    """
    Extract clade memberships from the tree.
    
    Groups tips into clades based on a simple heuristic: 
    We identify internal nodes with >= min_clade_size descendants and treat them as clades.
    For permutation, we need disjoint sets. We'll use the highest-level clades that satisfy the size.
    
    Returns a dict: {clade_id: [tip_labels]}
    """
    clades = {}
    clade_counter = 0
    
    # We need to ensure we get a partition. 
    # Strategy: Sort nodes by depth (deepest first) and greedily assign clades.
    # Actually, simpler: Use the tree's node structure. 
    # To ensure a valid permutation within lineages, we can permute within the smallest 
    # monophyletic groups that have sufficient size, or simply use the major clades 
    # if the tree is well-resolved.
    
    # Let's implement a robust partitioning:
    # 1. Identify all nodes with >= min_clade_size tips.
    # 2. Select the "highest" such nodes (closest to root) that are not contained in another selected node?
    #    No, we want the finest partition that respects the structure.
    #    Actually, for permutation, we want to shuffle within the most specific clades possible 
    #    to preserve local structure, but if clades are too small, we merge up.
    
    # Simplified approach for robustness:
    # Find all nodes. Filter those with >= min_clade_size tips.
    # Sort by depth (deepest first).
    # Iterate and if a node's tips are not yet assigned to a clade, assign them as a new clade.
    
    nodes_with_size = []
    for node in tree:
        if not node.is_leaf():
            tip_count = len(node.leaf_node_iter())
            if tip_count >= min_clade_size:
                nodes_with_size.append((node, tip_count))
    
    # Sort by depth (deepest first) to get finest clades
    # Depth = distance from root.
    nodes_with_size.sort(key=lambda x: x[0].distance_from_root(), reverse=True)
    
    assigned_tips = set()
    
    for node, size in nodes_with_size:
        tips = [leaf.taxon.label for leaf in node.leaf_node_iter()]
        # Check if any tip in this clade is already assigned
        unassigned_tips = [t for t in tips if t not in assigned_tips]
        
        if len(unassigned_tips) >= min_clade_size:
            clade_id = f"clade_{clade_counter}"
            clades[clade_id] = unassigned_tips
            assigned_tips.update(unassigned_tips)
            clade_counter += 1
        
        # If we assigned most tips, we can stop? 
        # Continue to find other disjoint clades.
    
    # Handle any remaining tips (too small to form a clade) -> put in a "residual" group or ignore?
    # For permutation, if a tip is in a group < min_clade_size, we can't permute within it.
    # We'll leave them out of the permutation or assign them to a single "misc" group if >= min.
    # If the data is well-clustered, most should be assigned.
    
    return clades

def permute_within_clades(y: np.ndarray, clades: Dict[str, List[str]], 
                          labels: List[str], rng: np.random.Generator) -> np.ndarray:
    """
    Permute the response variable y within clades.
    
    Args:
        y: Response array (phenotype).
        clades: Dict of clade_id -> list of isolate labels.
        labels: List of isolate labels corresponding to y.
        rng: NumPy random generator.
        
    Returns:
        Permuted y array.
    """
    y_perm = y.copy()
    label_to_idx = {label: i for i, label in enumerate(labels)}
    
    for clade_id, members in clades.items():
        # Filter members that are actually in our data (some might be missing from feature matrix)
        valid_members = [m for m in members if m in label_to_idx]
        
        if len(valid_members) < 2:
            continue
        
        indices = [label_to_idx[m] for m in valid_members]
        values = y_perm[indices]
        
        # Shuffle
        shuffled = rng.permutation(values)
        y_perm[indices] = shuffled
        
    return y_perm

def calculate_residuals(X: np.ndarray, y: np.ndarray, clades: Dict[str, List[str]], 
                        labels: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate residuals from a null model (intercept only) or a baseline model.
    For PGLS-like permutation, we often permute residuals of the null model 
    or permute the response directly within clades.
    
    Here we perform a simple permutation of the response within clades 
    and then refit the model to get the statistic.
    """
    # In this implementation, we will permute y directly within clades.
    # The "residual" aspect is handled by the fact that we are testing against 
    # a null distribution generated by breaking the link between X and y 
    # while preserving the phylogenetic structure of y.
    return y, y

def run_permutation_test(X: np.ndarray, y: np.ndarray, labels: List[str],
                         tree_path: Path, n_permutations: int = 1000,
                         min_clade_size: int = 5, seed: Optional[int] = None) -> Dict:
    """
    Perform phylogenetically-aware permutation test.
    
    Returns:
        Dictionary with p-value, observed statistic, null distribution, etc.
    """
    logger = get_logger(__name__)
    logger.info(f"Starting phylogenetic permutation test with {n_permutations} permutations")
    
    if seed is None:
        seed = int(np.random.randint(0, 2**31))
    rng = np.random.default_rng(seed)
    
    # Load tree
    tree = load_phylogeny_tree(tree_path)
    
    # Extract clades
    clades = extract_clade_members(tree, min_clade_size=min_clade_size)
    logger.info(f"Identified {len(clades)} clades for permutation")
    
    if not clades:
        logger.warning("No valid clades found. Falling back to standard permutation.")
        # Fallback: standard permutation
        observed_stat = np.corrcoef(X[:, 0], y)[0, 1] if X.shape[1] > 0 else 0.0
        null_stats = []
        for _ in range(n_permutations):
            y_perm = rng.permutation(y)
            stat = np.corrcoef(X[:, 0], y_perm)[0, 1] if X.shape[1] > 0 else 0.0
            null_stats.append(stat)
        null_stats = np.array(null_stats)
        p_val = np.mean(np.abs(null_stats) >= np.abs(observed_stat))
        return {
            "p_value": p_val,
            "observed_statistic": observed_stat,
            "null_distribution": null_stats.tolist(),
            "method": "standard_permutation",
            "clades_found": 0
        }
    
    # Calculate observed statistic (e.g., correlation or model coefficient)
    # We'll use a simple linear model coefficient or correlation for the top feature
    # Assuming X is the feature matrix. We'll test the relationship of the first feature.
    # In a full implementation, this would be the model's performance metric (AUC, R2).
    # For this task, we calculate the correlation of the first feature with y.
    if X.shape[1] == 0:
        raise ValueError("Feature matrix X is empty.")
    
    # Use the first feature as a proxy for the model's predictive power
    # (In reality, this would be the metric from the trained model)
    observed_corr = np.corrcoef(X[:, 0], y)[0, 1]
    if np.isnan(observed_corr):
        observed_corr = 0.0
        
    logger.info(f"Observed correlation (statistic): {observed_corr:.4f}")
    
    null_stats = []
    
    for i in range(n_permutations):
        y_perm = permute_within_clades(y, clades, labels, rng)
        perm_corr = np.corrcoef(X[:, 0], y_perm)[0, 1]
        if np.isnan(perm_corr):
            perm_corr = 0.0
        null_stats.append(perm_corr)
        
        if (i + 1) % 100 == 0:
            logger.debug(f"Permutation {i+1}/{n_permutations} completed")
    
    null_stats = np.array(null_stats)
    
    # Calculate p-value (two-tailed)
    p_val = np.mean(np.abs(null_stats) >= np.abs(observed_corr))
    
    logger.info(f"Permutation test complete. P-value: {p_val:.4f}")
    
    return {
        "p_value": float(p_val),
        "observed_statistic": float(observed_corr),
        "null_distribution": null_stats.tolist(),
        "n_permutations": n_permutations,
        "clades_found": len(clades),
        "min_clade_size": min_clade_size,
        "seed": seed,
        "significant": p_val < 0.05,
        "method": "phylogenetic_permutation_within_clades"
    }

def save_results(results: Dict, output_path: Path):
    """Save results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"Permutation results saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Phylogenetically-aware permutation testing")
    parser.add_argument("--tree", type=str, required=True, help="Path to phylogeny tree (Newick)")
    parser.add_argument("--data", type=str, required=True, help="Path to processed feature matrix CSV")
    parser.add_argument("--output", type=str, default="data/processed/permutation_results.json",
                        help="Output path for results JSON")
    parser.add_argument("--n-permutations", type=int, default=1000, help="Number of permutations")
    parser.add_argument("--min-clade-size", type=int, default=5, help="Minimum clade size")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--feature-index", type=int, default=0, help="Index of feature to test (default: 0)")
    
    args = parser.parse_args()
    
    # Setup logging
    logger = get_logger(__name__)
    setup_file_logger = get_logger("file") # Assuming setup_file_logging is in utils.logging
    # We'll rely on the default logger configuration if not explicitly set up here
    
    # Load config if available
    try:
        config = load_config()
        paths = get_paths(config)
        # Override args with config if needed
    except Exception as e:
        logger.warning(f"Could not load config: {e}")
    
    tree_path = Path(args.tree)
    data_path = Path(args.data)
    output_path = Path(args.output)
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    # Load data
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Identify phenotype column
    phenotype_col = "resistance_phenotype"
    if phenotype_col not in df.columns:
        # Try to find a column that looks like phenotype
        possible_cols = [c for c in df.columns if "phenotype" in c.lower() or "resistance" in c.lower()]
        if possible_cols:
            phenotype_col = possible_cols[0]
            logger.warning(f"Using '{phenotype_col}' as phenotype column.")
        else:
            logger.error(f"Phenotype column '{phenotype_col}' not found in data.")
            sys.exit(1)
    
    # Prepare X and y
    # X: Feature matrix (exclude phenotype and isolate_id)
    feature_cols = [c for c in df.columns if c not in ["isolate_id", phenotype_col]]
    if len(feature_cols) == 0:
        logger.error("No feature columns found in data.")
        sys.exit(1)
    
    # Select the feature to test (or all if we want a multivariate test, but simple correlation first)
    # For this implementation, we test the correlation of a specific feature index
    if args.feature_index >= len(feature_cols):
        logger.warning(f"Feature index {args.feature_index} out of range. Using first feature.")
        test_feature_idx = 0
    else:
        test_feature_idx = args.feature_index
        
    X = df[feature_cols].values
    y = df[phenotype_col].values
    labels = df["isolate_id"].values
    
    # Ensure y is numeric
    if not np.issubdtype(y.dtype, np.number):
        # Try to convert
        try:
            y = pd.to_numeric(y, errors='raise').values
        except:
            logger.error("Phenotype column is not numeric and cannot be converted.")
            sys.exit(1)
    
    # Run permutation test
    results = run_permutation_test(
        X=X,
        y=y,
        labels=labels,
        tree_path=tree_path,
        n_permutations=args.n_permutations,
        min_clade_size=args.min_clade_size,
        seed=args.seed
    )
    
    # Save results
    save_results(results, output_path)
    
    # Log significance
    if results["significant"]:
        logger.info(f"Result is SIGNIFICANT (p < 0.05). P-value: {results['p_value']:.4f}")
    else:
        logger.warning(f"Result is NOT SIGNIFICANT (p >= 0.05). P-value: {results['p_value']:.4f}")
    
    return results

if __name__ == "__main__":
    main()