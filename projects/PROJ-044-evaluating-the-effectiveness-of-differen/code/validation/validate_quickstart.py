"""
T033: Run quickstart.md validation to ensure end-to-end reproducibility.

This script validates the entire pipeline by:
1. Verifying project structure (T001)
2. Checking requirements (T002)
3. Verifying pre-commit config (T003)
4. Validating data download (T011)
5. Checking partition generation (T013)
6. Verifying training logs (T018b)
7. Validating filtered data (T035)
8. Checking plots (T026)
9. Verifying summary results (T028)
"""

import os
import sys
import subprocess
from pathlib import Path
import logging
import json
import pandas as pd
import hashlib
from typing import List, Tuple, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
VALIDATION_REPORT = PROJECT_ROOT / "results" / "quickstart_validation_report.json"

# Required paths based on tasks.md
REQUIRED_DIRS = [
    "code/data", "code/training", "code/analysis", "code/models",
    "tests/unit", "tests/integration", "data/raw", "data/partitions",
    "results", "artifacts", "figures"
]

REQUIRED_FILES = {
    "tree_output.txt": PROJECT_ROOT / "tree_output.txt",
    "requirements.txt": PROJECT_ROOT / "requirements.txt",
    ".pre-commit-config.yaml": PROJECT_ROOT / ".pre-commit-config.yaml",
    "femnist.parquet": PROJECT_ROOT / "data" / "raw" / "femnist.parquet",
    "femnist.sha256": PROJECT_ROOT / "data" / "raw" / "femnist.sha256",
    "raw_logs.csv": PROJECT_ROOT / "results" / "raw_logs.csv",
    "filtered_data.csv": PROJECT_ROOT / "results" / "filtered_data.csv",
    "summary.csv": PROJECT_ROOT / "results" / "summary.csv",
    "validation_report.md": PROJECT_ROOT / "results" / "validation_report.md"
}

# Expected plot files (T026)
PLOTS_DIR = PROJECT_ROOT / "results" / "plots"
REQUIRED_PLOTS = [
    "accuracy_gap_vs_alpha.png",
    "accuracy_vs_epsilon.png",
    "minority_degradation_overlay.png"
]

def check_directory_structure() -> Tuple[bool, List[str]]:
    """Verify all required directories exist."""
    logger.info("Checking directory structure...")
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing.append(str(full_path))
        elif not full_path.is_dir():
            missing.append(f"{full_path} (not a directory)")
    
    success = len(missing) == 0
    if success:
        logger.info("✓ All required directories exist")
    else:
        logger.error(f"✗ Missing directories: {missing}")
    return success, missing

def check_tree_output() -> Tuple[bool, Optional[str]]:
    """Verify tree_output.txt exists and contains expected content."""
    logger.info("Checking tree_output.txt...")
    tree_file = REQUIRED_FILES["tree_output.txt"]
    if not tree_file.exists():
        logger.error("✗ tree_output.txt does not exist")
        return False, "File missing"
    
    try:
        content = tree_file.read_text()
        if len(content) < 50:
            logger.error("✗ tree_output.txt is too small (likely empty)")
            return False, "File too small"
        
        # Check for some expected directories in the tree
        expected_dirs = ["code", "data", "results", "tests"]
        missing_dirs = [d for d in expected_dirs if d not in content]
        if missing_dirs:
            logger.error(f"✗ tree_output.txt missing expected directories: {missing_dirs}")
            return False, f"Missing dirs in tree: {missing_dirs}"
        
        logger.info("✓ tree_output.txt is valid")
        return True, None
    except Exception as e:
        logger.error(f"✗ Error reading tree_output.txt: {e}")
        return False, str(e)

def check_requirements() -> Tuple[bool, Optional[str]]:
    """Verify requirements.txt exists and contains key dependencies."""
    logger.info("Checking requirements.txt...")
    req_file = REQUIRED_FILES["requirements.txt"]
    if not req_file.exists():
        logger.error("✗ requirements.txt does not exist")
        return False, "File missing"
    
    try:
        content = req_file.read_text().lower()
        required_packages = ["torch", "opacus", "pandas", "numpy", "matplotlib", "scipy", "datasets"]
        missing_packages = [pkg for pkg in required_packages if pkg not in content]
        
        if missing_packages:
            logger.error(f"✗ requirements.txt missing packages: {missing_packages}")
            return False, f"Missing packages: {missing_packages}"
        
        logger.info("✓ requirements.txt is valid")
        return True, None
    except Exception as e:
        logger.error(f"✗ Error reading requirements.txt: {e}")
        return False, str(e)

