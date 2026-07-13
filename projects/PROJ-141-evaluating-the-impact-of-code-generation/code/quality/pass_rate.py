"""
HumanEval test suite execution and pass rate calculation.

Executes submitted code against the HumanEval test suite and calculates
the pass rate with >= 0.01 precision.

This module implements FR-001 (>=95% load rate) verification for the
quality assessment pipeline by ensuring test execution completes reliably.
"""
import os
import sys
import json
import logging
import subprocess
import tempfile
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_config
from logs.experiment import setup_experiment_logger

logger = setup_experiment_logger("quality")

# HumanEval test execution timeout (seconds)
EXECUTION_TIMEOUT = 300

def load_humaneval_tests() -> List[Dict[str, Any]]:
    """
    Load HumanEval test cases from the downloaded dataset.
    
    Returns:
        List of test case dictionaries with 'prompt', 'canonical_solution', 
        'test' (test code), and 'entry_point' keys.
        
    Raises:
        FileNotFoundError: If HumanEval dataset is not found.
        ValueError: If dataset structure is invalid.
    """
    config = get_config()
    humaneval_path = config.get('datasets', {}).get('humaneval_path', 'data/humaneval/humaneval.jsonl')
    
    if not os.path.exists(humaneval_path):
        raise FileNotFoundError(f"HumanEval dataset not found at {humaneval_path}")
    
    test_cases = []
    with open(humaneval_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                case = json.loads(line)
                # Validate required fields
                if 'prompt' not in case or 'canonical_solution' not in case or 'test' not in case:
                    logger.warning(f"Skipping invalid test case at line {line_num}: missing required fields")
                    continue
                test_cases.append(case)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON at line {line_num}: {e}")
                continue
    
    if not test_cases:
        raise ValueError("No valid test cases found in HumanEval dataset")
    
    logger.info(f"Loaded {len(test_cases)} HumanEval test cases")
    return test_cases


def execute_test_in_isolation(
    code: str,
    test_code: str,
    entry_point: str,
    timeout: int = EXECUTION_TIMEOUT
) -> Tuple[bool, Optional[str], float]:
    """
    Execute a single test case in an isolated environment.
    
    Args:
        code: The submitted code to test.
        test_code: The test code to execute.
        entry_point: The function name to test.
        timeout: Maximum execution time in seconds.
        
    Returns:
        Tuple of (passed, error_message, execution_time)
        - passed: True if all tests passed, False otherwise
        - error_message: Error details if execution failed, None otherwise
        - execution_time: Time taken to execute the test in seconds
    """
    # Create temporary file for execution
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
        tmp_path = tmp_file.name
        # Write code + test
        full_code = f"{code}\n{test_code}"
        tmp_file.write(full_code)
    
    try:
        start_time = time.time()
        
        # Execute with timeout
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(PROJECT_ROOT)
        )
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            # Check if tests actually ran (HumanEval test pattern)
            if "passed" in result.stdout.lower() or "ok" in result.stdout.lower():
                return True, None, execution_time
            else:
                # Tests ran but may have failed silently
                return False, f"No test output detected. Stdout: {result.stdout[:200]}", execution_time
        else:
            error_msg = result.stderr or result.stdout or "Unknown error"
            return False, error_msg, execution_time
            
    except subprocess.TimeoutExpired:
        execution_time = time.time() - start_time
        return False, f"Execution timed out after {timeout}s", execution_time
    except Exception as e:
        execution_time = time.time() - start_time
        return False, str(e), execution_time
    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def calculate_pass_rate(
    code: str,
    test_cases: Optional[List[Dict[str, Any]]] = None,
    problem_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate the pass rate for a code submission against HumanEval tests.
    
    Args:
        code: The submitted code to evaluate.
        test_cases: Optional list of test cases. If None, loads from dataset.
        problem_id: Optional problem ID for logging.
        
    Returns:
        Dictionary with pass rate metrics:
        - pass_rate: Float between 0.0 and 1.0 (precision >= 0.01)
        - total_tests: Total number of test cases
        - passed_tests: Number of passed test cases
        - failed_tests: Number of failed test cases
        - execution_times: List of execution times for each test
        - errors: List of error messages for failed tests
        - problem_id: The problem ID if provided
    """
    # Load test cases if not provided
    if test_cases is None:
        try:
            test_cases = load_humaneval_tests()
        except (FileNotFoundError, ValueError) as e:
            logger.error(f"Failed to load test cases: {e}")
            return {
                'pass_rate': 0.0,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'execution_times': [],
                'errors': [f"Failed to load test cases: {str(e)}"],
                'problem_id': problem_id
            }
    
    if not test_cases:
        return {
            'pass_rate': 0.0,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'execution_times': [],
            'errors': ["No test cases available"],
            'problem_id': problem_id
        }
    
    passed_count = 0
    failed_count = 0
    execution_times = []
    errors = []
    
    for i, test_case in enumerate(test_cases):
        prompt = test_case.get('prompt', '')
        test_code = test_case.get('test', '')
        entry_point = test_case.get('entry_point', '')
        
        # Combine prompt and submission code
        full_code = f"{prompt}\n{code}"
        
        passed, error_msg, exec_time = execute_test_in_isolation(
            full_code,
            test_code,
            entry_point
        )
        
        execution_times.append(exec_time)
        
        if passed:
            passed_count += 1
        else:
            failed_count += 1
            if error_msg:
                errors.append(f"Test {i+1}: {error_msg[:200]}")
    
    total_tests = len(test_cases)
    pass_rate = passed_count / total_tests if total_tests > 0 else 0.0
    
    # Ensure precision >= 0.01 (round to 2 decimal places)
    pass_rate = round(pass_rate, 2)
    
    logger.info(f"Pass rate calculation for problem {problem_id}: {pass_rate} ({passed_count}/{total_tests})")
    
    return {
        'pass_rate': pass_rate,
        'total_tests': total_tests,
        'passed_tests': passed_count,
        'failed_tests': failed_count,
        'execution_times': execution_times,
        'errors': errors,
        'problem_id': problem_id
    }


def verify_fr001_load_rate() -> bool:
    """
    Verify that the test suite loading rate is >= 95%.
    
    This function runs a verification test to ensure the HumanEval
    test suite can be loaded reliably, satisfying FR-001 requirements.
    
    Returns:
        True if load rate >= 95%, False otherwise.
    """
    try:
        test_cases = load_humaneval_tests()
        total_expected = 164  # Standard HumanEval has 164 test cases
        actual_loaded = len(test_cases)
        load_rate = actual_loaded / total_expected if total_expected > 0 else 0.0
        
        logger.info(f"FR-001 Verification: Loaded {actual_loaded}/{total_expected} test cases ({load_rate:.2%})")
        
        return load_rate >= 0.95
        
    except Exception as e:
        logger.error(f"FR-001 Verification failed: {e}")
        return False


def main():
    """
    Main entry point for pass rate calculation demonstration.
    
    This function demonstrates the pass rate calculation by:
    1. Loading a sample code submission
    2. Calculating its pass rate against HumanEval tests
    3. Logging the results
    """
    logger.info("Starting pass rate calculation demonstration")
    
    # Verify FR-001 load rate first
    if not verify_fr001_load_rate():
        logger.error("FR-001 verification failed: test loading rate < 95%")
        return 1
    
    # Sample code submission (a simple function that should pass some tests)
    sample_code = """
def add(x, y):
    return x + y
"""
    
    # Calculate pass rate
    result = calculate_pass_rate(
        code=sample_code,
        problem_id="sample_add_function"
    )
    
    # Log results
    logger.info(f"Pass rate result: {json.dumps(result, indent=2)}")
    
    # Write results to output file
    output_path = PROJECT_ROOT / "data" / "quality" / "pass_rate_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Results written to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())