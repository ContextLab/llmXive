"""
Data generation module for synthetic datasets and matrices.

This module generates synthetic genomic features and phylogenetic matrices
for the drought tolerance prediction pipeline.

IMPORTANT: This module is ONLY to be used in VALIDATION_MODE when real data
fetches fail. It explicitly invalidates biological claims (FR-001, SC-001).
"""
import os
import sys
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from pathlib import Path
import json
import logging

# Import config to access VALIDATION_MODE and gene lists
from config import get_config, ensure_directories, TRAINING_GENES, VALIDATION_GENES
from utils.logging import DataPipelineLog

# Configure logging for this module
logger = DataPipelineLog("generate")

def generate_synthetic_genomic_features(n_samples: int = 50) -> pd.DataFrame:
    """
    Generate synthetic genomic features and drought labels.

    Logic:
    - Trigger: Run ONLY if VALIDATION_MODE is True AND T011b returned FAILED.
    - Gene List: 20 specific stress-response genes.
    - Label Logic: prob = sigmoid(sum(hidden_genes) - 2) + noise(0.1, seed=42)
    - Hidden Genes: Subset of random genes from training genes (deterministic via seed).
    - Label: 1 if random() < prob else 0.

    Output:
    - data/processed/synthetic_genomics.csv

    Verification:
    - Output CSV has N rows.
    - Columns match gene list.
    - Label distribution mean is within 5% of expected sigmoid probability
      using a Chi-Square Goodness-of-Fit test (p-value > 0.05).
    """
    config = get_config()

    # Check if we are in VALIDATION_MODE
    if not config.get('VALIDATION_MODE', False):
        logger.log_warning("VALIDATION_MODE is False. Synthetic data generation is forbidden in Production.")
        # In Production mode, we should not generate synthetic data.
        # This function should ideally not be called, but if it is, we raise an error or return empty.
        # Per task logic: "Trigger: Run ONLY if VALIDATION_MODE is True".
        # We raise a critical error if called outside validation mode to prevent accidental usage.
        raise RuntimeError("CRITICAL: Synthetic data generation attempted in Production Mode (VALIDATION_MODE=False). Aborting.")

    # Check if real genomic data is detected (simulated by checking if T011b succeeded)
    # Since T011b status is not directly passed here, we rely on the caller (run_pipeline)
    # to ensure this is only called when T011b failed.
    # However, we add a check for the output file of T011b if it exists.
    # Assuming T011b would write to a specific location if successful.
    # For this implementation, we assume the caller handles the logic.
    # We proceed with generation.

    # Log the scope reduction explicitly
    logger.log_critical("Scope Reduction: Synthetic data used, invalidates FR-001/SC-001 biological claims")

    # Set random seed for reproducibility
    np.random.seed(42)
    random_state = np.random.RandomState(42)

    # Gene List (20)
    gene_list = TRAINING_GENES
    if len(gene_list) != 20:
        logger.log_error(f"Expected 20 training genes, got {len(gene_list)}. Using provided list.")

    # Select hidden genes (subset of random genes from the training genes)
    # The task says "Select a subset of random genes from the training genes (deterministic via seed)"
    # Let's select 5 hidden genes to drive the signal.
    n_hidden = 5
    hidden_gene_indices = random_state.choice(len(gene_list), size=n_hidden, replace=False)
    hidden_genes = [gene_list[i] for i in hidden_gene_indices]
    logger.log_info(f"Hidden genes for label generation: {hidden_genes}")

    # Generate synthetic data
    data = {}
    for gene in gene_list:
        # Generate binary features (0/1) for each gene
        # Probability of 1 is 0.5 for most genes, but we can add some noise
        data[gene] = random_state.binomial(1, 0.5, n_samples)

    # Create DataFrame
    df = pd.DataFrame(data)

    # Generate labels
    # prob = sigmoid(sum(hidden_genes) - 2) + noise(0.1, seed=42)
    # Sigmoid function: 1 / (1 + exp(-x))
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    # Calculate sum of hidden genes for each sample
    hidden_sum = df[hidden_genes].sum(axis=1)

    # Calculate probability
    # noise(0.1, seed=42) -> Gaussian noise with std=0.1
    noise = random_state.normal(0, 0.1, n_samples)
    probs = sigmoid(hidden_sum - 2) + noise

    # Clip probabilities to [0, 1]
    probs = np.clip(probs, 0, 1)

    # Generate labels: 1 if random() < prob else 0
    labels = (random_state.random(n_samples) < probs).astype(int)

    # Add label column
    df['label'] = labels

    # Verification: Chi-Square Goodness-of-Fit test
    # Expected mean=0.5, bins=10, uniform distribution across bins
    # We check if the label distribution is within 5% of the expected sigmoid probability
    # and perform a Chi-Square test for uniformity across bins.

    # Expected mean probability (theoretical)
    # We can calculate the expected mean of the sigmoid function over the distribution of hidden_sum
    # But for simplicity, we check if the observed mean is within 5% of the theoretical mean
    # Theoretical mean of sigmoid(hidden_sum - 2) where hidden_sum ~ Binomial(5, 0.5)
    # Let's compute it empirically from the generated probs
    expected_mean = np.mean(probs)
    observed_mean = np.mean(labels)

    logger.log_info(f"Expected label mean (from sigmoid): {expected_mean:.4f}")
    logger.log_info(f"Observed label mean: {observed_mean:.4f}")

    # Check if within 5%
    if abs(observed_mean - expected_mean) > 0.05 * expected_mean:
        logger.log_warning(f"Label distribution mean deviates by more than 5% from expected. Observed: {observed_mean:.4f}, Expected: {expected_mean:.4f}")
    else:
        logger.log_info("Label distribution mean is within 5% of expected.")

    # Chi-Square Goodness-of-Fit test for uniform distribution across bins
    # We bin the labels (0 and 1) and check if they are uniformly distributed?
    # The task says: "bins=10, uniform distribution across bins"
    # This is a bit ambiguous for binary labels. Let's interpret it as:
    # We bin the PROBABILITIES into 10 bins and check if the labels are uniformly distributed within those bins?
    # Or we check if the labels are uniformly distributed across 10 bins of the probability space?
    # Let's do: Bin the probabilities into 10 bins, and for each bin, check the proportion of 1s.
    # If the model is perfect, the proportion should match the probability.
    # But the task says "uniform distribution across bins", which might mean the labels themselves are uniformly distributed?
    # Let's re-read: "label distribution mean is within 5% of expected sigmoid probability using a Chi-Square Goodness-of-Fit test (p-value > 0.05, expected mean=0.5, bins=10, uniform distribution across bins)"
    # This suggests we are testing if the labels are uniformly distributed (mean=0.5) across 10 bins?
    # But labels are binary. Let's assume we are testing if the labels are uniformly distributed (50% 0, 50% 1) overall.
    # We can use a Chi-Square test for goodness of fit to a uniform distribution (50% 0, 50% 1).

    # Chi-Square test for uniform distribution of labels (0 and 1)
    observed_counts = np.bincount(labels, minlength=2)
    expected_counts = np.array([n_samples / 2, n_samples / 2])

    # Chi-Square statistic
    chi2 = np.sum((observed_counts - expected_counts) ** 2 / expected_counts)
    # Degrees of freedom = 1 (2 categories - 1)
    p_value = 1 - stats.chi2.cdf(chi2, 1)

    logger.log_info(f"Chi-Square Goodness-of-Fit test for uniform label distribution: chi2={chi2:.4f}, p-value={p_value:.4f}")

    if p_value > 0.05:
        logger.log_info("Label distribution is consistent with uniform distribution (p > 0.05).")
    else:
        logger.log_warning(f"Label distribution deviates significantly from uniform (p < 0.05).")

    # Ensure output directory exists
    ensure_directories([Path("data/processed")])

    # Save to CSV
    output_path = Path("data/processed/synthetic_genomics.csv")
    df.to_csv(output_path, index=False)
    logger.log_info(f"Synthetic genomic data saved to {output_path}")

    return df

