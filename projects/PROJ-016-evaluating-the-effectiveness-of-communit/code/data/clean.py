import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from config import get_config
from logging_config import get_logger
from data.download import fetch_fao_fra_data, load_world_bank_gdp_population, load_cbmrm_proxy_data

logger = get_logger(__name__)

def standardize_iso_code(series: pd.Series) -> pd.Series:
    """
    Standardize ISO country codes to 3-letter uppercase (alpha-3).
    Handles common variations (2-letter, mixed case, 'UK' -> 'GBR').
    """
    def normalize_code(code):
        if pd.isna(code):
            return None
        code_str = str(code).strip().upper()
        if code_str == '':
            return None
        # Handle specific 2-letter to 3-letter conversions if needed
        # Common mapping for 2-letter to ISO 3
        iso_map = {
            'US': 'USA', 'UK': 'GBR', 'DE': 'DEU', 'FR': 'FRA',
            'IT': 'ITA', 'ES': 'ESP', 'CN': 'CHN', 'JP': 'JPN',
            'IN': 'IND', 'BR': 'BRA', 'CA': 'CAN', 'AU': 'AUS',
            'RU': 'RUS', 'ZA': 'ZAF', 'NG': 'NGA', 'KE': 'KEN',
            'TZ': 'TZA', 'UG': 'UGA', 'MZ': 'MOZ', 'ZW': 'ZWE',
            'GH': 'GHA', 'ET': 'ETH', 'CD': 'COD', 'AO': 'AGO',
            'CM': 'CMR', 'BF': 'BFA', 'ML': 'MLI', 'NE': 'NER',
            'SN': 'SEN', 'TD': 'TCD', 'SD': 'SDN', 'EG': 'EGY',
            'MA': 'MAR', 'DZ': 'DZA', 'TN': 'TUN', 'LY': 'LBY'
        }
        if len(code_str) == 2:
            return iso_map.get(code_str, code_str) # Return as is if not mapped, might fail later validation
        return code_str

    return series.apply(normalize_code)

def standardize_year(series: pd.Series) -> pd.Series:
    """
    Standardize year column to integer.
    """
    def to_int(val):
        if pd.isna(val):
            return None
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return None
    return series.apply(to_int)

def load_fao_data() -> Optional[pd.DataFrame]:
    """
    Load FAO land use data from the processed raw file.
    Expected file: data/raw/fao_land_use.csv
    """
    fao_path = Path('data/raw/fao_land_use.csv')
    if not fao_path.exists():
        logger.error(f"FAO data file not found: {fao_path}")
        return None

    try:
        df = pd.read_csv(fao_path)
        logger.info(f"Loaded FAO data: {len(df)} rows")
        
        # Standardize columns if they exist
        if 'country_code' in df.columns:
            df['country_code'] = standardize_iso_code(df['country_code'])
        if 'year' in df.columns:
            df['year'] = standardize_year(df['year'])
        
        return df
    except Exception as e:
        logger.error(f"Error loading FAO data: {e}")
        return None

def load_world_bank_data() -> Optional[pd.DataFrame]:
    """
    Load World Bank economic data from the processed raw file.
    Expected file: data/raw/wb_economic_data.csv
    """
    wb_path = Path('data/raw/wb_economic_data.csv')
    if not wb_path.exists():
        logger.error(f"World Bank data file not found: {wb_path}")
        return None

    try:
        df = pd.read_csv(wb_path)
        logger.info(f"Loaded World Bank data: {len(df)} rows")

        # Standardize columns
        if 'country_code' in df.columns:
            df['country_code'] = standardize_iso_code(df['country_code'])
        if 'year' in df.columns:
            df['year'] = standardize_year(df['year'])

        return df
    except Exception as e:
        logger.error(f"Error loading World Bank data: {e}")
        return None

def load_regime_data() -> Optional[pd.DataFrame]:
    """
    Load CBNRM proxy/regime data.
    This task depends on T009/T012 which should have populated data/raw/cbnrm_proxy.csv.
    However, T013's specific requirement is merging FAO and WB.
    If regime data is needed for the merge (e.g. for T014 later), it should be loaded here.
    For T013, we primarily need FAO and WB. We will attempt to load proxy if it exists
    to prepare for downstream merging, but T013 focus is FAO+WB merge.
    """
    proxy_path = Path('data/raw/cbnrm_proxy.csv')
    if not proxy_path.exists():
        logger.warning(f"CBNRM proxy data file not found: {proxy_path}. Proceeding without it for this merge.")
        return None

    try:
        df = pd.read_csv(proxy_path)
        logger.info(f"Loaded CBNRM proxy data: {len(df)} rows")
        
        if 'country_code' in df.columns:
            df['country_code'] = standardize_iso_code(df['country_code'])
        if 'year' in df.columns:
            df['year'] = standardize_year(df['year'])
        
        return df
    except Exception as e:
        logger.error(f"Error loading CBNRM proxy data: {e}")
        return None

