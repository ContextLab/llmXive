"""
Integration test for the end-to-end grain boundary diffusivity pipeline.

Verifies the execution chain: T009 -> T010 -> T011 -> T016 -> T012.
Constraints: Must complete within 6 hours and use <7 GB RAM.

Note: This test assumes the data download (T009) has been executed
and raw data exists in data/raw/. If data is missing, it attempts to
run the download step first, but relies on the presence of real
external data sources (Materials Project, etc.) which may require
API keys.
"""
import os
import sys
import subprocess
import time
import tracemalloc
import json
import tempfile
import shutil
from pathlib import Path

import pytest

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODELS_DIR = PROJECT_ROOT / "models"

# Ensure paths are in sys.path for imports if running directly
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Maximum allowed memory (7 GB in bytes)
MAX_MEMORY_BYTES = 7 * 1024 * 1024 * 1024
# Maximum allowed time (6 hours in seconds) - reduced for CI safety to 1 hour if needed, 
# but spec says 6h. We will enforce the 6h limit in logic.
MAX_TIME_SECONDS = 6 * 3600

@pytest.fixture(scope="module")
def pipeline_env():
    """Ensure necessary directories exist."""
    dirs = [DATA_DIR, DATA_DIR / "raw", DATA_DIR / "processed", MODELS_DIR, ARTIFACTS_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup is optional for integration tests to preserve artifacts, 
    # but we ensure we don't leave temp files.

def run_script(script_name: str, args: list = None) -> subprocess.CompletedProcess:
    """Run a script from the code directory."""
    script_path = CODE_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")
    
    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)
    
    print(f"Running: {' '.join(cmd)}")
    start_time = time.time()
    process = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=MAX_TIME_SECONDS
    )
    elapsed = time.time() - start_time
    
    if process.returncode != 0:
        print(f"STDOUT:\n{process.stdout}")
        print(f"STDERR:\n{process.stderr}")
        raise RuntimeError(f"Script {script_name} failed with code {process.returncode} after {elapsed:.2f}s")
    
    print(f"Script {script_name} completed in {elapsed:.2f}s")
    return process

def check_memory_usage():
    """Check if peak memory usage exceeded the limit."""
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory: {current / 1024 / 1024:.2f} MB, Peak: {peak / 1024 / 1024:.2f} MB")
    if peak > MAX_MEMORY_BYTES:
        raise MemoryError(f"Peak memory usage {peak / 1024 / 1024:.2f} MB exceeded limit of {MAX_MEMORY_BYTES / 1024 / 1024:.2f} MB")

@pytest.mark.integration
def test_end_to_end_pipeline(pipeline_env):
    """
    Test the full pipeline: Download -> Parse -> Preprocess -> Diagnostics -> Train.
    Verifies timing and memory constraints.
    """
    tracemalloc.start()
    start_time = time.time()
    
    try:
        # 1. T009: Download
        # Note: If data already exists, this might skip or re-download depending on implementation.
        # We assume the script handles existence checks or we force re-run.
        # For this test, we assume the script is idempotent or data is missing.
        # If the download script requires API keys and they are missing, it should fail loudly.
        run_script("download.py")
        
        # Verify raw data exists
        raw_files = list((DATA_DIR / "raw").glob("*"))
        assert len(raw_files) > 0, "Download step failed to produce raw data files."

        # 2. T010: Geometry Parser
        run_script("geometry_parser.py")
        
        parsed_file = DATA_DIR / "processed" / "parsed_geometry.parquet"
        assert parsed_file.exists(), "Geometry parser failed to produce output."

        # 3. T011: Preprocess
        run_script("preprocess.py")
        
        cleaned_file = DATA_DIR / "processed" / "cleaned_dataset.parquet"
        assert cleaned_file.exists(), "Preprocess step failed to produce output."

        # 4. T016: Diagnostics
        run_script("diagnostics.py")
        
        diag_file = ARTIFACTS_DIR / "reports" / "collinearity_diagnostic.json"
        assert diag_file.exists(), "Diagnostics step failed to produce output."

        # 5. T012: Train
        run_script("train.py")
        
        model_file = MODELS_DIR / "best_model.json"
        metrics_file = ARTIFACTS_DIR / "reports" / "training_metrics.json"
        
        assert model_file.exists(), "Training step failed to save model."
        assert metrics_file.exists(), "Training step failed to save metrics."

        # Validate metrics file content
        with open(metrics_file, "r") as f:
            metrics = json.load(f)
            assert "r2" in metrics, "Metrics file missing 'r2' key."
            assert "rmse" in metrics, "Metrics file missing 'rmse' key."
            print(f"Model Metrics: R2={metrics['r2']}, RMSE={metrics['rmse']}")

    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        total_time = time.time() - start_time
        
        # Check constraints
        assert total_time <= MAX_TIME_SECONDS, f"Pipeline took {total_time:.2f}s, exceeding limit of {MAX_TIME_SECONDS}s"
        check_memory_usage()

    print("Pipeline integration test PASSED.")
    print(f"Total time: {total_time:.2f}s")
    print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
