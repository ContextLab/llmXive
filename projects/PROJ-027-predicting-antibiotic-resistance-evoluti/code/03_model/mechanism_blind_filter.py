"""
Mechanism-blind filtering for antibiotic resistance prediction.

This module excludes known resistance genes for the target antibiotic class
from the feature set to prevent data leakage and ensure the model learns
from secondary mechanisms rather than the primary resistance determinant.

Uses CARD database categories to map target antibiotic class to genes.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging import get_logger
from utils.config import load_config

logger = get_logger(__name__)

# CARD mapping: Antibiotic Class -> Gene/Protein Family patterns
# This is a simplified mapping based on CARD ontology
# In production, this would be dynamically loaded from CARD JSON
CARD_CLASS_TO_GENE_MAP = {
    "beta-lactam": [
        "blaTEM", "blaSHV", "blaCTX-M", "blaOXA", "blaPC1", 
        "ampC", "blaCMY", "blaDHA", "blaFOX", "blaMOX"
    ],
    "aminoglycoside": [
        "aac", "aph", "ant", "aad", "armA", "rmtB", "rmtC"
    ],
    "fluoroquinolone": [
        "qnr", "qepA", "oqxAB", "aac(6')-Ib-cr", "parC", "gyrA"
    ],
    "tetracycline": [
        "tet", "tetA", "tetB", "tetC", "tetD", "tetE", "tetM", "tetW"
    ],
    "macrolide": [
        "erm", "msr", "mph", "mel", "mphA", "ermB", "ermC"
    ],
    "sulfonamide": [
        "sul", "sul1", "sul2", "sul3"
    ],
    "trimethoprim": [
        "dfr", "dfrA", "dfrB", "dfrC", "dfrD"
    ],
    "chloramphenicol": [
        "cat", "cmlA", "floR", "cmIA"
    ],
    "glycopeptide": [
        "van", "vanA", "vanB", "vanC", "vanD", "vanE", "vanG"
    ],
    "polymyxin": [
        "mcr", "mcr-1", "mcr-2", "mcr-3", "mcr-4", "mcr-5"
    ],
    "fosfomycin": [
        "fos", "fosA", "fosB", "fosC"
    ],
    "nitroimidazole": [
        "nim", "nimA", "nimB", "nimC", "nimD", "nimE"
    ],
    "linezolid": [
        "cfr", "optrA", "poxtA"
    ],
    "colistin": [
        "mcr", "pmr", "mgrB"
    ]
}

def load_card_reference(card_data_path: Optional[Path] = None) -> Dict[str, List[str]]:
    """
    Load CARD reference data if available, otherwise use built-in mapping.
    
    Args:
        card_data_path: Path to CARD JSON file if available
        
    Returns:
        Dictionary mapping antibiotic classes to gene patterns
    """
    if card_data_path and card_data_path.exists():
        try:
            with open(card_data_path, 'r') as f:
                card_data = json.load(f)
            
            # Parse CARD data to extract class-gene mappings
            # This is a simplified extraction - real implementation would parse CARD ontology
            logger.info(f"Loading CARD reference from {card_data_path}")
            return card_data.get("antibiotic_class_to_genes", CARD_CLASS_TO_GENE_MAP)
            
        except Exception as e:
            logger.warning(f"Failed to load CARD reference: {e}. Using built-in mapping.")
            return CARD_CLASS_TO_GENE_MAP
    else:
        logger.info("CARD reference not found. Using built-in mapping.")
        return CARD_CLASS_TO_GENE_MAP

def get_target_class_genes(antibiotic_class: str, card_mapping: Dict[str, List[str]]) -> Set[str]:
    """
    Get the set of resistance genes associated with a specific antibiotic class.
    
    Args:
        antibiotic_class: The target antibiotic class (e.g., "beta-lactam")
        card_mapping: CARD class-to-gene mapping dictionary
        
    Returns:
        Set of gene names/patterns to exclude
    """
    # Normalize class name
    class_lower = antibiotic_class.lower().replace("-", "").replace(" ", "")
    
    # Try exact match first
    if antibiotic_class in card_mapping:
        return set(card_mapping[antibiotic_class])
    
    # Try normalized match
    for key, genes in card_mapping.items():
        if key.lower().replace("-", "").replace(" ", "") == class_lower:
            return set(genes)
    
    # If no match found, log warning and return empty set
    logger.warning(f"No gene mapping found for antibiotic class: {antibiotic_class}. Returning empty set.")
    return set()

def filter_mechanism_genes(
    feature_matrix: pd.DataFrame,
    target_class: str,
    card_mapping: Dict[str, List[str]],
    gene_columns_prefix: str = "gene_"
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out genes associated with the target antibiotic class from the feature matrix.
    
    Args:
        feature_matrix: Input feature matrix with gene presence columns
        target_class: The antibiotic class to filter genes for
        card_mapping: CARD class-to-gene mapping dictionary
        gene_columns_prefix: Prefix for gene presence columns (default: "gene_")
        
    Returns:
        Tuple of (filtered_feature_matrix, list_of_excluded_genes)
    """
    # Get genes to exclude
    genes_to_exclude = get_target_class_genes(target_class, card_mapping)
    excluded_genes = []
    
    if not genes_to_exclude:
        logger.info(f"No genes found to exclude for class: {target_class}")
        return feature_matrix, []
    
    # Identify columns to exclude
    columns_to_drop = []
    for gene_pattern in genes_to_exclude:
        # Check for exact column match
        col_name = f"{gene_columns_prefix}{gene_pattern}"
        if col_name in feature_matrix.columns:
            columns_to_drop.append(col_name)
            excluded_genes.append(gene_pattern)
            continue
        
        # Check for partial match (gene pattern appears in column name)
        for col in feature_matrix.columns:
            if gene_pattern.lower() in col.lower() and col.startswith(gene_columns_prefix):
                if col not in columns_to_drop:
                    columns_to_drop.append(col)
                    excluded_genes.append(gene_pattern)
    
    # Filter the matrix
    if columns_to_drop:
        logger.info(f"Excluding {len(columns_to_drop)} columns related to {target_class}: {columns_to_drop}")
        filtered_matrix = feature_matrix.drop(columns=columns_to_drop)
    else:
        logger.warning(f"No matching gene columns found for exclusion patterns: {list(genes_to_exclude)}")
        filtered_matrix = feature_matrix.copy()
    
    return filtered_matrix, excluded_genes

