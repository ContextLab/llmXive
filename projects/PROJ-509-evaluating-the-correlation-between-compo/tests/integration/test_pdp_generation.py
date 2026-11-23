"""
Integration test for Partial Dependence Plot (PDP) generation.

This test verifies that the PDP generation pipeline:
1. Successfully loads the trained Random Forest model from disk.
2. Loads the processed feature data (computed_descriptors.csv).
3. Generates PDPs for the top-ranked features using sklearn.inspection.
4. Saves the generated plots to the expected output directory.
5. Validates that the output files exist and are non-empty.

Prerequisites:
- T026: Model artifacts saved to data/evaluation/trained_models.pkl
- T016: Processed descriptors saved to data/processed/computed_descriptors.csv
- T040: Feature ranking saved to data/evaluation/feature_ranking.json (optional, fallback to all features)
"""

import os
import sys
import json
import pickle
import logging
from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import partial_dependence, PartialDependenceDisplay
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for CI/Headless environments
import matplotlib.pyplot as plt

# Add project root to path to import code modules
project_root = Path(__file__).resolve().parent.parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from config import load_paths
from utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)
logger.setLevel(logging.INFO)

# Constants
OUTPUT_DIR = "pdp_plots"
EXPECTED_PDP_COUNT_MIN = 1  # At least one PDP must be generated

class TestPDPGeneration:
    """Integration tests for PDP generation."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test paths and clean up previous outputs."""
        self.paths = load_paths()
        self.model_path = self.paths["data"] / "evaluation" / "trained_models.pkl"
        self.data_path = self.paths["data"] / "processed" / "computed_descriptors.csv"
        self.ranking_path = self.paths["data"] / "evaluation" / "feature_ranking.json"
        self.output_dir = self.paths["data"] / "evaluation" / OUTPUT_DIR

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Clean up any existing PDP files
        for f in self.output_dir.glob("*.png"):
            f.unlink()

        yield

        # Optional: Log success or failure after test
        if self.output_dir.exists():
            files = list(self.output_dir.glob("*.png"))
            logger.info(f"Generated {len(files)} PDP files in {self.output_dir}")

    def _load_model(self):
        """Load the trained Random Forest model."""
        if not self.model_path.exists():
            pytest.fail(f"Model artifact not found at {self.model_path}. "
                        "Ensure T026 (save_models) has been completed.")

        with open(self.model_path, 'rb') as f:
            data = pickle.load(f)

        if "rf_model" not in data:
            pytest.fail("Model artifact does not contain 'rf_model'.")

        return data["rf_model"]

    def _load_data(self):
        """Load the processed descriptor dataset."""
        if not self.data_path.exists():
            pytest.fail(f"Processed data not found at {self.data_path}. "
                        "Ensure T016 (descriptors) has been completed.")

        df = pd.read_csv(self.data_path)

        # Expected target column
        target_col = "formation_energy_per_atom"
        if target_col not in df.columns:
            pytest.fail(f"Target column '{target_col}' not found in dataset.")

        # Feature columns: exclude target and any non-feature metadata if present
        feature_cols = [c for c in df.columns if c != target_col]
        if not feature_cols:
            pytest.fail("No feature columns found in dataset.")

        return df, feature_cols, target_col

    def _get_top_features(self, feature_cols, n_top=3):
        """
        Determine which features to plot.
        Prefer loading from feature_ranking.json (T040), fallback to first n features.
        """
        if self.ranking_path.exists():
            try:
                with open(self.ranking_path, 'r') as f:
                    ranking_data = json.load(f)
                # Expecting a list of dicts or a dict with 'ranked_features'
                if isinstance(ranking_data, list):
                    top_features = [item.get("feature", item.get("name")) for item in ranking_data[:n_top]]
                elif isinstance(ranking_data, dict) and "ranked_features" in ranking_data:
                    top_features = [item.get("feature", item.get("name")) for item in ranking_data["ranked_features"][:n_top]]
                else:
                    top_features = feature_cols[:n_top]
                # Filter to only those present in current data
                valid_features = [f for f in top_features if f in feature_cols]
                if valid_features:
                    return valid_features
            except Exception as e:
                logger.warning(f"Could not load feature ranking: {e}. Falling back to default.")

        return feature_cols[:n_top]

    def test_pdp_generation_pipeline(self):
        """
        End-to-end test: Load model, load data, compute PDPs, save plots, verify existence.
        """
        # 1. Load Model
        model = self._load_model()
        assert isinstance(model, RandomForestRegressor), "Loaded model is not a RandomForestRegressor."

        # 2. Load Data
        df, feature_cols, target_col = self._load_data()
        X = df[feature_cols]
        y = df[target_col]

        # 3. Select Features to Plot
        features_to_plot = self._get_top_features(feature_cols, n_top=3)
        assert len(features_to_plot) > 0, "No features selected for PDP generation."

        # 4. Generate PDPs
        # We generate one plot per feature to ensure distinct files
        generated_files = []

        for feature in features_to_plot:
            try:
                # Compute partial dependence
                # Using 'auto' for kind to handle both regression and classification if needed
                pdp = partial_dependence(
                    model,
                    X,
                    features=[feature],
                    kind='average'
                )

                # Create plot
                fig, ax = plt.subplots(figsize=(8, 6))
                # pdp['values'] is a list of arrays, pdp['average'] is a list of arrays
                values = pdp['values'][0]
                average = pdp['average'][0]

                ax.plot(values, average, marker='o', linestyle='-')
                ax.set_xlabel(feature)
                ax.set_ylabel("Partial Dependence")
                ax.set_title(f"Partial Dependence Plot: {feature}")
                ax.grid(True, alpha=0.3)

                # Save figure
                safe_name = feature.replace(" ", "_").replace("(", "").replace(")", "").replace(".", "_")
                filename = f"pdp_{safe_name}.png"
                filepath = self.output_dir / filename

                plt.savefig(filepath, dpi=150, bbox_inches='tight')
                plt.close(fig)

                generated_files.append(filepath)

            except Exception as e:
                logger.error(f"Failed to generate PDP for {feature}: {e}")
                pytest.fail(f"Failed to generate PDP for feature '{feature}': {e}")

        # 5. Verify Outputs
        assert len(generated_files) >= EXPECTED_PDP_COUNT_MIN, \
            f"Expected at least {EXPECTED_PDP_COUNT_MIN} PDP files, but generated {len(generated_files)}."

        for fpath in generated_files:
            assert fpath.exists(), f"Output file {fpath} was not created."
            assert fpath.stat().st_size > 0, f"Output file {fpath} is empty."

        logger.info(f"Successfully generated and verified {len(generated_files)} PDP files.")