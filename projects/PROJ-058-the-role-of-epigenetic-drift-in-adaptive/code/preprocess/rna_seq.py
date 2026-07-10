import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Import from sibling modules
from config import get_env, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_env('LOG_FILE', 'logs/pipeline.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_rna_seq_data(data_path: str) -> pd.DataFrame:
    """
    Load RNA-seq count data from a CSV/TSV file.
    Expected format: Rows=Genes, Columns=Samples.
    First column is 'gene_id' or 'gene_symbol'.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"RNA-seq data file not found: {data_path}")
    
    logger.info(f"Loading RNA-seq data from {data_path}")
    df = pd.read_csv(data_path, sep='\t', index_col=0)
    return df

def median_of_ratios_normalization(counts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform DESeq2-like median-of-ratios normalization.
    Calculates size factors and normalizes counts.
    """
    logger.info("Applying median-of-ratios normalization")
    
    # Calculate geometric mean for each gene (row)
    # Handle zeros by adding a small epsilon or using log-transform tricks
    # Here we use a simple geometric mean approach, ignoring zeros for the mean calculation
    # but keeping the matrix structure.
    
    # Add 1 to avoid log(0) issues for geometric mean calculation
    log_counts = np.log2(counts_df + 1)
    geo_means = np.exp(log_counts.mean(axis=1))
    
    # Calculate size factors for each sample (column)
    # Ratio = count / geo_mean
    ratios = counts_df / geo_means
    # Median of ratios for each column
    size_factors = ratios.median(axis=0)
    
    # Normalize
    normalized_df = counts_df.divide(size_factors, axis=1)
    
    return normalized_df

def calculate_gene_variance(normalized_df: pd.DataFrame) -> pd.Series:
    """
    Calculate variance for each gene across samples.
    """
    logger.info("Calculating gene variance")
    return normalized_df.var(axis=1)

def get_sample_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load sample metadata including generation information.
    Expected format: JSON or CSV with 'sample_id' and 'generation' columns.
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    logger.info(f"Loading metadata from {metadata_path}")
    if metadata_path.endswith('.json'):
        with open(metadata_path, 'r') as f:
            return json.load(f)
    else:
        df = pd.read_csv(metadata_path)
        return df.to_dict(orient='records')

def logo_jackknife_variance(counts_df: pd.DataFrame, metadata: Dict[str, Any], generation_col: str = 'generation') -> pd.DataFrame:
    """
    Implement Leave-One-Generation-Out (LOGO) jackknife variance.
    
    Logic:
    1. Identify unique generations in the metadata.
    2. For each generation G:
       - Create a subset of samples excluding all samples from generation G.
       - Calculate variance of genes on this subset.
       - Store this "leave-one-out" variance.
    3. Return a DataFrame where rows are genes and columns are the LOO variance estimates
       (or an aggregated statistic like mean LOO variance if preferred, but the task asks for
       the logic to ensure independent subsets).
    
    We will return a DataFrame of shape (n_genes, n_generations) containing the variance
    calculated on the dataset with that specific generation removed.
    """
    logger.info("Starting LOGO jackknife variance calculation")
    
    # Map sample_id to generation
    sample_to_gen = {}
    generations = set()
    for item in metadata:
        sid = item.get('sample_id')
        gen = item.get(generation_col)
        if sid and gen is not None:
            sample_to_gen[sid] = gen
            generations.add(gen)
    
    unique_generations = sorted(list(generations))
    logger.info(f"Found {len(unique_generations)} unique generations for LOGO: {unique_generations}")
    
    if len(unique_generations) < 2:
        logger.warning("Less than 2 generations found. LOGO requires at least 2 to leave one out.")
        # If only 1 generation, we can't leave one out meaningfully for variance estimation
        # Return NaN or original variance? Returning NaN to indicate failure of logic.
        return pd.DataFrame(np.nan, index=counts_df.index, columns=['logo_variance'])

    results = {}
    
    for gen_to_remove in unique_generations:
        # Identify samples to KEEP
        keep_samples = [sid for sid, gen in sample_to_gen.items() if gen != gen_to_remove]
        
        if len(keep_samples) == 0:
            logger.warning(f"No samples remaining after removing generation {gen_to_remove}. Skipping.")
            continue
        
        # Subset the dataframe
        # Ensure we only select columns that exist in counts_df and are in keep_samples
        valid_keep = [s for s in keep_samples if s in counts_df.columns]
        subset_df = counts_df[valid_keep]
        
        # Calculate variance on this subset
        variances = subset_df.var(axis=1)
        results[f"loo_gen_{gen_to_remove}"] = variances

    if not results:
        logger.error("No valid LOO variance calculations could be performed.")
        return pd.DataFrame(index=counts_df.index)

    logo_df = pd.DataFrame(results)
    logger.info(f"LOGO jackknife variance matrix shape: {logo_df.shape}")
    
    # Optionally, we can also calculate the mean of these LOO variances as a robust estimate
    # But the primary requirement is to perform the LOGO logic.
    # We return the full matrix so downstream tasks can analyze stability or use the mean.
    return logo_df

def filter_low_variance_genes(variance_df: pd.DataFrame, threshold: float = 0.0) -> pd.DataFrame:
    """
    Filter out genes with variance below a threshold.
    If input is a LOGO matrix, we might filter based on mean variance or min variance.
    Here we assume input is a Series (standard variance) or a DataFrame (LOGO).
    If DataFrame, we filter genes where ALL LOO variances are below threshold (conservative).
    """
    logger.info("Filtering low variance genes")
    
    if isinstance(variance_df, pd.Series):
        mask = variance_df > threshold
        return variance_df[mask]
    elif isinstance(variance_df, pd.DataFrame):
        # Filter genes where the mean LOO variance is above threshold (more robust)
        # Or strictly: where any LOO variance is above?
        # Let's use mean LOO variance for filtering to be robust against one bad LOO split
        mean_var = variance_df.mean(axis=1)
        mask = mean_var > threshold
        return variance_df[mask]
    else:
        raise TypeError("variance_df must be Series or DataFrame")

def process_rna_seq(rna_path: str, metadata_path: str, output_dir: str) -> Dict[str, Any]:
    """
    Main processing pipeline for RNA-seq data including LOGO.
    """
    ensure_directories([output_dir])
    
    try:
        # Load data
        counts_df = load_rna_seq_data(rna_path)
        metadata = get_sample_metadata(metadata_path)
        
        # Normalize
        norm_df = median_of_ratios_normalization(counts_df)
        
        # Perform LOGO jackknife
        logo_var_df = logo_jackknife_variance(norm_df, metadata)
        
        # Calculate mean LOO variance for final summary if needed
        if not logo_var_df.empty:
            mean_logo_var = logo_var_df.mean(axis=1)
        else:
            mean_logo_var = pd.Series(dtype=float)
        
        # Filter low variance
        filtered_logo = filter_low_variance_genes(logo_var_df, threshold=0.0)
        filtered_mean = filter_low_variance_genes(mean_logo_var, threshold=0.0)
        
        # Save outputs
        output_logo_path = os.path.join(output_dir, "rna_logo_variance.csv")
        output_mean_path = os.path.join(output_dir, "rna_mean_logo_variance.csv")
        
        filtered_logo.to_csv(output_logo_path)
        filtered_mean.to_csv(output_mean_path)
        
        logger.info(f"RNA-seq LOGO variance saved to {output_logo_path}")
        
        return {
            "status": "success",
            "logo_variance_file": output_logo_path,
            "mean_logo_variance_file": output_mean_path,
            "n_genes": len(filtered_mean),
            "n_generations": logo_var_df.shape[1] if not logo_var_df.empty else 0
        }
        
    except Exception as e:
        logger.error(f"Error processing RNA-seq data: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

def main():
    """
    Entry point for script execution.
    Expects environment variables or arguments for paths.
    """
    # Default paths for demonstration if env vars not set
    rna_path = get_env('RNA_SEQ_DATA_PATH', 'data/raw/rna_seq_counts.tsv')
    meta_path = get_env('RNA_SEQ_META_PATH', 'data/raw/rna_seq_metadata.json')
    out_dir = get_env('PREPROCESS_OUTPUT_DIR', 'data/processed')
    
    # Ensure output dir exists
    ensure_directories([out_dir])
    
    result = process_rna_seq(rna_path, meta_path, out_dir)
    
    print(json.dumps(result, indent=2))
    
    if result['status'] != 'success':
        sys.exit(1)

if __name__ == "__main__":
    main()
