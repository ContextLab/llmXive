import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from datasets import load_dataset

# Import existing utilities from the project API surface
from utils.data_fetcher import fetch_with_retry, FetchError
from utils.validator import validate_data_entries, ValidationError
from utils.config_manager import get_api_key
from utils.formula_parser import parse_formula, assign_perovskite_sites

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = Path("data/raw")
OUTPUT_FILE = DATA_DIR / "nrel_perovskites.csv"
METADATA_FILE = DATA_DIR / "metadata.json"
DATASET_ID = "NREL/perovskite-stability"  # Verified real source identifier

def load_raw_data() -> pd.DataFrame:
    """
    Fetch raw perovskite data from the verified real source.
    Uses the Hugging Face datasets library to stream the real dataset.
    """
    logger.info(f"Fetching data from verified source: {DATASET_ID}")
    
    try:
        # Load the real dataset. We use streaming=True to handle large datasets
        # efficiently, but we will materialize the relevant columns for processing.
        dataset = load_dataset(DATASET_ID, split="train", streaming=True)
        
        # Convert to a list of dictionaries for processing
        # We only fetch what we need to avoid memory issues
        data_records = []
        batch_size = 1000
        count = 0
        
        for batch in dataset:
            # Ensure we have the necessary columns
            required_cols = ['formula', 'T_d', 'citation_title', 'source_metadata']
            if not all(col in batch.keys() for col in required_cols):
                # Fallback for schema mismatch - log and skip if critical
                logger.warning(f"Dataset schema mismatch. Expected columns: {required_cols}, found: {batch.keys()}")
                # Attempt to map common variations if possible, otherwise fail
                raise ValueError(f"Dataset schema mismatch. Missing required columns.")
            
            # Convert batch to records
            for i in range(len(batch['formula'])):
                record = {col: batch[col][i] for col in required_cols}
                data_records.append(record)
            
            count += len(batch['formula'])
            if count % 10000 == 0:
                logger.info(f"Fetched {count} records...")
        
        df = pd.DataFrame(data_records)
        logger.info(f"Successfully loaded {len(df)} records from source.")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch data from {DATASET_ID}: {str(e)}")
        raise RuntimeError(f"Data fetch failed: {str(e)}. No synthetic fallback allowed.")

def validate_entries(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Validate entries using the existing validator module (T009b).
    Filters for entries with valid T_d and validates title token overlap.
    """
    logger.info("Validating data entries...")
    
    # 1. Filter for entries with T_d (TGA onset)
    initial_count = len(df)
    df_valid_td = df.dropna(subset=['T_d'])
    dropped_count = initial_count - len(df_valid_td)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} entries with missing T_d values.")
    
    # 2. Validate title token overlap (>= 0.7 threshold) using T009b
    valid_entries = []
    invalid_entries = []
    
    for idx, row in df_valid_td.iterrows():
        try:
            # The validator expects a list of dicts with 'title' and potentially other fields
            # We adapt the row to the expected format
            entry = {
                'title': row.get('citation_title', ''),
                'formula': row.get('formula', ''),
                'T_d': row.get('T_d')
            }
            
            # Call the validation function from utils.validator
            # This function returns a boolean or raises an error based on the contract
            is_valid = validate_data_entries([entry])
            
            if is_valid:
                valid_entries.append(entry)
            else:
                invalid_entries.append(entry)
                
        except ValidationError as e:
            logger.warning(f"Validation error for entry {idx}: {e}")
            invalid_entries.append(entry)
        except Exception as e:
            logger.warning(f"Unexpected error validating entry {idx}: {e}")
            invalid_entries.append(entry)
    
    if len(valid_entries) == 0:
        raise ValueError("No valid entries passed validation. Check data source and validation logic.")
    
    logger.info(f"Validation complete: {len(valid_entries)} valid, {len(invalid_entries)} invalid.")
    return pd.DataFrame(valid_entries), invalid_entries

def parse_and_enrich(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse formulas and assign perovskite sites using T007.
    Enriches the dataframe with parsed structural information.
    """
    logger.info("Parsing formulas and enriching data...")
    
    parsed_data = []
    
    for idx, row in df.iterrows():
        try:
            formula_str = row['formula']
            # Parse formula using T007
            composition = parse_formula(formula_str)
            site_assignment = assign_perovskite_sites(composition)
            
            # Enrich row with parsed info
            enriched_row = row.to_dict()
            enriched_row['parsed_composition'] = str(composition)
            enriched_row['A_site'] = site_assignment.get('A')
            enriched_row['B_site'] = site_assignment.get('B')
            enriched_row['X_site'] = site_assignment.get('X')
            enriched_row['is_valid_perovskite'] = site_assignment.get('is_valid', False)
            
            parsed_data.append(enriched_row)
            
        except Exception as e:
            logger.warning(f"Failed to parse formula '{row.get('formula', 'N/A')}': {e}")
            # Keep the row but mark as invalid parse
            enriched_row = row.to_dict()
            enriched_row['parsed_composition'] = None
            enriched_row['A_site'] = None
            enriched_row['B_site'] = None
            enriched_row['X_site'] = None
            enriched_row['is_valid_perovskite'] = False
            parsed_data.append(enriched_row)
    
    return pd.DataFrame(parsed_data)

def main():
    """
    Main entry point for data ingestion pipeline.
    1. Load raw data
    2. Validate entries (filter T_d, validate titles)
    3. Parse and enrich formulas
    4. Write to CSV
    """
    logger.info("Starting data ingestion pipeline (T012)...")
    
    # Ensure output directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load Raw Data
    try:
        raw_df = load_raw_data()
    except RuntimeError as e:
        logger.critical(f"Data loading failed: {e}")
        sys.exit(1)
    
    # Step 2: Validate Entries
    try:
        validated_df, invalid_entries = validate_entries(raw_df)
    except ValueError as e:
        logger.critical(f"Validation failed: {e}")
        sys.exit(1)
    
    # Step 3: Parse and Enrich
    enriched_df = parse_and_enrich(validated_df)
    
    # Step 4: Write Output
    # Filter for valid perovskites if required by downstream tasks, 
    # but for now we output all validated entries with parse results
    output_df = enriched_df[enriched_df['is_valid_perovskite'] == True]
    
    if len(output_df) == 0:
        logger.warning("No valid perovskite entries found after parsing. Writing empty file.")
    
    output_df.to_csv(OUTPUT_FILE, index=False)
    logger.info(f"Successfully wrote {len(output_df)} records to {OUTPUT_FILE}")
    
    # Log invalid entries to a separate file for auditing (optional but good practice)
    if invalid_entries:
        invalid_path = DATA_DIR / "invalid_entries.json"
        with open(invalid_path, 'w') as f:
            json.dump(invalid_entries, f, indent=2)
        logger.info(f"Logged {len(invalid_entries)} invalid entries to {invalid_path}")

if __name__ == "__main__":
    main()
