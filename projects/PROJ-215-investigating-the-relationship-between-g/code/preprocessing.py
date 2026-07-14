import os
import logging
import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation
from sklearn.preprocessing import PowerTransformer
import skbio
from skbio.diversity import alpha_diversity
from skbio.diversity.beta import beta_diversity
from skbio.stats.distance import DistanceMatrix
from skbio import OrdinationResults
from skbio.tree import TreeNode
from skbio.diversity.beta._unifrac import weighted_unifrac, unweighted_unifrac
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import json

# Import config utilities
from code.config import ensure_directories, get_output_path, calculate_median_depth, estimate_rarefaction_loss
from code.utils.logging import get_logger

# Set up logger
logger = get_logger(__name__)

def calculate_sequencing_depth(counts_df: pd.DataFrame) -> pd.Series:
    """Calculate total sequencing depth (sum of counts) for each sample."""
    return counts_df.sum(axis=1)

def apply_rarefaction(counts_df: pd.DataFrame, depth: int, random_seed: int = 42) -> pd.DataFrame:
    """
    Rarefy the OTU table to a specified sequencing depth.
    Uses skbio's rarefy function which performs subsampling without replacement.
    """
    logger.info(f"Rarefying to depth {depth} with seed {random_seed}")
    # skbio expects a 2D array or DataFrame with samples as rows
    rarefied = counts_df.apply(
        lambda row: skbio.diversity.alpha.rarefy(row.values, depth, seed=random_seed),
        axis=1
    )
    # Convert back to DataFrame with original index and columns
    rarefied_df = pd.DataFrame(rarefied.tolist(), index=counts_df.index, columns=counts_df.columns)
    return rarefied_df

