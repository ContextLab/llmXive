import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd

from config import get_config, setup_logging
from logging_integration import get_pipeline_logger, log_exclusion_counts

# Constants for data source type detection
SOURCE_TYPE_ALIASES = [
    'data_source_type',
    'source_type',
    'experiment_type',
    'data_origin',
    'study_type',
    'experimental_type'
]

EXCLUDED_SOURCE_VALUES = [
    'manipulated',
    'controlled',
    'nutrient_manipulation',
    'treatment',
    'manipulated_nutrients',
    'controlled_environment'
]

# Global state flag set by T014
p_n_available: bool = False

def set_p_n_available(status: bool) -> None:
    """Set the global flag indicating if P/N columns are available."""
    global p_n_available
    p_n_available = status

def fetch_plantpheno() -> pd.DataFrame:
    """
    Fetch PlantPheno dataset.
    In a real implementation, this would use datasets.load_dataset or a direct URL.
    For this task, we assume the data is available via a verified source or T013 handles it.
    """
    config = get_config()
    # Placeholder for actual fetch logic from T013
    # This function is expected to be implemented fully in T013
    # We raise an error if not implemented to ensure T013 runs first
    raise NotImplementedError("fetch_plantpheno must be implemented in T013")

def fetch_rootreader() -> pd.DataFrame:
    """
    Fetch RootReader dataset.
    Placeholder for T013 implementation.
    """
    raise NotImplementedError("fetch_rootreader must be implemented in T013")

