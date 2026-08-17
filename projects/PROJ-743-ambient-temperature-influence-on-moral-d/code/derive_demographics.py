"""
Derivation of Age/Gender Covariates for Moral Machine Analysis.

This module implements the logic to fetch country-level demographic data from
the World Bank API to serve as covariates (Age/Life Expectancy, Population)
when individual-level data is absent in the Moral Machine dataset.

Per Task T028:
1. Check for individual 'age'/'gender' columns.
2. If absent, fetch aggregate data from World Bank (SP.DYN.LE00.IN, SP.POP.TOTL).
3. Merge to participant-aggregated rows.
4. Log gaps and failures strictly to results/logs/demographic_gap_log.txt.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import pandas as pd
import requests
from config import get_path_env_override
from setup_logging import setup_logging, get_data_quality_logger

# Constants
WORLD_BANK_API_BASE = "https://api.worldbank.org/v2"
INDICATORS = {
    "life_expectancy": "SP.DYN.LE00.IN",  # Life expectancy at birth, total
    "population": "SP.POP.TOTL"           # Population, total
}
YEARS = ["2016", "2017", "2018", "2019"]
LOG_FILE = "results/logs/demographic_gap_log.txt"

# Ensure logging is configured before running
setup_logging()
logger = get_data_quality_logger()

def fetch_world_bank_indicator(indicator_code: str, year: str) -> Optional[pd.DataFrame]:
    """
    Fetches data for a specific World Bank indicator and year.

    Args:
        indicator_code: The World Bank indicator code (e.g., 'SP.DYN.LE00.IN')
        year: The year string (e.g., '2016')

    Returns:
        A DataFrame with columns: ['country_code', 'country_name', 'value']
        or None if the fetch fails.
    """
    url = f"{WORLD_BANK_API_BASE}/indicator/{indicator_code}"
    params = {
        "date": year,
        "format": "json",
        "per_page": 3000  # Ensure we get all countries
    }

    try:
        logger.info(f"Fetching {indicator_code} for {year} from World Bank API...")
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if len(data) < 2:
            logger.warning(f"No data returned for {indicator_code} in {year}.")
            return None

        # World Bank API returns [metadata, [records]]
        records = data[1]
        if not records:
            logger.warning(f"Empty record list for {indicator_code} in {year}.")
            return None

        df = pd.DataFrame(records)
        # Filter for valid numeric values and country codes
        valid_cols = ['iso2Code', 'value', 'country']
        # Some entries might have 'iso2Code' as 'NA' or empty, or value as None
        df = df[df['value'].notna()]
        df = df[df['iso2Code'].notna() & (df['iso2Code'] != 'NA')]

        df = df.rename(columns={
            'iso2Code': 'country_code',
            'country': 'country_name',
            'value': 'value'
        })

        # Ensure value is numeric
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        df = df.dropna(subset=['value'])

        df['year'] = year
        df['indicator'] = indicator_code

        logger.info(f"Successfully fetched {len(df)} records for {indicator_code} ({year}).")
        return df

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch {indicator_code} for {year}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response for {indicator_code}: {e}")
        return None

def fetch_demographic_data() -> pd.DataFrame:
    """
    Fetches all required demographic indicators for the study period (2016-2019).
    Merges them into a single DataFrame indexed by country_code and year.
    """
    all_data = []

    for indicator_name, code in INDICATORS.items():
        for year in YEARS:
            df = fetch_world_bank_indicator(code, year)
            if df is not None:
                # Rename value column to be specific
                df = df.rename(columns={'value': indicator_name})
                all_data.append(df[['country_code', 'country_name', indicator_name, 'year']])

    if not all_data:
        logger.error("Failed to fetch ANY demographic data from World Bank.")
        return pd.DataFrame()

    # Merge all indicators into one wide table per country/year
    base_df = all_data[0]
    for df in all_data[1:]:
        base_df = base_df.merge(df, on=['country_code', 'country_name', 'year'], how='outer')

    # Drop rows where all values are missing (shouldn't happen if we filtered earlier)
    base_df = base_df.dropna(subset=list(INDICATORS.keys()))

    return base_df

def merge_demographics_to_data(merged_data: pd.DataFrame, demographics: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """
    Merges demographic data into the merged dataset.

    Logic:
    1. Check if 'age' or 'gender' columns exist in merged_data.
    2. If they do, return merged_data as is (individual data takes precedence).
    3. If not, attempt to merge on country_code and year.
    4. Log the outcome.

    Args:
        merged_data: The dataset from ingestion (T022).
        demographics: The World Bank data fetched.

    Returns:
        Tuple of (updated_dataframe, success_flag)
    """
    # Check for individual-level columns
    has_individual_age = 'age' in merged_data.columns
    has_individual_gender = 'gender' in merged_data.columns

    if has_individual_age or has_individual_gender:
        logger.info("Individual-level 'age' or 'gender' columns found. Skipping World Bank aggregation.")
        return merged_data, True

    if demographics.empty:
        logger.warning("No demographic data available to merge.")
        log_gap("No World Bank data available for 2016-2019.")
        return merged_data, False

    # Determine merge keys
    # We assume 'country_code' and 'year' (or similar) exist in merged_data from T022.
    # If 'year' is missing in merged_data, we might need to extract it from timestamp.
    # For this task, we assume T022 produced a 'year' column or 'timestamp' that can be derived.
    # If 'year' is not present, we try to infer from 'timestamp' if available.
    
    if 'year' not in merged_data.columns:
        if 'timestamp' in merged_data.columns:
            merged_data['year'] = pd.to_datetime(merged_data['timestamp'], errors='coerce').dt.year
        else:
            # Fallback: assume all data is from the study period or log error
            logger.warning("No 'year' or 'timestamp' column found in merged_data. Cannot merge demographics.")
            log_gap("Missing 'year' or 'timestamp' column in merged_data for demographic merge.")
            return merged_data, False

    # Ensure types match for merge
    demographics['year'] = demographics['year'].astype(int)
    merged_data['year'] = merged_data['year'].astype(int)

    # Merge
    # We use a left join to keep all moral machine data, even if country match fails
    result = merged_data.merge(
        demographics[['country_code', 'year', 'life_expectancy', 'population']],
        on=['country_code', 'year'],
        how='left'
    )

    # Check for missing matches
    missing_matches = result['life_expectancy'].isna().sum()
    total_rows = len(result)

    if missing_matches > 0:
        pct_missing = (missing_matches / total_rows) * 100
        logger.warning(f"{missing_matches} rows ({pct_missing:.2f}%) could not be matched to demographic data.")
        log_gap(f"{missing_matches} rows unmatched due to missing country/year in World Bank data.")
    else:
        logger.info("All rows successfully matched to demographic data.")

    return result, True

def log_gap(reason: str):
    """
    Logs a specific gap or failure to the demographic gap log file.
    """
    log_path = get_path_env_override(LOG_FILE, Path(LOG_FILE))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = pd.Timestamp.now().isoformat()
    log_entry = f"[{timestamp}] GAP: {reason}\n"
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)

def main():
    """
    Main entry point for T028.
    1. Loads the merged dataset from data/processed/merged_dataset.parquet.
    2. Checks for individual age/gender.
    3. Fetches World Bank data if needed.
    4. Merges and saves the result.
    """
    logger.info("Starting Task T028: Derivation of Age/Gender Covariates")

    input_path = get_path_env_override("data/processed/merged_dataset.parquet", Path("data/processed/merged_dataset.parquet"))
    output_path = get_path_env_override("data/processed/merged_dataset_with_demographics.parquet", Path("data/processed/merged_dataset_with_demographics.parquet"))

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info(f"Loading merged dataset from {input_path}")
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        sys.exit(1)

    # Step 1: Check for individual columns
    has_individual = 'age' in df.columns or 'gender' in df.columns
    if has_individual:
        logger.info("Individual demographics present. Saving original dataset as final.")
        df.to_parquet(output_path, index=False)
        logger.info(f"Saved output to {output_path}")
        return

    # Step 2: Fetch World Bank Data
    logger.info("Individual demographics absent. Fetching World Bank aggregate data...")
    demographics = fetch_demographic_data()

    if demographics.empty:
        logger.error("FATAL: Could not fetch any demographic data. Aborting.")
        sys.exit(1)

    # Step 3: Merge
    logger.info("Merging demographic data into main dataset...")
    final_df, success = merge_demographics_to_data(df, demographics)

    if not success:
        logger.warning("Merge completed with gaps. See demographic_gap_log.txt for details.")

    # Step 4: Save
    logger.info(f"Saving final dataset to {output_path}")
    final_df.to_parquet(output_path, index=False)

    logger.info("Task T028 completed.")

if __name__ == "__main__":
    main()
