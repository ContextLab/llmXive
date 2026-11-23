"""
Contract test for model output metrics.

This test validates that the model output files (predictions.csv and 
statistical_results.json) conform to the expected schema and contain
the required fields as defined in the project specification.

It verifies:
1. predictions.csv schema: [fold, smiles, true_value, predicted_value, model_type]
2. statistical_results.json schema: Contains per-model metrics and t-test results
3. Data types and non-null constraints for critical fields
"""
import pytest
import pandas as pd
import json
import os
from pathlib import Path
import numpy as np

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent.parent
PREDICTIONS_PATH = PROJECT_ROOT / "data" / "processed" / "predictions.csv"
STAT_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "statistical_results.json"

# Expected schema for predictions.csv
EXPECTED_PREDICTIONS_COLUMNS = {
    "fold",
    "smiles",
    "true_value",
    "predicted_value",
    "model_type"
}

# Expected schema for statistical_results.json
EXPECTED_STAT_RESULTS_KEYS = {
    "gnn_metrics",
    "rf_metrics",
    "lr_metrics",
    "t_test_results"
}

# Required metric keys within each model's metrics dict
REQUIRED_METRIC_KEYS = {
    "r2",
    "mae",
    "rmse",
    "std_r2",
    "std_mae",
    "std_rmse"
}

# Required keys within t_test_results
REQUIRED_TTEST_KEYS = {
    "gnn_vs_rf",
    "gnn_vs_lr"
}

# Required keys within each t-test comparison
REQUIRED_COMPARISON_KEYS = {
    "p_value",
    "statistic",
    "significant"
}


class TestPredictionsSchema:
    """Contract tests for predictions.csv output schema."""

    @pytest.fixture(scope="class")
    def predictions_df(self):
        """Load predictions data, skipping if file doesn't exist yet."""
        if not PREDICTIONS_PATH.exists():
            pytest.skip(f"Predictions file not found at {PREDICTIONS_PATH}. "
                        "Run training pipeline first.")
        return pd.read_csv(PREDICTIONS_PATH)

    def test_predictions_file_exists(self):
        """Verify predictions.csv exists."""
        assert PREDICTIONS_PATH.exists(), (
            f"Predictions file {PREDICTIONS_PATH} does not exist. "
            "Training pipeline must be run first."
        )

    def test_predictions_has_required_columns(self, predictions_df):
        """Verify all required columns are present."""
        actual_columns = set(predictions_df.columns)
        missing_columns = EXPECTED_PREDICTIONS_COLUMNS - actual_columns
        assert not missing_columns, (
            f"Missing required columns in predictions.csv: {missing_columns}. "
            f"Found: {actual_columns}"
        )

    def test_predictions_no_null_true_values(self, predictions_df):
        """Verify true_value column has no nulls."""
        null_count = predictions_df["true_value"].isnull().sum()
        assert null_count == 0, (
            f"Found {null_count} null values in 'true_value' column. "
            "All permeability values must be present."
        )

    def test_predictions_no_null_predicted_values(self, predictions_df):
        """Verify predicted_value column has no nulls."""
        null_count = predictions_df["predicted_value"].isnull().sum()
        assert null_count == 0, (
            f"Found {null_count} null values in 'predicted_value' column."
        )

    def test_predictions_no_null_smiles(self, predictions_df):
        """Verify smiles column has no nulls."""
        null_count = predictions_df["smiles"].isnull().sum()
        assert null_count == 0, (
            f"Found {null_count} null values in 'smiles' column."
        )

    def test_predictions_model_types_valid(self, predictions_df):
        """Verify model_type contains only expected values."""
        valid_types = {"gcn", "random_forest", "linear_regression"}
        actual_types = set(predictions_df["model_type"].str.lower())
        invalid_types = actual_types - valid_types
        assert not invalid_types, (
            f"Invalid model types found: {invalid_types}. "
            f"Valid types: {valid_types}"
        )

    def test_predictions_fold_values_valid(self, predictions_df):
        """Verify fold column contains valid integer values."""
        assert predictions_df["fold"].dtype in [np.int64, np.int32, int], (
            f"Fold column must be integer type, got {predictions_df['fold'].dtype}"
        )
        assert predictions_df["fold"].min() >= 0, "Fold values must be non-negative"


