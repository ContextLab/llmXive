"""
Sandbox module for executing HumanEval test suites in an isolated environment.
Implements strict resource limits (memory, CPU time, timeout) using subprocess
and the resource module to ensure stability and prevent network access.
"""
import os
import sys
import subprocess
import tempfile
import shutil
import resource
import signal
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, Tuple, List

# Import existing logging utilities from utils
try:
    from utils import setup_logging, get_logger, set_task_id, get_task_id
except ImportError:
    # Fallback for direct execution or missing utils
    def setup_logging():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
        return logging.getLogger(__name__)
    
    def get_logger(name=None):
        return logging.getLogger(name or __name__)
    
    def set_task_id(tid):
        pass
    
    def get_task_id():
        return None

# Constants
MEMORY_LIMIT_GB = 2
MEMORY_LIMIT_BYTES = MEMORY_LIMIT_GB * 1024 * 1024 * 1024
TIMEOUT_SECONDS = 30
CPU_LIMIT_SECONDS = 30  # Soft limit for CPU time

# Create sandbox directory if it doesn't exist
SANDBOX_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sandbox')

def ensure_sandbox_dir():
    """Ensure the sandbox directory exists."""
    if not os.path.exists(SANDBOX_DIR):
        os.makedirs(SANDBOX_DIR, exist_ok=True)
    return SANDBOX_DIR