def apply_vst(counts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Variance Stabilizing Transformation (VST) using sklearn's PowerTransformer.
    This approximates a VST for count data.
    """
    logger.info("Applying Variance Stabilizing Transformation (VST)")
    pt = PowerTransformer(method='yeo-johnson', standardize=True)
    # PowerTransformer expects 2D array, transform each column (taxon)
    transformed = pt.fit_transform(counts_df.values)
    transformed_df = pd.DataFrame(transformed, index=counts_df.index, columns=counts_df.columns)
    return transformed_df

def filter_low_prevalence(counts_df: pd.DataFrame, prevalence_threshold: float = 0.001) -> pd.DataFrame:
    """
    Filter taxa that appear in less than `prevalence_threshold` proportion of samples.
    Prevalence is calculated as the fraction of samples with non-zero counts.
    """
    logger.info(f"Filtering taxa with prevalence < {prevalence_threshold}")
    prevalence = (counts_df > 0).sum(axis=0) / counts_df.shape[0]
    filtered_df = counts_df.loc[:, prevalence >= prevalence_threshold]
    removed_count = counts_df.shape[1] - filtered_df.shape[1]
    logger.info(f"Removed {removed_count} low-prevalence taxa. Retained {filtered_df.shape[1]} taxa.")
    return filtered_df

def calculate_alpha_diversity(counts_df: pd.DataFrame, metrics: List[str] = None) -> pd.DataFrame:
    """
    Calculate alpha diversity metrics for each sample.
    Default metrics: Shannon, Simpson.
    """
    if metrics is None:
        metrics = ['shannon', 'simpson']
    
    logger.info(f"Calculating alpha diversity metrics: {metrics}")
    alpha_results = {}
    for metric in metrics:
        try:
            result = alpha_diversity(metric=metric, counts=counts_df.values, ids=counts_df.index)
            alpha_results[metric] = result
        except Exception as e:
            logger.error(f"Failed to calculate {metric} alpha diversity: {e}")
            raise
    
    alpha_df = pd.DataFrame(alpha_results, index=counts_df.index)
    return alpha_df

def generate_beta_diversity_matrices(
    counts_df: pd.DataFrame, 
    metadata: Optional[pd.DataFrame] = None,
    tree: Optional[TreeNode] = None,
    output_dir: str = "data/processed"
) -> Dict[str, DistanceMatrix]:
    """
    Generate Beta diversity distance matrices: Bray-Curtis, Weighted UniFrac, Unweighted UniFrac.
    
    Parameters:
    -----------
    counts_df : pd.DataFrame
        OTU table with samples as rows and taxa as columns.
    metadata : pd.DataFrame, optional
        Sample metadata. Required for UniFrac if tree is provided (to map samples).
    tree : TreeNode, optional
        Phylogenetic tree for UniFrac calculations. If None, UniFrac will be skipped.
    output_dir : str
        Directory to save the output .npz file.
    
    Returns:
    --------
    dict
        Dictionary of DistanceMatrix objects keyed by metric name.
    """
    ensure_directories([output_dir])
    logger.info("Generating Beta diversity distance matrices...")
    
    matrices = {}
    
    # 1. Bray-Curtis (always available)
    try:
        logger.info("Calculating Bray-Curtis distance matrix...")
        bray_curtis_dm = beta_diversity(
            metric='braycurtis',
            counts=counts_df.values,
            ids=counts_df.index,
            validate=True
        )
        matrices['bray_curtis'] = bray_curtis_dm
        logger.info(f"Bray-Curtis matrix shape: {bray_curtis_dm.shape}")
    except Exception as e:
        logger.error(f"Failed to calculate Bray-Curtis: {e}")
        raise

    # 2. UniFrac (requires tree)
    if tree is not None:
        try:
            logger.info("Calculating Weighted UniFrac distance matrix...")
            weighted_unifrac_dm = weighted_unifrac(
                counts=counts_df.values,
                ids=counts_df.index,
                tree=tree,
                weighted=True,
                validate=True
            )
            matrices['weighted_unifrac'] = weighted_unifrac_dm
            logger.info(f"Weighted UniFrac matrix shape: {weighted_unifrac_dm.shape}")
        except Exception as e:
            logger.error(f"Failed to calculate Weighted UniFrac: {e}")
            # Do not raise, just log. UniFrac might fail if tree topology doesn't match taxa.

        try:
            logger.info("Calculating Unweighted UniFrac distance matrix...")
            unweighted_unifrac_dm = unweighted_unifrac(
                counts=counts_df.values,
                ids=counts_df.index,
                tree=tree,
                weighted=False,
                validate=True
            )
            matrices['unweighted_unifrac'] = unweighted_unifrac_dm
            logger.info(f"Unweighted UniFrac matrix shape: {unweighted_unifrac_dm.shape}")
        except Exception as e:
            logger.error(f"Failed to calculate Unweighted UniFrac: {e}")
    else:
        logger.warning("No phylogenetic tree provided. Skipping UniFrac calculations.")

    # Save to .npz
    output_path = get_output_path(output_dir, "beta_distance_matrices.npz")
    logger.info(f"Saving beta diversity matrices to {output_path}")
    
    with open(output_path, 'wb') as f:
        np.savez(
            f,
            bray_curtis=matrices['bray_curtis'].data,
            bray_curtis_ids=matrices['bray_curtis'].ids,
            **{
                k: v.data for k, v in matrices.items() if k != 'bray_curtis'
            }
        )
        # Save IDs separately for non-Bray-Curtis if needed, or just rely on index
        # For simplicity, we assume all matrices share the same sample order as counts_df
        # If UniFrac failed, those keys won't be in the dict, so we need to handle that in loading
        # Let's save a metadata file for IDs to be safe
        np.savez(
            f,
            sample_ids=counts_df.index.values
        )
    
    # Actually, the above savez is tricky because we can't easily append to the file in one go with variable keys.
    # Let's do it properly:
    save_dict = {
        'bray_curtis': matrices['bray_curtis'].data,
        'bray_curtis_ids': matrices['bray_curtis'].ids,
        'sample_ids': counts_df.index.values
    }
    
    for key, dm in matrices.items():
        if key != 'bray_curtis':
            save_dict[key] = dm.data
            save_dict[f'{key}_ids'] = dm.idss
    
    # Re-save correctly
    np.savez(output_path, **save_dict)
    
    logger.info(f"Beta diversity matrices saved successfully to {output_path}")
    return matrices

def run_preprocessing(
    counts_df: pd.DataFrame,
    metadata_df: Optional[pd.DataFrame] = None,
    tree: Optional[TreeNode] = None,
    rarefaction_depth: Optional[int] = None,
    prevalence_threshold: float = 0.001,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, DistanceMatrix]]:
    """
    Run the full preprocessing pipeline:
    1. Calculate sequencing depth
    2. Apply rarefaction or VST
    3. Filter low prevalence taxa
    4. Calculate Alpha diversity
    5. Generate Beta diversity matrices
    
    Returns:
    --------
    Tuple containing:
    - preprocessed_counts_df: The cleaned OTU table
    - alpha_metrics_df: DataFrame with alpha diversity metrics
    - beta_matrices_dict: Dictionary of beta diversity DistanceMatrix objects
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Calculate sequencing depth
    depths = calculate_sequencing_depth(counts_df)
    median_depth = depths.median()
    logger.info(f"Median sequencing depth: {median_depth}")
    
    # 2. Determine rarefaction depth or VST
    if rarefaction_depth is None:
        rarefaction_depth = calculate_median_depth(depths)
    
    estimated_loss = estimate_rarefaction_loss(depths, rarefaction_depth)
    logger.info(f"Estimated sample loss at depth {rarefaction_depth}: {estimated_loss:.2%}")
    
    if median_depth < 1000 or estimated_loss > 0.20:
        logger.warning("Median depth < 1000 or estimated loss > 20%. Applying VST fallback.")
        processed_counts = apply_vst(counts_df)
    else:
        processed_counts = apply_rarefaction(counts_df, rarefaction_depth, random_seed)
    
    # 3. Filter low prevalence taxa
    processed_counts = filter_low_prevalence(processed_counts, prevalence_threshold)
    
    # 4. Calculate Alpha diversity
    alpha_metrics = calculate_alpha_diversity(processed_counts)
    
    # 5. Generate Beta diversity matrices
    beta_matrices = generate_beta_diversity_matrices(processed_counts, metadata_df, tree)
    
    logger.info("Preprocessing pipeline completed successfully.")
    return processed_counts, alpha_metrics, beta_matrices

def main():
    """
    Main entry point for preprocessing script.
    Loads data from data/raw, runs preprocessing, and saves outputs.
    """
    logger.info("Running preprocessing main...")
    
    # Load data (assuming data_ingestion has run and created the files)
    # We expect: data/raw/otu_table.csv, data/raw/sample_metadata.csv, data/raw/phylogeny.tre
    otu_path = "data/raw/otu_table.csv"
    meta_path = "data/raw/sample_metadata.csv"
    tree_path = "data/raw/phylogeny.tre"
    
    if not os.path.exists(otu_path):
        logger.error(f"OTU table not found at {otu_path}. Please run data_ingestion first.")
        return
    
    logger.info(f"Loading OTU table from {otu_path}")
    counts_df = pd.read_csv(otu_path, index_col=0)
    
    metadata_df = None
    if os.path.exists(meta_path):
        logger.info(f"Loading metadata from {meta_path}")
        metadata_df = pd.read_csv(meta_path, index_col=0)
    
    tree = None
    if os.path.exists(tree_path):
        logger.info(f"Loading phylogenetic tree from {tree_path}")
        try:
            tree = TreeNode.read(tree_path)
        except Exception as e:
            logger.warning(f"Failed to load tree: {e}. UniFrac calculations will be skipped.")
    
    # Run preprocessing
    preprocessed_counts, alpha_metrics, beta_matrices = run_preprocessing(
        counts_df=counts_df,
        metadata_df=metadata_df,
        tree=tree
    )
    
    # Save preprocessed counts and alpha metrics
    output_dir = "data/processed"
    ensure_directories([output_dir])
    
    preprocessed_counts.to_csv(get_output_path(output_dir, "preprocessed_counts.csv"))
    alpha_metrics.to_csv(get_output_path(output_dir, "alpha_metrics.csv"))
    
    logger.info("Preprocessing complete. Files saved to data/processed/")

if __name__ == "__main__":
    main()
