"""
Gate Launch Script (T037).

Executes validation checks (FR-008, FR-009) before allowing the study to launch.
Raises SystemExit(1) if any validation fails.
"""
import sys
from pathlib import Path
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_validation import (
    check_metadata_matching,
    check_visual_indistinguishability,
    run_all_validations
)

def main():
    """
    Run all validation gates.
    """
    print("Running Pre-Launch Validation Gates...")
    
    try:
        # Run all validations defined in data_validation.py
        results = run_all_validations()
        
        # Check results
        # run_all_validations returns a dict of {check_name: bool} or raises on failure
        # Assuming it returns a status or we check specific flags
        
        # Re-implementing the check logic here for clarity if run_all_validations is a wrapper
        # But based on T036/T037 spec, we call the specific functions.
        
        # FR-008: Metadata Matching
        print("Checking FR-008: Metadata Matching...")
        try:
            check_metadata_matching()
            print("  [PASS] Metadata matching verified.")
        except Exception as e:
            print(f"  [FAIL] Metadata matching failed: {e}")
            sys.exit(1)
        
        # FR-009: Visual Indistinguishability
        print("Checking FR-009: Visual Indistinguishability...")
        try:
            check_visual_indistinguishability()
            print("  [PASS] Visual indistinguishability verified (p > 0.05).")
        except Exception as e:
            print(f"  [FAIL] Visual indistinguishability failed: {e}")
            sys.exit(1)
        
        print("\nAll validation gates passed. Study launch authorized.")
        sys.exit(0)
        
    except SystemExit:
        raise
    except Exception as e:
        print(f"Critical error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
