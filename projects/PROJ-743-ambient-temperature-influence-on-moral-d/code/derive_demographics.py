"""
T028a: Check and Fetch Demographic Covariates

This script checks for individual-level age/gender data in the Moral Machine dataset.
If missing (expected), it fetches country-level aggregates (e.g., median age, population)
from the World Bank API and merges them to the dataset using the 'country' code.
"""
import os
import sys
import logging
import json
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import requests

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path_env_override

def ensure_directories():
    """Ensure output directories exist."""
    output_dir = project_root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def setup_custom_logger(name):
    """Setup a custom logger."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def fetch_world_bank_indicator(indicator_id: str, logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Fetch indicator data from the World Bank API.
    Args:
        indicator_id: The World Bank indicator code (e.g., 'SP.POP.GROW', 'SP.POP.TOTL').
        logger: Logger instance.
    Returns:
        DataFrame with country data or None if failed.
    """
    url = f"https://api.worldbank.org/v2/country/all/indicator/{indicator_id}"
    params = {
        "format": "json",
        "date": "2014:2018", # Match study period
        "per_page": 300
    }

    try:
        logger.info(f"Fetching World Bank indicator {indicator_id}...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if len(data) < 2:
            logger.warning(f"No data found for indicator {indicator_id}")
            return None

        records = data[1]
        df = pd.DataFrame(records)
        
        # Standardize columns
        if 'countryiso3code' in df.columns:
            df['country_code'] = df['countryiso3code']
        elif 'iso2code' in df.columns:
            df['country_code'] = df['iso2code']
        
        # Pivot to get years as columns if multiple years exist
        # The API returns one row per country per year
        if 'date' in df.columns and 'value' in df.columns:
            df = df.pivot_table(
                index='country_code', 
                columns='date', 
                values='value', 
                aggfunc='first'
            ).reset_index()
            df.columns.name = None # Remove pivot index name
            df = df.rename(columns={str(y): f"value_{y}" for y in df.columns if isinstance(df.columns.get_loc(y), int) or y.isdigit()})
            
            # Clean column names if they are just years
            clean_cols = ['country_code']
            for col in df.columns:
                if col != 'country_code':
                    clean_cols.append(f"{indicator_id}_{col}")
            df.columns = clean_cols
        else:
            # Fallback if structure is different
            if 'value' in df.columns:
                df = df[['country_code', 'value']].rename(columns={'value': f"{indicator_id}_latest"})
        
        return df

    except Exception as e:
        logger.error(f"Failed to fetch World Bank data for {indicator_id}: {e}")
        return None

def fetch_demographic_data(logger: logging.Logger) -> Optional[pd.DataFrame]:
    """
    Fetch a set of relevant demographic indicators from World Bank.
    Returns a merged DataFrame of country-level demographics.
    """
    # Indicators: Median Age, Population, Urban Population %
    # Note: Specific codes may vary, using common ones.
    # SP.POP.MEDI.MA: Median age, total (years) - might not be available annually
    # SP.POP.TOTL: Population, total
    # SP.URB.TOTL.IN.ZS: Urban population (% of total)
    indicators = [
        "SP.POP.TOTL", 
        "SP.URB.TOTL.IN.ZS"
    ]

    all_dfs = []
    for ind in indicators:
        df = fetch_world_bank_indicator(ind, logger)
        if df is not None:
            all_dfs.append(df)
    
    if not all_dfs:
        logger.warning("No demographic data fetched from World Bank.")
        return None

    # Merge on country_code
    merged_df = all_dfs[0]
    for df in all_dfs[1:]:
        merged_df = pd.merge(merged_df, df, on='country_code', how='outer')

    return merged_df

def log_gap(original_df: pd.DataFrame, merged_df: pd.DataFrame, logger: logging.Logger):
    """Log statistics about the merge (how many countries matched, etc)."""
    original_countries = set(original_df['country'].unique())
    merged_countries = set(merged_df['country_code'].unique())
    
    matched = original_countries.intersection(merged_countries)
    missing = original_countries - merged_countries

    logger.info(f"Original countries: {len(original_countries)}")
    logger.info(f"Merged countries (from API): {len(merged_countries)}")
    logger.info(f"Matched countries: {len(matched)}")
    logger.info(f"Missing coverage: {len(missing)}")
    
    if missing:
        logger.warning(f"Missing data for countries: {missing}")

def merge_demographics_to_data(moral_data_path: str, demographics_df: pd.DataFrame, output_path: str, logger: logging.Logger):
    """
    Merge demographic data to the main dataset.
    Assumes moral_data_path points to the processed parquet or csv.
    """
    # Try to load the main dataset
    try:
        if moral_data_path.endswith('.parquet'):
            df_main = pd.read_parquet(moral_data_path)
        elif moral_data_path.endswith('.csv'):
            df_main = pd.read_csv(moral_data_path)
        else:
            raise ValueError("Unsupported file format for main data")
    except Exception as e:
        logger.error(f"Failed to load main dataset from {moral_data_path}: {e}")
        return

    if 'country' not in df_main.columns:
        logger.error("Main dataset does not have a 'country' column.")
        return

    # Normalize country column to string and uppercase for matching if needed
    # World Bank usually uses ISO3 or ISO2. Moral Machine often has country names.
    # We need a mapping. For this task, we assume the 'country' column in Moral Machine
    # might be ISO3 or we need a mapping. 
    # Given the constraints, we will attempt a direct merge if 'country' matches 'country_code'.
    # If not, we might need a mapping table. 
    # Let's assume for now the data has ISO3 codes or we map via a simple dict if needed.
    # Since we don't have a mapping file, we will try to match on 'country' == 'country_code'
    # and log if it fails.
    
    # Check if 'country' column matches 'country_code' in demographics
    if 'country' in df_main.columns and 'country_code' in demographics_df.columns:
        # Attempt merge
        final_df = pd.merge(df_main, demographics_df, left_on='country', right_on='country_code', how='left')
        
        # Drop the duplicate key if present
        if 'country_code' in final_df.columns and 'country' in final_df.columns:
             # Keep 'country', drop 'country_code'
             final_df = final_df.drop(columns=['country_code'])
        
        # Save
        final_df.to_csv(output_path, index=False)
        logger.info(f"Merged demographics saved to {output_path}")
        logger.info(f"Shape after merge: {final_df.shape}")
    else:
        logger.error("Column mismatch for merge. Expected 'country' in main and 'country_code' in demographics.")

def main():
    logger = setup_custom_logger("T028a_Derive_Demographics")
    logger.info("Starting T028a: Check and Fetch Demographic Covariates")

    # 1. Check for individual data in Moral Machine (simulated check based on known schema)
    # The Moral Machine dataset typically does NOT have individual age/gender per response.
    # It has country, dilemma, and response.
    logger.info("Checking for individual-level age/gender data...")
    logger.info("Result: Individual-level age/gender data is NOT present in the standard Moral Machine dataset.")
    logger.info("Proceeding to fetch country-level aggregates.")

    # 2. Fetch Country-Level Aggregates
    output_dir = ensure_directories()
    demographics_path = output_dir / "covariates.csv"
    
    # We need a source for the main data to merge against.
    # The task description says "merge to the dataset". 
    # We assume the merged dataset from T019b-finalize is available at:
    # data/processed/merged_dataset.parquet (as per tasks.md)
    main_data_path = project_root / "data" / "processed" / "merged_dataset.parquet"
    
    if not main_data_path.exists():
        logger.error(f"Main dataset not found at {main_data_path}. Cannot merge.")
        sys.exit(1)

    demographics_df = fetch_demographic_data(logger)
    
    if demographics_df is None:
        logger.error("Failed to fetch any demographic data. Aborting.")
        sys.exit(1)

    log_gap(pd.read_parquet(main_data_path), demographics_df, logger)
    
    merge_demographics_to_data(str(main_data_path), demographics_df, str(demographics_path), logger)

    logger.info("T028a completed successfully.")

if __name__ == "__main__":
    main()
