from __future__ import annotations

import subprocess
import sys
import tempfile
import os
import signal
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from config import Paths, get_config_summary
from utils.logger import get_logger
from models.data_models import ExecutionOutcome, ExecutionStatus, HumanEvalProblem

logger = get_logger(__name__)

class ExecutionTimeoutError(Exception):
    """Raised when code execution exceeds the timeout limit."""
    pass

class ExecutionError(Exception):
    """Raised when code execution fails due to runtime errors."""
    pass

@dataclass
class ExecutionResult:
    """Internal result container before mapping to Pydantic model."""
    problem_id: str
    variant_id: str
    code: str
    pass_count: int = 0
    fail_count: int = 0
    error_details: str = ""
    timeout_flag: bool = False
    exception_type: Optional[str] = None
    execution_time: float = 0.0
    status: ExecutionStatus = ExecutionStatus.PENDING

def run_code_with_timeout(
    code: str,
    test_code: str,
    entry_point: str,
    timeout_seconds: int = 10
) -> ExecutionResult:
    """
    Executes generated code against a test suite with a configurable timeout.
    
    This function:
    1. Writes the generated code and test code to temporary files.
    2. Executes the test runner in a subprocess with a timeout.
    3. Captures stdout/stderr to detect syntax errors, runtime exceptions, and timeouts.
    4. Parses the output to determine pass/fail counts.
    
    Args:
        code: The generated code string to execute.
        test_code: The test harness code (from HumanEval).
        entry_point: The name of the function being tested.
        timeout_seconds: Maximum execution time per test case.
        
    Returns:
        ExecutionResult with pass/fail counts and error details.
    """
    result = ExecutionResult(
        problem_id="unknown", # Will be set by caller
        variant_id="unknown", # Will be set by caller
        code=code
    )
    
    start_time = time.time()
    
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            code_path = Path(tmpdir) / "solution.py"
            test_path = Path(tmpdir) / "test_solution.py"
            
            # Write code and tests to files
            code_path.write_text(code)
            test_path.write_text(test_code)
            
            # Construct the command to run the tests
            # We run the test file which imports the solution and runs checks
            cmd = [sys.executable, str(test_path)]
            
            # Execute with timeout
            try:
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    cwd=tmpdir
                )
                
                result.execution_time = time.time() - start_time
                
                # Analyze output
                stdout = process.stdout
                stderr = process.stderr
                return_code = process.returncode
                
                # Check for timeout (though subprocess timeout handles this)
                if return_code == -signal.SIGALRM or "timeout" in stdout.lower() or "timeout" in stderr.lower():
                    result.timeout_flag = True
                    result.status = ExecutionStatus.FAILED
                    result.error_details = "Execution timed out"
                    result.exception_type = "TimeoutError"
                    return result
                
                # Parse pass/fail from output (HumanEval format usually prints "Test X: PASS/FAIL")
                # Or if it's a standard unittest output
                lines = (stdout + stderr).splitlines()
                
                # Simple heuristic: look for "passed" or "failed" in output
                # HumanEval specific: often prints "Test 1: PASS", "Test 2: FAIL"
                # Or if using pytest/unittest: "X passed, Y failed"
                
                # Count occurrences
                pass_count = 0
                fail_count = 0
                error_found = False
                error_msg = ""
                
                for line in lines:
                    line_lower = line.lower()
                    if "test" in line_lower and "pass" in line_lower:
                        pass_count += 1
                    elif "test" in line_lower and "fail" in line_lower:
                        fail_count += 1
                    elif "passed" in line_lower and "failed" not in line_lower:
                        # "X passed"
                        pass_count += 1
                    elif "failed" in line_lower and "passed" not in line_lower:
                        # "X failed"
                        fail_count += 1
                    
                    # Check for syntax errors or tracebacks
                    if "syntaxerror" in line_lower or "traceback" in line_lower:
                        error_found = True
                        error_msg = line
                    if "runtimeerror" in line_lower:
                        error_found = True
                        error_msg = line
                    if "nameerror" in line_lower:
                        error_found = True
                        error_msg = line
                    if "importerror" in line_lower:
                        error_found = True
                        error_msg = line
                
                # If no explicit counts found but output is clean, assume success or failure based on return code
                if pass_count == 0 and fail_count == 0:
                    if return_code == 0:
                        # Assume all passed if no errors and exit 0, but this is risky
                        # Better to look for "OK" or similar
                        if "ok" in stdout.lower() or "ok" in stderr.lower():
                            pass_count = 1 # Default to 1 if we can't count
                        else:
                            # If we can't determine, assume failure if there's output
                            if stdout.strip() or stderr.strip():
                                fail_count = 1
                                result.error_details = f"Execution returned {return_code} with output: {stdout[:200]} {stderr[:200]}"
                            else:
                                pass_count = 1
                    else:
                        fail_count = 1
                        result.error_details = f"Execution returned non-zero exit code: {return_code}. Stderr: {stderr[:200]}"
                
                result.pass_count = pass_count
                result.fail_count = fail_count
                
                if error_found:
                    result.status = ExecutionStatus.FAILED
                    result.exception_type = "RuntimeError" if "runtimeerror" in error_msg.lower() else "SyntaxError" if "syntaxerror" in error_msg.lower() else "OtherError"
                    result.error_details = error_msg
                elif fail_count > 0:
                    result.status = ExecutionStatus.FAILED
                    result.exception_type = "TestFailure"
                    result.error_details = f"{fail_count} test(s) failed"
                elif pass_count > 0:
                    result.status = ExecutionStatus.PASSED
                    result.error_details = ""
                else:
                    result.status = ExecutionStatus.FAILED
                    result.error_details = "Unable to determine execution outcome"
                    
            except subprocess.TimeoutExpired:
                result.execution_time = time.time() - start_time
                result.timeout_flag = True
                result.status = ExecutionStatus.FAILED
                result.error_details = f"Execution timed out after {timeout_seconds} seconds"
                result.exception_type = "TimeoutError"
                
    except Exception as e:
        result.execution_time = time.time() - start_time
        result.status = ExecutionStatus.FAILED
        result.error_details = str(e)
        result.exception_type = type(e).__name__
        logger.error(f"Unexpected error during execution: {e}", exc_info=True)
        
    return result

