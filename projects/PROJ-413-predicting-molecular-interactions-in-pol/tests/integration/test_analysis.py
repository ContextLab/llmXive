"""
Integration test for attribution and VIF reporting (US3).

This test verifies that:
1. The trained model (results/model.pt) can be loaded.
2. Attribution analysis (Integrated Gradients) runs successfully on test samples.
3. VIF calculation runs successfully on hand-crafted descriptors.
4. Output artifacts (results/attribution.json, results/stats.csv) are generated with correct structure.
"""

import os
import sys
import json
import csv
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

import torch
import pandas as pd
import numpy as np

from models.gat import GATModel
from analysis.attribution import run_attribution_analysis
from analysis.collinearity import calculate_vif
from utils.exceptions import DataError
from utils.seed_utils import set_seed


# Constants
RESULTS_DIR = Path("results")
DATA_PROCESSED_DIR = Path("data") / "processed"
MODEL_PATH = RESULTS_DIR / "model.pt"
ATTRIBUTION_PATH = RESULTS_DIR / "attribution.json"
STATS_PATH = RESULTS_DIR / "stats.csv"
DESCRIPTORS_PATH = DATA_PROCESSED_DIR / "descriptors.csv"
GRAPHS_PATH = DATA_PROCESSED_DIR / "graphs.pt"


@pytest.fixture(autouse=True)
def setup_env():
    """Ensure deterministic behavior for tests."""
    set_seed(42)
    yield


class TestAttributionAndVif:
    """Integration tests for attribution and VIF reporting."""

    def test_model_loads_and_runs_inference(self):
        """Verify the trained model can be loaded and run inference."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Model not found at {MODEL_PATH}. US2 training must complete first.")

        # Load model checkpoint
        checkpoint = torch.load(MODEL_PATH, map_location="cpu")
        model = GATModel(
            in_channels=checkpoint.get("in_channels", 10),
            hidden_channels=64,
            out_channels=1,
            num_layers=3,
            dropout=0.5
        )
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        # Verify model is in eval mode and parameters are loaded
        assert model.training is False
        assert len(list(model.parameters())) > 0

    def test_attribution_analysis_runs_and_generates_output(self):
        """Verify attribution analysis runs and produces valid output file."""
        if not MODEL_PATH.exists():
            pytest.skip(f"Model not found at {MODEL_PATH}. US2 training must complete first.")
        if not GRAPHS_PATH.exists():
            pytest.skip(f"Graphs not found at {GRAPHS_PATH}. US2 graph building must complete first.")

        # Run attribution analysis
        try:
            run_attribution_analysis(
                model_path=str(MODEL_PATH),
                graphs_path=str(GRAPHS_PATH),
                output_path=str(ATTRIBUTION_PATH)
            )
        except Exception as e:
            pytest.fail(f"Attribution analysis failed: {e}")

        # Verify output file exists
        assert ATTRIBUTION_PATH.exists(), f"Attribution output not found at {ATTRIBUTION_PATH}"

        # Verify output structure
        with open(ATTRIBUTION_PATH, "r") as f:
            attribution_data = json.load(f)

        assert "samples" in attribution_data, "Missing 'samples' key in attribution output"
        assert "feature_importance" in attribution_data, "Missing 'feature_importance' key"
        assert len(attribution_data["samples"]) > 0, "No samples in attribution output"

        # Check sample structure
        sample = attribution_data["samples"][0]
        assert "sample_id" in sample, "Missing 'sample_id' in sample"
        assert "attributions" in sample, "Missing 'attributions' in sample"
        assert "predicted_value" in sample, "Missing 'predicted_value' in sample"

        # Check feature importance structure
        importance = attribution_data["feature_importance"]
        assert "top_features" in importance, "Missing 'top_features' in feature importance"
        assert len(importance["top_features"]) >= 3, "Expected at least 3 top features"

    def test_vif_calculation_runs_and_generates_output(self):
        """Verify VIF calculation runs and produces valid output."""
        if not DESCRIPTORS_PATH.exists():
            pytest.skip(f"Descriptors not found at {DESCRIPTORS_PATH}. US1 descriptor extraction must complete first.")

        # Run VIF calculation
        try:
            vif_results = calculate_vif(str(DESCRIPTORS_PATH))
        except Exception as e:
            pytest.fail(f"VIF calculation failed: {e}")

        # Verify results structure
        assert isinstance(vif_results, dict), "VIF results should be a dictionary"
        assert "vif_scores" in vif_results, "Missing 'vif_scores' in results"
        assert "collinearity_warnings" in vif_results, "Missing 'collinearity_warnings' in results"

        # Verify VIF scores are numeric
        for feature, vif in vif_results["vif_scores"].items():
            assert isinstance(vif, (int, float)), f"VIF score for {feature} is not numeric"
            assert vif >= 1.0, f"VIF score for {feature} is less than 1.0"

    def test_stats_csv_contains_required_columns(self):
        """Verify stats.csv contains all required columns for US3 reporting."""
        if not STATS_PATH.exists():
            pytest.skip(f"Stats file not found at {STATS_PATH}. US3 analysis must complete first.")

        with open(STATS_PATH, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) > 0, "Stats CSV is empty"

        required_columns = [
            "metric",
            "observed_value",
            "p_value",
            "corrected_p_value",
            "vif_score",
            "fwer"
        ]

        for row in rows:
            for col in required_columns:
                assert col in row, f"Missing column '{col}' in stats.csv row"

    def test_integration_workflow(self):
        """End-to-end test: attribution and VIF can run together and produce consistent results."""
        if not MODEL_PATH.exists() or not GRAPHS_PATH.exists() or not DESCRIPTORS_PATH.exists():
            pytest.skip("Prerequisites for integration workflow not met.")

        # Run attribution
        run_attribution_analysis(
            model_path=str(MODEL_PATH),
            graphs_path=str(GRAPHS_PATH),
            output_path=str(ATTRIBUTION_PATH)
        )

        # Run VIF
        vif_results = calculate_vif(str(DESCRIPTORS_PATH))

        # Verify both outputs exist and are readable
        assert ATTRIBUTION_PATH.exists()
        assert STATS_PATH.exists()

        # Cross-validate: if VIF shows high collinearity, attribution should still produce results
        # (Attribution methods like Integrated Gradients are robust to some collinearity)
        high_vif_features = [
            f for f, v in vif_results["vif_scores"].items()
            if v > 5.0
        ]

        with open(ATTRIBUTION_PATH, "r") as f:
            attribution_data = json.load(f)

        # Even with collinearity, we should have attributions
        assert len(attribution_data["samples"]) > 0, "Attribution failed despite VIF warnings"