"""
Validation script to verify that the crystal dataset has no nulls in key columns
and that fingerprint bit counts are of a fixed, high-dimensional magnitude.

Outputs: data/validation/fingerprint_check.json with pass/fail status.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_path_processed_data, get_path_validation, ensure_directory
from logging_config import get_logger, log_event

logger = get_logger("validate_fingerprints")

def validate_dataset(dataset_path: Optional[str] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate the crystal dataset for nulls in key columns and fingerprint bit count consistency.
    
    Args:
        dataset_path: Path to the dataset CSV. If None, uses default path from config.
        output_path: Path to output JSON. If None, uses default path from config.
        
    Returns:
        Dictionary containing validation results.
    """
    # Resolve paths
    if dataset_path is None:
        dataset_path = get_path_processed_data("crystal_dataset.csv")
    if output_path is None:
        output_path = get_path_validation("fingerprint_check.json")
        
    ensure_directory(output_path)
    
    result = {
        "status": "pending",
        "dataset_path": dataset_path,
        "total_rows": 0,
        "null_checks": {},
        "fingerprint_checks": {},
        "errors": [],
        "warnings": []
    }
    
    try:
        # Load dataset
        logger.info(f"Loading dataset from {dataset_path}")
        df = pd.read_csv(dataset_path)
        result["total_rows"] = len(df)
        
        # Define key columns that must not be null
        key_columns = [
            "smiles", 
            "space_group", 
            "lattice_a", "lattice_b", "lattice_c",
            "alpha", "beta", "gamma",
            "fingerprint"
        ]
        
        # Check for nulls in key columns
        for col in key_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                result["null_checks"][col] = {
                    "null_count": int(null_count),
                    "pass": null_count == 0
                }
                if null_count > 0:
                    result["errors"].append(f"Column '{col}' has {null_count} null values")
            else:
                result["warnings"].append(f"Expected column '{col}' not found in dataset")
                result["null_checks"][col] = {"pass": False, "error": "column_missing"}
        
        # Validate fingerprint bit counts
        if "fingerprint" in df.columns:
            fingerprint_counts = []
            for idx, row in df.iterrows():
                fp_str = row["fingerprint"]
                if isinstance(fp_str, str) and fp_str.startswith("[") and fp_str.endswith("]"):
                    # Parse the list string representation
                    try:
                        import ast
                        fp_list = ast.literal_eval(fp_str)
                        if isinstance(fp_list, list):
                            fingerprint_counts.append(len(fp_list))
                    except (ValueError, SyntaxError):
                        result["warnings"].append(f"Row {idx}: Could not parse fingerprint string")
                elif isinstance(fp_str, list):
                    fingerprint_counts.append(len(fp_str))
            
            if fingerprint_counts:
                result["fingerprint_checks"]["count"] = len(fingerprint_counts)
                result["fingerprint_checks"]["min_bits"] = min(fingerprint_counts)
                result["fingerprint_checks"]["max_bits"] = max(fingerprint_counts)
                result["fingerprint_checks"]["mean_bits"] = round(sum(fingerprint_counts) / len(fingerprint_counts), 2)
                
                # Check if all fingerprints have the same length (fixed dimensionality)
                unique_lengths = set(fingerprint_counts)
                result["fingerprint_checks"]["unique_lengths"] = list(unique_lengths)
                result["fingerprint_checks"]["is_fixed_dimensionality"] = len(unique_lengths) == 1
                
                # ECFP4 typically uses 2048 bits
                expected_bits = 2048
                if len(unique_lengths) == 1:
                    actual_bits = unique_lengths.pop()
                    if actual_bits == expected_bits:
                        result["fingerprint_checks"]["dimensionality_check"] = "pass"
                        result["fingerprint_checks"]["expected_bits"] = expected_bits
                        result["fingerprint_checks"]["actual_bits"] = actual_bits
                    else:
                        result["fingerprint_checks"]["dimensionality_check"] = "pass_with_warning"
                        result["fingerprint_checks"]["expected_bits"] = expected_bits
                        result["fingerprint_checks"]["actual_bits"] = actual_bits
                        result["warnings"].append(f"Fingerprint dimensionality is {actual_bits}, expected {expected_bits}")
                else:
                    result["fingerprint_checks"]["dimensionality_check"] = "fail"
                    result["errors"].append(f"Fingerprints have varying lengths: {list(unique_lengths)}")
            else:
                result["fingerprint_checks"]["error"] = "No valid fingerprints found"
                result["errors"].append("Could not validate fingerprint bit counts")
        else:
            result["errors"].append("Fingerprint column not found")
        
        # Determine overall status
        has_errors = len(result["errors"]) > 0
        null_checks_pass = all(
            check.get("pass", False) 
            for check in result["null_checks"].values() 
            if "error" not in check or check["error"] != "column_missing"
        )
        fp_checks_pass = result["fingerprint_checks"].get("dimensionality_check") == "pass"
        
        if has_errors:
            result["status"] = "fail"
        elif not null_checks_pass or not fp_checks_pass:
            result["status"] = "fail"
        else:
            result["status"] = "pass"
            
    except FileNotFoundError:
        result["status"] = "fail"
        result["errors"].append(f"Dataset file not found: {dataset_path}")
    except Exception as e:
        result["status"] = "fail"
        result["errors"].append(f"Validation failed with error: {str(e)}")
        logger.exception("Validation error")
    
    # Save result
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Validation complete. Status: {result['status']}")
    logger.info(f"Results saved to {output_path}")
    
    return result

def main():
    """Main entry point for the validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate crystal dataset fingerprints and nulls")
    parser.add_argument("--dataset", type=str, default=None, help="Path to dataset CSV")
    parser.add_argument("--output", type=str, default=None, help="Path to output JSON")
    args = parser.parse_args()
    
    validate_dataset(args.dataset, args.output)

if __name__ == "__main__":
    main()