def generate_synthetic_phylogenetic_matrix(n_species: int = 50) -> np.ndarray:
    """
    Generate a synthetic phylogenetic distance matrix.

    Logic:
    - Generate an N x N symmetric matrix (N=species count)
    - Zero diagonal
    - Off-diagonal values uniformly distributed between 0.01 and 1.0
    - Random seed: 42

    Output:
    - data/processed/synthetic_phylo_matrix.npy

    Verification:
    - Diagonal is zero
    - Off-diagonals > 0
    - Shape matches N
    - File exists
    """
    config = get_config()

    # Set random seed
    np.random.seed(42)

    # Generate symmetric matrix
    matrix = np.random.uniform(0.01, 1.0, size=(n_species, n_species))
    matrix = (matrix + matrix.T) / 2  # Make symmetric

    # Set diagonal to zero
    np.fill_diagonal(matrix, 0.0)

    # Ensure output directory exists
    ensure_directories([Path("data/processed")])

    # Save to .npy
    output_path = Path("data/processed/synthetic_phylo_matrix.npy")
    np.save(output_path, matrix)
    logger.log_info(f"Synthetic phylogenetic matrix saved to {output_path}")

    return matrix

def compute_real_phylogenetic_matrix(tree_path: str) -> Optional[np.ndarray]:
    """
    Compute a real phylogenetic distance matrix from a Newick tree file.

    Logic:
    - If tree_path exists, parse and compute distances.
    - Otherwise, return None.

    Output:
    - data/processed/real_phylo_matrix.npy (if successful)
    """
    if not os.path.exists(tree_path):
        logger.log_warning(f"Real tree file not found: {tree_path}. Skipping real phylogenetic matrix computation.")
        return None

    # Try to parse the tree and compute distances
    # We'll use ete3 if available, otherwise fall back to a simple parser or raise an error
    try:
        from ete3 import Tree
        tree = Tree(tree_path)
        # Get all leaf names
        leaves = tree.get_leaf_names()
        n = len(leaves)

        # Compute distance matrix
        matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i + 1, n):
                dist = tree.get_distance(leaves[i], leaves[j])
                matrix[i, j] = dist
                matrix[j, i] = dist

        # Ensure output directory exists
        ensure_directories([Path("data/processed")])

        # Save to .npy
        output_path = Path("data/processed/real_phylo_matrix.npy")
        np.save(output_path, matrix)
        logger.log_info(f"Real phylogenetic matrix saved to {output_path}")

        return matrix
    except ImportError:
        logger.log_error("ete3 library not found. Cannot parse Newick tree.")
        return None
    except Exception as e:
        logger.log_error(f"Error computing real phylogenetic matrix: {e}")
        return None

def main():
    """
    Main entry point for synthetic data generation.
    """
    config = get_config()

    # Check if VALIDATION_MODE is True
    if not config.get('VALIDATION_MODE', False):
        logger.log_warning("VALIDATION_MODE is False. Skipping synthetic data generation.")
        return

    # Check if T011b failed (we assume this is handled by the caller, but we can check for a flag)
    # For now, we proceed with generation.

    # Generate synthetic genomic features
    df = generate_synthetic_genomic_features(n_samples=50)

    # Generate synthetic phylogenetic matrix
    matrix = generate_synthetic_phylogenetic_matrix(n_species=50)

    logger.log_info("Synthetic data generation completed.")

if __name__ == "__main__":
    main()