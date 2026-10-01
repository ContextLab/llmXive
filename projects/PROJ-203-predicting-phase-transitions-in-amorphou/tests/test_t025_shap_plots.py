"""
Tests for T025: SHAP Summary Plots and Ranked Feature Importance.

Verifies that:
1. The evaluate module loads correctly.
2. SHAP values are computed correctly for a mock model/data.
3. Plots are generated and saved to disk.
4. Ranked feature lists are generated correctly.
"""
import os
import sys
import tempfile
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from models.evaluate import (
    compute_shap_values,
    generate_shap_plots_for_family,
    get_family_mask
)
import shap

class TestT025SHAPPlots:
    @pytest.fixture
    def mock_data(self):
        """Create a small mock dataset for testing."""
        np.random.seed(42)
        n_samples = 24
        data = {
            'composition_id': [f"comp_{i}" for i in range(n_samples)],
            'rdf_peak_pos': np.random.rand(n_samples) * 10,
            'rdf_peak_width': np.random.rand(n_samples) * 2,
            'bond_angle_variance': np.random.rand(n_samples) * 5,
            'coordination_numbers': np.random.rand(n_samples) * 6,
            'Tg_exp': np.random.rand(n_samples) * 300 + 200,
            'Tx_exp': np.random.rand(n_samples) * 300 + 250,
            'chemical_family': np.random.choice(['oxide', 'sulfide', 'organic'], n_samples)
        }
        df = pd.DataFrame(data)
        # Create a binary label for classification
        df['crystallization_label'] = (df['Tx_exp'] - df['Tg_exp'] <= 50).astype(int)
        return df

    @pytest.fixture
    def mock_models(self):
        """Create mock trained models."""
        np.random.seed(42)
        X = np.random.rand(24, 4)
        y_reg = np.random.rand(24) * 300 + 200
        y_clf = np.random.randint(0, 2, 24)

        regressor = RandomForestRegressor(n_estimators=10, random_state=42)
        regressor.fit(X, y_reg)

        classifier = RandomForestClassifier(n_estimators=10, random_state=42)
        classifier.fit(X, y_clf)

        return regressor, classifier

    def test_get_family_mask(self, mock_data):
        """Test filtering by chemical family."""
        mask = get_family_mask(mock_data, 'oxide')
        assert isinstance(mask, np.ndarray)
        assert mask.dtype == bool
        # Check that at least one family exists
        assert mock_data[mask].shape[0] > 0 or mock_data[~mask].shape[0] > 0

    def test_compute_shap_values_regressor(self, mock_data, mock_models):
        """Test SHAP computation for regressor."""
        X = mock_data[['rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers']]
        regressor, _ = mock_models

        result = compute_shap_values(regressor, X, model_type="regressor")

        assert isinstance(result, shap.Explanation)
        assert result.values.shape == (X.shape[0], X.shape[1])
        assert len(result.feature_names) == X.shape[1]

    def test_compute_shap_values_classifier(self, mock_data, mock_models):
        """Test SHAP computation for classifier."""
        X = mock_data[['rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers']]
        _, classifier = mock_models

        result = compute_shap_values(classifier, X, model_type="classifier")

        assert isinstance(result, shap.Explanation)
        assert result.values.shape == (X.shape[0], X.shape[1])

    def test_generate_shap_plots_for_family(self, mock_data, mock_models, tmp_path):
        """Test generation of plots and ranked lists for a family."""
        X = mock_data[['rdf_peak_pos', 'rdf_peak_width', 'bond_angle_variance', 'coordination_numbers']]
        regressor, _ = mock_models

        # Create a temporary output directory
        output_dir = tmp_path / "shap_plots"
        output_dir.mkdir()

        # Select a family that exists in the mock data
        family = mock_data['chemical_family'].iloc[0]

        result = generate_shap_plots_for_family(
            df=mock_data,
            model=regressor,
            family=family,
            model_type="regressor",
            output_dir=output_dir
        )

        assert result["status"] == "success"
        assert os.path.exists(result["plot_path"])
        assert os.path.exists(result["ranked_features_path"])

        # Verify the plot is a valid image file (check size > 0)
        assert os.path.getsize(result["plot_path"]) > 0

        # Verify the ranked features JSON
        with open(result["ranked_features_path"], 'r') as f:
            ranked_data = json.load(f)

        assert isinstance(ranked_data, list)
        assert len(ranked_data) == X.shape[1] # Should have one entry per feature
        assert all("rank" in item and "feature" in item and "mean_abs_shap" in item for item in ranked_data)

    def test_output_directory_structure(self, mock_data, mock_models, tmp_path):
        """Test that the correct directory structure and files are created."""
        regressor, classifier = mock_models
        output_dir = tmp_path / "shap_plots"
        output_dir.mkdir()

        # Run for both models and a family
        family = mock_data['chemical_family'].iloc[0]

        generate_shap_plots_for_family(mock_data, regressor, family, "regressor", output_dir)
        generate_shap_plots_for_family(mock_data, classifier, family, "classifier", output_dir)

        # Check for expected files
        expected_files = [
            f"shap_summary_{family}_regressor.png",
            f"shap_ranked_{family}_regressor.json",
            f"shap_metadata_{family}_regressor.json",
            f"shap_summary_{family}_classifier.png",
            f"shap_ranked_{family}_classifier.json",
            f"shap_metadata_{family}_classifier.json"
        ]

        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists(), f"Expected file {filename} not found in {output_dir}"
            assert os.path.getsize(file_path) > 0, f"File {filename} is empty"
