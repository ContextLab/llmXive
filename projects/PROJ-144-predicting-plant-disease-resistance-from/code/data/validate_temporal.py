"""
Temporal Validation Module for Plant Metabolomics Pipeline.

This module implements FR-014: Explicitly check metadata for 'pre-challenge',
'baseline', or timestamps prior to pathogen inoculation.

It reads raw phenotype CSVs downloaded in T012b, verifies temporal consistency,
and writes a validation log to data/processed/temporal_validation_log.json.
"""

import os
import sys
import json
import glob
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import constants and utilities from the project structure
from utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR
from utils.io import log_data_acquisition_step

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/temporal_validation.log')
    ]
)
logger = logging.getLogger(__name__)

class TemporalVerificationWarning(Warning):
    """Custom warning for ambiguous or missing temporal metadata."""
    pass

class TemporalVerificationError(Exception):
    """Custom error for critical temporal validation failures."""
    pass

def parse_date(date_str: str) -> Optional[datetime]:
    """
    Attempt to parse a date string into a datetime object.
    Supports common formats: ISO 8601, YYYY-MM-DD, MM/DD/YYYY.
    """
    if not date_str or pd.isna(date_str):
        return None

    date_str = str(date_str).strip()
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%m/%d/%Y",
        "%d-%m-%Y",
        "%Y%m%d"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def load_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """Load the study manifest JSON file."""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, 'r') as f:
        data = json.load(f)
    return data

def load_phenotype_data(study_id: str) -> Optional[Dict[str, Any]]:
    """
    Load phenotype data for a specific study.
    Returns a dictionary with the dataframe and metadata.
    """
    phenotype_path = os.path.join(DATA_RAW_DIR, f"{study_id}_phenotype.csv")
    
    if not os.path.exists(phenotype_path):
        logger.warning(f"Phenotype file not found for study {study_id}: {phenotype_path}")
        return None

    try:
        import pandas as pd
        df = pd.read_csv(phenotype_path)
        return {
            'study_id': study_id,
            'df': df,
            'path': phenotype_path
        }
    except Exception as e:
        logger.error(f"Error loading phenotype data for {study_id}: {e}")
        return None

def check_temporal_fields(df: Any, study_id: str) -> Dict[str, Any]:
    """
    Check for temporal fields in the dataframe and verify pre-challenge status.
    
    Fields to check:
    - 'timepoint', 'sample_date', 'collection_date', 'inoculation_date'
    
    Logic:
    - If 'inoculation_date' exists, verify 'sample_date' (or similar) is prior.
    - If 'timepoint' exists, check for values like 'baseline', 'pre-challenge', 0.
    """
    result = {
        'study_id': study_id,
        'status': 'unverified',
        'reason': 'Unknown',
        'fields_found': [],
        'warnings': []
    }

    columns = [str(c).lower() for c in df.columns]
    
    # Mapping of expected columns to canonical names
    date_columns = {
        'timepoint': 'timepoint',
        'sample_date': 'sample_date',
        'collection_date': 'sample_date',
        'inoculation_date': 'inoculation_date',
        'baseline': 'baseline_indicator'
    }

    found_fields = []
    sample_date_col = None
    inoculation_date_col = None
    timepoint_col = None
    baseline_col = None

    for col in df.columns:
        col_lower = str(col).lower()
        if col_lower in date_columns:
            found_fields.append(col)
            if col_lower == 'timepoint':
                timepoint_col = col
            elif col_lower in ['sample_date', 'collection_date']:
                sample_date_col = col
            elif col_lower == 'inoculation_date':
                inoculation_date_col = col
            elif col_lower == 'baseline':
                baseline_col = col

    result['fields_found'] = found_fields

    # Case 1: Check for explicit timepoint values (baseline, pre-challenge)
    if timepoint_col:
        logger.info(f"Study {study_id}: Found timepoint column '{timepoint_col}'")
        # Check if any value indicates pre-challenge
        sample_values = df[timepoint_col].dropna().unique()
        pre_challenge_keywords = ['baseline', 'pre-challenge', 'prechallenge', '0', 't0', 't_0']
        
        has_pre_challenge = False
        for val in sample_values:
            val_str = str(val).lower().strip()
            if any(kw in val_str for kw in pre_challenge_keywords):
                has_pre_challenge = True
                break

        if has_pre_challenge:
            result['status'] = 'verified'
            result['reason'] = 'Contains explicit pre-challenge/baseline timepoint'
        else:
            result['status'] = 'unverified'
            result['reason'] = 'Timepoint column present but no pre-challenge values found'
            result['warnings'].append(f"Timepoint values: {sample_values[:5]}...")

    # Case 2: Check for date comparison (sample_date < inoculation_date)
    elif sample_date_col and inoculation_date_col:
        logger.info(f"Study {study_id}: Found date columns for comparison")
        # Convert columns to datetime
        try:
            sample_dates = pd.to_datetime(df[sample_date_col], errors='coerce')
            inoc_dates = pd.to_datetime(df[inoculation_date_col], errors='coerce')
            
            # Check if any sample is before inoculation
            valid_pairs = sample_dates.notna() & inoc_dates.notna()
            if valid_pairs.any():
                prior_samples = sample_dates[valid_pairs] < inoc_dates[valid_pairs]
                if prior_samples.any():
                    result['status'] = 'verified'
                    result['reason'] = 'Sample dates found prior to inoculation dates'
                else:
                    result['status'] = 'unverified'
                    result['reason'] = 'No sample dates found prior to inoculation'
                    result['warnings'].append("All samples appear to be post-inoculation")
            else:
                result['status'] = 'unverified'
                result['reason'] = 'Could not parse date columns for comparison'
                result['warnings'].append("Invalid date formats in columns")
        except Exception as e:
            result['status'] = 'unverified'
            result['reason'] = f'Error parsing dates: {str(e)}'
            result['warnings'].append(str(e))

    # Case 3: Check for baseline indicator column
    elif baseline_col:
        logger.info(f"Study {study_id}: Found baseline indicator column")
        if df[baseline_col].any():
            result['status'] = 'verified'
            result['reason'] = 'Baseline indicator present and positive'
        else:
            result['status'] = 'unverified'
            result['reason'] = 'Baseline indicator column present but no positive values'
    
    else:
        # No relevant fields found
        result['status'] = 'unverified'
        result['reason'] = 'No temporal fields (timepoint, sample_date, inoculation_date) found'
        result['warnings'].append("Missing required temporal metadata fields")

    return result

