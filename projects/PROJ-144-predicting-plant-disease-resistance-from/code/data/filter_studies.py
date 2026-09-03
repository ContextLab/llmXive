"""
T013c: Filter studies for resistance metadata.

Logic:
1. Read data/raw/study_manifest.json.
2. For each study, fetch phenotype metadata (or read from downloaded files if available).
3. Filter for studies containing both pre-challenge/baseline profiles and disease resistance/phenotype metadata.
4. Map resistance values to binary 0/1.
5. Write data/raw/filtered_study_manifest.json.
"""

import os
import sys
import json
import glob
import requests
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
MANIFEST_PATH = Path("data/raw/study_manifest.json")
FILTERED_MANIFEST_PATH = Path("data/raw/filtered_study_manifest.json")
RAW_DATA_DIR = Path("data/raw")

# Resistance value mapping (case-insensitive)
RESISTANT_VALUES = {'resistant', 'r', '1', 'yes', 'true', 'resistant'}
SUSCEPTIBLE_VALUES = {'susceptible', 's', '0', 'no', 'false', 'susceptible'}

# Target column names for resistance metadata
RESISTANCE_COLUMNS = ['phenotype', 'resistance_score', 'disease_status', 'challenge_outcome']

# Target column names for temporal metadata (pre-challenge/baseline)
TEMPORAL_COLUMNS = ['timepoint', 'sample_date', 'collection_date', 'inoculation_date', 'pre_challenge', 'baseline']

class DataFetchError(Exception):
    """Raised when fetching metadata fails."""
    pass

