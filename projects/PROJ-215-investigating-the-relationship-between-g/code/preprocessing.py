import os
import logging
import json
import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation
from skbio import DistanceMatrix
from skbio.diversity import alpha_diversity
from skbio.diversity.beta import beta_diversity
from skbio.stats.distance import permanova
from skbio.tree import TreeNode
from biom import Table
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import warnings

from code.config import get_output_path, ensure_directories
from code.utils.logging import get_logger

logger = get_logger(__name__)

def calculate_sequencing_depth(otu_table: Table) -> float:
    """
    Calculate median sequencing depth (sum of non-zero counts per sample).
    
    Args:
        otu_table: BIOM Table object
        
    Returns:
        Median sequencing depth as float
    """
    # Convert to dense array for summing, but handle large tables carefully
    # Use sum(axis=1) to get per-sample counts
    sample_sums = otu_table.sum(axis=1)
    # Filter out zero-depth samples
    non_zero_sums = [s for s in sample_sums if s > 0]
    if not non_zero_sums:
        logger.warning("No samples with non-zero sequencing depth found.")
        return 0.0
    
    median_depth = float(np.median(non_zero_sums))
    logger.info(f"Calculated median sequencing depth: {median_depth:.2f}")
    return median_depth

def estimate_rarefaction_loss(otu_table: Table, depth: float) -> Dict[str, Any]:
    """
    Estimate the percentage of samples that would be lost if rarefied to a given depth.
    
    Args:
        otu_table: BIOM Table object
        depth: Target rarefaction depth
        
    Returns:
        Dictionary with 'loss_percentage' and 'samples_lost' count
    """
    sample_sums = otu_table.sum(axis=1)
    total_samples = len(sample_sums)
    if total_samples == 0:
        return {'loss_percentage': 0.0, 'samples_lost': 0, 'total_samples': 0}
    
    samples_below_depth = sum(1 for s in sample_sums if s < depth)
    loss_percentage = (samples_below_depth / total_samples) * 100
    
    logger.info(f"Estimated rarefaction loss at depth {depth:.2f}: {loss_percentage:.2f}% ({samples_below_depth}/{total_samples} samples)")
    
    return {
        'loss_percentage': loss_percentage,
        'samples_lost': samples_below_depth,
        'total_samples': total_samples,
        'target_depth': depth
    }

def apply_rarefaction(otu_table: Table, depth: int) -> Table:
    """
    Apply rarefaction (subsampling without replacement) to a BIOM table.
    
    Args:
        otu_table: BIOM Table object
        depth: Target rarefaction depth
        
    Returns:
        Rarefied BIOM Table
    """
    logger.info(f"Rarefying OTU table to depth {depth}")
    rarefied_table = otu_table.subsample(depth, axis='sample', replace=False)
    logger.info(f"Rarefaction complete. Samples retained: {rarefied_table.shape[1]}")
    return rarefied_table

def apply_vst(otu_table: Table) -> Table:
    """
    Apply Variance-Stabilizing Transformation (VST) as a fallback.
    Note: This is a simplified implementation using log1p transform.
    For true VST, DESeq2 or similar would be required, but skbio doesn't have it.
    
    Args:
        otu_table: BIOM Table object
        
    Returns:
        Transformed BIOM Table
    """
    logger.info("Applying VST (log1p transformation) as fallback for rarefaction")
    
    # Convert to numpy array
    data = otu_table.matrix_data.toarray()
    # Apply log1p transformation
    transformed_data = np.log1p(data)
    
    # Create new table with same observation/sample IDs
    new_table = Table(transformed_data, otu_table.ids(axis='observation'), otu_table.ids(axis='sample'))
    logger.info("VST transformation complete")
    return new_table

def filter_low_prevalence(otu_table: Table, prevalence_threshold: float = 0.001) -> Table:
    """
    Filter taxa with prevalence below a threshold.
    
    Args:
        otu_table: BIOM Table object
        prevalence_threshold: Minimum prevalence (e.g., 0.001 for 0.1%)
        
    Returns:
        Filtered BIOM Table
    """
    # Calculate prevalence (fraction of samples where taxon is present)
    sample_count = otu_table.shape[1]
    taxon_presence = (otu_table.matrix_data > 0).sum(axis=1)
    prevalence = taxon_presence / sample_count
    
    # Keep taxa above threshold
    keep_mask = np.array(prevalence) >= prevalence_threshold
    logger.info(f"Filtering taxa with prevalence < {prevalence_threshold*100:.2f}%. Keeping {keep_mask.sum()} of {len(prevalence)} taxa.")
    
    kept_taxa_ids = [tax_id for i, tax_id in enumerate(otu_table.ids(axis='observation')) if keep_mask[i]]
    filtered_table = otu_table.filter(kept_taxa_ids, axis='observation')
    
    return filtered_table

