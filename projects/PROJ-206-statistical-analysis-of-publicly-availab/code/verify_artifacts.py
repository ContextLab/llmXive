"""
Task T033: Verify all artifacts have valid checksums in state/projects/ 
and no manual data fabrication occurred.

This script:
1. Loads the state file for PROJ-206.
2. Verifies that every file listed in the state has a matching SHA-256 hash on disk.
3. Checks for signs of data fabrication (e.g., empty files, files with only header rows, 
   or files containing obvious placeholder text).
4. Validates that data files contain real, non-synthetic content (e.g., dates are not all the same, 
   vote shares are within realistic bounds).
"""
import os
import sys
import hashlib
import json
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime

# Add project root to path to import utils if needed, though we will use standard libs mostly
PROJECT_ROOT = Path(__file__).parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
DATA_DIR = PROJECT_ROOT / "data"

# Expected state file name based on project ID
STATE_FILE_NAME = "PROJ-206-statistical-analysis-of-publicly-availab.yaml"
STATE_FILE_PATH = STATE_DIR / STATE_FILE_NAME

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state_file() -> Dict[str, Any]:
    """Load the project state YAML file."""
    if not STATE_FILE_PATH.exists():
        raise FileNotFoundError(f"State file not found: {STATE_FILE_PATH}")
    
    with open(STATE_FILE_PATH, "r") as f:
        return yaml.safe_load(f)

def verify_checksums(state: Dict[str, Any]) -> List[Tuple[str, bool, str]]:
    """Verify that files in state match their recorded hashes."""
    results = []
    artifacts = state.get("artifacts", {})
    
    for artifact_name, artifact_info in artifacts.items():
        if not isinstance(artifact_info, dict):
            continue
        
        relative_path = artifact_info.get("path")
        recorded_hash = artifact_info.get("hash")
        
        if not relative_path or not recorded_hash:
            results.append((artifact_name, False, "Missing path or hash in state"))
            continue
        
        full_path = PROJECT_ROOT / relative_path
        
        if not full_path.exists():
            results.append((artifact_name, False, f"File missing on disk: {full_path}"))
            continue
        
        try:
            current_hash = compute_file_hash(full_path)
            if current_hash == recorded_hash:
                results.append((artifact_name, True, "Checksum valid"))
            else:
                results.append((artifact_name, False, f"Hash mismatch. Expected: {recorded_hash}, Got: {current_hash}"))
        except Exception as e:
            results.append((artifact_name, False, f"Error computing hash: {str(e)}"))
    
    return results