def save_filtered_matrix(
    filtered_matrix: pd.DataFrame,
    excluded_genes: List[str],
    target_class: str,
    output_path: Path,
    metadata_path: Optional[Path] = None
) -> None:
    """
    Save the filtered feature matrix and metadata about excluded genes.
    
    Args:
        filtered_matrix: The filtered feature matrix
        excluded_genes: List of genes that were excluded
        target_class: The antibiotic class that was filtered for
        output_path: Path to save the filtered matrix
        metadata_path: Optional path to save exclusion metadata
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save filtered matrix
    filtered_matrix.to_csv(output_path, index=False)
    logger.info(f"Saved filtered feature matrix to {output_path}")
    
    # Save exclusion metadata
    if metadata_path:
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        exclusion_metadata = {
            "target_class": target_class,
            "excluded_genes": excluded_genes,
            "original_columns": len(feature_matrix.columns) if 'feature_matrix' in locals() else 0,
            "filtered_columns": len(filtered_matrix.columns),
            "exclusion_count": len(excluded_genes),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        with open(metadata_path, 'w') as f:
            json.dump(exclusion_metadata, f, indent=2)
        
        logger.info(f"Saved exclusion metadata to {metadata_path}")

def main():
    """Main entry point for mechanism-blind filtering."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Filter mechanism genes from feature matrix")
    parser.add_argument("--input", type=str, required=True, help="Path to input feature matrix CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output filtered feature matrix CSV")
    parser.add_argument("--class", dest="antibiotic_class", type=str, required=True, 
                      help="Target antibiotic class to filter genes for")
    parser.add_argument("--card-ref", type=str, default=None, help="Path to CARD reference JSON (optional)")
    parser.add_argument("--metadata-output", type=str, default=None, help="Path to save exclusion metadata JSON")
    parser.add_argument("--config", type=str, default=None, help="Path to config file")
    
    args = parser.parse_args()
    
    # Setup logging
    config_path = Path(args.config) if args.config else None
    if config_path and config_path.exists():
        config = load_config(config_path)
        # Setup file logging based on config if needed
    
    logger.info(f"Starting mechanism-blind filtering for class: {args.antibiotic_class}")
    
    # Load feature matrix
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        feature_matrix = pd.read_csv(input_path)
        logger.info(f"Loaded feature matrix with {len(feature_matrix)} rows and {len(feature_matrix.columns)} columns")
    except Exception as e:
        logger.error(f"Failed to load feature matrix: {e}")
        sys.exit(1)
    
    # Load CARD reference
    card_ref_path = Path(args.card_ref) if args.card_ref else None
    card_mapping = load_card_reference(card_ref_path)
    
    # Filter genes
    filtered_matrix, excluded_genes = filter_mechanism_genes(
        feature_matrix,
        args.antibiotic_class,
        card_mapping
    )
    
    # Save results
    output_path = Path(args.output)
    metadata_path = Path(args.metadata_output) if args.metadata_output else None
    
    save_filtered_matrix(
        filtered_matrix,
        excluded_genes,
        args.antibiotic_class,
        output_path,
        metadata_path
    )
    
    logger.info(f"Mechanism-blind filtering complete. Excluded {len(excluded_genes)} genes.")
    logger.info(f"Output saved to: {output_path}")
    
    if metadata_path:
        logger.info(f"Metadata saved to: {metadata_path}")

if __name__ == "__main__":
    main()
