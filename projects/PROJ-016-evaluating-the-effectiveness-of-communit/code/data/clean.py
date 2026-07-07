import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
from logging_config import get_logger
from config import get_config

def standardize_iso_code(df: pd.DataFrame, code_col: str = 'country_code') -> pd.DataFrame:
    """
    Standardize country codes to ISO 3-letter format.
    """
    df = df.copy()
    if code_col in df.columns:
        df[code_col] = df[code_col].str.upper().str.strip()
        # Simple mapping for common 2-letter to 3-letter conversions if needed
        # For now, we assume data comes pre-formatted or we just enforce uppercase
    return df

def standardize_year(df: pd.DataFrame, year_col: str = 'year') -> pd.DataFrame:
    """
    Standardize year column to integer type.
    """
    df = df.copy()
    if year_col in df.columns:
        df[year_col] = pd.to_numeric(df[year_col], errors='coerce').astype('Int64')
    return df

def load_fao_data(file_path: str) -> pd.DataFrame:
    """
    Load FAO forest area change data from CSV.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"FAO data file not found: {file_path}")
    df = pd.read_csv(path)
    return df

def load_world_bank_data(file_path: str) -> pd.DataFrame:
    """
    Load World Bank GDP and population density data from CSV.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"World Bank data file not found: {file_path}")
    df = pd.read_csv(path)
    return df

def load_regime_data(file_path: str) -> pd.DataFrame:
    """
    Load regime classification data from CSV.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Regime data file not found: {file_path}")
    df = pd.read_csv(path)
    return df

def merge_datasets(df_fao: pd.DataFrame, df_wb: pd.DataFrame, df_regime: pd.DataFrame) -> pd.DataFrame:
    """
    Merge FAO, World Bank, and Regime datasets on country_code and year.
    """
    # Ensure common columns exist
    common_cols = ['country_code', 'year']
    for col in common_cols:
        if col not in df_fao.columns:
            raise ValueError(f"Missing column '{col}' in FAO data")
        if col not in df_wb.columns:
            raise ValueError(f"Missing column '{col}' in World Bank data")
        if col not in df_regime.columns:
            raise ValueError(f"Missing column '{col}' in Regime data")

    # Merge step-by-step
    df_merged = pd.merge(df_fao, df_wb, on=['country_code', 'year'], how='outer')
    df_merged = pd.merge(df_merged, df_regime, on=['country_code', 'year'], how='outer')
    return df_merged

def drop_missing_primary_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop rows where primary variables (land_use_change_rate, regime_type) are missing.
    Returns the cleaned dataframe.
    """
    primary_vars = ['land_use_change_rate', 'regime_type']
    initial_count = len(df)
    df_cleaned = df.dropna(subset=primary_vars)
    dropped_count = initial_count - len(df_cleaned)
    logging.info(f"Dropped {dropped_count} rows due to missing primary variables.")
    return df_cleaned

def clean_and_merge_data(fao_path: str, wb_path: str, regime_path: str) -> pd.DataFrame:
    """
    Full pipeline: load, standardize, merge, and drop missing primary vars.
    """
    logger = get_logger(__name__)
    logger.info("Starting data cleaning and merging pipeline.")

    df_fao = load_fao_data(fao_path)
    df_fao = standardize_year(df_fao)
    df_fao = standardize_iso_code(df_fao)

    df_wb = load_world_bank_data(wb_path)
    df_wb = standardize_year(df_wb)
    df_wb = standardize_iso_code(df_wb)

    df_regime = load_regime_data(regime_path)
    df_regime = standardize_year(df_regime)
    df_regime = standardize_iso_code(df_regime)

    df_merged = merge_datasets(df_fao, df_wb, df_regime)
    df_final = drop_missing_primary_vars(df_merged)

    logger.info(f"Final dataset shape: {df_final.shape}")
    return df_final

def calculate_coverage_rate(merged_count: int, total_count: int) -> float:
    """
    Calculate the coverage rate as the ratio of merged records to total available records.
    """
    if total_count == 0:
        return 0.0
    return merged_count / total_count

