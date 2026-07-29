from __future__ import annotations
import subprocess
import sys
import tempfile
import os
import signal
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time

from models.data_models import ExecutionStatus, GeneratedCode
from utils.logger import get_logger

# Custom exception for timeout scenarios
class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds the configured timeout."""
    pass

# Constants
DEFAULT_TIMEOUT_SECONDS = 10
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def run_code_with_timeout(code: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Executes Python code in a subprocess with a timeout.
    
    Args:
        code: The Python code string to execute.
        timeout: Maximum execution time in seconds.
        
    Returns:
        Tuple of (success, stdout, stderr, error_type)
        - success: True if execution completed without timeout or fatal error.
        - stdout: Standard output from the process.
        - stderr: Standard error from the process.
        - error_type: Type of error if failed (e.g., 'SyntaxError', 'RuntimeError', 'Timeout'), None if success.
    """
    logger = get_logger("execution.runner")
    logger.debug(f"Executing code with timeout {timeout}s")

    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        # Run the code in a subprocess
        start_time = time.time()
        process = subprocess.Popen(
            [sys.executable, temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=os.setsid if os.name != 'nt' else None  # Ensure we can kill the process group
        )

        try:
            stdout, stderr = process.communicate(timeout=timeout)
            elapsed = time.time() - start_time
            
            if process.returncode == 0:
                logger.debug(f"Execution succeeded in {elapsed:.2f}s")
                return True, stdout.strip(), stderr.strip(), None
            else:
                # Determine error type from stderr or traceback
                error_type = _classify_error(stderr)
                logger.warning(f"Execution failed with return code {process.returncode}. Type: {error_type}")
                return False, stdout.strip(), stderr.strip(), error_type

        except subprocess.TimeoutExpired:
            # Kill the process group to ensure cleanup
            if os.name != 'nt':
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            
            logger.error(f"Execution timed out after {timeout}s")
            return False, "", f"Execution timed out after {timeout} seconds", "TimeoutError"

    except Exception as e:
        logger.error(f"Unexpected error during execution: {str(e)}")
        return False, "", str(e), "UnexpectedError"
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except OSError:
            pass

def _classify_error(stderr: str) -> str:
    """
    Classifies the error type based on the stderr content.
    """
    if not stderr:
        return "RuntimeError"
    
    # Check for specific syntax errors
    if "SyntaxError" in stderr or "IndentationError" in stderr:
        return "SyntaxError"
    
    # Check for name errors (often indicates missing imports or typos)
    if "NameError" in stderr:
        return "NameError"
    
    # Check for type errors
    if "TypeError" in stderr:
        return "TypeError"
    
    # Check for attribute errors
    if "AttributeError" in stderr:
        return "AttributeError"
    
    # Check for value errors
    if "ValueError" in stderr:
        return "ValueError"
    
    # Check for import errors
    if "ImportError" in stderr or "ModuleNotFoundError" in stderr:
        return "ImportError"
    
    # Check for runtime exceptions (e.g., ZeroDivisionError)
    if "ZeroDivisionError" in stderr:
        return "ZeroDivisionError"
    
    # Default to RuntimeError for other exceptions
    return "RuntimeError"

def execute_sample(sample: Dict[str, Any], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Executes a single generated code sample and captures the result.
    
    Args:
        sample: Dictionary containing 'id', 'code', 'complexity_label', etc.
        timeout: Execution timeout in seconds.
        
    Returns:
        Dictionary with execution results including status, error type, and logs.
    """
    logger = get_logger("execution.runner")
    
    sample_id = sample.get('id', 'unknown')
    code = sample.get('code', '')
    complexity_label = sample.get('complexity_label', 'unknown')
    
    logger.info(f"Executing sample {sample_id} (complexity: {complexity_label})")
    
    try:
        success, stdout, stderr, error_type = run_code_with_timeout(code, timeout)
        
        if success:
            status = ExecutionStatus.PASS.value
            logger.info(f"Sample {sample_id} executed successfully.")
        else:
            # Mark as failed based on error type
            status = ExecutionStatus.FAIL.value
            logger.warning(f"Sample {sample_id} failed: {error_type}")
            
        return {
            'id': sample_id,
            'complexity_label': complexity_label,
            'status': status,
            'error_type': error_type,
            'stdout': stdout,
            'stderr': stderr,
            'execution_time': None, # Could be tracked if needed
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        # Catch-all for any unexpected errors during execution logic
        logger.exception(f"Critical error executing sample {sample_id}: {str(e)}")
        return {
            'id': sample_id,
            'complexity_label': complexity_label,
            'status': ExecutionStatus.FAIL.value,
            'error_type': 'CriticalExecutionError',
            'stdout': '',
            'stderr': str(e),
            'execution_time': None,
            'timestamp': datetime.now().isoformat()
        }

def run_batch_execution(samples: List[Dict[str, Any]], timeout: int = DEFAULT_TIMEOUT_SECONDS) -> List[Dict[str, Any]]:
    """
    Executes a batch of generated code samples.
    
    Args:
        samples: List of dictionaries containing code samples.
        timeout: Execution timeout in seconds per sample.
        
    Returns:
        List of execution result dictionaries.
    """
    logger = get_logger("execution.runner")
    logger.info(f"Starting batch execution of {len(samples)} samples")
    
    results = []
    for i, sample in enumerate(samples):
        logger.debug(f"Processing sample {i+1}/{len(samples)}")
        result = execute_sample(sample, timeout)
        results.append(result)
        
    logger.info(f"Batch execution completed. {len(results)} results generated.")
    return results

def main():
    """
    Main entry point for testing the runner module.
    This function demonstrates exception handling by running a sample with a syntax error
    and a sample that times out.
    """
    logger = setup_structured_logger("runner_test")
    logger.info("Starting runner.py test suite")
    
    # Test Case 1: Syntax Error
    syntax_error_sample = {
        'id': 'test_syntax_error',
        'code': 'def broken(\n    print("missing parenthesis"', # Intentional syntax error
        'complexity_label': 'simple'
    }
    
    result1 = execute_sample(syntax_error_sample, timeout=5)
    logger.info(f"Syntax Error Test Result: {result1['status']}, Error Type: {result1['error_type']}")
    assert result1['status'] == ExecutionStatus.FAIL.value, "Syntax error should result in FAIL status"
    assert result1['error_type'] == 'SyntaxError', "Error type should be classified as SyntaxError"
    
    # Test Case 2: Timeout
    timeout_sample = {
        'id': 'test_timeout',
        'code': 'import time\nwhile True:\n    time.sleep(1)', # Infinite loop
        'complexity_label': 'moderate'
    }
    
    result2 = execute_sample(timeout_sample, timeout=2) # Set short timeout
    logger.info(f"Timeout Test Result: {result2['status']}, Error Type: {result2['error_type']}")
    assert result2['status'] == ExecutionStatus.FAIL.value, "Timeout should result in FAIL status"
    assert result2['error_type'] == 'TimeoutError', "Error type should be classified as TimeoutError"
    
    # Test Case 3: Successful Execution
    success_sample = {
        'id': 'test_success',
        'code': 'print("Hello, World!")',
        'complexity_label': 'simple'
    }
    
    result3 = execute_sample(success_sample, timeout=5)
    logger.info(f"Success Test Result: {result3['status']}")
    assert result3['status'] == ExecutionStatus.PASS.value, "Successful code should result in PASS status"
    
    logger.info("All tests passed.")

if __name__ == "__main__":
    main()