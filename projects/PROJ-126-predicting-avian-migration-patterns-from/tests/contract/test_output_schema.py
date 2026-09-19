"""
Contract test for model output schema (US2).

This test verifies that the model training pipeline produces outputs
that strictly adhere to the expected schema defined in the specification.

It checks:
1. The structure of the metrics JSON file (data/processed/metrics.json)
2. The structure of the SHAP summary plot existence (data/outputs/shap_summary.png)
3. The structure of the permutation importance CSV (data/outputs/permutation_importance.csv)

Run this test AFTER the model training pipeline (T019-T024) has completed.
"""

import json
import os
import pandas as pd
import pytest
from pathlib import Path

# Project root is parent of 'tests'
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Expected file paths based on task descriptions
METRICS_FILE = DATA_PROCESSED_DIR / "metrics.json"
SHAP_PLOT_FILE = DATA_OUTPUTS_DIR / "shap_summary.png"
PERMUTATION_FILE = DATA_OUTPUTS_DIR / "permutation_importance.csv"
FIRST_ARRIVAL_FILE = DATA_PROCESSED_DIR / "first_arrival_sweep.csv"

class TestModelOutputSchema:
    """Contract tests for US2 model output artifacts."""

    def test_metrics_file_exists_and_is_valid_json(self):
        """
        Contract: data/processed/metrics.json must exist and be valid JSON.
        """
        assert METRICS_FILE.exists(), f"Metrics file not found at {METRICS_FILE}"
        
        try:
            with open(METRICS_FILE, 'r') as f:
                metrics = json.load(f)
            assert isinstance(metrics, dict), "Metrics file must contain a JSON object (dict)."
        except json.JSONDecodeError as e:
            pytest.fail(f"Metrics file is not valid JSON: {e}")

    def test_metrics_schema_structure(self):
        """
        Contract: Metrics JSON must contain specific keys required by US2/US3.
        
        Required keys based on T022 (RMSE, Correlation) and T029 (Bootstrap CIs).
        """
        assert METRICS_FILE.exists(), f"Metrics file not found at {METRICS_FILE}"
        
        with open(METRICS_FILE, 'r') as f:
            metrics = json.load(f)
        
        # Check for core model performance metrics (T022)
        required_core_keys = ['rmse', 'pearson_correlation', 'naive_baseline_rmse']
        for key in required_core_keys:
            assert key in metrics, f"Missing required metric key: '{key}'"
            assert isinstance(metrics[key], (int, float)), f"Metric '{key}' must be numeric."
        
        # Check for bootstrap results (T029) - these might be nested or top-level
        # Spec says: "Append results to data/processed/metrics.json with keys: ci_temp_vs_ndvi, ci_combined_vs_temp, p_value_combined_vs_temp"
        # We check for these specifically as top-level keys or within a 'bootstrap' section if refactored later.
        # Based on T029 description, they are direct keys.
        required_bootstrap_keys = ['ci_temp_vs_ndvi', 'ci_combined_vs_temp', 'p_value_combined_vs_temp']
        
        # Check if they exist at top level or if we have a 'bootstrap' section
        has_bootstrap_keys = all(k in metrics for k in required_bootstrap_keys)
        has_bootstrap_section = 'bootstrap' in metrics and all(k in metrics['bootstrap'] for k in required_bootstrap_keys)
        
        assert has_bootstrap_keys or has_bootstrap_section, (
            f"Metrics file must contain bootstrap results keys: {required_bootstrap_keys}. "
            f"Found keys: {list(metrics.keys())}"
        )

    def test_permutation_importance_schema(self):
        """
        Contract: data/outputs/permutation_importance.csv must exist and have correct columns.
        
        Based on T024: Verify feature rankings are robust.
        Expected columns: feature, score (or similar), importance.
        """
        assert PERMUTATION_FILE.exists(), f"Permutation importance file not found at {PERMUTATION_FILE}"
        
        df = pd.read_csv(PERMUTATION_FILE)
        
        # Check for essential columns
        # The spec doesn't explicitly name columns, but standard practice is 'feature' and 'importance'
        # We assert at least one column related to features and one to importance exists.
        has_feature_col = any('feature' in col.lower() for col in df.columns)
        has_importance_col = any('importance' in col.lower() for col in df.columns)
        
        assert has_feature_col, f"Permutation CSV must have a 'feature' column. Columns: {df.columns}"
        assert has_importance_col, f"Permutation CSV must have an 'importance' column. Columns: {df.columns}"
        
        # Ensure it's not empty
        assert len(df) > 0, "Permutation importance CSV must contain data rows."

    def test_shap_plot_exists(self):
        """
        Contract: data/outputs/shap_summary.png must exist.
        
        Based on T023: Generate beeswarm summary plots.
        """
        assert SHAP_PLOT_FILE.exists(), f"SHAP summary plot not found at {SHAP_PLOT_FILE}"
        
        # Basic validation that it's not a 0-byte file
        file_size = SHAP_PLOT_FILE.stat().st_size
        assert file_size > 0, f"SHAP summary plot is empty (0 bytes)."

    def test_input_data_consistency(self):
        """
        Contract: The model output should be consistent with the input data schema.
        
        Checks that the first_arrival_sweep.csv (input to model) has the expected columns
        referenced in T014/T015, ensuring the pipeline is coherent.
        """
        assert FIRST_ARRIVAL_FILE.exists(), f"First arrival sweep file not found at {FIRST_ARRIVAL_FILE}"
        
        df = pd.read_csv(FIRST_ARRIVAL_FILE)
        
        # Expected columns from T014: grid_id, week, arrival_date_3, arrival_date_5, arrival_date_10, status
        required_columns = ['grid_id', 'week', 'arrival_date_3', 'arrival_date_5', 'arrival_date_10', 'status']
        
        for col in required_columns:
            assert col in df.columns, f"First arrival sweep CSV missing required column: '{col}'"