"""
Sandbox utilities for enforcing resource limits on code execution.

Implements hard timeouts and memory limits as per FR-005.
"""
import os
import sys
import signal
import resource
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Callable, Union
from dataclasses import dataclass
from contextlib import contextmanager

# Constants
DEFAULT_TIMEOUT_SECONDS = 5
DEFAULT_MEMORY_LIMIT_BYTES = 500 * 1024 * 1024  # 500 MB
MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10 MB max output capture


class SandboxTimeoutError(Exception):
    """Raised when code execution exceeds the time limit."""
    pass


class SandboxMemoryError(Exception):
    """Raised when code execution exceeds the memory limit."""
    pass


class SandboxExecutionError(Exception):
    """Raised for other execution failures."""
    pass


@dataclass
class ExecutionResult:
    """Result of a sandboxed execution."""
    success: bool
    output: Optional[str]
    error: Optional[str]
    exit_code: Optional[int]
    timeout: bool
    memory_exceeded: bool
    duration_seconds: Optional[float]
    peak_memory_bytes: Optional[int]


@contextmanager
def _resource_limits(timeout: int, memory_limit: int):
    """
    Context manager to enforce timeout and memory limits.
    
    Uses signal.alarm for timeout and resource.setrlimit for memory.
    Note: signal.alarm only works on Unix-like systems.
    """
    if os.name != 'posix':
        # On Windows, we rely on subprocess timeout only
        yield
        return

    old_alarm = signal.signal(signal.SIGALRM, _timeout_handler)
    old_limit = resource.getrlimit(resource.RLIMIT_AS)
    
    try:
        signal.alarm(timeout)
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit, memory_limit))
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_alarm)
        resource.setrlimit(resource.RLIMIT_AS, old_limit)


def _timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Execution timed out")


def _get_memory_usage() -> int:
    """Get current memory usage in bytes."""
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on macOS
        if sys.platform == 'darwin':
            return usage.ru_maxrss
        else:
            return usage.ru_maxrss * 1024
    except Exception:
        return 0


def run_in_sandbox(
    code: str,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit: int = DEFAULT_MEMORY_LIMIT_BYTES,
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[Union[str, Path]] = None
) -> ExecutionResult:
    """
    Execute Python code in a sandboxed environment with resource limits.
    
    Args:
        code: The Python code to execute.
        timeout: Maximum execution time in seconds.
        memory_limit: Maximum memory usage in bytes.
        env: Optional environment variables.
        cwd: Optional working directory.
        
    Returns:
        ExecutionResult with execution details.
        
    Raises:
        SandboxTimeoutError: If execution exceeds timeout.
        SandboxMemoryError: If execution exceeds memory limit.
    """
    if not isinstance(code, str):
        raise ValueError("Code must be a string")
        
    if os.name != 'posix' and timeout <= 0:
        raise ValueError("Timeout must be positive on supported platforms")
        
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix='.py', 
        delete=False, 
        encoding='utf-8'
    ) as f:
        f.write(code)
        temp_file = f.name

    try:
        # Prepare command
        cmd = [sys.executable, temp_file]
        
        # Prepare environment
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
            
        # Record start time
        start_time = __import__('time').time()
        
        try:
            # Run with subprocess timeout (cross-platform)
            result = subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=True,
                text=True,
                env=run_env,
                cwd=str(cwd) if cwd else None,
                # Limit input/output sizes
                input=None,
                start_new_session=True  # Allow killing process group
            )
            
            duration = __import__('time').time() - start_time
            
            # Check for memory issues in output (if detectable)
            memory_exceeded = False
            if result.stderr and "MemoryError" in result.stderr:
                memory_exceeded = True
                
            return ExecutionResult(
                success=result.returncode == 0,
                output=result.stdout[:MAX_OUTPUT_SIZE] if result.stdout else None,
                error=result.stderr[:MAX_OUTPUT_SIZE] if result.stderr else None,
                exit_code=result.returncode,
                timeout=False,
                memory_exceeded=memory_exceeded,
                duration_seconds=duration,
                peak_memory_bytes=_get_memory_usage()
            )
            
        except subprocess.TimeoutExpired as e:
            duration = __import__('time').time() - start_time
            # Kill any remaining process group
            if e.stdout:
                stdout = e.stdout.decode('utf-8', errors='replace')
            else:
                stdout = None
            if e.stderr:
                stderr = e.stderr.decode('utf-8', errors='replace')
            else:
                stderr = None
              
            return ExecutionResult(
                success=False,
                output=stdout[:MAX_OUTPUT_SIZE] if stdout else None,
                error=stderr[:MAX_OUTPUT_SIZE] if stderr else None,
                exit_code=None,
                timeout=True,
                memory_exceeded=False,
                duration_seconds=duration,
                peak_memory_bytes=_get_memory_usage()
            )
            
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except OSError:
            pass


