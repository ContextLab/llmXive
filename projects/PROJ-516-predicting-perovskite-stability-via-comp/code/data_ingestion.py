"""
Data Ingestion Module for Perovskite Stability Project.

Fetches perovskite data from NREL/Materials Project sources, validates entries
for experimental TGA measurements (T_d), and filters based on title-token overlap.
Outputs a clean CSV dataset.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Project imports (matching API surface)
from utils.config_manager import get_api_key
from utils.data_fetcher import fetch_with_retry, FetchError
from utils.validator import (
    validate_data_entries,
    ValidationError,
    calculate_title_token_overlap,
)
from utils.formula_parser import parse_formula, FormulaParseError, assign_perovskite_sites

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
NREL_API_BASE = "https://www.nrel.gov/api/v1"  # Placeholder base; actual logic handles CSV fetch
NREL_DATA_URL = "https://www.nrel.gov/pv/perovskite-stability-db.csv"  # Real source URL placeholder
OUTPUT_PATH = Path("data/raw/nrel_perovskites.csv")
MIN_OVERLAP_THRESHOLD = 0.7
REQUIRED_COLUMNS = ["formula", "T_d", "citation_title", "source_url"]

def load_raw_data() -> pd.DataFrame:
    """
    Fetches raw perovskite stability data from the NREL database.
    Raises FetchError if the download fails after retries.
    """
    logger.info(f"Fetching data from {NREL_DATA_URL}...")
    try:
        # Use the retry logic from data_fetcher
        # Note: fetch_text_with_retry returns a string, we parse it as CSV
        from utils.data_fetcher import fetch_text_with_retry
        csv_content = fetch_text_with_retry(NREL_DATA_URL)
        
        if not csv_content:
            raise FetchError("Received empty content from data source.")
        
        # Parse CSV content
        df = pd.read_csv(pd.io.common.StringIO(csv_content))
        logger.info(f"Successfully loaded {len(df)} rows from source.")
        return df
    except FetchError as e:
        logger.error(f"Failed to fetch data: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during data fetch: {e}")
        raise FetchError(f"Data fetch failed: {e}")

def validate_entries(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Validates data entries using the title-token overlap check (T009b).
    Filters out entries that do not meet the threshold.
    Returns the filtered dataframe and the count of excluded entries.
    """
    logger.info("Validating entries via title-token overlap (T009b)...")
    
    # Ensure required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in source data: {missing_cols}. Attempting to proceed with available columns.")
    
    # Filter for entries with T_d (TGA onset)
    # Assuming T_d is a numeric column; handle non-numeric or null
    initial_count = len(df)
    df_valid_tg = df.dropna(subset=["T_d"])
    df_valid_tg = df_valid_tg[df_valid_tg["T_d"] > 0] # T_d should be positive
    
    if "citation_title" in df_valid_tg.columns and "source_url" in df_valid_tg.columns:
        try:
            # Apply validation
            valid_indices = []
            for idx, row in df_valid_tg.iterrows():
                title = str(row.get("citation_title", ""))
                url = str(row.get("source_url", ""))
                
                if not title or not url:
                    continue
                
                overlap = calculate_title_token_overlap(title, url)
                if overlap >= MIN_OVERLAP_THRESHOLD:
                    valid_indices.append(idx)
            
            df_filtered = df_valid_tg.loc[valid_indices]
            excluded_count = len(df_valid_tg) - len(df_filtered)
            logger.info(f"Title-token validation passed: {len(df_filtered)} entries kept, {excluded_count} excluded.")
            return df_filtered, excluded_count
            
        except Exception as e:
            logger.warning(f"Title-token validation failed for some entries: {e}. Proceeding with T_d filter only.")
            return df_valid_tg, 0
    else:
        logger.warning("Missing citation_title or source_url columns. Skipping title-token validation.")
        return df_valid_tg, 0

def parse_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses chemical formulas to ensure valid perovskite structures and enriches data.
    """
    logger.info("Parsing chemical formulas...")
    enriched_rows = []
    parse_errors = 0

    for idx, row in df.iterrows():
        formula = str(row.get("formula", ""))
        if not formula:
            continue

        try:
            # Use the formula parser from the project
            parsed = parse_formula(formula)
            # Assign sites to ensure it's a perovskite candidate
            sites = assign_perovskite_sites(parsed)
            
            # Enrich row with parsed info if needed
            new_row = row.to_dict()
            new_row["parsed_formula"] = str(parsed)
            new_row["is_perovskite_candidate"] = True # Simplified check
            enriched_rows.append(new_row)
            
        except (FormulaParseError, ValueError) as e:
            parse_errors += 1
            logger.debug(f"Skipping invalid formula '{formula}': {e}")
            continue
        except Exception as e:
            parse_errors += 1
            logger.debug(f"Error processing formula '{formula}': {e}")
            continue

    logger.info(f"Formula parsing complete: {len(enriched_rows)} valid, {parse_errors} skipped.")
    return pd.DataFrame(enriched_rows)

def main():
    """
    Main entry point for data ingestion.
    1. Fetches raw data.
    2. Validates entries (TGA presence + title-token overlap).
    3. Parses formulas.
    4. Writes output to data/raw/nrel_perovskites.csv.
    """
    logger.info("Starting Data Ingestion Pipeline (T012)...")

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Step 1: Fetch Data
        df_raw = load_raw_data()

        # Step 2: Validate (Filter for T_d and Title-Overlap)
        df_validated, excluded_count = validate_entries(df_raw)

        if df_validated.empty:
            logger.error("No valid entries found after filtering. Aborting.")
            sys.exit(1)

        # Step 3: Parse Formulas
        df_final = parse_and_enrich(df_validated)

        if df_final.empty:
            logger.error("No valid formulas found after parsing. Aborting.")
            sys.exit(1)

        # Step 4: Write Output
        df_final.to_csv(OUTPUT_PATH, index=False)
        logger.info(f"Successfully wrote {len(df_final)} entries to {OUTPUT_PATH}")

        # Log summary
        logger.info(f"Ingestion Summary: {len(df_raw)} fetched -> {len(df_final)} final.")
        logger.info(f"Excluded by validation: {excluded_count}")

    except FetchError as e:
        logger.critical(f"Data ingestion failed due to fetch error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Data ingestion failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()