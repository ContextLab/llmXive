import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_RESULTS = PROJECT_ROOT / "data" / "results"

DATA_RESULTS.mkdir(parents=True, exist_ok=True)

def load_merged_dataset():
    path = DATA_PROCESSED / "merged_dataset.csv"
    if not path.exists():
        raise FileNotFoundError(f"merged_dataset.csv not found at {path}")
    return pd.read_csv(path)

def validate_numeric_columns(df):
    """
    Validates that numeric columns are actually numeric.
    """
    issues = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    for col in numeric_cols:
        if df[col].isna().sum() > 0:
            issues.append(f"Column '{col}' has {df[col].isna().sum()} NaN values.")
    
    return {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "numeric_columns": list(numeric_cols),
        "issues": issues,
        "is_valid": len(issues) == 0
    }

def generate_validation_report(df):
    """
    Generates a validation report JSON.
    """
    validation = validate_numeric_columns(df)
    return validation

def main():
    """
    Main entry point for validation.
    Produces data/results/data_validation_report.json
    """
    try:
        df = load_merged_dataset()
        report = generate_validation_report(df)
        
        output_path = DATA_RESULTS / "data_validation_report.json"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation report saved to {output_path}")
        
    except Exception as e:
        print(f"Error in validation: {e}")
        raise

if __name__ == "__main__":
    main()
