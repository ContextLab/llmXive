"""
Collinearity analysis module for merging climate and trait data.

This module provides functionality to merge climate-derived predictor variables
with species-level functional traits to create a unified predictor matrix
required for Variance Inflation Factor (VIF) analysis and model training.

Prerequisites:
- T008: Preprocessed occurrence data and background sampling
- T013: Climate raster data loaded and aligned
- T020: Trait data fetched from TRY database

Outputs:
- Merged predictor DataFrame with columns for climate variables and traits
- Metadata regarding species coverage and missing data patterns
"""

import logging
import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any, List

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Constants for expected data structures
CLIMATE_COLUMNS = [
    'bio1', 'bio2', 'bio3', 'bio4', 'bio5', 'bio6', 'bio7', 
    'bio8', 'bio9', 'bio10', 'bio11', 'bio12', 'bio13', 
    'bio14', 'bio15', 'bio16', 'bio17', 'bio18', 'bio19'
]

TRAIT_COLUMNS = ['sla', 'seed_mass', 'plant_height']

SPECIES_COLUMN = 'species'

def load_climate_data(climate_path: str) -> pd.DataFrame:
    """
    Load preprocessed climate data from a CSV file.
    
    Args:
        climate_path: Path to the CSV file containing climate variables
        
    Returns:
        DataFrame with climate variables indexed by species
        
    Raises:
        FileNotFoundError: If the climate file does not exist
        ValueError: If expected columns are missing
    """
    logger.info(f"Loading climate data from {climate_path}")
    
    try:
        df = pd.read_csv(climate_path)
    except FileNotFoundError:
        logger.error(f"Climate data file not found: {climate_path}")
        raise
    
    # Validate expected columns
    missing_cols = set(CLIMATE_COLUMNS) - set(df.columns)
    if missing_cols:
        logger.warning(f"Missing expected climate columns: {missing_cols}")
    
    # Aggregate to species level (mean values per species)
    if SPECIES_COLUMN in df.columns:
        climate_agg = df.groupby(SPECIES_COLUMN)[CLIMATE_COLUMNS].mean().reset_index()
        logger.info(f"Aggregated climate data for {len(climate_agg)} species")
    else:
        logger.warning("No species column found in climate data, using raw data")
        climate_agg = df
        
    return climate_agg

def load_trait_data(trait_path: str) -> pd.DataFrame:
    """
    Load preprocessed trait data from a CSV file.
    
    Args:
        trait_path: Path to the CSV file containing trait values
        
    Returns:
        DataFrame with trait values indexed by species
        
    Raises:
        FileNotFoundError: If the trait file does not exist
        ValueError: If expected columns are missing
    """
    logger.info(f"Loading trait data from {trait_path}")
    
    try:
        df = pd.read_csv(trait_path)
    except FileNotFoundError:
        logger.error(f"Trait data file not found: {trait_path}")
        raise
    
    # Validate expected columns
    missing_cols = set(TRAIT_COLUMNS) - set(df.columns)
    if missing_cols:
        logger.warning(f"Missing expected trait columns: {missing_cols}")
    
    # Aggregate to species level if multiple records exist
    if SPECIES_COLUMN in df.columns:
        trait_agg = df.groupby(SPECIES_COLUMN)[TRAIT_COLUMNS].mean().reset_index()
        logger.info(f"Aggregated trait data for {len(trait_agg)} species")
    else:
        logger.warning("No species column found in trait data, using raw data")
        trait_agg = df
        
    return trait_agg

def merge_predictors(
    climate_df: pd.DataFrame, 
    trait_df: pd.DataFrame,
    species_column: str = SPECIES_COLUMN
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Merge climate and trait data into a unified predictor set.
    
    This function performs an inner join on species to create a complete
    predictor matrix containing both environmental and functional trait variables.
    
    Args:
        climate_df: DataFrame with climate variables
        trait_df: DataFrame with trait values
        species_column: Name of the column containing species names
        
    Returns:
        Tuple of (merged DataFrame, metadata dictionary)
        
    Metadata includes:
        - total_species: Number of species in the merged set
        - climate_species: Number of species with climate data
        - trait_species: Number of species with trait data
        - missing_traits: List of species missing trait data
        - missing_climate: List of species missing climate data
    """
    logger.info("Merging climate and trait predictor data")
    
    # Perform inner join to keep only species with both data types
    merged = pd.merge(
        climate_df, 
        trait_df, 
        on=species_column, 
        how='inner'
    )
    
    # Calculate metadata
    climate_species = set(climate_df[species_column].unique())
    trait_species = set(trait_df[species_column].unique())
    merged_species = set(merged[species_column].unique())
    
    missing_traits = list(climate_species - trait_species)
    missing_climate = list(trait_species - climate_species)
    
    metadata = {
        'total_species': len(merged),
        'climate_species': len(climate_species),
        'trait_species': len(trait_species),
        'missing_traits': missing_traits,
        'missing_climate': missing_climate,
        'excluded_species_count': len(climate_species - merged_species) + len(trait_species - merged_species)
    }
    
    logger.info(f"Merged dataset contains {metadata['total_species']} species")
    logger.info(f"Excluded {metadata['excluded_species_count']} species due to missing data")
    
    if metadata['missing_traits']:
        logger.warning(f"Species missing trait data: {metadata['missing_traits'][:5]}...")
        
    if metadata['missing_climate']:
        logger.warning(f"Species missing climate data: {metadata['missing_climate'][:5]}...")
        
    return merged, metadata

def create_full_predictor_matrix(
    climate_path: str,
    trait_path: str,
    output_path: Optional[str] = None
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main entry point for creating the full predictor matrix.
    
    Loads climate and trait data, merges them, and optionally saves the result.
    
    Args:
        climate_path: Path to climate data CSV
        trait_path: Path to trait data CSV
        output_path: Optional path to save the merged DataFrame
        
    Returns:
        Tuple of (merged DataFrame, metadata dictionary)
        
    Raises:
        FileNotFoundError: If input files do not exist
        ValueError: If merging results in an empty DataFrame
    """
    climate_df = load_climate_data(climate_path)
    trait_df = load_trait_data(trait_path)
    
    merged_df, metadata = merge_predictors(climate_df, trait_df)
    
    if merged_df.empty:
        error_msg = "Merging climate and trait data resulted in an empty DataFrame. " \
                   "Check that species names match between the two datasets."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Save if output path provided
    if output_path:
        logger.info(f"Saving merged predictor matrix to {output_path}")
        merged_df.to_csv(output_path, index=False)
    
    return merged_df, metadata

def get_predictor_columns() -> List[str]:
    """
    Return the list of all predictor column names.
    
    Returns:
        List of column names including climate variables and traits
    """
    return CLIMATE_COLUMNS + TRAIT_COLUMNS

def validate_predictor_matrix(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate that a DataFrame contains the expected predictor structure.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    required_cols = get_predictor_columns() + [SPECIES_COLUMN]
    
    missing = set(required_cols) - set(df.columns)
    if missing:
        issues.append(f"Missing required columns: {missing}")
    
    # Check for infinite values
    if np.any(np.isinf(df[required_cols].select_dtypes(include=[np.number]).values)):
        issues.append("DataFrame contains infinite values")
        
    # Check for excessive NaN
    nan_counts = df[required_cols].select_dtypes(include=[np.number]).isna().sum()
    high_nan = nan_counts[nan_counts > len(df) * 0.5]
    if not high_nan.empty:
        issues.append(f"Columns with >50% NaN: {high_nan.index.tolist()}")
        
    return len(issues) == 0, issues