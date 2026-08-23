import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Ensure parent directory is in path for relative imports if running as script
# but standard project structure assumes imports work via PYTHONPATH or installed package.
# We rely on the API surface provided.

def load_merged_dataset(path: Path) -> pd.DataFrame:
    """
    Loads the merged dataset from the specified path.
    Raises FileNotFoundError if file does not exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found at {path}")
    try:
        df = pd.read_csv(path)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load dataset from {path}: {e}")

def validate_numeric_columns(df: pd.DataFrame) -> Tuple[Dict[str, Any], List[str]]:
    """
    Validates that all expected numeric columns are indeed numeric and contain no non-numeric entries.
    
    Returns:
        summary: A dictionary containing validation statistics.
        errors: A list of error messages for columns that failed validation.
    """
    errors = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    non_numeric_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
    
    # Check for columns that should be numeric but are object/string
    # Heuristic: If a column looks like it should be numeric (based on name or content) but is object, flag it.
    # For this task, we strictly enforce that the 'merged_dataset.csv' should have numeric types for features/targets.
    
    # Identify potential numeric columns that are stored as objects (often due to mixed types)
    potential_numeric_errors = []
    for col in non_numeric_cols:
        # Attempt to convert to numeric
        try:
            converted = pd.to_numeric(df[col], errors='raise')
            # If successful, it means it was stored as object but is actually numeric
            # We flag this as a type warning or error depending on strictness.
            # Task requirement: "no non-numeric entries".
            # If it converts successfully, it's fine, but the dtype is wrong.
            potential_numeric_errors.append(col)
        except (ValueError, TypeError):
            # It truly contains non-numeric data
            # Check if it's a known categorical column (e.g., 'sample_id', 'species')
            # If it's a feature or target, this is an error.
            # We assume columns not explicitly known as ID/Category are features.
            # Without a strict schema here, we check if the column name suggests a feature.
            # For safety, we report any object column that isn't obviously an ID.
            if 'id' not in col.lower() and 'species' not in col.lower() and 'pathway' not in col.lower():
                errors.append(f"Column '{col}' contains non-numeric entries and is not a known identifier.")
    
    # Check for NaN values in numeric columns (if strict numeric requirement implies no missing)
    # The task says "no non-numeric entries", usually implies valid numbers. 
    # NaN is a float, so it's technically numeric, but often invalid for modeling.
    # We will report NaN counts but not flag as "non-numeric entry" unless specified.
    
    summary = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "numeric_columns": len(numeric_cols),
        "non_numeric_columns": len(non_numeric_cols),
        "potential_type_issues": potential_numeric_errors,
        "columns_with_na": {col: int(df[col].isna().sum()) for col in numeric_cols if df[col].isna().any()}
    }
    
    return summary, errors

def generate_validation_report(summary: Dict[str, Any], errors: List[str], input_path: Path) -> Dict[str, Any]:
    """
    Generates a structured validation report.
    """
    report = {
        "input_file": str(input_path),
        "validation_status": "passed" if not errors else "failed",
        "summary": summary,
        "errors": errors,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    return report

def main():
    """
    Main entry point for T017:
    1. Loads data/processed/merged_dataset.csv
    2. Validates types and numeric content.
    3. Saves data/results/data_validation_report.json
    """
    # Define paths relative to project root
    # Assuming the script is run from the project root or code/ directory
    # We use a robust path resolution strategy.
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    input_path = project_root / "data" / "processed" / "merged_dataset.csv"
    output_path = project_root / "data" / "results" / "data_validation_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting validation for {input_path}...")
    
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}.")
        # Create a failure report
        report = {
            "input_file": str(input_path),
            "validation_status": "failed",
            "error": "Input file not found",
            "timestamp": pd.Timestamp.now().isoformat()
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    try:
        df = load_merged_dataset(input_path)
        summary, errors = validate_numeric_columns(df)
        report = generate_validation_report(summary, errors, input_path)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation complete. Status: {report['validation_status']}")
        if errors:
            print(f"Errors found: {len(errors)}")
            for err in errors:
                print(f"  - {err}")
        else:
            print("No errors found.")
            
    except Exception as e:
        print(f"Validation failed with exception: {e}")
        report = {
            "input_file": str(input_path),
            "validation_status": "failed",
            "error": str(e),
            "timestamp": pd.Timestamp.now().isoformat()
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()