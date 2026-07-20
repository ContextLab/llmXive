import numpy as np
import pandas as pd
from typing import Union, Dict, Any, Optional
import logging
from pathlib import Path

from src.config import load_config

logger = logging.getLogger(__name__)

def rarefy_table(counts: pd.DataFrame, depth: int) -> pd.DataFrame:
    """
    Subsample OTU table rows to a fixed sequencing depth (rarefaction).
    
    Args:
        counts: DataFrame where rows are samples and columns are OTUs/features.
        depth: Target sequencing depth (integer).
    
    Returns:
        DataFrame with rarefied counts. Samples with total count < depth are excluded.
    """
    if depth <= 0:
        raise ValueError("Rarefaction depth must be positive.")
    
    # Filter out samples that don't meet the depth threshold
    sample_totals = counts.sum(axis=1)
    valid_samples = sample_totals >= depth
    
    if not valid_samples.any():
        logger.warning("No samples meet the rarefaction depth threshold.")
        return pd.DataFrame()
    
    valid_counts = counts[valid_samples].copy()
    rarefied = []
    
    for idx, row in valid_counts.iterrows():
        total = row.sum()
        if total < depth:
            continue
        
        # Perform multinomial subsampling
        # Normalize row to probabilities
        probs = row / total
        rarefied_row = np.random.multinomial(depth, probs)
        rarefied.append(rarefied_row)
    
    rarefied_df = pd.DataFrame(rarefied, index=valid_counts.index[valid_counts.index.isin(valid_counts.index)], columns=valid_counts.columns)
    # Ensure index is correctly mapped
    rarefied_df.index = valid_counts.index[valid_samples]
    
    return rarefied_df

def calculate_alpha_diversity(
    otu_table: pd.DataFrame,
    rarefaction_depth: Optional[int] = None,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Calculate alpha diversity indices (Shannon, Simpson, Observed OTUs) for a table.
    
    If rarefaction_depth is provided, the table is first rarefied to that depth.
    
    Args:
        otu_table: DataFrame of OTU counts (samples x features).
        rarefaction_depth: Optional depth to rarefy to before calculation.
        random_seed: Random seed for reproducibility during rarefaction.
    
    Returns:
        DataFrame with columns: ['sample_id', 'shannon', 'simpson', 'observed_otus']
    """
    np.random.seed(random_seed)
    
    if rarefaction_depth:
        logger.info(f"Rarefying table to depth {rarefaction_depth}...")
        otu_table = rarefy_table(otu_table, rarefaction_depth)
        if otu_table.empty:
            logger.error("Rarefaction resulted in an empty table. Cannot calculate diversity.")
            return pd.DataFrame()
    
    logger.info("Calculating alpha diversity indices...")
    
    results = []
    
    for sample_id, row in otu_table.iterrows():
        counts = row.values
        total_count = counts.sum()
        
        if total_count == 0:
            continue
        
        # Filter out zero counts for Shannon/Simpson calculation
        non_zero = counts[counts > 0]
        n_non_zero = len(non_zero)
        
        # Observed OTUs
        observed_otus = n_non_zero
        
        # Shannon Index: -sum(p * ln(p))
        # p = n_i / N
        if n_non_zero > 0:
            probs = non_zero / total_count
            shannon = -np.sum(probs * np.log(probs))
        else:
            shannon = 0.0
        
        # Simpson Index: 1 - sum(p^2)
        # Or D = sum(n_i * (n_i - 1)) / (N * (N - 1))
        # Using probability formulation: 1 - sum(p^2)
        if total_count > 1:
            simpson = 1.0 - np.sum((non_zero / total_count) ** 2)
        else:
            simpson = 0.0
        
        results.append({
            'sample_id': sample_id,
            'shannon': shannon,
            'simpson': simpson,
            'observed_otus': observed_otus
        })
    
    return pd.DataFrame(results)

def main():
    """
    Main entry point for T020b: Calculate alpha diversity from cleaned data.
    Requires: data/processed/cleaned_microbiome_sleep.csv
    Output: data/processed/alpha_diversity.csv
    """
    config = load_config()
    logger.setLevel(config.get('LOG_LEVEL', 'INFO'))
    
    input_path = Path(config.get('DATA_PATH', 'data/processed/cleaned_microbiome_sleep.csv'))
    output_path = Path('data/processed/alpha_diversity.csv')
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("T016 (cleaned data) must be completed before running T020b.")
        raise FileNotFoundError(f"Required input file missing: {input_path}")
    
    logger.info(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # Identify OTU columns (assumed to be numeric columns not in metadata)
    # Heuristic: Columns that are not sample_id, antibiotic_use, sleep metrics, etc.
    # Based on typical ingestion, OTU columns are numeric and not in the known metadata list
    metadata_cols = ['sample_id', 'antibiotic_use_last_3m', 'sleep_efficiency', 
                     'sleep_duration_hours', 'sleep_onset_latency', 'wake_after_sleep_onset']
    otu_cols = [col for col in df.columns if col not in metadata_cols and pd.api.types.is_numeric_dtype(df[col])]
    
    if not otu_cols:
        logger.error("No OTU columns found in the input data.")
        raise ValueError("No OTU columns found. Check the input data schema.")
    
    otu_table = df.set_index('sample_id')[otu_cols]
    
    # Rarefaction depth: Use the minimum non-zero sample count or a fixed value
    # For robustness, we can use a fixed depth if specified, or calculate min
    rarefaction_depth = config.get('RAREFACTION_DEPTH', None)
    if rarefaction_depth is None:
        # Calculate a safe depth (e.g., 10th percentile of non-zero sample totals)
        sample_totals = otu_table.sum(axis=1)
        sample_totals = sample_totals[sample_totals > 0]
        if len(sample_totals) == 0:
            logger.error("No samples with OTU counts found.")
            raise ValueError("No samples with OTU counts.")
        rarefaction_depth = int(np.percentile(sample_totals, 10))
        logger.info(f"Automatically selected rarefaction depth: {rarefaction_depth}")
    
    diversity_df = calculate_alpha_diversity(otu_table, rarefaction_depth=rarefaction_depth)
    
    if diversity_df.empty:
        logger.error("Alpha diversity calculation resulted in an empty dataframe.")
        raise RuntimeError("Alpha diversity calculation failed.")
    
    # Merge back with sample IDs if needed (already has sample_id column)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    diversity_df.to_csv(output_path, index=False)
    
    logger.info(f"Alpha diversity indices saved to {output_path}")
    logger.info(f"Calculated for {len(diversity_df)} samples at depth {rarefaction_depth}")

if __name__ == "__main__":
    main()