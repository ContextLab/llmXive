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

def load_methyl_data(data_path: str) -> pd.DataFrame:
    """
    Load methylation data (beta values or M-values) from CSV/TSV.
    Expected format: Rows=CpG sites or Genes, Columns=Samples.
    First column is 'cpg_id' or 'gene_id'.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Methylation data file not found: {data_path}")
    
    logger.info(f"Loading methylation data from {data_path}")
    df = pd.read_csv(data_path, sep='\t', index_col=0)
    return df

def cpg_density_normalization(methyl_df: pd.DataFrame, cpg_map: Optional[Dict[str, int]] = None) -> pd.DataFrame:
    """
    Normalize methylation data based on CpG density if mapping is provided.
    If no mapping is provided, returns the dataframe as is (or simple scaling).
    For this implementation, we assume the input is already aggregated to gene-level
    or we perform a simple global normalization if gene-level mapping is missing.
    
    Logic: Adjust beta values by the number of CpGs associated with the feature.
    """
    logger.info("Applying CpG density normalization")
    
    if cpg_map is None:
        # If no mapping, we might just return the data or apply a global scaling
        # For now, return as is, assuming data is pre-aggregated or density info is not available
        logger.warning("No CpG map provided. Skipping density adjustment.")
        return methyl_df
    
    # Apply normalization factor
    # Example: normalized = value / density (or similar logic depending on data type)
    # Here we assume cpg_map maps index (gene/cpg) to count
    densities = pd.Series(cpg_map).reindex(methyl_df.index).fillna(1)
    
    # Avoid division by zero
    densities = densities.replace(0, 1)
    
    normalized_df = methyl_df.divide(densities, axis=0)
    return normalized_df

def calculate_gene_variance(normalized_df: pd.DataFrame) -> pd.Series:
    """
    Calculate variance for each gene/CpG across samples.
    """
    logger.info("Calculating gene variance")
    return normalized_df.var(axis=1)

def get_sample_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load sample metadata including generation information.
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

def logo_jackknife_variance(methyl_df: pd.DataFrame, metadata: Dict[str, Any], generation_col: str = 'generation') -> pd.DataFrame:
    """
    Implement Leave-One-Generation-Out (LOGO) jackknife variance for methylation data.
    
    Logic:
    1. Identify unique generations.
    2. For each generation G:
       - Exclude samples from generation G.
       - Calculate variance on the remaining samples.
    3. Return DataFrame of LOO variances.
    """
    logger.info("Starting LOGO jackknife variance calculation for methylation")
    
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
        logger.warning("Less than 2 generations found. LOGO requires at least 2.")
        return pd.DataFrame(np.nan, index=methyl_df.index, columns=['logo_variance'])

    results = {}
    
    for gen_to_remove in unique_generations:
        # Identify samples to KEEP
        keep_samples = [sid for sid, gen in sample_to_gen.items() if gen != gen_to_remove]
        
        if len(keep_samples) == 0:
            logger.warning(f"No samples remaining after removing generation {gen_to_remove}. Skipping.")
            continue
        
        # Subset dataframe
        valid_keep = [s for s in keep_samples if s in methyl_df.columns]
        subset_df = methyl_df[valid_keep]
        
        # Calculate variance
        variances = subset_df.var(axis=1)
        results[f"loo_gen_{gen_to_remove}"] = variances

    if not results:
        logger.error("No valid LOO variance calculations could be performed.")
        return pd.DataFrame(index=methyl_df.index)

    logo_df = pd.DataFrame(results)
    logger.info(f"Methylation LOGO jackknife variance matrix shape: {logo_df.shape}")
    return logo_df

def filter_low_variance_genes(variance_df: pd.DataFrame, threshold: float = 0.0) -> pd.DataFrame:
    """
    Filter out genes/CpGs with variance below a threshold.
    """
    logger.info("Filtering low variance genes")
    
    if isinstance(variance_df, pd.Series):
        mask = variance_df > threshold
        return variance_df[mask]
    elif isinstance(variance_df, pd.DataFrame):
        # Use mean LOO variance for filtering
        mean_var = variance_df.mean(axis=1)
        mask = mean_var > threshold
        return variance_df[mask]
    else:
        raise TypeError("variance_df must be Series or DataFrame")

def process_methyl_data(methyl_path: str, metadata_path: str, output_dir: str, cpg_map: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Main processing pipeline for methylation data including LOGO.
    """
    ensure_directories([output_dir])
    
    try:
        # Load data
        methyl_df = load_methyl_data(methyl_path)
        metadata = get_sample_metadata(metadata_path)
        
        # Normalize
        norm_df = cpg_density_normalization(methyl_df, cpg_map)
        
        # Perform LOGO jackknife
        logo_var_df = logo_jackknife_variance(norm_df, metadata)
        
        # Calculate mean LOO variance
        if not logo_var_df.empty:
            mean_logo_var = logo_var_df.mean(axis=1)
        else:
            mean_logo_var = pd.Series(dtype=float)
        
        # Filter low variance
        filtered_logo = filter_low_variance_genes(logo_var_df, threshold=0.0)
        filtered_mean = filter_low_variance_genes(mean_logo_var, threshold=0.0)
        
        # Save outputs
        output_logo_path = os.path.join(output_dir, "methyl_logo_variance.csv")
        output_mean_path = os.path.join(output_dir, "methyl_mean_logo_variance.csv")
        
        filtered_logo.to_csv(output_logo_path)
        filtered_mean.to_csv(output_mean_path)
        
        logger.info(f"Methylation LOGO variance saved to {output_logo_path}")
        
        return {
            "status": "success",
            "logo_variance_file": output_logo_path,
            "mean_logo_variance_file": output_mean_path,
            "n_genes": len(filtered_mean),
            "n_generations": logo_var_df.shape[1] if not logo_var_df.empty else 0
        }
        
    except Exception as e:
        logger.error(f"Error processing methylation data: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

def main():
    """
    Entry point for script execution.
    """
    methyl_path = get_env('METHYL_DATA_PATH', 'data/raw/methyl_beta_values.tsv')
    meta_path = get_env('METHYL_META_PATH', 'data/raw/methyl_metadata.json')
    out_dir = get_env('PREPROCESS_OUTPUT_DIR', 'data/processed')
    
    ensure_directories([out_dir])
    
    # Note: cpg_map loading is omitted for brevity as it depends on external annotation
    # In a real run, this would be loaded from a file if available.
    cpg_map = None 
    
    result = process_methyl_data(methyl_path, meta_path, out_dir, cpg_map)
    
    print(json.dumps(result, indent=2))
    
    if result['status'] != 'success':
        sys.exit(1)

if __name__ == "__main__":
    main()
