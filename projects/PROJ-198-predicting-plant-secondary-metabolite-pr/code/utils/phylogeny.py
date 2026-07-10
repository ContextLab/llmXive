"""
Phylogeny utilities for tree parsing and Phylogenetic Eigenvector Regression (PVR).

This module provides functionality to:
1. Parse Newick format phylogenetic trees using DendroPy.
2. Calculate phylogenetic distance matrices.
3. Perform Phylogenetic Eigenvector Regression (PVR) using statsmodels.
   This replaces the Felsenstein's PIC method as per project plan deviation.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy.spatial.distance import squareform
from scipy.stats import zscore
import statsmodels.api as sm
from statsmodels.regression.linear_model import OLS

try:
    import dendropy
except ImportError:
    raise ImportError(
        "DendroPy is required for phylogeny parsing. "
        "Install it via: pip install dendropy"
    )

logger = logging.getLogger(__name__)


def parse_newick_tree(
    tree_path: str,
    taxon_namespace: Optional[str] = None
) -> dendropy.Tree:
    """
    Parse a phylogenetic tree from a Newick format file.

    Args:
        tree_path: Path to the Newick file.
        taxon_namespace: Optional taxon namespace label.

    Returns:
        A DendroPy Tree object.

    Raises:
        FileNotFoundError: If the tree file does not exist.
        ValueError: If the tree cannot be parsed.
    """
    if not os.path.exists(tree_path):
        raise FileNotFoundError(f"Tree file not found: {tree_path}")

    logger.info(f"Parsing Newick tree from: {tree_path}")
    try:
        tree = dendropy.Tree.get(
            path=tree_path,
            schema="newick",
            rooting="force-rooted"
        )
        logger.info(f"Tree loaded successfully. Tip count: {len(tree.taxon_nodes)}")
        return tree
    except Exception as e:
        logger.error(f"Failed to parse tree: {e}")
        raise ValueError(f"Invalid Newick tree format: {e}")


def get_tip_labels(tree: dendropy.Tree) -> List[str]:
    """
    Extract a list of tip (leaf) labels from a DendroPy tree.

    Args:
        tree: The DendroPy Tree object.

    Returns:
        List of tip labels as strings.
    """
    return [node.taxon.label for node in tree.leaf_nodes()]


def calculate_cophenetic_distance_matrix(
    tree: dendropy.Tree,
    tip_labels: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Calculate the cophenetic distance matrix from a tree.

    Args:
        tree: The DendroPy Tree object.
        tip_labels: Optional list of specific tip labels to include.
                   If None, all tips are used.

    Returns:
        A pandas DataFrame with species as index and columns, containing
        pairwise phylogenetic distances.
    """
    if tip_labels is None:
        tip_labels = get_tip_labels(tree)
    
    # Filter tree tips if specific labels are requested
    # DendroPy cophenetic matrix is easier to get for all tips, then filter
    # However, to ensure order matches, we construct manually or filter result.
    # DendroPy's cophenetic_distance_matrix returns a dict of dicts or matrix.
    
    # Get cophenetic distances for all pairs in the tree
    # We will filter the resulting matrix to the requested tip_labels
    
    all_tips = get_tip_labels(tree)
    
    # Build a matrix of distances
    n = len(all_tips)
    dist_matrix = np.zeros((n, n))
    
    # Map labels to indices
    label_to_idx = {label: i for i, label in enumerate(all_tips)}
    
    for i, node_i in enumerate(tree.leaf_nodes()):
        for j, node_j in enumerate(tree.leaf_nodes()):
            if i <= j:
                # DendroPy node distance
                d = tree.phylogenetic_distance(node_i, node_j)
                dist_matrix[i, j] = d
                dist_matrix[j, i] = d
    
    df = pd.DataFrame(
        dist_matrix,
        index=all_tips,
        columns=all_tips
    )
    
    # Filter to requested tips if provided
    if tip_labels is not None:
        # Ensure all requested tips exist
        missing = set(tip_labels) - set(all_tips)
        if missing:
            raise ValueError(f"Tip labels not found in tree: {missing}")
        df = df.loc[tip_labels, tip_labels]
        
    return df


