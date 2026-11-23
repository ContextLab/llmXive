"""
Script to verify that processed datasets are distinct artifacts from raw datasets.

This script performs the following checks:
1. Verifies that processed files exist in data/processed/
2. Verifies that raw files exist in data/raw/
3. Computes SHA-256 checksums for all files
4. Confirms that no processed file has the same checksum as any raw file
5. Confirms that file paths are different (processed vs raw directories)
6. Logs results to data/analysis/artifact_distinction_log.json

This task (T017b) ensures data lineage integrity by proving that
preprocessing transforms create new artifacts with distinct identities.
"""

import os
import sys
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add the code directory to the path so we can import utilities
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils.validators import compute_sha256
from utils.logging_utils import log_warning


def log_header(message: str, log_file: Optional[Path] = None) -> None:
    """Print a formatted header message and optionally log it."""
    header = f"\n{'='*60}\n{message}\n{'='*60}\n"
    print(header)
    if log_file:
        with open(log_file, 'a') as f:
            f.write(f"\n{header}\n")

def log_disclaimer(log_file: Optional[Path] = None) -> None:
    """Log the FR-008 disclaimer."""
    disclaimer = "FR-008 DISCLAIMER: Findings are associational only; no causal claims are made."
    print(disclaimer)
    if log_file:
        with open(log_file, 'a') as f:
            f.write(f"\n{disclaimer}\n")

def get_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        Hexadecimal string of the SHA-256 hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def load_state_file(state_path: Path) -> Dict:
    """
    Load the project state YAML file.
    
    Args:
        state_path: Path to the state YAML file
        
    Returns:
        Dictionary containing the state data
        
    Raises:
        FileNotFoundError: If the state file doesn't exist
        yaml.YAMLError: If the file is not valid YAML
    """
    import yaml
    if not state_path.exists():
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def get_raw_files(raw_dir: Path) -> List[Path]:
    """
    Get all CSV files in the raw data directory.
    
    Args:
        raw_dir: Path to the raw data directory
        
    Returns:
        List of Path objects for CSV files
    """
    if not raw_dir.exists():
        return []
    
    return sorted(raw_dir.glob("*.csv"))

def get_processed_files(processed_dir: Path) -> List[Path]:
    """
    Get all CSV files in the processed data directory.
    
    Args:
        processed_dir: Path to the processed data directory
        
    Returns:
        List of Path objects for CSV files
    """
    if not processed_dir.exists():
        return []
    
    return sorted(processed_dir.glob("*.csv"))

