"""
Validation runner for the llmXive pipeline.

Executes the full data pipeline: download, derive, curate, validate, hash.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from data.download import main as download_main
from data.derive_gt import main as derive_gt_main
from data.curate import main as curate_main
from data.validate_hard import main as validate_main
from data.hash_curated import main as hash_curated_main


class ValidationStatus:
    """Enum-like class for validation statuses."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


def check_structure() -> bool:
    """Check if required directory structure exists."""
    required_dirs = [
        "data/raw",
        "data/curated",
        "data/results",
        "tests/unit",
        "tests/contract",
        "contracts",
        "docs",
        "paper"
    ]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"WARNING: Directory does not exist: {dir_path}")
            return False
    return True


def run_download() -> ValidationStatus:
    """Run the download step."""
    print("\n" + "="*50)
    print("STEP: Download Dataset")
    print("="*50)
    try:
        exit_code = download_main()
        if exit_code == 0:
            print("Download completed successfully.")
            return ValidationStatus.SUCCESS
        else:
            print(f"Download failed with exit code {exit_code}")
            return ValidationStatus.FAILED
    except Exception as e:
        print(f"Download error: {e}")
        return ValidationStatus.FAILED


def run_derive_gt() -> ValidationStatus:
    """Run the ground truth derivation step."""
    print("\n" + "="*50)
    print("STEP: Derive Ground Truth")
    print("="*50)
    try:
        exit_code = derive_gt_main()
        if exit_code == 0:
            print("Ground truth derivation completed successfully.")
            return ValidationStatus.SUCCESS
        else:
            print(f"Ground truth derivation failed with exit code {exit_code}")
            return ValidationStatus.FAILED
    except Exception as e:
        print(f"Ground truth derivation error: {e}")
        return ValidationStatus.FAILED


def run_curation() -> ValidationStatus:
    """Run the curation step."""
    print("\n" + "="*50)
    print("STEP: Curate Dataset")
    print("="*50)
    try:
        exit_code = curate_main()
        if exit_code == 0:
            print("Curation completed successfully.")
            return ValidationStatus.SUCCESS
        else:
            print(f"Curation failed with exit code {exit_code}")
            return ValidationStatus.FAILED
    except Exception as e:
        print(f"Curation error: {e}")
        return ValidationStatus.FAILED


def run_validation_report() -> ValidationStatus:
    """Run the validation report generation step."""
    print("\n" + "="*50)
    print("STEP: Generate Validation Report")
    print("="*50)
    try:
        exit_code = validate_main()
        if exit_code == 0:
            print("Validation report generation completed successfully.")
            return ValidationStatus.SUCCESS
        else:
            print(f"Validation report generation failed with exit code {exit_code}")
            return ValidationStatus.FAILED
    except Exception as e:
        print(f"Validation report error: {e}")
        return ValidationStatus.FAILED


def run_hashing() -> ValidationStatus:
    """Run the hashing step for curated artifacts."""
    print("\n" + "="*50)
    print("STEP: Hash Curated Artifacts")
    print("="*50)
    try:
        exit_code = hash_curated_main()
        if exit_code == 0:
            print("Hashing completed successfully.")
            return ValidationStatus.SUCCESS
        else:
            print(f"Hashing failed with exit code {exit_code}")
            return ValidationStatus.FAILED
    except Exception as e:
        print(f"Hashing error: {e}")
        return ValidationStatus.FAILED


def verify_artifacts() -> bool:
    """Verify that all required artifacts exist."""
    required_artifacts = [
        "data/curated/hard_subset.jsonl",
        "data/curated/synthetic_issues.jsonl",
        "data/curated/synthetic_issues_meta.json",
        "data/curated/validation_report.md",
        "data/curated/manifest.json"
    ]
    
    all_exist = True
    for artifact in required_artifacts:
        if Path(artifact).exists():
            print(f"  [OK] {artifact}")
        else:
            print(f"  [MISSING] {artifact}")
            all_exist = False
    
    return all_exist


def main() -> int:
    """
    Main entry point for the validation runner.
    
    Executes the full pipeline: download -> derive -> curate -> validate -> hash.
    """
    print("="*60)
    print("LLMXIVE VALIDATION RUNNER")
    print("="*60)
    
    start_time = time.time()
    
    # Check structure
    if not check_structure():
        print("ERROR: Required directory structure is missing.")
        return 1
    
    # Execute pipeline steps
    steps = [
        ("Download", run_download),
        ("Derive GT", run_derive_gt),
        ("Curate", run_curation),
        ("Validate", run_validation_report),
        ("Hash", run_hashing),
    ]
    
    results = {}
    for step_name, step_func in steps:
        status = step_func()
        results[step_name] = status
        if status == ValidationStatus.FAILED:
            print(f"\nERROR: Step '{step_name}' failed. Aborting pipeline.")
            break
    
    # Verify artifacts
    print("\n" + "="*50)
    print("VERIFICATION")
    print("="*50)
    if verify_artifacts():
        print("All required artifacts present.")
    else:
        print("WARNING: Some artifacts are missing.")
    
    elapsed = time.time() - start_time
    print(f"\nPipeline completed in {elapsed:.2f} seconds.")
    
    # Return failure if any step failed
    if any(r == ValidationStatus.FAILED for r in results.values()):
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())