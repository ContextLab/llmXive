import os
import glob
import json
import sys
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd

from utils.exceptions import TemporalVerificationError, DataUnavailableError
from utils.io import log_pipeline_status

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

MANIFEST_PATH = "data/raw/study_manifest.json"
PROCESSED_DIR = Path("data/processed")
VALIDATION_LOG_PATH = PROCESSED_DIR / "temporal_validation_log.json"

# Keywords indicating pre-challenge or baseline measurements
TEMPORAL_KEYWORDS = [
    'pre-challenge', 'pre_challenge', 'baseline', 'preinoculation',
    'pre-inoculation', 'preinoc', 'control', 'time_0', 't0', 'start'
]

def validate_temporal_consistency(metadata: pd.DataFrame) -> bool:
    """
    Validates temporal consistency of the phenotype metadata.
    
    Explicitly checks metadata for 'pre-challenge', 'baseline', or timestamps 
    prior to pathogen inoculation.
    
    Args:
        metadata: DataFrame containing phenotype columns (e.g., 'measurement_time', 
                  'time_point', 'treatment', 'condition').
    
    Returns:
        bool: True if temporal criteria are met.
    
    Raises:
        TemporalVerificationError: If metadata lacks temporal indicators.
    """
    if metadata is None or metadata.empty:
        raise TemporalVerificationError("Metadata is empty or None.")
    
    # Normalize column names to lowercase for case-insensitive search
    metadata_cols = [str(col).lower() for col in metadata.columns]
    
    # Heuristic 1: Check for explicit temporal keywords in column values or names
    # We look for columns that might contain time-related strings
    temporal_columns = []
    for col in metadata.columns:
        col_str = str(col).lower()
        for keyword in TEMPORAL_KEYWORDS:
            if keyword in col_str:
                temporal_columns.append(col)
                break
    
    # If we found columns with temporal keywords, check their values
    if temporal_columns:
        logger.info(f"Found potential temporal columns: {temporal_columns}")
        has_valid_temporal = False
        for col in temporal_columns:
            # Check if any value in the column contains a temporal keyword
            col_values = metadata[col].astype(str).str.lower()
            for keyword in TEMPORAL_KEYWORDS:
                if col_values.str.contains(keyword, na=False).any():
                    has_valid_temporal = True
                    logger.info(f"Valid temporal indicator found in column '{col}': {keyword}")
                    break
            if has_valid_temporal:
                break
        
        if not has_valid_temporal:
            raise TemporalVerificationError(
                f"Temporal keywords found in column names but not in values. "
                f"Columns checked: {temporal_columns}. "
                f"Expected values like 'baseline', 'pre-challenge', etc."
            )
        return True

    # Heuristic 2: Check for time-point columns that indicate time 0 or early time
    # Look for common time column names
    time_col_candidates = ['time', 'time_point', 'day', 'days', 'hours', 't', 'sample_time']
    time_col = None
    for candidate in time_col_candidates:
        if candidate in metadata_cols:
            # Find the actual column name (case preserved)
            for col in metadata.columns:
                if str(col).lower() == candidate:
                    time_col = col
                    break
            if time_col:
                break
    
    if time_col:
        logger.info(f"Checking time column: {time_col}")
        # Check if there are values <= 0 or very small values indicating baseline
        # Assuming time is numeric
        try:
            time_values = pd.to_numeric(metadata[time_col], errors='coerce')
            if time_values.min() <= 0:
                logger.info(f"Time column {time_col} contains values <= 0, indicating baseline/pre-challenge.")
                return True
            # If min > 0, we might still have baseline if there's a 'control' group
            # But strictly for FR-014, we need explicit 'pre-challenge' or 'baseline'
            # If time starts > 0 and no explicit labels, we fail
            logger.warning(f"Time column {time_col} starts at {time_values.min()}. "
                         f"No explicit 'pre-challenge' or 'baseline' labels found.")
            # We will be strict: if no explicit label and min time > 0, fail
            raise TemporalVerificationError(
                f"Time column '{time_col}' exists but starts at {time_values.min()}. "
                f"Explicit 'pre-challenge' or 'baseline' labels required by FR-014."
            )
        except Exception as e:
            logger.warning(f"Could not parse time column '{time_col}' as numeric: {e}")
            # If we can't parse, we can't verify temporal consistency strictly
            raise TemporalVerificationError(
                f"Could not verify temporal consistency for column '{time_col}' (non-numeric). "
                f"Requires explicit 'pre-challenge' or 'baseline' labels."
            )

    # Heuristic 3: Check for treatment/condition columns that might indicate control/baseline
    # If we have a 'treatment' or 'condition' column, check for 'control' or 'mock'
    condition_cols = ['treatment', 'condition', 'group', 'status']
    for cond_col in condition_cols:
        if cond_col in metadata_cols:
            for col in metadata.columns:
                if str(col).lower() == cond_col:
                    cond_values = metadata[col].astype(str).str.lower()
                    # Check for control-like values
                    if cond_values.str.contains('control|mock|untreated|baseline', na=False).any():
                        logger.info(f"Found control-like values in '{col}' indicating pre-challenge.")
                        return True
                    break
    
    # If we reach here, no temporal indicators found
    logger.error("No temporal indicators (pre-challenge, baseline, time=0, or control) found in metadata.")
    raise TemporalVerificationError(
        "Metadata lacks 'pre-challenge', 'baseline', or timestamps prior to pathogen inoculation. "
        "Cannot proceed with study."
    )

