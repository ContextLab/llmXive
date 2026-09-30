import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from pathlib import Path
from typing import Tuple, List, Dict, Optional, Any
import json

# Local imports matching the provided API surface
from config import get_output_path, ensure_directories
from utils.logging import get_logger

# Attempt to import datasets for HuggingFace streaming
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    logging.warning("datasets library not installed. Streaming validation will fail if external source required.")

logger = get_logger(__name__)

def check_independent_cohort_access() -> Dict[str, Any]:
    """
    Checks for accessible independent cohorts for validation (US4).
    Attempts to load known datasets via HuggingFace streaming or local files.
    
    Returns a dictionary with status and details.
    """
    result = {
        "status": "inaccessible",
        "source": None,
        "details": "No accessible cohort found.",
        "path": None
    }

    # 1. Check local external files first (fastest)
    local_path = Path("data/external")
    if local_path.exists():
        csv_files = list(local_path.glob("*.csv"))
        if csv_files:
            logger.info(f"Found local external data: {csv_files[0]}")
            result["status"] = "accessible"
            result["source"] = "local"
            result["path"] = str(csv_files[0])
            result["details"] = f"Local file found: {csv_files[0].name}"
            return result

    # 2. Attempt HuggingFace streaming for known IDs
    # These are hypothetical IDs based on common microbiome datasets.
    # In a real scenario, these would be verified in T030b.
    candidate_ids = [
        "ukbiobank-microbiome", 
        "metahit", 
        "gut-microbiome-mh"
    ]

    if not HAS_DATASETS:
        result["details"] = "HuggingFace datasets library not available."
        return result

    for ds_id in candidate_ids:
        try:
            logger.info(f"Attempting to stream dataset: {ds_id}")
            # Use streaming=True to avoid downloading full dataset (~GBs)
            # We only need to verify accessibility and structure
            ds = load_dataset(ds_id, split="train", streaming=True)
            
            # Verify we can iterate at least once
            sample = next(iter(ds))
            
            # Check for expected columns (microbiome or metadata)
            # We assume the dataset has either 'taxonomy'/'counts' or metadata like 'phq9'
            has_taxonomy = any(k in sample for k in ['taxonomy', 'counts', 'otu', 'feature'])
            has_metadata = any(k in sample for k in ['phq9', 'gad7', 'mental_health', 'depression'])
            
            if has_taxonomy or has_metadata:
                logger.info(f"Successfully accessed independent cohort: {ds_id}")
                result["status"] = "accessible"
                result["source"] = "huggingface"
                result["dataset_id"] = ds_id
                result["details"] = f"Streamed successfully. Keys: {list(sample.keys())}"
                return result
            else:
                logger.warning(f"Dataset {ds_id} accessible but missing expected columns.")
                
        except Exception as e:
            logger.debug(f"Failed to load {ds_id}: {str(e)}")
            continue

    result["details"] = "All candidate datasets inaccessible or missing required structure."
    return result

def run_validation_check() -> Dict[str, Any]:
    """
    Main entry point for T031.
    Checks cohort access and writes status to results/validation_urls_verified.json
    (as per dependency on T030b) and results/validation_report.txt (as per T032b).
    """
    logger.info("Starting T031: Independent Cohort Access Check")
    ensure_directories()
    
    # 1. Check access
    access_result = check_independent_cohort_access()
    
    # 2. Write verification status (T030b output expectation)
    verification_path = Path(get_output_path("results/validation_urls_verified.json"))
    with open(verification_path, 'w') as f:
        json.dump(access_result, f, indent=2)
    logger.info(f"Wrote verification status to {verification_path}")
    
    # 3. Write validation report (T032b requirement)
    # If accessible, we mark it as ready for T032a. If not, we write the skip message.
    report_path = Path(get_output_path("results/validation_report.txt"))
    
    with open(report_path, 'w') as f:
        f.write("=== Independent Cohort Validation Report ===\n\n")
        f.write(f"Status: {access_result['status'].upper()}\n")
        f.write(f"Source: {access_result.get('source', 'None')}\n")
        f.write(f"Details: {access_result['details']}\n\n")
        
        if access_result['status'] == 'accessible':
            f.write("Validation is READY. Proceed to T032a to download and correlate.\n")
        else:
            f.write("Validation Skipped: No independent cohort available.\n")
            f.write("Marking SC-003 as 'Not Applicable' per protocol.\n")
    
    logger.info(f"Wrote validation report to {report_path}")
    
    return access_result

def main():
    """Entry point for script execution."""
    result = run_validation_check()
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    main()