"""
Global filters for preprocessing:
1. Global methylation level filter (exclude samples/genes with <1% mean methylation)
2. Non-model organism exclusion (ensure organism is mouse, C. elegans, or Drosophila)
"""
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

from config import get_env

logger = logging.getLogger(__name__)

# Model organisms allowed per spec (US1)
ALLOWED_ORGANISMS = {
    "mus musculus",
    "homo sapiens", 
    "caenorhabditis elegans",
    "drosophila melanogaster",
    "c. elegans",
    "d. melanogaster",
    "mouse",
    "human",
    "fruit fly"
}

# Normalized names for lookup
ORGANISM_MAP = {
    "mus musculus": "mouse",
    "homo sapiens": "human",
    "caenorhabditis elegans": "c. elegans",
    "drosophila melanogaster": "drosophila",
    "c. elegans": "c. elegans",
    "d. melanogaster": "drosophila",
    "mouse": "mouse",
    "human": "human",
    "fruit fly": "drosophila"
}

def normalize_organism_name(organism: str) -> str:
    """Normalize organism name to lowercase and map to standard form."""
    if not organism:
        return ""
    org_lower = organism.lower().strip()
    return ORGANISM_MAP.get(org_lower, org_lower)

def is_model_organism(organism: str) -> bool:
    """Check if organism is in the allowed list."""
    normalized = normalize_organism_name(organism)
    return normalized in {normalize_organism_name(o) for o in ALLOWED_ORGANISMS}

def filter_by_organism(df: pd.DataFrame, organism_column: str = "organism") -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter dataframe to keep only model organisms.
    
    Args:
        df: Input dataframe with organism column
        organism_column: Name of the column containing organism info
        
    Returns:
        Tuple of (filtered dataframe, list of excluded organism names)
    """
    if organism_column not in df.columns:
        logger.warning(f"Organism column '{organism_column}' not found in dataframe. Keeping all rows.")
        return df, []
    
    # Normalize organism names
    df = df.copy()
    df['_normalized_organism'] = df[organism_column].apply(normalize_organism_name)
    
    # Filter
    mask = df['_normalized_organism'].apply(is_model_organism)
    excluded_mask = ~mask
    
    excluded_orgs = df.loc[excluded_mask, '_normalized_organism'].unique().tolist()
    filtered_df = df[mask].drop(columns=['_normalized_organism'])
    
    logger.info(f"Organism filter: kept {filtered_df.shape[0]} rows, excluded {excluded_mask.sum()} rows")
    if excluded_orgs:
        logger.info(f"Excluded organisms: {excluded_orgs}")
    
    return filtered_df, excluded_orgs

def filter_by_global_methylation_level(
    df: pd.DataFrame, 
    methylation_column: str = "mean_methylation",
    threshold: float = 0.01,
    min_samples: int = 1
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Filter out samples/genes with global methylation level below threshold.
    
    Args:
        df: Input dataframe with methylation values
        methylation_column: Column name containing methylation level
        threshold: Minimum methylation level (default 0.01 = 1%)
        min_samples: Minimum number of samples required to keep a gene
        
    Returns:
        Tuple of (filtered dataframe, stats dict)
    """
    if methylation_column not in df.columns:
        logger.warning(f"Methylation column '{methylation_column}' not found. No filtering applied.")
        return df, {"excluded_count": 0, "excluded_ids": []}
    
    df = df.copy()
    
    # Handle missing values
    df['_valid_meth'] = df[methylation_column].notna()
    
    # Filter by threshold
    mask = (df[methylation_column] >= threshold) | ~df['_valid_meth']
    
    excluded_mask = ~mask
    excluded_ids = df.loc[excluded_mask, df.columns[0]].tolist() if len(df.columns) > 0 else []
    
    filtered_df = df[mask].drop(columns=['_valid_meth'])
    
    stats = {
        "excluded_count": int(excluded_mask.sum()),
        "excluded_ids": excluded_ids[:10],  # First 10 for logging
        "threshold_used": threshold,
        "original_count": len(df),
        "filtered_count": len(filtered_df)
    }
    
    logger.info(f"Methylation filter (>{threshold*100}%): excluded {excluded_mask.sum()} rows")
    
    return filtered_df, stats

