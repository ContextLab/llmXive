"""
Data Hygiene Module for Visual Salience Project.

This module enforces strict data separation between real survey data and synthetic
validation data to prevent conflation and ensure scientific integrity.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
DATA_SURVEY_DIR = PROJECT_ROOT / "data" / "survey"
DATA_SYNTH_DIR = PROJECT_ROOT / "data" / "synth"

# Allowed file extensions for data files
ALLOWED_EXTENSIONS = {".csv", ".json", ".tsv"}

# Naming conventions (prefixes for real data)
REAL_DATA_PREFIXES = ("pilot_responses_real", "responses_real", "survey_data_real")
SYNTH_DATA_PREFIXES = ("pilot_responses_synth", "responses_synth", "synth_data")


class DataHygieneError(Exception):
    """Raised when data separation rules are violated."""
    pass


def _get_directory_files(directory: Path) -> List[Path]:
    """
    Recursively get all data files in a directory.
    
    Args:
        directory: Path to the directory to scan.
        
    Returns:
        List of Path objects for all files with allowed extensions.
    """
    if not directory.exists():
        return []
    
    files = []
    for ext in ALLOWED_EXTENSIONS:
        files.extend(directory.rglob(f"*{ext}"))
        # Also check for files without extension but with known names
        files.extend(directory.rglob("*"))
    
    # Filter to only allowed extensions
    return [f for f in files if f.suffix in ALLOWED_EXTENSIONS]


def _classify_file(file_path: Path) -> str:
    """
    Classify a file as 'real', 'synth', or 'unknown' based on naming conventions.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Classification string: 'real', 'synth', or 'unknown'.
    """
    filename = file_path.name.lower()
    
    # Check for real data prefixes
    for prefix in REAL_DATA_PREFIXES:
        if filename.startswith(prefix):
            return "real"
    
    # Check for synthetic data prefixes
    for prefix in SYNTH_DATA_PREFIXES:
        if filename.startswith(prefix):
            return "synth"
    
    # Check for generic naming patterns that might indicate synthetic data
    if "synth" in filename or "simulation" in filename:
        return "synth"
    
    # Default to unknown for files that don't match patterns
    return "unknown"


def verify_data_separation(strict_mode: bool = True) -> Tuple[bool, List[str]]:
    """
    Verify that data separation rules are enforced across directories.
    
    Rules:
    1. data/survey/ should only contain real data files
    2. data/synth/ should only contain synthetic data files
    3. Files should follow naming conventions
    
    Args:
        strict_mode: If True, unknown files are treated as violations.
                    If False, only explicit violations are reported.
                    
    Returns:
        Tuple of (success: bool, violations: List[str])
    """
    violations = []
    
    # Ensure directories exist
    DATA_SURVEY_DIR.mkdir(parents=True, exist_ok=True)
    DATA_SYNTH_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check survey directory
    survey_files = _get_directory_files(DATA_SURVEY_DIR)
    for file_path in survey_files:
        classification = _classify_file(file_path)
        
        if classification == "synth":
            violations.append(
                f"SYNTHETIC DATA IN REAL DIRECTORY: {file_path.relative_to(PROJECT_ROOT)} "
                f"found in {DATA_SURVEY_DIR.relative_to(PROJECT_ROOT)}"
            )
        elif classification == "unknown" and strict_mode:
            violations.append(
                f"UNKNOWN FILE IN REAL DIRECTORY: {file_path.relative_to(PROJECT_ROOT)} "
                f"found in {DATA_SURVEY_DIR.relative_to(PROJECT_ROOT)}. "
                f"File should be renamed to follow naming conventions (e.g., 'responses_real.csv')."
            )
    
    # Check synth directory
    synth_files = _get_directory_files(DATA_SYNTH_DIR)
    for file_path in synth_files:
        classification = _classify_file(file_path)
        
        if classification == "real":
            violations.append(
                f"REAL DATA IN SYNTHETIC DIRECTORY: {file_path.relative_to(PROJECT_ROOT)} "
                f"found in {DATA_SYNTH_DIR.relative_to(PROJECT_ROOT)}"
            )
        elif classification == "unknown" and strict_mode:
            violations.append(
                f"UNKNOWN FILE IN SYNTHETIC DIRECTORY: {file_path.relative_to(PROJECT_ROOT)} "
                f"found in {DATA_SYNTH_DIR.relative_to(PROJECT_ROOT)}. "
                f"File should be renamed to follow naming conventions (e.g., 'responses_synth.csv')."
            )
    
    success = len(violations) == 0
    return success, violations


def enforce_data_separation() -> None:
    """
    Enforce data separation by raising an error if violations are found.
    
    Raises:
        DataHygieneError: If any data separation violations are detected.
    """
    success, violations = verify_data_separation(strict_mode=True)
    
    if not success:
        error_msg = (
            "DATA SEPARATION VIOLATIONS DETECTED:\n\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nPlease fix the file locations/names to maintain data integrity."
        )
        raise DataHygieneError(error_msg)


def get_data_inventory() -> dict:
    """
    Generate an inventory of all data files in survey and synth directories.
    
    Returns:
        Dictionary with counts and lists of files by directory and classification.
    """
    inventory = {
        "survey": {"real": [], "synth": [], "unknown": [], "total": 0},
        "synth": {"real": [], "synth": [], "unknown": [], "total": 0}
    }
    
    # Scan survey directory
    survey_files = _get_directory_files(DATA_SURVEY_DIR)
    for file_path in survey_files:
        classification = _classify_file(file_path)
        inventory["survey"][classification].append(str(file_path.relative_to(PROJECT_ROOT)))
        inventory["survey"]["total"] += 1
    
    # Scan synth directory
    synth_files = _get_directory_files(DATA_SYNTH_DIR)
    for file_path in synth_files:
        classification = _classify_file(file_path)
        inventory["synth"][classification].append(str(file_path.relative_to(PROJECT_ROOT)))
        inventory["synth"]["total"] += 1
    
    return inventory


def main():
    """
    Main entry point for data hygiene verification.
    
    This function verifies data separation and reports results.
    """
    print("=" * 60)
    print("DATA HYGIENE VERIFICATION")
    print("=" * 60)
    
    # Verify separation
    success, violations = verify_data_separation(strict_mode=True)
    
    if success:
        print("✓ Data separation verified successfully.")
        print("  - data/survey/ contains only real data files")
        print("  - data/synth/ contains only synthetic data files")
    else:
        print("✗ DATA SEPARATION VIOLATIONS DETECTED:")
        for violation in violations:
            print(f"  - {violation}")
        print("\nPlease fix the issues above to ensure data integrity.")
        sys.exit(1)
    
    # Print inventory
    print("\nDATA INVENTORY:")
    inventory = get_data_inventory()
    
    print(f"\nSurvey Directory ({DATA_SURVEY_DIR.relative_to(PROJECT_ROOT)}):")
    print(f"  Total files: {inventory['survey']['total']}")
    print(f"  Real data: {len(inventory['survey']['real'])}")
    print(f"  Synthetic data: {len(inventory['survey']['synth'])}")
    print(f"  Unknown: {len(inventory['survey']['unknown'])}")
    
    if inventory['survey']['real']:
        print("  Files:")
        for f in inventory['survey']['real']:
            print(f"    - {f}")
    
    print(f"\nSynth Directory ({DATA_SYNTH_DIR.relative_to(PROJECT_ROOT)}):")
    print(f"  Total files: {inventory['synth']['total']}")
    print(f"  Real data: {len(inventory['synth']['real'])}")
    print(f"  Synthetic data: {len(inventory['synth']['synth'])}")
    print(f"  Unknown: {len(inventory['synth']['unknown'])}")
    
    if inventory['synth']['synth']:
        print("  Files:")
        for f in inventory['synth']['synth']:
            print(f"    - {f}")
    
    print("\n" + "=" * 60)
    print("Verification complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
