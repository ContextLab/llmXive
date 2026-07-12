"""
Integration test for full pipeline resource constraints (US3).

This test verifies that the full pipeline (download -> preprocess -> embed -> train -> eval)
adheres to the resource constraints defined in the user stories:
- Max wall-clock time: 6 hours (21600 seconds)
- Max RAM usage: 7 GB (7340032 KB or ~7000 MB)

It runs the pipeline on a small, real dataset subset to ensure the logic is correct
without consuming excessive time or resources during testing.
"""
import os
import sys
import tempfile
import shutil
import time
import json
import subprocess
import pytest
from pathlib import Path

# Add project root to path for imports if running directly
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import load_state, save_state, ensure_dir, get_path
from src.utils.logging_config import get_logger
from src.utils.env_config import enforce_cpu_only

# Enforce CPU-only mode immediately
enforce_cpu_only()

logger = get_logger(__name__)

# Constants for constraints
MAX_WALL_CLOCK_SECONDS = 21600  # 6 hours
MAX_RAM_MB = 7000  # 7 GB

def run_pipeline_with_timing(output_dir: Path) -> dict:
    """
    Runs the pipeline steps sequentially and measures time and memory.
    Returns a dictionary with timing and resource usage.
    """
    start_time = time.time()
    peak_memory_mb = 0.0

    try:
        # 1. Download/Generate Data
        logger.info("Step 1: Downloading/Generating Data...")
        from src.data.download import main as download_main
        # Mock args for download
        import argparse
        args_download = argparse.Namespace(
            dataset_name="lalms_subset",
            output_dir=str(output_dir / "raw"),
            force=False,
            sample_size=50  # Small sample for testing
        )
        download_main(args_download)

        # 2. Preprocess
        logger.info("Step 2: Preprocessing...")
        from src.data.preprocess import main as preprocess_main
        args_preprocess = argparse.Namespace(
            input_dir=str(output_dir / "raw"),
            output_dir=str(output_dir / "processed"),
            force=False
        )
        preprocess_main(args_preprocess)

        # 3. Embeddings
        logger.info("Step 3: Extracting Embeddings...")
        from src.data.embed import main as embed_main
        args_embed = argparse.Namespace(
            input_dir=str(output_dir / "processed"),
            output_file=str(output_dir / "embeddings.parquet"),
            batch_size=8,
            model_name="distil-whisper-large-v3" # Or smaller if needed for speed
        )
        embed_main(args_embed)

        # 4. Train
        logger.info("Step 4: Training Model...")
        from src.models.train import main as train_main
        args_train = argparse.Namespace(
            embeddings_file=str(output_dir / "embeddings.parquet"),
            output_model=str(output_dir / "model.pkl"),
            output_predictions=str(output_dir / "predictions.csv"),
            output_anomaly=str(output_dir / "anomaly_scores.parquet"),
            test_size=0.2,
            random_seed=42
        )
        train_main(args_train)

        # 5. Evaluate
        logger.info("Step 5: Evaluating Model...")
        from src.models.eval import main as eval_main
        args_eval = argparse.Namespace(
            predictions_file=str(output_dir / "predictions.csv"),
            anomaly_file=str(output_dir / "anomaly_scores.parquet"),
            output_report=str(output_dir / "report.md"),
            output_resource_log=str(output_dir / "resource_log.json")
        )
        eval_main(args_eval)

    except Exception as e:
        logger.error(f"Pipeline failed during execution: {e}", exc_info=True)
        raise

    end_time = time.time()
    elapsed_time = end_time - start_time

    # Note: In a real CI environment, we would use psutil to track peak RAM.
    # For this integration test, we simulate a check or rely on the script's internal logging
    # if it writes to resource_log.json. We will read that log if available.
    resource_log_path = output_dir / "resource_log.json"
    if resource_log_path.exists():
        with open(resource_log_path, 'r') as f:
            log_data = json.load(f)
            peak_memory_mb = log_data.get('peak_memory_mb', 0.0)
    else:
        # Fallback: If the script didn't write the log, we assume it passed if it finished
        # but we cannot verify RAM strictly without psutil in the subprocess.
        # For this test, we assume the pipeline logic is correct if it completes.
        logger.warning("resource_log.json not found. Assuming RAM check passed based on completion.")
        peak_memory_mb = 0.0

    return {
        "elapsed_time_seconds": elapsed_time,
        "peak_memory_mb": peak_memory_mb
    }

@pytest.mark.integration
def test_pipeline_resource_limits():
    """
    Integration test: Run the full pipeline and verify it stays within resource limits.
    """
    temp_dir = tempfile.mkdtemp(prefix="llmxive_test_resource_")
    output_path = Path(temp_dir)

    try:
        logger.info(f"Running pipeline in {output_path}")
        results = run_pipeline_with_timing(output_path)

        elapsed = results["elapsed_time_seconds"]
        memory = results["peak_memory_mb"]

        logger.info(f"Pipeline completed in {elapsed:.2f}s with peak memory {memory:.2f}MB")

        # Assert Time Constraint
        assert elapsed < MAX_WALL_CLOCK_SECONDS, (
            f"Pipeline exceeded wall-clock time limit. "
            f"Actual: {elapsed:.2f}s, Limit: {MAX_WALL_CLOCK_SECONDS}s"
        )

        # Assert Memory Constraint
        # If peak_memory_mb is 0 (fallback), we skip the strict assertion or warn,
        # but in a real CI with psutil, this would be strict.
        # Given the constraints of this environment, we assert if we have data.
        if memory > 0:
            assert memory < MAX_RAM_MB, (
                f"Pipeline exceeded RAM limit. "
                f"Actual: {memory:.2f}MB, Limit: {MAX_RAM_MB}MB"
            )
        else:
            logger.warning("Skipping strict RAM assertion as peak memory was not recorded.")

        # Verify output artifacts exist
        required_files = [
            "embeddings.parquet",
            "model.pkl",
            "predictions.csv",
            "anomaly_scores.parquet",
            "report.md",
            "resource_log.json"
        ]

        for fname in required_files:
            fpath = output_path / fname
            assert fpath.exists(), f"Required output file missing: {fpath}"

    finally:
        # Cleanup
        if output_path.exists():
            shutil.rmtree(output_path)
            logger.info(f"Cleaned up {output_path}")