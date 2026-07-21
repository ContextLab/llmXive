import numpy as np
import pandas as pd
from typing import Union, Dict, Any, Optional
import logging
from pathlib import Path
from src.config import load_config

logger = logging.getLogger(__name__)

def rarefy_table(counts: Union[pd.DataFrame, np.ndarray], depth: int) -> pd.DataFrame:
    """
    Subsample OTU table to a fixed sequencing depth (rarefaction).
    
    Args:
        counts: OTU table (samples as rows, OTUs as columns)
        depth: Target sequencing depth (rarefaction depth)
        
    Returns:
        Rarefied OTU table (DataFrame) with same shape, counts subsampled
        
    Raises:
        ValueError: If depth is invalid or all samples have fewer reads than depth
    """
    if depth <= 0:
        raise ValueError(f"Rarefaction depth must be positive, got {depth}")
        
    if isinstance(counts, np.ndarray):
        counts = pd.DataFrame(counts)
        
    # Ensure we have integer counts
    counts = counts.astype(int)
    
    # Calculate total reads per sample
    sample_totals = counts.sum(axis=1)
    
    # Filter out samples with insufficient reads
    valid_samples = sample_totals >= depth
    if not valid_samples.any():
        raise ValueError(
            f"No samples have >= {depth} reads. "
            f"Min reads: {sample_totals.min()}, Max reads: {sample_totals.max()}"
        )
        
    valid_counts = counts[valid_samples].copy()
    
    rarefied_data = []
    
    for sample_idx in valid_counts.index:
        sample_row = valid_counts.loc[sample_idx]
        total_reads = sample_row.sum()
        
        if total_reads < depth:
            continue
            
        # Subsample: for each OTU, sample from multinomial distribution
        # Probability = OTU count / total reads for this sample
        probs = sample_row / total_reads
        rarefied_counts = np.random.multinomial(depth, probs.to_numpy())
        rarefied_data.append(rarefied_counts)
        
    rarefied_df = pd.DataFrame(
        rarefied_data,
        index=valid_counts.index[valid_counts.index.isin(valid_counts.index)],
        columns=valid_counts.columns
    )
    
    logger.info(f"Rarefaction complete: {len(rarefied_df)} samples at depth {depth}")
    return rarefied_df

def calculate_alpha_diversity(
    otu_table: pd.DataFrame,
    rarefaction_depth: Optional[int] = None
) -> pd.DataFrame:
    """
    Calculate alpha diversity indices (Shannon, Simpson, Observed OTUs).
    
    Args:
        otu_table: OTU table (samples as rows, OTUs as columns)
        rarefaction_depth: If provided, rarefy table to this depth first
        
    Returns:
        DataFrame with alpha diversity metrics per sample:
            - shannon: Shannon diversity index
            - simpson: Simpson diversity index (1-D)
            - observed_otus: Number of OTUs with count > 0
    """
    config = load_config()
    random_seed = config.get('RANDOM_SEED', 42)
    np.random.seed(random_seed)
    
    # Rarefy if depth specified
    if rarefaction_depth is not None:
        otu_table = rarefy_table(otu_table, rarefaction_depth)
        
    if otu_table.empty:
        logger.warning("Empty OTU table after rarefaction, returning empty diversity DataFrame")
        return pd.DataFrame(columns=['shannon', 'simpson', 'observed_otus'])
        
    # Calculate Shannon diversity: -sum(p * ln(p))
    # where p = proportion of each OTU in the sample
    def calc_shannon(row):
        total = row.sum()
        if total == 0:
            return 0.0
        probs = row[row > 0] / total
        return -np.sum(probs * np.log(probs))
        
    # Calculate Simpson diversity: 1 - sum(p^2)
    # Using 1-D to express diversity (higher = more diverse)
    def calc_simpson(row):
        total = row.sum()
        if total == 0:
            return 0.0
        probs = row / total
        return 1 - np.sum(probs ** 2)
        
    # Observed OTUs: count of OTUs with abundance > 0
    def calc_observed_otus(row):
        return (row > 0).sum()
        
    diversity_df = pd.DataFrame(index=otu_table.index)
    diversity_df['shannon'] = otu_table.apply(calc_shannon, axis=1)
    diversity_df['simpson'] = otu_table.apply(calc_simpson, axis=1)
    diversity_df['observed_otus'] = otu_table.apply(calc_observed_otus, axis=1)
    
    logger.info(
        f"Alpha diversity calculated: "
        f"Shannon range [{diversity_df['shannon'].min():.3f}, {diversity_df['shannon'].max():.3f}], "
        f"Simpson range [{diversity_df['simpson'].min():.3f}, {diversity_df['simpson'].max():.3f}], "
        f"Observed OTUs range [{diversity_df['observed_otus'].min()}, {diversity_df['observed_otus'].max()}]"
    )
    
    return diversity_df

