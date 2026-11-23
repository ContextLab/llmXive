import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

# Ensure imports from sibling modules match the API surface
# The API surface lists: standardize_iso_code, standardize_year, load_fao_data, load_world_bank_data,
# load_regime_data, merge_datasets, drop_missing_primary_vars, calculate_coverage_rate,
# clean_and_merge_data, apply_fr007_exclusion, apply_country_level_exclusion, main

# We need to import logging_config if it's used, but the API surface for clean.py
# doesn't explicitly list it. We'll use standard logging setup as per existing patterns.
import logging

# Configure logging similar to other modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/run.log')
    ]
)
logger = logging.getLogger(__name__)

def standardize_iso_code(df: pd.DataFrame, col: str = 'iso_code') -> pd.DataFrame:
    """Standardize ISO codes to 3-letter format."""
    if col not in df.columns:
        return df
    df[col] = df[col].str.upper().str[:3]
    return df

def standardize_year(df: pd.DataFrame, col: str = 'year') -> pd.DataFrame:
    """Standardize year to integer."""
    if col not in df.columns:
        return df
    df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
    return df

def load_fao_data(filepath: Path) -> pd.DataFrame:
    """Load FAO land use data."""
    if not filepath.exists():
        logger.error(f"FAO data file not found: {filepath}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded FAO data: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load FAO data: {e}")
        return pd.DataFrame()

def load_world_bank_data(filepath: Path) -> pd.DataFrame:
    """Load World Bank economic data."""
    if not filepath.exists():
        logger.warning(f"World Bank data file not found: {filepath}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded World Bank data: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load World Bank data: {e}")
        return pd.DataFrame()

def load_regime_data(filepath: Path) -> pd.DataFrame:
    """Load regime classification data."""
    if not filepath.exists():
        logger.warning(f"Regime data file not found: {filepath}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded regime data: {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Failed to load regime data: {e}")
        return pd.DataFrame()

def merge_datasets(fao_df: pd.DataFrame, wb_df: pd.DataFrame, regime_df: pd.DataFrame) -> pd.DataFrame:
    """Merge FAO, World Bank, and regime data."""
    if fao_df.empty or wb_df.empty:
        logger.error("Cannot proceed with merge: FAO or WB data missing.")
        return pd.DataFrame()
    
    # Standardize columns
    fao_df = standardize_iso_code(fao_df)
    wb_df = standardize_iso_code(wb_df)
    
    # Merge on iso_code and year
    merged = fao_df.merge(wb_df, on=['iso_code', 'year'], how='inner')
    
    if not regime_df.empty:
        regime_df = standardize_iso_code(regime_df)
        merged = merged.merge(regime_df, on=['iso_code', 'year'], how='left')
    
    logger.info(f"Merged dataset: {len(merged)} rows")
    return merged

def drop_missing_primary_vars(df: pd.DataFrame, primary_vars: List[str] = None) -> pd.DataFrame:
    """Drop rows missing primary variables (land_use_change_rate, regime_type)."""
    if primary_vars is None:
        primary_vars = ['land_use_change_rate', 'regime_type']
    
    # Filter rows where any primary variable is null
    before = len(df)
    df = df.dropna(subset=primary_vars)
    after = len(df)
    
    if before > after:
        logger.info(f"Dropped {before - after} rows missing primary variables")
    
    return df

def calculate_coverage_rate(total_merged: int, total_fao_available: int, total_wb_available: int) -> float:
    """Calculate coverage rate as intersection of available records."""
    min_available = min(total_fao_available, total_wb_available)
    if min_available == 0:
        return 0.0
    return total_merged / min_available

def apply_fr007_exclusion(df: pd.DataFrame, secondary_vars: List[str] = None) -> pd.DataFrame:
    """
    Apply row-level exclusion (FR-007) for Secondary Variables (GDP, Pop).
    Log the specific missing variable name, exclude the row, continue.
    """
    if secondary_vars is None:
        secondary_vars = ['gdp_per_capita', 'population_density']
    
    # Filter for rows where any secondary variable is null
    mask = df[secondary_vars].notna().all(axis=1)
    
    # Identify rows to exclude and log them
    excluded_mask = ~mask
    if excluded_mask.any():
        excluded_rows = df[excluded_mask]
        for idx, row in excluded_rows.iterrows():
            missing_vars = [var for var in secondary_vars if pd.isna(row.get(var))]
            if missing_vars:
                logger.warning(f"Row {idx} excluded due to missing secondary variables: {missing_vars}")
        
        df = df[mask]
        logger.info(f"FR-007: Excluded {excluded_mask.sum()} rows with missing secondary variables")
    
    return df

