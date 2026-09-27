"""
T095: Mode Gate Implementation.

Enforces DATA_MODE and the "fail loudly" constraint.

Logic:
1. If DATA_MODE='real', verify real MFQ/Stories sources (T054b) and VR logs (T054c-Verify) are available.
2. If DATA_MODE='real' and MFQ/Stories are missing, raise ConnectionError immediately.
3. If DATA_MODE='real' and MFQ/Stories exist but VR logs are missing:
   - HARD FAIL: Raise SystemExit with message "FR-006 Violation: Real VR logs missing..."
4. If DATA_MODE='simulation':
   - CHECK AMENDMENT: Verify spec_amendment_FR006.md exists (T090 template).
   - If file exists, log deviation and allow.
   - If file is missing, log warning but allow (per Plan.md "Resolved" status).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Import from existing API surface
from code.config import get_path, DATA_MODE, FORMAL_DEVIATION_VR_LOGS

# Constants for file paths
MFQ_REAL_PATH = "data/raw/mfq_real.csv"
STORIES_REAL_PATH = "data/raw/stories_real.csv"
VR_LOGS_REAL_PATH = "data/raw/vr_logs_real.csv"
SPEC_AMENDMENT_PATH = "specs/001-the-cognitive-mechanisms-underlying-intu/spec_amendment_FR006.md"

def check_mode_and_data() -> bool:
    """
    Enforce the mode gate logic.
    
    Returns:
        bool: True if the mode is valid and data requirements are met (or simulation is allowed).
        
    Raises:
        ConnectionError: If DATA_MODE='real' but MFQ or Stories are missing.
        SystemExit: If DATA_MODE='real' but VR logs are missing (FR-006 Violation).
    """
    print(f"Checking data mode: {DATA_MODE}")
    
    if DATA_MODE == 'simulation':
        # Simulation Mode
        amendment_path = get_path(SPEC_AMENDMENT_PATH)
        if not amendment_path.exists():
            print(f"WARNING: Spec Amendment T090 ({SPEC_AMENDMENT_PATH}) is missing.")
            print("Simulation mode is allowed per Plan.md 'Resolved' status, but formal approval is pending.")
        else:
            print(f"Spec Amendment T090 found at {amendment_path}. Deviation authorized.")
        return True

    elif DATA_MODE == 'real':
        # Real Mode - Strict Checks
        
        # 1. Check MFQ and Stories
        mfq_path = get_path(MFQ_REAL_PATH)
        stories_path = get_path(STORIES_REAL_PATH)
        
        if not mfq_path.exists():
            raise ConnectionError(f"Real Data Mode: MFQ data missing at {mfq_path}. Ensure T054b completed.")
        
        if not stories_path.exists():
            raise ConnectionError(f"Real Data Mode: Moral Stories data missing at {stories_path}. Ensure T054b completed.")
        
        print("Real MFQ and Stories data verified.")
        
        # 2. Check VR Logs (The Critical Gate)
        vr_logs_path = get_path(VR_LOGS_REAL_PATH)
        
        if not vr_logs_path.exists():
            # HARD FAIL: FR-006 Violation
            error_msg = (
                "FR-006 Violation: Real VR logs missing. "
                f"Expected at {vr_logs_path}. "
                "Spec Amendment T090 is required to enable simulation mode. "
                "Please complete T090 before proceeding or set DATA_MODE='simulation' in config."
            )
            print(f"ERROR: {error_msg}")
            raise SystemExit(error_msg)
        
        print("Real VR logs verified. Proceeding with Real Data Mode.")
        return True

    else:
        raise ValueError(f"Invalid DATA_MODE: '{DATA_MODE}'. Must be 'real' or 'simulation'.")

def main():
    """Entry point for the gate script."""
    try:
        check_mode_and_data()
        print("Mode Gate Check PASSED.")
        sys.exit(0)
    except ConnectionError as e:
        print(f"MODE GATE FAILED (ConnectionError): {e}")
        sys.exit(1)
    except SystemExit as e:
        # Re-raise SystemExit to ensure the process stops with the error code
        raise
    except Exception as e:
        print(f"MODE GATE FAILED (Unexpected Error): {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()