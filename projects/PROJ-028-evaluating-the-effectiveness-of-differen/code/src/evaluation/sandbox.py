"""
Sandbox module for executing generated code with resource constraints.

Implements FR-004: Hardcoded 10s timeout and constrained memory limit per subprocess
using resource.setrlimit.
"""
import os
import sys
import time
import subprocess
import tempfile
import resource
import signal
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Constants for resource limits (FR-004)
TIMEOUT_SECONDS = 10
# Memory limit: 512 MB (0.5 GB) to constrain system performance evaluation
# resource.setrlimit uses bytes
MEMORY_LIMIT_BYTES = 512 * 1024 * 1024 


class SandboxExecutionError(Exception):
    """Base exception for sandbox execution failures."""
    pass


class SandboxTimeoutError(SandboxExecutionError):
    """Raised when code execution exceeds the time limit."""
    pass


class SandboxMemoryError(SandboxExecutionError):
    """Raised when code execution exceeds the memory limit."""
    pass


class SandboxSecurityError(SandboxExecutionError):
    """Raised when code execution attempts forbidden operations."""
    pass


def _set_resource_limits():
    """
    Set resource limits for the current process.
    
    Called inside the child process before executing code.
    """
    # Set CPU time limit (soft and hard)
    resource.setrlimit(resource.RLIMIT_CPU, (TIMEOUT_SECONDS, TIMEOUT_SECONDS))
    
    # Set memory limit (soft and hard) in bytes
    # RLIMIT_AS limits the size of the process's virtual memory
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
    
    # Disable core dumps to prevent disk space issues
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))


def _execute_code_in_subprocess(code: str, timeout: int = TIMEOUT_SECONDS) -> Tuple[bool, str, str]:
    """
    Execute Python code in a subprocess with resource constraints.
    
    Args:
        code: The Python code to execute.
        timeout: Maximum execution time in seconds.
        
    Returns:
        Tuple of (success, stdout, stderr)
        
    Raises:
        SandboxTimeoutError: If execution exceeds the time limit.
        SandboxMemoryError: If execution exceeds memory limit.
        SandboxSecurityError: If forbidden operations are attempted.
    """
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        # Create a pipe for capturing output
        process = subprocess.Popen(
            [sys.executable, temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=_set_resource_limits  # Unix-only: set limits before exec
        )
        
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            if process.returncode == 0:
                return True, stdout_str, stderr_str
            else:
                # Check for specific error messages indicating resource limits
                if "MemoryError" in stderr_str or "virtual memory exhausted" in stderr_str:
                    raise SandboxMemoryError("Memory limit exceeded")
                return False, stdout_str, stderr_str
                
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            raise SandboxTimeoutError(f"Execution exceeded {timeout}s timeout")
            
    except (OSError, ValueError) as e:
        # Handle cases where preexec_fn fails or process creation fails
        if "resource" in str(e).lower():
            raise SandboxSecurityError("Cannot set resource limits (non-Unix system?)")
        raise SandboxExecutionError(f"Failed to execute code: {str(e)}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file)
        except OSError:
            pass


def execute_sandbox(code: str, timeout: int = TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Execute code in a sandboxed environment with resource constraints.
    
    Args:
        code: The Python code to execute.
        timeout: Maximum execution time in seconds (default: 10).
        
    Returns:
        Dictionary containing:
            - success (bool): Whether execution completed without exceptions
            - stdout (str): Standard output
            - stderr (str): Standard error
            - execution_time (float): Time taken in seconds
            - timeout (bool): Whether execution timed out
            - memory_exceeded (bool): Whether memory limit was exceeded
            - error_type (str): Type of error if any
    """
    start_time = time.time()
    
    result = {
        'success': False,
        'stdout': '',
        'stderr': '',
        'execution_time': 0.0,
        'timeout': False,
        'memory_exceeded': False,
        'error_type': None
    }
    
    try:
        success, stdout, stderr = _execute_code_in_subprocess(code, timeout)
        result['success'] = success
        result['stdout'] = stdout
        result['stderr'] = stderr
        
    except SandboxTimeoutError as e:
        result['timeout'] = True
        result['error_type'] = 'timeout'
        result['stderr'] = str(e)
        
    except SandboxMemoryError as e:
        result['memory_exceeded'] = True
        result['error_type'] = 'memory_limit'
        result['stderr'] = str(e)
        
    except SandboxSecurityError as e:
        result['error_type'] = 'security'
        result['stderr'] = str(e)
        
    except SandboxExecutionError as e:
        result['error_type'] = 'execution_error'
        result['stderr'] = str(e)
        
    except Exception as e:
        result['error_type'] = 'unexpected'
        result['stderr'] = str(e)
        
    finally:
        result['execution_time'] = time.time() - start_time
        
    return result


def run_code_with_sandbox(code: str, timeout: int = TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Wrapper for execute_sandbox that handles edge cases and platform differences.
    
    On non-Unix systems (Windows), resource limits cannot be enforced via setrlimit.
    In such cases, this function falls back to subprocess timeout only.
    
    Args:
        code: The Python code to execute.
        timeout: Maximum execution time in seconds.
        
    Returns:
        Execution result dictionary.
    """
    if sys.platform != 'linux' and sys.platform != 'darwin':
        # Fallback for Windows: only time limit via subprocess
        result = {
            'success': False,
            'stdout': '',
            'stderr': '',
            'execution_time': 0.0,
            'timeout': False,
            'memory_exceeded': False,
            'error_type': None
        }
        
        start_time = time.time()
        try:
            process = subprocess.Popen(
                [sys.executable, '-c', code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                result['success'] = (process.returncode == 0)
                result['stdout'] = stdout.decode('utf-8', errors='replace')
                result['stderr'] = stderr.decode('utf-8', errors='replace')
                
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                result['timeout'] = True
                result['error_type'] = 'timeout'
                result['stderr'] = f"Execution exceeded {timeout}s timeout"
                
        except Exception as e:
            result['error_type'] = 'execution_error'
            result['stderr'] = str(e)
            
        result['execution_time'] = time.time() - start_time
        return result
        
    return execute_sandbox(code, timeout)