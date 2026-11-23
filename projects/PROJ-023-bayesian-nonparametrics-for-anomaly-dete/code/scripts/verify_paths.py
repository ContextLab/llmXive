"""
Verify all file paths in the codebase match the specifications in tasks.md.

This script scans the project directory structure to ensure that:
1. All scripts are located under `code/scripts/` (not root `scripts/`)
2. All libraries are located under `code/lib/` (not root `lib/`)
3. All tests are located under `code/tests/` (not root `tests/`)
4. All data files are located under `data/` with proper subdirectories
5. All paper artifacts are located under `paper/`
6. All config files are located under `code/config/`

Returns exit code 0 if all paths are correct, 1 otherwise.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Define the expected directory structure based on tasks.md
EXPECTED_ROOT_DIRS = {
    "code",
    "data",
    "paper",
    "contracts",
    "tests",  # This might be at root or under code - check both
    "specs",
    "docs"
}

# Define the correct paths for specific file types
SCRIPTS_DIR = Path("code/scripts")
LIB_DIR = Path("code/lib")
TESTS_DIR = Path("code/tests")
CONFIG_DIR = Path("code/config")
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
DATA_RESULTS_DIR = Path("data/results")
PAPER_FIGURES_DIR = Path("paper/figures")
PAPER_DIR = Path("paper")

# Define files that should NOT exist at the root level (they should be under code/)
ROOT_EXCLUSIONS = {
    "scripts",  # Directory - should be code/scripts
    "lib",      # Directory - should be code/lib
    "tests",    # Directory - should be code/tests (if not at root for top-level tests)
    "config",   # Directory - should be code/config
}

def check_file_exists(file_path: Path, description: str) -> Tuple[bool, str]:
    """Check if a specific file exists and return status message."""
    if file_path.exists():
        return True, f"✓ {description}: {file_path}"
    else:
        return False, f"✗ MISSING {description}: {file_path}"

def check_directory_exists(dir_path: Path, description: str) -> Tuple[bool, str]:
    """Check if a specific directory exists and return status message."""
    if dir_path.is_dir():
        return True, f"✓ {description}: {dir_path}"
    else:
        return False, f"✗ MISSING {description}: {dir_path}"

def scan_for_deviations(project_root: Path) -> List[str]:
    """
    Scan the project directory for path deviations from the specification.
    
    Returns a list of deviation messages.
    """
    deviations = []
    
    # Check for root-level directories that should be under code/
    for root_dir in ROOT_EXCLUSIONS:
        root_path = project_root / root_dir
        if root_path.exists():
            deviations.append(
                f"✗ PATH DEVIATION: '{root_dir}' exists at root level. "
                f"Should be under 'code/{root_dir}'"
            )
    
    # Check for scripts at root level
    root_scripts = project_root.glob("*.py")
    for script in root_scripts:
        if script.name not in ["setup_linting.py", "setup_structure.py", "conftest.py"]:
            # These are allowed at root per some conventions, but check tasks.md
            # tasks.md specifies code/scripts/ for all scripts
            deviations.append(
                f"✗ PATH DEVIATION: Script '{script.name}' at root level. "
                f"Should be under 'code/scripts/'"
            )
    
    # Check for lib at root level
    root_lib = project_root / "lib"
    if root_lib.exists() and root_lib.is_dir():
        deviations.append(
            f"✗ PATH DEVIATION: 'lib' directory exists at root level. "
            f"Should be under 'code/lib/'"
        )
    
    # Check for tests at root level (excluding pytest config)
    root_tests = project_root.glob("test_*.py")
    for test in root_tests:
        deviations.append(
            f"✗ PATH DEVIATION: Test file '{test.name}' at root level. "
            f"Should be under 'code/tests/'"
        )
    
    # Check for config at root level
    root_config = project_root / "config"
    if root_config.exists() and root_config.is_dir():
        deviations.append(
            f"✗ PATH DEVIATION: 'config' directory exists at root level. "
            f"Should be under 'code/config/'"
        )
    
    # Check for data directories at root level
    for data_dir in ["raw", "processed", "results"]:
        root_data = project_root / data_dir
        if root_data.exists() and root_data.is_dir():
            deviations.append(
                f"✗ PATH DEVIATION: '{data_dir}' directory exists at root level. "
                f"Should be under 'data/{data_dir}/'"
            )
    
    # Check for paper figures at root level
    root_figures = project_root / "figures"
    if root_figures.exists() and root_figures.is_dir():
        deviations.append(
            f"✗ PATH DEVIATION: 'figures' directory exists at root level. "
            f"Should be under 'paper/figures/'"
        )
    
    # Verify required directories exist at correct paths
    required_dirs = [
        (SCRIPTS_DIR, "Scripts directory"),
        (LIB_DIR, "Libraries directory"),
        (TESTS_DIR, "Tests directory"),
        (CONFIG_DIR, "Config directory"),
        (DATA_RAW_DIR, "Raw data directory"),
        (DATA_PROCESSED_DIR, "Processed data directory"),
        (DATA_RESULTS_DIR, "Results data directory"),
        (PAPER_FIGURES_DIR, "Paper figures directory"),
    ]
    
    for dir_path, description in required_dirs:
        exists, msg = check_directory_exists(project_root / dir_path, description)
        if not exists:
            deviations.append(msg)
    
    # Verify specific required files exist at correct paths
    required_files = [
        (SCRIPTS_DIR / "bayesian_gp.py", "Bayesian GP script"),
        (SCRIPTS_DIR / "evaluate.py", "Evaluation script"),
        (SCRIPTS_DIR / "render_fig1.py", "Figure 1 script"),
        (SCRIPTS_DIR / "render_fig2.py", "Figure 2 script"),
        (SCRIPTS_DIR / "baseline_shewhart.py", "Shewhart baseline script"),
        (SCRIPTS_DIR / "baseline_cusum.py", "CUSUM baseline script"),
        (SCRIPTS_DIR / "baseline_vae.py", "VAE baseline script"),
        (SCRIPTS_DIR / "inject_anomalies.py", "Anomaly injection script"),
        (SCRIPTS_DIR / "sensitivity_analysis.py", "Sensitivity analysis script"),
        (PAPER_DIR / "results.md", "Results document"),
        (DATA_RESULTS_DIR / "bayesian_predictions.csv", "Bayesian predictions"),
        (DATA_RESULTS_DIR / "evaluation.json", "Evaluation results"),
        (PAPER_FIGURES_DIR / "fig1_timeseries.png", "Figure 1"),
        (PAPER_FIGURES_DIR / "fig2_method_comparison.png", "Figure 2"),
        (CONFIG_DIR / "inference_engine.yaml", "Inference engine config"),
        (CONFIG_DIR / "anomaly_injection_config.yaml", "Anomaly injection config"),
        (CONFIG_DIR / "threshold_strategy.yaml", "Threshold strategy config"),
    ]
    
    for file_path, description in required_files:
        exists, msg = check_file_exists(project_root / file_path, description)
        if not exists:
            deviations.append(msg)
    
    return deviations

def main():
    """Main entry point for path verification."""
    project_root = Path.cwd()
    
    print("=" * 70)
    print("PATH VERIFICATION REPORT")
    print("=" * 70)
    print(f"Project root: {project_root}")
    print()
    
    deviations = scan_for_deviations(project_root)
    
    if not deviations:
        print("✓ All paths match the specification in tasks.md")
        print("✓ No deviations found")
        sys.exit(0)
    else:
        print(f"✗ Found {len(deviations)} path deviation(s):")
        print()
        for i, deviation in enumerate(deviations, 1):
            print(f"{i}. {deviation}")
        print()
        print("Please correct the path deviations above to match tasks.md specifications.")
        sys.exit(1)

if __name__ == "__main__":
    main()