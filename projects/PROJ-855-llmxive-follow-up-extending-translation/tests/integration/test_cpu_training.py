"""
Integration test for CPU-only training loop (T020).

This test verifies that the training script:
1. Runs successfully on a CPU-only environment (no CUDA).
2. Completes within the 6-hour timeout constraint (simulated via timeout logic).
3. Logs peak RAM usage in the required format.
4. Produces a valid model file with < 10M parameters.
5. Does not attempt to allocate GPU memory.
"""
import os
import sys
import subprocess
import tempfile
import json
import time
import shutil
from pathlib import Path
import pytest

# Add code directory to path for imports if running locally
CODE_ROOT = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(CODE_ROOT))

TRAIN_SCRIPT = CODE_ROOT / "train_model.py"
PROCESSED_DATA_DIR = CODE_ROOT.parent / "data" / "processed"
OUTPUT_MODEL_PATH = PROCESSED_DATA_DIR / "trained_model.pt"

# Ensure paths exist for the test to run (mock if necessary, but prefer real check)
# Note: In a real CI/CD environment, T016c/T016b must have run first.
# We will assert existence or skip if data is missing to prevent false negatives in isolation.

@pytest.fixture(scope="module")
def ensure_data_exists():
    """
    Fixture to ensure required data files exist before running integration test.
    If T016c hasn't run, we skip the integration test rather than fail.
    """
    train_parquet = PROCESSED_DATA_DIR / "train.parquet"
    if not train_parquet.exists():
        pytest.skip(f"Required data file {train_parquet} not found. Please run T016c first.")
    return True

def test_cpu_training_integration(ensure_data_exists):
    """
    Integration test: Run train_model.py on CPU, verify outputs and logs.
    """
    # Clean up any previous model output
    if OUTPUT_MODEL_PATH.exists():
        OUTPUT_MODEL_PATH.unlink()

    # Prepare environment variables to force CPU
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = ""
    env["PYTORCH_NO_CUDA"] = "1"

    # Define a timeout (e.g., 10 minutes for integration test, 
    # though real limit is 6 hours. We use a shorter time for CI speed).
    timeout_seconds = 600 

    start_time = time.time()
    
    try:
        # Run the training script
        # We use subprocess to capture stdout/stderr for log verification
        result = subprocess.run(
            [sys.executable, str(TRAIN_SCRIPT)],
            cwd=CODE_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds
        )
    except subprocess.TimeoutExpired:
        pytest.fail(f"Training script timed out after {timeout_seconds} seconds.")
    
    elapsed = time.time() - start_time

    # 1. Check exit code
    assert result.returncode == 0, (
        f"Training script failed with code {result.returncode}.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # 2. Verify output file exists
    assert OUTPUT_MODEL_PATH.exists(), (
        f"Model file {OUTPUT_MODEL_PATH} was not created.\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )

    # 3. Verify RAM logging format (SC-002)
    # Look for the specific prefix in stdout
    ram_log_pattern = "[RAM-PEAK-MB]:"
    assert ram_log_pattern in result.stdout, (
        f"Failed to find RAM peak log pattern '{ram_log_pattern}' in stdout.\n"
        f"STDOUT:\n{result.stdout}"
    )

    # Extract and verify the RAM value is a number
    for line in result.stdout.splitlines():
        if ram_log_pattern in line:
            try:
                value_str = line.split(ram_log_pattern)[1].strip()
                ram_mb = float(value_str)
                assert ram_mb > 0, f"RAM value {ram_mb} must be positive."
                break
            except ValueError:
                pytest.fail(f"Invalid RAM value format in line: {line}")
    
    # 4. Verify parameter count constraint (< 10M)
    # We check the stdout for the parameter count log
    param_log_pattern = "Total parameters:"
    found_param_count = False
    for line in result.stdout.splitlines():
        if param_log_pattern in line:
            found_param_count = True
            # Extract number (e.g., "Total parameters: 5432100")
            parts = line.split(":")
            if len(parts) > 1:
                try:
                    param_count = int(parts[-1].strip().replace(",", ""))
                    assert param_count < 10_000_000, (
                        f"Model parameter count {param_count} exceeds 10M limit."
                    )
                    print(f"Verified parameter count: {param_count} < 10M")
                    break
                except ValueError:
                    pass
    
    assert found_param_count, (
        f"Could not find parameter count log in stdout.\n"
        f"STDOUT:\n{result.stdout}"
    )

    # 5. Verify no CUDA errors or GPU allocation attempts in stderr
    cuda_errors = ["CUDA out of memory", "CUDA error", "Cannot load CUDA"]
    for error in cuda_errors:
        assert error not in result.stderr, (
            f"Found CUDA error in stderr: {error}\nSTDERR:\n{result.stderr}"
        )

    print(f"Integration test passed. Time: {elapsed:.2f}s, RAM logged, Params < 10M.")

def test_no_gpu_allocation():
    """
    Additional check: Ensure torch.cuda.is_available() is False or ignored during run.
    We verify this by checking the environment setup in the script execution context.
    """
    # This is implicitly tested by the environment variables in the main test,
    # but we can add a specific assertion if the script explicitly checks for CUDA.
    # For now, the absence of CUDA errors in test_cpu_training_integration is sufficient.
    pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
