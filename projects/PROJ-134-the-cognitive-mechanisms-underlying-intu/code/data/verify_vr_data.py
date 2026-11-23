"""
T054c-Verify: Real VR Data Gate.

This script verifies the absence of real VR logs (as they are not available in public
repositories for this specific experimental design) and triggers the formal deviation
path if DATA_MODE='real'.

Per the project specification (FR-006 deviation):
- If DATA_MODE='real' and real VR logs are missing, raise ConnectionError.
- If DATA_MODE='simulation', log a warning and proceed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.config import get_path, load_yaml_config, DATA_MODE, FORMAL_DEVIATION_VR_LOGS


def check_vr_data_availability() -> bool:
    """
    Check if real VR logs are available.

    Since the specific VR logs for this study (PROJ-134) do not exist in public
    repositories (OSF/HF), this function simulates the check for the canonical
    dataset ID defined in T050.

    Returns:
        True if data exists (unlikely), False if missing.
    """
    # The canonical dataset ID defined in T050 for VR logs
    # This dataset does not exist, so we expect this to fail or return empty.
    # We check for a local file that would represent a successful download,
    # or attempt to verify the remote source.
    # Since we cannot fetch non-existent data, we check for the local artifact
    # that T054b would have created if it existed (it won't).
    
    # Check for the expected local path if it were downloaded
    expected_local_path = get_path("data/raw/vr_logs_real.csv")
    if expected_local_path.exists():
        return True

    # Attempt to verify the remote source (HuggingFace)
    # We use a simple check: try to import datasets and list the dataset
    try:
        from datasets import load_dataset
        # The specific dataset ID defined in T050 (hypothetical)
        hf_dataset_id = "moral-foundations/vr-logs-v1" 
        
        # We try to load just the info to see if it exists
        # This will raise an error if the dataset does not exist
        ds = load_dataset(hf_dataset_id, split="train", streaming=True)
        # If we get here, the dataset exists. Try to peek.
        next(iter(ds))
        return True
    except Exception:
        # Dataset does not exist or is unreachable
        return False


def verify_vr_data_gate() -> None:
    """
    Enforce the Real Data Gate for VR logs.

    Logic:
    1. If DATA_MODE is 'simulation', log a warning and return.
    2. If DATA_MODE is 'real':
       a. Check if FORMAL_DEVIATION_VR_LOGS is True. If so, log warning and return.
       b. Check if real VR data is available.
       c. If NOT available, raise ConnectionError with the specific FR-006 violation message.
    """
    logger = logging.getLogger(__name__)
    
    # Import logging here to avoid circular import if config uses logging
    import logging

    logger.info(f"Checking VR data availability in {DATA_MODE} mode...")

    if DATA_MODE == 'simulation':
        logger.warning("DATA_MODE is 'simulation'. Skipping real VR data check.")
        return

    # We are in 'real' mode
    if FORMAL_DEVIATION_VR_LOGS:
        logger.warning(
            "FORMAL_DEVIATION_VR_LOGS is True. Proceeding with simulation data for VR logs "
            "despite DATA_MODE='real'. This is a documented deviation from FR-006."
        )
        return

    # Check availability
    if not check_vr_data_availability():
        error_msg = (
            "FR-006 Violation: Real VR logs missing. "
            "Switch DATA_MODE to 'simulation' manually or set FORMAL_DEVIATION_VR_LOGS=True in config."
        )
        logger.error(error_msg)
        raise ConnectionError(error_msg)

    logger.info("Real VR logs found. Proceeding.")


def main() -> None:
    """Entry point for T054c-Verify."""
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        verify_vr_data_gate()
        print("VR Data Gate Check: PASSED (or Deviation Allowed)")
    except ConnectionError as e:
        print(f"VR Data Gate Check: FAILED - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
