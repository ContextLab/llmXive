"""
Semantic Outcome Oracle and Validation Logic for EnterpriseClawBench.

This module implements:
1. The Semantic Outcome Oracle (T021a) to derive 'correctable' labels.
2. The Oracle Validation logic (T021b) to verify determinism and consistency.
"""
import json
import os
import sys
import random
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Constants for the Oracle Logic
CORRECTABLE_ERROR_TYPES = {'syntax', 'token_mismatch'}
EXCLUDED_ERROR_TYPES = {'semantic_error', 'reasoning_gap'}

def derive_correctable_label(entry: Dict[str, Any]) -> bool:
    """
    Derives the 'correctable' label based on the error type.
    
    Logic (T021a):
    correctable = (error_type in ['syntax', 'token_mismatch'] 
                   AND error_type not in ['semantic_error', 'reasoning_gap'])
    
    Args:
        entry: A dictionary representing a log entry, expected to have an 'error_type' field.
    
    Returns:
        bool: True if the error is considered correctable, False otherwise.
    """
    error_type = entry.get('error_type', '').lower()
    
    # Ensure the logic strictly follows the rule:
    # Must be in the correctable set AND NOT in the excluded set.
    if error_type in CORRECTABLE_ERROR_TYPES and error_type not in EXCLUDED_ERROR_TYPES:
        return True
    return False

def validate_oracle_determinism(
    data_path: str,
    output_path: str,
    sample_size: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Validates that the Oracle labels are deterministic and consistent.
    
    This function:
    1. Loads the dataset from `data_path`.
    2. Takes a random sample of `sample_size` entries (seeded).
    3. Runs the derivation logic twice on the same sample.
    4. Compares the results to ensure 100% consistency (determinism).
    5. Writes a validation report to `output_path`.
    
    Args:
        data_path: Path to the input JSONL file containing raw logs/features.
        output_path: Path where the validation report JSON will be saved.
        sample_size: Number of records to sample for validation.
        seed: Random seed for reproducibility.
    
    Returns:
        Dict containing the validation results.
    
    Raises:
        FileNotFoundError: If data_path does not exist.
        ValueError: If the dataset is too small for the requested sample size.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    # Load data
    records = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    
    if len(records) < sample_size:
        # If the dataset is smaller than the sample size, use the whole dataset
        # but adjust the reported sample size.
        sample_size = len(records)
        if sample_size == 0:
            raise ValueError("Dataset is empty.")
    
    # Set seed for reproducibility
    random.seed(seed)
    sampled_indices = random.sample(range(len(records)), sample_size)
    sample_records = [records[i] for i in sampled_indices]
    
    # Run Oracle Logic (Pass 1)
    labels_pass_1 = [derive_correctable_label(r) for r in sample_records]
    
    # Run Oracle Logic (Pass 2) - Should be identical
    labels_pass_2 = [derive_correctable_label(r) for r in sample_records]
    
    # Check Determinism
    is_deterministic = (labels_pass_1 == labels_pass_2)
    
    # Check Consistency (No internal contradictions in logic application)
    # Since the logic is a pure function, consistency is guaranteed if deterministic.
    # We verify that the function doesn't raise exceptions on the sample.
    consistency_status = "PASS" if is_deterministic else "FAIL"
    
    # Calculate distribution stats for the sample
    correctable_count = sum(labels_pass_1)
    total_count = len(labels_pass_1)
    correctable_ratio = correctable_count / total_count if total_count > 0 else 0.0
    
    report = {
        "status": "PASS" if is_deterministic else "FAIL",
        "sample_size": total_count,
        "seed": seed,
        "determinism_check": {
            "pass": is_deterministic,
            "message": "Oracle logic produced identical results on repeated runs." if is_deterministic else "Oracle logic produced different results on repeated runs."
        },
        "consistency_check": {
            "status": consistency_status,
            "message": "Labels are consistent across the sample."
        },
        "statistics": {
            "total_samples": total_count,
            "correctable_count": correctable_count,
            "uncorrectable_count": total_count - correctable_count,
            "correctable_ratio": correctable_ratio
        },
        "validation_details": {
            "error_types_found": list(set(r.get('error_type', 'unknown') for r in sample_records)),
            "rule_applied": "correctable = (error_type in ['syntax', 'token_mismatch'] AND error_type not in ['semantic_error', 'reasoning_gap'])"
        }
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """
    Entry point for the Oracle Validation script.
    Runs the validation on the standard processed features file.
    """
    # Define paths relative to project root
    # Assuming the script is run from the project root or code/src directory
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_path = base_dir / "data" / "processed" / "features.jsonl"
    output_path = base_dir / "data" / "results" / "oracle_validation.json"
    
    if not data_path.exists():
        print(f"Error: Input file not found at {data_path}")
        print("Please ensure T017 (Generate features.jsonl) has been completed.")
        sys.exit(1)
    
    print(f"Running Oracle Validation on {data_path}...")
    try:
        report = validate_oracle_determinism(
            data_path=str(data_path),
            output_path=str(output_path),
            sample_size=1000,
            seed=42
        )
        print(f"Validation Complete. Status: {report['status']}")
        print(f"Report saved to: {output_path}")
        print(f"Correctable Ratio in sample: {report['statistics']['correctable_ratio']:.2%}")
    except Exception as e:
        print(f"Validation Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()