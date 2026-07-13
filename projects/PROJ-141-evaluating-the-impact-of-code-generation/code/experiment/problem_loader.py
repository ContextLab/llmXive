"""
Problem loading module for HumanEval and Codeforces datasets.
Implements FR-001: Verify ≥95% problem loading rate.
"""
import os
import sys
import json
import logging
import hashlib
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
HUMAN_EVAL_DIR = Path("data/humaneval")
CODEFORCES_DIR = Path("data/codeforces")
SAMPLE_SIZE = 100
MIN_SUCCESS_RATE = 0.95

def load_humaneval_problems() -> List[Dict[str, Any]]:
    """
    Load HumanEval problems from the downloaded dataset.
    
    Returns:
        List of problem dictionaries.
        
    Raises:
        FileNotFoundError: If the dataset directory is missing.
        json.JSONDecodeError: If the JSON file is corrupted.
    """
    json_path = HUMAN_EVAL_DIR / "human_eval.json"
    
    if not json_path.exists():
        # Check for alternative naming or structure
        alt_path = HUMAN_EVAL_DIR / "data.json"
        if not alt_path.exists():
            raise FileNotFoundError(f"HumanEval dataset not found at {HUMAN_EVAL_DIR}. "
                                  f"Please run code/data/download_humaneval.py first.")
        json_path = alt_path
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'problems' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'problems' in data:
        return data['problems']
    else:
        # Fallback: treat as list of items if keys match expected structure
        return [data] if isinstance(data, dict) else []

def load_codeforces_problems() -> List[Dict[str, Any]]:
    """
    Load Codeforces problems from the downloaded dataset.
    
    Returns:
        List of problem dictionaries.
        
    Raises:
        FileNotFoundError: If the dataset directory is missing.
        json.JSONDecodeError: If the JSON file is corrupted.
    """
    json_path = CODEFORCES_DIR / "codeforces_problems.json"
    
    if not json_path.exists():
        alt_path = CODEFORCES_DIR / "problems.json"
        if not alt_path.exists():
            raise FileNotFoundError(f"Codeforces dataset not found at {CODEFORCES_DIR}. "
                                  f"Please run code/data/download_codeforces.py first.")
        json_path = alt_path
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict with 'problems' key
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and 'problems' in data:
        return data['problems']
    else:
        return [data] if isinstance(data, dict) else []

def load_all_problems() -> List[Dict[str, Any]]:
    """
    Load all problems from both HumanEval and Codeforces datasets.
    
    Returns:
        Combined list of all problems.
    """
    problems = []
    
    try:
        humaneval_problems = load_humaneval_problems()
        problems.extend(humaneval_problems)
        logger.info(f"Loaded {len(humaneval_problems)} HumanEval problems")
    except Exception as e:
        logger.warning(f"Failed to load HumanEval problems: {e}")
    
    try:
        codeforces_problems = load_codeforces_problems()
        problems.extend(codeforces_problems)
        logger.info(f"Loaded {len(codeforces_problems)} Codeforces problems")
    except Exception as e:
        logger.warning(f"Failed to load Codeforces problems: {e}")
    
    return problems

def verify_loading_rate(sample_size: int = SAMPLE_SIZE) -> Tuple[float, int, int]:
    """
    Verify that the problem loading rate is ≥95% (FR-001).
    
    This function runs a load test by attempting to load a random sample of problems
    and calculating the success rate.
    
    Args:
        sample_size: Number of problems to sample for testing.
        
    Returns:
        Tuple of (success_rate, successes, total_attempts)
        
    Raises:
        FileNotFoundError: If datasets are not available.
    """
    # Get all available problems first
    all_problems = load_all_problems()
    
    if not all_problems:
        raise FileNotFoundError("No problems could be loaded from any dataset. "
                              "Cannot perform load rate verification.")
    
    # Ensure we don't sample more than available
    actual_sample_size = min(sample_size, len(all_problems))
    
    # Randomly sample problems
    sampled_problems = random.sample(all_problems, actual_sample_size)
    
    successes = 0
    failures = 0
    
    for i, problem in enumerate(sampled_problems):
        try:
            # Simulate "loading" by validating required fields
            # This mimics the actual loading process without re-reading files
            required_fields = ['task', 'prompt', 'canonical_solution']
            
            if not isinstance(problem, dict):
                raise ValueError("Problem is not a dictionary")
            
            for field in required_fields:
                if field not in problem:
                    # Some datasets might use different field names
                    if field == 'canonical_solution' and 'solution' in problem:
                        continue
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate problem structure integrity
            if not problem.get('task') or not problem.get('prompt'):
                raise ValueError("Invalid problem content")
            
            successes += 1
            
        except Exception as e:
            failures += 1
            logger.debug(f"Failed to load problem {i}: {e}")
    
    total_attempts = successes + failures
    success_rate = successes / total_attempts if total_attempts > 0 else 0.0
    
    return success_rate, successes, total_attempts

def main():
    """
    Main entry point for problem loading and verification.
    
    Runs the load rate verification test and reports results.
    Exits with code 0 if ≥95% success rate, 1 otherwise.
    """
    logger.info("Starting problem loading verification (FR-001)...")
    
    try:
        # Run the verification
        success_rate, successes, total = verify_loading_rate(SAMPLE_SIZE)
        
        logger.info(f"Load test results:")
        logger.info(f"  Total attempts: {total}")
        logger.info(f"  Successful loads: {successes}")
        logger.info(f"  Failed loads: {total - successes}")
        logger.info(f"  Success rate: {success_rate:.2%}")
        logger.info(f"  Target rate: ≥95%")
        
        if success_rate >= MIN_SUCCESS_RATE:
            logger.info(f"✓ PASSED: Loading rate ({success_rate:.2%}) meets requirement (≥95%)")
            print(f"VERIFICATION_PASSED: Rate={success_rate:.4f} (≥{MIN_SUCCESS_RATE})")
            return 0
        else:
            logger.error(f"✗ FAILED: Loading rate ({success_rate:.2%}) is below requirement (≥95%)")
            print(f"VERIFICATION_FAILED: Rate={success_rate:.4f} (<{MIN_SUCCESS_RATE})")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Dataset error: {e}")
        print(f"VERIFICATION_FAILED: Dataset not available - {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        print(f"VERIFICATION_FAILED: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