def check_precommit_config() -> Tuple[bool, Optional[str]]:
    """Verify .pre-commit-config.yaml exists and contains required hooks."""
    logger.info("Checking .pre-commit-config.yaml...")
    precommit_file = REQUIRED_FILES[".pre-commit-config.yaml"]
    if not precommit_file.exists():
        logger.error("✗ .pre-commit-config.yaml does not exist")
        return False, "File missing"
    
    try:
        content = precommit_file.read_text().lower()
        required_hooks = ["black", "ruff", "pre-commit-hooks"]
        missing_hooks = [hook for hook in required_hooks if hook not in content]
        
        if missing_hooks:
            logger.error(f"✗ .pre-commit-config.yaml missing hooks: {missing_hooks}")
            return False, f"Missing hooks: {missing_hooks}"
        
        logger.info("✓ .pre-commit-config.yaml is valid")
        return True, None
    except Exception as e:
        logger.error(f"✗ Error reading .pre-commit-config.yaml: {e}")
        return False, str(e)

def verify_checksum(filepath: Path) -> Optional[str]:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {filepath}: {e}")
        return None

def check_data_download() -> Tuple[bool, List[str]]:
    """Verify FEMNIST data was downloaded correctly."""
    logger.info("Checking data download...")
    errors = []
    
    parquet_file = REQUIRED_FILES["femnist.parquet"]
    sha_file = REQUIRED_FILES["femnist.sha256"]
    
    if not parquet_file.exists():
        errors.append("femnist.parquet missing")
        logger.error("✗ femnist.parquet does not exist")
    else:
        try:
            df = pd.read_parquet(parquet_file)
            if len(df) == 0:
                errors.append("femnist.parquet is empty")
                logger.error("✗ femnist.parquet is empty")
            else:
                logger.info(f"✓ femnist.parquet loaded successfully ({len(df)} rows)")
        except Exception as e:
            errors.append(f"Error loading femnist.parquet: {e}")
            logger.error(f"✗ Error loading femnist.parquet: {e}")
    
    if not sha_file.exists():
        errors.append("femnist.sha256 missing")
        logger.error("✗ femnist.sha256 does not exist")
    else:
        try:
            with open(sha_file, 'r') as f:
                stored_hash = f.read().strip()
            
            computed_hash = verify_checksum(parquet_file)
            if computed_hash and stored_hash != computed_hash:
                errors.append(f"Checksum mismatch: stored={stored_hash[:16]}..., computed={computed_hash[:16]}...")
                logger.error("✗ Checksum mismatch for femnist.parquet")
            else:
                logger.info("✓ Checksum verification passed")
        except Exception as e:
            errors.append(f"Error verifying checksum: {e}")
            logger.error(f"✗ Error verifying checksum: {e}")
    
    success = len(errors) == 0
    if success:
        logger.info("✓ Data download validation passed")
    return success, errors

def check_partition_metadata() -> Tuple[bool, List[str]]:
    """Verify partition metadata files exist."""
    logger.info("Checking partition metadata...")
    errors = []
    
    partitions_dir = PROJECT_ROOT / "data" / "partitions"
    if not partitions_dir.exists():
        errors.append("partitions directory missing")
        logger.error("✗ data/partitions directory does not exist")
        return False, errors
    
    # Look for at least one partition file
    partition_files = list(partitions_dir.glob("partition_*.json"))
    if not partition_files:
        errors.append("No partition metadata files found")
        logger.error("✗ No partition metadata files found")
    else:
        logger.info(f"✓ Found {len(partition_files)} partition metadata file(s)")
        # Verify one file has expected schema
        try:
            with open(partition_files[0], 'r') as f:
                data = json.load(f)
            required_keys = {'client_id', 'label_distribution', 'total_samples'}
            if not required_keys.issubset(data.keys()):
                errors.append(f"Partition file missing required keys: {required_keys - set(data.keys())}")
                logger.error(f"✗ Partition file schema invalid")
            else:
                logger.info("✓ Partition metadata schema is valid")
        except Exception as e:
            errors.append(f"Error reading partition file: {e}")
            logger.error(f"✗ Error reading partition file: {e}")
    
    return len(errors) == 0, errors

