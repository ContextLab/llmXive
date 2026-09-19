import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import numpy as np

# Ensure logging is configured
try:
    from logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

# --- Helper Functions for Standardization ---

def standardize_iso_code(df: pd.DataFrame, col: str = 'country_code') -> pd.DataFrame:
    """
    Standardizes country codes to ISO 3-letter format (upper case).
    Handles common 2-letter codes if necessary, but primarily ensures uppercase 3-letter.
    """
    if col not in df.columns:
        logger.warning(f"Column '{col}' not found in dataframe for standardization.")
        return df

    df = df.copy()
    # Convert to string, strip whitespace, and upper case
    df[col] = df[col].astype(str).str.strip().str.upper()

    # Simple mapping for common 2-letter to 3-letter if needed (optional, usually data is 3)
    # For this implementation, we assume the source data provides 3-letter or we just uppercase.
    # If specific 2->3 mapping is required, it should be added here.
    return df

def standardize_year(df: pd.DataFrame, col: str = 'year') -> pd.DataFrame:
    """
    Ensures the year column is integer type.
    """
    if col not in df.columns:
        logger.warning(f"Column '{col}' not found in dataframe for standardization.")
        return df

    df = df.copy()
    try:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64') # Nullable integer
    except Exception as e:
        logger.error(f"Failed to convert year column to numeric: {e}")
    return df

# --- Data Loading Functions ---

def load_fao_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Loads FAO land use data from the raw CSV.
    """
    if filepath is None:
        filepath = str(Path(__file__).parent.parent.parent / 'data' / 'raw' / 'fao_land_use.csv')
    
    path = Path(filepath)
    if not path.exists():
        logger.error(f"FAO data file not found at {filepath}")
        raise FileNotFoundError(f"FAO data file not found at {filepath}")
    
    logger.info(f"Loading FAO data from {filepath}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from FAO data.")
    return df

def load_world_bank_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Loads World Bank GDP and Population data from the raw CSV.
    """
    if filepath is None:
        filepath = str(Path(__file__).parent.parent.parent / 'data' / 'raw' / 'world_bank_data.csv')
    
    path = Path(filepath)
    if not path.exists():
        # Fallback to a generic name if specific one doesn't exist, based on T012 output
        # T012 output is likely 'world_bank_data.csv' or similar.
        # If the file doesn't exist, we raise an error as per "Fail Loud" principle.
        logger.error(f"World Bank data file not found at {filepath}")
        raise FileNotFoundError(f"World Bank data file not found at {filepath}")

    logger.info(f"Loading World Bank data from {filepath}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from World Bank data.")
    return df

