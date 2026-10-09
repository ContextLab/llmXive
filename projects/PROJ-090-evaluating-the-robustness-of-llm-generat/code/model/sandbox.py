"""
Sandbox execution environment with timeout and security constraints.
"""
import os
import sys
import subprocess
import resource
import signal
import tempfile
import time
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

class ExecutionStatus(Enum):
    PASS = "pass"
    FAIL = "fail"
    TIMEOUT = "timeout"
    ERROR = "error"
    OOM = "oom"


class SandboxError(Exception):
    """Base exception for sandbox errors."""
    pass


class TimeoutError(SandboxError):
    """Raised when execution exceeds the time limit."""
    pass


class SecurityViolationError(SandboxError):
    """Raised when a security violation is detected."""
    pass


class ExecutionError(SandboxError):
    """Raised when code execution fails."""
    pass


class ExecutionResult:
    """Container for execution results."""
    def __init__(self, status: ExecutionStatus, output: str = "", error: str = "", execution_time: float = 0.0):
        self.status = status
        self.output = output
        self.error = error
        self.execution_time = execution_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time
        }

    def __repr__(self) -> str:
        return f"ExecutionResult(status={self.status}, output={self.output!r}, error={self.error!r}, execution_time={self.execution_time})"


@dataclass
class Result:
    """Simple result object returned by the public API."""
    status: str
    output: str = ""
    error: str = ""
    execution_time: float = 0.0

    def __repr__(self) -> str:
        return (f"Result(status={self.status!r}, output={self.output!r}, "
                f"error={self.error!r}, execution_time={self.execution_time})")


def _check_security_violations(code: str) -> None:
    """Check for obvious security violations in the code."""
    dangerous_imports = ['os.system', 'subprocess', 'eval', 'exec', 'open', 'socket', 'http']
    for dangerous in dangerous_imports:
        if dangerous in code:
            raise SecurityViolationError(f"Security violation: usage of '{dangerous}' is not allowed")


def execute_code(code: str, timeout: int = 5, memory_limit_mb: int = 512) -> Dict[str, Any]:
    """
    Execute Python code in a sandboxed environment with timeout and memory limits.

    Args:
        code: The Python code to execute.
        timeout: Maximum execution time in seconds.
        memory_limit_mb: Maximum memory usage in megabytes.

    Returns:
        A dictionary containing execution status, output, and error information.

    Raises:
        ValueError: If timeout or memory_limit_mb is invalid.
        SecurityViolationError: If the code contains forbidden operations.
        TimeoutError: If execution exceeds the timeout.
    """
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError(f"Timeout must be a positive number, got {timeout}")
    if not isinstance(memory_limit_mb, int) or memory_limit_mb <= 0:
        raise ValueError(f"Memory limit must be a positive integer, got {memory_limit_mb}")

    # Security check
    _check_security_violations(code)

    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name

    try:
        start_time = time.time()

        # Set up resource limits (Unix only)
        if sys.platform != 'win32':
            memory_limit_bytes = memory_limit_mb * 1024 * 1024
            try:
                soft, hard = resource.getrlimit(resource.RLIMIT_AS)
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, hard))
            except (ValueError, resource.error):
                pass

            try:
                soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
                resource.setrlimit(resource.RLIMIT_CPU, (int(timeout), hard))
            except (ValueError, resource.error):
                pass

        proc = subprocess.Popen(
            [sys.executable, temp_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=None if sys.platform == 'win32' else os.setsid
        )

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            execution_time = time.time() - start_time

            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')

            if proc.returncode == 0:
                return {
                    "status": ExecutionStatus.PASS.value,
                    "output": stdout_str,
                    "error": stderr_str,
                    "execution_time": execution_time
                }
            else:
                return {
                    "status": ExecutionStatus.FAIL.value,
                    "output": stdout_str,
                    "error": stderr_str,
                    "execution_time": execution_time
                }

        except subprocess.TimeoutExpired:
            if sys.platform != 'win32':
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                proc.kill()
            proc.wait()
            raise TimeoutError(f"Execution timed out after {timeout} seconds")

    except TimeoutError:
        raise
    except Exception as e:
        raise ExecutionError(f"Execution failed: {str(e)}")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def execute_test_case(test_code: str, timeout: int = 5) -> Dict[str, Any]:
    """
    Execute a specific test case within the sandbox.

    Args:
        test_code: The test code to execute.
        timeout: Maximum execution time in seconds.

    Returns:
        A dictionary containing execution results.
    """
    return execute_code(test_code, timeout=timeout)


def add(a: int, b: int) -> int:
    """Helper function for testing."""
    return a + b


def broken() -> None:
    """Placeholder for broken function."""
    pass


# ----------------------------------------------------------------------
# Public API required by task T005
# ----------------------------------------------------------------------
def _dict_to_result(d: Dict[str, Any]) -> Result:
    """
    Convert the dictionary returned by ``execute_code`` into a ``Result``.
    """
    return Result(
        status=d.get("status", ExecutionStatus.ERROR.value),
        output=d.get("output", ""),
        error=d.get("error", ""),
        execution_time=d.get("execution_time", 0.0)
    )


def run_in_sandbox(code: str) -> Result:
    """
    Execute ``code`` in the sandbox with the default timeout (5 seconds).

    Returns:
        Result: An object with ``status`` equal to ``'pass'`` when the
        code runs without errors, otherwise ``'fail'``, ``'timeout'``,
        or ``'error'`` depending on the failure mode.
    """
    try:
        exec_dict = execute_code(code, timeout=5)
        return _dict_to_result(exec_dict)
    except SandboxError as e:
        # Map sandbox‑specific exceptions to a generic error result
        return Result(status=ExecutionStatus.ERROR.value, error=str(e))
    except Exception as e:
        # Any unexpected exception is also reported as an error
        return Result(status=ExecutionStatus.ERROR.value, error=str(e))


def execute_with_timeout(code: str, timeout: int) -> Result:
    """
    Execute ``code`` in the sandbox enforcing a custom ``timeout`` (seconds).

    Args:
        code: Python source code to run.
        timeout: Maximum allowed execution time in seconds.

    Returns:
        Result instance mirroring the outcome of the execution.
    """
    if not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError(f"Timeout must be a positive number, got {timeout}")

    try:
        exec_dict = execute_code(code, timeout=int(timeout))
        return _dict_to_result(exec_dict)
    except SandboxError as e:
        return Result(status=ExecutionStatus.ERROR.value, error=str(e))
    except Exception as e:
        return Result(status=ExecutionStatus.ERROR.value, error=str(e))


def main():
    """Main entry point for CLI usage."""
    # Example usage
    sample_code = """
print("Hello from sandbox")
result = sum(range(10))
print(f"Sum: {result}")
"""
    try:
        result = run_in_sandbox(sample_code)
        print(f"Status: {result.status}")
        print(f"Output: {result.output}")
        print(f"Error: {result.error}")
    except SandboxError as e:
        print(f"Sandbox error: {e}")


if __name__ == "__main__":
    main()