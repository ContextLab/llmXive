"""
Integration test for User Story 3: Profiling.
Runs the pipeline on a small subset and asserts resource logs are generated and non-zero.
"""
import os
import json
import pytest
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil

# Ensure the project root is in the path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.profiling import start_profiling, stop_profiling, get_peak_memory_mb
from gatekeeper.pipeline import GatekeeperPipeline
from data.loader import fetch_gatemem, validate_fields

class TestUS3ProfilingIntegration:
    """
    Integration test: Run pipeline on small subset and assert resource logs are generated and non-zero.
    """

    def test_profiling_integration_small_subset(self, tmp_path):
        """
        Run the Gatekeeper pipeline on a small subset of the GateMem dataset
        and verify that profiling results (latency and RAM) are recorded and non-zero.
        """
        # Setup temporary output directory
        output_dir = tmp_path / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / "performance_results.json"

        # 1. Fetch a small subset of the real GateMem dataset
        # We fetch the full dataset but process only a few episodes to save time
        # T006 ensures we have a loader, but we call fetch_gatemem directly here
        try:
            dataset = fetch_gatemem()
        except Exception as e:
            # If dataset fetch fails (e.g., network), skip this test or fail loudly
            # For integration tests, we expect the environment to have access
            pytest.fail(f"Failed to fetch GateMem dataset: {e}")

        if len(dataset) == 0:
            pytest.fail("Dataset is empty")

        # Select a small subset (e.g., 5 episodes) for speed
        subset_size = 5
        subset_data = dataset.select(range(min(subset_size, len(dataset))))
        
        # 2. Initialize the pipeline
        # We need to configure the pipeline to run on this subset
        # The GatekeeperPipeline expects a dataset and config
        pipeline = GatekeeperPipeline(
            dataset=subset_data,
            config={
                "output_dir": str(output_dir),
                "mode": "test", # Run in test mode to skip heavy LLM generation if possible, or just run fast
                "profile": True
            }
        )

        # 3. Start profiling
        start_profiling()
        
        # 4. Run the pipeline
        # We run the gatekeeper logic which should trigger the classifier and rules
        # This will process the subset and record metrics
        try:
            pipeline.run()
        except Exception as e:
            # If the pipeline fails due to missing model files or other setup issues,
            # we need to ensure the test environment is correct.
            # However, the task is to assert resource logs exist.
            # If the pipeline crashes before logging, we fail.
            pytest.fail(f"Pipeline execution failed: {e}")

        # 5. Stop profiling
        stop_profiling()
        
        peak_ram = get_peak_memory_mb()
        
        # 6. Assertions
        # A. Check that the results file exists
        assert results_file.exists(), f"Performance results file {results_file} was not created"

        # B. Load and verify content
        with open(results_file, 'r') as f:
            results = json.load(f)

        # C. Verify structure matches expected schema (latency_ms, peak_ram_mb)
        assert "latency_ms" in results, "Results missing 'latency_ms'"
        assert "peak_ram_mb" in results, "Results missing 'peak_ram_mb'"

        # D. Assert values are non-zero (meaningful measurement occurred)
        # Note: In some virtualized environments, RAM might be low, but > 0 for a running process
        assert results["latency_ms"] > 0, f"Latency must be non-zero, got {results['latency_ms']}"
        assert results["peak_ram_mb"] > 0, f"Peak RAM must be non-zero, got {results['peak_ram_mb']}"

        # E. Verify the profiling API also recorded values (cross-check)
        assert peak_ram > 0, f"Global peak memory profiler recorded 0 MB"

    def test_profiling_on_baseline_subset(self, tmp_path):
        """
        Run the Baseline pipeline on a small subset and verify profiling.
        """
        output_dir = tmp_path / "baseline_results"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        results_file = output_dir / "baseline_performance_results.json"

        try:
            dataset = fetch_gatemem()
        except Exception as e:
            pytest.fail(f"Failed to fetch GateMem dataset: {e}")

        subset_size = 3
        subset_data = dataset.select(range(min(subset_size, len(dataset))))

        pipeline = GatekeeperPipeline(
            dataset=subset_data,
            config={
                "output_dir": str(output_dir),
                "mode": "baseline", # Run baseline mode
                "profile": True
            }
        )

        start_profiling()
        try:
            pipeline.run()
        except Exception as e:
            pytest.fail(f"Baseline pipeline execution failed: {e}")
        stop_profiling()

        assert results_file.exists(), f"Baseline results file {results_file} was not created"

        with open(results_file, 'r') as f:
            results = json.load(f)

        assert "latency_ms" in results
        assert "peak_ram_mb" in results
        assert results["latency_ms"] > 0
        assert results["peak_ram_mb"] > 0