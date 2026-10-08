import os
import logging
import json
import numpy as np
import pandas as pd
from scipy.stats import median_abs_deviation
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import biom
from sklearn.preprocessing import PowerTransformer
from config import get_output_path, ensure_directories
from utils.logging import get_logger

logger = get_logger(__name__)

def calculate_sequencing_depth(input_path: str) -> Dict[str, float]:
    """
    Step 1: Calculate median sequencing depth.
    Input: data/raw/otu_table.biom (filtered by T013)
    Logic: Sum counts per sample (row-wise, axis=1), filter non-zero, take median.
    Output: data/interior/median_depth.json
    """
    logger.info(f"Calculating sequencing depth for {input_path}")
    
    # Load BIOM table
    table = biom.load_table(input_path)
    
    # Get observation matrix (samples x taxa)
    # In biom format, observations are usually rows (taxa), samples are columns.
    # However, the task description says "sum of counts per sample (row-wise, axis=1)".
    # We need to be careful with orientation. biom.Table is typically (observation, sample).
    # Let's assume standard: rows=taxa, cols=samples.
    # So we sum along axis=0 (across taxa) to get depth per sample.
    
    # Convert to dense array for calculation (assuming manageable size for this step)
    # If too large, we would need to iterate.
    dense = table.matrix_data.toarray()
    
    # Sum across taxa (axis=0) to get depth per sample
    sample_depths = np.sum(dense, axis=0)
    
    # Filter non-zero depths
    non_zero_depths = sample_depths[sample_depths > 0]
    
    if len(non_zero_depths) == 0:
        raise ValueError("No samples with non-zero sequencing depth found.")
        
    median_depth = float(np.median(non_zero_depths))
    
    logger.info(f"Median sequencing depth calculated: {median_depth}")
    
    return {"median_depth": median_depth}

def estimate_rarefaction_loss(input_path: str, median_depth: float) -> Dict[str, float]:
    """
    Step 2: Estimate sample loss if rarefying to median depth.
    Input: data/interior/median_depth.json (from T014a)
    Algorithm: Simulate rarefaction to median depth, count samples with zero depth.
    Output: data/interior/estimated_loss.json
    """
    logger.info(f"Estimating rarefaction loss for {input_path} at depth {median_depth}")
    
    table = biom.load_table(input_path)
    dense = table.matrix_data.toarray()
    
    # Count samples with total depth < median_depth
    # If we rarefy to median_depth, any sample with total depth < median_depth will be lost (zero depth after rarefaction)
    sample_depths = np.sum(dense, axis=0)
    
    total_samples = len(sample_depths)
    lost_samples = np.sum(sample_depths < median_depth)
    loss_rate = float(lost_samples / total_samples) if total_samples > 0 else 0.0
    
    logger.info(f"Estimated rarefaction loss: {loss_rate * 100:.2f}%")
    
    return {
        "median_depth": median_depth,
        "total_samples": int(total_samples),
        "lost_samples": int(lost_samples),
        "loss_rate": loss_rate
    }

def apply_rarefaction(input_path: str, output_path: str, depth: int) -> None:
    """
    Apply rarefaction to the OTU table.
    """
    logger.info(f"Applying rarefaction to depth {depth}")
    table = biom.load_table(input_path)
    
    # Use biom's rarefaction method
    # Note: biom.rarefy requires a random seed for reproducibility
    rarefied_table = table.rarefy(depth=depth, seed=42)
    
    # Save
    with open(output_path, 'w') as f:
        biom.write_table(rarefied_table, f)
    
    logger.info(f"Rarefied table saved to {output_path}")

