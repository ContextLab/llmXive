"""
Unit tests for the save_metrics module.
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
import numpy as np
import pandas as pd

from src.models.save_metrics import save_model_metrics, save_single_model_metrics, _convert_numpy_types
from src.validation.validate_contracts import assert_model_output_valid


class TestConvertNumpyTypes:
    """Test the numpy type conversion utility."""

    def test_convert_numpy_int(self):
        """Test conversion of numpy integers."""
        val = np.int64(42)
        result = _convert_numpy_types(val)
        assert isinstance(result, int)
        assert result == 42

    def test_convert_numpy_float(self):
        """Test conversion of numpy floats."""
        val = np.float64(3.14)
        result = _convert_numpy_types(val)
        assert isinstance(result, float)
        assert abs(result - 3.14) < 1e-10

    def test_convert_numpy_array(self):
        """Test conversion of numpy arrays."""
        val = np.array([1, 2, 3])
        result = _convert_numpy_types(val)
        assert isinstance(result, list)
        assert result == [1, 2, 3]

    def test_convert_nested_dict(self):
        """Test conversion of nested dictionaries with numpy types."""
        val = {
            "coeff": np.float64(0.5),
            "count": np.int32(10),
            "nested": {
                "value": np.float64(2.5)
            }
        }
        result = _convert_numpy_types(val)
        assert isinstance(result["coeff"], float)
        assert isinstance(result["count"], int)
        assert isinstance(result["nested"]["value"], float)


class TestSaveModelMetrics:
    """Test the save_model_metrics function."""

    def test_save_empty_list_raises(self):
        """Test that saving an empty list raises ValueError."""
        with pytest.raises(ValueError, match="model_results cannot be empty"):
            save_model_metrics([])

    def test_save_single_model(self, tmp_path):
        """Test saving a single model's metrics."""
        output_path = str(tmp_path / "test_metrics.json")
        
        results = [
            {
                "model_type": "Gaussian GLM",
                "coefficients": {"intercept": 0.1, "feature1": 0.5},
                "p_values": {"intercept": 0.01, "feature1": 0.05},
                "r_squared": 0.75,
                "aic": 123.45,
                "cross_validation_scores": [0.7, 0.72, 0.68]
            }
        ]
        
        saved_path = save_model_metrics(results, output_path=output_path, validate=False)
        
        assert os.path.exists(saved_path)
        with open(saved_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["model_type"] == "Gaussian GLM"
        assert abs(data[0]["r_squared"] - 0.75) < 1e-6

    def test_save_numpy_types(self, tmp_path):
        """Test that numpy types are properly converted to JSON-serializable types."""
        output_path = str(tmp_path / "test_numpy_metrics.json")
        
        results = [
            {
                "model_type": "Ridge",
                "coefficients": {"x1": np.float64(0.5), "x2": np.int64(1)},
                "p_values": {"x1": np.float64(0.05)},
                "r_squared": np.float64(0.8),
                "aic": np.float64(100.0),
                "cross_validation_scores": np.array([0.75, 0.76])
            }
        ]
        
        saved_path = save_model_metrics(results, output_path=output_path, validate=False)
        
        with open(saved_path, 'r') as f:
            data = json.load(f)
        
        # Verify all values are native Python types
        assert isinstance(data[0]["coefficients"]["x1"], float)
        assert isinstance(data[0]["coefficients"]["x2"], int)
        assert isinstance(data[0]["r_squared"], float)
        assert isinstance(data[0]["cross_validation_scores"], list)

    def test_save_and_validate(self, tmp_path):
        """Test saving and validating against schema."""
        output_path = str(tmp_path / "test_validated_metrics.json")
        
        results = [
            {
                "model_type": "Gaussian GLM",
                "coefficients": {"intercept": 0.1, "eco_kings_pawn": 0.5},
                "p_values": {"intercept": 0.01, "eco_kings_pawn": 0.05},
                "r_squared": 0.75,
                "aic": 123.45,
                "cross_validation_scores": [0.7, 0.72, 0.68, 0.69, 0.71]
            }
        ]
        
        # This should not raise
        saved_path = save_model_metrics(results, output_path=output_path, validate=True)
        
        assert os.path.exists(saved_path)

    def test_save_creates_directory(self, tmp_path):
        """Test that the function creates parent directories if they don't exist."""
        nested_path = tmp_path / "results" / "subdir" / "metrics.json"
        
        results = [
            {
                "model_type": "Test",
                "coefficients": {"x": 0.1},
                "p_values": {"x": 0.5},
                "r_squared": 0.5,
                "aic": 10.0,
                "cross_validation_scores": []
            }
        ]
        
        saved_path = save_model_metrics(results, output_path=str(nested_path), validate=False)
        
        assert os.path.exists(saved_path)


class TestSaveSingleModelMetrics:
    """Test the save_single_model_metrics function."""

    def test_save_single_model_creates_file(self, tmp_path):
        """Test saving a single model creates the file."""
        output_path = str(tmp_path / "single_model.json")
        
        saved_path = save_single_model_metrics(
            model_type="Gaussian GLM",
            coefficients={"intercept": 0.1, "feature1": 0.5},
            p_values={"intercept": 0.01, "feature1": 0.05},
            r_squared=0.75,
            aic=123.45,
            cross_validation_scores=[0.7, 0.72],
            output_path=output_path,
            validate=False
        )
        
        assert os.path.exists(saved_path)
        
        with open(saved_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]["model_type"] == "Gaussian GLM"

    def test_append_to_existing_file(self, tmp_path):
        """Test that saving multiple times appends to the file."""
        output_path = str(tmp_path / "append_test.json")
        
        # First save
        save_single_model_metrics(
            model_type="Model A",
            coefficients={"x": 0.1},
            p_values={"x": 0.5},
            r_squared=0.5,
            aic=10.0,
            cross_validation_scores=[],
            output_path=output_path,
            validate=False
        )
        
        # Second save
        save_single_model_metrics(
            model_type="Model B",
            coefficients={"y": 0.2},
            p_values={"y": 0.4},
            r_squared=0.6,
            aic=15.0,
            cross_validation_scores=[],
            output_path=output_path,
            validate=False
        )
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert len(data) == 2
        assert data[0]["model_type"] == "Model A"
        assert data[1]["model_type"] == "Model B"

    def test_save_single_model_with_numpy_types(self, tmp_path):
        """Test that numpy types are handled correctly."""
        output_path = str(tmp_path / "numpy_test.json")
        
        save_single_model_metrics(
            model_type="Ridge",
            coefficients={"x": np.float64(0.5)},
            p_values={"x": np.float64(0.05)},
            r_squared=np.float64(0.8),
            aic=np.float64(100.0),
            output_path=output_path,
            validate=False
        )
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert isinstance(data[0]["coefficients"]["x"], float)
        assert isinstance(data[0]["r_squared"], float)