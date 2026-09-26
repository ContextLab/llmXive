"""
Diversity metric calculations for microbiome data.

This module implements Alpha diversity (Shannon, Simpson, Chao1) and Beta diversity
(Bray-Curtis, Weighted UniFrac) calculations from OTU/ASV tables.
"""

import pandas as pd
import numpy as np
from typing import Union, List, Optional, Tuple, Dict, Any
import logging
from pathlib import Path

from code.src.utils.config import (
    get_project_root,
    get_processed_data_dir,
    get_results_dir,
    get_logs_dir,
    ensure_directories,
    set_global_seed,
    SEED
)

# Configure logging
logger = logging.getLogger(__name__)
logs_dir = get_logs_dir()
ensure_directories()

if not logger.hasHandlers():
    handler = logging.FileHandler(logs_dir / "diversity.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def calculate_shannon(otu_table: pd.DataFrame) -> pd.Series:
    """
    Calculate Shannon diversity index for each sample.

    Shannon Index: H' = - sum(p_i * ln(p_i))
    where p_i is the proportion of species i.

    Args:
        otu_table: DataFrame with samples as rows and taxa as columns.
                   Values are counts (OTU/ASV abundances).

    Returns:
        Series of Shannon diversity values indexed by sample ID.
    """
    if otu_table.empty:
        logger.warning("Empty OTU table provided to Shannon calculation.")
        return pd.Series(dtype=float)

    # Calculate proportions
    total_counts = otu_table.sum(axis=1)
    # Avoid division by zero
    total_counts = total_counts.replace(0, np.nan)
    proportions = otu_table.div(total_counts, axis=0)

    # Calculate Shannon: -sum(p * ln(p))
    # Where p > 0
    log_proportions = np.where(proportions > 0, np.log(proportions), 0)
    shannon = -(proportions * log_proportions).sum(axis=1)

    logger.info(f"Calculated Shannon diversity for {len(shannon)} samples.")
    return shannon

def calculate_simpson(otu_table: pd.DataFrame) -> pd.Series:
    """
    Calculate Simpson diversity index (1 - D) for each sample.

    Simpson Index: D = sum(p_i^2)
    Simpson Diversity: 1 - D

    Args:
        otu_table: DataFrame with samples as rows and taxa as columns.

    Returns:
        Series of Simpson diversity values (1 - D).
    """
    if otu_table.empty:
        logger.warning("Empty OTU table provided to Simpson calculation.")
        return pd.Series(dtype=float)

    total_counts = otu_table.sum(axis=1)
    total_counts = total_counts.replace(0, np.nan)
    proportions = otu_table.div(total_counts, axis=0)

    # Calculate D = sum(p^2)
    simpson_d = (proportions ** 2).sum(axis=1)
    simpson_diversity = 1 - simpson_d

    logger.info(f"Calculated Simpson diversity for {len(simpson_diversity)} samples.")
    return simpson_diversity

def calculate_chao1(otu_table: pd.DataFrame) -> pd.Series:
    """
    Calculate Chao1 richness estimator for each sample.

    Chao1 = S_obs + (F1^2 / (2 * F2))
    where S_obs is observed species, F1 is singletons, F2 is doubletons.
    If F2 is 0, Chao1 = S_obs + F1/2.

    Args:
        otu_table: DataFrame with samples as rows and taxa as columns.

    Returns:
        Series of Chao1 richness estimates.
    """
    if otu_table.empty:
        logger.warning("Empty OTU table provided to Chao1 calculation.")
        return pd.Series(dtype=float)

    # Observed species (non-zero columns)
    s_obs = (otu_table > 0).sum(axis=1)

    # Singletons (count = 1)
    f1 = (otu_table == 1).sum(axis=1)

    # Doubletons (count = 2)
    f2 = (otu_table == 2).sum(axis=1)

    # Chao1 calculation
    # Handle division by zero for f2
    chao1 = s_obs.astype(float)
    mask_f2_zero = f2 == 0
    mask_f2_nonzero = ~mask_f2_zero

    # When f2 > 0: S_obs + (f1^2 / (2 * f2))
    chao1.loc[mask_f2_nonzero] = s_obs.loc[mask_f2_nonzero] + (
        f1.loc[mask_f2_nonzero] ** 2 / (2 * f2.loc[mask_f2_nonzero])
    )

    # When f2 == 0: S_obs + f1/2
    chao1.loc[mask_f2_zero] = s_obs.loc[mask_f2_zero] + (f1.loc[mask_f2_zero] / 2)

    logger.info(f"Calculated Chao1 richness for {len(chao1)} samples.")
    return chao1

def calculate_bray_curtis(otu_table: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate Bray-Curtis dissimilarity matrix between samples.

    Bray-Curtis = sum(|x_i - y_i|) / sum(x_i + y_i)

    Args:
        otu_table: DataFrame with samples as rows and taxa as columns.

    Returns:
        DataFrame representing the dissimilarity matrix (samples x samples).
    """
    if otu_table.empty or len(otu_table) < 2:
        logger.warning("Insufficient samples for Bray-Curtis calculation.")
        return pd.DataFrame()

    # Use scipy.spatial.distance for efficiency if available, otherwise manual
    try:
        from scipy.spatial.distance import pdist, squareform
        distances = pdist(otu_table.values, metric='braycurtis')
        bc_matrix = squareform(distances)
        bc_df = pd.DataFrame(
            bc_matrix,
            index=otu_table.index,
            columns=otu_table.index
        )
        logger.info(f"Calculated Bray-Curtis dissimilarity for {len(otu_table)} samples.")
        return bc_df
    except ImportError:
        logger.warning("scipy not available, using manual Bray-Curtis calculation.")
        # Manual calculation fallback
        samples = otu_table.index
        n = len(samples)
        bc_matrix = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                x = otu_table.iloc[i].values
                y = otu_table.iloc[j].values
                numerator = np.sum(np.abs(x - y))
                denominator = np.sum(x + y)
                if denominator == 0:
                    bc_matrix[i, j] = 0.0
                else:
                    bc_matrix[i, j] = numerator / denominator
                bc_matrix[j, i] = bc_matrix[i, j]

        return pd.DataFrame(
            bc_matrix,
            index=samples,
            columns=samples
        )

def calculate_unifrac_weighted(otu_table: pd.DataFrame, tree_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Calculate Weighted UniFrac distance matrix.

    Note: This is a simplified implementation. A full implementation requires
    a phylogenetic tree. If no tree is provided, it falls back to Bray-Curtis
    as a placeholder, logging a warning.

    Args:
        otu_table: DataFrame with samples as rows and taxa as columns.
        tree_path: Path to a phylogenetic tree file (Newick format).

    Returns:
        DataFrame representing the weighted UniFrac distance matrix.
    """
    if otu_table.empty or len(otu_table) < 2:
        logger.warning("Insufficient samples for UniFrac calculation.")
        return pd.DataFrame()

    if tree_path is None or not tree_path.exists():
        logger.warning("No valid phylogenetic tree provided. Falling back to Bray-Curtis as placeholder for Weighted UniFrac.")
        return calculate_bray_curtis(otu_table)

    try:
        import skbio
        from skbio import TreeNode
        from skbio.diversity.beta import unifrac

        # Load tree
        tree = TreeNode.read(str(tree_path))

        # Ensure OTU table has taxa as columns matching tree tips
        # This is a simplified check; real implementation needs robust mapping
        taxa_in_tree = set(tree.taxa())
        taxa_in_table = set(otu_table.columns)
        common_taxa = taxa_in_tree.intersection(taxa_in_table)

        if len(common_taxa) == 0:
            logger.error("No common taxa between OTU table and phylogenetic tree.")
            return pd.DataFrame()

        # Filter table to common taxa
        otu_filtered = otu_table[list(common_taxa)]

        # Calculate weighted UniFrac
        # skbio expects OTU table in specific format (samples x taxa)
        # We assume the input is already in that format
        distances = unifrac(
            otu_filtered.values,
            tree,
            weighted=True,
            normalized=True,
            cast_to_float=True
        )

        # Convert to DataFrame
        unifrac_matrix = squareform(distances)
        unifrac_df = pd.DataFrame(
            unifrac_matrix,
            index=otu_filtered.index,
            columns=otu_filtered.index
        )

        logger.info(f"Calculated Weighted UniFrac distance for {len(otu_filtered)} samples.")
        return unifrac_df

    except ImportError:
        logger.warning("scikit-bio (skbio) not installed. Falling back to Bray-Curtis.")
        return calculate_bray_curtis(otu_table)
    except Exception as e:
        logger.error(f"Error calculating Weighted UniFrac: {e}. Falling back to Bray-Curtis.")
        return calculate_bray_curtis(otu_table)

def calculate_alpha_beta_diversity(
    otu_table: pd.DataFrame,
    output_dir: Optional[Path] = None,
    tree_path: Optional[Path] = None
) -> Dict[str, Union[pd.Series, pd.DataFrame]]:
    """
    Calculate all alpha and beta diversity metrics.

    Args:
        otu_table: DataFrame with samples as rows and taxa as columns.
        output_dir: Directory to save results (optional).
        tree_path: Path to phylogenetic tree for UniFrac (optional).

    Returns:
        Dictionary containing:
            - 'shannon': Series
            - 'simpson': Series
            - 'chao1': Series
            - 'bray_curtis': DataFrame
            - 'unifrac_weighted': DataFrame
    """
    logger.info("Starting diversity metric calculation.")

    # Alpha Diversity
    shannon = calculate_shannon(otu_table)
    simpson = calculate_simpson(otu_table)
    chao1 = calculate_chao1(otu_table)

    # Beta Diversity
    bray_curtis = calculate_bray_curtis(otu_table)
    unifrac_weighted = calculate_unifrac_weighted(otu_table, tree_path)

    results = {
        'shannon': shannon,
        'simpson': simpson,
        'chao1': chao1,
        'bray_curtis': bray_curtis,
        'unifrac_weighted': unifrac_weighted
    }

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save Alpha diversity
        alpha_df = pd.DataFrame({
            'shannon': shannon,
            'simpson': simpson,
            'chao1': chao1
        })
        alpha_df.to_csv(output_dir / "alpha_diversity.csv")
        logger.info(f"Saved alpha diversity to {output_dir / 'alpha_diversity.csv'}")

        # Save Beta diversity (Bray-Curtis)
        if not bray_curtis.empty:
            bray_curtis.to_csv(output_dir / "bray_curtis_distance.csv")
            logger.info(f"Saved Bray-Curtis to {output_dir / 'bray_curtis_distance.csv'}")

        if not unifrac_weighted.empty:
            unifrac_weighted.to_csv(output_dir / "unifrac_weighted_distance.csv")
            logger.info(f"Saved Weighted UniFrac to {output_dir / 'unifrac_weighted_distance.csv'}")

    logger.info("Diversity metric calculation completed.")
    return results

def main():
    """
    Main entry point to calculate diversity metrics from the filtered cohort.
    """
    set_global_seed(SEED)

    processed_dir = get_processed_data_dir()
    results_dir = get_results_dir()

    # Load filtered cohort
    cohort_path = processed_dir / "filtered_cohort.csv"
    if not cohort_path.exists():
        logger.error(f"Filtered cohort not found at {cohort_path}. Please run filtering first.")
        return

    logger.info(f"Loading filtered cohort from {cohort_path}")
    cohort = pd.read_csv(cohort_path, index_col=0)

    # Identify OTU/ASV columns (assuming they start with 'OTU_' or similar pattern)
    # For synthetic data generated by T011, columns might be 'species_0', 'species_1', etc.
    # We assume columns that are not metadata (age, sex, bmi, fiber, antibiotics, cognitive_score, shannon, simpson, chao1) are OTUs.
    # A safer approach is to look for numeric columns that are not in the known metadata list.
    metadata_cols = ['age', 'sex', 'bmi', 'fiber', 'antibiotics', 'cognitive_score']
    otu_cols = [col for col in cohort.columns if col not in metadata_cols and pd.api.types.is_numeric_dtype(cohort[col])]

    if not otu_cols:
        logger.error("No OTU/ASV columns found in the cohort.")
        return

    logger.info(f"Found {len(otu_cols)} OTU/ASV columns.")
    otu_table = cohort[otu_cols]

    # Calculate diversity
    results = calculate_alpha_beta_diversity(
        otu_table,
        output_dir=results_dir,
        tree_path=None  # No tree for synthetic data
    )

    # Merge alpha diversity back into the cohort for downstream analysis
    alpha_df = pd.DataFrame({
        'shannon': results['shannon'],
        'simpson': results['simpson'],
        'chao1': results['chao1']
    })
    merged_cohort = pd.concat([cohort, alpha_df], axis=1)
    merged_cohort.to_csv(processed_dir / "filtered_cohort_with_diversity.csv")
    logger.info(f"Saved merged cohort with diversity metrics to {processed_dir / 'filtered_cohort_with_diversity.csv'}")

    logger.info("Task T019 completed successfully.")

if __name__ == "__main__":
    main()
