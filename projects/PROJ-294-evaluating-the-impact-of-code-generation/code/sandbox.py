import os
import sys
import subprocess
import tempfile
import shutil
import resource
import logging
from utils import setup_logging, get_logger, set_task_id, get_task_id

def ensure_sandbox_dir():
    """Create data/sandbox/ directory if needed."""
    sandbox_dir = "data/sandbox"
    os.makedirs(sandbox_dir, exist_ok=True)
    return sandbox_dir

class TestSandbox:
    """
    T015a: Isolated execution environment for HumanEval test suites.
    """
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.sandbox_dir = ensure_sandbox_dir()
        self.logger = setup_logging(task_id="T015a")

    def __enter__(self):
        # Create a temporary directory for execution
        self.temp_dir = tempfile.mkdtemp(dir=self.sandbox_dir)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def execute(self, code: str, test_code: str) -> dict:
        """
        Execute code and tests in a sandboxed environment.
        Enforces memory limit and timeout.
        """
        result = {"passed": False, "error": None, "output": None}
        
        # Write code and test to temp files
        code_file = os.path.join(self.temp_dir, "solution.py")
        test_file = os.path.join(self.temp_dir, "test.py")
        
        with open(code_file, "w") as f:
            f.write(code)
        with open(test_file, "w") as f:
            f.write(test_code)

        # Prepare command
        cmd = [sys.executable, test_file]
        
        try:
            # Run with timeout and resource limits
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.temp_dir,
                preexec_fn=lambda: resource.setrlimit(
                    resource.RLIMIT_AS, 
                    (2 * 1024 * 1024 * 1024, 2 * 1024 * 1024 * 1024)
                )
            )
            
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                result["output"] = stdout.decode("utf-8")
                result["error"] = stderr.decode("utf-8")
                result["passed"] = (process.returncode == 0)
            except subprocess.TimeoutExpired:
                process.kill()
                result["error"] = "Timeout expired"
                result["passed"] = False
        except Exception as e:
            result["error"] = str(e)
            result["passed"] = False

        return result

def run_test_suite(code: str, test_code: str, timeout: int = 10) -> dict:
    """Helper to run test suite without context manager."""
    with TestSandbox(timeout=timeout) as sandbox:
        return sandbox.execute(code, test_code)

def add(a, b):
    """Test function."""
    return a + b

def main():
    logger = setup_logging(task_id="T015a")
    logger.info("Sandbox module initialized.")

if __name__ == "__main__":
    main()
