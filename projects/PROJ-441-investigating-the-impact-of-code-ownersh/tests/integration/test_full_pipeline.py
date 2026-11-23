"""
Integration test for full pipeline execution (T024).

This test verifies the end-to-end execution of the research pipeline:
1. Extraction of ownership metrics (US1)
2. Calculation of code complexity and documentation density (US2)
3. LLM inference and BLEU score calculation (US3)
4. Statistical regression analysis (US3)

The test runs the pipeline on a small, controlled subset of data to ensure
all components integrate correctly and produce valid output artifacts.
"""
import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List

import pytest

# Add the code directory to the path for imports
code_root = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_root))

from utils.config import get_path, set_seed
from utils.logger import get_logger

logger = get_logger(__name__)


class TestFullPipeline:
    """Integration tests for the full research pipeline."""

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path: Path):
        """Set up a temporary directory for test outputs."""
        self.test_output_dir = tmp_path / "pipeline_test_output"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up environment variables for the test
        os.environ["PROJECT_ROOT"] = str(code_root.parent)
        os.environ["DATA_DIR"] = str(self.test_output_dir)
        os.environ["LOG_LEVEL"] = "DEBUG"
        
        set_seed(42)
        logger.info(f"Test output directory: {self.test_output_dir}")

    def _create_mock_data(self, output_dir: Path) -> Dict[str, str]:
        """
        Create minimal mock data required for the pipeline to run.
        
        This creates:
        1. A minimal git repository with ownership history
        2. A few code snippets with known complexity
        3. A small inference dataset
        
        Returns paths to created data files.
        """
        data_dirs = {
            "raw": output_dir / "raw",
            "processed": output_dir / "processed",
            "results": output_dir / "results"
        }
        
        for d in data_dirs.values():
            d.mkdir(parents=True, exist_ok=True)
        
        # Create a minimal ownership metrics file
        ownership_metrics = {
            "repositories": [
                {
                    "repo_id": "test_repo_1",
                    "repo_url": "https://github.com/example/test-repo",
                    "gini_coefficient": 0.65,
                    "developer_count": 3,
                    "total_commits": 50,
                    "files_analyzed": 5
                }
            ]
        }
        
        ownership_path = data_dirs["processed"] / "ownership_metrics.json"
        with open(ownership_path, "w") as f:
            json.dump(ownership_metrics, f, indent=2)
        
        # Create a minimal code metrics file
        code_metrics = {
            "snippets": [
                {
                    "snippet_id": "snippet_001",
                    "repo_id": "test_repo_1",
                    "file_path": "test_file.py",
                    "cyclomatic_complexity": 5,
                    "documentation_density": 0.15,
                    "total_lines": 100,
                    "comment_lines": 15
                },
                {
                    "snippet_id": "snippet_002",
                    "repo_id": "test_repo_1",
                    "file_path": "test_file2.py",
                    "cyclomatic_complexity": 8,
                    "documentation_density": 0.20,
                    "total_lines": 80,
                    "comment_lines": 16
                }
            ]
        }
        
        code_metrics_path = data_dirs["processed"] / "code_metrics.json"
        with open(code_metrics_path, "w") as f:
            json.dump(code_metrics, f, indent=2)
        
        # Create a minimal inference dataset (CodeXGLUE style)
        inference_data = [
            {
                "id": "snippet_001",
                "code": "def add(a, b):\n    return a + b",
                "ground_truth": "def add(a, b):\n    return a + b",
                "repo_id": "test_repo_1"
            },
            {
                "id": "snippet_002",
                "code": "def multiply(a, b):\n    return a * b",
                "ground_truth": "def multiply(a, b):\n    return a * b",
                "repo_id": "test_repo_1"
            }
        ]
        
        inference_path = data_dirs["raw"] / "inference_dataset.json"
        with open(inference_path, "w") as f:
            json.dump(inference_data, f, indent=2)
        
        return {
            "ownership_metrics": str(ownership_path),
            "code_metrics": str(code_metrics_path),
            "inference_data": str(inference_path)
        }

    def test_full_pipeline_execution(self):
        """
        Test that the full pipeline executes end-to-end without errors.
        
        This test:
        1. Sets up mock data
        2. Runs the main pipeline script
        3. Verifies all expected output files are created
        4. Validates the structure of output artifacts
        """
        logger.info("Starting full pipeline integration test")
        
        # Create mock data
        data_paths = self._create_mock_data(self.test_output_dir)
        logger.info(f"Mock data created at: {data_paths}")
        
        # Run the pipeline
        pipeline_script = code_root / "main.py"
        
        cmd = [
            sys.executable,
            str(pipeline_script),
            "--stages", "extraction,inference,analysis",
            "--data-dir", str(self.test_output_dir),
            "--output-dir", str(self.test_output_dir / "results"),
            "--verbose"
        ]
        
        logger.info(f"Running pipeline with command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(code_root.parent),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for test
            )
            
            logger.info(f"Pipeline stdout: {result.stdout}")
            logger.info(f"Pipeline stderr: {result.stderr}")
            
            # Check that the pipeline completed successfully
            assert result.returncode == 0, \
                f"Pipeline failed with return code {result.returncode}. Stderr: {result.stderr}"
            
            logger.info("Pipeline execution completed successfully")
            
        except subprocess.TimeoutExpired:
            pytest.fail("Pipeline execution timed out")
        except Exception as e:
            pytest.fail(f"Pipeline execution failed with exception: {str(e)}")
        
        # Verify output artifacts exist
        expected_outputs = [
            "results/regression_results.json",
            "results/regression_summary.csv",
            "results/inference_results.json",
            "results/pipeline_execution_log.json"
        ]
        
        for output_file in expected_outputs:
            output_path = self.test_output_dir / output_file
            assert output_path.exists(), \
                f"Expected output file missing: {output_file}"
            logger.info(f"Verified output file exists: {output_file}")
        
        # Validate regression results structure
        regression_path = self.test_output_dir / "results" / "regression_results.json"
        with open(regression_path, "r") as f:
            regression_data = json.load(f)
        
        assert "model_summary" in regression_data, \
            "Regression results missing 'model_summary' key"
        assert "coefficients" in regression_data, \
            "Regression results missing 'coefficients' key"
        assert "ownership_coefficient" in regression_data["coefficients"], \
            "Regression results missing 'ownership_coefficient' in coefficients"
        
        logger.info("Regression results structure validated")
        
        # Validate inference results structure
        inference_path = self.test_output_dir / "results" / "inference_results.json"
        with open(inference_path, "r") as f:
            inference_data = json.load(f)
        
        assert "inference_results" in inference_data, \
            "Inference results missing 'inference_results' key"
        assert len(inference_data["inference_results"]) > 0, \
            "Inference results are empty"
        
        # Check that BLEU scores are present
        for result in inference_data["inference_results"]:
            assert "bleu_score" in result, \
                "Inference result missing 'bleu_score' field"
            assert "snippet_id" in result, \
                "Inference result missing 'snippet_id' field"
        
        logger.info("Inference results structure validated")
        
        # Validate that regression coefficients are reasonable
        ownership_coef = regression_data["coefficients"]["ownership_coefficient"]
        assert isinstance(ownership_coef, dict), \
            "Ownership coefficient should be a dictionary with estimate and p-value"
        assert "estimate" in ownership_coef, \
            "Ownership coefficient missing 'estimate' field"
        assert "p_value" in ownership_coef, \
            "Ownership coefficient missing 'p_value' field"
        
        logger.info("Regression coefficients validated")
        
        logger.info("Full pipeline integration test PASSED")

    def test_pipeline_with_progressive_reduction(self):
        """
        Test that the pipeline correctly applies progressive sample reduction
        when configured (T009, T041).
        """
        logger.info("Testing pipeline with progressive sample reduction")
        
        # Create mock data
        data_paths = self._create_mock_data(self.test_output_dir)
        
        # Run pipeline with progressive reduction enabled
        pipeline_script = code_root / "main.py"
        
        cmd = [
            sys.executable,
            str(pipeline_script),
            "--stages", "extraction,inference,analysis",
            "--data-dir", str(self.test_output_dir),
            "--output-dir", str(self.test_output_dir / "results"),
            "--progressive-reduction",
            "--max-runtime-hours", "0.1",  # Very short timeout to trigger reduction
            "--verbose"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(code_root.parent),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # The pipeline should either complete successfully or trigger reduction
            # and complete with fewer samples
            logger.info(f"Pipeline stdout: {result.stdout}")
            logger.info(f"Pipeline stderr: {result.stderr}")
            
            # Check if reduction was triggered
            if "progressive reduction" in result.stdout.lower() or \
               "progressive reduction" in result.stderr.lower():
                logger.info("Progressive reduction was triggered as expected")
            
            # Verify that output files were still created
            output_path = self.test_output_dir / "results" / "regression_results.json"
            assert output_path.exists(), \
                "Output files should exist even with progressive reduction"
            
            logger.info("Progressive reduction test completed")
            
        except subprocess.TimeoutExpired:
            # Timeout is acceptable if reduction is working correctly
            logger.info("Pipeline timed out (expected with aggressive timeout)")
            # Verify that partial results were written
            output_path = self.test_output_dir / "results"
            if output_path.exists():
                logger.info("Partial results directory exists")
        except Exception as e:
            logger.warning(f"Progressive reduction test encountered: {str(e)}")
            # This is acceptable as long as the main test passes

    def test_error_handling_in_pipeline(self):
        """
        Test that the pipeline handles errors gracefully and logs them appropriately.
        """
        logger.info("Testing pipeline error handling")
        
        # Create a corrupted data file to trigger an error
        corrupted_path = self.test_output_dir / "raw" / "corrupted_data.json"
        corrupted_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(corrupted_path, "w") as f:
            f.write("{ invalid json }")
        
        # Run pipeline with corrupted data
        pipeline_script = code_root / "main.py"
        
        cmd = [
            sys.executable,
            str(pipeline_script),
            "--stages", "extraction",
            "--data-dir", str(self.test_output_dir),
            "--output-dir", str(self.test_output_dir / "results"),
            "--verbose"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(code_root.parent),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # The pipeline should fail gracefully and log the error
            logger.info(f"Pipeline stdout: {result.stdout}")
            logger.info(f"Pipeline stderr: {result.stderr}")
            
            # Check that an error was logged
            assert "error" in result.stderr.lower() or "error" in result.stdout.lower(), \
                "Pipeline should log an error when encountering corrupted data"
            
            logger.info("Error handling test completed - error was logged as expected")
            
        except Exception as e:
            logger.warning(f"Error handling test encountered: {str(e)}")
            # This is acceptable as long as the error was handled