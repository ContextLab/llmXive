"""
Integration test for the full execution pipeline (US2).

This test verifies the end-to-end flow:
1. Load prompt variants from the processed parquet file.
2. Execute the generated code against HumanEval unit tests.
3. Capture execution outcomes (pass/fail counts, errors, timeouts).
4. Write results to the designated CSV output.
5. Verify the output file exists and contains valid data.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
import pytest
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import Paths
from execution.runner import run_batch_execution, ExecutionError, ExecutionTimeoutError
from execution.write_results import write_results_to_csv
from data.storage import load_variants_from_parquet
from utils.logger import get_logger

logger = get_logger(__name__)


class TestExecutionPipeline:
    """Integration tests for the execution pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test environment."""
        # Ensure output directories exist
        Paths.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        Paths.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        yield
        # Cleanup is handled by pytest temp directories if used

    def _create_mock_variants_parquet(self, sample_size: int = 3) -> Path:
        """
        Create a mock prompt_variants.parquet file with minimal valid data.
        This simulates the output of T018 (storage.py) for integration testing.
        """
        # We use a small subset of HumanEval problems to avoid heavy dependencies
        # in the test environment, but the structure matches the real data model.
        mock_data = []
        for i in range(sample_size):
            problem_id = f"HumanEval/{i}"
            base_prompt = f"def solve_{i}(x): pass"
            for label in ["simple", "moderate", "complex"]:
                mock_data.append({
                    "problem_id": problem_id,
                    "variant_id": f"{problem_id}_{label}",
                    "variant_label": label,
                    "complexity_label": label,
                    "prompt_text": f"{base_prompt} # {label}",
                    "token_count": 50 + (i * 10),
                    "structural_element_count": {"examples": 1, "constraints": 0, "steps": 1},
                    "dependency_depth": 1,
                    "generated_code": f"def solve_{i}(x): return x # {label}",
                    "generation_metadata": {"model": "test", "timestamp": datetime.now().isoformat()}
                })

        df = pd.DataFrame(mock_data)
        output_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"
        df.to_parquet(output_path, index=False)
        logger.info(f"Created mock parquet at {output_path} with {len(df)} rows")
        return output_path

    def test_full_execution_pipeline_writes_results(self):
        """
        Test the full pipeline: load variants -> execute -> write results.

        This verifies:
        1. The runner executes code without crashing.
        2. Outcomes are captured correctly (pass/fail counts).
        3. The output CSV is written to the correct path.
        4. The CSV contains the expected columns.
        """
        # 1. Setup mock data
        variants_path = self._create_mock_variants_parquet(sample_size=2)
        assert variants_path.exists(), "Mock parquet file not created"

        # 2. Load variants
        variants = load_variants_from_parquet(variants_path)
        assert len(variants) > 0, "No variants loaded"
        logger.info(f"Loaded {len(variants)} variants for execution")

        # 3. Execute batch
        # We use a very short timeout to ensure tests run fast in CI
        timeout_seconds = 5
        outcomes = run_batch_execution(variants, timeout_seconds=timeout_seconds)

        assert len(outcomes) == len(variants), "Outcome count mismatch"
        logger.info(f"Execution complete. Generated {len(outcomes)} outcomes.")

        # 4. Write results
        output_csv_path = Paths.RESULTS_DIR / "execution_outcomes.csv"
        write_results_to_csv(outcomes, output_csv_path)

        # 5. Verify output file exists
        assert output_csv_path.exists(), f"Output CSV not written to {output_csv_path}"

        # 6. Verify CSV content
        results_df = pd.read_csv(output_csv_path)
        required_columns = [
            "problem_id", "variant_id", "variant_label", "complexity_label",
            "pass_count", "fail_count", "error_details", "timeout_flag"
        ]

        for col in required_columns:
            assert col in results_df.columns, f"Missing column: {col}"

        assert len(results_df) == len(outcomes), "Result row count mismatch"

        # 7. Verify data integrity
        # Check that pass_count + fail_count >= 0 (sanity check)
        # Note: In a real run, pass_count + fail_count should equal total tests run.
        # For this mock, we just ensure the fields exist and are numeric.
        assert results_df["pass_count"].dtype in ["int64", "float64"], "pass_count must be numeric"
        assert results_df["fail_count"].dtype in ["int64", "float64"], "fail_count must be numeric"

        logger.info(f"Pipeline test passed. Output saved to {output_csv_path}")

    def test_execution_handles_syntax_errors(self):
        """
        Test that the pipeline correctly handles syntax errors in generated code.
        """
        # Create a variant with invalid Python code
        mock_data = [{
            "problem_id": "HumanEval/error_test",
            "variant_id": "HumanEval/error_test_simple",
            "variant_label": "simple",
            "complexity_label": "simple",
            "prompt_text": "def broken():",
            "token_count": 20,
            "structural_element_count": {"examples": 0, "constraints": 0, "steps": 0},
            "dependency_depth": 1,
            "generated_code": "def broken():\n    print 'missing parentheses'", # Syntax error in Py3
            "generation_metadata": {}
        }]

        df = pd.DataFrame(mock_data)
        variants_path = Paths.PROCESSED_DIR / "test_error_variants.parquet"
        df.to_parquet(variants_path, index=False)

        variants = load_variants_from_parquet(variants_path)
        outcomes = run_batch_execution(variants, timeout_seconds=5)

        assert len(outcomes) == 1
        outcome = outcomes[0]

        # The runner should capture the error, not crash
        assert outcome["error_details"] is not None
        assert "SyntaxError" in outcome["error_details"] or outcome["fail_count"] > 0

        # Write results to verify pipeline handles errors gracefully
        output_path = Paths.RESULTS_DIR / "test_error_results.csv"
        write_results_to_csv(outcomes, output_path)
        assert output_path.exists()

    def test_execution_handles_timeout(self):
        """
        Test that the pipeline correctly handles code execution timeouts.
        """
        # Create a variant with infinite loop
        mock_data = [{
            "problem_id": "HumanEval/timeout_test",
            "variant_id": "HumanEval/timeout_test_simple",
            "variant_label": "simple",
            "complexity_label": "simple",
            "prompt_text": "def infinite(): while True: pass",
            "token_count": 30,
            "structural_element_count": {"examples": 0, "constraints": 0, "steps": 0},
            "dependency_depth": 1,
            "generated_code": "def infinite():\n    while True:\n        pass",
            "generation_metadata": {}
        }]

        df = pd.DataFrame(mock_data)
        variants_path = Paths.PROCESSED_DIR / "test_timeout_variants.parquet"
        df.to_parquet(variants_path, index=False)

        variants = load_variants_from_parquet(variants_path)
        
        # Use a very short timeout to trigger the timeout handler quickly
        outcomes = run_batch_execution(variants, timeout_seconds=1)

        assert len(outcomes) == 1
        outcome = outcomes[0]

        assert outcome["timeout_flag"] is True
        assert outcome["error_details"] is not None

        # Verify write
        output_path = Paths.RESULTS_DIR / "test_timeout_results.csv"
        write_results_to_csv(outcomes, output_path)
        assert output_path.exists()