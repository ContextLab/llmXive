import pytest
import sys
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from memory_monitor import get_peak_memory_mb, reset_peak_memory

# Constants
MEMORY_LIMIT_MB = 6144  # 6 GB

@pytest.fixture
def reset_memory():
    reset_peak_memory()
    yield
    reset_peak_memory()

def test_memory_monitor_basic(reset_memory):
    """Test that memory monitor correctly tracks basic allocations."""
    # Simulate some memory usage
    data = [i for i in range(1000000)]
    peak = get_peak_memory_mb()
    assert peak > 0, "Peak memory should be greater than 0 after allocation"
    del data
    reset_peak_memory()

def test_training_execution_memory_limit(reset_memory):
    """
    Pytest fixture/test that wraps training execution and asserts peak memory < 6 GB.
    
    This test invokes the training script (code/03_train.py) as a subprocess to ensure
    we measure the actual memory usage of the full training pipeline, including
    data loading, model training, and permutation testing.
    
    The test asserts that the peak memory reported by the memory_monitor module
    during the execution does not exceed the 6 GB limit defined in the project specs.
    """
    # Ensure we start fresh
    reset_peak_memory()
    
    # Path to the training script
    code_dir = Path(__file__).parent.parent / "code"
    train_script = code_dir / "03_train.py"
    
    if not train_script.exists():
        pytest.skip("Training script not found. Skipping memory limit test.")
    
    # We need to run the script in a way that allows us to check the memory.
    # Since memory_monitor uses a global process-wide tracker, we can run the script
    # as a subprocess and check the memory usage via the process's own monitoring
    # or by checking the output if the script logs it.
    # However, the task specifically asks for a fixture that wraps execution.
    # A more robust way for a CI environment is to run the script and assert
    # the memory limit was not breached based on the script's own logging or exit code,
    # OR by using psutil to monitor the subprocess directly.
    
    # Strategy: Run the script, capture its output, and check if it logged a memory warning.
    # Alternatively, since the memory_monitor is designed to be imported, we can't easily
    # access its internal state from a subprocess unless we write to a file.
    # Given the constraints, we will run the script and rely on the fact that if it
    # exceeds memory, it might crash or we can monitor the subprocess RSS.
    
    # Let's implement a direct subprocess monitoring approach using psutil.
    # This is the most reliable way to assert peak memory < 6GB for a subprocess.
    
    try:
        # Start the process
        process = subprocess.Popen(
            [sys.executable, str(train_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(code_dir.parent)
        )
        
        import psutil
        try:
            proc = psutil.Process(process.pid)
            peak_mem_mb = 0
            
            while process.poll() is None:
                try:
                    mem_info = proc.memory_info()
                    current_mb = mem_info.rss / (1024 * 1024)
                    if current_mb > peak_mem_mb:
                        peak_mem_mb = current_mb
                except psutil.NoSuchProcess:
                    break
                
            # Wait for process to finish
            stdout, stderr = process.communicate(timeout=3600) # 1 hour timeout
            
            # Final check
            try:
                final_mem = proc.memory_info().rss / (1024 * 1024)
                if final_mem > peak_mem_mb:
                    peak_mem_mb = final_mem
            except psutil.NoSuchProcess:
                pass
            
            # Assert the limit
            assert peak_mem_mb < MEMORY_LIMIT_MB, (
                f"Peak memory usage {peak_mem_mb:.2f} MB exceeds limit of {MEMORY_LIMIT_MB} MB. "
                f"Script output:\n{stdout.decode()}\n{stderr.decode()}"
            )
            
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
                
    except subprocess.TimeoutExpired:
        pytest.fail("Training script exceeded timeout. Memory limit test inconclusive.")
    except Exception as e:
        pytest.fail(f"Error running training script: {e}")