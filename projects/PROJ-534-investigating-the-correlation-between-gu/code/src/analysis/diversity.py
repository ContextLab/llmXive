import pandas as pd
import numpy as np
from typing import Union, List, Optional, Tuple, Dict, Any
import logging
from pathlib import Path

from code.src.utils.config import (
    get_project_root,
    get_processed_data_dir,
    get_results_dir,
    set_global_seed,
    get_config
)

# Configure logging
logger = logging.getLogger(__name__)

def calculate_shannon(otu_row: pd.Series) -> float:
    """
    Calculate Shannon diversity index for a single OTU row.
    H' = - sum(pi * ln(pi))
    where pi is the proportion of reads for species i.
    """
    counts = otu_row.values
    total = counts.sum()
    if total == 0:
        return 0.0
    
    # Proportions
    pi = counts / total
    # Filter out zeros to avoid log(0)
    pi = pi[pi > 0]
    shannon = -np.sum(pi * np.log(pi))
    return float(shannon)

def calculate_simpson(otu_row: pd.Series) -> float:
    """
    Calculate Simpson diversity index for a single OTU row.
    D = 1 - sum(pi^2)
    where pi is the proportion of reads for species i.
    """
    counts = otu_row.values
    total = counts.sum()
    if total == 0:
        return 0.0
    
    pi = counts / total
    simpson = 1 - np.sum(pi ** 2)
    return float(simpson)

def calculate_chao1(otu_row: pd.Series) -> float:
    """
    Calculate Chao1 richness estimator for a single OTU row.
    Chao1 = S_obs + (F1^2 / (2 * F2)) if F2 > 0, else S_obs + F1
    where S_obs is observed species, F1 is singletons, F2 is doubletons.
    """
    counts = otu_row.values
    # Species present (count > 0)
    presence = counts > 0
    s_obs = np.sum(presence)
    
    if s_obs == 0:
        return 0.0
    
    f1 = np.sum(counts == 1)  # Singletons
    f2 = np.sum(counts == 2)  # Doubletons
    
    if f2 > 0:
        chao1 = s_obs + (f1 ** 2) / (2 * f2)
    else:
        chao1 = s_obs + f1
    
    return float(chao1)

def calculate_bray_curtis(df: pd.DataFrame, otu_cols: List[str]) -> pd.DataFrame:
    """
    Calculate Bray-Curtis dissimilarity matrix between samples.
    BC_ij = 1 - (2 * sum(min(x_i, x_j)) / (sum(x_i) + sum(x_j)))
    Returns a DataFrame with samples as index and columns, symmetric matrix.
    """
    if len(otu_cols) == 0:
        raise ValueError("No OTU columns provided for Bray-Curtis calculation")
    
    otu_matrix = df[otu_cols].values
    n_samples = len(df)
    
    # Initialize distance matrix
    bc_matrix = np.zeros((n_samples, n_samples))
    
    for i in range(n_samples):
        for j in range(i, n_samples):
            if i == j:
                bc_matrix[i, j] = 0.0
            else:
                x_i = otu_matrix[i]
                x_j = otu_matrix[j]
                
                sum_min = np.sum(np.minimum(x_i, x_j))
                sum_total = np.sum(x_i) + np.sum(x_j)
                
                if sum_total == 0:
                    bc_matrix[i, j] = 0.0
                else:
                    bc_matrix[i, j] = 1 - (2 * sum_min / sum_total)
                
                bc_matrix[j, i] = bc_matrix[i, j]
    
    # Create DataFrame with participant_id as index
    bc_df = pd.DataFrame(
        bc_matrix,
        index=df.index,
        columns=df.index
    )
    
    return bc_df

def calculate_unifrac_weighted(df: pd.DataFrame, otu_cols: List[str], 
                               phylogenetic_tree: Optional[Any] = None) -> pd.DataFrame:
    """
    Calculate Weighted UniFrac distance matrix.
    
    Note: This is a simplified implementation. For full phylogenetic UniFrac,
    a phylogenetic tree (newick format) is required. If no tree is provided,
    we fall back to a weighted Bray-Curtis approximation (which is not true
    UniFrac but serves as a placeholder if tree is missing).
    
    In a real pipeline, this would use skbio.stats.distance.unifrac.
    """
    if phylogenetic_tree is None:
        logger.warning("No phylogenetic tree provided. Using weighted Bray-Curtis as proxy for UniFrac.")
        return calculate_bray_curtis(df, otu_cols)
    
    # If a tree is provided, we would compute true weighted UniFrac here.
    # For now, this is a placeholder that assumes the tree is valid and
    # delegates to a hypothetical skbio implementation.
    try:
        import skbio
        from skbio.stats.distance import unifrac
        
        # Convert to OTU table format expected by skbio
        # This assumes df has participant_id as index and OTU counts as columns
        otu_table = skbio.OTUTable(
            df[otu_cols].values,
            sample_ids=df.index.tolist(),
            otu_ids=otu_cols
        )
        
        # Compute weighted UniFrac
        distance_matrix = unifrac(
            otu_table,
            phylogenetic_tree,
            weighted=True,
            normalized=True
        )
        
        return pd.DataFrame(
            distance_matrix.data,
            index=distance_matrix.ids,
            columns=distance_matrix.ids
        )
    except ImportError:
        logger.error("scikit-bio not installed. Cannot compute true UniFrac.")
        raise
    except Exception as e:
        logger.error(f"Error computing UniFrac: {e}")
        # Fallback to Bray-Curtis if UniFrac fails
        logger.warning("Falling back to weighted Bray-Curtis.")
        return calculate_bray_curtis(df, otu_cols)

