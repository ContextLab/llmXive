import os
import sys
import json
import subprocess
import argparse
import logging
from pathlib import Path

# Add project root to path to ensure imports work if run as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / 'code'))

from config import load_config
from exceptions import FatalSieveError, BenchmarkFailure

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_file_exists(path_str: str) -> bool:
    """Check if a file or directory exists."""
    path = Path(path_str)
    if not path.exists():
        logger.error(f"Required path does not exist: {path_str}")
        return False
    return True

def validate_quickstart(args: argparse.Namespace) -> int:
    """
    Validate the quickstart.md instructions by executing the pipeline
    with a small N (e.g., 10000) to ensure reproducibility and correctness
    without exceeding time/memory budgets in a validation run.
    
    Returns 0 on success, 1 on failure.
    """
    logger.info("Starting Quickstart Validation...")
    
    # 1. Verify Directory Structure
    required_dirs = [
        "code",
        "data/raw", "data/processed",
        "results/plots", "results/reports",
        "tests/unit", "tests/integration"
    ]
    for d in required_dirs:
        if not check_file_exists(str(project_root / d)):
            logger.error(f"Directory check failed: {d}")
            return 1
    
    # 2. Verify Input Files
    if not check_file_exists(str(project_root / "quickstart.md")):
        logger.error("quickstart.md not found in project root.")
        return 1

    # 3. Execute Pipeline
    # We run the actual analysis script with a small N to verify the code path
    # works end-to-end. The quickstart typically suggests N=5M, but for validation
    # we use a smaller N to ensure the script runs quickly in a CI/fresh env.
    # However, we respect the CLI argument if provided, defaulting to a safe small N.
    run_script = project_root / "code" / "run_analysis.py"
    if not run_script.exists():
        logger.error("run_analysis.py not found.")
        return 1

    # Determine N to use. If user provided --n, use it. Otherwise use 10000 for validation.
    n_val = args.n if args.n else 10000
    primes = args.primes if args.primes else "3,5,7"
    
    cmd = [
        sys.executable, str(run_script),
        "--n", str(n_val),
        "--primes", primes,
        "--seed", "42"
    ]
    
    logger.info(f"Executing pipeline: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for validation
        )
        
        if result.returncode != 0:
            logger.error("Pipeline execution failed.")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            return 1
        
        logger.info("Pipeline execution completed successfully.")
        
    except subprocess.TimeoutExpired:
        logger.error("Pipeline execution timed out.")
        return 1
    except Exception as e:
        logger.error(f"Error running pipeline: {e}")
        return 1

    # 4. Verify Outputs
    # Check that expected output files were created
    output_checks = [
        f"data/raw/residues_3_{n_val}.json",
        f"data/processed/stats_3_{n_val}.json",
        "results/reports/summary_{N}.md".replace("{N}", str(n_val)), # Generic check
    ]
    
    # Specific check for the first prime in the list
    first_prime = int(primes.split(",")[0])
    expected_raw = f"data/raw/residues_{first_prime}_{n_val}.json"
    expected_stats = f"data/processed/stats_{first_prime}_{n_val}.json"
    
    if not check_file_exists(str(project_root / expected_raw)):
        logger.error(f"Missing raw output: {expected_raw}")
        return 1
    
    if not check_file_exists(str(project_root / expected_stats)):
        logger.error(f"Missing processed output: {expected_stats}")
        return 1

    # 5. Validate JSON Content (Sanity Check)
    try:
        with open(project_root / expected_raw, 'r') as f:
            data = json.load(f)
            if 'prime_modulus' not in data or 'frequency_map' not in data:
                logger.error("Raw data JSON missing required fields.")
                return 1
            if data['prime_modulus'] != first_prime:
                logger.error(f"Raw data prime mismatch: expected {first_prime}, got {data['prime_modulus']}")
                return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in raw output: {e}")
        return 1

    try:
        with open(project_root / expected_stats, 'r') as f:
            data = json.load(f)
            if 'p_value' not in data or 'pass_fail_flag' not in data:
                logger.error("Stats data JSON missing required fields.")
                return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in stats output: {e}")
        return 1

    logger.info("Quickstart validation PASSED.")
    return 0

def main():
    parser = argparse.ArgumentParser(description="Validate quickstart.md reproducibility")
    parser.add_argument("--n", type=int, default=None, help="N value to run (default: 10000 for validation)")
    parser.add_argument("--primes", type=str, default="3,5,7", help="Comma-separated primes")
    args = parser.parse_args()
    
    exit_code = validate_quickstart(args)
    sys.exit(exit_code)

if __name__ == "__main__":
    main()