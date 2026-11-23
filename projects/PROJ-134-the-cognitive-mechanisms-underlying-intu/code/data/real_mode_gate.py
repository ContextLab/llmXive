"""
T069: Real Data Mode Gate Implementation.

This task implements the logic previously assigned to T069 (Real Data Mode Gate)
by consolidating the gate logic into this dedicated module. It enforces the
'Real Data Only' constraint per T043 and T054b/T054c requirements.

Logic:
1. If DATA_MODE='real', verify real MFQ/Stories sources (T054b) and VR logs (T054c).
2. If MFQ/Stories missing in 'real' mode -> Raise ConnectionError immediately.
3. If VR logs missing in 'real' mode:
   - If config.FORMAL_DEVIATION_VR_LOGS is False -> Raise ConnectionError.
   - If config.FORMAL_DEVIATION_VR_LOGS is True -> Log warning and proceed (simulation allowed for VR).
4. If DATA_MODE='simulation', log deviation and allow simulation.

This module replaces the removed T069 task and serves as the central gate for
data mode enforcement.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

# Import from existing modules to avoid circular dependencies
from code.config import get_path, load_yaml_config
from code.data.ingest_real import OSF_API_URL, HF_DATASET_ID, VR_LOG_SCHEMA_COLUMNS

# Constants
CONFIG_PATH = "data/config/deviation_config.yaml"
STATE_PATH = "state"
DATA_RAW_PATH = "data/raw"

def check_real_data_mode() -> bool:
    """
    Enforce DATA_MODE and the 'fail loudly' constraint.
    
    Returns:
        bool: True if the mode is valid and data is available (or allowed to proceed).
        
    Raises:
        ConnectionError: If real data is missing in 'real' mode and not allowed to deviate.
        FileNotFoundError: If config files are missing.
    """
    config_path = get_path(CONFIG_PATH)
    state_path = get_path(STATE_PATH)
    
    # Load configuration
    if not config_path.exists():
        # If config missing, assume strict mode (no deviation allowed)
        formal_deviation_vr_logs = False
    else:
        config = load_yaml_config(config_path)
        formal_deviation_vr_logs = config.get("FORMAL_DEVIATION_VR_LOGS", False)
    
    # Determine current mode (from environment or config)
    # Default to 'real' per T043
    data_mode = os.getenv("DATA_MODE", "real")
    
    if data_mode == "simulation":
        print("WARNING: Running in SIMULATION mode. Real data sources skipped.")
        return True
    
    if data_mode != "real":
        raise ValueError(f"Invalid DATA_MODE: '{data_mode}'. Must be 'real' or 'simulation'.")
    
    # --- REAL MODE CHECKS ---
    print("Checking real data availability in REAL MODE...")
    
    # 1. Check MFQ and Stories (MANDATORY per FR-001)
    mfq_path = get_path(DATA_RAW_PATH, "mfq_real.csv")
    stories_path = get_path(DATA_RAW_PATH, "stories_real.csv")
    
    if not mfq_path.exists():
        raise ConnectionError(
            f"FR-001 Violation: Real MFQ data missing at {mfq_path}. "
            "Ensure T054b (fetch_real.py) has completed successfully. "
            "Switch DATA_MODE to 'simulation' manually if real data is unavailable."
        )
    
    if not stories_path.exists():
        raise ConnectionError(
            f"FR-001 Violation: Real Moral Stories data missing at {stories_path}. "
            "Ensure T054b (fetch_real.py) has completed successfully. "
            "Switch DATA_MODE to 'simulation' manually if real data is unavailable."
        )
    
    print("✓ Real MFQ and Stories data found.")
    
    # 2. Check VR Logs (FR-006 - Partially Deferred)
    vr_logs_path = get_path(DATA_RAW_PATH, "vr_logs_real.csv")
    
    if not vr_logs_path.exists():
        if not formal_deviation_vr_logs:
            raise ConnectionError(
                f"FR-006 Violation: Real VR logs missing at {vr_logs_path}. "
                "Switch DATA_MODE to 'simulation' manually or set "
                "FORMAL_DEVIATION_VR_LOGS=True in config to allow simulation fallback."
            )
        else:
            print("WARNING: Real VR logs missing. Proceeding with simulation fallback (Deviation Allowed).")
    else:
        print("✓ Real VR logs found.")
    
    return True

def main():
    """Entry point for the gate check."""
    try:
        check_real_data_mode()
        print("Real Data Mode Gate: PASSED")
        return 0
    except (ConnectionError, FileNotFoundError, ValueError) as e:
        print(f"Real Data Mode Gate: FAILED - {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()