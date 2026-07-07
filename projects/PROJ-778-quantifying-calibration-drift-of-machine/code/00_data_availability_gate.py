"""
Data Availability Gate for Calibration Drift Analysis.

This script checks for the availability of required real-world datasets
(IPUMS CPS or valid synthetic configuration) as per FR-001 and Constitution Principle II.
It halts execution with a clear error if the primary data sources are missing
and no valid fallback configuration exists.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Tuple, Optional

# Import project utilities using the defined API surface
from utils.config import get_path, ensure_directories, get_config_dict


def check_ipums_cps_availability(config: dict) -> Tuple[bool, str]:
    """
    Checks if IPUMS CPS data is available or configured.

    Args:
        config: Configuration dictionary containing data paths.

    Returns:
        Tuple of (is_available: bool, message: str)
    """
    data_root = get_path("data/raw")
    required_dirs = ["cps", "adult"] # Adult is primary target per FR-001, CPS is fallback/alternative
    
    # Check for Adult dataset first (Primary target per FR-001)
    adult_path = data_root / "adult"
    if adult_path.exists() and any(adult_path.iterdir()):
        return True, f"UCI Adult dataset found at {adult_path}"

    # Check for IPUMS CPS configuration
    ipums_config_path = get_path("data/ipums_config.json")
    if ipums_config_path.exists():
        # Verify the config file is not empty
        if ipums_config_path.stat().st_size > 0:
            return True, f"IPUMS CPS configuration found at {ipums_config_path}. Data download required."
        else:
            return False, "IPUMS CPS configuration file exists but is empty."
    
    # Check for synthetic config as a last resort fallback (if explicitly allowed in config)
    # Note: Per FR-001, we should NOT proceed to synthetic data automatically in this gate.
    # We only check if a "synthetic_mode" flag is set to True in the main config.
    if config.get("allow_synthetic_fallback", False):
       return False, "No real data found. Synthetic fallback allowed by config, but gate halts to require explicit confirmation."

    return False, "No IPUMS CPS configuration or UCI Adult dataset found."


def check_synthetic_config(config: dict) -> Tuple[bool, str]:
    """
    Checks if a valid synthetic data generation configuration exists.
    
    Per FR-001, synthetic data is only a fallback if IPUMS is unavailable.
    This function validates the existence of the configuration file.

    Args:
        config: Configuration dictionary.

    Returns:
        Tuple of (is_available: bool, message: str)
    """
    synth_config_path = get_path("data/synthetic_config.yaml")
    if synth_config_path.exists() and synth_config_path.stat().st_size > 0:
        return True, f"Synthetic data configuration found at {synth_config_path}"
    return False, "No synthetic data configuration found."


def run_gate() -> int:
    """
    Main entry point for the data availability gate.
    
    Returns:
        0 if data is available, 1 if missing/halted.
    """
    parser = argparse.ArgumentParser(
        description="Check availability of required datasets for calibration drift analysis."
    )
    parser.add_argument(
        "--allow-synthetic",
        action="store_true",
        help="Allow synthetic data fallback if real data is missing (overrides FR-001 strict halt)."
    )
    args = parser.parse_args()

    # Load configuration
    config = get_config_dict()
    if args.allow_synthetic:
        config["allow_synthetic_fallback"] = True

    print("=== Data Availability Gate ===")
    print("Checking for required datasets (IPUMS CPS / UCI Adult)...")
    
    # 1. Check Primary Real Data Sources
    is_real_data_available, real_msg = check_ipums_cps_availability(config)
    
    if is_real_data_available:
        print(f"[OK] {real_msg}")
        print("Proceeding with real data pipeline.")
        return 0
    
    print(f"[WARN] {real_msg}")

    # 2. Check Fallback Options (Only if explicitly configured)
    if config.get("allow_synthetic_fallback", False):
        is_synth_available, synth_msg = check_synthetic_config(config)
        if is_synth_available:
            print(f"[INFO] {synth_msg}")
            print("[WARN] Scope Reduction: Proceeding with synthetic data due to missing real data.")
            print("[WARN] This deviates from FR-001 primary targets. Ensure this is authorized.")
            return 0
        
        print(f"[WARN] {synth_msg}")

    # 3. Halt if nothing is available
    print("\n" + "="*50)
    print("CRITICAL ERROR: Required data sources missing.")
    print("="*50)
    print("The pipeline cannot proceed without real data (IPUMS CPS or UCI Adult).")
    print("To fix this:")
    print("1. Download the UCI Adult dataset (1994-2022 snapshots) and place in data/raw/adult/")
    print("2. OR configure IPUMS CPS access in data/ipums_config.json")
    print("3. OR run with --allow-synthetic if authorized to use synthetic fallback.")
    print("\nHalting execution to prevent invalid research results.")
    
    return 1


if __name__ == "__main__":
    sys.exit(run_gate())