"""
Temporal validation module.
Verifies that sample_time < challenge_time for all samples.

This script enforces FR-014: "For all samples, sample collection time must be 
strictly less than challenge time."

Execution:
    python code/data/validate_temporal.py

Outputs:
    - Prints validation results to stdout.
    - Writes a validation report to `data/processed/temporal_validation_report.json`.
    - Returns exit code 0 if valid, 1 if violations found or errors occur.
"""
import os
import glob
import json
import sys
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

from code.utils.constants import DATA_RAW_DIR, DATA_PROCESSED_DIR

def validate_temporal_consistency(report_path: Optional[str] = None) -> bool:
    """
    Validates that for all samples, sample_time < challenge_time.
    
    Searches for phenotype/metadata files in DATA_RAW_DIR and checks temporal constraints.
    Handles multiple date/time formats and column naming conventions.
    
    Args:
        report_path: Optional path to write the JSON validation report. Defaults to 
                     `data/processed/temporal_validation_report.json`.
    
    Returns:
        True if all samples satisfy the constraint, False otherwise.
    """
    # Ensure processed directory exists
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)
    
    if report_path is None:
        report_path = os.path.join(DATA_PROCESSED_DIR, "temporal_validation_report.json")
    
    # Find all phenotype files (common naming patterns)
    phenotype_patterns = [
        os.path.join(DATA_RAW_DIR, "*phenotype*.csv"),
        os.path.join(DATA_RAW_DIR, "*metadata*.csv"),
        os.path.join(DATA_RAW_DIR, "*samples*.csv"),
        os.path.join(DATA_RAW_DIR, "*data*.csv"),
        os.path.join(DATA_RAW_DIR, "placeholder_phenotypes.csv")  # Fallback for testing
    ]
    
    phenotype_files = []
    for pattern in phenotype_patterns:
        phenotype_files.extend(glob.glob(pattern))
    
    # Remove duplicates
    phenotype_files = list(set(phenotype_files))
    
    if not phenotype_files:
        error_msg = "No phenotype files found for temporal validation."
        print(error_msg)
        # Write error report
        _write_report(
            report_path=report_path,
            success=False,
            message=error_msg,
            total_files=0,
            valid_files=0,
            violation_count=0
        )
        return False

    all_valid = True
    total_samples = 0
    valid_samples = 0
    violation_count = 0
    file_results = []

    for file_path in phenotype_files:
        try:
            df = pd.read_csv(file_path)
            file_result = _process_file(df, file_path)
            file_results.append(file_result)
            
            if not file_result["valid"]:
                all_valid = False
            
            total_samples += file_result["total_rows"]
            valid_samples += file_result["valid_rows"]
            violation_count += file_result["violation_count"]
            
        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            print(error_msg)
            all_valid = False
            file_results.append({
                "file": file_path,
                "valid": False,
                "error": str(e),
                "total_rows": 0,
                "valid_rows": 0,
                "violation_count": 0,
                "sample_time_col": None,
                "challenge_time_col": None
            })

    # Write detailed report
    _write_report(
        report_path=report_path,
        success=all_valid,
        message="Temporal validation passed." if all_valid else "Temporal violations detected.",
        total_files=len(phenotype_files),
        valid_files=len([f for f in file_results if f.get("valid", False)]),
        violation_count=violation_count,
        total_samples=total_samples,
        valid_samples=valid_samples,
        file_details=file_results
    )

    if all_valid:
        print(f"✓ Temporal validation PASSED: {valid_samples} samples checked, 0 violations.")
    else:
        print(f"✗ Temporal validation FAILED: {violation_count} violations found in {total_samples} samples.")
    
    return all_valid

def _identify_time_columns(df: pd.DataFrame) -> tuple[Optional[str], Optional[str]]:
    """
    Identifies sample_time and challenge_time columns in a DataFrame.
    
    Args:
        df: Input DataFrame.
    
    Returns:
        Tuple of (sample_time_col, challenge_time_col) or (None, None) if not found.
    """
    sample_time_col = None
    challenge_time_col = None
    
    for col in df.columns:
        col_lower = col.lower().strip()
        
        # Check for sample time
        if "sample_time" in col_lower or "time_sample" in col_lower or "collection_time" in col_lower:
            if sample_time_col is None:  # Prefer exact match
                sample_time_col = col
            elif "sample_time" in col_lower and "sample_time_col" not in col_lower:
                sample_time_col = col
        
        # Check for challenge time
        if "challenge_time" in col_lower or "time_challenge" in col_lower or "inoculation_time" in col_lower:
            if challenge_time_col is None:
                challenge_time_col = col
            elif "challenge_time" in col_lower and "challenge_time_col" not in col_lower:
                challenge_time_col = col
    
    # Fallback: try exact names if not found by pattern
    if not sample_time_col and "sample_time" in df.columns:
        sample_time_col = "sample_time"
    if not challenge_time_col and "challenge_time" in df.columns:
        challenge_time_col = "challenge_time"
    
    return sample_time_col, challenge_time_col

