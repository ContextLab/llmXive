"""
Integration test for the twin prime generation pipeline (US1).

Verifies:
1. The generation script `code/generate_primes.py` executes successfully.
2. The output file `data/raw/twin_primes.csv` is created.
3. The CSV contains the expected columns: p, p_next, delta, normalized_gap.
4. The row count is within ±5% of the theoretical expectation based on the
   Hardy-Littlewood conjecture for twin primes up to 10^9.
"""
import os
import sys
import subprocess
import csv
import math
import logging
from pathlib import Path

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (assumes tests/integration is 2 levels deep)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "code" / "generate_primes.py"
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "twin_primes.csv"

# Theoretical constants
# Twin Prime Constant (Hardy-Littlewood)
# C2 ≈ 0.66016181584686957392781211001455577843262336028473
TWIN_PRIME_CONSTANT = 0.66016181584686957392781211001455577843262336028473
LIMIT = 1_000_000_000  # 10^9

def get_theoretical_count(limit: int) -> float:
    """
    Estimates the number of twin prime pairs up to `limit` using the
    Hardy-Littlewood conjecture:
    π₂(x) ~ 2 * C2 * x / (log x)^2
    """
    if limit < 2:
        return 0.0
    log_x = math.log(limit)
    return 2.0 * TWIN_PRIME_CONSTANT * limit / (log_x * log_x)

def run_generation_script() -> bool:
    """
    Executes the generation script and returns True if it exits with code 0.
    """
    logger.info(f"Executing generation script: {SCRIPT_PATH}")
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Script failed with code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            return False
        
        logger.info("Script executed successfully.")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Script execution timed out.")
        return False
    except Exception as e:
        logger.error(f"Failed to execute script: {e}")
        return False

def validate_output_file() -> bool:
    """
    Validates the existence, schema, and row count of the generated CSV.
    """
    if not OUTPUT_PATH.exists():
        logger.error(f"Output file not found: {OUTPUT_PATH}")
        return False

    logger.info(f"Validating output file: {OUTPUT_PATH}")
    
    expected_columns = {'p', 'p_next', 'delta', 'normalized_gap'}
    row_count = 0
    
    try:
        with open(OUTPUT_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check headers
            if not reader.fieldnames:
                logger.error("CSV file is empty or has no headers.")
                return False
            
            actual_columns = set(reader.fieldnames)
            if not expected_columns.issubset(actual_columns):
                missing = expected_columns - actual_columns
                logger.error(f"Missing columns: {missing}")
                return False
            
            # Count rows
            for row in reader:
                row_count += 1
                
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return False

    logger.info(f"Generated {row_count} rows.")

    # Theoretical expectation check
    theoretical = get_theoretical_count(LIMIT)
    lower_bound = theoretical * 0.95
    upper_bound = theoretical * 1.05
    
    logger.info(f"Theoretical expectation (±5%): [{lower_bound:.0f}, {upper_bound:.0f}]")
    logger.info(f"Actual count: {row_count}")

    if not (lower_bound <= row_count <= upper_bound):
        logger.error(f"Row count {row_count} is outside expected range [{lower_bound:.0f}, {upper_bound:.0f}].")
        return False

    if row_count == 0:
        logger.error("Row count is zero.")
        return False

    return True

def test_generation_pipeline():
    """
    Main test entry point.
    """
    logger.info("Starting Integration Test for Twin Prime Generation (T011).")
    
    # Step 1: Run the script
    if not run_generation_script():
        logger.error("Test FAILED: Generation script did not complete successfully.")
        sys.exit(1)

    # Step 2: Validate the output
    if not validate_output_file():
        logger.error("Test FAILED: Output validation failed.")
        sys.exit(1)

    logger.info("Test PASSED: Generation pipeline verified successfully.")
    sys.exit(0)

if __name__ == "__main__":
    test_generation_pipeline()