import numpy as np
import pandas as pd
from typing import Union, Dict, Any, Optional
import logging
from pathlib import Path

from src.config import load_config

logger = logging.getLogger(__name__)

def rarefy_table(otu_table: pd.DataFrame, depth: int, random_state: Optional[int] = None) -> pd.DataFrame:
    """
    Rarefy an OTU table to a specified sequencing depth.
    
    This normalizes sequencing depth by subsampling reads without replacement.
    Samples with fewer reads than the target depth are excluded.
    
    Args:
        otu_table: DataFrame with samples as rows and OTUs as columns.
        depth: Target sequencing depth (number of reads to subsample to).
        random_state: Random seed for reproducibility.
        
    Returns:
        Rarefied DataFrame with the same OTU columns but potentially fewer rows.
        
    Raises:
        ValueError: If depth is negative or if all samples are excluded.
    """
    if depth < 0:
        raise ValueError("Rarefaction depth must be non-negative.")
        
    if random_state is not None:
        np.random.seed(random_state)
        
    # Calculate total reads per sample
    sample_sums = otu_table.sum(axis=1)
    
    # Identify samples that meet the depth threshold
    valid_samples = sample_sums >= depth
    
    if not valid_samples.any():
        raise ValueError(f"All samples have fewer reads than the target depth ({depth}).")
        
    valid_otu_table = otu_table[valid_samples].copy()
    
    # Perform rarefaction
    rarefied_data = []
    for idx, row in valid_otu_table.iterrows():
        total_reads = int(row.sum())
        counts = row.values.astype(int)
        
        # Create a list of OTU indices repeated by their counts
        # This is memory intensive for large tables, so we use a generator approach
        # for the rarefaction process
        otu_indices = np.repeat(np.arange(len(counts)), counts)
        
        # Subsample without replacement
        if len(otu_indices) > depth:
            sampled_indices = np.random.choice(otu_indices, size=depth, replace=False)
        else:
            sampled_indices = otu_indices
        
        # Count occurrences of each OTU in the sample
        rarefied_counts = np.bincount(sampled_indices, minlength=len(counts))
        rarefied_data.append(rarefied_counts)
        
    rarefied_df = pd.DataFrame(
        rarefied_data,
        index=valid_otu_table.index,
        columns=valid_otu_table.columns
    )
    
    logger.info(f"Rarefied {len(rarefied_df)} samples to depth {depth}. "
               f"Excluded {len(valid_otu_table) - len(rarefied_df)} samples with low depth.")
    
    return rarefied_df

