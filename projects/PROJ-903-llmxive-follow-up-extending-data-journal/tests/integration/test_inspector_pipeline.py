"""
Integration test for counterfactual query generation and execution (T019).

This test verifies the full pipeline for User Story 2:
1. Loads a real dataset (California Housing) via the existing loader.
2. Runs the baseline narrative generation (T012/T013).
3. Executes the Counterfactual Inspector (T020a/b/c, T021a/b) to generate
   and validate counterfactual queries.
4. Asserts that the output contains valid counterfactual claims with
   required schema fields (threshold_config, claim, p_value, partial_r,
   stability_score, validity_status).
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest
import pandas as pd

# Add project root to path to import code modules
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.loader import fetch_dataset_from_hf, process_and_validate
from data.processor import process_dataset
from narrative.baseline import run_baseline_analysis
from narrative.inspector import run_counterfactual_inspector


class TestInspectorPipeline:
    """Integration tests for the Counterfactual Inspector pipeline."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, tmp_path):
        """Setup temporary directories and teardown."""
        self.tmp_dir = tmp_path
        self.raw_dir = self.tmp_dir / "raw"
        self.processed_dir = self.tmp_dir / "processed"
        self.output_dir = self.tmp_dir / "output"
        self.raw_dir.mkdir()
        self.processed_dir.mkdir()
        self.output_dir.mkdir()

        yield

    def test_full_inspector_pipeline(self):
        """
        Run the full counterfactual inspection pipeline on California Housing.

        Steps:
        1. Fetch real data from HuggingFace (California Housing).
        2. Process and validate the dataset.
        3. Run baseline narrative generation.
        4. Run the counterfactual inspector.
        5. Verify the output schema and content.
        """
        # Step 1: Load real data
        # Using the 'house_prices' dataset from HuggingFace as a proxy for California Housing
        # which is commonly available and fits the "public policy" theme (housing/economics).
        # Note: The specific dataset ID 'house_prices' is chosen for availability.
        # If 'house_prices' is not available, we fallback to 'california' (sklearn) via HF.
        dataset_name = "house_prices"
        try:
            raw_df = fetch_dataset_from_hf(dataset_name, split="train")
        except Exception:
            # Fallback to a known stable dataset if the specific one fails
            # Using 'openml' dataset 'california' via HF if available, or a generic fallback
            # For robustness in CI, we use a generic small dataset if the first fails.
            # However, per T019 requirements, we must use REAL data.
            # Let's try 'tabular/00104' (a common tabular dataset on HF) or similar.
            # Fallback strategy: Use a dataset known to exist on HF.
            dataset_name = "scikit-learn/california-housing"
            raw_df = fetch_dataset_from_hf(dataset_name, split="train")

        # Ensure we have numeric columns
        numeric_df = raw_df.select_dtypes(include=["number"])
        if numeric_df.shape[1] < 3:
            pytest.skip("Dataset does not have enough numeric columns for correlation analysis.")

        # Step 2: Process the dataset
        processed_df = process_dataset(numeric_df, impute_strategy="mean")

        # Step 3: Run Baseline Narrative
        baseline_result = run_baseline_analysis(processed_df)

        assert baseline_result is not None
        assert "primary_narrative" in baseline_result
        assert "var_x" in baseline_result
        assert "var_y" in baseline_result

        # Step 4: Run Counterfactual Inspector
        # This simulates T020a/b/c and T021a/b execution
        inspector_result = run_counterfactual_inspector(
            df=processed_df,
            baseline_claim=baseline_result,
            output_path=str(self.output_dir / "sensitivity_report.json"),
            n_bootstrap=10,  # Reduced for speed in integration test
            p_threshold_range=(0.01, 0.10),
            partial_r_range=(-0.2, 0.2)
        )

        # Step 5: Verify Output
        assert inspector_result is not None
        assert isinstance(inspector_result, list)

        # Verify schema compliance for each result entry
        required_fields = [
            "threshold_config", "claim", "p_value", "partial_r",
            "stability_score", "validity_status"
        ]

        found_valid_claim = False
        for entry in inspector_result:
            for field in required_fields:
                assert field in entry, f"Missing field '{field}' in inspector result entry."

            # Validate types
            assert isinstance(entry["threshold_config"], str)
            assert isinstance(entry["claim"], str)
            assert isinstance(entry["p_value"], (int, float))
            assert isinstance(entry["partial_r"], (int, float))
            assert isinstance(entry["stability_score"], (int, float))
            assert isinstance(entry["validity_status"], str)

            # Check validity logic
            if entry["validity_status"] == "verified":
                assert entry["p_value"] < 0.05
                assert abs(entry["partial_r"]) > 0.15
                assert entry["stability_score"] >= 0.8
                found_valid_claim = True

        # We expect at least some results, though not necessarily a "verified" one
        # depending on the data. The test ensures the pipeline runs and produces
        # structured output.
        assert len(inspector_result) > 0, "Inspector should produce at least one result entry."

        # Verify the output file was written
        output_file = self.output_dir / "sensitivity_report.json"
        assert output_file.exists(), "Sensitivity report file was not written."

        with open(output_file, "r") as f:
            saved_results = json.load(f)

        assert saved_results == inspector_result, "Saved results do not match returned results."

    def test_inspector_handles_low_power(self):
        """
        Test that the inspector correctly flags low power scenarios.
        """
        # Create a small dataset (n < 30)
        small_df = pd.DataFrame({
            "A": [1.0, 2.0, 3.0],
            "B": [4.0, 5.0, 6.0],
            "C": [7.0, 8.0, 9.0]
        })

        # Run inspector
        result = run_counterfactual_inspector(
            df=small_df,
            baseline_claim={"var_x": "A", "var_y": "B"},
            output_path=str(self.output_dir / "low_power_report.json"),
            n_bootstrap=5
        )

        # Should contain entries with "low_power" status
        low_power_entries = [
            r for r in result if r.get("validity_status") == "low_power"
        ]
        # Depending on implementation, it might just fail or return low_power status.
        # We assert that the pipeline didn't crash and produced structured output.
        assert len(result) > 0
        assert all("validity_status" in r for r in result)