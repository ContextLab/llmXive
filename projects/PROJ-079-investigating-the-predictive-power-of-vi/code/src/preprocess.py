import logging
import csv
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path
import pandas as pd
from src.config import DATA_PROCESSED_PATH

logger = logging.getLogger(__name__)

def map_isg_genes(species: str, gene_list: list) -> list:
    """
    Map human ISG set to orthologs for non-human species using Ensembl Compara.
    Fallback: If API fails, exclude sample and log reason.
    """
    if not gene_list:
        return []
    
    # Placeholder implementation - actual Ensembl API call would go here
    # This is a stub to maintain API compatibility
    logger.warning(f"Ortholog mapping for {species} not fully implemented. Returning original list.")
    return gene_list

def save_ortholog_mapping(mapping: Dict[str, str], output_path: str) -> None:
    """Save ortholog mapping to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['human_gene', 'ortholog_gene', 'species'])
        for human_gene, ortholog_info in mapping.items():
            writer.writerow([human_gene, ortholog_info['gene'], ortholog_info['species']])

def process_isg_mapping_for_species(species: str, isg_genes: list, normalized_counts: pd.DataFrame) -> list:
    """
    Process ISG mapping for a specific species and return filtered gene list.
    """
    if species.lower() == 'human':
        return isg_genes
    
    mapped_genes = map_isg_genes(species, isg_genes)
    # Filter to genes that exist in the normalized_counts columns
    available_genes = [g for g in mapped_genes if g in normalized_counts.columns]
    return available_genes

def normalize_counts(counts_matrix: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize counts matrix using edgeR's calcNormFactors via rpy2.
    Falls back to TMM-like manual calculation if rpy2 is unavailable.
    """
    try:
        import rpy2.robjects as ro
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.packages import importr
        pandas2ri.activate()
        
        edgeR = importr('edgeR')
        dge = edgeR.DGEList(counts=pandas2ri.p2r(counts_matrix))
        dge = edgeR.calcNormFactors(dge, method='TMM')
        
        # Extract normalized counts
        norm_counts = pandas2ri.r2py(dge[['counts']])
        return norm_counts
    except ImportError:
        logger.warning("rpy2 not available. Using fallback normalization (library size scaling).")
        lib_sizes = counts_matrix.sum(axis=1)
        median_lib_size = lib_sizes.median()
        norm_factors = median_lib_size / lib_sizes
        return counts_matrix.multiply(norm_factors, axis=0)

def save_normalized_counts(counts_matrix: pd.DataFrame, output_path: str) -> None:
    """Save normalized counts to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    counts_matrix.to_csv(output_path, index=True)

def calculate_isg_score(normalized_counts: pd.DataFrame, isg_genes: list) -> pd.Series:
    """
    Calculate ISG score as the first principal component of ISG gene expression.
    """
    if not isg_genes:
        raise ValueError("ISG gene list is empty. Cannot calculate ISG score.")
    
    # Filter to available ISG genes
    available_isg = [g for g in isg_genes if g in normalized_counts.columns]
    if not available_isg:
        raise ValueError("No ISG genes found in normalized counts matrix.")
    
    isg_matrix = normalized_counts[available_isg]
    
    # Standardize
    isg_matrix_std = (isg_matrix - isg_matrix.mean()) / isg_matrix.std()
    
    # PCA
    from sklearn.decomposition import PCA
    pca = PCA(n_components=1)
    scores = pca.fit_transform(isg_matrix_std)
    
    return pd.Series(scores.flatten(), index=normalized_counts.index, name='isg_score')

def filter_samples(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter samples to remove rows with missing strain links and ensure >=30 samples remain.
    
    Args:
        merged_df: DataFrame containing merged data with 'strain_accession' column.
    
    Returns:
        Filtered DataFrame with valid strain links and >=30 samples.
    
    Raises:
        ValueError: If fewer than 30 samples remain after filtering.
    """
    logger.info(f"Starting sample filtering. Initial sample count: {len(merged_df)}")
    
    # Identify the strain link column - try common names
    strain_col = None
    possible_cols = ['strain_accession', 'accession', 'strain_id', 'host_accession']
    for col in possible_cols:
        if col in merged_df.columns:
            strain_col = col
            break
    
    if strain_col is None:
        raise ValueError("Could not identify strain accession column in merged dataframe. "
                       f"Available columns: {list(merged_df.columns)}")
    
    # Remove rows with missing strain links
    initial_count = len(merged_df)
    filtered_df = merged_df.dropna(subset=[strain_col])
    filtered_df = filtered_df[filtered_df[strain_col].astype(str).str.strip() != '']
    
    removed_count = initial_count - len(filtered_df)
    logger.info(f"Removed {removed_count} samples with missing strain links. "
               f"Remaining: {len(filtered_df)}")
    
    # Check minimum sample count
    min_samples = 30
    if len(filtered_df) < min_samples:
        error_msg = (f"Sample filtering resulted in {len(filtered_df)} samples, "
                    f"which is below the minimum required {min_samples} per FR-013. "
                    f"Pipeline must abort.")
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Sample filtering complete. Final sample count: {len(filtered_df)}")
    return filtered_df