def calculate_alpha_beta_diversity(
    cohort_df: pd.DataFrame,
    otu_columns: List[str],
    participant_id_col: str = 'participant_id'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate all alpha and beta diversity metrics for the cohort.
    
    Args:
        cohort_df: DataFrame containing participant data with OTU columns
        otu_columns: List of column names representing OTU counts
        participant_id_col: Column name for participant IDs
    
    Returns:
        Tuple of (alpha_metrics_df, beta_metrics_df)
        - alpha_metrics_df: DataFrame with Shannon, Simpson, Chao1 per participant
        - beta_metrics_df: Distance matrices (Bray-Curtis, UniFrac) as DataFrames
    """
    logger.info(f"Calculating diversity metrics for {len(cohort_df)} participants")
    logger.info(f"OTU columns: {otu_columns}")
    
    # Calculate alpha diversity
    alpha_metrics = pd.DataFrame()
    alpha_metrics[participant_id_col] = cohort_df[participant_id_col]
    
    # Apply calculations row-wise
    alpha_metrics['shannon_diversity'] = cohort_df.apply(
        lambda row: calculate_shannon(row[otu_columns]), axis=1
    )
    alpha_metrics['simpson_diversity'] = cohort_df.apply(
        lambda row: calculate_simpson(row[otu_columns]), axis=1
    )
    alpha_metrics['chao1'] = cohort_df.apply(
        lambda row: calculate_chao1(row[otu_columns]), axis=1
    )
    
    # Calculate beta diversity
    bray_curtis_matrix = calculate_bray_curtis(cohort_df, otu_columns)
    
    # For UniFrac, we attempt to load a tree if available
    unifrac_matrix = None
    tree_path = get_project_root() / "data" / "phylogeny" / "tree.nwk"
    if tree_path.exists():
        try:
            import skbio
            tree = skbio.TreeNode.read(str(tree_path))
            unifrac_matrix = calculate_unifrac_weighted(cohort_df, otu_columns, tree)
        except Exception as e:
            logger.warning(f"Could not load phylogenetic tree: {e}. Skipping UniFrac.")
            unifrac_matrix = bray_curtis_matrix  # Fallback
    else:
        logger.warning("No phylogenetic tree found. Using Bray-Curtis as UniFrac proxy.")
        unifrac_matrix = bray_curtis_matrix
    
    beta_metrics = {
        'bray_curtis': bray_curtis_matrix,
        'unifrac_weighted': unifrac_matrix
    }
    
    return alpha_metrics, beta_metrics

def main():
    """
    Main entry point for diversity calculation.
    Reads filtered cohort from data/processed/filtered_cohort.csv
    and outputs alpha metrics to data/processed/alpha_diversity.csv
    and beta metrics to data/results/beta_diversity_matrix.csv (Bray-Curtis)
    """
    set_global_seed()
    
    # Paths
    processed_dir = get_processed_data_dir()
    results_dir = get_results_dir()
    input_file = processed_dir / "filtered_cohort.csv"
    alpha_output = processed_dir / "alpha_diversity.csv"
    beta_output = results_dir / "beta_diversity_matrix.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Filtered cohort not found at {input_file}")
    
    logger.info(f"Loading filtered cohort from {input_file}")
    cohort_df = pd.read_csv(input_file)
    
    # Identify OTU columns (assuming they start with 'otu_' or contain 'otu')
    # Based on synthetic_gen, OTU columns are named 'otu_1', 'otu_2', etc.
    otu_columns = [col for col in cohort_df.columns if col.startswith('otu_')]
    
    if len(otu_columns) == 0:
        raise ValueError("No OTU columns found in filtered cohort. Check column naming.")
    
    logger.info(f"Found {len(otu_columns)} OTU columns")
    
    # Calculate diversity
    alpha_metrics, beta_metrics = calculate_alpha_beta_diversity(
        cohort_df, otu_columns
    )
    
    # Save alpha diversity
    alpha_metrics.to_csv(alpha_output, index=False)
    logger.info(f"Alpha diversity saved to {alpha_output}")
    
    # Save beta diversity (Bray-Curtis as flat CSV)
    # Convert distance matrix to long format for storage
    bray_curtis_df = beta_metrics['bray_curtis']
    bray_curtis_long = bray_curtis_df.reset_index().melt(
        id_vars='index',
        var_name='sample_2',
        value_name='bray_curtis_distance'
    )
    bray_curtis_long.columns = ['sample_1', 'sample_2', 'bray_curtis_distance']
    bray_curtis_long.to_csv(beta_output, index=False)
    logger.info(f"Beta diversity (Bray-Curtis) saved to {beta_output}")
    
    # Save UniFrac if available and different
    if 'unifrac_weighted' in beta_metrics:
        unifrac_df = beta_metrics['unifrac_weighted']
        unifrac_long = unifrac_df.reset_index().melt(
            id_vars='index',
            var_name='sample_2',
            value_name='unifrac_weighted_distance'
        )
        unifrac_long.columns = ['sample_1', 'sample_2', 'unifrac_weighted_distance']
        unifrac_output = results_dir / "unifrac_weighted_matrix.csv"
        unifrac_long.to_csv(unifrac_output, index=False)
        logger.info(f"UniFrac weighted saved to {unifrac_output}")
    
    return alpha_metrics, beta_metrics

if __name__ == "__main__":
    main()
