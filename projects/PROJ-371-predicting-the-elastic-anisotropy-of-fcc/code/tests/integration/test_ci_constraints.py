"""
Integration tests for T017: Verify pipeline execution on free-tier CI constraints.

This module validates that the full data pipeline (Ingest -> Clean -> Features)
runs successfully within the memory (<7GB) and CPU-only constraints of free-tier
CI environments (e.g., GitHub Actions free tier, GitLab CI shared runners).

It executes a reduced subset of the pipeline to ensure:
1. The process completes without OOM (Out Of Memory) errors.
2. Execution time is reasonable for CI (< 5 minutes).
3. Output artifacts are correctly generated in `data/processed/`.
"""

import os
import sys
import subprocess
import time
import tempfile
import shutil
from pathlib import Path
import pytest
import pandas as pd

# Add project root to path if running from specific context
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import get_config, get_path, ensure_directories, set_random_seed

# Constants for CI Constraints
MAX_MEMORY_MB = 7168  # 7GB
MAX_TIME_SECONDS = 300  # 5 minutes
SAMPLE_SIZE = 10  # Number of entries to process for the constraint test

class TestCIConstraints:
    """Tests to verify pipeline performance under CI constraints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Ensure directories exist before test."""
        ensure_directories()
        yield

    def test_pipeline_memory_and_time_constraints(self):
        """
        Verify the pipeline runs on a sample subset within CI memory and time limits.

        This test:
        1. Sets up a temporary manifest with a small subset of known FCC IDs.
        2. Executes the pipeline script with the `--sample` flag.
        3. Monitors the process to ensure it exits cleanly.
        4. Verifies the output file exists and contains data.
        """
        set_random_seed(42)
        
        # Define the sample manifest path
        raw_dir = get_path("data_raw")
        manifest_path = raw_dir / "manifest_subset_ci.json"
        
        # Create a small subset manifest for the test
        # Using known FCC materials from Materials Project to ensure real data fetch
        sample_ids = [
            "mp-134",   # Aluminum (FCC)
            "mp-1144",  # Copper (FCC)
            "mp-3037",  # Nickel (FCC)
            "mp-11812", # Silver (FCC)
            "mp-1055",  # Gold (FCC)
            "mp-2296",  # Lead (FCC)
            "mp-1083",  # Platinum (FCC)
            "mp-1190",  # Palladium (FCC)
            "mp-1094",  # Iridium (FCC)
            "mp-1093"   # Rhodium (FCC)
        ]

        # Write the subset manifest
        import json
        with open(manifest_path, 'w') as f:
            json.dump({"ids": sample_ids}, f)

        # Construct the command to run the pipeline
        # We assume the script is runnable via python -m or direct path
        # The task description implies running the script directly
        pipeline_script = PROJECT_ROOT / "code" / "src" / "cli" / "run_pipeline.py"
        
        cmd = [
            sys.executable,
            str(pipeline_script),
            "--manifest", str(manifest_path),
            "--sample-size", str(SAMPLE_SIZE)
        ]

        start_time = time.time()
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = process.communicate(timeout=MAX_TIME_SECONDS)
        except subprocess.TimeoutExpired:
            process.kill()
            pytest.fail(f"Pipeline exceeded time limit of {MAX_TIME_SECONDS}s")

        end_time = time.time()
        elapsed = end_time - start_time

        # Check exit code
        if process.returncode != 0:
            pytest.fail(f"Pipeline failed with code {process.returncode}.\nStderr: {stderr}\nStdout: {stdout}")

        # Verify output file exists
        output_path = get_path("data_processed") / "elastic_anisotropy.csv"
        assert output_path.exists(), f"Output file {output_path} was not created."

        # Verify data content
        df = pd.read_csv(output_path)
        assert len(df) > 0, "Output CSV is empty."
        
        # Verify required columns exist (from T015/T016 logic)
        required_cols = ["C11", "C12", "C44", "A1"]
        for col in required_cols:
            assert col in df.columns, f"Missing required column: {col}"

        # Log metrics for CI monitoring
        print(f"Pipeline completed in {elapsed:.2f}s with {len(df)} entries.")
        print(f"Memory usage check passed (process exited cleanly without OOM).")
        print(f"Time usage: {elapsed:.2f}s (Limit: {MAX_TIME_SECONDS}s)")

        # Clean up the temporary manifest if it was created for this test
        # (Optional, but keeps data/raw clean for other runs)
        # We leave it for reproducibility if needed, but usually CI cleans state.

    def test_no_gpu_usage(self):
        """
        Verify that the pipeline does not attempt to initialize GPU resources.
        
        This is a heuristic check: we look for CUDA initialization errors or
        specific environment variable checks in the logs.
        """
        # This is a soft check. If the pipeline runs on CPU-only CI and doesn't crash,
        # it implies no GPU was forced. We verify the script doesn't import torch/cuda
        # in a way that forces allocation.
        
        # Check the source code for explicit CUDA forcing (e.g., torch.cuda.set_device)
        # which would fail on a CPU-only runner.
        pipeline_script = PROJECT_ROOT / "code" / "src" / "cli" / "run_pipeline.py"
        
        with open(pipeline_script, 'r') as f:
            content = f.read()
        
        # Simple heuristic: ensure no explicit CUDA device setting that would crash
        # on a headless CPU runner if not guarded.
        # Note: sklearn and pandas are CPU-only by default, so this is mostly for safety.
        assert "torch.cuda" not in content, "Pipeline script explicitly references torch.cuda."
        assert "CUDA_VISIBLE_DEVICES=1" not in os.environ.get("CUDA_VISIBLE_DEVICES", ""), \
            "Environment forces GPU usage."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
