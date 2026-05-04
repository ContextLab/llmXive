#!/usr/bin/env python3
"""
Verify results path structure per plan.md specification.

Checks:
1. data/processed/results/ exists
2. No legacy data/results/ path exists
3. Reports contents of results directory

This script is executed by the runtime to verify directory structure
compliance with Constitution Principle III (no nested data/raw/raw/)
and plan.md path conventions.
"""

import os
import sys
from pathlib import Path

def main():
    """Verify results directory structure."""
    # Get project root (assuming script is in code/scripts/)
    project_root = Path(__file__).parent.parent.parent
    results_path = project_root / "data" / "processed" / "results"
    legacy_path = project_root / "data" / "results"
    raw_path = project_root / "data" / "raw"

    print("=" * 60)
    print("Results Path Verification Report")
    print("=" * 60)
    print()

    all_checks_passed = True

    # Check 1: data/processed/results/ exists
    print("CHECK 1: Verifying data/processed/results/ exists...")
    if results_path.exists() and results_path.is_dir():
        print(f"  ✓ PASS: {results_path} exists")
        # List contents
        contents = list(results_path.iterdir())
        if contents:
            print(f"  Contents ({len(contents)} items):")
            for item in sorted(contents):
                size = ""
                if item.is_file():
                    size = f" ({item.stat().st_size} bytes)"
                print(f"    - {item.name}{size}")
        else:
            print(f"  Note: Directory is empty (will be populated by evaluation pipeline)")
    else:
        print(f"  ✗ FAIL: {results_path} does not exist or is not a directory")
        all_checks_passed = False
    print()

    # Check 2: No legacy data/results/ path
    print("CHECK 2: Verifying no legacy data/results/ path exists...")
    if legacy_path.exists():
        print(f"  ✗ FAIL: Legacy path {legacy_path} exists (should be removed)")
        all_checks_passed = False
    else:
        print(f"  ✓ PASS: No legacy data/results/ path exists")
    print()

    # Check 3: No nested data/raw/raw/ directories
    print("CHECK 3: Verifying no nested data/raw/raw/ directories...")
    nested_raw = raw_path / "raw"
    if nested_raw.exists():
        print(f"  ✗ FAIL: Nested directory {nested_raw} exists (should be flat)")
        all_checks_passed = False
    else:
        print(f"  ✓ PASS: No nested data/raw/raw/ directory")
    print()

    # Check 4: data/raw/ exists for raw datasets
    print("CHECK 4: Verifying data/raw/ exists for raw datasets...")
    if raw_path.exists() and raw_path.is_dir():
        print(f"  ✓ PASS: {raw_path} exists")
        raw_contents = list(raw_path.iterdir())
        if raw_contents:
            print(f"  Contents ({len(raw_contents)} items):")
            for item in sorted(raw_contents):
                size = ""
                if item.is_file():
                    size = f" ({item.stat().st_size} bytes)"
                print(f"    - {item.name}{size}")
    else:
        print(f"  ✗ FAIL: {raw_path} does not exist")
        all_checks_passed = False
    print()

    # Summary
    print("=" * 60)
    if all_checks_passed:
        print("VERIFICATION RESULT: ALL CHECKS PASSED ✓")
        print("=" * 60)
        return 0
    else:
        print("VERIFICATION RESULT: SOME CHECKS FAILED ✗")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
