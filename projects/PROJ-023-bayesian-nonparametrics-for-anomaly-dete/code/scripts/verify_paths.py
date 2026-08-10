"""
Script to verify all file paths in the codebase match tasks.md specifications.

This script checks that:
1. All Python scripts are under code/scripts/
2. All libraries are under code/lib/
3. All tests are under code/tests/
4. All data files are under data/ (raw/, processed/, results/)
5. All paper artifacts are under paper/ (figures/, results.md)
6. All contracts are under contracts/

It reports any deviations from the expected path structure.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Define expected directory structure based on tasks.md
EXPECTED_DIRS = {
    "code": [
        "scripts",
        "lib",
        "tests",
        "tests/contract",
        "tests/integration",
        "setup_linting.py",
        "setup_structure.py",
    ],
    "data": [
        "raw",
        "processed",
        "results",
        "PROVENANCE.md",
        "VERSION.txt",
    ],
    "paper": [
        "figures",
        "README.md",
        "results.md",
    ],
    "contracts": [
        "dataset.schema.yaml",
        "evaluation.schema.yaml",
        "prediction.schema.yaml",
    ],
}

# Define expected script files
EXPECTED_SCRIPTS = [
    "code/scripts/download_data.py",
    "code/scripts/inject_anomalies.py",
    "code/scripts/baseline_shewhart.py",
    "code/scripts/baseline_cusum.py",
    "code/scripts/baseline_vae.py",
    "code/scripts/bayesian_gp.py",
    "code/scripts/evaluate.py",
    "code/scripts/sensitivity_analysis.py",
    "code/scripts/render_fig1.py",
    "code/scripts/render_fig2.py",
    "code/scripts/baseline_integration.py",
]

# Define expected library files
EXPECTED_LIBS = [
    "code/lib/data_loader.py",
    "code/lib/anomaly_injector.py",
    "code/lib/metrics.py",
    "code/lib/utils.py",
]

# Define expected test files
EXPECTED_TESTS = [
    "code/tests/test_data_injection.py",
    "code/tests/test_metrics.py",
    "code/tests/test_anomaly_injector.py",
    "code/tests/test_utils.py",
    "code/tests/contract/test_bayesian_schema.py",
    "code/tests/contract/test_baseline_schema.py",
    "code/tests/contract/test_evaluation_schema.py",
    "code/tests/integration/test_bayesian_inference.py",
    "code/tests/integration/test_baseline_comparison.py",
    "code/tests/integration/test_statistical_analysis.py",
]

# Define expected data files
EXPECTED_DATA_FILES = [
    "data/PROVENANCE.md",
    "data/VERSION.txt",
    "data/raw/series.csv",
    "data/processed/series_with_anomalies.csv",
    "data/processed/ground_truth.csv",
    "data/results/bayesian_predictions.csv",
    "data/results/shewhart_predictions.csv",
    "data/results/cusum_predictions.csv",
    "data/results/vae_predictions.csv",
    "data/results/evaluation.json",
    "data/results/sensitivity_analysis.json",
]

# Define expected paper files
EXPECTED_PAPER_FILES = [
    "paper/README.md",
    "paper/results.md",
    "paper/figures/fig1_timeseries.png",
    "paper/figures/fig2_method_comparison.png",
]

# Define expected contract files
EXPECTED_CONTRACTS = [
    "contracts/dataset.schema.yaml",
    "contracts/evaluation.schema.yaml",
    "contracts/prediction.schema.yaml",
]

def check_file_exists(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a file exists and return status."""
    if path.exists():
        return True, f"✓ {description}: {path}"
    else:
        return False, f"✗ MISSING: {description}: {path}"

def check_directory_exists(path: Path, description: str) -> Tuple[bool, str]:
    """Check if a directory exists and return status."""
    if path.exists() and path.is_dir():
        return True, f"✓ {description}: {path}"
    else:
        return False, f"✗ MISSING DIR: {description}: {path}"