def load_manifest(manifest_path: Path) -> list:
    """Load the study manifest JSON."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        return json.load(f)

def fetch_phenotype_metadata(study_id: str, download_url: str) -> dict:
    """
    Fetch phenotype metadata for a study.
    Attempts to read from local file first if available, otherwise fetches from URL.
    """
    # Check for local file first (from T012b download)
    local_file = RAW_DATA_DIR / f"{study_id}_phenotype.csv"
    if local_file.exists():
        logger.info(f"Reading phenotype data from local file: {local_file}")
        import pandas as pd
        try:
            df = pd.read_csv(local_file)
            return df.to_dict(orient='records')
        except Exception as e:
            logger.warning(f"Failed to read local phenotype file {local_file}: {e}")
            # Fall through to URL fetch

    # Fallback to API fetch if local file missing or invalid
    # Construct phenotype URL based on study ID
    phenotype_url = f"https://www.metabolomicsworkbench.org/data/study.php?STUDY_ID={study_id}&PROGRAM=phenotype"
    
    try:
        response = requests.get(phenotype_url, timeout=30)
        if response.status_code == 200:
            # Assume CSV format for now, parse accordingly
            import pandas as pd
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            return df.to_dict(orient='records')
        else:
            logger.warning(f"Failed to fetch phenotype for {study_id}: HTTP {response.status_code}")
            return {}
    except requests.RequestException as e:
        logger.warning(f"Network error fetching phenotype for {study_id}: {e}")
        return {}

def check_columns_in_metadata(metadata: list, target_columns: list) -> list:
    """Check which target columns exist in the metadata."""
    if not metadata:
        return []
    
    # Get columns from the first record (assuming uniform schema)
    first_record = metadata[0]
    if isinstance(first_record, dict):
        available_cols = set(first_record.keys())
    else:
        # If it's a list of lists or other format, we can't easily check columns
        return []
    
    found_cols = [col for col in target_columns if col.lower() in [c.lower() for c in available_cols]]
    return found_cols

def has_resistance_metadata(metadata: list) -> tuple:
    """
    Check if metadata contains resistance-related columns and values.
    Returns (has_metadata, column_name, mapped_values)
    """
    if not metadata:
        return False, None, []

    # Check for resistance columns
    found_cols = check_columns_in_metadata(metadata, RESISTANCE_COLUMNS)
    if not found_cols:
        return False, None, []

    # Use the first found resistance column
    target_col = found_cols[0]
    
    # Find the actual case-insensitive column name
    first_record = metadata[0]
    actual_col = None
    for col in first_record.keys():
        if col.lower() == target_col.lower():
            actual_col = col
            break
    
    if not actual_col:
        return False, None, []

    # Extract and map values
    mapped_values = []
    has_valid_values = False

    for record in metadata:
        val = record.get(actual_col)
        if val is None:
            continue
        
        val_str = str(val).strip().lower()
        
        if val_str in RESISTANT_VALUES:
            mapped_values.append(1)
            has_valid_values = True
        elif val_str in SUSCEPTIBLE_VALUES:
            mapped_values.append(0)
            has_valid_values = True
        elif val_str in ['1']:
            mapped_values.append(1)
            has_valid_values = True
        elif val_str in ['0']:
            mapped_values.append(0)
            has_valid_values = True

    return has_valid_values, actual_col, mapped_values

def has_temporal_metadata(metadata: list) -> bool:
    """Check if metadata contains temporal/pre-challenge related columns."""
    if not metadata:
        return False

    found_cols = check_columns_in_metadata(metadata, TEMPORAL_COLUMNS)
    return len(found_cols) > 0

def filter_studies(manifest: list) -> list:
    """
    Filter studies that have both resistance and temporal metadata.
    """
    filtered = []
    
    for study in manifest:
        study_id = study.get('study_id')
        title = study.get('title')
        download_url = study.get('download_url')
        
        if not study_id:
            logger.warning(f"Skipping study without ID: {study}")
            continue

        logger.info(f"Checking study: {study_id} - {title}")
        
        # Fetch phenotype metadata
        metadata = fetch_phenotype_metadata(study_id, download_url)
        
        if not metadata:
            logger.warning(f"No metadata found for {study_id}, skipping.")
            continue

        # Check for resistance metadata
        has_res, res_col, res_values = has_resistance_metadata(metadata)
        
        # Check for temporal metadata
        has_temp = has_temporal_metadata(metadata)

        if has_res and has_temp:
            logger.info(f"Study {study_id} PASSED: has resistance ({res_col}) and temporal metadata.")
            # Add study to filtered list with metadata summary
            study_entry = {
                'study_id': study_id,
                'title': title,
                'download_url': download_url,
                'has_resistance_metadata': True,
                'resistance_column': res_col,
                'resistance_value_count': len(res_values),
                'has_temporal_metadata': True,
                'status': 'qualified'
            }
            filtered.append(study_entry)
        else:
            reason = []
            if not has_res:
                reason.append("missing resistance metadata")
            if not has_temp:
                reason.append("missing temporal metadata")
            logger.info(f"Study {study_id} FAILED: {', '.join(reason)}")
            # Still include in manifest but mark as unqualified
            study_entry = {
                'study_id': study_id,
                'title': title,
                'download_url': download_url,
                'has_resistance_metadata': has_res,
                'has_temporal_metadata': has_temp,
                'status': 'unqualified'
            }
            filtered.append(study_entry)

    return filtered

def save_filtered_manifest(filtered_studies: list, output_path: Path):
    """Save the filtered manifest to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(filtered_studies, f, indent=2)
    logger.info(f"Saved filtered manifest to {output_path}")

def main():
    """Main entry point for T013c."""
    logger.info("Starting T013c: Filter studies for resistance metadata.")
    
    # Pre-check: Verify input manifest exists
    if not MANIFEST_PATH.exists():
        logger.error(f"Pre-check failed: {MANIFEST_PATH} does not exist.")
        logger.error("Run T012a-val first to generate study_manifest.json.")
        sys.exit(1)

    # Load manifest
    try:
        manifest = load_manifest(MANIFEST_PATH)
        logger.info(f"Loaded {len(manifest)} studies from manifest.")
    except Exception as e:
        logger.error(f"Failed to load manifest: {e}")
        sys.exit(1)

    # Filter studies
    filtered_studies = filter_studies(manifest)
    
    # Count qualified studies
    qualified_count = sum(1 for s in filtered_studies if s.get('status') == 'qualified')
    logger.info(f"Filtering complete. Qualified studies: {qualified_count}/{len(filtered_studies)}")

    # Save output (even if count is 0, as per task requirements)
    try:
        save_filtered_manifest(filtered_studies, FILTERED_MANIFEST_PATH)
        logger.info("T013c completed successfully.")
    except Exception as e:
        logger.error(f"Failed to save filtered manifest: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()