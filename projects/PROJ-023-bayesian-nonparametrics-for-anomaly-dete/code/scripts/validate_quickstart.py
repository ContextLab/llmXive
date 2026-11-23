"""
Validation script for quickstart.md to ensure documentation matches implementation.

This script verifies that:
1. All commands in quickstart.md can be executed
2. All expected output files are generated
3. All file paths match the specification in tasks.md
4. The pipeline runs end-to-end successfully
"""

import os
import sys
import subprocess
import argparse
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Expected files and directories based on tasks.md
EXPECTED_DIRECTORIES = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "paper",
    "paper/figures",
    "contracts",
    "tests",
    "specs",
]

EXPECTED_SCRIPTS = [
    "code/scripts/download_data.py",
    "code/scripts/inject_anomalies.py",
    "code/scripts/bayesian_gp.py",
    "code/scripts/baseline_shewhart.py",
    "code/scripts/baseline_cusum.py",
    "code/scripts/baseline_vae.py",
    "code/scripts/evaluate.py",
    "code/scripts/sensitivity_analysis.py",
    "code/scripts/render_fig1.py",
    "code/scripts/render_fig2.py",
    "code/scripts/verify_paths.py",
]

EXPECTED_LIBRARIES = [
    "code/lib/data_loader.py",
    "code/lib/anomaly_injector.py",
    "code/lib/metrics.py",
    "code/lib/utils.py",
]

EXPECTED_OUTPUTS = [
    "data/raw/series.csv",
    "data/processed/series_with_anomalies.csv",
    "data/processed/ground_truth.csv",
    "data/results/bayesian_predictions.csv",
    "data/results/shewhart_predictions.csv",
    "data/results/cusum_predictions.csv",
    "data/results/vae_predictions.csv",
    "data/results/evaluation.json",
    "data/results/sensitivity_analysis.json",
    "paper/figures/fig1_timeseries.png",
    "paper/figures/fig2_method_comparison.png",
    "paper/results.md",
    "data/PROVENANCE.md",
    "data/VERSION.txt",
]

EXPECTED_CONTRACTS = [
    "contracts/dataset.schema.yaml",
    "contracts/evaluation.schema.yaml",
    "contracts/prediction.schema.yaml",
]

QUICKSTART_COMMANDS = [
    {
        "name": "Verify project structure",
        "command": ["python", "code/scripts/verify_paths.py"],
        "description": "Check that all file paths match specification"
    },
    {
        "name": "Download data",
        "command": ["python", "code/scripts/download_data.py"],
        "description": "Fetch real time series data from UCR/UCI"
    },
    {
        "name": "Inject anomalies",
        "command": ["python", "code/scripts/inject_anomalies.py"],
        "description": "Inject synthetic anomalies with known ground truth"
    },
    {
        "name": "Run Bayesian GP",
        "command": ["python", "code/scripts/bayesian_gp.py"],
        "description": "Execute Bayesian nonparametric anomaly detection"
    },
    {
        "name": "Run baseline methods",
        "command": ["python", "code/scripts/baseline_shewhart.py"],
        "description": "Execute Shewhart baseline"
    },
    {
        "name": "Run CUSUM baseline",
        "command": ["python", "code/scripts/baseline_cusum.py"],
        "description": "Execute CUSUM baseline"
    },
    {
        "name": "Run VAE baseline",
        "command": ["python", "code/scripts/baseline_vae.py"],
        "description": "Execute VAE baseline"
    },
    {
        "name": "Evaluate results",
        "command": ["python", "code/scripts/evaluate.py"],
        "description": "Calculate metrics and statistical significance"
    },
    {
        "name": "Sensitivity analysis",
        "command": ["python", "code/scripts/sensitivity_analysis.py"],
        "description": "Sweep decision thresholds"
    },
    {
        "name": "Generate Figure 1",
        "command": ["python", "code/scripts/render_fig1.py"],
        "description": "Plot time series with anomalies"
    },
    {
        "name": "Generate Figure 2",
        "command": ["python", "code/scripts/render_fig2.py"],
        "description": "Plot method comparison"
    },
]

def check_directory_exists(path: Path) -> bool:
    """Check if a directory exists."""
    return path.exists() and path.is_dir()

def check_file_exists(path: Path) -> bool:
    """Check if a file exists."""
    return path.exists() and path.is_file()

