"""
Quickstart Validation Script for PROJ-044
Validates end-to-end reproducibility by checking all required artifacts
exist and are consistent with the project specification.
"""

import os
import sys
import subprocess
from pathlib import Path
import logging
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent
REQUIRED_DIRS = [
    "code",
    "code/data",
    "code/training",
    "code/analysis",
    "code/models",
    "code/validation",
    "tests",
    "tests/unit",
    "tests/integration",
    "data",
    "data/raw",
    "data/partitions",
    "results",
    "results/plots"
]

REQUIRED_FILES = [
    "requirements.txt",
    ".pre-commit-config.yaml",
    "tree_output.txt",
    "data/raw/femnist.parquet",
    "data/raw/femnist.sha256",
    "results/summary.csv",
    "results/validation_report.md"
]

def check_directory_structure():
    """Verify all required directories exist."""
    logger.info("Checking directory structure...")
    missing = []
    for dir_path in REQUIRED_DIRS:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    if missing:
        logger.error(f"Missing directories: {missing}")
        return False
    
    logger.info("✓ All required directories exist")
    return True

def check_tree_output():
    """Verify tree_output.txt exists and contains expected content."""
    logger.info("Checking tree_output.txt...")
    tree_file = PROJECT_ROOT / "tree_output.txt"
    
    if not tree_file.exists():
        logger.error("tree_output.txt not found")
        return False
    
    content = tree_file.read_text()
    if len(content.strip()) < 100:
        logger.error("tree_output.txt is too small, likely invalid")
        return False
    
    logger.info("✓ tree_output.txt exists and has content")
    return True

def check_requirements():
    """Verify requirements.txt contains essential packages."""
    logger.info("Checking requirements.txt...")
    req_file = PROJECT_ROOT / "requirements.txt"
    
    if not req_file.exists():
        logger.error("requirements.txt not found")
        return False
    
    content = req_file.read_text().lower()
    required_packages = ["torch", "opacus", "pandas", "numpy", "matplotlib", "scipy"]
    missing = [pkg for pkg in required_packages if pkg not in content]
    
    if missing:
        logger.error(f"Missing required packages in requirements.txt: {missing}")
        return False
    
    logger.info("✓ requirements.txt contains all required packages")
    return True

def check_precommit_config():
    """Verify .pre-commit-config.yaml has required hooks."""
    logger.info("Checking .pre-commit-config.yaml...")
    config_file = PROJECT_ROOT / ".pre-commit-config.yaml"
    
    if not config_file.exists():
        logger.error(".pre-commit-config.yaml not found")
        return False
    
    content = config_file.read_text().lower()
    required_hooks = ["black", "ruff", "pre-commit-hooks"]
    missing = [hook for hook in required_hooks if hook not in content]
    
    if missing:
        logger.error(f"Missing required hooks in .pre-commit-config.yaml: {missing}")
        return False
    
    logger.info("✓ .pre-commit-config.yaml contains all required hooks")
    return True

def verify_checksum():
    """Verify data checksums match."""
    logger.info("Verifying data checksums...")
    data_file = PROJECT_ROOT / "data/raw/femnist.parquet"
    checksum_file = PROJECT_ROOT / "data/raw/femnist.sha256"
    
    if not data_file.exists():
        logger.error("data/raw/femnist.parquet not found")
        return False
    
    if not checksum_file.exists():
        logger.error("data/raw/femnist.sha256 not found")
        return False
    
    try:
        from data.checksum_utils import verify_checksum
        if not verify_checksum(data_file, checksum_file):
            logger.error("Checksum verification failed")
            return False
    except Exception as e:
        logger.error(f"Error during checksum verification: {e}")
        return False
    
    logger.info("✓ Data checksums verified")
    return True

def check_data_download():
    """Verify downloaded data file exists and has content."""
    logger.info("Checking downloaded data...")
    data_file = PROJECT_ROOT / "data/raw/femnist.parquet"
    
    if not data_file.exists():
        logger.error("data/raw/femnist.parquet not found")
        return False
    
    if data_file.stat().st_size == 0:
        logger.error("data/raw/femnist.parquet is empty")
        return False
    
    logger.info(f"✓ Data file exists ({data_file.stat().st_size} bytes)")
    return True