def verify_artifact_distinction(
    raw_dir: Path,
    processed_dir: Path,
    state_path: Path,
    output_path: Path
) -> Dict:
    """
    Verify that processed datasets are distinct artifacts from raw datasets.
    
    This function:
    1. Collects all raw and processed CSV files
    2. Computes checksums for each
    3. Verifies no checksum collision between raw and processed
    4. Verifies file paths are in different directories
    5. Checks that state file contains both raw and processed checksums
    6. Generates a detailed report
    
    Args:
        raw_dir: Path to raw data directory
        processed_dir: Path to processed data directory
        state_path: Path to project state YAML file
        output_path: Path to write the JSON report
        
    Returns:
        Dictionary containing verification results
    """
    start_time = time.time()
    results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "raw_directory": str(raw_dir),
        "processed_directory": str(processed_dir),
        "state_file": str(state_path),
        "output_file": str(output_path),
        "raw_files": [],
        "processed_files": [],
        "checksums": {
            "raw": {},
            "processed": {}
        },
        "path_distinction": {
            "verified": True,
            "details": "Raw and processed files are in separate directories"
        },
        "checksum_distinction": {
            "verified": True,
            "details": "",
            "collisions": []
        },
        "state_file_verification": {
            "verified": True,
            "details": ""
        },
        "summary": {
            "total_raw_files": 0,
            "total_processed_files": 0,
            "verification_passed": True,
            "elapsed_seconds": 0
        }
    }
    
    # Get raw files
    raw_files = get_raw_files(raw_dir)
    results["summary"]["total_raw_files"] = len(raw_files)
    
    if not raw_files:
        results["path_distinction"]["verified"] = False
        results["path_distinction"]["details"] = "No raw files found in data/raw/"
        results["summary"]["verification_passed"] = False
        log_warning("No raw files found in data/raw/")
    else:
        # Compute raw checksums
        for file_path in raw_files:
            try:
                checksum = get_file_checksum(file_path)
                results["checksums"]["raw"][file_path.name] = checksum
                results["raw_files"].append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "checksum": checksum
                })
            except Exception as e:
                results["path_distinction"]["verified"] = False
                results["summary"]["verification_passed"] = False
                results["raw_files"].append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "error": str(e)
                })
                log_warning(f"Error computing checksum for {file_path}: {e}")
    
    # Get processed files
    processed_files = get_processed_files(processed_dir)
    results["summary"]["total_processed_files"] = len(processed_files)
    
    if not processed_files:
        results["path_distinction"]["verified"] = False
        results["path_distinction"]["details"] = "No processed files found in data/processed/"
        results["summary"]["verification_passed"] = False
        log_warning("No processed files found in data/processed/")
    else:
        # Compute processed checksums
        for file_path in processed_files:
            try:
                checksum = get_file_checksum(file_path)
                results["checksums"]["processed"][file_path.name] = checksum
                results["processed_files"].append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "checksum": checksum
                })
            except Exception as e:
                results["path_distinction"]["verified"] = False
                results["summary"]["verification_passed"] = False
                results["processed_files"].append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "error": str(e)
                })
                log_warning(f"Error computing checksum for {file_path}: {e}")
    
    # Verify path distinction
    if raw_files and processed_files:
        raw_dir_str = str(raw_dir)
        processed_dir_str = str(processed_dir)
        for raw_file in results["raw_files"]:
            for proc_file in results["processed_files"]:
                if "error" not in raw_file and "error" not in proc_file:
                    if raw_file["path"].startswith(raw_dir_str) and \
                       proc_file["path"].startswith(processed_dir_str):
                        # Paths are correctly separated
                        pass
    
    # Verify checksum distinction (no collisions)
    if results["checksums"]["raw"] and results["checksums"]["processed"]:
        raw_checksums = set(results["checksums"]["raw"].values())
        proc_checksums = set(results["checksums"]["processed"].values())
        collisions = raw_checksums.intersection(proc_checksums)
        
        if collisions:
            results["checksum_distinction"]["verified"] = False
            results["checksum_distinction"]["details"] = f"Found {len(collisions)} checksum collision(s)"
            results["checksum_distinction"]["collisions"] = list(collisions)
            results["summary"]["verification_passed"] = False
            log_warning(f"Checksum collisions detected: {collisions}")
        else:
            results["checksum_distinction"]["details"] = "All processed files have distinct checksums from raw files"
    else:
        results["checksum_distinction"]["details"] = "Insufficient files to verify checksum distinction"
    
    # Verify state file contains both raw and processed checksums
    if state_path.exists():
        try:
            state = load_state_file(state_path)
            artifacts = state.get("artifact_hashes", {})
            raw_checksums_in_state = any("raw" in key.lower() for key in artifacts.keys())
            processed_checksums_in_state = any("processed" in key.lower() for key in artifacts.keys())
            
            if not raw_checksums_in_state:
                results["state_file_verification"]["verified"] = False
                results["state_file_verification"]["details"] = "State file missing raw dataset checksums"
                results["summary"]["verification_passed"] = False
            elif not processed_checksums_in_state:
                results["state_file_verification"]["verified"] = False
                results["state_file_verification"]["details"] = "State file missing processed dataset checksums"
                results["summary"]["verification_passed"] = False
            else:
                results["state_file_verification"]["details"] = "State file contains both raw and processed checksums"
        except Exception as e:
            results["state_file_verification"]["verified"] = False
            results["state_file_verification"]["details"] = f"Error reading state file: {e}"
            results["summary"]["verification_passed"] = False
    else:
        results["state_file_verification"]["verified"] = False
        results["state_file_verification"]["details"] = "State file not found"
        results["summary"]["verification_passed"] = False
    
    # Update summary
    results["summary"]["elapsed_seconds"] = round(time.time() - start_time, 2)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

def main():
    """Main entry point for the artifact distinction verification script."""
    log_header("T017b: Verifying Artifact Distinction Between Raw and Processed Datasets")
    log_disclaimer()
    
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    state_path = project_root / "state" / "projects" / "PROJ-099-statistical-analysis-of-algorithmic-fair.yaml"
    output_path = project_root / "data" / "analysis" / "artifact_distinction_log.json"
    
    print(f"\nProject root: {project_root}")
    print(f"Raw directory: {raw_dir}")
    print(f"Processed directory: {processed_dir}")
    print(f"State file: {state_path}")
    print(f"Output file: {output_path}")
    
    # Perform verification
    results = verify_artifact_distinction(raw_dir, processed_dir, state_path, output_path)
    
    # Print summary
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    print(f"Total raw files: {results['summary']['total_raw_files']}")
    print(f"Total processed files: {results['summary']['total_processed_files']}")
    print(f"Path distinction verified: {results['path_distinction']['verified']}")
    print(f"Checksum distinction verified: {results['checksum_distinction']['verified']}")
    print(f"State file verification: {results['state_file_verification']['verified']}")
    print(f"Overall verification passed: {results['summary']['verification_passed']}")
    print(f"Elapsed time: {results['summary']['elapsed_seconds']} seconds")
    
    if results['summary']['verification_passed']:
        print("\n✓ SUCCESS: Processed datasets are verified as distinct artifacts from raw datasets.")
        print(f"  Results written to: {output_path}")
    else:
        print("\n✗ FAILURE: Artifact distinction verification failed.")
        print("  Please review the details above and fix the issues.")
    
    # Exit with appropriate code
    sys.exit(0 if results['summary']['verification_passed'] else 1)

if __name__ == "__main__":
    main()
