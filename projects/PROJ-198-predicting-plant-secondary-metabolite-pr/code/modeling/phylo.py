"""
Phylogenetic analysis utilities for plant secondary metabolite prediction.

This module provides functions to load phylogenetic trees, construct
phylogenetic covariance matrices, and perform phylogenetic generalized
least squares (PGLS) regression.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import dendropy
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.spatial.distance import cdist

from utils.logging import get_logger

logger = get_logger(__name__)


class PhylogenyError(Exception):
    """Custom exception for phylogenetic analysis errors."""
    pass


def load_phylogeny(tree_path: Union[str, Path]) -> dendropy.Tree:
    """
    Load a phylogenetic tree from a Newick format file.
    
    Args:
        tree_path: Path to the Newick tree file.
        
    Returns:
        A DendroPy Tree object.
        
    Raises:
        PhylogenyError: If the file cannot be read or parsed.
    """
    tree_path = Path(tree_path)
    
    if not tree_path.exists():
        raise PhylogenyError(f"Tree file not found: {tree_path}")
    
    try:
        tree = dendropy.Tree.get(
            path=str(tree_path),
            schema="newick",
            rooting="force-rooted"
        )
        logger.info(f"Loaded phylogenetic tree with {len(tree.leaf_nodes())} tips from {tree_path}")
        return tree
    except Exception as e:
        raise PhylogenyError(f"Failed to parse tree file {tree_path}: {e}")


def construct_covariance_matrix(
    tree: dendropy.Tree,
    species_list: Optional[List[str]] = None
) -> Tuple[np.ndarray, List[str]]:
    """
    Construct a phylogenetic covariance matrix from a DendroPy tree.
    
    The covariance matrix is computed based on the shared branch length
    from the root to the most recent common ancestor for each pair of species.
    This assumes a Brownian motion model of evolution.
    
    Args:
        tree: A DendroPy Tree object.
        species_list: Optional list of species names to include in the matrix.
                     If None, all tip labels are used.
                     
    Returns:
        A tuple containing:
            - covariance_matrix: np.ndarray of shape (n_species, n_species)
            - species_order: List of species names corresponding to matrix rows/cols
        
    Raises:
        PhylogenyError: If species in species_list are not found in the tree.
    """
    # Get all tip labels from the tree
    all_tips = [leaf.taxon.label for leaf in tree.leaf_nodes()]
    all_tips_set = set(all_tips)
    
    # Determine which species to include
    if species_list is not None:
        # Filter to only species present in the tree
        missing = set(species_list) - all_tips_set
        if missing:
            logger.warning(f"Species not found in tree and will be excluded: {missing}")
        
        species_order = [s for s in species_list if s in all_tips_set]
        
        if len(species_order) == 0:
            raise PhylogenyError("No valid species found in the provided list.")
    else:
        species_order = all_tips
    
    n = len(species_order)
    logger.info(f"Constructing {n}x{n} phylogenetic covariance matrix")
    
    # Create a mapping from taxon label to taxon object for faster lookup
    taxon_map = {leaf.taxon.label: leaf.taxon for leaf in tree.leaf_nodes()}
    
    # Initialize covariance matrix
    covariance_matrix = np.zeros((n, n))
    
    # For each pair of species, compute the shared path length from root
    for i, sp1 in enumerate(species_order):
        taxon1 = taxon_map[sp1]
        node1 = tree.taxon_namespace[taxon1]
        
        # Get the path from root to tip1
        path1_nodes = set(tree.get_path_to_node(node1).nodes())
        
        for j, sp2 in enumerate(species_order):
            taxon2 = taxon_map[sp2]
            node2 = tree.taxon_namespace[taxon2]
            
            # Get the path from root to tip2
            path2_nodes = set(tree.get_path_to_node(node2).nodes())
            
            # Find shared nodes (from root to MRCA)
            shared_nodes = path1_nodes.intersection(path2_nodes)
            
            # Sum the edge lengths for shared path
            shared_length = 0.0
            for node in shared_nodes:
                if node.edge is not None:
                    shared_length += node.edge.length or 0.0
            
            covariance_matrix[i, j] = shared_length
    
    # Ensure symmetry (numerical stability)
    covariance_matrix = (covariance_matrix + covariance_matrix.T) / 2.0
    
    logger.info("Phylogenetic covariance matrix constructed successfully")
    return covariance_matrix, species_order


def train_pgls(
    X: pd.DataFrame,
    y: pd.Series,
    covariance_matrix: np.ndarray,
    species_order: List[str],
    add_intercept: bool = True
) -> Dict[str, Union[float, Dict[str, float], sm.regression.linear_model.RegressionResults]]:
    """
    Train a Phylogenetic Generalized Least Squares (PGLS) regression model.
    
    This function accounts for non-independence of data points due to shared
    evolutionary history by using the phylogenetic covariance matrix as the
    error structure.
    
    Args:
        X: DataFrame of features (predictors). Rows must be ordered to match
           the species_order used to construct the covariance matrix.
        y: Series of target values (responses). Must be ordered to match
           the species_order.
        covariance_matrix: The phylogenetic covariance matrix (n x n).
        species_order: List of species names corresponding to rows/cols of
                       the covariance matrix and X/y.
        add_intercept: Whether to add an intercept term to the model.
        
    Returns:
        A dictionary containing:
            - 'r_squared': R-squared value of the model
            - 'adj_r_squared': Adjusted R-squared value
            - 'coefficients': Dictionary of feature names to coefficients
            - 'p_values': Dictionary of feature names to p-values
            - 'model': The fitted statsmodels GLS model object
            - 'results': The full RegressionResults object
        
    Raises:
        PhylogenyError: If dimensions of X, y, and covariance_matrix are inconsistent.
        PhylogenyError: If the covariance matrix is singular or near-singular.
    """
    # Validate dimensions
    n_samples = len(species_order)
    if X.shape[0] != n_samples:
        raise PhylogenyError(
            f"Number of samples in X ({X.shape[0]}) does not match "
            f"number of species ({n_samples})"
        )
    if len(y) != n_samples:
        raise PhylogenyError(
            f"Length of y ({len(y)}) does not match "
            f"number of species ({n_samples})"
        )
    if covariance_matrix.shape != (n_samples, n_samples):
        raise PhylogenyError(
            f"Covariance matrix shape {covariance_matrix.shape} does not match "
            f"number of species ({n_samples})"
        )
    
    logger.info(f"Training PGLS model with {n_samples} species and {X.shape[1]} features")
    
    # Add intercept if requested
    if add_intercept:
        X_model = sm.add_constant(X)
    else:
        X_model = X
    
    # Fit the GLS model with the phylogenetic covariance structure
    try:
        model = sm.GLS(y, X_model, sigma=covariance_matrix)
        results = model.fit()
    except np.linalg.LinAlgError as e:
        raise PhylogenyError(f"Failed to fit PGLS model: Covariance matrix is singular. {e}")
    
    # Extract results
    r_squared = results.rsquared
    adj_r_squared = results.rsquared_adj
    
    # Get feature names
    feature_names = list(X.columns)
    if add_intercept:
        feature_names = ['intercept'] + feature_names
    
    coefficients = dict(zip(feature_names, results.params))
    p_values = dict(zip(feature_names, results.pvalues))
    
    logger.info(f"PGLS model fitted successfully. R² = {r_squared:.4f}, "
                f"Adjusted R² = {adj_r_squared:.4f}")
    
    return {
        'r_squared': r_squared,
        'adj_r_squared': adj_r_squared,
        'coefficients': coefficients,
        'p_values': p_values,
        'model': model,
        'results': results
    }


def main():
    """
    Main entry point for testing phylogenetic covariance matrix construction and PGLS.
    This function loads a tree, constructs the covariance matrix, and demonstrates PGLS usage.
    """
    import sys
    from utils.logging import setup_logging
    
    # Setup logging
    setup_logging()
    
    logger.info("Phylogenetic analysis module loaded.")
    logger.info("Functions available:")
    logger.info("  - load_phylogeny(tree_path)")
    logger.info("  - construct_covariance_matrix(tree, species_list)")
    logger.info("  - train_pgls(X, y, covariance_matrix, species_order)")
    logger.info("Use these functions to perform phylogenetic comparative analysis.")

if __name__ == "__main__":
    main()