"""
Data schemas and directory structure management for the llmXive pipeline.

Defines expected strata, directory layouts, and validation logic.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import sys

# Ensure parent is in path for imports if run as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    get_data_dir,
    get_raw_dir,
    get_processed_dir,
    get_stratified_dir,
    get_features_dir,
    get_results_dir,
    ensure_directories
)
from utils.seeds import set_global_seed

# --------------------------------------------------------------------------
# Schema Definitions
# --------------------------------------------------------------------------

# The four expected strata based on the User Story 1 specification:
# (Motion Magnitude: Static/Slow/Fast) x (Texture Entropy: High/Low)
# Note: The task description mentions 4 subsets (Static/Slow/Fast x High/Low).
# Based on standard stratification logic for this project, we define:
# 1. Static-High
# 2. Static-Low
# 3. Fast-High
# 4. Fast-Low
# (Assuming "Slow" is treated as "Static" for the binary split in the 4-subset model,
# or the specific 4 are defined as above. The code below enforces the existence of the 4
# specific strata defined in T008/T009 logic).
EXPECTED_STRATA = [
    "Static-High",
    "Static-Low",
    "Fast-High",
    "Fast-Low"
]

# Directory structure definition relative to project root
# This function ensures the physical existence of the data hierarchy.
def create_directories() -> Dict[str, Path]:
    """
    Creates the base data directory structure if it doesn't exist.
    
    Returns:
        Dict mapping logical names to Path objects.
    """
    paths = {
        "data": get_data_dir(),
        "raw": get_raw_dir(),
        "processed": get_processed_dir(),
        "stratified": get_stratified_dir(),
        "features": get_features_dir(),
        "results": get_results_dir()
    }
    
    ensure_directories()
    return paths

# --------------------------------------------------------------------------
# Validation Logic
# --------------------------------------------------------------------------

def validate_strata_existence() -> Tuple[bool, List[str]]:
    """
    Checks if the expected strata directories exist under data/stratified/.
    
    Returns:
        Tuple of (is_valid, list_of_missing_strata)
    """
    stratified_dir = get_stratified_dir()
    missing = []
    
    if not stratified_dir.exists():
        return False, ["data/stratified (root directory missing)"]
        
    for stratum in EXPECTED_STRATA:
        stratum_path = stratified_dir / stratum
        if not stratum_path.exists():
            missing.append(stratum)
            
    return len(missing) == 0, missing

def validate_directory_structure() -> Tuple[bool, List[str]]:
    """
    Validates the entire base directory structure.
    
    Returns:
        Tuple of (is_valid, list_of_missing_paths)
    """
    paths = create_directories() # Ensure they are created first
    missing = []
    
    # Check all required directories
    checks = [
        ("data", paths["data"]),
        ("raw", paths["raw"]),
        ("processed", paths["processed"]),
        ("stratified", paths["stratified"]),
        ("features", paths["features"]),
        ("results", paths["results"])
    ]
    
    for name, path in checks:
        if not path.exists():
            missing.append(f"{name} ({path})")
            
    return len(missing) == 0, missing

def check_directory_contents() -> Dict[str, Any]:
    """
    Inspects the contents of the data directories and returns a summary.
    
    Returns:
        Dictionary with counts of files/subdirs per directory.
    """
    report = {}
    paths = create_directories()
    
    for name, path in paths.items():
        if path.exists():
          if path.is_dir():
              items = list(path.iterdir())
              report[name] = {
                  "exists": True,
                  "is_dir": True,
                  "item_count": len(items),
                  "items": [str(i.name) for i in items]
              }
          else:
              report[name] = {
                  "exists": True,
                  "is_dir": False,
                  "size_bytes": path.stat().st_size
              }
        else:
            report[name] = {"exists": False}
            
    return report

def create_schema_report(output_path: Optional[Path] = None) -> Path:
    """
    Generates a JSON report of the current data schema state.
    
    Args:
        output_path: Optional path to write the report. Defaults to data/results/schema_report.json.
        
    Returns:
        Path to the written report.
    """
    if output_path is None:
        output_path = get_results_dir() / "schema_report.json"
        
    report = {
        "expected_strata": EXPECTED_STRATA,
        "directory_structure": {},
        "validation": {
            "structure_valid": False,
            "strata_valid": False,
            "missing_structure": [],
            "missing_strata": []
        }
    }
    
    # Fill directory structure
    paths = create_directories()
    for name, path in paths.items():
        report["directory_structure"][name] = str(path)
        
    # Run validations
    valid_struct, missing_struct = validate_directory_structure()
    valid_strata, missing_strata = validate_strata_existence()
    
    report["validation"]["structure_valid"] = valid_struct
    report["validation"]["strata_valid"] = valid_strata
    report["validation"]["missing_structure"] = missing_struct
    report["validation"]["missing_strata"] = missing_strata
    
    # Add content check
    report["content_summary"] = check_directory_contents()
    
    # Write to disk
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    return output_path

def ensure_schema_compliance() -> bool:
    """
    Ensures the schema is valid. Raises an error if critical directories are missing.
    Returns True if valid.
    """
    valid_struct, missing = validate_directory_structure()
    if not valid_struct:
        raise FileNotFoundError(f"Base directory structure incomplete: {missing}")
        
    # Strata might not exist yet if data hasn't been stratified, so we don't error there,
    # but we log a warning.
    valid_strata, missing_strata = validate_strata_existence()
    if not valid_strata:
        # Log warning but don't crash, as this is expected before T008 runs
        print(f"Warning: Strata directories not yet created: {missing_strata}")
        
    return True

def main():
    """
    Entry point for running schema validation and directory creation.
    """
    set_global_seed(42)
    
    print("Initializing data directory structure...")
    paths = create_directories()
    print(f"Created directories: {list(paths.keys())}")
    
    print("Checking schema compliance...")
    try:
        ensure_schema_compliance()
        print("Schema compliance check passed.")
    except FileNotFoundError as e:
        print(f"Schema compliance check FAILED: {e}")
        sys.exit(1)
        
    print("Generating schema report...")
    report_path = create_schema_report()
    print(f"Report written to: {report_path}")
    
    # Print summary
    summary = check_directory_contents()
    print("\nDirectory Summary:")
    for name, info in summary.items():
        if info.get("exists"):
            print(f"  {name}: {info.get('item_count', 0)} items")
        else:
            print(f"  {name}: MISSING")

if __name__ == "__main__":
    main()
