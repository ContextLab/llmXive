import logging
import os
from typing import Any, Dict, List, Union

import dendropy
import numpy as np

logger = logging.getLogger(__name__)


class PhylogenyError(Exception):
    """Exception raised for phylogeny-related errors."""

    pass


def load_phylogeny(tree_path: str) -> dendropy.Tree:
    """
    Load a phylogenetic tree from a Newick file.

    Args:
        tree_path: Path to Newick file

    Returns:
        Dendropy Tree object
    """
    if not os.path.exists(tree_path):
        raise PhylogenyError(f"Tree file not found: {tree_path}")

    try:
        tree = dendropy.Tree.get(path=tree_path, schema="newick")
        logger.info(f"Loaded tree with {len(tree.taxon_namespace)} taxa")
        return tree
    except Exception as e:
        raise PhylogenyError(f"Failed to parse tree: {e}")


def construct_covariance_matrix(tree: Union[str, dendropy.Tree]) -> np.ndarray:
    """
    Construct phylogenetic covariance matrix from a tree.

    Args:
        tree: Path to Newick file or Dendropy Tree object

    Returns:
        Covariance matrix (n_taxa, n_taxa)
    """
    if isinstance(tree, str):
        tree = load_phylogeny(tree)

    # Ensure each taxon has a label; dendropy may use None for unlabeled taxa
    for idx, taxon in enumerate(tree.taxon_namespace):
        if taxon.label is None:
            taxon.label = f"taxon_{idx}"

    # Compute the patristic (pairwise) distance matrix
    # dendropy provides a ``phylogenetic_distance_matrix`` method that
    # yields an object supporting ``distance(taxon1, taxon2)``.
    pdm = tree.phylogenetic_distance_matrix()
    taxa = list(tree.taxon_namespace)
    n = len(taxa)

    cov_matrix = np.zeros((n, n))

    # The covariance under a Brownian‑motion model is proportional to the
    # shared evolutionary history between two taxa, i.e. the distance from
    # the root to their most recent common ancestor (MRCA).  The distance
    # matrix returned by dendropy gives the total path length between
    # taxa; the MRCA shared length can be derived as:
    #
    #   cov(i, j) = (d_root_i + d_root_j - d_ij) / 2
    #
    # where d_root_i is the distance from the root to taxon i and d_ij
    # is the patristic distance between i and j.
    #
    # For the diagonal (i == j) this reduces to d_root_i.

    # Pre‑compute root‑to‑tip distances
    root_to_tip = np.array([pdm.distance(tree.seed_node, taxon) for taxon in taxa])

    for i, taxon_i in enumerate(taxa):
        for j, taxon_j in enumerate(taxa):
            if i == j:
                cov_matrix[i, j] = root_to_tip[i]
            else:
                dij = pdm.distance(taxon_i, taxon_j)
                cov_matrix[i, j] = (root_to_tip[i] + root_to_tip[j] - dij) / 2.0

    logger.info(f"Constructed {n}x{n} phylogenetic covariance matrix")
    return cov_matrix


def train_pgls(
    X: np.ndarray,
    y: np.ndarray,
    species: List[str],
    phylogenetic_covariance: np.ndarray,
) -> Dict[str, Any]:
    """
    Train a Phylogenetic Generalized Least Squares (PGLS) model.

    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        species: List of species names (must match covariance matrix order)
        phylogenetic_covariance: Phylogenetic covariance matrix

    Returns:
        Dictionary containing model results
    """
    if len(X) != len(y):
        raise ValueError("X and y must have the same number of samples")

    if len(X) != phylogenetic_covariance.shape[0]:
        raise ValueError(
            "Number of samples must match covariance matrix dimension"
        )

    try:
        import statsmodels.api as sm

        # Add intercept
        X_with_intercept = sm.add_constant(X)

        # Fit PGLS using GLS with covariance structure
        # Note: statsmodels GLS expects the inverse of the covariance matrix
        try:
            cov_inv = np.linalg.inv(phylogenetic_covariance)
        except np.linalg.LinAlgError:
            logger.warning(
                "Covariance matrix is singular, adding small regularization"
            )
            cov_inv = np.linalg.inv(
                phylogenetic_covariance
                + 1e-6 * np.eye(phylogenetic_covariance.shape[0])
            )

        model = sm.GLS(y, X_with_intercept, sigma=phylogenetic_covariance)
        results = model.fit()

        # Calculate R²
        y_pred = results.fittedvalues
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot)

        # Extract coefficients
        coefficients = {
            "intercept": float(results.params[0]),
            "features": {
                species[i]: float(results.params[i + 1])
                for i in range(X.shape[1])
            },
        }

        # Feature importance (absolute coefficient magnitude)
        feature_importance = {
            species[i]: float(abs(results.params[i + 1]))
            for i in range(X.shape[1])
        }

        logger.info(f"PGLS R² = {r_squared:.4f}")

        return {
            "r_squared": float(r_squared),
            "p_value": float(results.f_pvalue),
            "coefficients": coefficients,
            "feature_importance": feature_importance,
            "n_samples": len(y),
            "n_features": X.shape[1],
        }

    except Exception as e:
        logger.error(f"PGLS fitting failed: {e}")
        raise PhylogenyError(f"PGLS training failed: {e}")


def main():
    """Main entry point for phylogeny utilities."""
    logger.info("Phylogeny utilities module loaded")


if __name__ == "__main__":
    main()