def scan_for_deviations(root: Path) -> List[str]:
    """Scan the project root for files that don't match expected structure."""
    deviations = []
    
    # Check for files at root that should be under code/
    root_files = [f for f in root.iterdir() if f.is_file() and f.name not in 
                 ["requirements.txt", "README.md", "tasks.md", "plan.md", "spec.md", 
                  "data-model.md", "research.md", "quickstart.md"]]
    
    for f in root_files:
        if f.name.endswith(".py"):
            deviations.append(f"✗ ROOT PYTHON FILE (should be under code/): {f}")
        elif f.name.endswith(".md"):
            # Allow some root markdown files
            pass
        else:
            deviations.append(f"? ROOT FILE (verify location): {f}")
    
    # Check for data files at root
    data_files_at_root = list(root.glob("*.csv")) + list(root.glob("*.json")) + list(root.glob("*.yaml"))
    for f in data_files_at_root:
        deviations.append(f"✗ DATA FILE AT ROOT (should be under data/): {f}")
    
    # Check for scripts at root
    scripts_at_root = list(root.glob("scripts/*.py"))
    for f in scripts_at_root:
        if not f.parent.name == "scripts":
            continue
        # Check if it should be under code/scripts
        expected_path = root / "code" / "scripts" / f.name
        if not expected_path.exists():
            deviations.append(f"✗ SCRIPT AT ROOT (should be under code/scripts/): {f}")
    
    return deviations

def main():
    """Main function to verify paths."""
    print("=" * 80)
    print("PATH STRUCTURE VERIFICATION FOR PROJ-023")
    print("=" * 80)
    
    root = Path(".")
    all_ok = True
    messages = []
    
    # Check expected scripts
    print("\n[1] Checking Expected Scripts...")
    for script in EXPECTED_SCRIPTS:
        path = root / script
        ok, msg = check_file_exists(path, "Script")
        messages.append(msg)
        if not ok:
            all_ok = False
    
    # Check expected libraries
    print("\n[2] Checking Expected Libraries...")
    for lib in EXPECTED_LIBS:
        path = root / lib
        ok, msg = check_file_exists(path, "Library")
        messages.append(msg)
        if not ok:
            all_ok = False
    
    # Check expected tests
    print("\n[3] Checking Expected Tests...")
    for test in EXPECTED_TESTS:
        path = root / test
        ok, msg = check_file_exists(path, "Test")
        messages.append(msg)
        if not ok:
            all_ok = False
    
    # Check expected data files
    print("\n[4] Checking Expected Data Files...")
    for data_file in EXPECTED_DATA_FILES:
        path = root / data_file
        ok, msg = check_file_exists(path, "Data File")
        messages.append(msg)
        if not ok:
            all_ok = False
    
    # Check expected paper files
    print("\n[5] Checking Expected Paper Files...")
    for paper_file in EXPECTED_PAPER_FILES:
        path = root / paper_file
        ok, msg = check_file_exists(path, "Paper File")
        messages.append(msg)
        if not ok:
            all_ok = False
    
    # Check expected contracts
    print("\n[6] Checking Expected Contracts...")
    for contract in EXPECTED_CONTRACTS:
        path = root / contract
        ok, msg = check_file_exists(path, "Contract")
        messages.append(msg)
        if not ok:
            all_ok = False
    
    # Scan for deviations
    print("\n[7] Scanning for Path Deviations...")
    deviations = scan_for_deviations(root)
    if deviations:
        all_ok = False
        messages.extend(deviations)
    else:
        messages.append("✓ No path deviations detected")
    
    # Print results
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    for msg in messages:
        print(msg)
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✓ ALL PATHS MATCH TASKS.MD SPECIFICATIONS")
        sys.exit(0)
    else:
        print("✗ PATH MISMATCHES DETECTED - REVIEW ABOVE")
        sys.exit(1)

if __name__ == "__main__":
    main()