def validate_studies_from_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """
    Validates studies from the manifest file.
    
    Args:
        manifest_path: Path to the study manifest JSON file.
    
    Returns:
        List of dicts with study_id and validation status.
    
    Raises:
        DataUnavailableError: If manifest is missing.
    """
    if not os.path.exists(manifest_path):
        raise DataUnavailableError(
            f"Pre-requisite manifest missing: {manifest_path}. Run T012a first."
        )
    
    with open(manifest_path, 'r') as f:
        studies = json.load(f)
    
    if not studies:
        raise DataUnavailableError("Manifest is empty.")
    
    results = []
    for study in studies:
        study_id = study.get('study_id')
        phenotype_url = study.get('phenotype_url')
        
        if not study_id or not phenotype_url:
            logger.warning(f"Skipping study {study_id}: missing study_id or phenotype_url.")
            continue
        
        # Expected phenotype file path based on T012b naming convention
        # T012b saves as data/raw/{study_id}_phenotype.csv
        phenotype_file = Path("data/raw") / f"{study_id}_phenotype.csv"
        
        if not phenotype_file.exists():
            logger.warning(f"Phenotype file missing for {study_id}: {phenotype_file}")
            # We can't validate without the file, but we shouldn't crash the whole script
            # However, T013 requires validation of existing files. 
            # If the file is missing, we log it but don't necessarily raise for the whole script
            # unless the task implies we must have the file. T013 says "Input: data/raw/{study_id}_phenotype.csv"
            # So if it's missing, we can't validate. We'll mark as failed for this study.
            results.append({
                "study_id": study_id,
                "status": "failed",
                "reason": "Phenotype file missing"
            })
            continue
        
        try:
            # Load the phenotype data
            df = pd.read_csv(phenotype_file)
            
            # Validate temporal consistency
            is_valid = validate_temporal_consistency(df)
            
            results.append({
                "study_id": study_id,
                "status": "passed" if is_valid else "failed",
                "reason": None
            })
            logger.info(f"Study {study_id}: PASSED temporal validation.")
            
        except TemporalVerificationError as e:
            results.append({
                "study_id": study_id,
                "status": "failed",
                "reason": str(e)
            })
            logger.error(f"Study {study_id}: FAILED temporal validation. Reason: {e}")
        except Exception as e:
            results.append({
                "study_id": study_id,
                "status": "failed",
                "reason": f"Unexpected error: {str(e)}"
            })
            logger.error(f"Study {study_id}: Unexpected error during validation. Reason: {e}")
    
    return results

def main():
    """Entry point for temporal validation."""
    logger.info("Starting temporal validation for studies.")
    
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        validation_results = validate_studies_from_manifest(MANIFEST_PATH)
        
        # Write results to JSON
        with open(VALIDATION_LOG_PATH, 'w') as f:
            json.dump(validation_results, f, indent=2)
        
        logger.info(f"Temporal validation log written to {VALIDATION_LOG_PATH}")
        
        # Check if any study failed
        failed_studies = [r for r in validation_results if r['status'] == 'failed']
        if failed_studies:
            logger.warning(f"{len(failed_studies)} study(s) failed temporal validation.")
            # We do not raise here to allow the log to be generated, 
            # but the pipeline should ideally halt or skip these studies.
            # The task says "raise ... and halt the pipeline for that study", which we did per study.
            # For the script itself, we return success if at least one passed, 
            # or we could exit with error if all failed. 
            # Given the requirement "raise ... and halt", we've raised per study.
            # We'll log the failure but not exit with error code to allow inspection.
        else:
            logger.info("All studies passed temporal validation.")
            
        return validation_results
        
    except DataUnavailableError as e:
        logger.error(f"Data unavailable: {e}")
        # Re-raise to halt the pipeline as per requirements
        raise
    except Exception as e:
        logger.error(f"Unexpected error in main: {e}")
        raise

if __name__ == "__main__":
    main()
