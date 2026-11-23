"""
Integration test for end-to-end pipeline comparison (Static Baseline vs Dynamic Router).

This test verifies the full evaluation pipeline for User Story 3 (US3).
It compares the Static Baseline method against the Dynamic Router method
using real data artifacts generated in previous phases.

Prerequisites:
- data/processed/correlation_results.json (T018)
- data/processed/quantized_activations.json (T019a)
- data/processed/clustering_report.json (T022)
- code/evaluation/metrics.py (T030)
- code/evaluation/timing.py (T031)
- code/run_evaluation.py (T034) - The orchestration script being tested.

The test runs the evaluation pipeline on a small subset (configurable) to
ensure it completes within the time budget while validating the full flow.
"""

import os
import sys
import json
import time
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from evaluation.metrics import compute_metrics_batch, save_metrics_to_json
from evaluation.timing import measure_inference_time
from run_evaluation import run_static_baseline, run_dynamic_router, compare_results

# Configure logging for the test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestFullPipeline:
    """Integration tests for the full evaluation pipeline."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.config = Config()
        self.test_subset_size = 2  # Run on 2 samples to ensure speed
        self.output_dir = Path(self.config.data_dir) / "test_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Verify prerequisite artifacts exist
        self._verify_prerequisites()

    def _verify_prerequisites(self):
        """Check that required data files from previous phases exist."""
        required_files = [
            "data/processed/clustering_report.json",
            "data/processed/correlation_results.json",
            "data/processed/quantized_activations.json",
            "data/processed/prompts.csv"
        ]
        for file_path in required_files:
            full_path = PROJECT_ROOT / file_path
            assert full_path.exists(), f"Prerequisite file missing: {file_path}"
            logger.info(f"Found prerequisite: {file_path}")

    def test_static_baseline_execution(self):
        """
        Test that the static baseline pipeline runs and produces metrics.
        """
        logger.info("Running static baseline pipeline test...")

        try:
            # Run the static baseline on a small subset
            metrics, timing_data = run_static_baseline(
                subset_size=self.test_subset_size,
                output_dir=str(self.output_dir)
            )

            # Assertions on output structure
            assert isinstance(metrics, dict), "Metrics should be a dictionary"
            assert "fid" in metrics or "clip_score" in metrics, "Metrics must contain FID or CLIP score"
            assert "mse" in metrics, "Metrics must contain MSE"

            # Check timing data
            assert isinstance(timing_data, dict), "Timing data should be a dictionary"
            assert "total_time" in timing_data, "Timing data must include total_time"

            # Verify output file was created
            output_file = self.output_dir / "static_baseline_metrics.json"
            assert output_file.exists(), "Static baseline metrics file was not created"

            logger.info(f"Static baseline test passed. Metrics: {metrics}")

        except Exception as e:
            logger.error(f"Static baseline test failed: {e}")
            pytest.fail(f"Static baseline pipeline execution failed: {str(e)}")

    def test_dynamic_router_execution(self):
        """
        Test that the dynamic router pipeline runs and produces metrics.
        """
        logger.info("Running dynamic router pipeline test...")

        try:
            # Run the dynamic router on a small subset
            metrics, timing_data = run_dynamic_router(
                subset_size=self.test_subset_size,
                output_dir=str(self.output_dir)
            )

            # Assertions on output structure
            assert isinstance(metrics, dict), "Metrics should be a dictionary"
            assert "fid" in metrics or "clip_score" in metrics, "Metrics must contain FID or CLIP score"
            assert "mse" in metrics, "Metrics must contain MSE"

            # Check timing data
            assert isinstance(timing_data, dict), "Timing data should be a dictionary"
            assert "total_time" in timing_data, "Timing data must include total_time"

            # Verify output file was created
            output_file = self.output_dir / "dynamic_router_metrics.json"
            assert output_file.exists(), "Dynamic router metrics file was not created"

            logger.info(f"Dynamic router test passed. Metrics: {metrics}")

        except Exception as e:
            logger.error(f"Dynamic router test failed: {e}")
            pytest.fail(f"Dynamic router pipeline execution failed: {str(e)}")

    def test_comparison_logic(self):
        """
        Test that the comparison logic correctly computes overhead and gains.
        """
        logger.info("Running comparison logic test...")

        # Mock metrics for comparison
        static_metrics = {
            "fid": 15.0,
            "clip_score": 30.5,
            "mse": 0.002,
            "total_time": 10.0
        }
        dynamic_metrics = {
            "fid": 14.2,
            "clip_score": 31.0,
            "mse": 0.0018,
            "total_time": 11.5
        }

        try:
            comparison = compare_results(static_metrics, dynamic_metrics)

            # Verify comparison structure
            assert "fid_improvement_pct" in comparison, "Comparison missing FID improvement"
            assert "overhead_pct" in comparison, "Comparison missing overhead percentage"
            assert "mse_improvement_pct" in comparison, "Comparison missing MSE improvement"

            # Verify calculations (approximate)
            expected_fid_improvement = ((15.0 - 14.2) / 15.0) * 100
            assert abs(comparison["fid_improvement_pct"] - expected_fid_improvement) < 0.1, \
                f"FID improvement calculation incorrect: {comparison['fid_improvement_pct']} vs {expected_fid_improvement}"

            expected_overhead = ((11.5 - 10.0) / 10.0) * 100
            assert abs(comparison["overhead_pct"] - expected_overhead) < 0.1, \
                f"Overhead calculation incorrect: {comparison['overhead_pct']} vs {expected_overhead}"

            logger.info(f"Comparison logic test passed. Results: {comparison}")

        except Exception as e:
            logger.error(f"Comparison logic test failed: {e}")
            pytest.fail(f"Comparison logic failed: {str(e)}")

    def test_end_to_end_pipeline_integration(self):
        """
        Full end-to-end integration test: Run both methods and compare.
        This is the primary test for T029.
        """
        logger.info("Running full end-to-end pipeline integration test...")

        try:
            # Run static baseline
            static_metrics, static_timing = run_static_baseline(
                subset_size=self.test_subset_size,
                output_dir=str(self.output_dir)
            )

            # Run dynamic router
            dynamic_metrics, dynamic_timing = run_dynamic_router(
                subset_size=self.test_subset_size,
                output_dir=str(self.output_dir)
            )

            # Compare results
            comparison = compare_results(static_metrics, dynamic_metrics)

            # Save final report
            report = {
                "static_baseline": {
                    "metrics": static_metrics,
                    "timing": static_timing
                },
                "dynamic_router": {
                    "metrics": dynamic_metrics,
                    "timing": dynamic_timing
                },
                "comparison": comparison
            }

            report_path = self.output_dir / "full_pipeline_report.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)

            assert report_path.exists(), "Final report file was not created"

            logger.info("End-to-end pipeline integration test PASSED.")
            logger.info(f"Report saved to: {report_path}")

        except Exception as e:
            logger.error(f"End-to-end pipeline integration test FAILED: {e}")
            pytest.fail(f"Full pipeline integration failed: {str(e)}")

    def test_error_handling_missing_data(self):
        """
        Test that the pipeline fails gracefully when prerequisite data is missing.
        """
        logger.info("Testing error handling for missing data...")

        # Temporarily rename a prerequisite file
        prereq_file = PROJECT_ROOT / "data/processed/clustering_report.json"
        backup_file = PROJECT_ROOT / "data/processed/clustering_report.json.bak"

        if prereq_file.exists():
            prereq_file.rename(backup_file)

        try:
            with pytest.raises(FileNotFoundError) as exc_info:
                run_static_baseline(subset_size=1, output_dir=str(self.output_dir))
            
            assert "clustering_report.json" in str(exc_info.value), \
                "Error message should mention the missing file"
            
            logger.info("Error handling test PASSED: Pipeline correctly failed on missing data.")

        finally:
            # Restore the file
            if backup_file.exists():
                backup_file.rename(prereq_file)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])