def calculate_alpha_diversity(otu_table: pd.DataFrame, 
                              sleep_data: pd.DataFrame,
                              depth: Optional[int] = None,
                              random_state: Optional[int] = None) -> pd.DataFrame:
    """
    Calculate alpha diversity indices (Shannon, Simpson, Observed OTUs) for samples.
    
    Includes an optional rarefaction step to normalize sequencing depth.
    
    Args:
        otu_table: DataFrame with samples as rows and OTUs as columns.
        sleep_data: DataFrame containing sleep metrics and sample IDs.
        depth: Target sequencing depth for rarefaction. If None, no rarefaction is performed.
        random_state: Random seed for reproducibility.
        
    Returns:
        DataFrame with sample IDs and alpha diversity metrics (Shannon, Simpson, Observed OTUs)
        merged with sleep metrics.
        
    Raises:
        FileNotFoundError: If the input data file is missing.
        ValueError: If required columns are missing from the input data.
    """
    config = load_config()
    input_path = Path(config.get('INPUT_FILE', 'data/processed/cleaned_microbiome_sleep.csv'))
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                              "Ensure T016 has completed successfully.")
    
    # Load the cleaned data
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_otu_cols = ['sample_id'] + [col for col in df.columns if col.startswith('OTU_')]
    required_sleep_cols = ['sample_id', 'sleep_efficiency', 'sleep_duration_hours']
    
    otu_cols = [col for col in df.columns if col.startswith('OTU_') or col == 'sample_id']
    sleep_cols = [col for col in required_sleep_cols if col in df.columns]
    
    if not otu_cols:
        raise ValueError("No OTU columns found in the input data.")
    if len(sleep_cols) < 3:
        raise ValueError(f"Missing required sleep columns. Found: {sleep_cols}")
        
    # Separate OTU table and metadata
    otu_table = df[otu_cols].set_index('sample_id')
    metadata = df[['sample_id'] + sleep_cols].set_index('sample_id')
    
    logger.info(f"OTU table shape: {otu_table.shape}")
    logger.info(f"Metadata shape: {metadata.shape}")
    
    # Optional rarefaction
    if depth is not None:
        logger.info(f"Performing rarefaction to depth {depth}")
        otu_table = rarefy_table(otu_table, depth, random_state)
        # Update metadata to match rarefied samples
        metadata = metadata.loc[otu_table.index]
    
    # Calculate alpha diversity metrics
    # Observed OTUs: number of OTUs with at least one read
    observed_otus = (otu_table > 0).sum(axis=1)
    
    # Shannon index: -sum(p * ln(p)) where p is the proportion of each OTU
    def shannon_index(row):
        total = row.sum()
        if total == 0:
            return 0.0
        proportions = row / total
        # Avoid log(0) by filtering out zero proportions
        proportions = proportions[proportions > 0]
        return -np.sum(proportions * np.log(proportions))
    
    shannon = otu_table.apply(shannon_index, axis=1)
    
    # Simpson index: 1 - sum(p^2)
    def simpson_index(row):
        total = row.sum()
        if total == 0:
            return 0.0
        proportions = row / total
        return 1 - np.sum(proportions ** 2)
    
    simpson = otu_table.apply(simpson_index, axis=1)
    
    # Create results DataFrame
    diversity_df = pd.DataFrame({
        'sample_id': shannon.index,
        'shannon': shannon.values,
        'simpson': simpson.values,
        'observed_otus': observed_otus.values
    })
    
    # Merge with sleep data
    results = diversity_df.merge(metadata.reset_index(), on='sample_id')
    
    logger.info(f"Calculated alpha diversity for {len(results)} samples")
    logger.info(f"Shannon range: [{results['shannon'].min():.3f}, {results['shannon'].max():.3f}]")
    logger.info(f"Simpson range: [{results['simpson'].min():.3f}, {results['simpson'].max():.3f}]")
    
    return results

def main():
    """
    Main entry point for alpha diversity computation.
    
    This function:
    1. Loads configuration
    2. Reads the cleaned microbiome and sleep data
    3. Performs rarefaction (if configured)
    4. Calculates alpha diversity indices
    5. Saves results to data/processed/diversity_metrics.csv
    """
    config = load_config()
    
    # Configuration
    rarefaction_depth = config.get('RAREFACTION_DEPTH')
    if rarefaction_depth:
        rarefaction_depth = int(rarefaction_depth)
        
    random_seed = config.get('RANDOM_SEED')
    if random_seed:
        random_seed = int(random_seed)
        
    output_path = Path(config.get('OUTPUT_FILE', 'data/processed/diversity_metrics.csv'))
    
    logger.info("Starting alpha diversity computation")
    logger.info(f"Rarefaction depth: {rarefaction_depth}")
    logger.info(f"Random seed: {random_seed}")
    
    try:
        results = calculate_alpha_diversity(
            otu_table=None,  # Passed internally in the function
            sleep_data=None,  # Passed internally in the function
            depth=rarefaction_depth,
            random_state=random_seed
        )
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(output_path, index=False)
        
        logger.info(f"Alpha diversity metrics saved to {output_path}")
        logger.info(f"Output shape: {results.shape}")
        logger.info(f"Columns: {list(results.columns)}")
        
    except FileNotFoundError as e:
        logger.error(f"Input data not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during alpha diversity computation: {e}")
        raise

if __name__ == "__main__":
    main()