def apply_country_level_exclusion(df: pd.DataFrame, primary_vars: List[str] = None, threshold: float = 0.2) -> pd.DataFrame:
    """
    Apply country-level exclusion for Primary Variables.
    If >20% of a country's years are missing for a primary variable, exclude the entire country.
    """
    if primary_vars is None:
        primary_vars = ['land_use_change_rate', 'regime_type']
    
    if df.empty:
        return df, []
    
    excluded_countries = []
    
    for var in primary_vars:
        if var not in df.columns:
            continue
        
        # Group by country and calculate missing percentage
        country_stats = df.groupby('iso_code').agg(
            total_count=(var, 'count'),
            missing_count=(var, lambda x: x.isna().sum())
        ).reset_index()
        
        country_stats['missing_pct'] = country_stats['missing_count'] / country_stats['total_count']
        
        # Identify countries exceeding threshold
        bad_countries = country_stats[country_stats['missing_pct'] > threshold]['iso_code'].tolist()
        
        if bad_countries:
            excluded_countries.extend(bad_countries)
            logger.warning(f"Primary Variable Missing ({var}): Excluding countries with >{threshold*100}% missing: {bad_countries}")
    
    # Remove duplicates
    excluded_countries = list(set(excluded_countries))
    
    if excluded_countries:
        df = df[~df['iso_code'].isin(excluded_countries)]
        logger.info(f"Country-level exclusion: Removed {len(excluded_countries)} countries")
    
    return df, excluded_countries

def clean_and_merge_data(fao_path: Path, wb_path: Path, regime_path: Optional[Path] = None) -> pd.DataFrame:
    """Main function to clean and merge all datasets."""
    fao_df = load_fao_data(fao_path)
    wb_df = load_world_bank_data(wb_path)
    
    if fao_df.empty or wb_df.empty:
        logger.error("Cannot proceed: Required source data files are missing or empty.")
        return pd.DataFrame()
    
    regime_df = pd.DataFrame()
    if regime_path and regime_path.exists():
        regime_df = load_regime_data(regime_path)
    
    # Merge datasets
    merged = merge_datasets(fao_df, wb_df, regime_df)
    
    if merged.empty:
        logger.error("Merge resulted in empty dataset.")
        return pd.DataFrame()
    
    # Apply FR-007 row-level exclusion for secondary variables
    merged = apply_fr007_exclusion(merged)
    
    # Apply country-level exclusion for primary variables
    merged, excluded_countries = apply_country_level_exclusion(merged)
    
    # Drop rows missing primary variables
    merged = drop_missing_primary_vars(merged)
    
    # Standardize types
    merged = standardize_iso_code(merged)
    merged = standardize_year(merged)
    
    return merged

def main():
    """Main entry point for T013/T016 data cleaning and merging."""
    logger.info("Starting T013/T016: Data Merging, Cleaning, and Row-Level Exclusion")
    
    # Define paths
    fao_path = Path('data/raw/fao_land_use.csv')
    wb_path = Path('data/raw/wb_economic_data.csv')
    regime_path = Path('data/processed/classified_panel.csv')  # T014 output
    output_path = Path('data/processed/merged_panel.csv')
    excluded_countries_path = Path('data/processed/excluded_countries_primary.json')
    
    # Perform cleaning and merging
    df = clean_and_merge_data(fao_path, wb_path, regime_path)
    
    if df.empty:
        logger.error("Failed to produce merged dataset.")
        sys.exit(1)
    
    # Save merged panel
    df.to_csv(output_path, index=False)
    logger.info(f"Saved merged panel to {output_path}: {len(df)} rows")
    
    # Save excluded countries (from country-level exclusion)
    # We need to re-run the exclusion logic to get the list, or store it during processing
    # For now, we'll re-calculate it
    _, excluded_countries = apply_country_level_exclusion(df)
    
    with open(excluded_countries_path, 'w') as f:
        json.dump({"excluded_countries": excluded_countries}, f, indent=2)
    logger.info(f"Saved excluded countries to {excluded_countries_path}")
    
    # Calculate and save metrics (T015)
    # Load raw counts
    fao_raw = load_fao_data(fao_path)
    wb_raw = load_world_bank_data(wb_path)
    
    total_fao = len(fao_raw)
    total_wb = len(wb_raw)
    total_merged = len(df)
    
    coverage_rate = calculate_coverage_rate(total_merged, total_fao, total_wb)
    
    metrics = {
        "total_fao_available": total_fao,
        "total_wb_available": total_wb,
        "total_merged": total_merged,
        "coverage_rate": coverage_rate
    }
    
    metrics_path = Path('data/processed/metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")
    
    logger.info("T013/T016 completed successfully")

if __name__ == "__main__":
    main()
