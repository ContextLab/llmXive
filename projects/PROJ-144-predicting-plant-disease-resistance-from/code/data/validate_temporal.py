"""
Temporal validation module for plant disease resistance metabolomics data.

This module verifies FR-014: Explicitly check metadata for 'pre-challenge', 
'baseline', or timestamps prior to pathogen inoculation.
"""

import os
import glob
import json
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

# Import custom exceptions from the project's utility module
from utils.exceptions import TemporalVerificationError, DataUnavailableError
from utils.io import compute_file_hash, log_artifact

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('state/temporal_validation.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
TEMPORAL_KEYWORDS = [
    'pre-challenge', 'prechallenge', 'baseline', 'pre_inoculation', 
    'preinoculation', 'pre-inoculation', 'control', 'time_0', 't0', 
    't_0', 'before_infection', 'pre_infection', 'preinfection'
]
TEMPO_REL_SEPARATION_KEYWORDS = [
    'post-challenge', 'postchallenge', 'post_inoculation', 'postinoculation',
    'post-inoculation', 'after_infection', 'post_infection', 'postinfection',
    'disease_onset', 'symptom_onset'
]

DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
MANIFEST_PATH = DATA_RAW_DIR / "study_manifest.json"
OUTPUT_LOG_PATH = DATA_PROCESSED_DIR / "temporal_validation_log.json"

def validate_temporal_consistency(phenotype_df: pd.DataFrame, study_id: str) -> Dict[str, Any]:
    """
    Validate that a study's phenotype metadata contains explicit temporal markers
    indicating pre-challenge/baseline measurements.
    
    Args:
        phenotype_df: DataFrame containing phenotype metadata for a single study.
        study_id: Identifier for the study being validated.
        
    Returns:
        Dictionary containing validation results for the study.
        
    Raises:
        TemporalVerificationError: If no valid temporal markers are found.
    """
    logger.info(f"Validating temporal consistency for study: {study_id}")
    
    result = {
        "study_id": study_id,
        "passed": False,
        "reason": "",
        "details": {}
    }
    
    # Check if DataFrame is empty
    if phenotype_df.empty:
        result["reason"] = "Phenotype DataFrame is empty"
        logger.error(f"Study {study_id}: {result['reason']}")
        raise TemporalVerificationError(f"Study {study_id}: {result['reason']}")
    
    # Collect all columns to search
    columns_to_search = phenotype_df.columns.tolist()
    
    # Search for temporal keywords in column names and values
    found_keywords = []
    matching_rows = 0
    
    for col in columns_to_search:
        col_str = str(col).lower()
        col_values = phenotype_df[col].astype(str).str.lower()
        
        # Check column name
        for keyword in TEMPORAL_KEYWORDS:
            if keyword in col_str:
                found_keywords.append(f"column_name:{col}:{keyword}")
                matching_rows += len(phenotype_df)  # All rows match by column name
                break
        
        # Check column values if no keyword found in name yet
        if not any(k.startswith(f"column_name:{col}:") for k in found_keywords):
            for keyword in TEMPORAL_KEYWORDS:
                mask = col_values.str.contains(keyword, na=False)
                if mask.any():
                    count = mask.sum()
                    found_keywords.append(f"value:{col}:{keyword}:{count}")
                    matching_rows += count
                    break
    
    # Also check for explicit time/visit columns that might indicate baseline
    time_columns = [col for col in columns_to_search if 'time' in col.lower() or 'visit' in col.lower() or 'day' in col.lower()]
    
    if not found_keywords and not time_columns:
        result["reason"] = "No temporal markers (pre-challenge, baseline, etc.) found in metadata"
        logger.error(f"Study {study_id}: {result['reason']}")
        raise TemporalVerificationError(f"Study {study_id}: {result['reason']}")
    
    # If we found time/visit columns but no explicit baseline keywords, check for value 0 or 'baseline'
    if not found_keywords and time_columns:
        for col in time_columns:
            col_values = phenotype_df[col].astype(str).str.lower().str.strip()
            # Check for 0, 'baseline', 'pre', etc. in time columns
            if col_values.isin(['0', 'baseline', 'pre', 't0', 't_0']).any():
                found_keywords.append(f"time_col:{col}:has_baseline_value")
                matching_rows += len(phenotype_df)
                break
    
    # Final check
    if not found_keywords:
        result["reason"] = "No explicit temporal markers indicating pre-challenge/baseline measurements found"
        logger.error(f"Study {study_id}: {result['reason']}")
        raise TemporalVerificationError(f"Study {study_id}: {result['reason']}")
    
    # If we get here, validation passed
    result["passed"] = True
    result["reason"] = "Temporal markers found"
    result["details"] = {
        "keywords_found": found_keywords,
        "matching_row_count": matching_rows,
        "total_rows": len(phenotype_df)
    }
    
    logger.info(f"Study {study_id} passed temporal validation")
    return result

def validate_studies_from_manifest(manifest_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Validate temporal consistency for all studies listed in the manifest.
    
    Args:
        manifest_path: Path to the study manifest JSON file. Defaults to DATA_RAW_DIR/study_manifest.json.
        
    Returns:
        List of validation result dictionaries for all studies.
        
    Raises:
        DataUnavailableError: If manifest is missing or invalid.
        TemporalVerificationError: If any study fails temporal validation.
    """
    if manifest_path is None:
        manifest_path = MANIFEST_PATH
        
    # Verify manifest exists
    if not manifest_path.exists():
        raise DataUnavailableError(
            f"Manifest file not found: {manifest_path}. "
            "Pre-requisite T012a must complete first."
        )
    
    # Load manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    if not isinstance(manifest, list) or len(manifest) == 0:
        raise DataUnavailableError(
            f"Manifest file is empty or invalid: {manifest_path}"
        )
    
    logger.info(f"Validating {len(manifest)} studies from manifest")
    
    all_results = []
    failed_studies = []
    
    for study_entry in manifest:
        study_id = study_entry.get('study_id')
        phenotype_url = study_entry.get('phenotype_url')
        
        if not study_id:
            logger.warning("Study entry missing study_id, skipping")
            continue
        
        # Determine phenotype file path
        phenotype_file = DATA_RAW_DIR / f"{study_id}_phenotype.csv"
        
        if not phenotype_file.exists():
            logger.warning(f"Phenotype file not found for study {study_id}: {phenotype_file}")
            # Try to find it with different naming patterns
            possible_files = list(DATA_RAW_DIR.glob(f"{study_id}*phenotype*.csv"))
            if possible_files:
                phenotype_file = possible_files[0]
                logger.info(f"Found phenotype file at alternative path: {phenotype_file}")
            else:
                result = {
                    "study_id": study_id,
                    "passed": False,
                    "reason": f"Phenotype file not found: {phenotype_file}",
                    "details": {}
                }
                all_results.append(result)
                failed_studies.append(study_id)
                continue
        
        # Load phenotype data
        try:
            phenotype_df = pd.read_csv(phenotype_file)
            logger.info(f"Loaded phenotype data for {study_id}: {len(phenotype_df)} rows, {len(phenotype_df.columns)} columns")
        except Exception as e:
            result = {
                "study_id": study_id,
                "passed": False,
                "reason": f"Failed to load phenotype file: {str(e)}",
                "details": {}
            }
            all_results.append(result)
            failed_studies.append(study_id)
            continue
        
        # Validate temporal consistency
        try:
            validation_result = validate_temporal_consistency(phenotype_df, study_id)
            all_results.append(validation_result)
        except TemporalVerificationError as e:
            result = {
                "study_id": study_id,
                "passed": False,
                "reason": str(e),
                "details": {}
            }
            all_results.append(result)
            failed_studies.append(study_id)
    
    # Log summary
    passed_count = sum(1 for r in all_results if r.get('passed', False))
    failed_count = len(all_results) - passed_count
    logger.info(f"Temporal validation complete: {passed_count} passed, {failed_count} failed")
    
    # If any studies failed, raise an error to halt the pipeline
    if failed_studies:
        error_msg = f"Temporal validation failed for studies: {', '.join(failed_studies)}"
        logger.error(error_msg)
        raise TemporalVerificationError(error_msg)
    
    return all_results

def main():
    """
    Main entry point for temporal validation script.
    
    This script:
    1. Reads the study manifest from data/raw/study_manifest.json
    2. For each study, loads the phenotype CSV
    3. Validates temporal markers (pre-challenge, baseline, etc.)
    4. Writes results to data/processed/temporal_validation_log.json
    5. Raises TemporalVerificationError if any study fails
    """
    logger.info("Starting temporal validation pipeline")
    
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Run validation
        results = validate_studies_from_manifest()
        
        # Write results to output file
        with open(OUTPUT_LOG_PATH, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Validation results written to {OUTPUT_LOG_PATH}")
        
        # Compute and log checksum
        file_hash = compute_file_hash(OUTPUT_LOG_PATH)
        log_artifact(OUTPUT_LOG_PATH, file_hash)
        logger.info(f"Computed checksum for output: {file_hash}")
        
        logger.info("Temporal validation completed successfully")
        
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        sys.exit(1)
    except TemporalVerificationError as e:
        logger.error(f"Temporal verification failed: {e}")
        # Re-raise to halt the pipeline as required
        raise
    except Exception as e:
        logger.error(f"Unexpected error during temporal validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
