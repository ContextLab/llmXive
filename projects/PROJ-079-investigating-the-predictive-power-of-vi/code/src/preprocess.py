import logging
from typing import List, Dict, Any, Optional
import requests
from pathlib import Path
import pandas as pd
import json

from src.config import DATA_PROCESSED_PATH
from src.utils.logging import get_logger

logger = get_logger(__name__)

def map_isg_genes(species: str, gene_list: list) -> list:
    """
    Maps human ISG genes to orthologs for a given species using Ensembl Compara.
    Returns a list of Ensembl IDs.
    """
    # Placeholder for actual API call to Ensembl
    # In a real implementation, this would query the Compara API
    logger.info(f"Mapping ISG genes for species: {species}")
    return gene_list  # Simplified for now

def validate_isg_mapping(mappings: list, counts_matrix: pd.DataFrame) -> bool:
    """
    Verifies that mapped orthologs exist in the normalized counts matrix.
    
    Parameters
    ----------
    mappings : list
        List of mapped gene identifiers (Ensembl IDs or symbols) that should be present.
    counts_matrix : pd.DataFrame
        Normalized gene expression counts matrix with genes as columns (or index).
    
    Returns
    -------
    bool
        True if overlap >= 80%, False otherwise.
    
    Raises
    ------
    ValueError
        If inputs are invalid.
    
    Notes
    -----
    This implements FR-015: If overlap < 80%, the sample is marked as 'excluded'
    and the reason is logged. The function returns False to signal exclusion.
    """
    if not mappings:
        logger.warning("Empty mappings list provided to validate_isg_mapping.")
        return False
    
    if counts_matrix is None or counts_matrix.empty:
        logger.error("Counts matrix is empty or None.")
        return False
    
    # Determine if genes are columns or index
    # Standard convention: columns are genes, rows are samples
    available_genes = set(counts_matrix.columns)
    
    if not available_genes:
        # Fallback: check index
        available_genes = set(counts_matrix.index)
    
    mapped_genes = set(mappings)
    
    if not mapped_genes:
        logger.error("No mapped genes found in input list.")
        return False
    
    # Calculate overlap
    overlap = mapped_genes.intersection(available_genes)
    overlap_ratio = len(overlap) / len(mapped_genes)
    
    logger.info(f"ISG Mapping Validation: {len(overlap)} / {len(mapped_genes)} genes found ({overlap_ratio:.2%})")
    
    if overlap_ratio < 0.80:
        logger.error(f"FR-015 Violation: ISG mapping overlap is {overlap_ratio:.2%} (< 80%). "
                     f"Sample will be EXCLUDED. Missing genes: {mapped_genes - available_genes}")
        return False
    
    logger.info("ISG mapping validation passed (overlap >= 80%).")
    return True
