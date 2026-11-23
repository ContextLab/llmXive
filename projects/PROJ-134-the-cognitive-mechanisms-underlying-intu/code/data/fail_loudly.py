"""
T096: Real Data Fail-Loud Gate.

Enforces the "fail loudly" constraint for Real Data Mode specifically regarding VR logs.
If DATA_MODE='real' and no real VR logs are found, raises SystemExit with a clear error message.
This ensures FR-006 is satisfied by explicitly failing rather than silently falling back.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Import from existing API surface
from code.config import get_path, DATA_MODE
from code.data.verify_vr_data import check_vr_data_availability

# Constants
VR_LOGS_PATH_KEY = "data/raw/vr_logs_real.csv"
VR_LOGS_DATASET_ID = "moral-foundations/vr-logs-v"

def check_real_vr_data() -> bool:
    """
    Checks for the existence of real VR logs.
    
    Returns:
        bool: True if VR logs exist, False otherwise.
    
    Raises:
        SystemExit: If DATA_MODE is 'real' and VR logs are missing.
    """
    # First, perform the availability check (which only warns if missing)
    is_available = check_vr_data_availability()
    
    if not is_available:
        # If the check indicates data is not available
        if DATA_MODE == "real":
            # HARD FAIL: Real VR logs are missing in Real Mode
            error_msg = (
                f"FR-006 Violation: Real VR logs missing. "
                f"Dataset '{VR_LOGS_DATASET_ID}' not found or inaccessible. "
                f"DATA_MODE is set to 'real'. "
                f"Please complete T092 (Real VR Log Ingestion) or switch DATA_MODE to 'simulation' "
                f"after completing T090 (Spec Amendment)."
            )
            raise SystemExit(error_msg)
        else:
            # Simulation mode: VR logs are not required, just log and return
            return False
    
    # Data is available
    return True

def main() -> None:
    """
    Main entry point for the fail-loud gate.
    """
    print("Executing T096: Real Data Fail-Loud Gate...")
    print(f"Current DATA_MODE: {DATA_MODE}")
    
    try:
        check_real_vr_data()
        print("SUCCESS: Real VR data check passed (or mode is simulation).")
        sys.exit(0)
    except SystemExit as e:
        print(f"FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during check: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()