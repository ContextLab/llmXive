"""
Validation Runner for quickstart.md verification.

This script executes the core pipeline steps defined in quickstart.md
to verify that the system produces the expected artifacts and outputs.

It validates:
1. Project structure existence
2. Data download and derivation (T012, T013)
3. Curation and hard instance selection (T014a, T014b, T014c)
4. Validation report generation (T015)
5. Artifact hashing (T016)
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_config_summary
from utils.hash_artifacts import compute_sha256, hash_directory, generate_manifest
from data.download import download_benchmark_dataset
from data.derive_gt import derive_ground_truth
from data.curate import filter_hard_instances, generate_synthetic_issues
from data.validate_hard import generate_report
from utils.validation import validate_all_curated_artifacts


class ValidationStatus:
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.errors: List[str] = []
        self.start_time: float = time.time()

    def log(self, step: str, status: str, details: Optional[str] = None):
        self.results[step] = {
            "status": status,
            "time_elapsed": time.time() - self.start_time,
            "details": details
        }
        if status == "FAILED":
            self.errors.append(f"{step}: {details}")
        print(f"[{status}] {step}: {details or ''}")

    def summary(self) -> str:
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r["status"] == "PASSED")
        failed = total - passed
        return f"\nValidation Summary: {passed}/{total} steps passed, {failed} failed."


def check_structure():
    """Verify project directory structure exists."""
    required_dirs = [
        "code", "data/raw", "data/curated", "data/results",
        "tests/unit", "tests/contract", "contracts", "docs", "paper"
    ]
    missing = []
    for d in required_dirs:
        if not (PROJECT_ROOT / d).exists():
            missing.append(d)
    
    if missing:
        return f"Missing directories: {', '.join(missing)}"
    return "All required directories exist."


def run_download(status: ValidationStatus):
    """Execute T012: Download benchmark dataset."""
    try:
        # This calls the real download function which fetches from HuggingFace
        download_benchmark_dataset()
        status.log("T012_Download", "PASSED", "Dataset downloaded successfully")
    except Exception as e:
        status.log("T012_Download", "FAILED", str(e))


def run_derive_gt(status: ValidationStatus):
    """Execute T013: Derive ground truth."""
    try:
        # This parses the downloaded solution patches
        derive_ground_truth()
        status.log("T013_DeriveGT", "PASSED", "Ground truth derived")
    except Exception as e:
        status.log("T013_DeriveGT", "FAILED", str(e))


def run_curation(status: ValidationStatus):
    """Execute T014: Curate hard instances and generate synthetic issues."""
    try:
        # Part A: Filter hard instances
        filter_hard_instances()
        
        # Part B: Generate synthetic issues
        generate_synthetic_issues()
        
        status.log("T014_Curation", "PASSED", "Hard instances filtered and synthetic issues generated")
    except Exception as e:
        status.log("T014_Curation", "FAILED", str(e))


def run_validation_report(status: ValidationStatus):
    """Execute T015: Generate validation report."""
    try:
        generate_report()
        status.log("T015_ValidationReport", "PASSED", "Validation report generated")
    except Exception as e:
        status.log("T015_ValidationReport", "FAILED", str(e))


def run_hashing(status: ValidationStatus):
    """Execute T016: Hash curated artifacts."""
    try:
        # Hash the curated directory
        hash_directory(PROJECT_ROOT / "data" / "curated")
        status.log("T016_Hashing", "PASSED", "Artifacts hashed successfully")
    except Exception as e:
        status.log("T016_Hashing", "FAILED", str(e))


def verify_artifacts(status: ValidationStatus):
    """Verify that all expected output files exist and are valid."""
    expected_files = [
        "data/curated/hard_subset.jsonl",
        "data/curated/synthetic_issues.jsonl",
        "data/curated/validation_report.md",
        "data/curated/manifest.json"
    ]
    
    missing = []
    for f in expected_files:
        if not (PROJECT_ROOT / f).exists():
            missing.append(f)
    
    if missing:
        status.log("T017_ArtifactVerification", "FAILED", f"Missing files: {', '.join(missing)}")
    else:
        status.log("T017_ArtifactVerification", "PASSED", "All expected artifacts exist")


def main():
    """Main entry point for validation."""
    print("=" * 60)
    print("Starting quickstart.md Validation (T040)")
    print("=" * 60)
    
    status = ValidationStatus()
    
    # Step 1: Check structure
    structure_check = check_structure()
    if "Missing" in structure_check:
        status.log("T001_Structure", "FAILED", structure_check)
        status.log("StructureCheck", "FAILED", structure_check)
    else:
        status.log("T001_Structure", "PASSED", structure_check)
        status.log("StructureCheck", "PASSED", structure_check)
    
    # Step 2: Run download
    run_download(status)
    
    # Step 3: Derive ground truth
    run_derive_gt(status)
    
    # Step 4: Curation
    run_curation(status)
    
    # Step 5: Validation report
    run_validation_report(status)
    
    # Step 6: Hashing
    run_hashing(status)
    
    # Step 7: Verify artifacts
    verify_artifacts(status)
    
    # Print summary
    print("\n" + status.summary())
    
    if status.errors:
        print("\nErrors encountered:")
        for err in status.errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nValidation completed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()