def calculate_alpha_diversity(otu_table: Table, metrics: List[str] = None) -> pd.DataFrame:
    """
    Calculate alpha diversity metrics for all samples.
    
    Args:
        otu_table: BIOM Table object
        metrics: List of metrics to calculate (default: ['shannon', 'simpson'])
        
    Returns:
        DataFrame with sample_id and diversity metrics
    """
    if metrics is None:
        metrics = ['shannon', 'simpson']
    
    logger.info(f"Calculating alpha diversity metrics: {metrics}")
    
    # skbio.alpha_diversity expects a 2D array (samples x taxa)
    # BIOM table is stored as (taxa x samples), so we transpose
    data = otu_table.matrix_data.toarray().T
    sample_ids = otu_table.ids(axis='sample')
    
    results = {}
    for metric in metrics:
        try:
            alpha_vals = alpha_diversity(metric, data, ids=sample_ids)
            results[metric] = alpha_vals
        except Exception as e:
            logger.error(f"Error calculating {metric}: {e}")
            results[metric] = np.zeros(len(sample_ids))
    
    df = pd.DataFrame(results, index=sample_ids)
    df.index.name = 'sample_id'
    df = df.reset_index()
    
    logger.info(f"Alpha diversity calculated for {len(df)} samples")
    return df

def generate_beta_diversity_matrices(
    otu_table: Table,
    metadata: Optional[pd.DataFrame] = None,
    phylogenetic_tree: Optional[TreeNode] = None
) -> Dict[str, str]:
    """
    Generate beta diversity distance matrices.
    
    Args:
        otu_table: BIOM Table object
        metadata: Optional metadata DataFrame (for sample ordering)
        phylogenetic_tree: Optional phylogenetic tree for UniFrac
        
    Returns:
        Dictionary mapping metric name to output file path
    """
    logger.info("Generating beta diversity matrices")
    
    output_files = {}
    
    # Ensure output directory exists
    output_dir = Path(get_output_path('data/processed'))
    ensure_directories([output_dir])
    
    # Prepare data for skbio
    # skbio expects samples as rows, so transpose
    data = otu_table.matrix_data.toarray().T
    sample_ids = list(otu_table.ids(axis='sample'))
    
    # 1. Bray-Curtis (always)
    try:
        logger.info("Calculating Bray-Curtis distance matrix")
        bray_curtis_dm = beta_diversity('braycurtis', data, ids=sample_ids)
        bray_curtis_path = output_dir / 'bray_curtis.npz'
        
        # Save as .npz with condensed distances and sample_ids
        # DistanceMatrix.condensed_form() returns a 1D array
        condensed = bray_curtis_dm.condensed_form()
        np.savez(
            bray_curtis_path,
            distances=condensed.astype(np.float64),
            sample_ids=np.array(sample_ids, dtype=object)
        )
        output_files['bray_curtis'] = str(bray_curtis_path)
        logger.info(f"Bray-Curtis matrix saved to {bray_curtis_path}")
        
        # Verify non-zero shape
        assert condensed.size > 0, "Bray-Curtis matrix is empty"
        
    except Exception as e:
        logger.error(f"Failed to calculate Bray-Curtis: {e}")
        # Re-raise to fail loudly
        raise RuntimeError(f"Bray-Curtis calculation failed: {e}")
    
    # 2. Weighted UniFrac (if tree present)
    if phylogenetic_tree is not None:
        try:
            logger.info("Calculating Weighted UniFrac distance matrix")
            weighted_unifrac_dm = beta_diversity('weighted_unifrac', data, ids=sample_ids, tree=phylogenetic_tree)
            weighted_unifrac_path = output_dir / 'weighted_unifrac.npz'
            
            condensed = weighted_unifrac_dm.condensed_form()
            np.savez(
                weighted_unifrac_path,
                distances=condensed.astype(np.float64),
                sample_ids=np.array(sample_ids, dtype=object)
            )
            output_files['weighted_unifrac'] = str(weighted_unifrac_path)
            logger.info(f"Weighted UniFrac matrix saved to {weighted_unifrac_path}")
            
            assert condensed.size > 0, "Weighted UniFrac matrix is empty"
            
        except Exception as e:
            logger.error(f"Failed to calculate Weighted UniFrac: {e}")
            # Log but don't fail the whole pipeline if tree is problematic
            logger.warning("Weighted UniFrac calculation skipped due to error")
    else:
        logger.warning("No phylogenetic tree provided. Skipping Weighted UniFrac.")
    
    # 3. Unweighted UniFrac (if tree present)
    if phylogenetic_tree is not None:
        try:
            logger.info("Calculating Unweighted UniFrac distance matrix")
            unweighted_unifrac_dm = beta_diversity('unweighted_unifrac', data, ids=sample_ids, tree=phylogenetic_tree)
            unweighted_unifrac_path = output_dir / 'unweighted_unifrac.npz'
            
            condensed = unweighted_unifrac_dm.condensed_form()
            np.savez(
                unweighted_unifrac_path,
                distances=condensed.astype(np.float64),
                sample_ids=np.array(sample_ids, dtype=object)
            )
            output_files['unweighted_unifrac'] = str(unweighted_unifrac_path)
            logger.info(f"Unweighted UniFrac matrix saved to {unweighted_unifrac_path}")
            
            assert condensed.size > 0, "Unweighted UniFrac matrix is empty"
            
        except Exception as e:
            logger.error(f"Failed to calculate Unweighted UniFrac: {e}")
            logger.warning("Unweighted UniFrac calculation skipped due to error")
    else:
        logger.warning("No phylogenetic tree provided. Skipping Unweighted UniFrac.")
    
    return output_files

