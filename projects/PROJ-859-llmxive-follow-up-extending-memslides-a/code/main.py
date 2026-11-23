"""
Main entry point for the llmXive Trace Compressibility Analysis pipeline.

This script performs a 'Fail-Loud' pre-flight check to ensure all required
artifacts from previous stages (T012, T012b, T020b) exist and are valid
before executing the full pipeline.

It prevents partial or synthetic execution by verifying:
1. data/training/ directory exists and is non-empty.
2. data/held_out/ directory exists and is non-empty.
3. data/processed/feature_matrix.csv exists and is non-empty.

If any check fails, the script exits with a clear error message listing
the missing artifacts and returns exit code 1.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path if necessary (standard for this project structure)
# The script is located at code/main.py, so root is parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_config

class PipelinePreFlightError(RuntimeError):
    """Raised when a required artifact is missing or invalid."""
    pass

def check_directory_non_empty(dir_path: Path, description: str) -> Tuple[bool, str]:
    """
    Checks if a directory exists and contains at least one file.
    
    Args:
        dir_path: Path to the directory.
        description: Human-readable description for error messages.
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not dir_path.exists():
        return False, f"Missing directory: {description} at '{dir_path}'"
    
    if not dir_path.is_dir():
        return False, f"Path is not a directory: {description} at '{dir_path}'"
    
    try:
        files = list(dir_path.iterdir())
    except PermissionError:
        return False, f"Permission denied accessing directory: {description} at '{dir_path}'"
    
    if not files:
        return False, f"Directory is empty: {description} at '{dir_path}'"
    
    return True, f"OK: {description} found with {len(files)} files."

def check_file_non_empty(file_path: Path, description: str) -> Tuple[bool, str]:
    """
    Checks if a file exists and is non-empty.
    
    Args:
        file_path: Path to the file.
        description: Human-readable description for error messages.
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not file_path.exists():
        return False, f"Missing file: {description} at '{file_path}'"
    
    if not file_path.is_file():
        return False, f"Path is not a file: {description} at '{file_path}'"
    
    try:
        size = file_path.stat().st_size
    except PermissionError:
        return False, f"Permission denied reading file: {description} at '{file_path}'"
    
    if size == 0:
        return False, f"File is empty: {description} at '{file_path}'"
    
    return True, f"OK: {description} found ({size} bytes)."

def run_preflight_checks() -> None:
    """
    Executes the fail-loud pre-flight checks.
    
    Raises:
        PipelinePreFlightError: If any required artifact is missing or invalid.
    """
    config = get_config()
    errors: List[str] = []
    
    # Define paths relative to project root
    data_root = PROJECT_ROOT / "data"
    training_dir = data_root / "training"
    held_out_dir = data_root / "held_out"
    feature_matrix_path = data_root / "processed" / "feature_matrix.csv"
    
    print("=== llmXive Pipeline Pre-Flight Checks ===")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Root: {data_root}")
    print("")
    
    # Check 1: Training Set
    valid, msg = check_directory_non_empty(training_dir, "Training Set (data/training/)")
    print(f"[{'PASS' if valid else 'FAIL'}] {msg}")
    if not valid:
        errors.append(msg)
        
    # Check 2: Held-Out Set
    valid, msg = check_directory_non_empty(held_out_dir, "Held-Out Set (data/held_out/)")
    print(f"[{'PASS' if valid else 'FAIL'}] {msg}")
    if not valid:
        errors.append(msg)
        
    # Check 3: Feature Matrix
    valid, msg = check_file_non_empty(feature_matrix_path, "Feature Matrix (data/processed/feature_matrix.csv)")
    print(f"[{'PASS' if valid else 'FAIL'}] {msg}")
    if not valid:
        errors.append(msg)
        
    print("")
    
    if errors:
        print("--- PRE-FLIGHT FAILED ---")
        print("The following required artifacts are missing or invalid:")
        for err in errors:
            print(f"  - {err}")
        print("")
        print("Please ensure the following tasks have completed successfully:")
        print("  - T012: Synthetic Trace Generation (data/raw/)")
        print("  - T012b: Dataset Splitting (data/training/, data/held_out/)")
        print("  - T020b: Metric Extraction (data/processed/feature_matrix.csv)")
        print("")
        raise PipelinePreFlightError("Pre-flight checks failed. Aborting pipeline execution.")
        
    print("--- PRE-FLIGHT PASSED ---")
    print("All required artifacts verified.")
    print("Pipeline is ready to proceed.")

def main() -> int:
    """
    Main entry point for the pre-flight check script.
    
    Returns:
        0 on success (all checks passed), 1 on failure (any check failed).
    """
    try:
        run_preflight_checks()
        # If we reach here, all checks passed.
        # In a full pipeline execution, subsequent steps would be invoked here.
        # For this specific task (T066), we stop after verification.
        return 0
    except PipelinePreFlightError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error during pre-flight checks: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())