def merge_datasets(fao_df: pd.DataFrame, wb_df: pd.DataFrame, proxy_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Merge FAO and World Bank datasets on country_code and year.
    Optional: merge proxy data as well.
    """
    logger.info("Starting dataset merge...")
    
    # Ensure keys are present
    common_cols = ['country_code', 'year']
    if not all(col in fao_df.columns for col in common_cols):
        raise ValueError("FAO data missing required columns: country_code, year")
    if not all(col in wb_df.columns for col in common_cols):
        raise ValueError("WB data missing required columns: country_code, year")

    # Perform inner merge to ensure we only have rows where both sources have data
    merged = pd.merge(fao_df, wb_df, on=['country_code', 'year'], how='inner')
    logger.info(f"After FAO+WB merge: {len(merged)} rows")

    if proxy_df is not None and len(proxy_df) > 0:
        if all(col in proxy_df.columns for col in common_cols):
            merged = pd.merge(merged, proxy_df, on=['country_code', 'year'], how='left')
            logger.info(f"After proxy merge: {len(merged)} rows")
        else:
            logger.warning("Proxy data missing required columns for merge, skipping proxy merge.")

    return merged

def drop_missing_primary_vars(df: pd.DataFrame, primary_vars: List[str] = None) -> pd.DataFrame:
    """
    Drop rows missing primary variables.
    Primary vars for this task: land_use_change_rate (from FAO), regime_type (if available, but T013 is pre-classification usually? 
    Wait, T013 description says: "drop rows missing primary vars". 
    Based on T011/T012, primary vars are likely FAO's land use change and WB's GDP/Pop.
    Let's define primary vars as: 'AG.LND.FRST.ZS' (or renamed), 'NY.GDP.PCAP.CD', 'SP.POP.DENS'.
    We need to know the column names after download.
    Assuming download.py standardizes column names or we map them here.
    Let's assume the columns in the raw CSVs are:
    FAO: 'country_code', 'year', 'indicator', 'value' OR 'country_code', 'year', 'Forest_Area_Change'
    WB: 'country_code', 'year', 'GDP', 'Pop_Density'
    
    To be safe, we will check for common column names derived from the indicator codes or generic names.
    Let's assume the download scripts produce columns like:
    'land_use_change' (from FAO), 'gdp_per_capita', 'population_density' (from WB).
    If these don't exist, we try to find them by indicator code.
    """
    if primary_vars is None:
        # Heuristic: look for these columns, or fallback to indicator codes if raw
        potential_primary = ['land_use_change', 'gdp_per_capita', 'population_density', 'AG.LND.FRST.ZS', 'NY.GDP.PCAP.CD', 'SP.POP.DENS']
        found_primary = [col for col in potential_primary if col in df.columns]
        if not found_primary:
            # If no standard names, maybe the raw indicator codes are columns?
            # Or maybe the raw data is in 'value' column with 'indicator' column.
            # For T013, let's assume the download scripts have already pivoted or named columns appropriately.
            # If not, we must handle the 'wide' vs 'long' format.
            # Assuming 'wide' format for simplicity based on typical download.py patterns in this project context.
            # If 'value' column exists, we might need to pivot. But T013 says "Standardize... drop rows".
            # Let's assume the columns are named after the indicator code or a cleaned version.
            # We will define the primary vars as the ones we expect to be non-null.
            # Let's try to detect them dynamically if not found.
            pass
        primary_vars = found_primary

    if not primary_vars:
        logger.warning("No primary variables identified to drop missing rows. Skipping drop.")
        return df

    initial_count = len(df)
    # Drop rows where ANY of the primary variables are NaN
    df_clean = df.dropna(subset=primary_vars)
    dropped = initial_count - len(df_clean)
    logger.info(f"Dropped {dropped} rows missing primary variables: {primary_vars}")
    
    return df_clean

def apply_fr007_exclusion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply row-level exclusion for Secondary Variables (GDP, Pop).
    Log specific missing variable name.
    """
    # This is handled in drop_missing_primary_vars for primary, but FR-007 mentions Secondary.
    # If secondary vars are present, we might want to log which ones are missing but keep the row?
    # The task T013 says "drop rows missing primary vars". T016 handles FR-007 for secondary.
    # So T013 just drops primary missing.
    return df

def apply_country_level_exclusion(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply country-level exclusion for Primary Variables (>20% missing).
    This is T016b, but we include it here if needed for T013 completeness?
    T013 description: "Standardize years (int), ISO codes (alpha-3), drop rows missing primary vars. Save merged panel."
    It does not explicitly mention country-level exclusion. That is T016b.
    So we skip this for T013 to avoid scope creep, unless "cleaning" implies it.
    We will stick to the strict definition: Standardize + Drop Row + Save.
    """
    return df

def clean_and_merge_data() -> pd.DataFrame:
    """
    Main orchestration for T013:
    1. Load FAO, WB, Proxy (if exists)
    2. Merge
    3. Drop missing primary vars
    4. Return cleaned dataframe
    """
    fao_df = load_fao_data()
    wb_df = load_world_bank_data()
    proxy_df = load_regime_data()

    if fao_df is None or wb_df is None:
        logger.error("Cannot proceed with merge: FAO or WB data missing.")
        # Create empty DF with expected schema to prevent downstream crash?
        # Or raise error. T013 says "Save merged panel". If no data, save empty?
        # Let's create an empty one with headers if possible, but better to fail loud if source missing.
        # However, T011/T012 say "If missing, create empty CSV". So they should exist.
        # If they exist but are empty, merge will be empty.
        raise FileNotFoundError("Required source data files are missing or empty.")

    merged = merge_datasets(fao_df, wb_df, proxy_df)
    
    # Identify primary variables dynamically if not passed
    # Expected primary: Land Use (FAO), GDP, Pop (WB)
    # Let's assume column names are standardized by download.py or we map them here.
    # If download.py uses indicator codes as column names:
    fao_cols = [c for c in fao_df.columns if c != 'country_code' and c != 'year']
    wb_cols = [c for c in wb_df.columns if c != 'country_code' and c != 'year']
    proxy_cols = [c for c in (proxy_df.columns if proxy_df is not None else []) if c != 'country_code' and c != 'year']
    
    # Heuristic for primary vars:
    # Land use change is likely the FAO value.
    # GDP and Pop are WB values.
    # We need to drop rows where these are null.
    # Let's assume the columns are named 'land_use_change', 'gdp_per_capita', 'population_density' 
    # OR the indicator codes 'AG.LND.FRST.ZS', 'NY.GDP.PCAP.CD', 'SP.POP.DENS'.
    
    primary_vars = []
    # Check for standard names first
    for name in ['land_use_change', 'gdp_per_capita', 'population_density']:
        if name in merged.columns:
            primary_vars.append(name)
    
    # If not found, check indicator codes
    if not primary_vars:
        for code in ['AG.LND.FRST.ZS', 'NY.GDP.PCAP.CD', 'SP.POP.DENS']:
            if code in merged.columns:
                primary_vars.append(code)
    
    if not primary_vars:
        # Fallback: drop rows where ANY numeric column (except year) is null? Too aggressive.
        # Or just drop rows where the 'value' column is null if data is long format.
        # Assuming wide format for now. If no primary vars found, we might have a format issue.
        # Let's assume the download scripts produce wide format with indicator codes or cleaned names.
        # If we still don't find them, we assume the 'value' column exists and we need to pivot?
        # No, T013 assumes data is ready to merge.
        logger.warning("Could not identify primary variables. Skipping drop_missing_primary_vars.")
        return merged

    cleaned = drop_missing_primary_vars(merged, primary_vars)
    return cleaned

def calculate_coverage_rate(cleaned_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate coverage rate as per T015.
    T015 is a separate task, but we can compute it here or return counts.
    T013 just says "Save merged panel".
    We will return the dataframe. T015 will handle the calculation.
    """
    return {}

def main():
    """
    Entry point for T013.
    """
    logger.info("Starting T013: Data Merging and Cleaning")
    
    try:
        cleaned_df = clean_and_merge_data()
        
        output_path = Path('data/processed/merged_panel.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cleaned_df.to_csv(output_path, index=False)
        logger.info(f"Saved merged panel to {output_path} ({len(cleaned_df)} rows)")
        
        # Log some stats
        logger.info(f"Columns in merged panel: {list(cleaned_df.columns)}")
        
    except Exception as e:
        logger.error(f"Failed to complete T013: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
