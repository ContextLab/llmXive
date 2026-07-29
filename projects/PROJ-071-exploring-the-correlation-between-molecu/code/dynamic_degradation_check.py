"""
T012a: Dynamic Degradation Check.

Inspects data/processed/structural_subset.csv for degradation columns.
Updates data/gate_status.json accordingly.
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Optional
import pandas as pd

# Add project root to path if needed
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config

def check_degradation_columns(csv_path: Path) -> tuple[bool, Optional[str]]:
    """
    Check if the CSV file contains degradation-related columns.
    
    Args:
        csv_path: Path to the structural_subset.csv file.
        
    Returns:
        Tuple of (columns_found, column_name)
    """
    degradation_keywords = ['half_life', 'degradation_rate', 't12', 't_half', 'half-life', 'rate_constant']
    
    try:
        # Read the CSV header only to check columns
        df = pd.read_csv(csv_path, nrows=0)
        columns = [col.lower() for col in df.columns]
        
        for keyword in degradation_keywords:
            if any(keyword in col for col in columns):
                return True, keyword
                
        return False, None
        
    except FileNotFoundError:
        return False, None
    except Exception as e:
        print(f"Error checking columns: {e}")
        return False, None

def update_gate_status(passed: bool, reason: str, n: int = 0) -> None:
    """
    Update the gate_status.json file with the check results.
    
    Args:
        passed: Whether degradation columns were found.
        reason: Reason for the status.
        n: Number of records (0 if not found).
    """
    gate_status = {
        "status": "PASS" if passed else "FAIL",
        "reason": reason,
        "N": n,
        "timestamp": pd.Timestamp.utcnow().isoformat()
    }
    
    config = get_config()
    gate_status_path = config['paths']['data_root'] / 'gate_status.json'
    
    with open(gate_status_path, 'w') as f:
        json.dump(gate_status, f, indent=2)
        
    print(f"Gate status updated: {gate_status_path}")

def main():
    """Main entry point for T012a."""
    config = get_config()
    structural_subset_path = config['paths']['data_root'] / 'processed' / 'structural_subset.csv'
    
    print(f"Checking for degradation columns in: {structural_subset_path}")
    
    if not structural_subset_path.exists():
        print(f"File not found: {structural_subset_path}")
        update_gate_status(
            passed=False,
            reason="structural_subset.csv not found",
            n=0
        )
        return
    
    # Check for degradation columns
    found, column_name = check_degradation_columns(structural_subset_path)
    
    if found:
        # Read the file to count records
        try:
            df = pd.read_csv(structural_subset_path)
            n = len(df)
            update_gate_status(
                passed=True,
                reason=f"Found degradation column: {column_name}",
                n=n
            )
            print(f"PASS: Found {column_name} in {n} records")
        except Exception as e:
            print(f"Error reading file: {e}")
            update_gate_status(
                passed=False,
                reason=f"Error reading file: {e}",
                n=0
            )
    else:
        update_gate_status(
            passed=False,
            reason="No verified degradation source found",
            n=0
        )
        print("FAIL: No degradation columns found")

if __name__ == '__main__':
    main()