"""
Synthetic data generation module for the drought tolerance prediction pipeline.

This module generates synthetic datasets required for model training and validation,
including genomic features, drought labels, and phylogenetic distance matrices.

Note: All genomic data and labels are synthetic per project plan constraints.
"""

import os
import sys
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from config import get_config, validate_config, ensure_directories
from utils.logging import DataPipelineLog


def generate_synthetic_phylogenetic_matrix(
    species_count: int,
    lower_bound: float = 0.1,
    upper_bound: float = 1.0,
    random_state: int = 42
) -> np.ndarray:
    """
    Generate a synthetic phylogenetic distance matrix for a list of species.

    Logic:
    - Create an N x N symmetric matrix where N is the species count.
    - Diagonal elements are set to 0 (distance from self is zero).
    - Off-diagonal elements are uniformly distributed between lower_bound and upper_bound.

    Args:
        species_count (int): Number of species (N) for the matrix dimensions.
        lower_bound (float): Minimum value for off-diagonal distances.
        upper_bound (float): Maximum value for off-diagonal distances.
        random_state (int): Random seed for reproducibility.

    Returns:
        np.ndarray: A symmetric N x N matrix representing phylogenetic distances.
    """
    if species_count <= 0:
        raise ValueError("Species count must be a positive integer.")
    if lower_bound < 0 or upper_bound < 0 or lower_bound >= upper_bound:
        raise ValueError("Bounds must be non-negative and lower_bound < upper_bound.")

    np.random.seed(random_state)

    # Generate random values for the upper triangle (excluding diagonal)
    # We need N*(N-1)/2 values for the upper triangle
    num_off_diagonal = (species_count * (species_count - 1)) // 2
    upper_triangle_values = np.random.uniform(lower_bound, upper_bound, num_off_diagonal)

    # Initialize the matrix with zeros
    matrix = np.zeros((species_count, species_count))

    # Fill the upper triangle
    idx = 0
    for i in range(species_count):
        for j in range(i + 1, species_count):
            matrix[i, j] = upper_triangle_values[idx]
            idx += 1

    # Mirror to the lower triangle to make it symmetric
    matrix = matrix + matrix.T

    # Ensure diagonal is exactly zero (though it was initialized so)
    np.fill_diagonal(matrix, 0.0)

    return matrix


def generate_synthetic_genomic_features(
    species_list: List[str],
    gene_list: List[str],
    random_state: int = 42
) -> pd.DataFrame:
    """
    Generate synthetic genomic features and drought labels for a list of species.

    Logic:
    - For each species, generate binary expression values (0 or 1) for each gene in the gene_list.
    - The label is determined by the sum of genomic markers:
      label = 1 if sum(genomic_markers) >= 12, else 0.

    Args:
        species_list (List[str]): List of species names.
        gene_list (List[str]): List of gene names to generate features for.
        random_state (int): Random seed for reproducibility.

    Returns:
        pd.DataFrame: DataFrame with species_id, genomic marker columns, and a 'label' column.
    """
    if not species_list:
        raise ValueError("Species list cannot be empty.")
    if not gene_list:
        raise ValueError("Gene list cannot be empty.")

    np.random.seed(random_state)

    n_species = len(species_list)
    n_genes = len(gene_list)

    # Generate binary expression data (0 or 1) for each gene for each species
    # Using a probability of 0.5 for each gene to be expressed (1) or not (0)
    expression_data = np.random.randint(0, 2, size=(n_species, n_genes))

    # Create DataFrame
    df = pd.DataFrame(expression_data, columns=gene_list)
    df.insert(0, 'species_id', species_list)

    # Calculate the sum of genomic markers for each species
    genomic_sum = df[gene_list].sum(axis=1)

    # Apply label logic: label = 1 if sum >= 12, else 0
    df['label'] = (genomic_sum >= 12).astype(int)

    return df


def main():
    """
    Main entry point for generating synthetic genomic features and labels.
    Loads configuration, generates the data, and saves it to the processed data directory.
    """
    # Initialize logger
    logger = DataPipelineLog()
    logger.info("Starting synthetic genomic features and labels generation.")

    # Load configuration
    try:
        config = get_config()
        validate_config(config)
    except Exception as e:
        logger.error(f"Failed to load or validate configuration: {e}")
        raise

    # Ensure output directories exist
    ensure_directories(config)

    # Extract parameters from config
    species_list = config.get("species_list", [])
    random_state = config.get("random_state", 42)

    # Define the gene list as per task specification
    gene_list = [
        "NCED3", "ABF3", "P5CS", "DREB2A", "ERF1", "ABI5", "RD29A", "COR15A",
        "LEA3", "HSP70", "SOD", "APX1", "CAT1", "GPX1", "MDHAR", "DHAR",
        "GSTU", "ZAT12", "WRKY33", "MYB96"
    ]

    if len(species_list) == 0:
        logger.error("No species found in configuration. Cannot generate genomic data.")
        raise ValueError("Species list is empty in configuration.")

    logger.info(f"Generating genomic data for {len(species_list)} species using {len(gene_list)} genes.")

    # Generate the synthetic genomic features and labels
    try:
        genomic_df = generate_synthetic_genomic_features(
            species_list=species_list,
            gene_list=gene_list,
            random_state=random_state
        )
    except Exception as e:
        logger.error(f"Genomic data generation failed: {e}")
        raise

    # Determine output path
    output_filename = "synthetic_genomics.csv"
    output_path = os.path.join(config["data_dirs"]["processed"], output_filename)

    # Save the DataFrame to CSV
    try:
        genomic_df.to_csv(output_path, index=False)
        logger.info(f"Successfully saved synthetic genomic data to {output_path}")
        logger.info(f"DataFrame shape: {genomic_df.shape}")
        logger.info(f"Label distribution:\n{genomic_df['label'].value_counts()}")
    except Exception as e:
        logger.error(f"Failed to save data to {output_path}: {e}")
        raise

    return genomic_df


if __name__ == "__main__":
    main()