class TestStatisticalResultsSchema:
    """Contract tests for statistical_results.json output schema."""

    @pytest.fixture(scope="class")
    def stat_results(self):
        """Load statistical results, skipping if file doesn't exist."""
        if not STAT_RESULTS_PATH.exists():
            pytest.skip(f"Statistical results file not found at {STAT_RESULTS_PATH}. "
                        "Run statistical analysis first.")
        with open(STAT_RESULTS_PATH, "r") as f:
            return json.load(f)

    def test_stat_results_file_exists(self):
        """Verify statistical_results.json exists."""
        assert STAT_RESULTS_PATH.exists(), (
            f"Statistical results file {STAT_RESULTS_PATH} does not exist. "
            "Statistical analysis must be run first."
        )

    def test_stat_results_has_required_keys(self, stat_results):
        """Verify all required top-level keys are present."""
        missing_keys = EXPECTED_STAT_RESULTS_KEYS - set(stat_results.keys())
        assert not missing_keys, (
            f"Missing required keys in statistical_results.json: {missing_keys}. "
            f"Found: {set(stat_results.keys())}"
        )

    def test_gnn_metrics_structure(self, stat_results):
        """Verify GNN metrics have required structure."""
        gnn_metrics = stat_results["gnn_metrics"]
        missing_keys = REQUIRED_METRIC_KEYS - set(gnn_metrics.keys())
        assert not missing_keys, (
            f"Missing metric keys in gnn_metrics: {missing_keys}. "
            f"Found: {set(gnn_metrics.keys())}"
        )

    def test_rf_metrics_structure(self, stat_results):
        """Verify RF metrics have required structure."""
        rf_metrics = stat_results["rf_metrics"]
        missing_keys = REQUIRED_METRIC_KEYS - set(rf_metrics.keys())
        assert not missing_keys, (
            f"Missing metric keys in rf_metrics: {missing_keys}. "
            f"Found: {set(rf_metrics.keys())}"
        )

    def test_lr_metrics_structure(self, stat_results):
        """Verify LR metrics have required structure."""
        lr_metrics = stat_results["lr_metrics"]
        missing_keys = REQUIRED_METRIC_KEYS - set(lr_metrics.keys())
        assert not missing_keys, (
            f"Missing metric keys in lr_metrics: {missing_keys}. "
            f"Found: {set(lr_metrics.keys())}"
        )

    def test_t_test_results_structure(self, stat_results):
        """Verify t-test results have required structure."""
        ttest_results = stat_results["t_test_results"]
        missing_keys = REQUIRED_TTEST_KEYS - set(ttest_results.keys())
        assert not missing_keys, (
            f"Missing t-test comparison keys: {missing_keys}. "
            f"Found: {set(ttest_results.keys())}"
        )

    def test_t_test_comparison_structure(self, stat_results):
        """Verify each t-test comparison has required fields."""
        ttest_results = stat_results["t_test_results"]
        for comparison_name in REQUIRED_TTEST_KEYS:
            comparison = ttest_results[comparison_name]
            missing_keys = REQUIRED_COMPARISON_KEYS - set(comparison.keys())
            assert not missing_keys, (
                f"Missing keys in {comparison_name}: {missing_keys}. "
                f"Found: {set(comparison.keys())}"
            )

    def test_metric_values_are_numeric(self, stat_results):
        """Verify all metric values are numeric."""
        for model_key in ["gnn_metrics", "rf_metrics", "lr_metrics"]:
            metrics = stat_results[model_key]
            for metric_name, value in metrics.items():
                assert isinstance(value, (int, float, np.number)), (
                    f"Metric {model_key}.{metric_name} must be numeric, got {type(value)}"
                )

    def test_p_value_is_valid(self, stat_results):
        """Verify p-values are valid probabilities."""
        ttest_results = stat_results["t_test_results"]
        for comparison_name in REQUIRED_TTEST_KEYS:
            p_value = ttest_results[comparison_name]["p_value"]
            assert 0 <= p_value <= 1, (
                f"p-value for {comparison_name} must be between 0 and 1, got {p_value}"
            )

    def test_statistic_is_numeric(self, stat_results):
        """Verify t-test statistics are numeric."""
        ttest_results = stat_results["t_test_results"]
        for comparison_name in REQUIRED_TTEST_KEYS:
            statistic = ttest_results[comparison_name]["statistic"]
            assert isinstance(statistic, (int, float, np.number)), (
                f"Statistic for {comparison_name} must be numeric, got {type(statistic)}"
            )

    def test_significant_is_boolean(self, stat_results):
        """Verify significant flag is boolean."""
        ttest_results = stat_results["t_test_results"]
        for comparison_name in REQUIRED_TTEST_KEYS:
            significant = ttest_results[comparison_name]["significant"]
            assert isinstance(significant, bool), (
                f"significant flag for {comparison_name} must be boolean, got {type(significant)}"
            )


class TestIntegration:
    """Integration tests validating consistency between predictions and stats."""

    @pytest.fixture(scope="class")
    def predictions_df(self):
        if not PREDICTIONS_PATH.exists():
            pytest.skip("Predictions file not found.")
        return pd.read_csv(PREDICTIONS_PATH)

    @pytest.fixture(scope="class")
    def stat_results(self):
        if not STAT_RESULTS_PATH.exists():
            pytest.skip("Statistical results file not found.")
        with open(STAT_RESULTS_PATH, "r") as f:
            return json.load(f)

    def test_predictions_count_matches_folds(self, predictions_df):
        """Verify predictions are generated for all folds."""
        unique_folds = predictions_df["fold"].nunique()
        assert unique_folds == 5, (
            f"Expected 5 folds in predictions, got {unique_folds}. "
            "Scaffold CV should generate 5 folds."
        )

    def test_all_models_have_predictions(self, predictions_df):
        """Verify all three models have predictions."""
        model_counts = predictions_df["model_type"].value_counts()
        expected_models = ["gcn", "random_forest", "linear_regression"]
        for model in expected_models:
            assert model in model_counts.index, (
                f"Model {model} has no predictions. Found: {list(model_counts.index)}"
            )
            assert model_counts[model] > 0, (
                f"Model {model} has zero predictions."
            )