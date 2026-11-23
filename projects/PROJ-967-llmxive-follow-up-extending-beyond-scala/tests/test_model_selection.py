import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from code.model_selection import load_cleaned_data, select_model_type, save_selection


class TestModelSelection:
    """Tests for the model selection task (T027d)."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def cleaned_data_small(self, temp_dir):
        """Create a small cleaned dataset (N=25) for fail case."""
        df = pd.DataFrame({
            'sample_id': [f's{i}' for i in range(25)],
            'prompt': ['test prompt'] * 25,
            'student_scalar': [1.0] * 25,
            'fidelity_loss': [0.5] * 25,
            'primary_dimension': ['Alignment'] * 25,
        })
        path = os.path.join(temp_dir, 'cleaned_small.parquet')
        df.to_parquet(path)
        return path

    @pytest.fixture
    def cleaned_data_medium(self, temp_dir):
        """Create a medium cleaned dataset (N=150) for ridge case."""
        df = pd.DataFrame({
            'sample_id': [f's{i}' for i in range(150)],
            'prompt': ['test prompt'] * 150,
            'student_scalar': [1.0] * 150,
            'fidelity_loss': [0.5] * 150,
            'primary_dimension': ['Alignment'] * 150,
        })
        path = os.path.join(temp_dir, 'cleaned_medium.parquet')
        df.to_parquet(path)
        return path

    @pytest.fixture
    def cleaned_data_large(self, temp_dir):
        """Create a large cleaned dataset (N=500) for rf case."""
        df = pd.DataFrame({
            'sample_id': [f's{i}' for i in range(500)],
            'prompt': ['test prompt'] * 500,
            'student_scalar': [1.0] * 500,
            'fidelity_loss': [0.5] * 500,
            'primary_dimension': ['Alignment'] * 500,
        })
        path = os.path.join(temp_dir, 'cleaned_large.parquet')
        df.to_parquet(path)
        return path

    def test_select_model_fail(self):
        """Test that N < 30 results in 'fail' model type."""
        model_type, reason = select_model_type(25, None)
        assert model_type == "fail"
        assert "N < 30" in reason

    def test_select_model_ridge(self):
        """Test that 30 <= N < 300 results in 'ridge' model type."""
        model_type, reason = select_model_type(150, None)
        assert model_type == "ridge"
        assert "Ridge" in reason

    def test_select_model_rf(self):
        """Test that N >= 300 results in 'rf' model type."""
        model_type, reason = select_model_type(500, None)
        assert model_type == "rf"
        assert "Random Forest" in reason

    def test_load_cleaned_data(self, cleaned_data_small):
        """Test loading cleaned data."""
        df = load_cleaned_data(None, cleaned_data_small)
        assert len(df) == 25
        assert 'sample_id' in df.columns

    def test_save_selection(self, temp_dir):
        """Test saving model selection to JSON."""
        output_path = os.path.join(temp_dir, 'model_selection.json')
        selection_data = {
            "model_type": "ridge",
            "n_samples": 150,
            "threshold": 30,
            "reason": "Low Power: Using Ridge Regression",
            "status": "selected"
        }
        save_selection(selection_data, output_path, None)
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            saved = json.load(f)
        
        assert saved['model_type'] == "ridge"
        assert saved['n_samples'] == 150

    def test_file_not_found(self, temp_dir):
        """Test that missing input file raises FileNotFoundError."""
        non_existent = os.path.join(temp_dir, 'missing.parquet')
        with pytest.raises(FileNotFoundError):
            load_cleaned_data(None, non_existent)

    def test_edge_case_n_equals_30(self):
        """Test boundary case where N == 30."""
        model_type, reason = select_model_type(30, None)
        assert model_type == "ridge"

    def test_edge_case_n_equals_299(self):
        """Test boundary case where N == 299."""
        model_type, reason = select_model_type(299, None)
        assert model_type == "ridge"

    def test_edge_case_n_equals_300(self):
        """Test boundary case where N == 300."""
        model_type, reason = select_model_type(300, None)
        assert model_type == "rf"