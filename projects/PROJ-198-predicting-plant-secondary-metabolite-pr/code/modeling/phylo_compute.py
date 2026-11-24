"""
Phylogenetic covariance matrix construction script.

This script loads the aligned feature‑target matrix produced by the
data‑alignment step, extracts the list of species, loads a phylogenetic
tree (Newick format), builds a full phylogenetic covariance matrix using
the utilities in ``code.modeling.phylo``, and then extracts the sub‑matrix
that corresponds exactly to the species present in the aligned matrix.

The resulting covariance matrix is saved as a NumPy binary ``.npy`` file
under ``data/processed/phylo_covariance.npy``.  Its dimensions are
``(n_species, n_species)`` where ``n_species`` matches the number of rows
(unique species) in ``aligned_matrix.csv``.  An error is raised if any
species from the aligned matrix are missing in the tree, ensuring the
verification condition is met.
"""

import pandas as pd
import numpy as np

from llmxive_toolkit import paths, get_logger
from code.modeling.phylo import load_phylogeny, construct_covariance_matrix

def _load_aligned_species(aligned_path: str) -> list:
    """Read the aligned matrix CSV and return the ordered list of species."""
    df = pd.read_csv(aligned_path)
    if "species" not in df.columns:
        raise ValueError(f"'species' column not found in {aligned_path}")
    # Preserve the order as it appears in the file
    return df["species"].tolist()

def _extract_submatrix(
    full_cov: np.ndarray, taxa_labels: list, target_species: list
) -> np.ndarray:
    """
    Given a full covariance matrix and the ordered list of taxon labels,
    return the sub‑matrix that contains only ``target_species`` in the
    same order.
    """
    label_to_index = {label: idx for idx, label in enumerate(taxa_labels)}
    missing = [s for s in target_species if s not in label_to_index]
    if missing:
        raise ValueError(
            f"The following species are present in the aligned matrix but "
            f"missing from the phylogenetic tree: {missing}"
        )
    indices = [label_to_index[s] for s in target_species]
    return full_cov[np.ix_(indices, indices)]

def main() -> None:
    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # Paths (project‑relative, created automatically by llmxive_toolkit)
    # ------------------------------------------------------------------
    aligned_path = paths.data("processed", "aligned_matrix.csv")
    phylo_tree_path = paths.data("raw", "phylogeny", "tree.newick")
    output_path = paths.data("processed", "phylo_covariance.npy")

    logger.info(f"Loading aligned matrix from {aligned_path}")
    species_list = _load_aligned_species(str(aligned_path))
    logger.info(f"Found {len(species_list)} species in aligned matrix")

    logger.info(f"Loading phylogenetic tree from {phylo_tree_path}")
    tree = load_phylogeny(str(phylo_tree_path))

    logger.info("Constructing full phylogenetic covariance matrix")
    full_cov = construct_covariance_matrix(tree)

    # Dendropy stores taxon labels in the taxon_namespace; preserve order
    taxa_labels = [taxon.label for taxon in tree.taxon_namespace]

    logger.info("Extracting covariance sub‑matrix for aligned species")
    sub_cov = _extract_submatrix(full_cov, taxa_labels, species_list)

    logger.info(
        f"Saving covariance matrix of shape {sub_cov.shape} to {output_path}"
    )
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, sub_cov)

    logger.info("Phylogenetic covariance matrix construction completed successfully")

if __name__ == "__main__":
    main()