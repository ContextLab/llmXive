import numpy as np
import pandas as pd
from typing import Union, Dict, Any, Optional
import logging
from pathlib import Path
from src.config import load_config

logger = logging.getLogger(__name__)

def rarefy_table(counts: Union[pd.DataFrame, np.ndarray], depth: int) -> pd.DataFrame:
    """
    Subsample OTU tables to a fixed sequencing depth (rarefaction).

    This function performs multinomial subsampling without replacement to
    normalize sequencing depth across samples. It ensures that every sample
    in the output has exactly 'depth' total reads, provided the original
    sample had at least 'depth' reads. Samples with fewer reads than 'depth'
    are excluded from the result.

    Parameters
    ----------
    counts : pd.DataFrame or np.ndarray
        OTU table where rows are samples and columns are OTUs/ASVs.
        If DataFrame, index is sample IDs and columns are feature IDs.
    depth : int
        Target sequencing depth for subsampling. Must be positive.

    Returns
    -------
    pd.DataFrame
        Rarefied OTU table with samples normalized to 'depth' reads.
        Samples with total reads < depth are dropped.

    Raises
    ------
    ValueError
        If depth is not positive or if input is empty.
    """
    if depth <= 0:
        raise ValueError(f"Rarefaction depth must be positive, got {depth}")

    # Convert to DataFrame if numpy array
    if isinstance(counts, np.ndarray):
        df = pd.DataFrame(counts)
    elif isinstance(counts, pd.DataFrame):
        df = counts.copy()
    else:
        raise TypeError(f"counts must be DataFrame or ndarray, got {type(counts)}")

    if df.empty:
        raise ValueError("Input OTU table is empty")

    # Calculate total reads per sample
    sample_totals = df.sum(axis=1)

    # Identify samples that have enough reads
    valid_samples = sample_totals >= depth
    if not valid_samples.any():
        raise ValueError(f"No samples have >= {depth} reads for rarefaction")

    # Filter to valid samples only
    rarefied_df = df[valid_samples].copy()
    logger.info(f"Rarefying {rarefied_df.shape[0]} samples to depth {depth} "
                f"(excluded {(~valid_samples).sum()} samples with insufficient depth)")

    # Perform rarefaction for each sample
    rarefied_counts = []
    for idx, row in rarefied_df.iterrows():
        # Get counts for this sample
        sample_counts = row.values.astype(int)
        
        # Skip if somehow the sum is still less than depth (shouldn't happen)
        if sample_counts.sum() < depth:
            continue

        # Use numpy's choice with replacement=false is not available for weighted,
        # so we use multinomial approximation or iterative sampling.
        # For efficiency with large tables, we use np.random.multinomial.
        # However, multinomial samples WITH replacement in the limit.
        # For true rarefaction (without replacement), we need to sample indices.
        
        # Efficient approach: expand counts to indices, sample, then recount
        # This is memory intensive for very large counts, but standard for rarefaction.
        # Alternative: use scipy.stats.rv_discrete or similar, but numpy is sufficient.
        
        # Method: Generate indices based on cumulative counts
        # To avoid memory explosion for huge counts, we use a loop or efficient sampling.
        # Given typical microbiome data (10k-100k reads), we can do this.
        
        # Optimized approach using numpy's choice on expanded indices
        # But expanding 100k reads is fine.
        # Let's use a more memory-efficient method: sample directly from the distribution
        # using the fact that we are sampling 'depth' items from a multinomial distribution
        # is mathematically equivalent to rarefaction without replacement if we treat
        # the counts as a population.
        
        # Actually, the standard definition of rarefaction is sampling WITHOUT replacement.
        # The multinomial distribution is sampling WITH replacement.
        # We must sample WITHOUT replacement.
        
        # Approach: Create an array of feature IDs repeated by their counts,
        # sample 'depth' items without replacement, then count frequencies.
        
        # To handle large counts efficiently without exploding memory:
        # We can use numpy's choice on a range of indices if we map them,
        # but the simplest robust way for this scale is:
        # 1. Create a list of (feature_idx, count)
        # 2. If total reads is manageable, expand and sample.
        # 3. If too large, use a reservoir sampling or similar, but standard rarefaction
        #    usually implies the expand-and-sample method for exactness.
        
        # Given the constraints (7GB RAM), and typical OTU tables, we assume the expansion
        # is feasible. If not, we would need a specialized library, but we stick to numpy/pandas.
        
        # Construct the expanded array of feature indices
        # This creates an array of length 'sample_counts.sum()'
        # If sum is 100,000, this is ~400KB-800KB, which is fine.
        expanded_indices = np.repeat(np.arange(len(sample_counts)), sample_counts)
        
        # Sample 'depth' indices without replacement
        if depth > len(expanded_indices):
            # This should be caught by the check above, but safety net
            raise ValueError(f"Sample {idx} has fewer reads ({len(expanded_indices)}) than requested depth ({depth})")
        
        sampled_indices = np.random.choice(expanded_indices, size=depth, replace=False)
        
        # Count the occurrences of each feature in the sample
        rarefied_row = np.bincount(sampled_indices, minlength=len(sample_counts))
        rarefied_counts.append(rarefied_row)

    # Convert back to DataFrame
    result = pd.DataFrame(rarefied_counts, index=rarefied_df.index, columns=rarefied_df.columns)
    
    # Ensure all values are integers
    result = result.astype(int)
    
    logger.info(f"Rarefaction complete. Output shape: {result.shape}")
    return result

