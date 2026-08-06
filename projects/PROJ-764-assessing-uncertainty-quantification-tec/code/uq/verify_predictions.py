import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List

# Schema definition based on T016 requirements
REQUIRED_COLUMNS = [
    'sample_id',
    'method',
    'prediction',
    'variance',
    'lower_50',
    'upper_50',
    'lower_90',
    'upper_90'
]

def verify_schema(file_path: str) -> Dict[str, Any]:
    """
    Verifies that the CSV file exists and contains the required columns.
    
    Args:
        file_path: Path to the CSV file to verify.
        
    Returns:
        Dictionary with verification results.
    """
    result = {
        "file_exists": False,
        "schema_valid": False,
        "missing_columns": [],
        "extra_columns": [],
        "row_count": 0,
        "errors": []
    }
    
    if not os.path.exists(file_path):
        result["errors"].append(f"File not found: {file_path}")
        return result
        
    result["file_exists"] = True
    
    try:
        df = pd.read_csv(file_path)
        result["row_count"] = len(df)
        
        # Check for required columns
        present_columns = set(df.columns)
        required_set = set(REQUIRED_COLUMNS)
        
        missing = required_set - present_columns
        extra = present_columns - required_set
        
        result["missing_columns"] = list(missing)
        result["extra_columns"] = list(extra)
        
        if not missing:
            result["schema_valid"] = True
        else:
            result["errors"].append(f"Missing required columns: {missing}")
            
        # Verify numeric types for prediction and variance
        for col in ['prediction', 'variance', 'lower_50', 'upper_50', 'lower_90', 'upper_90']:
            if col in df.columns:
                if not np.issubdtype(df[col].dtype, np.number):
                    result["errors"].append(f"Column '{col}' is not numeric")
                    
    except Exception as e:
        result["errors"].append(f"Failed to read CSV: {str(e)}")
        
    return result

def verify_data_integrity(file_path: str) -> Dict[str, Any]:
    """
    Verifies data integrity: bounds consistency, non-negative variance, etc.
    
    Args:
        file_path: Path to the CSV file to verify.
        
    Returns:
        Dictionary with integrity check results.
    """
    result = {
        "integrity_valid": True,
        "issues": [],
        "stats": {}
    }
    
    if not os.path.exists(file_path):
        result["issues"].append("File does not exist")
        result["integrity_valid"] = False
        return result
        
    try:
        df = pd.read_csv(file_path)
        
        # Check variance is non-negative
        if 'variance' in df.columns:
            neg_variance = df[df['variance'] < 0]
            if len(neg_variance) > 0:
                result["issues"].append(f"Found {len(neg_variance)} rows with negative variance")
                result["integrity_valid"] = False
                
        # Check bounds consistency: lower < prediction < upper
        for interval in ['50', '90']:
            lower_col = f'lower_{interval}'
            upper_col = f'upper_{interval}'
            
            if lower_col in df.columns and upper_col in df.columns:
                invalid_lower = df[df[lower_col] > df['prediction']]
                invalid_upper = df[df[upper_col] < df['prediction']]
                
                if len(invalid_lower) > 0:
                    result["issues"].append(f"Found {len(invalid_lower)} rows where lower_{interval} > prediction")
                    result["integrity_valid"] = False
                    
                if len(invalid_upper) > 0:
                    result["issues"].append(f"Found {len(invalid_upper)} rows where upper_{interval} < prediction")
                    result["integrity_valid"] = False
                    
        # Check that 90% bounds are wider than 50% bounds
        if 'lower_50' in df.columns and 'lower_90' in df.columns:
            invalid_range = df[df['lower_90'] > df['lower_50']]
            if len(invalid_range) > 0:
                result["issues"].append(f"Found {len(invalid_range)} rows where lower_90 > lower_50")
                result["integrity_valid"] = False
                
        if 'upper_50' in df.columns and 'upper_90' in df.columns:
            invalid_range = df[df['upper_90'] < df['upper_50']]
            if len(invalid_range) > 0:
                result["issues"].append(f"Found {len(invalid_range)} rows where upper_90 < upper_50")
                result["integrity_valid"] = False
                
        # Basic statistics
        numeric_cols = ['prediction', 'variance', 'lower_50', 'upper_50', 'lower_90', 'upper_90']
        available_cols = [c for c in numeric_cols if c in df.columns]
        if available_cols:
            result["stats"] = df[available_cols].describe().to_dict()
            
    except Exception as e:
        result["issues"].append(f"Error during integrity check: {str(e)}")
        result["integrity_valid"] = False
        
    return result

def main():
    """Main entry point for verification."""
    input_file = "results/uq_predictions.csv"
    
    print(f"Verifying {input_file}...")
    
    # Schema verification
    schema_result = verify_schema(input_file)
    print("\n--- Schema Verification ---")
    print(f"File exists: {schema_result['file_exists']}")
    print(f"Schema valid: {schema_result['schema_valid']}")
    print(f"Row count: {schema_result['row_count']}")
    if schema_result['missing_columns']:
        print(f"Missing columns: {schema_result['missing_columns']}")
    if schema_result['errors']:
        print(f"Errors: {schema_result['errors']}")
        
    # Data integrity verification
    integrity_result = verify_data_integrity(input_file)
    print("\n--- Data Integrity Verification ---")
    print(f"Integrity valid: {integrity_result['integrity_valid']}")
    if integrity_result['issues']:
        print(f"Issues found: {integrity_result['issues']}")
        
    # Determine overall success
    success = schema_result['file_exists'] and schema_result['schema_valid'] and integrity_result['integrity_valid']
    
    if success:
        print("\n✅ Verification PASSED: All checks successful.")
        sys.exit(0)
    else:
        print("\n❌ Verification FAILED: One or more checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()