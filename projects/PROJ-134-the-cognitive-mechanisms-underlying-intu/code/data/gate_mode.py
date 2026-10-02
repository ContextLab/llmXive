"""
T095: Mode Gate Implementation.

Enforces DATA_MODE and the "fail loudly" constraint.

Logic:
1. If DATA_MODE='real':
   - Attempt to fetch/verify Real MFQ/Stories (T054b) and VR logs (T092).
   - If MFQ/Stories missing: raise ConnectionError immediately.
   - If VR logs missing: raise RealDataUnavailableError immediately (FR-006 Violation).
   - DO NOT check T090 in this path. Real data is mandatory.
2. If DATA_MODE='simulation':
   - CHECK AMENDMENT: Verify file `specs/.../spec_amendment_FR006.md` exists (T090).
   - CHECK CONFIG: Verify `code/config.py` has `ENABLE_SIMULATION = True`.
   - CHECK STATUS: Verify file contains "APPROVED".
   - If all checks pass: log deviation and allow simulation.
   - If any check fails: raise RealDataUnavailableError.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Import from existing API surface
from code.config import get_path, DATA_MODE, ENABLE_SIMULATION
from code.data.exceptions import RealDataUnavailableError

# Constants for file paths
MFQ_REAL_PATH = "data/raw/mfq_real.csv"
STORIES_REAL_PATH = "data/raw/stories_real.csv"
VR_LOGS_REAL_PATH = "data/raw/vr_logs_real.parquet"
SPEC_AMENDMENT_PATH = "specs/001-the-cognitive-mechanisms-underlying-intu/spec_amendment_FR006.md"

def check_mode_and_data() -> bool:
    """
    Enforce the mode gate logic.
    
    Returns:
        bool: True if the mode is valid and data requirements are met (or simulation is allowed).
            
    Raises:
        ConnectionError: If DATA_MODE='real' but MFQ or Stories are missing.
        RealDataUnavailableError: If DATA_MODE='real' and VR logs are missing,
                                  OR if DATA_MODE='simulation' but T090 is invalid.
    """
    print(f"Checking data mode: {DATA_MODE}")
    
    if DATA_MODE == 'simulation':
        # Simulation Mode
        # 1. Check Config Flag
        if not ENABLE_SIMULATION:
            error_msg = (
                "Spec Amendment T090 is missing or not approved. "
                "Simulation mode is not authorized. "
                "Set ENABLE_SIMULATION = True in code/config.py and ensure T090 is APPROVED."
            )
            print(f"ERROR: {error_msg}")
            raise RealDataUnavailableError(error_msg)
        
        # 2. Check Amendment File Existence
        amendment_path = get_path(SPEC_AMENDMENT_PATH)
        if not amendment_path.exists():
            error_msg = (
                f"Spec Amendment T090 file not found at {amendment_path}. "
                "Simulation mode is not authorized without the draft document."
            )
            print(f"ERROR: {error_msg}")
            raise RealDataUnavailableError(error_msg)
        
        # 3. Check Amendment Status
        try:
            with open(amendment_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "APPROVED" not in content:
                    error_msg = (
                        f"Spec Amendment T090 at {amendment_path} does not contain 'APPROVED'. "
                        "Simulation mode is not authorized."
                    )
                    print(f"ERROR: {error_msg}")
                    raise RealDataUnavailableError(error_msg)
        except Exception as e:
            error_msg = f"Failed to read Spec Amendment T090: {e}"
            print(f"ERROR: {error_msg}")
            raise RealDataUnavailableError(error_msg)
        
        print(f"Spec Amendment T090 verified. Deviation authorized.")
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
        # Note: T092 is responsible for fetching this. If it doesn't exist, we fail loudly.
        vr_logs_path = get_path(VR_LOGS_REAL_PATH)
        
        if not vr_logs_path.exists():
            # HARD FAIL: FR-006 Violation
            error_msg = (
                "FR-006 Violation: Real VR logs missing. Fetch failed. "
                f"Expected at {vr_logs_path}. "
                "Real data is mandatory in 'real' mode."
            )
            print(f"ERROR: {error_msg}")
            raise RealDataUnavailableError(error_msg)
        
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
    except RealDataUnavailableError as e:
        print(f"MODE GATE FAILED (RealDataUnavailableError): {e}")
        sys.exit(1)
    except Exception as e:
        print(f"MODE GATE FAILED (Unexpected Error): {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()