def apply_global_filters(
    methyl_df: pd.DataFrame,
    rna_df: pd.DataFrame,
    methyl_org_col: str = "organism",
    rna_org_col: str = "organism",
    methyl_col: str = "mean_methylation",
    methylation_threshold: float = 0.01
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Apply both organism and methylation filters to the datasets.
    
    Args:
        methyl_df: Methylation dataframe
        rna_df: RNA-seq dataframe
        methyl_org_col: Organism column name in methyl_df
        rna_org_col: Organism column name in rna_df
        methyl_col: Methylation level column name
        methylation_threshold: Minimum methylation threshold (default 0.01)
        
    Returns:
        Tuple of (filtered methyl_df, filtered rna_df, combined stats)
    """
    stats = {
        "organism_filter": {},
        "methylation_filter": {}
    }
    
    # Filter methylation data by organism
    methyl_df, methyl_excluded_orgs = filter_by_organism(methyl_df, methyl_org_col)
    stats["organism_filter"]["methyl"] = {
        "excluded_organisms": methyl_excluded_orgs,
        "rows_before": len(methyl_df),
        "rows_after": len(methyl_df)
    }
    
    # Filter RNA-seq data by organism
    rna_df, rna_excluded_orgs = filter_by_organism(rna_df, rna_org_col)
    stats["organism_filter"]["rna"] = {
        "excluded_organisms": rna_excluded_orgs,
        "rows_before": len(rna_df),
        "rows_after": len(rna_df)
    }
    
    # Filter methylation data by global methylation level
    methyl_df, methyl_stats = filter_by_global_methylation_level(
        methyl_df, 
        methyl_col, 
        threshold=methylation_threshold
    )
    stats["methylation_filter"] = methyl_stats
    
    logger.info(f"Global filters applied. Final shapes: methyl={methyl_df.shape}, rna={rna_df.shape}")
    
    return methyl_df, rna_df, stats

def main():
    """
    Main entry point for applying global filters.
    This function is designed to be called from main.py or run standalone.
    """
    import json
    
    # Load configuration
    data_dir = Path(get_env("DATA_DIR", "data"))
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Example: Load variance matrix and apply filters
    # In practice, this would be called after T017's filter_genes_by_variance_and_missing
    variance_matrix_path = processed_dir / "variance_matrix.csv"
    
    if not variance_matrix_path.exists():
        logger.warning(f"Variance matrix not found at {variance_matrix_path}. Skipping filter application.")
        return
    
    df = pd.read_csv(variance_matrix_path)
    logger.info(f"Loaded variance matrix with shape {df.shape}")
    
    # Apply organism filter (assuming 'organism' column exists)
    if "organism" in df.columns:
        filtered_df, org_stats = filter_by_organism(df, "organism")
        logger.info(f"After organism filter: {filtered_df.shape}, excluded: {org_stats}")
        df = filtered_df
    
    # Apply methylation filter if column exists
    if "mean_methylation" in df.columns:
        filtered_df, methyl_stats = filter_by_global_methylation_level(df, "mean_methylation", threshold=0.01)
        logger.info(f"After methylation filter: {filtered_df.shape}, stats: {methyl_stats}")
        df = filtered_df
    
    # Save filtered data
    output_path = processed_dir / "variance_matrix_filtered.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered data to {output_path}")
    
    # Save stats
    stats_path = processed_dir / "filter_stats.json"
    with open(stats_path, 'w') as f:
        json.dump({
            "organism_filter": org_stats if "organism" in df.columns else {},
            "methylation_filter": methyl_stats if "mean_methylation" in df.columns else {}
        }, f, indent=2)
    logger.info(f"Saved filter stats to {stats_path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