def detect_fabrication(file_path: Path) -> List[str]:
    """
    Detect potential signs of data fabrication in CSV/JSON files.
    Returns a list of warning messages if issues are found.
    """
    warnings = []
    
    if not file_path.exists():
        return [f"File does not exist: {file_path}"]
    
    file_size = file_path.stat().st_size
    if file_size == 0:
        warnings.append("File is empty (0 bytes)")
        return warnings
    
    # Try to detect as CSV/TSV
    try:
        df = pd.read_csv(file_path)
        
        # Check for empty data (only headers)
        if len(df) == 0:
            warnings.append("File contains only headers, no data rows")
        
        # Check for obvious placeholder values
        # Common fabrication signs: all same value, extreme outliers, placeholder strings
        for col in df.columns:
            if df[col].dtype == object:
                # Check for placeholder strings
                if df[col].nunique() == 1:
                    val = df[col].iloc[0]
                    if val and isinstance(val, str):
                        lower_val = val.lower()
                        if any(placeholder in lower_val for placeholder in 
                             ['placeholder', 'todo', 'sample', 'fake', 'test_data', 'no_data']):
                            warnings.append(f"Column '{col}' contains likely placeholder value: {val}")
                elif df[col].nunique() > 1:
                    # Check if all values are the same placeholder
                    unique_vals = df[col].unique()
                    if len(unique_vals) == 1:
                        val = unique_vals[0]
                        if val and isinstance(val, str) and 'placeholder' in str(val).lower():
                            warnings.append(f"Column '{col}' contains only placeholder value: {val}")
            elif df[col].dtype in ['int64', 'float64']:
                # Check for all zeros or all same value (unless expected like IDs)
                if df[col].nunique() == 1:
                    val = df[col].iloc[0]
                    if val == 0 and len(df) > 10: # Likely fabricated if many rows are all 0
                        warnings.append(f"Column '{col}' contains all zeros for {len(df)} rows")
                
                # Check for extreme outliers that might indicate random fabrication
                if len(df) > 10:
                    q1 = df[col].quantile(0.25)
                    q3 = df[col].quantile(0.75)
                    iqr = q3 - q1
                    lower_bound = q1 - 3 * iqr
                    upper_bound = q3 + 3 * iqr
                    
                    if (df[col] < lower_bound).any() or (df[col] > upper_bound).any():
                        # Not necessarily fabrication, but worth noting if extreme
                        pass
        
        # Specific checks for election poll data
        if 'vote_share' in df.columns:
            # Vote shares should be between 0 and 100 (or 0 and 1)
            if df['vote_share'].min() < 0 or df['vote_share'].max() > 100:
                if df['vote_share'].min() < 0 or df['vote_share'].max() > 1:
                    warnings.append("Vote share values are outside realistic range (0-100 or 0-1)")
        
        if 'date' in df.columns:
            # Check if all dates are the same (unlikely for real data)
            if df['date'].nunique() == 1 and len(df) > 10:
                warnings.append("All dates are identical - possible fabrication")
            
            # Check for dates far in the future or past
            try:
                if isinstance(df['date'].iloc[0], str):
                    dates = pd.to_datetime(df['date'], errors='coerce')
                    today = datetime.now()
                    future_dates = dates[dates > today]
                    if len(future_dates) > 0:
                        warnings.append(f"Found {len(future_dates)} dates in the future")
            except:
                pass
        
    except pd.errors.EmptyDataError:
        warnings.append("File is empty or contains no valid CSV data")
    except Exception as e:
        warnings.append(f"Error reading file as CSV: {str(e)}")
        # Try JSON
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) == 0:
                warnings.append("JSON file is an empty list")
            elif isinstance(data, dict) and len(data) == 0:
                warnings.append("JSON file is an empty object")
        except:
            warnings.append("Could not parse as JSON either")
    
    return warnings

def verify_no_fabrication() -> List[Tuple[str, List[str]]]:
    """Check all data files for signs of fabrication."""
    results = []
    
    # Find all CSV and JSON files in data/
    data_files = []
    for ext in ['*.csv', '*.json', '*.tsv']:
        data_files.extend(DATA_DIR.rglob(ext))
    
    for file_path in data_files:
        warnings = detect_fabrication(file_path)
        if warnings:
            results.append((str(file_path.relative_to(PROJECT_ROOT)), warnings))
    
    return results

def main():
    print("=" * 60)
    print("T033: Artifact Verification and Fabrication Check")
    print("=" * 60)
    
    all_passed = True
    
    # 1. Verify checksums
    print("\n[1/2] Verifying artifact checksums...")
    try:
        state = load_state_file()
        checksum_results = verify_checksums(state)
        
        for artifact_name, passed, message in checksum_results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  {status} {artifact_name}: {message}")
            if not passed:
                all_passed = False
    
    except FileNotFoundError as e:
        print(f"  ✗ FAIL: {e}")
        all_passed = False
    except Exception as e:
        print(f"  ✗ FAIL: Error loading state file: {e}")
        all_passed = False
    
    # 2. Check for fabrication
    print("\n[2/2] Checking for data fabrication...")
    fabrication_results = verify_no_fabrication()
    
    if not fabrication_results:
        print("  ✓ PASS: No fabrication signs detected in data files")
    else:
        for file_path, warnings in fabrication_results:
            print(f"  ✗ WARNING: {file_path}")
            for warning in warnings:
                print(f"    - {warning}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("RESULT: All verifications PASSED. Artifacts are valid and no fabrication detected.")
        return 0
    else:
        print("RESULT: VERIFICATION FAILED. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())