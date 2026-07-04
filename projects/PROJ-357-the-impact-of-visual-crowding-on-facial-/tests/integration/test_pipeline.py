"""
Integration test for the full visual crowding stimuli generation pipeline (US1).

This test verifies the end-to-end flow:
1. Configuration and directory setup.
2. Data download (RAVDESS).
3. Frame extraction.
4. Stimulus generation (with overlap detection).
5. Manifest generation and validation.

It asserts that output artifacts exist and contain valid data structures.
"""
import os
import sys
import json
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import set_all_seeds, ensure_directories, get_env_config
from utils.download import fetch_ravdess_dataset
from utils.frame_extractor import extract_frames_from_dataset
from utils.stimulus_gen import generate_stimuli
from utils.stimuli_manifest import generate_manifest
from utils.manifest_validator import validate_manifest_completeness, generate_validation_report

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration_test_pipeline")

def run_integration_test():
    """
    Executes the full pipeline and asserts success.
    """
    logger.info("Starting Integration Test for US1 (Stimuli Generation Pipeline)")
    
    # 1. Setup: Configuration and Directories
    logger.info("Step 1: Configuring environment and directories...")
    set_all_seeds(42)
    env_config = get_env_config()
    
    # Use temporary directory for the test run to avoid cluttering data/ in CI
    # In a real run, this would use the actual project data paths
    test_data_root = Path(tempfile.mkdtemp(prefix="ravdess_integration_test_"))
    logger.info(f"Using temporary data root: {test_data_root}")
    
    # Override config paths for this test
    env_config['data_root'] = str(test_data_root)
    env_config['raw_dir'] = str(test_data_root / "raw")
    env_config['interim_dir'] = str(test_data_root / "interim")
    env_config['frames_dir'] = str(test_data_root / "raw" / "frames")
    env_config['stimuli_dir'] = str(test_data_root / "interim" / "stimuli")
    
    ensure_directories(
        raw_dir=env_config['raw_dir'],
        frames_dir=env_config['frames_dir'],
        stimuli_dir=env_config['stimuli_dir']
    )

    # 2. Download: Fetch RAVDESS (or simulate if not available)
    logger.info("Step 2: Fetching RAVDESS dataset...")
    try:
        fetch_ravdess_dataset(env_config['raw_dir'])
    except Exception as e:
        # If download fails (e.g., no internet or missing credentials), 
        # we check if we can proceed with a minimal subset or fail gracefully.
        # For this integration test, we assume the download function handles 
        # the "missing data" case by raising a clear error or creating a 
        # minimal structure if the dataset is already present.
        # If the directory is empty, the subsequent steps will fail, which is expected.
        if not Path(env_config['raw_dir']).exists():
            logger.error("Failed to create raw data directory. Pipeline cannot proceed.")
            return False
        logger.warning("Download step encountered an issue, proceeding to check existing data.")

    # 3. Frame Extraction
    logger.info("Step 3: Extracting frames from videos...")
    try:
        extract_frames_from_dataset(env_config['raw_dir'], env_config['frames_dir'])
    except Exception as e:
        logger.error(f"Frame extraction failed: {e}")
        return False

    # 4. Stimulus Generation
    logger.info("Step 4: Generating stimuli with crowding parameters...")
    # Define a minimal set of parameters for the integration test to run quickly
    test_params = {
        "emotions": ["happy", "sad"],  # Limit to 2 for speed
        "flanker_counts": [3, 5],      # 2 levels
        "eccentricities": [5.0, 10.0], # 2 levels
        "max_stimuli_per_combo": 2     # Limit total count
    }
    
    try:
        generate_stimuli(
            frames_dir=env_config['frames_dir'],
            output_dir=env_config['stimuli_dir'],
            emotions=test_params['emotions'],
            flanker_counts=test_params['flanker_counts'],
            eccentricities=test_params['eccentricities'],
            max_per_combo=test_params['max_stimuli_per_combo']
        )
    except Exception as e:
        logger.error(f"Stimulus generation failed: {e}")
        return False

    # 5. Manifest Generation
    logger.info("Step 5: Generating stimuli manifest...")
    try:
        manifest_path = generate_manifest(env_config['stimuli_dir'])
        if not manifest_path.exists():
            logger.error("Manifest file was not created.")
            return False
    except Exception as e:
        logger.error(f"Manifest generation failed: {e}")
        return False

    # 6. Manifest Validation
    logger.info("Step 6: Validating manifest completeness...")
    try:
        is_valid, report = validate_manifest_completeness(manifest_path)
        if not is_valid:
            logger.error(f"Manifest validation failed: {report}")
            return False
        
        # Generate detailed report
        report_path = generate_validation_report(manifest_path)
        logger.info(f"Validation report generated at: {report_path}")
        
    except Exception as e:
        logger.error(f"Manifest validation failed: {e}")
        return False

    # Final Assertions
    logger.info("Step 7: Verifying output artifacts...")
    
    # Check for stimuli files
    stimuli_files = list(Path(env_config['stimuli_dir']).glob("*.png"))
    if len(stimuli_files) == 0:
        logger.error("No stimuli images were generated.")
        return False
    
    # Check manifest content
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    if len(manifest_data) == 0:
        logger.error("Manifest is empty.")
        return False

    # Verify required fields in manifest entries
    required_fields = ['file_path', 'emotion', 'flanker_count', 'eccentricity', 'status']
    for entry in manifest_data:
        for field in required_fields:
            if field not in entry:
                logger.error(f"Missing required field '{field}' in manifest entry: {entry}")
                return False
        
        # Verify flanker_count and eccentricity are numeric
        if not isinstance(entry['flanker_count'], (int, float)):
            logger.error(f"flanker_count is not numeric: {entry['flanker_count']}")
            return False
        if not isinstance(entry['eccentricity'], (int, float)):
            logger.error(f"eccentricity is not numeric: {entry['eccentricity']}")
            return False

    logger.info("Integration Test PASSED: All pipeline steps completed successfully.")
    
    # Cleanup
    shutil.rmtree(test_data_root)
    logger.info(f"Cleaned up temporary directory: {test_data_root}")
    
    return True

def main():
    success = run_integration_test()
    if not success:
        logger.error("Integration Test FAILED.")
        sys.exit(1)
    else:
        logger.info("Integration Test SUCCESS.")
        sys.exit(0)

if __name__ == "__main__":
    main()