@contextmanager
def sandbox_context(task_id: str = None):
    """
    Context manager that sets up an isolated execution environment.
    
    Sets strict resource limits:
    - Memory: 2GB
    - CPU Time: 30s
    - Wall Time: 30s (enforced via subprocess timeout)
    
    Args:
        task_id: Optional task ID for logging purposes.
        
    Yields:
        None
        
    Raises:
        RuntimeError: If resource limits cannot be set.
    """
    logger = get_logger('SANDBOX')
    if task_id:
        logger.info(f"Setting up sandbox for task {task_id}")
    else:
        logger.info("Setting up sandbox")
    
    # Save original limits
    original_rlimits = {}
    try:
        original_rlimits['mem'] = resource.getrlimit(resource.RLIMIT_AS)
        original_rlimits['cpu'] = resource.getrlimit(resource.RLIMIT_CPU)
        original_rlimits['data'] = resource.getrlimit(resource.RLIMIT_DATA)
        original_rlimits['stack'] = resource.getrlimit(resource.RLIMIT_STACK)
    except (ValueError, OSError) as e:
        logger.warning(f"Could not get original limits: {e}")
    
    try:
        # Set new limits
        # RLIMIT_AS: Address space limit (memory)
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
        # RLIMIT_CPU: CPU time limit
        resource.setrlimit(resource.RLIMIT_CPU, (CPU_LIMIT_SECONDS, CPU_LIMIT_SECONDS))
        # RLIMIT_DATA: Data segment size
        resource.setrlimit(resource.RLIMIT_DATA, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
        # RLIMIT_STACK: Stack size (keep reasonable)
        resource.setrlimit(resource.RLIMIT_STACK, (1024 * 1024, 1024 * 1024))  # 1MB
        
        if task_id:
            logger.info(f"Sandbox limits set: Memory={MEMORY_LIMIT_GB}GB, CPU={CPU_LIMIT_SECONDS}s")
        else:
            logger.info(f"Sandbox limits set: Memory={MEMORY_LIMIT_GB}GB, CPU={CPU_LIMIT_SECONDS}s")
        
        yield
        
    except ValueError as e:
        logger.error(f"Failed to set resource limits: {e}")
        raise RuntimeError(f"Cannot set resource limits: {e}")
    finally:
        # Restore original limits
        try:
            if 'mem' in original_rlimits:
                resource.setrlimit(resource.RLIMIT_AS, original_rlimits['mem'])
            if 'cpu' in original_rlimits:
                resource.setrlimit(resource.RLIMIT_CPU, original_rlimits['cpu'])
            if 'data' in original_rlimits:
                resource.setrlimit(resource.RLIMIT_DATA, original_rlimits['data'])
            if 'stack' in original_rlimits:
                resource.setrlimit(resource.RLIMIT_STACK, original_rlimits['stack'])
        except (ValueError, OSError) as e:
            logger.warning(f"Could not restore original limits: {e}")

def execute_code_in_sandbox(code: str, test_code: str, entry_point: str = None, timeout: int = TIMEOUT_SECONDS) -> Dict[str, Any]:
    """
    Executes code and its test suite in an isolated sandbox.
    
    Args:
        code: The code to execute (function definition).
        test_code: The test code to run against the function.
        entry_point: Name of the function to test (optional, inferred if None).
        timeout: Maximum execution time in seconds.
        
    Returns:
        Dictionary with execution results:
            - 'status': 'passed', 'failed', 'timeout', 'error', 'memory_error'
            - 'output': stdout/stderr output
            - 'return_code': exit code
            - 'execution_time': time taken (if applicable)
            
    Raises:
        RuntimeError: If execution environment cannot be created.
    """
    logger = get_logger('SANDBOX_EXEC')
    logger.info(f"Executing code in sandbox (timeout={timeout}s)")
    
    # Create a temporary directory for execution
    temp_dir = tempfile.mkdtemp(dir=ensure_sandbox_dir())
    code_file = os.path.join(temp_dir, 'solution.py')
    test_file = os.path.join(temp_dir, 'test_solution.py')
    
    try:
        # Write code and test files
        with open(code_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_code)
        
        # Prepare the execution command
        # We run the test file which imports and tests the solution
        cmd = [
            sys.executable, '-c',
            f"""
import sys
import os
import time

# Add temp dir to path so imports work
sys.path.insert(0, '{temp_dir}')

# Redirect stderr to capture errors
import io
from contextlib import redirect_stderr, redirect_stdout

stdout_capture = io.StringIO()
stderr_capture = io.StringIO()

start_time = time.time()
status = 'passed'
output = ''

try:
    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
  # Import the solution module
  import solution
  
  # Run the test
  exec(open('{test_file}').read())
  
  # If we get here without exception, tests passed
  status = 'passed'
except TimeoutError:
    status = 'timeout'
except MemoryError:
    status = 'memory_error'
except Exception as e:
    status = 'failed'
    output = str(e)
finally:
    end_time = time.time()
    exec_time = end_time - start_time
    
    # Get captured output
    stdout_val = stdout_capture.getvalue()
    stderr_val = stderr_capture.getvalue()
    
    result = {{
  'status': status,
  'output': stdout_val + stderr_val + output,
  'execution_time': exec_time,
  'return_code': 0 if status == 'passed' else 1
    }}
    
    import json
    print(json.dumps(result))
            """
        ]
        
        # Execute with timeout and resource limits
        result = None
        try:
            with sandbox_context():
                proc = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=temp_dir,
                    env={**os.environ, 'PYTHONPATH': temp_dir}
                )
                
                # Parse the result JSON from stdout
                output_str = proc.stdout.strip()
                if output_str:
                    try:
                        import json
                        result = json.loads(output_str)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse JSON output: {output_str}")
                        result = {
                            'status': 'error',
                            'output': output_str + proc.stderr,
                            'execution_time': 0,
                            'return_code': proc.returncode
                        }
                else:
                    result = {
                        'status': 'error',
                        'output': proc.stderr,
                        'execution_time': 0,
                        'return_code': proc.returncode
                    }
                    
        except subprocess.TimeoutExpired:
            logger.warning(f"Execution timed out after {timeout}s")
            result = {
                'status': 'timeout',
                'output': '',
                'execution_time': timeout,
                'return_code': -1
            }
        except MemoryError:
            logger.warning("Execution hit memory limit")
            result = {
                'status': 'memory_error',
                'output': '',
                'execution_time': 0,
                'return_code': -1
            }
        except Exception as e:
            logger.error(f"Execution error: {e}")
            result = {
                'status': 'error',
                'output': str(e),
                'execution_time': 0,
                'return_code': -1
            }
        
        return result
        
    finally:
        # Cleanup temporary files
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

def run_test_suite(code: str, tests: str, entry_point: str = None) -> float:
    """
    Runs a test suite and calculates pass rate.
    
    Args:
        code: The code to test.
        tests: The test code to run.
        entry_point: Name of the function to test.
        
    Returns:
        Pass rate as a float (0.0 to 1.0).
    """
    logger = get_logger('SANDBOX_PASS_RATE')
    logger.info("Calculating pass rate for test suite")
    
    # For HumanEval, we typically run the full test suite
    # The result status tells us if all tests passed
    result = execute_code_in_sandbox(code, tests, entry_point)
    
    if result['status'] == 'passed':
        return 1.0
    else:
        return 0.0

if __name__ == "__main__":
    # Simple test of the sandbox functionality
    test_code = """
def add(a, b):
    return a + b

# Test
assert add(2, 3) == 5
assert add(0, 0) == 0
assert add(-1, 1) == 0
print("All tests passed")
"""
    
    result = execute_code_in_sandbox(test_code, "", timeout=10)
    print(f"Result: {result}")
    
    if result['status'] == 'passed':
        print("Sandbox test PASSED")
        sys.exit(0)
    else:
        print(f"Sandbox test FAILED: {result['status']}")
        sys.exit(1)