def main():
    """
    Main entry point for alpha-diversity computation.
    
    Reads cleaned data from data/processed/cleaned_microbiome_sleep.csv,
    extracts OTU table and metadata, performs rarefaction, calculates
    alpha diversity, and saves results.
    """
    config = load_config()
    random_seed = config.get('RANDOM_SEED', 42)
    rarefaction_depth = config.get('RAREFACTION_DEPTH', 10000)  # Default depth
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Load cleaned data
    input_path = Path('data/processed/cleaned_microbiome_sleep.csv')
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Run T016 first to generate cleaned data.")
        sys.exit(1)
        
    logger.info(f"Loading cleaned data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Identify OTU columns (typically prefixed with 'otu_' or similar)
    # Assuming OTU columns are all numeric columns that are not metadata
    # Common pattern: columns starting with 'otu_' or containing OTU IDs
    otu_columns = [col for col in df.columns if col.startswith('otu_') or col.startswith('OTU_')]
    
    if not otu_columns:
        # Fallback: assume all numeric columns except known metadata are OTUs
        metadata_cols = ['sample_id', 'antibiotic_use_last_3m', 'sleep_efficiency', 
                       'sleep_duration_hours', 'sleep_quality_score']
        otu_columns = [col for col in df.columns if df[col].dtype in ['int64', 'float64'] 
                     and col not in metadata_cols]
    
    logger.info(f"Identified {len(otu_columns)} OTU columns")
    
    if len(otu_columns) == 0:
        logger.error("No OTU columns found in the dataset.")
        sys.exit(1)
        
    # Extract OTU table and metadata
    otu_table = df[otu_columns].copy()
    metadata = df[['sample_id']].copy() if 'sample_id' in df.columns else pd.DataFrame(index=otu_table.index)
    
    # Add sleep metrics if present
    sleep_cols = ['sleep_efficiency', 'sleep_duration_hours']
    for col in sleep_cols:
        if col in df.columns:
            metadata[col] = df[col]
            
    # Rarefy and calculate diversity
    logger.info(f"Rarefying to depth {rarefaction_depth}")
    try:
        rarefied_table = rarefy_table(otu_table, rarefaction_depth)
    except ValueError as e:
        logger.error(f"Rarefaction failed: {e}")
        sys.exit(1)
        
    # Calculate alpha diversity
    diversity_metrics = calculate_alpha_diversity(rarefied_table, rarefaction_depth=None)  # Already rarefied
    
    # Merge with metadata
    if 'sample_id' in metadata.columns:
        diversity_metrics['sample_id'] = metadata['sample_id']
        
    for col in sleep_cols:
        if col in metadata.columns:
            diversity_metrics[col] = metadata[col]
            
    # Save results
    output_path = Path('data/processed/alpha_diversity_metrics.csv')
    diversity_metrics.to_csv(output_path, index=False)
    logger.info(f"Alpha diversity metrics saved to {output_path}")
    
    # Print summary
    print("\n=== Alpha Diversity Summary ===")
    print(f"Samples processed: {len(diversity_metrics)}")
    print(f"Rarefaction depth: {rarefaction_depth}")
    print(f"Shannon: mean={diversity_metrics['shannon'].mean():.3f}, std={diversity_metrics['shannon'].std():.3f}")
    print(f"Simpson: mean={diversity_metrics['simpson'].mean():.3f}, std={diversity_metrics['simpson'].std():.3f}")
    print(f"Observed OTUs: mean={diversity_metrics['observed_otus'].mean():.1f}, std={diversity_metrics['observed_otus'].std():.1f}")
    
    return diversity_metrics

if __name__ == '__main__':
    import sys
    main()