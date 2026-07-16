"""
Integration test for end-to-end data pairing (US1).

This test verifies that the data acquisition and pairing pipeline correctly:
1. Loads expression and metabolite matrices from the 'data/processed/' directory.
2. Matches samples based on biological sample identifiers.
3. Calculates the pairing rate.
4. Logs mismatches to 'logs/data_pairing.json' if pairing rate < 95%.
5. Raises E-PAIRING if the pairing rate is insufficient and no valid fallback exists.

Prerequisites:
- T021/T022 (Data Downloaders) must have generated processed CSVs in data/processed/.
- T023 (Pairing Logic) must be implemented in code/data_download.py or a dedicated pairing module.
- T004 (Logging Utils) must be available to write mismatch logs.
- T007 (Error Handler) must be available to raise E-PAIRING.
"""
import json
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set

# Project root is two levels up from tests/integration/
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from exceptions import E_PAIRING
from logging_utils import log_data_pairing_mismatches_batch
from data_aggregation import load_expression_matrix, load_metabolite_matrix, calculate_pairing_rate
from error_handler import raise_pairing_error

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PAIRED_DIR = PROJECT_ROOT / "data" / "paired"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"
PAIRING_LOG_PATH = LOGS_DIR / "data_pairing.json"
MIN_PAIRING_RATE = 0.95

def load_sample_ids_from_matrix(matrix_path: Path) -> Set[str]:
    """
    Extracts sample IDs from a processed matrix CSV.
    Assumes the first column is 'sample_id' or 'biosample_id'.
    """
    if not matrix_path.exists():
        raise FileNotFoundError(f"Matrix file not found: {matrix_path}")
    
    df = load_expression_matrix(matrix_path) if "expression" in matrix_path.name else load_metabolite_matrix(matrix_path)
    if df is None:
        raise ValueError(f"Failed to load matrix: {matrix_path}")
    
    # Identify the sample ID column
    sample_col = None
    for col in ['sample_id', 'biosample_id', 'Sample_ID', 'Biosample_ID']:
        if col in df.columns:
            sample_col = col
            break
    
    if not sample_col:
        # Fallback: assume first column is ID
        sample_col = df.columns[0]
        logger.warning(f"Using first column '{sample_col}' as sample ID for {matrix_path.name}")
    
    return set(df[sample_col].astype(str).str.strip().tolist())

def find_processed_files() -> Tuple[Path, Path]:
    """
    Locates the expression and metabolite CSVs in the processed directory.
    """
    exp_file = None
    metab_file = None
    
    for f in PROCESSED_DIR.glob("*.csv"):
        name = f.name.lower()
        if "expression" in name:
            exp_file = f
        elif "metabolite" in name or "metabolomics" in name:
            metab_file = f
    
    if not exp_file:
        raise FileNotFoundError("No expression matrix found in data/processed/")
    if not metab_file:
        raise FileNotFoundError("No metabolite matrix found in data/processed/")
    
    return exp_file, metab_file

def run_pairing_integration_test():
    """
    Main integration test logic.
    """
    logger.info("Starting End-to-End Data Pairing Integration Test (T020)...")
    
    # 1. Locate input files
    try:
        exp_path, metab_path = find_processed_files()
        logger.info(f"Found Expression Matrix: {exp_path}")
        logger.info(f"Found Metabolite Matrix: {metab_path}")
    except FileNotFoundError as e:
        logger.error(f"Missing required data files. Ensure T021/T022 have run. Error: {e}")
        # In a CI context, this might be a skip or a fail depending on whether data is expected.
        # For this test, we fail loudly if data is missing.
        raise e

    # 2. Load sample IDs
    try:
        exp_ids = load_sample_ids_from_matrix(exp_path)
        metab_ids = load_sample_ids_from_matrix(metab_path)
        logger.info(f"Loaded {len(exp_ids)} expression samples and {len(metab_ids)} metabolite samples.")
    except Exception as e:
        logger.error(f"Failed to parse sample IDs: {e}")
        raise e

    if not exp_ids or not metab_ids:
        logger.error("One or both matrices are empty.")
        raise ValueError("Empty matrices provided.")

    # 3. Calculate Pairing
    matched_ids = exp_ids.intersection(metab_ids)
    unmatched_exp = exp_ids - matched_ids
    unmatched_metab = metab_ids - matched_ids
    
    total_samples = len(exp_ids)
    pairing_rate = len(matched_ids) / total_samples if total_samples > 0 else 0.0
    
    logger.info(f"Matched samples: {len(matched_ids)}/{total_samples} ({pairing_rate:.2%})")
    logger.info(f"Unmatched expression samples: {len(unmatched_exp)}")
    logger.info(f"Unmatched metabolite samples: {len(unmatched_metab)}")

    # 4. Log Mismatches (T026 requirement)
    if unmatched_exp or unmatched_metab:
        mismatches = []
        for uid in unmatched_exp:
            mismatches.append({
                "sample_id": uid,
                "expression_source": str(exp_path),
                "metabolite_source": str(metab_path),
                "reason": "no_sample_level_pair"
            })
        for uid in unmatched_metab:
            mismatches.append({
                "sample_id": uid,
                "expression_source": str(exp_path),
                "metabolite_source": str(metab_path),
                "reason": "no_sample_level_pair"
            })
        
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_data_pairing_mismatches_batch(mismatches, str(PAIRING_LOG_PATH))
        logger.info(f"Logged {len(mismatches)} mismatches to {PAIRING_LOG_PATH}")

    # 5. Validate Pairing Rate (T027 requirement)
    if pairing_rate < MIN_PAIRING_RATE:
        logger.error(f"Pairing rate {pairing_rate:.2%} is below threshold {MIN_PAIRING_RATE:.2%}.")
        logger.warning("Checking for fallback aggregation (T016b) - Not implemented in this test scope.")
        
        # Per T027: Halt with E-PAIRING if <95% and no valid fallback.
        # Since this is an integration test for the pairing logic itself, we simulate the abort.
        # In a real pipeline, T016b would run here. If T016b also fails, we raise.
        
        raise_pairing_error(
            f"Sample-level pairing rate ({pairing_rate:.2%}) is below 95% threshold. "
            "Project aborted per FR-009. Fallback aggregation not verified in this test."
        )
    
    logger.info("Integration Test PASSED: Pairing rate >= 95%.")
    return True

def main():
    """
    Entry point for the test script.
    """
    try:
        success = run_pairing_integration_test()
        if success:
            logger.info("T020 Integration Test: SUCCESS")
            sys.exit(0)
    except E_PAIRING as e:
        logger.error(f"T020 Integration Test: FAILED - {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"T020 Integration Test: FAILED - Missing Data - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"T020 Integration Test: FAILED - Unexpected Error - {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()