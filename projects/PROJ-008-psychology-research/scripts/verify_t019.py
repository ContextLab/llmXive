"""
Script to verify T019: Ensure T014-T018 successfully generate required artifacts.

This script runs the verification logic defined in code/data/verify_output.py
to confirm that:
1. data/processed/cleaned_studies.csv exists and is valid
2. data/raw/excluded_studies.log exists
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data.verify_output import verify_csv_artifact, verify_log_artifact

def main():
    print("=" * 60)
    print("T019 VERIFICATION: Checking artifacts from T014-T018")
    print("=" * 60)
    
    # Define expected artifacts
    csv_path = "processed/cleaned_studies.csv"
    log_path = "raw/excluded_studies.log"
    
    # Required columns for cleaned_studies.csv based on the pipeline
    required_columns = [
        "study_id",
        "title",
        "year",
        "sample_size",
        "mean_age",
        "asd_diagnosis",
        "intervention_type",
        "delivery_format",
        "effect_size",
        "se_effect_size"
    ]
    
    all_passed = True
    
    # 1. Verify CSV
    print(f"\n1. Verifying: {csv_path}")
    print("-" * 40)
    csv_result = verify_csv_artifact(csv_path, required_columns, min_rows=1)
    
    if csv_result['exists']:
        print(f"   ✓ File exists: {csv_result['path']}")
        print(f"   ✓ Row count: {csv_result['row_count']}")
        print(f"   ✓ Columns: {csv_result['columns']}")
        
        if csv_result['is_valid']:
            print(f"   ✓ VALIDATION PASSED")
        else:
            print(f"   ✗ VALIDATION FAILED: {csv_result['errors']}")
            all_passed = False
    else:
        print(f"   ✗ File NOT FOUND: {csv_result['path']}")
        print(f"   ✗ VALIDATION FAILED")
        all_passed = False
    
    # 2. Verify Log
    print(f"\n2. Verifying: {log_path}")
    print("-" * 40)
    log_result = verify_log_artifact(log_path, min_lines=0)
    
    if log_result['exists']:
        print(f"   ✓ File exists: {log_result['path']}")
        print(f"   ✓ Line count: {log_result['line_count']}")
        
        if log_result['is_valid']:
            print(f"   ✓ VALIDATION PASSED")
        else:
            print(f"   ✗ VALIDATION FAILED: {log_result['errors']}")
            all_passed = False
    else:
        print(f"   ✗ File NOT FOUND: {log_result['path']}")
        print(f"   ✗ VALIDATION FAILED")
        all_passed = False
    
    # Final Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("RESULT: T019 VERIFICATION SUCCESSFUL")
        print("All required artifacts from T014-T018 are present and valid.")
        print("=" * 60)
        return 0
    else:
        print("RESULT: T019 VERIFICATION FAILED")
        print("One or more required artifacts are missing or invalid.")
        print("Please ensure T014-T018 have been executed successfully.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())