def check_partition_metadata():
    """Verify partition metadata files exist."""
    logger.info("Checking partition metadata...")
    partition_dir = PROJECT_ROOT / "data/partitions"
    
    if not partition_dir.exists():
        logger.error("data/partitions directory not found")
        return False
    
    json_files = list(partition_dir.glob("*.json"))
    if not json_files:
        logger.error("No partition metadata JSON files found")
        return False
    
    logger.info(f"✓ Found {len(json_files)} partition metadata files")
    return True

def check_training_logs():
    """Verify training logs exist."""
    logger.info("Checking training logs...")
    logs_file = PROJECT_ROOT / "results/raw_logs.csv"
    
    if not logs_file.exists():
        logger.error("results/raw_logs.csv not found")
        return False
    
    if logs_file.stat().st_size == 0:
        logger.error("results/raw_logs.csv is empty")
        return False
    
    logger.info("✓ Training logs exist")
    return True

def check_filtered_data():
    """Verify filtered data exists."""
    logger.info("Checking filtered data...")
    filtered_file = PROJECT_ROOT / "results/filtered_data.csv"
    
    if not filtered_file.exists():
        logger.error("results/filtered_data.csv not found")
        return False
    
    if filtered_file.stat().st_size == 0:
        logger.error("results/filtered_data.csv is empty")
        return False
    
    logger.info("✓ Filtered data exists")
    return True

def check_plots():
    """Verify analysis plots exist."""
    logger.info("Checking analysis plots...")
    plots_dir = PROJECT_ROOT / "results/plots"
    
    if not plots_dir.exists():
        logger.error("results/plots directory not found")
        return False
    
    png_files = list(plots_dir.glob("*.png"))
    if not png_files:
        logger.error("No PNG plots found in results/plots")
        return False
    
    logger.info(f"✓ Found {len(png_files)} plot files")
    return True

def check_summary_results():
    """Verify summary results exist."""
    logger.info("Checking summary results...")
    summary_file = PROJECT_ROOT / "results/summary.csv"
    report_file = PROJECT_ROOT / "results/validation_report.md"
    
    if not summary_file.exists():
        logger.error("results/summary.csv not found")
        return False
    
    if not report_file.exists():
        logger.error("results/validation_report.md not found")
        return False
    
    logger.info("✓ Summary results and validation report exist")
    return True

def run_validation_checks():
    """Run all validation checks and return results."""
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Tree Output", check_tree_output),
        ("Requirements", check_requirements),
        ("Pre-commit Config", check_precommit_config),
        ("Data Download", check_data_download),
        ("Checksum Verification", verify_checksum),
        ("Partition Metadata", check_partition_metadata),
        ("Training Logs", check_training_logs),
        ("Filtered Data", check_filtered_data),
        ("Plots", check_plots),
        ("Summary Results", check_summary_results),
    ]
    
    results = {}
    all_passed = True
    
    for name, check_func in checks:
        try:
            passed = check_func()
            results[name] = "PASS" if passed else "FAIL"
            if not passed:
                all_passed = False
        except Exception as e:
            logger.error(f"Error in {name}: {e}")
            results[name] = f"ERROR: {e}"
            all_passed = False
    
    return results, all_passed

def generate_report(results, all_passed):
    """Generate a validation report."""
    report_path = PROJECT_ROOT / "results" / "quickstart_validation_report.json"
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "project": "PROJ-044-evaluating-the-effectiveness-of-differen",
        "task": "T033 - Quickstart Validation",
        "overall_status": "PASSED" if all_passed else "FAILED",
        "checks": results
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {report_path}")
    return report

def main():
    """Main entry point for validation."""
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation for PROJ-044")
    logger.info("=" * 60)
    
    results, all_passed = run_validation_checks()
    report = generate_report(results, all_passed)
    
    logger.info("=" * 60)
    logger.info(f"Validation Result: {report['overall_status']}")
    logger.info("=" * 60)
    
    for check_name, status in results.items():
        status_symbol = "✓" if status == "PASS" else "✗"
        logger.info(f"  {status_symbol} {check_name}: {status}")
    
    if all_passed:
        logger.info("✓ All validation checks passed!")
        return 0
    else:
        logger.error("✗ Some validation checks failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
