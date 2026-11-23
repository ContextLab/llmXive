"""
Quickstart Validator for PROJ-057.
Validates the entire pipeline end-to-end to ensure reproducibility on fresh runners.
Executes the full flow: Setup -> Generate -> Compile -> Run -> Analyze -> Viz.
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
import logging

# Ensure code directory is in path
CODE_ROOT = Path(__file__).parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from utils.logger import setup_logging, get_logger
from benchmarks.tensor_generator import main as gen_main
from benchmarks.reference import main as ref_main
from benchmarks.compile_runner import main as compile_main
from benchmarks.executor import main as exec_main
from analysis.stability_check import main as stability_main
from analysis.stats import main as stats_main
from analysis.viz import main as viz_main
from utils.manifest_generator import main as manifest_main

logger = None

def log_info(msg: str):
    if logger:
        logger.info(msg)
    else:
        print(f"[INFO] {msg}")

def log_error(msg: str):
    if logger:
        logger.error(msg)
    else:
        print(f"[ERROR] {msg}")

def run_command(cmd: list, description: str) -> bool:
    """Execute a shell command and return True if successful."""
    log_info(f"Running: {description}")
    log_info(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=CODE_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes per step
        )
        if result.returncode != 0:
            log_error(f"Command failed: {description}")
            log_error(f"Stdout: {result.stdout}")
            log_error(f"Stderr: {result.stderr}")
            return False
        return True
    except subprocess.TimeoutExpired:
        log_error(f"Command timed out: {description}")
        return False
    except Exception as e:
        log_error(f"Exception running {description}: {str(e)}")
        return False

def validate_quickstart(args):
    """
    Orchestrates the full validation flow.
    This script is designed to be run on a fresh runner to verify reproducibility.
    """
    global logger
    logger = setup_logging(level=logging.INFO)
    log_info("Starting Quickstart Validation for PROJ-057")
    log_info(f"Working directory: {CODE_ROOT}")

    # 1. Verify Directory Structure (T001, T004)
    required_dirs = [
        "code/kernels", "code/benchmarks", "code/analysis", "code/utils",
        "data/raw", "data/intermediates", "data/results", "tests"
    ]
    for d in required_dirs:
        if not (CODE_ROOT / d).exists():
            log_error(f"Missing required directory: {d}")
            return False
    log_info("Directory structure verified.")

    # 2. Generate Tensors (T005)
    # We run the generator to create the raw input data
    if not run_command(
        [sys.executable, "benchmarks/tensor_generator.py", "--seed", "42", "--size", "512"],
        "Generate synthetic tensors"
    ):
        return False
    if not (CODE_ROOT.parent / "data" / "raw").exists():
        # Check relative to code root if data is sibling
        if not (CODE_ROOT / ".." / "data" / "raw").exists():
             log_error("Failed to generate raw tensors")
             return False

    # 3. Generate Reference (T006)
    if not run_command(
        [sys.executable, "benchmarks/reference.py", "--size", "512"],
        "Generate high-precision reference tensors"
    ):
        return False

    # 4. Compile Kernels (T014)
    # This compiles the C++ kernels with various flags
    if not run_command(
        [sys.executable, "benchmarks/compile_runner.py", "--test"],
        "Compile and test kernels"
    ):
        return False

    # 5. Execute Benchmarks (T015)
    # Runs the compiled binaries and measures latency
    if not run_command(
        [sys.executable, "benchmarks/executor.py", "--size", "512", "--iterations", "100"], # Reduced iterations for validation speed
        "Execute compiled kernels"
    ):
        return False

    # 6. Stability Analysis (T017, T020-T023)
    if not run_command(
        [sys.executable, "analysis/stability_check.py"],
        "Perform stability analysis"
    ):
        return False

    # 7. Statistical Analysis (T027-T029)
    if not run_command(
        [sys.executable, "analysis/stats.py"],
        "Perform statistical analysis"
    ):
        return False

    # 8. Visualization (T030, T031)
    if not run_command(
        [sys.executable, "analysis/viz.py"],
        "Generate Pareto frontier plots"
    ):
        return False

    # 9. Manifest Generation (T034)
    if not run_command(
        [sys.executable, "utils/manifest_generator.py"],
        "Generate data manifest"
    ):
        return False

    # 10. Verify Outputs
    log_info("Verifying output artifacts...")
    required_outputs = [
        "data/raw/tensor_*.bin",
        "data/intermediates/raw_logs/*.jsonl",
        "data/results/stability_metrics.csv",
        "data/results/aggregated.csv",
        "data/results/pareto_frontier_exploration.png",
        "data/results/pareto_frontier_final.png",
        "data/manifest.json"
    ]
    
    # Check for existence of at least one file matching patterns
    found = False
    for pattern in required_outputs:
        # Simple glob check
        matches = list((CODE_ROOT.parent).glob(pattern))
        if not matches:
            # Check relative to code root if needed
            matches = list(CODE_ROOT.glob(pattern))
        
        if not matches:
            log_error(f"Missing required output: {pattern}")
            return False
        found = True

    if found:
        log_info("All required output artifacts verified.")
    
    log_info("Quickstart Validation PASSED.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Validate PROJ-057 Quickstart Reproducibility")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    success = validate_quickstart(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()