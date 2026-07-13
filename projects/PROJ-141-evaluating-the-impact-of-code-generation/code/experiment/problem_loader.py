import os
import sys
import json
import logging
import hashlib
import random
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
HUMAN_EVAL_PATH = "data/humaneval/human-eval.jsonl"
CODEFORCES_PATH = "data/codeforces/problems.json"
SAMPLE_SIZE = 100
TARGET_LOAD_RATE = 0.95

def compute_file_hash(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return ""

def load_humaneval_problems(sample_size: int = SAMPLE_SIZE) -> Tuple[List[Dict], int]:
    """
    Load HumanEval problems from the downloaded dataset.
    Returns a list of successfully loaded problems and the count.
    """
    problems = []
    success_count = 0
    
    if not os.path.exists(HUMAN_EVAL_PATH):
        logger.warning(f"HumanEval dataset not found at {HUMAN_EVAL_PATH}. Skipping.")
        return problems, success_count

    try:
        with open(HUMAN_EVAL_PATH, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f):
                if line_num >= sample_size:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    problem = json.loads(line)
                    # Basic validation: ensure required fields exist
                    if 'prompt' in problem and 'canonical_solution' in problem:
                        problems.append(problem)
                        success_count += 1
                    else:
                        logger.debug(f"Skipping line {line_num}: missing required fields")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON at line {line_num}: {e}")
                    continue
    except Exception as e:
        logger.error(f"Error reading HumanEval file: {e}")
    
    return problems, success_count

def load_codeforces_problems(sample_size: int = SAMPLE_SIZE) -> Tuple[List[Dict], int]:
    """
    Load Codeforces problems from the downloaded dataset.
    Returns a list of successfully loaded problems and the count.
    """
    problems = []
    success_count = 0

    if not os.path.exists(CODEFORCES_PATH):
        logger.warning(f"Codeforces dataset not found at {CODEFORCES_PATH}. Skipping.")
        return problems, success_count

    try:
        with open(CODEFORCES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle both list and dict with 'problems' key
            items = data.get('problems', data) if isinstance(data, dict) else data
            
            count = 0
            for item in items:
                if count >= sample_size:
                    break
                try:
                    # Basic validation: ensure required fields exist
                    if 'name' in item and 'type' in item:
                        problems.append(item)
                        success_count += 1
                        count += 1
                    else:
                        logger.debug(f"Skipping item: missing required fields")
                except Exception as e:
                    logger.warning(f"Failed to process item: {e}")
                    continue
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in Codeforces file: {e}")
    except Exception as e:
        logger.error(f"Error reading Codeforces file: {e}")

    return problems, success_count

def load_all_problems(sample_size: int = SAMPLE_SIZE) -> Tuple[List[Dict], int, int]:
    """
    Load problems from both HumanEval and Codeforces.
    Returns (all_problems, total_successes, total_attempts).
    """
    he_problems, he_success = load_humaneval_problems(sample_size // 2)
    cf_problems, cf_success = load_codeforces_problems(sample_size - len(he_problems))
    
    all_problems = he_problems + cf_problems
    total_success = he_success + cf_success
    total_attempts = min(SAMPLE_SIZE, len(he_problems) + len(cf_problems)) # Approximation of attempts based on availability
    
    # If we didn't get enough from one source, try to get more from the other
    if len(all_problems) < sample_size:
        needed = sample_size - len(all_problems)
        if he_success < sample_size:
            # Retry loading more from HumanEval if available
            remaining_he, _ = load_humaneval_problems(sample_size)
            # In a real scenario, we'd track indices, but for this test we assume full reload
            # For the specific 100-sample test, we just sum what we got
            pass
    
    return all_problems, total_success, SAMPLE_SIZE

def verify_loading_rate(sample_size: int = SAMPLE_SIZE, target_rate: float = TARGET_LOAD_RATE) -> bool:
    """
    Run a load test to verify that the problem loading rate meets the requirement.
    FR-001: Verify ≥95% problem loading rate.
    
    This function:
    1. Attempts to load `sample_size` problems from the available datasets.
    2. Counts successful loads.
    3. Computes rate = successes / sample_size.
    4. Verifies rate >= target_rate.
    
    Returns True if the rate meets the threshold, False otherwise.
    """
    logger.info(f"Starting load test for {sample_size} samples (Target rate: {target_rate})")
    
    # We need to attempt to load exactly sample_size items.
    # Since load_all_problems aggregates, we simulate the "attempt" count
    # by defining the target as the input sample_size.
    
    problems, successes, total_attempts = load_all_problems(sample_size)
    
    # If datasets are missing, we might have 0 successes.
    # In a real CI environment, datasets should be downloaded by T009/T010.
    if total_attempts == 0:
        logger.error("No problems could be attempted (datasets missing or empty).")
        rate = 0.0
    else:
        # Ensure we don't divide by zero if logic changes, though sample_size > 0
        rate = successes / sample_size
    
    logger.info(f"Load Test Results:")
    logger.info(f"  Target Sample Size: {sample_size}")
    logger.info(f"  Successful Loads: {successes}")
    logger.info(f"  Calculated Rate: {rate:.4f}")
    logger.info(f"  Target Rate: {target_rate}")
    
    if rate >= target_rate:
        logger.info(f"SUCCESS: Load rate {rate:.4f} >= {target_rate}")
        return True
    else:
        logger.error(f"FAILURE: Load rate {rate:.4f} < {target_rate}")
        return False

def main():
    """
    Entry point for running the load verification test.
    """
    success = verify_loading_rate()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()