def calculate_alpha_diversity(rarefied_table: pd.DataFrame, 
                              metrics: Optional[list] = None) -> pd.DataFrame:
    """
    Calculate alpha diversity metrics from a rarefied OTU table.

    Parameters
    ----------
    rarefied_table : pd.DataFrame
        Rarefied OTU table (samples x OTUs).
    metrics : list, optional
        List of metrics to calculate. Default: ['shannon', 'simpson', 'observed_otus'].

    Returns
    -------
    pd.DataFrame
        DataFrame with alpha diversity metrics as columns and samples as index.
    """
    if rarefied_table.empty:
        return pd.DataFrame()

    if metrics is None:
        metrics = ['shannon', 'simpson', 'observed_otus']

    results = {}
    total_reads = rarefied_table.sum(axis=1)

    for metric in metrics:
        if metric == 'observed_otus':
            # Count non-zero OTUs per sample
            results['observed_otus'] = (rarefied_table > 0).sum(axis=1)
        elif metric == 'shannon':
            # Shannon index: -sum(p * ln(p))
            # p = count / total_reads
            shannon_vals = []
            for _, row in rarefied_table.iterrows():
                total = row.sum()
                if total == 0:
                    shannon_vals.append(0.0)
                    continue
                p = row[row > 0] / total
                shannon = -np.sum(p * np.log(p))
                shannon_vals.append(shannon)
            results['shannon'] = pd.Series(shannon_vals, index=rarefied_table.index)
        elif metric == 'simpson':
            # Simpson index: 1 - sum(p^2)
            simpson_vals = []
            for _, row in rarefied_table.iterrows():
                total = row.sum()
                if total == 0:
                    simpson_vals.append(0.0)
                    continue
                p = row / total
                simpson = 1 - np.sum(p ** 2)
                simpson_vals.append(simpson)
            results['simpson'] = pd.Series(simpson_vals, index=rarefied_table.index)
        else:
            logger.warning(f"Unknown metric '{metric}' skipped")

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results, index=rarefied_table.index)

def main():
    """
    Main entry point for running the diversity analysis pipeline.
    Loads cleaned data, performs rarefaction, calculates alpha diversity,
    and saves results.
    """
    config = load_config()
    logger.info("Starting diversity analysis pipeline")

    input_path = Path(config['DATA_DIR']) / 'processed' / 'cleaned_microbiome_sleep.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)

    # Identify OTU columns (assume they start with 'OTU_' or are numeric columns not in metadata)
    # For this implementation, we assume the first N columns are OTUs and the rest are metadata.
    # A more robust check would look for specific column patterns.
    # Let's assume columns containing 'OTU' or 'ASV' are features, or simply numeric columns
    # that are not the sample ID or known metadata.
    
    # Heuristic: Columns that are numeric and not 'sample_id', 'sleep_efficiency', etc.
    metadata_cols = ['sample_id', 'sleep_efficiency', 'sleep_duration_hours', 
                     'antibiotic_use_last_3m', 'age', 'sex']
    otu_cols = [col for col in df.columns if col not in metadata_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not otu_cols:
        raise ValueError("No OTU columns found in the dataset. Please check column names.")

    logger.info(f"Found {len(otu_cols)} OTU columns")

    # Extract OTU table
    otu_table = df.set_index('sample_id')[otu_cols]
    sample_ids = otu_table.index

    # Determine rarefaction depth (e.g., minimum sequencing depth or a fixed value)
    # Using 10,000 as a common default, or min depth if lower
    min_depth = otu_table.sum(axis=1).min()
    rarefaction_depth = min(10000, min_depth)
    
    if rarefaction_depth <= 0:
        raise ValueError("Invalid sequencing depth detected")

    logger.info(f"Performing rarefaction to depth {rarefaction_depth}")
    rarefied_table = rarefy_table(otu_table, rarefaction_depth)

    logger.info("Calculating alpha diversity metrics")
    alpha_diversity = calculate_alpha_diversity(rarefied_table)

    # Merge with metadata for downstream analysis
    # We only keep samples that survived rarefaction
    valid_samples = rarefied_table.index
    metadata = df[df['sample_id'].isin(valid_samples)].set_index('sample_id')
    
    final_df = pd.merge(alpha_diversity, metadata, left_index=True, right_index=True, how='inner')

    output_path = Path(config['DATA_DIR']) / 'processed' / 'alpha_diversity_results.csv'
    final_df.to_csv(output_path)
    logger.info(f"Alpha diversity results saved to {output_path}")

    return final_df

if __name__ == "__main__":
    main()