def check_training_logs() -> Tuple[bool, Optional[str]]:
    """Verify training logs exist and have expected structure."""
    logger.info("Checking training logs...")
    logs_file = REQUIRED_FILES["raw_logs.csv"]
    
    if not logs_file.exists():
        logger.error("✗ raw_logs.csv does not exist")
        return False, "File missing"
    
    try:
        df = pd.read_csv(logs_file)
        required_columns = ['seed', 'alpha', 'epsilon', 'global_accuracy', 'minority_accuracy', 'majority_accuracy']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            logger.error(f"✗ raw_logs.csv missing columns: {missing_cols}")
            return False, f"Missing columns: {missing_cols}"
        
        if len(df) == 0:
            logger.error("✗ raw_logs.csv is empty")
            return False, "File empty"
        
        logger.info(f"✓ raw_logs.csv valid ({len(df)} rows, {len(df.columns)} columns)")
        return True, None
    except Exception as e:
        logger.error(f"✗ Error reading raw_logs.csv: {e}")
        return False, str(e)

def check_filtered_data() -> Tuple[bool, Optional[str]]:
    """Verify filtered data exists and has expected structure."""
    logger.info("Checking filtered data...")
    filtered_file = REQUIRED_FILES["filtered_data.csv"]
    
    if not filtered_file.exists():
        logger.error("✗ filtered_data.csv does not exist")
        return False, "File missing"
    
    try:
        df = pd.read_csv(filtered_file)
        required_columns = ['seed', 'alpha', 'epsilon', 'global_accuracy', 'minority_accuracy', 'majority_accuracy']
        missing_cols = [col for col in required_columns if col not in df.columns]
        
        if missing_cols:
            logger.error(f"✗ filtered_data.csv missing columns: {missing_cols}")
            return False, f"Missing columns: {missing_cols}"
        
        # Verify filtering actually happened
        raw_file = REQUIRED_FILES["raw_logs.csv"]
        if raw_file.exists():
            raw_df = pd.read_csv(raw_file)
            if len(df) >= len(raw_df):
                logger.warning("⚠ filtered_data.csv has same or more rows than raw_logs.csv (filtering may not have occurred)")
        
        logger.info(f"✓ filtered_data.csv valid ({len(df)} rows)")
        return True, None
    except Exception as e:
        logger.error(f"✗ Error reading filtered_data.csv: {e}")
        return False, str(e)

def check_plots() -> Tuple[bool, List[str]]:
    """Verify all required plot files exist."""
    logger.info("Checking plots...")
    errors = []
    
    if not PLOTS_DIR.exists():
        errors.append("plots directory missing")
        logger.error("✗ results/plots directory does not exist")
        return False, errors
    
    for plot_name in REQUIRED_PLOTS:
        plot_path = PLOTS_DIR / plot_name
        if not plot_path.exists():
            errors.append(f"{plot_name} missing")
            logger.error(f"✗ {plot_name} does not exist")
        else:
            # Check file size (should not be empty)
            if plot_path.stat().st_size < 1000:
                errors.append(f"{plot_name} is too small")
                logger.error(f"✗ {plot_name} is too small (likely empty)")
            else:
                logger.info(f"✓ {plot_name} exists ({plot_path.stat().st_size} bytes)")
    
    success = len(errors) == 0
    if success:
        logger.info("✓ All required plots exist")
    return success, errors