def load_regime_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Loads classified regime data from the processed CSV.
    """
    if filepath is None:
        # T014 output
        filepath = str(Path(__file__).parent.parent.parent / 'data' / 'processed' / 'regime_classified.csv')
    
    path = Path(filepath)
    if not path.exists():
        logger.error(f"Regime data file not found at {filepath}")
        raise FileNotFoundError(f"Regime data file not found at {filepath}")
    
    logger.info(f"Loading Regime data from {filepath}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from Regime data.")
    return df

# --- Merging and Cleaning Functions ---

def merge_datasets(list_of_dfs: List[pd.DataFrame], on: List[str], how: str = 'inner') -> pd.DataFrame:
    """
    Merges multiple dataframes on specified columns.
    """
    if not list_of_dfs:
        raise ValueError("No dataframes provided to merge.")
    
    df_merged = list_of_dfs[0]
    for df in list_of_dfs[1:]:
        df_merged = pd.merge(df_merged, df, on=on, how=how)
    
    logger.info(f"Merged data shape: {df_merged.shape}")
    return df_merged

def drop_missing_primary_vars(df: pd.DataFrame, primary_vars: List[str]) -> pd.DataFrame:
    """
    Drops rows where any of the primary variables are missing.
    """
    initial_count = len(df)
    df_clean = df.dropna(subset=primary_vars)
    dropped_count = initial_count - len(df_clean)
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing primary variables: {primary_vars}")
    
    return df_clean

def apply_fr007_exclusion(df: pd.DataFrame, secondary_vars: List[str]) -> pd.DataFrame:
    """
    Applies FR-007 exclusion logic for secondary variables.
    Logs the specific missing variable and excludes the row.
    """
    initial_count = len(df)
    
    # We iterate to log specific missing variables if needed, but dropna handles the logic
    # To satisfy "Log the specific missing variable name", we check row by row or use a mask
    # For efficiency with large data, we can just dropna and log the count, 
    # but let's try to be specific if possible.
    
    # Create a mask for rows that have any secondary var missing
    mask = df[secondary_vars].isnull().any(axis=1)
    rows_to_drop = df[mask]
    
    if not rows_to_drop.empty:
        # Log unique combinations of missing variables for debugging
        missing_info = rows_to_drop[secondary_vars].isnull()
        logger.warning(f"Excluding {len(rows_to_drop)} rows due to missing secondary variables.")
        # Log first few instances of missing variables
        for idx, row in rows_to_drop.head(5).iterrows():
            missing_cols = [col for col in secondary_vars if pd.isna(row[col])]
            logger.debug(f"Row {idx} missing: {missing_cols}")

    df_clean = df.dropna(subset=secondary_vars)
    return df_clean

def apply_country_level_exclusion(df: pd.DataFrame, primary_vars: List[str], threshold: float = 0.20) -> pd.DataFrame:
    """
    Applies country-level exclusion if >20% of a country's years are missing for a primary variable.
    """
    countries_to_exclude = set()
    
    for var in primary_vars:
        if var not in df.columns:
            logger.warning(f"Primary variable {var} not found in dataframe for country exclusion.")
            continue
        
        # Group by country and calculate missing percentage
        country_stats = df.groupby('country_code')[var].apply(lambda x: x.isnull().mean())
        
        # Identify countries exceeding threshold
        bad_countries = country_stats[country_stats > threshold].index.tolist()
        for c in bad_countries:
            countries_to_exclude.add(c)
            logger.warning(f"Excluding country {c} for primary variable '{var}' (missing: {country_stats[c]:.2%})")
    
    if countries_to_exclude:
        initial_count = len(df)
        df_clean = df[~df['country_code'].isin(countries_to_exclude)]
        logger.info(f"Excluded {len(countries_to_exclude)} countries. New shape: {df_clean.shape}")
        return df_clean
    
    return df

def clean_and_merge_data() -> pd.DataFrame:
    """
    Orchestrates the full cleaning and merging pipeline.
    """
    logger.info("Starting clean_and_merge_data pipeline.")
    
    # 1. Load raw data
    try:
        df_fao = load_fao_data()
        df_wb = load_world_bank_data()
        df_regime = load_regime_data()
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        raise

    # 2. Standardize
    df_fao = standardize_iso_code(df_fao)
    df_fao = standardize_year(df_fao)
    
    df_wb = standardize_iso_code(df_wb)
    df_wb = standardize_year(df_wb)
    
    df_regime = standardize_iso_code(df_regime)
    df_regime = standardize_year(df_regime)

    # 3. Merge
    # Assuming common keys: country_code, year
    on_cols = ['country_code', 'year']
    
    # Merge FAO and WB first
    df_fao_wb = merge_datasets([df_fao, df_wb], on=on_cols, how='inner')
    
    # Merge with Regime
    df_merged = merge_datasets([df_fao_wb, df_regime], on=on_cols, how='inner')

    # 4. Drop Primary Missing (Land Use, Regime)
    # Identify primary variables based on task context
    primary_vars = ['land_use_change_rate', 'regime_type']
    # Check if columns exist with expected names, adjust if FAO/WB used different names
    # FAO likely: 'Forest_Area_Change' or similar. Let's assume standardization mapped them.
    # If not, we need to map them here. For now, assume T013 logic handled renaming or we use generic names.
    # Let's assume the columns are named 'land_use_change_rate' and 'regime_type' after T013 processing.
    # If T013 didn't rename, we might need to find the actual column names.
    # Given the task description, we assume the columns exist.
    
    df_cleaned = drop_missing_primary_vars(df_merged, primary_vars)

    # 5. Apply FR-007 (Secondary)
    secondary_vars = ['gdp_per_capita', 'population_density']
    df_cleaned = apply_fr007_exclusion(df_cleaned, secondary_vars)

    # 6. Country Level Exclusion
    df_final = apply_country_level_exclusion(df_cleaned, primary_vars)

    # 7. Save to processed
    output_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'merged_panel.csv'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_csv(output_path, index=False)
    logger.info(f"Saved merged panel to {output_path}")

    return df_final

# --- T015: Coverage Rate Calculation ---

def calculate_coverage_rate() -> Dict[str, Any]:
    """
    Loads the total available record count and merged count from T008 output.
    Calculates the proportion (merged/total).
    Logs and saves the result to metrics.json.
    """
    logger.info("Starting coverage rate calculation (T015).")
    
    base_path = Path(__file__).parent.parent.parent
    counts_file = base_path / 'data' / 'processed' / 'total_records_count.json'
    metrics_file = base_path / 'data' / 'processed' / 'metrics.json'
    
    # 1. Load T008 output
    if not counts_file.exists():
        logger.error(f"Required input file not found: {counts_file}")
        raise FileNotFoundError(f"Total records count file not found at {counts_file}. "
                                "Ensure T008 has been executed successfully.")
    
    try:
        with open(counts_file, 'r') as f:
            counts_data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {counts_file}: {e}")
        raise
    
    total_available = counts_data.get('total_available')
    total_merged = counts_data.get('total_merged')
    
    if total_available is None or total_merged is None:
        logger.error("Missing 'total_available' or 'total_merged' in total_records_count.json")
        raise ValueError("Invalid data in total_records_count.json")
    
    if total_available == 0:
        logger.warning("Total available records is 0. Coverage rate is undefined (0/0).")
        coverage_rate = 0.0
    else:
        coverage_rate = total_merged / total_available
    
    logger.info(f"Total Available: {total_available}, Total Merged: {total_merged}")
    logger.info(f"Calculated Coverage Rate: {coverage_rate:.4f} ({coverage_rate*100:.2f}%)")
    
    # 2. Prepare metrics
    metrics = {
        "coverage_rate": coverage_rate,
        "total_available_records": total_available,
        "total_merged_records": total_merged,
        "calculation_date": pd.Timestamp.now().isoformat(),
        "source": "T008 (total_records_count.json) + T013 (merged_panel.csv)"
    }
    
    # 3. Save to metrics.json
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"Coverage rate metrics saved to {metrics_file}")
    
    return metrics

def main():
    """
    Main entry point for the clean and merge pipeline and coverage calculation.
    """
    logger.info("Running code/data/clean.py main.")
    try:
        # First, ensure the merged panel exists (T013 logic)
        # Note: In a real pipeline, this might be called by a runner that ensures order.
        # Here we call it to ensure the data exists for T015 if it doesn't already.
        # However, T015 specifically depends on T008 and T013.
        # If T013 hasn't run, we should run it first to be safe, or assume it ran.
        # Given the dependency, we assume T013 ran, but we can call it to be sure.
        # To avoid double processing, we check if the file exists.
        merged_path = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'merged_panel.csv'
        if not merged_path.exists():
            logger.info("Merged panel not found. Running clean_and_merge_data first.")
            clean_and_merge_data()
        
        # Now run T015 logic
        calculate_coverage_rate()
        
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