def run_preprocessing(
    input_path: str,
    output_dir: str = 'data/processed',
    prevalence_threshold: float = 0.001,
    rarefaction_loss_threshold: float = 0.20
) -> Dict[str, Any]:
    """
    Run the full preprocessing pipeline.
    
    Args:
        input_path: Path to input BIOM table
        output_dir: Output directory
        prevalence_threshold: Threshold for filtering low-prevalence taxa
        rarefaction_loss_threshold: Threshold for switching to VST
        
    Returns:
        Dictionary with output file paths and metrics
    """
    logger.info(f"Starting preprocessing pipeline from {input_path}")
    
    # Load BIOM table
    otu_table = Table.load(input_path)
    logger.info(f"Loaded OTU table: {otu_table.shape[1]} samples, {otu_table.shape[0]} taxa")
    
    # Step 1: Calculate median sequencing depth
    median_depth = calculate_sequencing_depth(otu_table)
    median_depth_path = Path(output_dir).parent / 'interior' / 'median_depth.json'
    ensure_directories([median_depth_path.parent])
    with open(median_depth_path, 'w') as f:
        json.dump({'median_depth': median_depth}, f, indent=2)
    logger.info(f"Saved median depth to {median_depth_path}")
    
    # Step 2: Estimate rarefaction loss
    loss_info = estimate_rarefaction_loss(otu_table, median_depth)
    loss_path = Path(output_dir).parent / 'interior' / 'estimated_loss.json'
    with open(loss_path, 'w') as f:
        json.dump(loss_info, f, indent=2)
    logger.info(f"Saved estimated loss to {loss_path}")
    
    # Step 3: Apply rarefaction or VST based on loss threshold
    if loss_info['loss_percentage'] > rarefaction_loss_threshold * 100:
        logger.warning(f"Rarefaction loss ({loss_info['loss_percentage']:.2f}%) exceeds threshold ({rarefaction_loss_threshold*100:.2f}%). Using VST.")
        preprocessed_table = apply_vst(otu_table)
        method = 'vst'
    else:
        logger.info(f"Rarefaction loss ({loss_info['loss_percentage']:.2f}%) within threshold. Applying rarefaction.")
        preprocessed_table = apply_rarefaction(otu_table, int(median_depth))
        method = 'rarefaction'
    
    preprocessed_path = Path(output_dir) / 'preprocessed_otu_table.biom'
    preprocessed_table.to_hdf5(preprocessed_path, "Preprocessing pipeline")
    logger.info(f"Saved preprocessed table to {preprocessed_path}")
    
    # Step 4: Filter low prevalence taxa
    filtered_table = filter_low_prevalence(preprocessed_table, prevalence_threshold)
    filtered_path = Path(output_dir) / 'filtered_otu_table.biom'
    filtered_table.to_hdf5(filtered_path, "Filtered OTU table")
    logger.info(f"Saved filtered table to {filtered_path}")
    
    # Step 5: Calculate alpha diversity
    alpha_metrics = calculate_alpha_diversity(filtered_table)
    alpha_path = Path(output_dir) / 'alpha_metrics.csv'
    alpha_metrics.to_csv(alpha_path, index=False)
    logger.info(f"Saved alpha metrics to {alpha_path}")
    
    # Step 6: Generate beta diversity matrices (T016b)
    # Note: We need a phylogenetic tree for UniFrac. If not provided, skip.
    # For now, we assume tree is not available unless explicitly loaded.
    beta_outputs = generate_beta_diversity_matrices(filtered_table, phylogenetic_tree=None)
    
    results = {
        'method': method,
        'median_depth': median_depth,
        'loss_percentage': loss_info['loss_percentage'],
        'samples_retained': filtered_table.shape[1],
        'taxa_retained': filtered_table.shape[0],
        'alpha_metrics_path': str(alpha_path),
        'beta_diversity_files': beta_outputs
    }
    
    logger.info(f"Preprocessing complete. Results: {results}")
    return results

def main():
    """Main entry point for preprocessing script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess microbiome data')
    parser.add_argument('--input', type=str, required=True, help='Input BIOM table path')
    parser.add_argument('--output', type=str, default='data/processed', help='Output directory')
    parser.add_argument('--prevalence-threshold', type=float, default=0.001, help='Prevalence threshold for filtering')
    parser.add_argument('--rarefaction-loss-threshold', type=float, default=0.20, help='Loss threshold for VST fallback')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    results = run_preprocessing(
        input_path=args.input,
        output_dir=args.output,
        prevalence_threshold=args.prevalence_threshold,
        rarefaction_loss_threshold=args.rarefaction_loss_threshold
    )
    
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()