def check_summary_results() -> Tuple[bool, Optional[str]]:
    """Verify summary results and validation report exist."""
    logger.info("Checking summary results...")
    errors = []
    
    summary_file = REQUIRED_FILES["summary.csv"]
    report_file = REQUIRED_FILES["validation_report.md"]
    
    if not summary_file.exists():
        errors.append("summary.csv missing")
        logger.error("✗ summary.csv does not exist")
    else:
        try:
            df = pd.read_csv(summary_file)
            required_columns = ['seed', 'alpha', 'epsilon', 'global_accuracy', 'minority_accuracy', 'majority_accuracy', 'rounds_to_target', 'p_value_dp_vs_nondp', 'p_value_majority_vs_minority']
            missing_cols = [col for col in required_columns if col not in df.columns]
            
            if missing_cols:
                errors.append(f"summary.csv missing columns: {missing_cols}")
                logger.error(f"✗ summary.csv missing columns: {missing_cols}")
            else:
                logger.info(f"✓ summary.csv valid ({len(df)} rows)")
        except Exception as e:
            errors.append(f"Error reading summary.csv: {e}")
            logger.error(f"✗ Error reading summary.csv: {e}")
    
    if not report_file.exists():
        errors.append("validation_report.md missing")
        logger.error("✗ validation_report.md does not exist")
    else:
        try:
            content = report_file.read_text()
            if len(content) < 100:
                errors.append("validation_report.md is too small")
                logger.error("✗ validation_report.md is too small")
            else:
                logger.info(f"✓ validation_report.md valid ({len(content)} chars)")
        except Exception as e:
            errors.append(f"Error reading validation_report.md: {e}")
            logger.error(f"✗ Error reading validation_report.md: {e}")
    
    return len(errors) == 0, errors

def run_validation_checks() -> Dict[str, Any]:
    """Run all validation checks and return results."""
    results = {
        "timestamp": str(pd.Timestamp.now()),
        "checks": {},
        "overall_passed": True,
        "errors": []
    }
    
    checks = [
        ("directory_structure", check_directory_structure),
        ("tree_output", check_tree_output),
        ("requirements", check_requirements),
        ("precommit_config", check_precommit_config),
        ("data_download", check_data_download),
        ("partition_metadata", check_partition_metadata),
        ("training_logs", check_training_logs),
        ("filtered_data", check_filtered_data),
        ("plots", check_plots),
        ("summary_results", check_summary_results),
    ]
    
    for check_name, check_func in checks:
        logger.info(f"\n{'='*60}")
        logger.info(f"Running check: {check_name}")
        logger.info(f"{'='*60}")
        
        try:
            success, error_data = check_func()
            
            if isinstance(error_data, list):
                results["checks"][check_name] = {
                    "passed": success,
                    "errors": error_data
                }
                if not success:
                    results["overall_passed"] = False
                    results["errors"].extend(error_data)
            else:
                results["checks"][check_name] = {
                    "passed": success,
                    "error": error_data
                }
                if not success:
                    results["overall_passed"] = False
                    results["errors"].append(error_data)
            
            status = "PASSED" if success else "FAILED"
            logger.info(f"Check {check_name}: {status}")
            
        except Exception as e:
            logger.error(f"✗ Check {check_name} raised exception: {e}")
            results["checks"][check_name] = {
                "passed": False,
                "error": str(e)
            }
            results["overall_passed"] = False
            results["errors"].append(f"{check_name}: {e}")
    
    return results

def generate_report(results: Dict[str, Any]) -> None:
    """Generate and save the validation report."""
    report_path = VALIDATION_REPORT
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nValidation report saved to: {report_path}")
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("VALIDATION SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Overall Status: {'PASSED' if results['overall_passed'] else 'FAILED'}")
    logger.info(f"Total Checks: {len(results['checks'])}")
    passed_count = sum(1 for c in results['checks'].values() if c.get('passed', False))
    logger.info(f"Passed: {passed_count}/{len(results['checks'])}")
    
    if results['errors']:
        logger.info(f"\nErrors found ({len(results['errors'])}):")
        for i, error in enumerate(results['errors'], 1):
            logger.info(f"  {i}. {error}")
    
    logger.info(f"{'='*60}\n")

def main() -> int:
    """Main entry point for quickstart validation."""
    logger.info("Starting quickstart validation (T033)...")
    logger.info(f"Project root: {PROJECT_ROOT}")
    
    if not PROJECT_ROOT.exists():
        logger.error(f"✗ Project root does not exist: {PROJECT_ROOT}")
        return 1
    
    results = run_validation_checks()
    generate_report(results)
    
    if results['overall_passed']:
        logger.info("✓ All validation checks passed!")
        return 0
    else:
        logger.error("✗ Some validation checks failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())