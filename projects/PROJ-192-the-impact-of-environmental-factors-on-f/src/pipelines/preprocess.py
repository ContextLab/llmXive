import os
import pandas as pd
import numpy as np
import skbio
from skbio.diversity import alpha_diversity, beta_diversity
from skbio.stats.distance import permanova
import yaml
import logging

from src.utils.logging import get_logger, log_structured
from src.utils.checksums import calculate_sha256

logger = get_logger(__name__)

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'constants.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def calculate_diversity_metrics(asv_table_path: str, metadata_path: str, output_dir: str):
    """
    Implements beta-diversity (Bray-Curtis) and alpha-diversity (Shannon, Observed ASVs).
    Outputs:
      - data/diversity/alpha_diversity.csv
      - data/diversity/beta_diversity_bray_curtis.csv
      - data/diversity/beta_diversity_euclidean.csv
    """
    config = load_config()
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Loading ASV table from {asv_table_path}")
    if not os.path.exists(asv_table_path):
        raise FileNotFoundError(f"ASV table not found at {asv_table_path}. Ensure T013c has run.")
    
    # Load ASV table (samples as rows, ASVs as columns)
    # Expected format: First column 'sample-id', rest are counts
    asv_df = pd.read_csv(asv_table_path, sep='\t', index_col=0)
    
    # Ensure counts are numeric
    asv_df = asv_df.apply(pd.to_numeric, errors='coerce').fillna(0).astype(int)

    logger.info(f"Loading metadata from {metadata_path}")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata not found at {metadata_path}. Ensure T013d/T015/T016 have run.")
    
    metadata_df = pd.read_csv(metadata_path, index_col=0)

    # Align samples
    common_samples = asv_df.index.intersection(metadata_df.index)
    if len(common_samples) == 0:
        raise ValueError("No common samples between ASV table and metadata.")
    
    asv_aligned = asv_df.loc[common_samples]
    meta_aligned = metadata_df.loc[common_samples]

    logger.info(f"Calculating Alpha Diversity (Shannon, Observed ASVs) for {len(common_samples)} samples...")
    
    # Calculate Alpha Diversity
    # skbio alpha_diversity expects a 2D array or DataFrame of counts
    shannon = alpha_diversity('shannon', asv_aligned.values, ids=asv_aligned.index)
    observed = alpha_diversity('observed_otus', asv_aligned.values, ids=asv_aligned.index)
    
    alpha_df = pd.DataFrame({
        'sample_id': common_samples,
        'shannon': shannon,
        'observed_asvs': observed
    })
    alpha_df.set_index('sample_id', inplace=True)
    
    alpha_output_path = os.path.join(output_dir, 'alpha_diversity.csv')
    alpha_df.to_csv(alpha_output_path)
    logger.info(f"Alpha diversity saved to {alpha_output_path}")

    logger.info("Calculating Beta Diversity (Bray-Curtis)...")
    # Bray-Curtis
    bray_curtis = beta_diversity('braycurtis', asv_aligned.values, ids=asv_aligned.index)
    bray_df = bray_curtis.to_data_frame()
    bray_output_path = os.path.join(output_dir, 'beta_diversity_bray_curtis.csv')
    bray_df.to_csv(bray_output_path)
    logger.info(f"Bray-Curtis distance matrix saved to {bray_output_path}")

    logger.info("Calculating Beta Diversity (Euclidean)...")
    # Euclidean
    euclidean = beta_diversity('euclidean', asv_aligned.values, ids=asv_aligned.index)
    eucl_df = euclidean.to_data_frame()
    eucl_output_path = os.path.join(output_dir, 'beta_diversity_euclidean.csv')
    eucl_df.to_csv(eucl_output_path)
    logger.info(f"Euclidean distance matrix saved to {eucl_output_path}")

    log_structured("INFO", "Diversity calculation complete", {
        "samples_processed": len(common_samples),
        "alpha_output": alpha_output_path,
        "bray_output": bray_output_path,
        "euclidean_output": eucl_output_path
    })

    return alpha_df, bray_df, eucl_df

if __name__ == "__main__":
    # Default paths assuming standard project structure
    # These should ideally be passed via CLI or config, but hardcoded for this task execution
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    asv_path = os.path.join(base_dir, 'data', 'qc', 'asv_table.tsv')
    meta_path = os.path.join(base_dir, 'data', 'cleaned_metadata.csv')
    output_path = os.path.join(base_dir, 'data', 'diversity')
    
    # Ensure data directories exist for the runner to work if files were present
    # In a real run, T013c and T016 must have populated these files first.
    # If files are missing, this will raise FileNotFoundError as per constraints.
    
    if not os.path.exists(asv_path):
        logger.error(f"Required input missing: {asv_path}. Run T013c first.")
        # Create dummy directories to satisfy structure check if needed, but logic fails
        os.makedirs(os.path.dirname(asv_path), exist_ok=True)
        raise FileNotFoundError(f"Input ASV table {asv_path} not found. Prerequisites T013c not met.")
    
    if not os.path.exists(meta_path):
        logger.error(f"Required input missing: {meta_path}. Run T016 first.")
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)
        raise FileNotFoundError(f"Input metadata {meta_path} not found. Prerequisites T016 not met.")

    calculate_diversity_metrics(asv_path, meta_path, output_path)
