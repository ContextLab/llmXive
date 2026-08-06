import numpy as np
import pandas as pd
from typing import Union, Dict, Any, Optional
import logging
from pathlib import Path
from src.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rarefy_table(counts: Union[pd.DataFrame, np.ndarray], depth: int) -> pd.DataFrame:
    """
    Subsample OTU tables to a fixed sequencing depth (rarefaction).
    
    Args:
        counts: OTU table (samples as rows, OTUs as columns).
        depth: Sequencing depth to rarefy to.
        
    Returns:
        Rarefied OTU table with same shape, counts subsampled.
    """
    if isinstance(counts, np.ndarray):
        counts = pd.DataFrame(counts)
        
    if depth <= 0:
        raise ValueError("Rarefaction depth must be positive")
        
    result = pd.DataFrame(index=counts.index, columns=counts.columns, dtype=int)
    
    for idx in counts.index:
        row = counts.loc[idx]
        total_count = row.sum()
        
        if total_count < depth:
            logger.warning(f"Sample {idx} has total count {total_count} < rarefaction depth {depth}. Excluding.")
            result.loc[idx] = 0
        else:
            # Multinomial sampling to rarefy
            probs = row / total_count
            rarefied_counts = np.random.multinomial(depth, probs.values)
            result.loc[idx] = rarefied_counts
            
    return result

def calculate_alpha_diversity(otu_table: pd.DataFrame, 
                              rarefied_table: Optional[pd.DataFrame] = None,
                              depth: Optional[int] = None) -> pd.DataFrame:
    """
    Calculate alpha diversity metrics (Shannon, Simpson, Observed OTUs).
    
    If rarefied_table is not provided, rarefaction is performed first if depth is specified.
    
    Args:
        otu_table: Original OTU table (samples as rows, OTUs as columns).
        rarefied_table: Pre-rarefied OTU table (optional).
        depth: Rarefaction depth (required if rarefied_table not provided).
        
    Returns:
        DataFrame with alpha diversity metrics per sample.
    """
    if rarefied_table is None:
        if depth is None:
            raise ValueError("Either rarefied_table or depth must be provided")
        rarefied_table = rarefy_table(otu_table, depth)
        
    diversity_metrics = pd.DataFrame(index=rarefied_table.index)
    
    for idx in rarefied_table.index:
        counts = rarefied_table.loc[idx].values
        total_count = counts.sum()
        
        if total_count == 0:
            diversity_metrics.loc[idx, 'shannon'] = 0.0
            diversity_metrics.loc[idx, 'simpson'] = 0.0
            diversity_metrics.loc[idx, 'observed_otus'] = 0
            continue
            
        # Filter out zeros for Shannon and Simpson
        non_zero = counts[counts > 0]
        probs = non_zero / non_zero.sum()
        
        # Shannon index: -sum(p * log(p))
        shannon = -np.sum(probs * np.log(probs))
        
        # Simpson index: 1 - sum(p^2)
        simpson = 1 - np.sum(probs ** 2)
        
        # Observed OTUs: count of non-zero features
        observed_otus = len(non_zero)
        
        diversity_metrics.loc[idx, 'shannon'] = shannon
        diversity_metrics.loc[idx, 'simpson'] = simpson
        diversity_metrics.loc[idx, 'observed_otus'] = observed_otus
        
    return diversity_metrics

def main():
    """
    Main entry point for alpha diversity computation.
    Loads cleaned data, performs rarefaction, calculates diversity metrics,
    and saves results.
    """
    config = load_config()
    input_path = Path(config['DATA_PATH']) / 'processed' / 'cleaned_microbiome_sleep.csv'
    output_path = Path(config['DATA_PATH']) / 'processed' / 'alpha_diversity_metrics.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Identify OTU columns (typically prefixed with 'otu_' or similar)
    otu_cols = [col for col in df.columns if col.startswith('otu_')]
    
    if not otu_cols:
        # Fallback: assume all numeric columns except metadata are OTUs
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        metadata_cols = ['sample_id', 'sleep_efficiency', 'sleep_duration_hours', 
                       'antibiotic_use_last_3m', 'age', 'gender']
        otu_cols = [col for col in numeric_cols if col not in metadata_cols]
        
    if not otu_cols:
        raise ValueError("No OTU columns found in the dataset")
        
    logger.info(f"Found {len(otu_cols)} OTU columns")
    
    otu_table = df.set_index('sample_id')[otu_cols]
    metadata = df.set_index('sample_id')[['sleep_efficiency', 'sleep_duration_hours']]
    
    # Get rarefaction depth from config or use a reasonable default
    rarefaction_depth = config.get('RAREFACTION_DEPTH', 10000)
    
    logger.info(f"Rarefying to depth {rarefaction_depth}")
    rarefied = rarefy_table(otu_table, rarefaction_depth)
    
    logger.info("Calculating alpha diversity metrics")
    diversity = calculate_alpha_diversity(otu_table, rarefied_table=rarefied)
    
    # Merge with metadata
    diversity_with_metadata = diversity.join(metadata)
    
    # Save results
    diversity_with_metadata.to_csv(output_path)
    logger.info(f"Alpha diversity metrics saved to {output_path}")
    
    return diversity_with_metadata

if __name__ == '__main__':
    main()