def apply_vst(input_path: str, output_path: str) -> None:
    """
    Apply Variance-Stabilizing Transformation (VST) using sklearn's PowerTransformer.
    This is a fallback when rarefaction loss > 20%.
    """
    logger.info("Applying Variance-Stabilizing Transformation (VST)")
    
    table = biom.load_table(input_path)
    dense = table.matrix_data.toarray()
    
    # PowerTransformer with Yeo-Johnson can handle zeros and negative values
    # However, microbiome data is non-negative. Box-Cox requires strictly positive.
    # We'll use Yeo-Johnson which is more robust.
    # Add a small constant to avoid log(0) issues if using Box-Cox, but Yeo-Johnson handles 0.
    
    pt = PowerTransformer(method='yeo-johnson', standardize=True)
    
    # Apply VST
    # We transform across samples (axis=0) for each taxon (row)
    # Or across taxa? Usually we want to stabilize variance across samples for each feature.
    # Let's transform each row (taxon) across samples.
    transformed = pt.fit_transform(dense.T).T  # Transpose to transform rows, then transpose back
    
    # Create new BIOM table
    new_table = biom.Table(transformed, observation_ids=table.observation_ids, sample_ids=table.sample_ids)
    
    with open(output_path, 'w') as f:
        biom.write_table(new_table, f)
    
    logger.info(f"VST applied and saved to {output_path}")

def filter_low_prevalence(input_path: str, output_path: str, prevalence_threshold: float = 0.001) -> None:
    """
    Filter taxa with < 0.1% prevalence.
    """
    logger.info(f"Filtering taxa with prevalence < {prevalence_threshold * 100}%")
    table = biom.load_table(input_path)
    dense = table.matrix_data.toarray()
    
    # Calculate prevalence (fraction of samples with non-zero count)
    prevalence = np.sum(dense > 0, axis=1) / dense.shape[1]
    
    # Keep taxa with prevalence >= threshold
    keep_mask = prevalence >= prevalence_threshold
    
    if not np.any(keep_mask):
        logger.warning("No taxa meet the prevalence threshold. Keeping all.")
        keep_mask = np.ones(dense.shape[0], dtype=bool)
    
    # Filter table
    filtered_obs_ids = table.observation_ids[keep_mask]
    filtered_dense = dense[keep_mask, :]
    
    new_table = biom.Table(filtered_dense, observation_ids=filtered_obs_ids, sample_ids=table.sample_ids)
    
    with open(output_path, 'w') as f:
        biom.write_table(new_table, f)
    
    logger.info(f"Filtered table saved to {output_path}")

def calculate_alpha_diversity(input_path: str, output_path: str) -> None:
    """
    Calculate Alpha diversity metrics (Shannon, Simpson).
    """
    logger.info("Calculating alpha diversity metrics")
    table = biom.load_table(input_path)
    dense = table.matrix_data.toarray()
    
    # Shannon entropy
    shannon = -np.sum(dense * np.log(dense + 1e-10), axis=1)  # +1e-10 to avoid log(0)
    # Simpson index (1 - sum(p^2))
    simpson = 1 - np.sum((dense / np.sum(dense, axis=1, keepdims=True))**2, axis=1)
    
    # Create DataFrame
    df = pd.DataFrame({
        'sample_id': table.sample_ids,
        'shannon': shannon,
        'simpson': simpson
    })
    
    df.to_csv(output_path, index=False)
    logger.info(f"Alpha diversity metrics saved to {output_path}")

