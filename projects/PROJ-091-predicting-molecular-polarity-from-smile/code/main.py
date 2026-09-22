import sys
import os
import argparse
import logging
import gc
import json
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logging_config import setup_logging, get_logger
from utils.validators import assert_no_3d_calls, validate_dataset_schema
from utils.checksums import compute_file_checksum
from data.preprocess_2d import preprocess_2d, main as preprocess_main
from data.save_descriptors import save_descriptors, main as save_main
from data.validate import validate_processed_descriptors, main as validate_main
from data.loader import iterate_smiles
from utils.config import get_config_summary

logger = None

def check_prerequisites():
    """Verify basic project structure and config."""
    global logger
    logger = get_logger("main")
    logger.info("Checking prerequisites...")
    
    # Check directories
    dirs = ["code", "tests", "data", "data/raw", "data/processed", "data/processed/analysis", "logs", "state"]
    for d in dirs:
        path = PROJECT_ROOT / d
        if not path.exists():
            logger.error(f"Directory missing: {path}")
            return False
    
    # Check config
    config_summary = get_config_summary()
    if not config_summary:
        logger.error("Failed to load configuration")
        return False
    
    logger.info("Prerequisites check passed.")
    return True

def validate_2d_compliance():
    """
    Verify that the pipeline execution (specifically descriptor computation)
    does not contain 3D conformer generation calls.
    Uses the shared validator from code/utils/validators.py.
    """
    global logger
    logger = get_logger("main")
    logger.info("Validating 2D-only compliance...")

    # Read the source code of the descriptor computation module
    preprocess_path = PROJECT_ROOT / "code" / "data" / "preprocess_2d.py"
    if not preprocess_path.exists():
        logger.error(f"Preprocessing script not found: {preprocess_path}")
        return False

    code_str = preprocess_path.read_text(encoding="utf-8")
    
    # Call the validator. The validator is designed to accept a string of code
    # to inspect for forbidden 3D functions (e.g., EmbedMolecule, Get3DConformer).
    try:
        if not assert_no_3d_calls(code_str):
            logger.critical("2D-only compliance check FAILED: 3D calls detected in code.")
            return False
        logger.info("2D-only compliance check PASSED.")
        return True
    except Exception as e:
        logger.error(f"Error during 2D compliance check: {e}")
        return False

def validate_descriptors_file():
    """
    Verify that the processed descriptors file exists and matches the expected schema.
    Uses the schema validators from T006.
    """
    global logger
    logger = get_logger("main")
    logger.info("Validating descriptors file...")

    descriptors_path = PROJECT_ROOT / "data" / "processed" / "descriptors.parquet"
    if not descriptors_path.exists():
        logger.error(f"Descriptors file not found: {descriptors_path}")
        return False

    # Call the validator from utils.validators
    # This function checks for required columns (smiles, target) and dynamic desc_* columns
    try:
        if not validate_dataset_schema(str(descriptors_path)):
            logger.critical("Schema validation FAILED for descriptors file.")
            return False
        logger.info("Schema validation PASSED for descriptors file.")
        return True
    except Exception as e:
        logger.error(f"Error during schema validation: {e}")
        return False

def validate_artifact_integrity():
    """
    [FR-003] Verify that critical artifacts have not been modified since generation.
    Reads state/manifest.json and compares file checksums against stored values.
    """
    global logger
    logger = get_logger("main")
    logger.info("Validating artifact integrity (checksums)...")

    manifest_path = PROJECT_ROOT / "state" / "manifest.json"
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return False

    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read manifest: {e}")
        return False

    if "checksums" not in manifest:
        logger.error("Manifest missing 'checksums' key.")
        return False

    checksums = manifest["checksums"]
    success = True

    # Define expected artifacts and their keys in manifest
    expected_artifacts = {
        "data/processed/descriptors.parquet": "descriptors_parquet",
        "data/processed/cluster_map.csv": "cluster_map_csv"
    }

    for rel_path, key in expected_artifacts.items():
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            logger.error(f"Artifact missing for integrity check: {full_path}")
            success = False
            continue

        if key not in checksums:
            logger.error(f"Checksum missing in manifest for {key}")
            success = False
            continue

        expected_hash = checksums[key]
        try:
            current_hash = compute_file_checksum(str(full_path))
            if current_hash != expected_hash:
                logger.critical(f"INTEGRITY FAILURE: {rel_path} hash mismatch.")
                logger.critical(f"  Expected: {expected_hash}")
                logger.critical(f"  Current:  {current_hash}")
                success = False
            else:
                logger.info(f"Integrity OK: {rel_path}")
        except Exception as e:
            logger.error(f"Error computing checksum for {rel_path}: {e}")
            success = False

    return success

def run_data_preprocessing():
    """Run the data preprocessing pipeline."""
    global logger
    logger = get_logger("main")
    logger.info("Running data preprocessing...")
    
    # This invokes the logic in preprocess_2d.py which downloads (if needed),
    # computes descriptors, handles NaNs, and saves to data/processed/descriptors.parquet
    try:
        preprocess_main()
        return True
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        return False

def run_pipeline():
    """Execute the full pipeline with runtime assertions."""
    global logger
    
    # 1. Check Prerequisites
    if not check_prerequisites():
        return False

    # 2. Validate 2D Compliance (Runtime Assertion on Code)
    if not validate_2d_compliance():
        return False

    # 3. Run Data Preprocessing (Produces descriptors.parquet)
    if not run_data_preprocessing():
        return False

    # 4. Validate Output File (Runtime Assertion on Data)
    # This ensures the file produced in step 3 matches the schema defined in T006
    if not validate_descriptors_file():
        return False

    # 5. Validate Artifact Integrity (T049)
    # Verifies that descriptors.parquet and cluster_map.csv match the manifest (T049a)
    if not validate_artifact_integrity():
        logger.critical("Artifact integrity check failed. Data may have been tampered with or regenerated inconsistently.")
        return False

    logger.info("Pipeline execution completed successfully with all assertions passed.")
    return True

def main():
    global logger
    parser = argparse.ArgumentParser(description="Main pipeline orchestrator")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    args = parser.parse_args()

    # Setup logging
    setup_logging(level=logging.INFO)
    logger = get_logger("main")
    logger.info("Starting pipeline...")

    success = run_pipeline()

    if success:
        logger.info("Pipeline finished successfully.")
        sys.exit(0)
    else:
        logger.error("Pipeline failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()