def apply_fr007_exclusion(df: pd.DataFrame, country_col: str = 'country_code', year_col: str = 'year') -> pd.DataFrame:
    """
    Apply FR-007 exclusion logic:
    1. Secondary Variables (GDP, Pop): Log missing variable, exclude row, continue.
    2. Primary Variables (Land-Use, Regime): Log "Primary Variable Missing", exclude row.
       If >20% of a country's years are missing for a primary variable, exclude the entire country.
    
    Args:
        df: Input dataframe with columns including 'country_code', 'year', 'gdp_per_capita', 
            'population_density', 'land_use_change_rate', 'regime_type'.
        country_col: Name of the country code column.
        year_col: Name of the year column.
    
    Returns:
        Filtered dataframe with excluded rows and countries removed.
    """
    logger = get_logger(__name__)
    df = df.copy()
    
    primary_vars = ['land_use_change_rate', 'regime_type']
    secondary_vars = ['gdp_per_capita', 'population_density']
    
    # Track countries to exclude
    countries_to_exclude = set()
    
    # Step 1: Check Primary Variables for country-level exclusion
    for var in primary_vars:
        if var not in df.columns:
            logger.warning(f"Primary variable '{var}' not found in dataset. Skipping check.")
            continue
        
        # Group by country and calculate missing rate
        country_stats = df.groupby(country_col).apply(
            lambda x: x[var].isna().mean(), 
            include_groups=False
        )
        
        # Identify countries where >20% of years are missing for this primary variable
        bad_countries = country_stats[country_stats > 0.20].index.tolist()
        
        if bad_countries:
            logger.warning(f"Excluding {len(bad_countries)} countries because >20% of years are missing for '{var}': {bad_countries}")
            countries_to_exclude.update(bad_countries)
        
        # Log specific missing rows for primary variables (before dropping)
        missing_mask = df[var].isna()
        missing_rows = df[missing_mask]
        for _, row in missing_rows.iterrows():
            logger.info(f"Primary Variable Missing: {var} is missing for {row.get(country_col)} in year {row.get(year_col)}")
    
    # Remove rows belonging to excluded countries
    if countries_to_exclude:
        df = df[~df[country_col].isin(countries_to_exclude)]
        logger.info(f"Removed {len(countries_to_exclude)} countries due to excessive missing primary data.")
    
    # Step 2: Check Secondary Variables for row-level exclusion
    for var in secondary_vars:
        if var not in df.columns:
            logger.warning(f"Secondary variable '{var}' not found in dataset. Skipping check.")
            continue
        
        missing_mask = df[var].isna()
        missing_rows = df[missing_mask]
        
        for _, row in missing_rows.iterrows():
            logger.info(f"Secondary Variable Missing: {var} is missing for {row.get(country_col)} in year {row.get(year_col)}. Excluding row.")
        
        # Drop rows where secondary variable is missing
        df = df.dropna(subset=[var])
    
    logger.info(f"FR-007 Exclusion complete. Final shape: {df.shape}")
    return df

def main():
    """
    Main entry point for the data cleaning script.
    Reads from data/raw and data/processed, applies cleaning logic,
    and writes the final cleaned dataset to data/processed.
    """
    config = get_config()
    logger = get_logger(__name__)
    
    # Define paths
    raw_dir = Path(config['data_paths']['raw'])
    processed_dir = Path(config['data_paths']['processed'])
    
    fao_file = raw_dir / 'fao_forest_area_change.csv'
    wb_file = raw_dir / 'world_bank_gdp_pop.csv'
    regime_file = processed_dir / 'regime_classified.csv'
    
    output_file = processed_dir / 'cleaned_data.csv'
    
    logger.info(f"Loading data from: {fao_file}, {wb_file}, {regime_file}")
    
    try:
        # Load and merge data
        df = clean_and_merge_data(
            str(fao_file),
            str(wb_file),
            str(regime_file)
        )
        
        # Apply FR-007 exclusion logic
        df_cleaned = apply_fr007_exclusion(df)
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Save final dataset
        df_cleaned.to_csv(output_file, index=False)
        logger.info(f"Cleaned data saved to {output_file}")
        
        # Log summary statistics
        logger.info(f"Total rows after cleaning: {len(df_cleaned)}")
        logger.info(f"Columns: {list(df_cleaned.columns)}")
        
    except Exception as e:
        logger.error(f"Error during data cleaning: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
