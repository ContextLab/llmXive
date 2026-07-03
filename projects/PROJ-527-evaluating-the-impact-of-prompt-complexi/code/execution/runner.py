from __future__ import annotations
import subprocess
import sys
import tempfile
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import signal
import time

from models.data_models import ExecutionStatus, GeneratedCode
from utils.logger import get_logger

# Default timeout in seconds (configurable via env or argument)
DEFAULT_TIMEOUT_SECONDS = 10

logger = get_logger(__name__)


class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds the allowed time limit."""
    pass


def run_code_with_timeout(
    code_content: str,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
) -> tuple[ExecutionStatus, Optional[str], Optional[str]]:
    """
    Executes the provided Python code string in a subprocess with a strict timeout.
    
    Args:
        code_content: The Python code to execute.
        timeout_seconds: Maximum time allowed for execution.
        
    Returns:
        A tuple of (status, stdout, stderr).
        Status is ExecutionStatus.PASS if execution completes without error and output is clean,
        ExecutionStatus.TIMEOUT if the process exceeds the time limit,
        ExecutionStatus.FAIL if the process returns a non-zero exit code or raises an exception.
    """
    # Create a temporary file to hold the code
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.py', delete=False, encoding='utf-8'
    ) as tmp_file:
        tmp_file.write(code_content)
        tmp_path = tmp_file.name

    try:
        # Start the subprocess
        start_time = time.time()
        process = subprocess.Popen(
            [sys.executable, tmp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.getcwd()
        )

        try:
            # Wait for the process with timeout
            stdout, stderr = process.communicate(timeout=timeout_seconds)
            end_time = time.time()
            duration = end_time - start_time

            if process.returncode == 0:
                logger.debug(f"Execution succeeded in {duration:.2f}s")
                return ExecutionStatus.PASS, stdout, stderr
            else:
                logger.debug(f"Execution failed with code {process.returncode} in {duration:.2f}s")
                return ExecutionStatus.FAIL, stdout, stderr

        except subprocess.TimeoutExpired:
            # Kill the process tree to ensure it stops
            process.kill()
            # Consume any remaining output to prevent zombie processes
            try:
                process.communicate(timeout=1)
            except subprocess.TimeoutExpired:
                process.wait()
            
            logger.warning(f"Execution timed out after {timeout_seconds}s")
            return ExecutionStatus.TIMEOUT, "", f"Execution timed out after {timeout_seconds} seconds"

    except Exception as e:
        logger.error(f"Unexpected error during execution: {e}")
        return ExecutionStatus.FAIL, "", str(e)
    finally:
        # Clean up the temporary file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass  # Ignore cleanup errors


def execute_sample(
    sample: GeneratedCode,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
) -> GeneratedCode:
    """
    Executes a single generated code sample and updates its status.
    
    Args:
        sample: The GeneratedCode object containing the code to run.
        timeout_seconds: Maximum execution time.
        
    Returns:
        The updated GeneratedCode object with status and output populated.
    """
    status, stdout, stderr = run_code_with_timeout(
        sample.code_content, 
        timeout_seconds
    )
    
    sample.execution_status = status
    sample.stdout = stdout.strip() if stdout else ""
    sample.stderr = stderr.strip() if stderr else ""
    
    if status == ExecutionStatus.TIMEOUT:
        logger.info(f"Marking sample {sample.id} as TIMEOUT")
    elif status == ExecutionStatus.FAIL:
        logger.info(f"Marking sample {sample.id} as FAIL: {sample.stderr[:100]}...")
    else:
        logger.info(f"Marking sample {sample.id} as PASS")
        
    return sample


def run_batch_execution(
    samples: List[GeneratedCode],
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
) -> List[GeneratedCode]:
    """
    Executes a batch of code samples sequentially.
    
    Args:
        samples: List of GeneratedCode objects.
        timeout_seconds: Timeout for each sample.
        
    Returns:
        List of updated GeneratedCode objects.
    """
    results = []
    for i, sample in enumerate(samples):
        logger.info(f"Running sample {i+1}/{len(samples)}: {sample.id}")
        updated_sample = execute_sample(sample, timeout_seconds)
        results.append(updated_sample)
    return results


def main():
    """
    Main entry point for testing the runner with a sample code snippet.
    Reads a sample from data/processed if available, or runs a simple demo.
    """
    from config import Paths
    from data.storage import load_variants_from_parquet
    
    # Try to load real data first
    data_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"
    if data_path.exists():
        logger.info(f"Loading variants from {data_path}")
        try:
            variants_df = load_variants_from_parquet()
            # Convert to GeneratedCode objects (simplified for demo)
            # In real pipeline, this would be handled by the orchestrator
            logger.info(f"Loaded {len(variants_df)} variants for execution test")
            # For a real run, we would iterate and call run_batch_execution
            # Here we just verify the import and basic structure
            print(f"Ready to execute {len(variants_df)} samples.")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            print("Demo mode: Running a simple timeout test.")
            demo_code = "import time; time.sleep(2)"
            status, out, err = run_code_with_timeout(demo_code, timeout_seconds=5)
            print(f"Demo Result: {status}, Output: {out}, Error: {err}")
    else:
        print("No processed data found. Running demo timeout test.")
        # Demo: Code that finishes quickly
        demo_code = "print('Hello, World!')"
        status, out, err = run_code_with_timeout(demo_code, timeout_seconds=5)
        print(f"Demo (Quick) Result: {status}")
        
        # Demo: Code that times out
        demo_timeout = "import time; time.sleep(10)"
        status, out, err = run_code_with_timeout(demo_timeout, timeout_seconds=2)
        print(f"Demo (Timeout) Result: {status}")


if __name__ == "__main__":
    main()