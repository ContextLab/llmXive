from __future__ import annotations

import subprocess
import sys
import tempfile
import os
import signal
import logging
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from models.data_models import ExecutionStatus
from utils.logger import get_logger

# Import logger setup to ensure structured logging
logger = get_logger(__name__)

class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds the timeout threshold."""
    pass

class ExecutionError(Exception):
    """Raised when code execution fails due to syntax or runtime errors."""
    def __init__(self, message: str, error_type: str = "RuntimeError"):
        super().__init__(message)
        self.error_type = error_type

def run_code_with_timeout(code: str, timeout: float = 5.0) -> Tuple[bool, Optional[str], Optional[str], str]:
    """
    Execute code in an isolated subprocess with a timeout.
    
    Returns:
        Tuple of (success, stdout, stderr, error_type)
        - success: bool indicating if execution completed without timeout
        - stdout: captured stdout or None
        - stderr: captured stderr or None
        - error_type: 'Timeout', 'SyntaxError', 'RuntimeError', or 'None'
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "test_script.py"
        script_path.write_text(code)
        
        try:
            # Run with timeout
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir
            )
            
            if result.returncode == 0:
                return True, result.stdout, result.stderr, "None"
            else:
                # Check for syntax errors vs runtime errors
                error_output = result.stderr
                if "SyntaxError" in error_output or "IndentationError" in error_output:
                    return False, result.stdout, error_output, "SyntaxError"
                else:
                    return False, result.stdout, error_output, "RuntimeError"
                    
        except subprocess.TimeoutExpired:
            return False, None, None, "Timeout"
        except Exception as e:
            return False, None, str(e), "SystemError"

def execute_sample(sample: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
    """
    Execute a single code sample and capture execution status and errors.
    
    Args:
        sample: Dictionary containing 'code' (the generated code) and metadata
        timeout: Maximum execution time in seconds
        
    Returns:
        Dictionary with execution results including status, error types, and logs
    """
    code = sample.get('code', '')
    sample_id = sample.get('sample_id', 'unknown')
    complexity_label = sample.get('complexity_label', 'unknown')
    problem_id = sample.get('problem_id', 'unknown')
    
    logger.info(f"Executing sample {sample_id} (Complexity: {complexity_label})")
    
    try:
        success, stdout, stderr, error_type = run_code_with_timeout(code, timeout)
        
        if success:
            status = ExecutionStatus.PASS
            error_message = None
            logger.info(f"Sample {sample_id} executed successfully")
        else:
            if error_type == "Timeout":
                status = ExecutionStatus.FAIL
                error_message = f"Execution timed out after {timeout} seconds"
                logger.warning(f"Sample {sample_id} timed out")
            elif error_type == "SyntaxError":
                status = ExecutionStatus.FAIL
                error_message = f"Syntax error: {stderr}"
                logger.error(f"Sample {sample_id} failed with syntax error: {stderr[:200]}")
            elif error_type == "RuntimeError":
                status = ExecutionStatus.FAIL
                error_message = f"Runtime error: {stderr}"
                logger.error(f"Sample {sample_id} failed with runtime error: {stderr[:200]}")
            else:
                status = ExecutionStatus.FAIL
                error_message = f"Unknown error: {stderr}"
                logger.error(f"Sample {sample_id} failed with unknown error: {stderr[:200]}")
        
        return {
            'sample_id': sample_id,
            'problem_id': problem_id,
            'complexity_label': complexity_label,
            'status': status.value,
            'error_type': error_type if not success else None,
            'error_message': error_message,
            'stdout': stdout,
            'stderr': stderr,
            'execution_time': timeout if error_type == "Timeout" else None
        }
        
    except Exception as e:
        # Catch-all for unexpected exceptions during execution
        logger.exception(f"Unexpected error executing sample {sample_id}: {e}")
        return {
            'sample_id': sample_id,
            'problem_id': problem_id,
            'complexity_label': complexity_label,
            'status': ExecutionStatus.FAIL.value,
            'error_type': 'SystemError',
            'error_message': str(e),
            'stdout': None,
            'stderr': traceback.format_exc(),
            'execution_time': None
        }

def run_batch_execution(samples: List[Dict[str, Any]], timeout: float = 5.0) -> List[Dict[str, Any]]:
    """
    Execute a batch of code samples with exception handling for each.
    
    Args:
        samples: List of dictionaries containing code and metadata
        timeout: Maximum execution time per sample
        
    Returns:
        List of execution result dictionaries
    """
    logger.info(f"Starting batch execution of {len(samples)} samples")
    results = []
    
    for i, sample in enumerate(samples):
        logger.debug(f"Processing sample {i+1}/{len(samples)}")
        result = execute_sample(sample, timeout)
        results.append(result)
        
        # Log progress
        if (i + 1) % 10 == 0:
            logger.info(f"Completed {i+1}/{len(samples)} samples")
    
    # Log summary
    success_count = sum(1 for r in results if r['status'] == ExecutionStatus.PASS.value)
    fail_count = len(results) - success_count
    logger.info(f"Batch execution complete: {success_count} passed, {fail_count} failed")
    
    return results

def main():
    """Main entry point for testing the execution runner."""
    # Example usage
    test_samples = [
        {
            'sample_id': 'test_001',
            'problem_id': 'human_eval_001',
            'complexity_label': 'simple',
            'code': 'def add(a, b): return a + b\nprint(add(2, 3))'
        },
        {
            'sample_id': 'test_002',
            'problem_id': 'human_eval_002',
            'complexity_label': 'moderate',
            'code': 'def multiply(a, b): return a * b\nprint(multiply(4, 5))'
        },
        {
            'sample_id': 'test_003',
            'problem_id': 'human_eval_003',
            'complexity_label': 'complex',
            'code': 'def divide(a, b):\n    if b == 0:\n        raise ValueError("Cannot divide by zero")\n    return a / b\nprint(divide(10, 2))'
        },
        {
            'sample_id': 'test_004',
            'problem_id': 'human_eval_004',
            'complexity_label': 'very_complex',
            'code': 'def invalid_syntax\n    print("This is invalid")'  # Intentional syntax error
        },
        {
            'sample_id': 'test_005',
            'problem_id': 'human_eval_005',
            'complexity_label': 'degenerate',
            'code': 'import time\ntime.sleep(10)\nprint("Done")'  # Intentional timeout
        }
    ]
    
    results = run_batch_execution(test_samples, timeout=2.0)
    
    # Print results
    for result in results:
        print(f"\nSample: {result['sample_id']}")
        print(f"Status: {result['status']}")
        if result['error_type']:
            print(f"Error Type: {result['error_type']}")
            print(f"Error Message: {result['error_message']}")
        print("-" * 50)

if __name__ == "__main__":
    main()