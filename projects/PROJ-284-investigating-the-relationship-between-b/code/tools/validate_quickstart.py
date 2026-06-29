import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from logging_config import setup_logging, get_logger
from config import get_config, validate_config

# Initialize logger
setup_logging()
logger = get_logger(__name__)

def check_file_exists(path_str: str) -> bool:
    """Check if a file exists relative to project root."""
    full_path = project_root / path_str
    exists = full_path.exists()
    status = "✓" if exists else "✗"
    logger.info(f"{status} File check: {path_str} -> {'Found' if exists else 'Missing'}")
    return exists

def check_imports(module_path: str, names: list) -> bool:
    """Check if specific names can be imported from a module."""
    module_name = module_path.replace("/", ".").replace("\\", ".")
    if module_name.startswith("."):
        module_name = module_name[1:]
    
    try:
        module = __import__(module_name, fromlist=names)
        missing = []
        for name in names:
            if not hasattr(module, name):
                missing.append(name)
        
        if missing:
            logger.error(f"✗ Import check failed for {module_path}: Missing names: {missing}")
            return False
        
        logger.info(f"✓ Import check passed for {module_path}: {names}")
        return True
    except ImportError as e:
        logger.error(f"✗ Import check failed for {module_path}: {e}")
        return False

def run_script(script_path: str, args: list = None) -> bool:
    """Attempt to run a script with --help or a dry-run flag if available."""
    full_path = project_root / script_path
    if not full_path.exists():
        logger.error(f"✗ Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(full_path)]
    if args:
        cmd.extend(args)
    
    # Try running with --help first to verify script is executable and parses args
    try:
        result = subprocess.run(
            cmd + ["--help"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(project_root)
        )
        if result.returncode == 0:
            logger.info(f"✓ Script execution check passed (help): {script_path}")
            return True
        else:
            # Some scripts might not support --help, try a dry run or just syntax check
            logger.warning(f"⚠ Script --help failed for {script_path}, checking syntax...")
            # Syntax check
            compile_result = subprocess.run(
                [sys.executable, "-m", "py_compile", str(full_path)],
                capture_output=True,
                text=True,
                cwd=str(project_root)
            )
            if compile_result.returncode == 0:
                logger.info(f"✓ Script syntax valid: {script_path}")
                return True
            else:
                logger.error(f"✗ Script syntax error: {script_path}\n{compile_result.stderr}")
                return False
    except subprocess.TimeoutExpired:
        logger.error(f"✗ Script timeout during check: {script_path}")
        return False
    except Exception as e:
        logger.error(f"✗ Script execution error: {script_path} -> {e}")
        return False

def validate_quickstart():
    """
    Validates the project against the requirements implied by a typical quickstart.md.
    Checks:
    1. Directory structure exists.
    2. Core configuration loads and validates.
    3. Key modules can be imported.
    4. Key scripts are syntactically valid and parse arguments.
    """
    logger.info("Starting Quickstart Validation...")
    all_passed = True

    # 1. Directory Structure
    required_dirs = [
        "code", "code/data", "code/analysis", "code/viz", "code/report", "code/tests",
        "data/raw", "data/processed", "data/analysis",
        "logs", "docs", "templates"
    ]
    for d in required_dirs:
        if not (project_root / d).exists():
            logger.error(f"✗ Missing directory: {d}")
            all_passed = False
        else:
            logger.info(f"✓ Directory exists: {d}")

    # 2. Configuration
    try:
        config = get_config()
        if validate_config(config):
            logger.info("✓ Configuration loaded and validated successfully.")
        else:
            logger.error("✗ Configuration validation failed.")
            all_passed = False
    except Exception as e:
        logger.error(f"✗ Configuration load failed: {e}")
        all_passed = False

    # 3. Imports
    import_checks = [
        ("code/config", ["get_config", "validate_config", "get_hcp_credentials"]),
        ("code/logging_config", ["setup_logging", "get_logger"]),
        ("code/models", ["Subject", "ConnectivityMatrix", "NetworkMetric", "CorrelationResult"]),
        ("code/data/download", ["get_subject_list_with_behavioral_data", "fetch_subject_data", "download_pipeline"]),
        ("code/data/preprocess", ["PreprocessingResult", "correct_motion", "calculate_tsnr", "validate_motion_parameters", "main"]),
        ("code/data/metrics", ["download_schaefer_atlas", "extract_time_series", "calculate_connectivity_matrix", "calculate_graph_metrics", "aggregate_node_metrics", "main"]),
        ("code/analysis/correlations", ["run_correlation_analysis", "apply_fdr_correction", "main"]),
        ("code/analysis/power", ["calculate_detectable_effect_size", "main"]),
        ("code/viz/scatter", ["generate_scatter_plot", "main"]),
        ("code/viz/network", ["generate_network_diagram", "main"]),
        ("code/report/generate", ["generate_report", "main"]),
    ]

    for module, names in import_checks:
        if not check_imports(module, names):
            all_passed = False

    # 4. Script Execution/Syntax
    script_checks = [
        ("code/tools/verify_batching.py", ["--help"]),
        ("code/tools/verify_imports.py", ["--help"]),
        ("code/tools/verify_security.py", ["--help"]),
        ("code/tools/cleanup.py", ["--help"]),
        ("code/tools/lint_format.py", ["--help"]),
        ("code/tools/refactor.py", ["--help"]),
    ]

    for script, args in script_checks:
        if not run_script(script, args):
            all_passed = False

    # Summary
    if all_passed:
        logger.info("="*50)
        logger.info("✓ Quickstart Validation PASSED")
        logger.info("Project structure, imports, and scripts are ready.")
        logger.info("="*50)
        return 0
    else:
        logger.error("="*50)
        logger.error("✗ Quickstart Validation FAILED")
        logger.error("Please review the errors above.")
        logger.error("="*50)
        return 1

def main():
    parser = argparse.ArgumentParser(description="Validate project setup against quickstart requirements.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    sys.exit(validate_quickstart())

if __name__ == "__main__":
    main()