def calculate_pvr_eigenvectors(
    distance_matrix: pd.DataFrame,
    k: Optional[int] = None
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Calculate Phylogenetic Eigenvectors from a distance matrix.

    This performs Principal Coordinate Analysis (PCoA) on the phylogenetic
    distance matrix to generate eigenvectors (eigenfunctions) that can be
    used as predictors in regression to control for phylogenetic signal.

    Args:
        distance_matrix: Square, symmetric DataFrame of phylogenetic distances.
        k: Number of eigenvectors to retain. If None, retains all positive
           eigenvalues.

    Returns:
        Tuple of (eigenvectors_df, eigenvalues_dict)
        - eigenvectors_df: DataFrame where rows are species and columns are eigenvectors.
        - eigenvalues_dict: Dictionary mapping eigenvector column names to their eigenvalues.
    """
    if distance_matrix.empty:
        raise ValueError("Distance matrix is empty.")
    
    species = distance_matrix.index
    dist_vals = distance_matrix.values

    # Double centering for PCoA
    # B = -0.5 * J * D^2 * J
    n = dist_vals.shape[0]
    J = np.eye(n) - (1 / n) * np.ones((n, n))
    D_sq = dist_vals ** 2
    B = -0.5 * J @ D_sq @ J

    # Eigen decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(B)
    
    # Sort by eigenvalues descending
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    # Filter out non-positive eigenvalues (numerical noise can create tiny negatives)
    pos_mask = eigenvalues > 1e-10
    eigenvalues = eigenvalues[pos_mask]
    eigenvectors = eigenvectors[:, pos_mask]

    if k is not None:
        k = min(k, len(eigenvalues))
        eigenvalues = eigenvalues[:k]
        eigenvectors = eigenvectors[:, :k]

    # Normalize eigenvectors by sqrt of eigenvalue (standard in PVR)
    # Eigenvectors = V * sqrt(Lambda)
    if len(eigenvalues) > 0:
        eigenvectors = eigenvectors * np.sqrt(eigenvalues)
    
    # Create DataFrame
    col_names = [f"EV_{i+1}" for i in range(eigenvectors.shape[1])]
    eigenvector_df = pd.DataFrame(
        eigenvectors,
        index=species,
        columns=col_names
    )
    
    eigenvalues_dict = {col: val for col, val in zip(col_names, eigenvalues)}
    
    logger.info(f"Generated {len(col_names)} phylogenetic eigenvectors.")
    
    return eigenvector_df, eigenvalues_dict


def run_pvr_regression(
    y: Union[pd.Series, np.ndarray],
    X: Union[pd.DataFrame, np.ndarray],
    phylo_evs: pd.DataFrame,
    species_index: List[str],
    k: Optional[int] = None
) -> Dict:
    """
    Perform Phylogenetic Eigenvector Regression (PVR).

    Steps:
    1. Calculate phylogenetic eigenvectors from a distance matrix (derived from tree).
    2. Select top k eigenvectors (or all positive).
    3. Regress Y on X + selected EVs.
    4. Return model results and residuals.

    Args:
        y: Dependent variable (1D array or Series).
        X: Independent variables (2D array or DataFrame), excluding intercept.
        phylo_evs: Full DataFrame of phylogenetic eigenvectors (from calculate_pvr_eigenvectors).
        species_index: List of species names corresponding to rows in y, X, and phylo_evs.
        k: Number of eigenvectors to include. If None, all positive are used.

    Returns:
        Dictionary containing:
        - 'model': The fitted statsmodels OLS model.
        - 'results': The regression results summary object.
        - 'residuals': The PVR-adjusted residuals (phylogeny-corrected Y).
        - 'r_squared': R-squared of the full model.
        - 'p_value': P-value for the overall model (F-test).
        - 'selected_evs': List of selected eigenvector column names.
    """
    # Align data
    # Ensure y, X, and phylo_evs are indexed by species_index
    # We assume inputs are already aligned or we align them here.
    
    if isinstance(y, (pd.Series, pd.DataFrame)):
        y = y.reindex(species_index).values
    if isinstance(X, pd.DataFrame):
        X = X.reindex(species_index).values
    
    # Filter phylo_evs
    if not set(species_index).issubset(set(phylo_evs.index)):
        missing = set(species_index) - set(phylo_evs.index)
        raise ValueError(f"Species missing in phylo_evs: {missing}")
    
    ev_data = phylo_evs.loc[species_index]
    
    # Select top k eigenvectors
    all_ev_cols = ev_data.columns.tolist()
    if k is not None:
        selected_evs = all_ev_cols[:k]
    else:
        selected_evs = all_ev_cols
    
    if not selected_evs:
        raise ValueError("No positive eigenvectors found.")
    
    ev_selected = ev_data[selected_evs]
    
    # Combine X and EVs
    # X should be a DataFrame for easy concatenation, or handle as array
    if isinstance(X, np.ndarray):
        # Create a dummy index to concat with ev_selected
        X_df = pd.DataFrame(X, index=species_index)
    else:
        X_df = X.reindex(species_index)
        
    # Ensure X and ev_selected have same index
    if not X_df.index.equals(ev_selected.index):
        # Force reindex if not equal (should not happen if logic above is correct)
        common_idx = X_df.index.intersection(ev_selected.index)
        X_df = X_df.loc[common_idx]
        ev_selected = ev_selected.loc[common_idx]
        y = y[common_idx] if isinstance(y, np.ndarray) else y.loc[common_idx]
        
    X_full = pd.concat([X_df, ev_selected], axis=1)
    
    # Add constant
    X_full = sm.add_constant(X_full)
    
    # Fit model
    try:
        model = OLS(y, X_full)
        results = model.fit()
    except Exception as e:
        logger.error(f"OLS regression failed: {e}")
        raise RuntimeError(f"Regression failed: {e}")
    
    # Calculate residuals (these are the phylogeny-corrected Y values relative to X)
    # Actually, PVR residuals usually refer to residuals of Y ~ EVs, then regress those on X.
    # But the prompt asks for "PVR calculation using statsmodels" to replace PIC.
    # Standard PVR approach: Y = X*beta + EV*gamma + error.
    # The "phylogenetic correction" is achieved by including EVs.
    # The residuals of this full model are the phylogenetically independent errors.
    
    residuals = results.resid
    
    return {
        "model": model,
        "results": results,
        "residuals": residuals,
        "r_squared": results.rsquared,
        "adj_r_squared": results.rsquared_adj,
        "p_value": results.f_pvalue,
        "selected_evs": selected_evs,
        "coefficients": results.params
    }


def main():
    """
    Main entry point for standalone execution (CLI or simple test).
    Demonstrates parsing a tree and calculating PVR components.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage (requires a real tree file in data/raw/ or similar)
    # This is a placeholder for the actual pipeline integration
    logger.info("Phylogeny module loaded. Use parse_newick_tree, calculate_pvr_eigenvectors, and run_pvr_regression.")
    
    # If a tree file is provided as an argument, run a quick test
    if len(os.sys.argv) > 1:
        tree_path = os.sys.argv[1]
        try:
            tree = parse_newick_tree(tree_path)
            tips = get_tip_labels(tree)
            dist_mat = calculate_cophenetic_distance_matrix(tree)
            evs, evals = calculate_pvr_eigenvectors(dist_mat, k=3)
            logger.info(f"Successfully processed {len(tips)} species. Generated {len(evs.columns)} eigenvectors.")
            logger.info(f"First 3 EVs: {list(evs.columns[:3])}")
        except Exception as e:
            logger.error(f"Error processing tree: {e}")
            os.sys.exit(1)
    else:
        logger.info("No tree path provided. Run with: python code/utils/phylogeny.py <path_to_tree.newick>")

if __name__ == "__main__":
    main()
