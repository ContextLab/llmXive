"""
T017: Validate output CSV types and generate validation report.

Ensures `data/processed/merged_dataset.csv` has correct types and no non-numeric entries
(except for ID/text columns), then generates `data/results/data_validation_report.json`.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.config import get_config
from utils.validation import validate_data_types

def load_merged_dataset() -> pd.DataFrame:
    """Load the merged dataset produced by T016."""
    config = get_config()
    input_path = config.get("data_paths.processed_merged_csv")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    return df

def validate_numeric_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate that numeric columns contain only numeric data (no strings, no NaN in critical fields).
    Returns a summary of validation results.
    """
    issues = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    object_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Check for non-numeric entries in numeric columns
    for col in numeric_cols:
        # Check for NaN values
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            issues.append({
                "column": col,
                "issue": "missing_values",
                "count": int(nan_count),
                "severity": "warning" if nan_count < len(df) * 0.1 else "error"
            })
        
        # Check for infinite values
        inf_count = np.isinf(df[col]).sum()
        if inf_count > 0:
            issues.append({
                "column": col,
                "issue": "infinite_values",
                "count": int(inf_count),
                "severity": "error"
            })
        
        # Check for non-numeric strings that might have been parsed as object
        # (though select_dtypes should have filtered these)
        if df[col].apply(lambda x: isinstance(x, str)).any():
            issues.append({
                "column": col,
                "issue": "non_numeric_string_in_numeric_column",
                "count": int(df[col].apply(lambda x: isinstance(x, str)).sum()),
                "severity": "error"
            })
    
    # Check object columns for unexpected numeric strings
    for col in object_cols:
        # Check if column should be numeric but is stored as object
        # (e.g., "1.0", "2" as strings)
        try:
            pd.to_numeric(df[col], errors='raise')
            # If successful, it's a numeric string column
            issues.append({
                "column": col,
                "issue": "numeric_stored_as_string",
                "count": len(df),
                "severity": "warning",
                "suggestion": "Convert to numeric type"
            })
        except (ValueError, TypeError):
            pass  # Expected for text/ID columns
    
    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "numeric_columns": len(numeric_cols),
        "object_columns": len(object_cols),
        "issues_found": len(issues),
        "issues": issues,
        "is_valid": len([i for i in issues if i["severity"] == "error"]) == 0
    }

def generate_validation_report(df: pd.DataFrame, output_path: Path) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report and save to JSON.
    """
    # Basic schema validation
    report = {
        "file_path": str(output_path),
        "timestamp": pd.Timestamp.now().isoformat(),
        "dataset_info": {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict()
        },
        "numeric_validation": validate_numeric_columns(df),
        "schema_compliance": validate_data_types(df)
    }
    
    # Add summary statistics for numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        report["summary_statistics"] = {
            col: {
                "mean": float(df[col].mean()),
                "std": float(df[col].std()),
                "min": float(df[col].min()),
                "max": float(df[col].max())
            }
            for col in numeric_cols
        }
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    return report

def main():
    """Main entry point for T017 validation task."""
    config = get_config()
    
    input_path = Path(config.get("data_paths.processed_merged_csv"))
    output_path = Path(config.get("data_paths.validation_report_json"))
    
    print(f"Loading merged dataset from: {input_path}")
    try:
        df = load_merged_dataset()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    print(f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
    
    print(f"Generating validation report: {output_path}")
    report = generate_validation_report(df, output_path)
    
    if report["numeric_validation"]["is_valid"]:
        print("✅ Validation PASSED: No critical issues found.")
    else:
        error_count = len([i for i in report["numeric_validation"]["issues"] if i["severity"] == "error"])
        print(f"⚠️  Validation completed with {error_count} error(s) and {report['numeric_validation']['issues_found']} total issue(s).")
        for issue in report["numeric_validation"]["issues"]:
            if issue["severity"] == "error":
                print(f"   - {issue['column']}: {issue['issue']} ({issue['count']} occurrences)")
    
    print(f"Report saved to: {output_path}")
    return report

if __name__ == "__main__":
    main()