def parse_rootreader(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse RootReader DataFrame into standard schema.
    Placeholder for T013 implementation.
    """
    raise NotImplementedError("parse_rootreader must be implemented in T013")

def check_p_n_columns(df: pd.DataFrame) -> bool:
    """
    Check if Phosphorus and Nitrogen columns exist.
    Sets global p_n_available flag.
    """
    global p_n_available
    # Check for standard names or aliases
    p_cols = [c for c in df.columns if 'phosphorus' in c.lower() or 'p_' in c.lower()]
    n_cols = [c for c in df.columns if 'nitrogen' in c.lower() or 'n_' in c.lower()]
    
    p_n_available = len(p_cols) > 0 and len(n_cols) > 0
    return p_n_available

def detect_source_type_column(df: pd.DataFrame) -> str:
    """
    Detect the column representing data source type.
    Raises ValueError if no matching column is found.
    """
    for alias in SOURCE_TYPE_ALIASES:
        if alias in df.columns:
            return alias
    
    # Try case-insensitive match
    cols_lower = {c.lower(): c for c in df.columns}
    for alias in SOURCE_TYPE_ALIASES:
        if alias.lower() in cols_lower:
            return cols_lower[alias.lower()]
    
    raise ValueError(
        f"Could not detect 'data_source_type' column. "
        f"Checked aliases: {SOURCE_TYPE_ALIASES}. "
        f"Available columns: {list(df.columns)}"
    )

def apply_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Apply filtering logic as per T015:
    1. Exclude rows where data_source_type indicates manipulation/controlled conditions.
    2. Exclude rows where Phosphorus or Nitrogen are missing (if p_n_available).
    3. Exclude species with n < 20.
    
    Returns:
        Tuple of (filtered_df, exclusion_stats)
    """
    global p_n_available
    logger = get_pipeline_logger("data_ingestion")
    
    stats = {
        "total_rows_input": len(df),
        "excluded_source_type": 0,
        "excluded_missing_nutrients": 0,
        "excluded_low_sample_size": 0,
        "total_rows_output": 0
    }
    
    # 1. Filter by data_source_type
    source_col = detect_source_type_column(df)
    initial_len = len(df)
    
    # Normalize values to lowercase for comparison
    df[source_col] = df[source_col].astype(str).str.lower().str.strip()
    
    mask_source = ~df[source_col].isin(EXCLUDED_SOURCE_VALUES)
    df_filtered = df[mask_source].copy()
    stats["excluded_source_type"] = initial_len - len(df_filtered)
    
    logger.info(f"Excluded {stats['excluded_source_type']} rows due to data_source_type in {EXCLUDED_SOURCE_VALUES}")
    
    # 2. Filter by missing nutrients (if p_n_available)
    if p_n_available:
        # Identify P and N columns
        p_col = next((c for c in df_filtered.columns if 'phosphorus' in c.lower() or 'p_' in c.lower()), None)
        n_col = next((c for c in df_filtered.columns if 'nitrogen' in c.lower() or 'n_' in c.lower()), None)
        
        if p_col and n_col:
            initial_len = len(df_filtered)
            mask_nutrients = df_filtered[p_col].notna() & df_filtered[n_col].notna()
            df_filtered = df_filtered[mask_nutrients].copy()
            stats["excluded_missing_nutrients"] = initial_len - len(df_filtered)
            logger.info(f"Excluded {stats['excluded_missing_nutrients']} rows due to missing P/N values")
        else:
            logger.warning("P/N columns not found despite p_n_available=True")
    
    # 3. Filter by species sample size (n < 20)
    initial_len = len(df_filtered)
    species_counts = df_filtered['species'].value_counts()
    valid_species = species_counts[species_counts >= 20].index.tolist()
    excluded_species = species_counts[species_counts < 20].index.tolist()
    
    mask_species = df_filtered['species'].isin(valid_species)
    df_filtered = df_filtered[mask_species].copy()
    stats["excluded_low_sample_size"] = initial_len - len(df_filtered)
    stats["excluded_species_list"] = excluded_species
    stats["total_species_input"] = len(species_counts)
    stats["excluded_species_count"] = len(excluded_species)
    
    logger.info(f"Excluded {stats['excluded_low_sample_size']} rows due to species sample size < 20")
    logger.info(f"Excluded species (n<20): {excluded_species}")
    
    stats["total_rows_output"] = len(df_filtered)
    
    return df_filtered, stats

def write_species_counts_report(stats: Dict[str, Any]) -> Path:
    """
    Write the species counts report to artifacts/reports/species_counts.json.
    """
    config = get_config()
    output_path = Path(config.get("OUTPUT_PATH", "artifacts/reports")) / "species_counts.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure keys match spec exactly
    report = {
        "total_species_input": stats.get("total_species_input", 0),
        "excluded_species_count": stats.get("excluded_species_count", 0),
        "excluded_species_list": stats.get("excluded_species_list", [])
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger = get_pipeline_logger("data_ingestion")
    logger.info(f"Species counts report written to {output_path}")
    return output_path

def main():
    """
    Main entry point for T015 filtering logic.
    Assumes T013 (fetching) and T014 (P/N check) have been executed.
    """
    logger = setup_logging()
    logger.info("Starting T015: Filtering logic implementation")
    
    # In a real pipeline, data would be fetched here or passed from previous step
    # For this task, we assume the data is available in a processed state or fetched by T013
    # Since T013 is marked as completed, we assume fetch_plantpheno works
    # However, to make this script runnable for verification, we need to handle the case
    # where T013 might not have fully populated the data yet.
    
    # NOTE: This script is designed to be run after T013 and T014.
    # If T013 hasn't been run, fetch_plantpheno will raise NotImplementedError.
    # If T014 hasn't been run, p_n_available will be False.
    
    try:
        # Attempt to fetch data (T013 responsibility)
        df = fetch_plantpheno()
    except NotImplementedError as e:
        logger.error(f"Data fetching not implemented: {e}")
        print(f"Error: {e}. Please ensure T013 is completed.")
        sys.exit(1)
    
    # Ensure P/N check was done (T014 responsibility)
    # If not, we check here as a fallback
    if not p_n_available:
        logger.warning("p_n_available is False. Checking columns now.")
        check_p_n_columns(df)
    
    # Apply filters
    filtered_df, stats = apply_filters(df)
    
    # Write report
    write_species_counts_report(stats)
    
    logger.info("T015 completed successfully")
    return filtered_df, stats

if __name__ == "__main__":
    main()