def execute_sample(
    problem: HumanEvalProblem,
    variant_id: str,
    generated_code: str,
    timeout_seconds: int = 10
) -> ExecutionOutcome:
    """
    Executes a single generated code sample against the problem's tests.
    
    Args:
        problem: The HumanEvalProblem containing tests and entry point.
        variant_id: The ID of the prompt variant used.
        generated_code: The code generated by the LLM.
        timeout_seconds: Timeout per execution.
        
    Returns:
        ExecutionOutcome Pydantic model.
    """
    result = run_code_with_timeout(
        code=generated_code,
        test_code=problem.test_list[0] if problem.test_list else "", # HumanEval tests are usually a list of strings, but often concatenated. Assuming list of strings or single string.
        entry_point=problem.problem_id, # Using problem_id as entry point name placeholder
        timeout_seconds=timeout_seconds
    )
    
    # Map internal result to Pydantic model
    outcome = ExecutionOutcome(
        outcome_id=f"out_{variant_id}_{int(time.time())}",
        code_id=f"code_{variant_id}",
        pass_count=result.pass_count,
        fail_count=result.fail_count,
        error_details=result.error_details,
        timeout_flag=result.timeout_flag
    )
    
    logger.info(
        f"Executed {variant_id}: "
        f"Pass={result.pass_count}, Fail={result.fail_count}, "
        f"Timeout={result.timeout_flag}, Time={result.execution_time:.2f}s"
    )
    
    return outcome

def run_batch_execution(
    variants: List[Dict[str, Any]],
    problems: Dict[str, HumanEvalProblem],
    timeout_seconds: int = 10
) -> List[ExecutionOutcome]:
    """
    Runs execution for a batch of generated code variants.
    
    Args:
        variants: List of dicts containing variant_id, problem_id, code.
        problems: Dict mapping problem_id to HumanEvalProblem.
        timeout_seconds: Timeout per test case.
        
    Returns:
        List of ExecutionOutcome objects.
    """
    outcomes = []
    
    for variant in variants:
        variant_id = variant.get("variant_id")
        problem_id = variant.get("problem_id")
        code = variant.get("code")
        
        if not all([variant_id, problem_id, code]):
            logger.warning(f"Skipping invalid variant: {variant}")
            continue
        
        if problem_id not in problems:
            logger.error(f"Problem {problem_id} not found in dataset.")
            continue
        
        problem = problems[problem_id]
        
        try:
            outcome = execute_sample(
                problem=problem,
                variant_id=variant_id,
                generated_code=code,
                timeout_seconds=timeout_seconds
            )
            outcomes.append(outcome)
        except Exception as e:
            logger.error(f"Failed to execute variant {variant_id}: {e}", exc_info=True)
            # Create a failed outcome
            outcomes.append(ExecutionOutcome(
                outcome_id=f"out_{variant_id}_error",
                code_id=f"code_{variant_id}",
                pass_count=0,
                fail_count=1,
                error_details=str(e),
                timeout_flag=False
            ))
            
    return outcomes

def main():
    """
    Main entry point for testing the runner.
    This is a stub for CLI invocation; real execution is done via orchestrator or pipeline.
    """
    logger.info("Execution Runner Module Loaded.")
    logger.info("Use run_batch_execution() to process variants.")

if __name__ == "__main__":
    main()