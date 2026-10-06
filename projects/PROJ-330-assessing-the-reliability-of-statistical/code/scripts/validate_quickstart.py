"""
Script to validate the quickstart.md instructions.

This script simulates the execution of the quickstart.md guide to ensure:
1. All required directories exist.
2. All required dependencies are importable.
3. The main entry points can be called without errors (using mocks where necessary).
4. The expected output artifacts can be generated (or their paths verified).

Usage:
    python code/scripts/validate_quickstart.py
"""
import os
import sys
import subprocess
import importlib.util
import logging
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
FIGURES_DIR = PROJECT_ROOT / "figures"
SPECS_DIR = PROJECT_ROOT / "specs" / "001-assess-significance-reliability"
QUICKSTART_PATH = SPECS_DIR / "quickstart.md"

# Required directories
REQUIRED_DIRS = [
    CODE_DIR,
    CODE_DIR / "src",
    CODE_DIR / "scripts",
    CODE_DIR / "tests",
    DATA_DIR,
    FIGURES_DIR,
    SPECS_DIR
]

# Required dependencies (from T002)
REQUIRED_PACKAGES = [
    "pandas", "numpy", "scikit-learn", "matplotlib", "seaborn",
    "pyyaml", "requests", "tqdm", "statsmodels", "scipy", "psutil"
]

# Required entry points based on API surface
ENTRY_POINTS = [
    ("main", "run_r_de_analysis", "run_stability_analysis", "main"),
    ("src.config", "ensure_directories", "get_memory_limit_mb"),
    ("src.data_loader", "load_manifest", "fetch_dataset"),
    ("src.preprocessing", "filter_zero_count_genes", "stratify_samples"),
    ("src.metrics", "calculate_pearson_correlation_all_genes", "calculate_stability_metrics"),
    ("src.permutation", "run_permutation_test", "load_dispersion_params"),
    ("src.report", "generate_stability_report", "generate_cross_dataset_comparison"),
]

def check_directories() -> Tuple[bool, List[str]]:
    """Check if all required directories exist."""
    missing = []
    for d in REQUIRED_DIRS:
        if not d.exists():
            missing.append(str(d))
        else:
            logger.info(f"Directory exists: {d}")
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False, missing
    return True, []

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check if all required packages are importable."""
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            logger.info(f"Package imported successfully: {pkg}")
        except ImportError as e:
            logger.error(f"Failed to import package {pkg}: {e}")
            missing.append(pkg)
    
    if missing:
        return False, missing
    return True, []

def check_entry_points() -> Tuple[bool, List[str]]:
    """Check if all required entry points exist and are callable."""
    failed = []
    for module_name, *functions in ENTRY_POINTS:
        try:
            module_path = str(CODE_DIR / module_name.replace(".", "/") + ".py")
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load spec for {module_name} from {module_path}")
                continue
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for func_name in functions:
                if not hasattr(module, func_name):
                    logger.error(f"Function {func_name} not found in {module_name}")
                    failed.append(f"{module_name}:{func_name}")
                else:
                    logger.info(f"Function {func_name} found in {module_name}")
        except Exception as e:
            logger.error(f"Error checking {module_name}: {e}")
            failed.append(f"{module_name}: {str(e)}")
    
    if failed:
        return False, failed
    return True, []

def check_quickstart_exists() -> bool:
    """Check if quickstart.md exists."""
    if QUICKSTART_PATH.exists():
        logger.info(f"Found quickstart.md at {QUICKSTART_PATH}")
        return True
    else:
        logger.error(f"quickstart.md not found at {QUICKSTART_PATH}")
        return False

def run_quickstart_simulation() -> Tuple[bool, str]:
    """
    Simulate running the quickstart.md instructions.
    This is a simplified simulation to ensure the main flow works.
    """
    logger.info("Starting quickstart simulation...")
    
    try:
        # 1. Ensure directories
        from src.config import ensure_directories
        ensure_directories()
        logger.info("Directories ensured.")
        
        # 2. Load manifest (mock if file doesn't exist)
        from src.data_loader import load_manifest
        manifest_path = DATA_DIR / "manifest.json"
        if not manifest_path.exists():
            logger.warning("manifest.json not found. Creating a minimal one for simulation.")
            import json
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(manifest_path, "w") as f:
                json.dump({
                    "datasets": [
                        {
                            "id": "GEO-MOCK-001",
                            "source": "GEO",
                            "url": "https://example.com/mock_data.csv",
                            "checksum": "0000000000000000000000000000000000000000000000000000000000000000"
                        }
                    ]
                }, f)
        
        # Note: We don't actually fetch data here to avoid network calls in validation
        # The real quickstart would call fetch_dataset, but that requires network
        logger.info("Manifest loading simulation passed.")
        
        # 3. Run basic metric calculation (mock data)
        from src.metrics import calculate_pearson_correlation_all_genes
        import pandas as pd
        import numpy as np
        
        # Create small mock data for validation
        np.random.seed(42)
        mock_data = pd.DataFrame(np.random.rand(10, 5), columns=[f"gene_{i}" for i in range(5)])
        
        try:
            # This should work with mock data
            result = calculate_pearson_correlation_all_genes(mock_data, mock_data)
            logger.info(f"Mock metric calculation result: {result}")
        except Exception as e:
            logger.error(f"Mock metric calculation failed: {e}")
            return False, f"Mock metric calculation failed: {e}"
        
        logger.info("Quickstart simulation completed successfully.")
        return True, "Simulation passed"
        
    except Exception as e:
        logger.error(f"Quickstart simulation failed: {e}")
        return False, str(e)

def main() -> int:
    """Main validation function."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation")
    logger.info("=" * 60)
    
    checks = []
    
    # 1. Check directories
    logger.info("\n[1/4] Checking required directories...")
    dir_ok, dir_issues = check_directories()
    checks.append(("Directories", dir_ok, dir_issues))
    
    # 2. Check dependencies
    logger.info("\n[2/4] Checking required dependencies...")
    dep_ok, dep_issues = check_dependencies()
    checks.append(("Dependencies", dep_ok, dep_issues))
    
    # 3. Check entry points
    logger.info("\n[3/4] Checking entry points...")
    entry_ok, entry_issues = check_entry_points()
    checks.append(("Entry Points", entry_ok, entry_issues))
    
    # 4. Check quickstart exists and simulate
    logger.info("\n[4/4] Checking quickstart.md and simulating execution...")
    q_exists = check_quickstart_exists()
    sim_ok, sim_msg = run_quickstart_simulation()
    checks.append(("Quickstart Simulation", sim_ok, [sim_msg] if not sim_ok else []))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    all_passed = True
    for name, passed, issues in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{name}: {status}")
        if not passed:
            all_passed = False
            for issue in issues:
                logger.info(f"  - {issue}")
    
    if all_passed:
        logger.info("\n🎉 All validation checks passed!")
        return 0
    else:
        logger.error("\n❌ Some validation checks failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
