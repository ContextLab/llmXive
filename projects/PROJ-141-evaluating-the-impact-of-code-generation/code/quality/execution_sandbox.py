"""
Execution Sandbox for Test Suite Execution with Timeout and Crash Handling.

This module implements robust timeout and crash handling for test suite execution
as required by FR-015 and the User Story 2 specifications.

Features:
- 300-second timeout for test execution
- Subprocess timeout handling (subprocess.TimeoutExpired)
- General exception handling
- Error logging with submission ID and traceback
- Safe error response generation for clients
"""

import os
import sys
import json
import logging
import subprocess
import traceback
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Constants
DEFAULT_TIMEOUT_SECONDS = 300
MAX_OUTPUT_SIZE = 1024 * 1024  # 1MB limit for output capture


class ExecutionTimeoutError(Exception):
    """Raised when test execution exceeds the timeout limit."""
    pass


class ExecutionCrashError(Exception):
    """Raised when test execution crashes unexpectedly."""
    pass


def execute_with_timeout(
    cmd: List[str],
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None
) -> Tuple[bool, str, str, Optional[float]]:
    """
    Execute a command with timeout and crash handling.

    Args:
        cmd: Command and arguments to execute
        timeout: Maximum execution time in seconds (default: 300)
        cwd: Working directory for execution
        env: Environment variables for the subprocess

    Returns:
        Tuple of (success, stdout, stderr, duration_seconds)

    Raises:
        ExecutionTimeoutError: If execution exceeds timeout
        ExecutionCrashError: If execution crashes with unexpected error
    """
    start_time = datetime.now(timezone.utc)
    stdout = ""
    stderr = ""

    try:
        logger.info(f"Executing command with {timeout}s timeout: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            timeout=timeout,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False  # Don't raise on non-zero exit codes
        )

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        stdout = result.stdout[:MAX_OUTPUT_SIZE] if result.stdout else ""
        stderr = result.stderr[:MAX_OUTPUT_SIZE] if result.stderr else ""

        if result.returncode == 0:
            logger.info(f"Execution completed successfully in {duration:.2f}s")
            return True, stdout, stderr, duration
        else:
            logger.warning(f"Execution failed with return code {result.returncode} in {duration:.2f}s")
            return False, stdout, stderr, duration

    except subprocess.TimeoutExpired as e:
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        error_msg = f"Execution timed out after {timeout} seconds"
        logger.error(f"{error_msg}: {str(e)}")
        
        # Capture partial output if available
        if e.stdout:
            stdout = str(e.stdout)[:MAX_OUTPUT_SIZE]
        if e.stderr:
            stderr = str(e.stderr)[:MAX_OUTPUT_SIZE]
        
        raise ExecutionTimeoutError(error_msg) from e

    except Exception as e:
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        error_msg = f"Execution crashed: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        
        raise ExecutionCrashError(error_msg) from e


def run_test_suite(
    submission_id: str,
    test_command: List[str],
    test_dir: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS
) -> Dict[str, Any]:
    """
    Run a test suite for a code submission with full error handling.

    Args:
        submission_id: Unique identifier for the code submission
        test_command: Command to run the tests
        test_dir: Directory containing the tests
        timeout: Maximum execution time in seconds

    Returns:
        Dictionary with execution results or error information
    """
    result = {
        "submission_id": submission_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timeout_seconds": timeout,
        "success": False,
        "error_type": None,
        "error_message": None,
        "traceback": None,
        "duration_seconds": None,
        "stdout": "",
        "stderr": ""
    }

    try:
        success, stdout, stderr, duration = execute_with_timeout(
            cmd=test_command,
            timeout=timeout,
            cwd=test_dir
        )

        result["success"] = success
        result["duration_seconds"] = duration
        result["stdout"] = stdout
        result["stderr"] = stderr

        if not success:
            result["error_type"] = "ExecutionFailed"
            result["error_message"] = f"Test suite returned non-zero exit code. stderr: {stderr[:200]}"

        return result

    except ExecutionTimeoutError as e:
        result["error_type"] = "TimeoutError"
        result["error_message"] = str(e)
        result["traceback"] = traceback.format_exc()
        logger.error(f"[{submission_id}] {result['error_type']}: {result['error_message']}")
        return result

    except ExecutionCrashError as e:
        result["error_type"] = "CrashError"
        result["error_message"] = str(e)
        result["traceback"] = traceback.format_exc()
        logger.error(f"[{submission_id}] {result['error_type']}: {result['error_message']}")
        return result

    except Exception as e:
        result["error_type"] = "UnexpectedError"
        result["error_message"] = str(e)
        result["traceback"] = traceback.format_exc()
        logger.error(f"[{submission_id}] {result['error_type']}: {result['error_message']}")
        return result


def create_error_response(
    submission_id: str,
    error_type: str,
    error_message: str,
    traceback_str: Optional[str] = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """
    Create a standardized error response for client consumption.

    Args:
        submission_id: Unique identifier for the submission
        error_type: Type of error (TimeoutError, CrashError, etc.)
        error_message: Human-readable error message
        traceback_str: Optional full traceback string
        status_code: HTTP status code for the error

    Returns:
        Dictionary formatted as an error response
    """
    response = {
        "success": False,
        "submission_id": submission_id,
        "error": {
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

    if traceback_str:
        response["error"]["traceback"] = traceback_str

    # Log the error for debugging
    logger.error(
        f"[{submission_id}] {error_type}: {error_message}",
        extra={"status_code": status_code}
    )

    return response


def log_execution_error(
    submission_id: str,
    error_type: str,
    error_message: str,
    traceback_str: Optional[str] = None
) -> None:
    """
    Log execution errors to the experiment log.

    Args:
        submission_id: Unique identifier for the submission
        error_type: Type of error
        error_message: Error message
        traceback_str: Optional traceback string
    """
    log_entry = {
        "event_type": "execution_error",
        "submission_id": submission_id,
        "error_type": error_type,
        "error_message": error_message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "traceback": traceback_str
    }

    logger.error(
        f"[{submission_id}] {error_type}: {error_message}",
        extra={"log_entry": json.dumps(log_entry)}
    )


def main():
    """
    Main entry point for testing the execution sandbox.
    
    This function demonstrates the timeout and crash handling capabilities
    by running a sample test command.
    """
    if len(sys.argv) < 2:
        print("Usage: python execution_sandbox.py <test_command> [timeout_seconds]")
        print("Example: python execution_sandbox.py 'python -m pytest tests/' 300")
        sys.exit(1)

    # Parse arguments
    test_command_str = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TIMEOUT_SECONDS

    submission_id = str(uuid.uuid4())
    
    # Split command string into list
    import shlex
    test_command = shlex.split(test_command_str)

    logger.info(f"Running sandbox test for submission {submission_id}")
    logger.info(f"Command: {' '.join(test_command)}")
    logger.info(f"Timeout: {timeout}s")

    result = run_test_suite(
        submission_id=submission_id,
        test_command=test_command,
        test_dir=os.getcwd(),
        timeout=timeout
    )

    # Print results
    print("\n" + "="*60)
    print("EXECUTION SANDBOX RESULT")
    print("="*60)
    print(json.dumps(result, indent=2))
    print("="*60)

    if result["success"]:
        print("✓ Execution completed successfully")
    else:
        print(f"✗ Execution failed: {result['error_type']}")
        print(f"  Message: {result['error_message']}")

    return result


if __name__ == "__main__":
    main()