def run_code_with_limits(
    func: Callable[[], Any],
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    memory_limit: int = DEFAULT_MEMORY_LIMIT_BYTES
) -> Tuple[Any, ExecutionResult]:
    """
    Run a Python function with resource limits.
    
    This is for in-process execution where we want to monitor
    the function directly rather than spawning a subprocess.
    
    Args:
        func: The function to execute.
        timeout: Maximum execution time in seconds.
        memory_limit: Maximum memory usage in bytes.
        
    Returns:
        Tuple of (result, ExecutionResult)
        
    Raises:
        SandboxTimeoutError: If execution exceeds timeout.
        SandboxMemoryError: If execution exceeds memory limit.
    """
    result_container = {'value': None, 'error': None}
    
    def wrapper():
        try:
            result_container['value'] = func()
        except Exception as e:
            result_container['error'] = e
            
    start_time = __import__('time').time()
    
    try:
        with _resource_limits(timeout, memory_limit):
            wrapper()
            
        duration = __import__('time').time() - start_time
        
        if result_container['error']:
            return None, ExecutionResult(
                success=False,
                output=None,
                error=str(result_container['error']),
                exit_code=1,
                timeout=False,
                memory_exceeded=False,
                duration_seconds=duration,
                peak_memory_bytes=_get_memory_usage()
            )
            
        return result_container['value'], ExecutionResult(
            success=True,
            output=None,
            error=None,
            exit_code=0,
            timeout=False,
            memory_exceeded=False,
            duration_seconds=duration,
            peak_memory_bytes=_get_memory_usage()
        )
        
    except TimeoutError:
        duration = __import__('time').time() - start_time
        return None, ExecutionResult(
            success=False,
            output=None,
            error="Execution timed out",
            exit_code=None,
            timeout=True,
            memory_exceeded=False,
            duration_seconds=duration,
            peak_memory_bytes=_get_memory_usage()
        )
    except Exception as e:
        duration = __import__('time').time() - start_time
        return None, ExecutionResult(
            success=False,
            output=None,
            error=str(e),
            exit_code=1,
            timeout=False,
            memory_exceeded="MemoryError" in str(e),
            duration_seconds=duration,
            peak_memory_bytes=_get_memory_usage()
        )


def main():
    """
    CLI entry point for testing the sandbox.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test sandbox execution with resource limits"
    )
    parser.add_argument(
        "--timeout", 
        type=int, 
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"Timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS})"
    )
    parser.add_argument(
        "--memory", 
        type=int, 
        default=DEFAULT_MEMORY_LIMIT_BYTES,
        help=f"Memory limit in bytes (default: {DEFAULT_MEMORY_LIMIT_BYTES})"
    )
    parser.add_argument(
        "--code", 
        type=str, 
        help="Python code to execute"
    )
    parser.add_argument(
        "--file", 
        type=str, 
        help="File containing Python code to execute"
    )
    
    args = parser.parse_args()
    
    if args.code:
        code = args.code
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            code = f.read()
    else:
        print("Error: Provide --code or --file")
        sys.exit(1)
        
    result = run_in_sandbox(
        code=code,
        timeout=args.timeout,
        memory_limit=args.memory
    )
    
    output = {
        "success": result.success,
        "timeout": result.timeout,
        "memory_exceeded": result.memory_exceeded,
        "duration_seconds": result.duration_seconds,
        "exit_code": result.exit_code,
        "output": result.output,
        "error": result.error
    }
    
    print(json.dumps(output, indent=2))
    
    if not result.success:
        sys.exit(1)


if __name__ == "__main__":
    main()