def generate_beta_diversity_matrices(input_path: str, output_dir: str, tree_path: Optional[str] = None) -> Dict[str, str]:
    """
    Generate beta diversity metrics: Bray-Curtis, Weighted/Unweighted UniFrac (if tree available).
    """
    logger.info("Generating beta diversity matrices")
    from skbio.diversity import beta_diversity
    from skbio.stats.distance import DistanceMatrix
    import scipy.spatial.distance as spdist
    
    table = biom.load_table(input_path)
    dense = table.matrix_data.toarray()
    
    # Bray-Curtis
    bray_curtis = beta_diversity('braycurtis', dense, ids=table.sample_ids)
    bray_curtis_path = os.path.join(output_dir, "bray_curtis.npz")
    np.savez(bray_curtis_path, data=bray_curtis.data, ids=bray_curtis.ids)
    logger.info(f"Bray-Curtis saved to {bray_curtis_path}")
    
    results = {"bray_curtis": bray_curtis_path}
    
    # UniFrac (if tree available)
    if tree_path and os.path.exists(tree_path):
        from skbio import TreeNode
        from skbio.diversity import beta_diversity as skbio_beta_diversity
        
        tree = TreeNode.read(tree_path)
        
        # Weighted UniFrac
        try:
            weighted_unifrac = skbio_beta_diversity('weighted_unifrac', dense, table.sample_ids, tree)
            weighted_path = os.path.join(output_dir, "weighted_unifrac.npz")
            np.savez(weighted_path, data=weighted_unifrac.data, ids=weighted_unifrac.ids)
            results["weighted_unifrac"] = weighted_path
            logger.info(f"Weighted UniFrac saved to {weighted_path}")
        except Exception as e:
            logger.warning(f"Weighted UniFrac failed: {e}")
            # Create empty file with flag
            empty_path = os.path.join(output_dir, "weighted_unifrac.npz")
            np.savez(empty_path, data=np.array([]), ids=np.array([]), skipped=True)
            results["weighted_unifrac"] = empty_path
        
        # Unweighted UniFrac
        try:
            unweighted_unifrac = skbio_beta_diversity('unweighted_unifrac', dense, table.sample_ids, tree)
            unweighted_path = os.path.join(output_dir, "unweighted_unifrac.npz")
            np.savez(unweighted_path, data=unweighted_unifrac.data, ids=unweighted_unifrac.ids)
            results["unweighted_unifrac"] = unweighted_path
            logger.info(f"Unweighted UniFrac saved to {unweighted_path}")
        except Exception as e:
            logger.warning(f"Unweighted UniFrac failed: {e}")
            empty_path = os.path.join(output_dir, "unweighted_unifrac.npz")
            np.savez(empty_path, data=np.array([]), ids=np.array([]), skipped=True)
            results["unweighted_unifrac"] = empty_path
    else:
        logger.warning("No tree available, skipping UniFrac.")
        # Create empty files with skipped flag
        empty_path = os.path.join(output_dir, "weighted_unifrac.npz")
        np.savez(empty_path, data=np.array([]), ids=np.array([]), skipped=True)
        results["weighted_unifrac"] = empty_path
        
        empty_path = os.path.join(output_dir, "unweighted_unifrac.npz")
        np.savez(empty_path, data=np.array([]), ids=np.array([]), skipped=True)
        results["unweighted_unifrac"] = empty_path
    
    return results

def run_preprocessing(
    input_path: str,
    output_path: str,
    median_depth_path: str,
    loss_path: str,
    loss_threshold: float = 0.2
) -> None:
    """
    Step 3: Main preprocessing logic.
    If estimated loss > 20%, apply VST; otherwise, apply rarefaction.
    """
    logger.info("Running preprocessing step 3")
    
    # Load median depth
    with open(median_depth_path, 'r') as f:
        median_depth_data = json.load(f)
    median_depth = median_depth_data['median_depth']
    
    # Load estimated loss
    with open(loss_path, 'r') as f:
        loss_data = json.load(f)
    loss_rate = loss_data['loss_rate']
    
    logger.info(f"Median depth: {median_depth}, Estimated loss: {loss_rate * 100:.2f}%")
    
    # Ensure output directory exists
    ensure_directories([Path(output_path).parent])
    
    if loss_rate > loss_threshold:
        logger.warning(f"Estimated loss ({loss_rate * 100:.2f}%) exceeds threshold ({loss_threshold * 100}%). Applying VST.")
        apply_vst(input_path, output_path)
    else:
        logger.info(f"Estimated loss ({loss_rate * 100:.2f}%) within threshold. Applying rarefaction.")
        apply_rarefaction(input_path, output_path, int(median_depth))
    
    logger.info(f"Preprocessed OTU table saved to {output_path}")

def main():
    """
    Main entry point for preprocessing script.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess OTU table")
    parser.add_argument("--input", required=True, help="Input OTU table path")
    parser.add_argument("--output", required=True, help="Output OTU table path")
    parser.add_argument("--median-depth", required=True, help="Path to median depth JSON")
    parser.add_argument("--loss", required=True, help="Path to estimated loss JSON")
    parser.add_argument("--loss-threshold", type=float, default=0.2, help="Loss threshold (default: 0.2)")
    
    args = parser.parse_args()
    
    # Setup logging
    logger.setLevel(logging.INFO)
    
    run_preprocessing(
        input_path=args.input,
        output_path=args.output,
        median_depth_path=args.median_depth,
        loss_path=args.loss,
        loss_threshold=args.loss_threshold
    )

if __name__ == "__main__":
    main()
