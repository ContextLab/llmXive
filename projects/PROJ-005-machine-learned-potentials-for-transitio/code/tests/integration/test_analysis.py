"""
Integration test for the analysis pipeline (User Story 3).

This test verifies the end-to-end execution of the analysis pipeline,
ensuring that:
1. Feature importance analysis runs and produces ranked descriptors.
2. Statistical testing (Welch's t-test) runs and produces p-values.
3. All expected output files are generated with valid content.

Prerequisites:
- US2 must be complete (predictions.parquet, residuals.parquet, metrics.json exist).
- T034 (statistics.py) must be implemented.
- T031 (feature_importance.py) must be implemented.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.feature_importance import run_feature_importance_analysis, main as fi_main
from src.analysis.statistics import run_statistical_analysis, main as stats_main
from src.analysis.descriptor_ranking import run_descriptor_ranking, main as desc_main


class TestAnalysisPipelineIntegration:
    """Integration tests for the US3 analysis pipeline."""

    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Ensure required input files exist before running tests."""
        self.data_processed = PROJECT_ROOT / "code" / "data" / "processed"
        self.data_results = PROJECT_ROOT / "code" / "data" / "results"
        
        # Ensure directories exist
        self.data_results.mkdir(parents=True, exist_ok=True)
        
        # Check for required US2 outputs
        assert (self.data_processed / "residuals.parquet").exists(), \
            "Integration test failed: residuals.parquet missing. Run US2 first."
        assert (self.data_processed / "predictions.parquet").exists(), \
            "Integration test failed: predictions.parquet missing. Run US2 first."
        
        yield

    def test_feature_importance_pipeline(self):
        """
        Test the full feature importance pipeline:
        1. Run feature importance analysis (Integrated Gradients + SHAP).
        2. Verify output files exist.
        3. Verify output content is valid.
        """
        # Run the feature importance analysis
        # This calls the main entry point which orchestrates the full pipeline
        try:
            fi_main()
        except Exception as e:
            pytest.fail(f"Feature importance analysis failed: {e}")

        # Verify output files exist
        feature_importance_csv = self.data_results / "feature_importance.csv"
        top_descriptors_json = self.data_results / "top_descriptors_subset.json"
        
        assert feature_importance_csv.exists(), \
            "feature_importance.csv was not generated"
        assert top_descriptors_json.exists(), \
            "top_descriptors_subset.json was not generated"

        # Verify CSV content
        df = pd.read_csv(feature_importance_csv)
        assert len(df) > 0, "feature_importance.csv is empty"
        assert "descriptor" in df.columns, "feature_importance.csv missing 'descriptor' column"
        assert "variance_explained" in df.columns, "feature_importance.csv missing 'variance_explained' column"
        
        # Check that variance_explained values are numeric and positive
        assert df["variance_explained"].dtype in [np.float64, np.float32], \
            "variance_explained column is not numeric"
        assert all(df["variance_explained"] > 0), \
            "variance_explained values must be positive"

        # Verify JSON content
        with open(top_descriptors_json, 'r') as f:
            data = json.load(f)
        
        assert "descriptors" in data, "top_descriptors_subset.json missing 'descriptors'"
        assert "cumulative_variance" in data, "top_descriptors_subset.json missing 'cumulative_variance'"
        assert "total_variance_explained" in data, "top_descriptors_subset.json missing 'total_variance_explained'"
        
        assert isinstance(data["descriptors"], list), "descriptors must be a list"
        assert len(data["descriptors"]) > 0, "descriptors list is empty"
        assert isinstance(data["cumulative_variance"], (int, float)), \
            "cumulative_variance must be numeric"
        assert data["cumulative_variance"] >= 0.60, \
            f"Cumulative variance {data['cumulative_variance']} is below threshold 0.60"

    def test_statistical_testing_pipeline(self):
        """
        Test the full statistical testing pipeline:
        1. Run Welch's t-test on error residuals by ligand class.
        2. Verify output files exist.
        3. Verify output content is valid.
        """
        # Run the statistical analysis
        try:
            stats_main()
        except Exception as e:
            pytest.fail(f"Statistical analysis failed: {e}")

        # Verify output files exist
        statistical_tests_json = self.data_results / "statistical_tests.json"
        deviation_log = self.data_results / "deviation_log.md"
        
        assert statistical_tests_json.exists(), \
            "statistical_tests.json was not generated"
        assert deviation_log.exists(), \
            "deviation_log.md was not generated"

        # Verify JSON content
        with open(statistical_tests_json, 'r') as f:
            data = json.load(f)
        
        assert "test_type" in data, "statistical_tests.json missing 'test_type'"
        assert data["test_type"] == "welch_ttest", \
            f"Expected 'welch_ttest', got '{data['test_type']}'"
        
        assert "results" in data, "statistical_tests.json missing 'results'"
        results = data["results"]
        
        assert "group13" in results, "Missing results for Group 13 ligands"
        assert "conventional" in results, "Missing results for Conventional ligands"
        
        # Check that Group 13 results have required fields
        group13 = results["group13"]
        assert "mean_error" in group13, "group13 missing 'mean_error'"
        assert "std_error" in group13, "group13 missing 'std_error'"
        assert "n_samples" in group13, "group13 missing 'n_samples'"
        assert "t_statistic" in group13, "group13 missing 't_statistic'"
        assert "p_value" in group13, "group13 missing 'p_value'"
        
        # Verify numeric types
        assert isinstance(group13["p_value"], (int, float)), \
            "p_value must be numeric"
        assert 0 <= group13["p_value"] <= 1, \
            "p_value must be between 0 and 1"

        # Verify deviation log content
        with open(deviation_log, 'r') as f:
            log_content = f.read()
        
        assert "Welch's t-test" in log_content, \
            "deviation_log.md should mention Welch's t-test"
        assert "FR-006" in log_content, \
            "deviation_log.md should reference FR-006 deviation"

    def test_end_to_end_analysis_order(self):
        """
        Test that the full analysis pipeline runs in the correct order:
        1. Feature importance
        2. Descriptor ranking
        3. Statistical testing
        
        This ensures dependencies are respected and all outputs are generated.
        """
        # Run feature importance first
        try:
            fi_main()
        except Exception as e:
            pytest.fail(f"Feature importance analysis failed: {e}")

        # Run descriptor ranking (depends on feature importance output)
        try:
            desc_main()
        except Exception as e:
            pytest.fail(f"Descriptor ranking failed: {e}")

        # Run statistical testing (independent but part of the pipeline)
        try:
            stats_main()
        except Exception as e:
            pytest.fail(f"Statistical testing failed: {e}")

        # Verify all expected outputs exist
        expected_files = [
            "feature_importance.csv",
            "top_descriptors_subset.json",
            "statistical_tests.json",
            "deviation_log.md"
        ]
        
        for filename in expected_files:
            filepath = self.data_results / filename
            assert filepath.exists(), f"Expected output file {filename} was not generated"

    def test_analysis_consistency_with_metrics(self):
        """
        Verify that analysis results are consistent with previously computed metrics.
        Specifically, check that the statistical test results align with the
        error distributions in residuals.parquet.
        """
        # Load residuals
        residuals_path = self.data_processed / "residuals.parquet"
        residuals = pd.read_parquet(residuals_path)
        
        # Load statistical test results
        stats_path = self.data_results / "statistical_tests.json"
        with open(stats_path, 'r') as f:
            stats_data = json.load(f)
        
        # Verify the test was performed on the correct groups
        assert "ligand_class" in residuals.columns, \
            "residuals.parquet must have 'ligand_class' column"
        
        # Check that the groups in the test match the data
        unique_classes = set(residuals["ligand_class"].unique())
        test_groups = set(stats_data["results"].keys())
        
        # At least one group should match (Group 13 or Conventional)
        assert len(unique_classes.intersection(test_groups)) > 0, \
            f"Test groups {test_groups} do not match data classes {unique_classes}"

    def test_analysis_handles_data_scarcity(self):
        """
        Verify that the analysis pipeline handles data scarcity gracefully.
        If scarcity flag is set, the pipeline should still run but log warnings.
        """
        scarcity_flag_path = self.data_processed / "data_scarcity_flag.json"
        
        if scarcity_flag_path.exists():
            # If scarcity flag exists, verify the pipeline still ran
            stats_path = self.data_results / "statistical_tests.json"
            assert stats_path.exists(), \
                "Analysis should run even with data scarcity flag"
            
            # Verify the statistical test still produced results
            with open(stats_path, 'r') as f:
                stats_data = json.load(f)
            
            assert "results" in stats_data, \
                "Statistical results should exist despite scarcity"
            assert "group13" in stats_data["results"] or "conventional" in stats_data["results"], \
                "At least one group should have results"

    def test_no_synthetic_data_used(self):
        """
        Verify that the analysis is using real data from residuals.parquet
        and not synthetic/fake data.
        """
        residuals_path = self.data_processed / "residuals.parquet"
        residuals = pd.read_parquet(residuals_path)
        
        # Check for signs of synthetic data
        # Real data should have varied error residuals, not all zeros or identical values
        assert len(residuals) > 0, "Residuals dataset is empty"
        
        error_column = "error_ml_dft"
        assert error_column in residuals.columns, \
            f"Missing {error_column} column in residuals"
        
        # Check for variance in errors (real data should have variation)
        error_std = residuals[error_column].std()
        assert error_std > 0.001, \
            "Error residuals have near-zero variance, suggesting synthetic data"
        
        # Check that errors are not all identical
        assert residuals[error_column].nunique() > 1, \
            "All error values are identical, suggesting synthetic data"