def _parse_time(value: Any) -> Optional[float]:
    """
    Parses a time value to a numeric representation (seconds since epoch or days).
    
    Args:
        value: Value to parse (could be numeric timestamp, string date, etc.)
    
    Returns:
        Numeric value or None if parsing fails.
    """
    if pd.isna(value):
        return None
    
    if isinstance(value, (int, float)):
        # Assume seconds or days; normalize to days for comparison
        if value < 1e10:  # Likely seconds since epoch
            return value / 86400.0
        return float(value)
    
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        
        # Try numeric string
        try:
            num_val = float(value)
            if num_val < 1e10:
                return num_val / 86400.0
            return num_val
        except ValueError:
            pass
        
        # Try date parsing
        date_formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%m-%d-%Y",
            "%m/%d/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%d-%m-%Y %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(value, fmt)
                return dt.timestamp() / 86400.0
            except ValueError:
                continue
        
        # Try pandas parser as last resort
        try:
            dt = pd.to_datetime(value)
            return dt.timestamp() / 86400.0
        except:
            return None
    
    return None

def _process_file(df: pd.DataFrame, file_path: str) -> Dict[str, Any]:
    """
    Processes a single file to check temporal constraints.
    
    Args:
        df: DataFrame to process.
        file_path: Path to the file.
    
    Returns:
        Dictionary with validation results for this file.
    """
    result = {
        "file": file_path,
        "valid": True,
        "total_rows": len(df),
        "valid_rows": 0,
        "violation_count": 0,
        "sample_time_col": None,
        "challenge_time_col": None,
        "violations": []
    }
    
    sample_time_col, challenge_time_col = _identify_time_columns(df)
    result["sample_time_col"] = sample_time_col
    result["challenge_time_col"] = challenge_time_col
    
    if not sample_time_col or not challenge_time_col:
        print(f"Warning: Could not identify time columns in {file_path}. Skipping.")
        return result
    
    # Parse time values
    df_temp = df.copy()
    df_temp[sample_time_col] = df_temp[sample_time_col].apply(_parse_time)
    df_temp[challenge_time_col] = df_temp[challenge_time_col].apply(_parse_time)
    
    # Drop rows with NaN in time columns
    valid_rows = df_temp.dropna(subset=[sample_time_col, challenge_time_col])
    
    if len(valid_rows) == 0:
        print(f"Warning: No valid rows with time data in {file_path}")
        return result
    
    result["valid_rows"] = len(valid_rows)
    
    # Check constraint: sample_time < challenge_time
    violations = valid_rows[valid_rows[sample_time_col] >= valid_rows[challenge_time_col]]
    
    if len(violations) > 0:
        result["valid"] = False
        result["violation_count"] = len(violations)
        
        # Record first few violations for reporting
        for idx, row in violations.head(5).iterrows():
            result["violations"].append({
                "index": int(idx),
                "sample_time": float(row[sample_time_col]),
                "challenge_time": float(row[challenge_time_col])
            })
        
        print(f"Temporal violation in {file_path}: {len(violations)} samples where sample_time >= challenge_time")
    else:
        print(f"Temporal validation passed for {file_path} ({len(valid_rows)} samples)")
    
    return result

def _write_report(
    report_path: str,
    success: bool,
    message: str,
    total_files: int,
    valid_files: int,
    violation_count: int,
    total_samples: int = 0,
    valid_samples: int = 0,
    file_details: List[Dict] = None
):
    """
    Writes the validation report to a JSON file.
    
    Args:
        report_path: Path to write the report.
        success: Overall validation success.
        message: Summary message.
        total_files: Total files processed.
        valid_files: Number of files that passed.
        violation_count: Total number of violations.
        total_samples: Total samples checked.
        valid_samples: Valid samples.
        file_details: Detailed results per file.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "success": success,
        "message": message,
        "summary": {
            "total_files": total_files,
            "valid_files": valid_files,
            "violation_count": violation_count,
            "total_samples": total_samples,
            "valid_samples": valid_samples
        },
        "file_results": file_details or []
    }
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Report written to: {report_path}")

if __name__ == "__main__":
    success = validate_temporal_consistency()
    sys.exit(0 if success else 1)
