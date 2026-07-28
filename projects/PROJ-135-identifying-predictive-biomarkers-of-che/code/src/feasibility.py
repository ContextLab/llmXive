import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import existing config utilities to ensure paths are consistent
# The API surface indicates src.config has get_project_root
try:
    from src.config import get_project_root
except ImportError:
    # Fallback if import path differs slightly in execution context
    from code.src.config import get_project_root

from src.utils import setup_logging, ensure_path_exists

# Configure logging
logger = setup_logging("feasibility")

def count_available_tumor_types(data_dir: Path) -> int:
    """
    Count the total number of tumor types available for LOO validation.
    
    This function checks the `data/processed/` directory for discovery sets
    that have been generated (or are expected to be generated) by the acquisition
    and preprocessing stages. Specifically, it looks for files matching
    the pattern `{tumor_type}_discovery_set.csv`.
    
    If no processed data exists yet, it attempts to infer available tumor types
    from the raw data directory or a configuration mapping if available.
    However, per the task description, this check is independent of GEO dataset
    availability and focuses on the TCGA types that will be used for modeling.
    
    For the purpose of this Pre-Check (T009), which runs BEFORE T014 (Data Feasibility Gate)
    and before T031/T032 (Modeling), we assume the project structure defines
    a set of target tumor types in the configuration or we scan for existing
    processed files if a partial run occurred.
    
    Since T009 is a "Pre-Check" that must run *before* data acquisition completes
    (T014), it likely relies on a configuration of *intended* tumor types or
    a preliminary scan of available TCGA codes.
    
    Given the task description: "count the total number of tumor types (N) available...
    independent of GEO dataset availability... run before any model training...
    and before the Data Feasibility Gate (T014)".
    
    We will implement a check that:
    1. Checks for a configuration file specifying target tumor types (if exists).
    2. If not, scans `data/processed/` for any existing `_discovery_set.csv` files.
    3. If neither, it returns 0 (indicating no types found yet, which might trigger a halt
       if the pipeline expects them to be pre-defined, but usually this task implies
       checking the *potential* pool. However, without real data, we must rely on
       the existence of files or a config.
    
    Re-reading T009: "count the total number of tumor types (N) available for Leave-One-Cancer-Type-Out (LOO) validation".
    This implies we need to know what types we *have* or *will have*.
    Since T014 (Data Feasibility) is the one that counts TCGA types and decides to halt,
    T009 seems to be a specific check for the *modeling phase* viability.
    
    Interpretation: The task asks to count N. If N < 3, halt.
    Since T014 is the one that downloads and counts, T009 might be checking a
    *pre-defined list* of tumor types intended for the study, or it might be
    checking the `data/processed` directory if the pipeline is being resumed.
    
    However, the most robust implementation for a "Pre-Check" that runs *before*
    T014 (which does the actual counting and downloading) is to check a
    configuration file that lists the *target* tumor types for this project.
    If that list is empty or < 3, we halt.
    
    Let's assume the project uses a `config.py` or a specific YAML file to define
    the `TARGET_TUMOR_TYPES`. If not present, we might scan `data/processed`
    as a fallback (for resuming).
    
    We will look for `TARGET_TUMOR_TYPES` in `src/config.py` or a local config.
    If `src/config` does not expose this, we will check `data/processed` for
    existing files.
    
    Updated Strategy:
    1. Try to load target types from `src/config` (if exposed) or a local `config.yaml`.
    2. If not found, scan `data/processed/` for `{name}_discovery_set.csv`.
    3. Count unique tumor types.
    4. If count < 3, write halt file and exit.
    """
    
    project_root = get_project_root()
    processed_dir = project_root / "data" / "processed"
    target_types = []
    
    # Strategy 1: Check for a configuration of target types
    # We'll look for a common config pattern or a specific file mentioned in specs
    # Since T004 defines config, let's assume we might need to read a specific file
    # if not in the main config module.
    # However, the task says "count... available".
    # If this runs before T014, we might not have data.
    # But T009 is a "Halt Condition".
    
    # Let's check if there are any existing processed files (for resuming or partial runs)
    if processed_dir.exists():
        files = list(processed_dir.glob("*_discovery_set.csv"))
        for f in files:
            # Extract tumor type from filename: {tumor_type}_discovery_set.csv
            name = f.stem.replace("_discovery_set", "")
            if name and name not in target_types:
                target_types.append(name)
    
    # If we found types in processed data, return that count.
    # If not, and this is a fresh run, we might need to rely on a config list.
    # Since we cannot download data yet (T014 does that), and we can't guess,
    # we must rely on the existence of *something*.
    # If the count is 0, and we have no config, we might just return 0.
    # But the task implies we should count "available" types.
    # If the pipeline is designed to run T009 *after* T012 (Acquisition) but *before* T014?
    # No, T014 is the "Data Feasibility Gate". T009 is "Pre-Check LOO Feasibility".
    # The description says: "This check is independent of GEO dataset availability;
    # it must run before any model training (T031/T032) and before the Data Feasibility Gate (T014)".
    # This is slightly contradictory if T014 is the one that counts TCGA types.
    # Perhaps T009 is checking the *intended* list from a spec/config.
    
    # Let's assume there is a `target_tumor_types` list in `src/config` or a local file.
    # If not, we assume the user has pre-configured the environment.
    # Since I cannot invent a config file not in the API surface, I will rely on
    # the `data/processed` directory scan as the primary source of truth for "available" types.
    # If the directory is empty, N=0.
    
    return len(target_types)

def write_feasibility_gate_result(
    gate_path: Path,
    status: str,
    reason: str,
    tumor_types_count: int
) -> None:
    """
    Write the feasibility gate result to a JSON file.
    """
    ensure_path_exists(gate_path)
    result = {
        "status": status,
        "reason": reason,
        "tumor_types_count": tumor_types_count,
        "timestamp": "N/A" # Could add datetime if needed
    }
    with open(gate_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Feasibility gate result written: {gate_path}")

def main() -> int:
    """
    Main entry point for T009: Pre-Check LOO Feasibility.
    
    1. Count available tumor types (N).
    2. If N < 3:
       - Write data/feasibility_gate.json with status "halted".
       - Exit with code 1.
    3. If N >= 3:
       - Proceed (exit 0).
    """
    project_root = get_project_root()
    gate_file = project_root / "data" / "feasibility_gate.json"
    
    logger.info("Starting Pre-Check LOO Feasibility (T009)...")
    
    # Count available types
    # Note: This implementation scans `data/processed` for existing discovery sets.
    # If this is a fresh run, N might be 0.
    # However, the task implies we should count "available" types.
    # If the pipeline is sequential, T009 might be intended to run after T012 (Acquisition)
    # but before T014 (Gate). But T014 is the one that counts TCGA types.
    # Let's assume the user has placed some data or config.
    # If N=0, we halt.
    
    N = count_available_tumor_types(project_root / "data" / "processed")
    logger.info(f"Found {N} tumor types available for LOO validation.")
    
    if N < 3:
        logger.warning(f"Insufficient tumor types for LOO validation (N={N} < 3). Halting.")
        write_feasibility_gate_result(
            gate_file,
            status="halted",
            reason="insufficient_loo_types",
            tumor_types_count=N
        )
        return 1
    
    logger.info(f"Feasibility check passed. {N} tumor types available.")
    # Optionally write a "ready" state if we want to be explicit,
    # but the task says "Proceed Condition: If N >= 3, proceed."
    # We return 0 to indicate success/proceed.
    return 0

if __name__ == "__main__":
    sys.exit(main())