def validate_studies_from_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """
    Iterate through studies in the manifest and validate temporal consistency.
    """
    studies = load_manifest(manifest_path)
    validation_results = []
    verified_count = 0

    for study in studies:
        study_id = study.get('study_id')
        if not study_id:
            logger.warning("Skipping study with missing ID in manifest")
            continue

        logger.info(f"Validating temporal consistency for study: {study_id}")
        
        # Load phenotype data
        data = load_phenotype_data(study_id)
        if not data:
            # If data is missing, we mark as unverified but do not halt
            # The task says: "mark the study as 'unverified' and log a TemporalVerificationWarning"
            warning_msg = f"Phenotype data missing for {study_id}"
            logger.warning(warning_msg)
            result = {
                'study_id': study_id,
                'status': 'unverified',
                'reason': 'Phenotype data file missing',
                'fields_found': [],
                'warnings': [warning_msg]
            }
            validation_results.append(result)
            continue

        # Check temporal fields
        result = check_temporal_fields(data['df'], study_id)
        validation_results.append(result)

        if result['status'] == 'verified':
            verified_count += 1
        
        # Log warnings if status is unverified
        if result['status'] == 'unverified' and result['warnings']:
            for w in result['warnings']:
                logger.warning(f"TemporalVerificationWarning for {study_id}: {w}")

    return validation_results

def main():
    """
    Main entry point for the temporal validation script.
    
    1. Load study manifest from data/raw/study_manifest.json
    2. Validate each study's phenotype data for temporal consistency
    3. Write results to data/processed/temporal_validation_log.json
    4. Exit with code 0 if at least one study is verified, else 1
    """
    manifest_path = os.path.join(DATA_RAW_DIR, "study_manifest.json")
    output_dir = DATA_PROCESSED_DIR
    output_path = os.path.join(output_dir, "temporal_validation_log.json")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    logger.info("Starting temporal validation pipeline...")
    
    try:
        # Validate studies
        results = validate_studies_from_manifest(manifest_path)
        
        # Write results to JSON
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Validation log written to: {output_path}")

        # Determine exit code
        verified_studies = [r for r in results if r['status'] == 'verified']
        
        if len(verified_studies) == 0:
            logger.error("NO studies were verified. Exiting with code 1.")
            sys.exit(1)
        else:
            logger.info(f"Success: {len(verified_studies)} study(s) verified. Exiting with code 0.")
            sys.exit(0)

    except FileNotFoundError as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