def run_command(command: List[str], cwd: Optional[Path] = None) -> Tuple[bool, str, str]:
    """Run a command and return success status, stdout, and stderr."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out after 1 hour"
    except Exception as e:
        return False, "", str(e)

def validate_structure() -> bool:
    """Validate project structure matches specification."""
    logger.info("Validating project structure...")
    all_valid = True

    # Check directories
    for dir_path in EXPECTED_DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        if not check_directory_exists(full_path):
            logger.error(f"Missing directory: {full_path}")
            all_valid = False
        else:
            logger.info(f"✓ Directory exists: {full_path}")

    # Check scripts
    for script_path in EXPECTED_SCRIPTS:
        full_path = PROJECT_ROOT / script_path
        if not check_file_exists(full_path):
            logger.error(f"Missing script: {full_path}")
            all_valid = False
        else:
            logger.info(f"✓ Script exists: {full_path}")

    # Check libraries
    for lib_path in EXPECTED_LIBRARIES:
        full_path = PROJECT_ROOT / lib_path
        if not check_file_exists(full_path):
            logger.error(f"Missing library: {full_path}")
            all_valid = False
        else:
            logger.info(f"✓ Library exists: {full_path}")

    # Check contracts
    for contract_path in EXPECTED_CONTRACTS:
        full_path = PROJECT_ROOT / contract_path
        if not check_file_exists(full_path):
            logger.error(f"Missing contract: {full_path}")
            all_valid = False
        else:
            logger.info(f"✓ Contract exists: {full_path}")

    return all_valid

def validate_outputs() -> bool:
    """Validate that all expected output files exist."""
    logger.info("Validating output files...")
    all_valid = True

    for output_path in EXPECTED_OUTPUTS:
        full_path = PROJECT_ROOT / output_path
        if not check_file_exists(full_path):
            logger.warning(f"Missing output file: {full_path}")
            # Don't mark as failed - these are generated by running the pipeline
            all_valid = False
        else:
            logger.info(f"✓ Output file exists: {full_path}")

    return all_valid

def run_quickstart_commands() -> bool:
    """Run all quickstart commands and verify they succeed."""
    logger.info("Running quickstart commands...")
    all_success = True

    for cmd_info in QUICKSTART_COMMANDS:
        name = cmd_info["name"]
        command = cmd_info["command"]
        description = cmd_info["description"]

        logger.info(f"Running: {name}")
        logger.info(f"  Description: {description}")

        success, stdout, stderr = run_command(command)

        if success:
            logger.info(f"  ✓ {name} completed successfully")
            if stdout:
                logger.debug(f"  Output: {stdout[:200]}...")
        else:
            logger.error(f"  ✗ {name} failed")
            logger.error(f"  Error: {stderr}")
            all_success = False

    return all_success

def validate_python_imports() -> bool:
    """Validate that all Python files can be imported without errors."""
    logger.info("Validating Python imports...")
    all_valid = True

    # Add code directory to Python path
    sys.path.insert(0, str(PROJECT_ROOT / "code"))

    # Test imports for each script
    script_modules = [
        "scripts.download_data",
        "scripts.inject_anomalies",
        "scripts.bayesian_gp",
        "scripts.baseline_shewhart",
        "scripts.baseline_cusum",
        "scripts.baseline_vae",
        "scripts.evaluate",
        "scripts.sensitivity_analysis",
        "scripts.render_fig1",
        "scripts.render_fig2",
        "scripts.verify_paths",
        "lib.data_loader",
        "lib.anomaly_injector",
        "lib.metrics",
        "lib.utils",
    ]

    for module_name in script_modules:
        try:
            __import__(module_name)
            logger.info(f"✓ Successfully imported: {module_name}")
        except ImportError as e:
            logger.error(f"✗ Failed to import {module_name}: {e}")
            all_valid = False
        except Exception as e:
            logger.error(f"✗ Error importing {module_name}: {e}")
            all_valid = False

    return all_valid

def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate quickstart.md documentation against implementation"
    )
    parser.add_argument(
        "--skip-commands",
        action="store_true",
        help="Skip running the actual pipeline commands"
    )
    parser.add_argument(
        "--skip-imports",
        action="store_true",
        help="Skip Python import validation"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any missing output files"
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Starting quickstart validation")
    logger.info("=" * 60)

    results = {
        "structure": False,
        "outputs": False,
        "commands": False,
        "imports": False,
        "overall": False
    }

    # Step 1: Validate structure
    results["structure"] = validate_structure()

    # Step 2: Validate outputs (warning if missing, but not failing unless strict)
    results["outputs"] = validate_outputs()
    if args.strict and not results["outputs"]:
        logger.error("Strict mode: Missing output files cause failure")
        results["overall"] = False
    else:
        logger.info("Output files will be generated by running commands")

    # Step 3: Run quickstart commands
    if not args.skip_commands:
        results["commands"] = run_quickstart_commands()

    # Step 4: Validate Python imports
    if not args.skip_imports:
        results["imports"] = validate_python_imports()

    # Final result
    results["overall"] = (
        results["structure"] and
        (args.strict or results["outputs"]) and
        (args.skip_commands or results["commands"]) and
        (args.skip_imports or results["imports"])
    )

    logger.info("=" * 60)
    logger.info("Validation Summary")
    logger.info("=" * 60)
    logger.info(f"Structure: {'✓ PASS' if results['structure'] else '✗ FAIL'}")
    logger.info(f"Outputs: {'✓ PASS' if results['outputs'] else '✗ FAIL'}")
    logger.info(f"Commands: {'✓ PASS' if results['commands'] else '✗ FAIL'}")
    logger.info(f"Imports: {'✓ PASS' if results['imports'] else '✗ FAIL'}")
    logger.info(f"Overall: {'✓ PASS' if results['overall'] else '✗ FAIL'}")
    logger.info("=" * 60)

    if results["overall"]:
        logger.info("✓ All validations passed!")
        return 0
    else:
        logger.error("✗ Some validations failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())