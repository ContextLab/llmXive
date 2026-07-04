import os
import sys
import pytest
import pandas as pd
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.data_pipeline import (
    load_sampled_functions, 
    compute_radon_metrics, 
    run_pylint_analysis, 
    normalize_pylint_smells, 
    validate_output,
    REQUIRED_COLUMNS,
    COMPLETENESS_THRESHOLD
)

class TestDataPipeline:
    
    @pytest.fixture
    def sample_code(self):
        return """
        def example_function(x, y):
            '''This is a docstring.'''
            return x + y
        """

    @pytest.fixture
    def sample_invalid_code(self):
        return "def invalid_function( x, y : "

    def test_compute_radon_metrics_valid_code(self, sample_code):
        """Test radon metrics computation on valid code."""
        loc, cc = compute_radon_metrics(sample_code)
        assert loc > 0, "LOC should be positive"
        assert cc >= 0, "Cyclomatic complexity should be non-negative"

    def test_compute_radon_metrics_invalid_code(self, sample_invalid_code):
        """Test radon metrics computation on invalid code raises error."""
        with pytest.raises(Exception):
            compute_radon_metrics(sample_invalid_code)

    def test_normalize_pylint_smells(self):
        """Test normalization of Pylint codes to smell names."""
        mock_output = "C0114: Missing module docstring\nR0913: Too many arguments"
        smells = normalize_pylint_smells(mock_output)
        assert "missing_module_docstring" in smells
        assert "too_many_arguments" in smells
        assert len(smells) == 2

    def test_validate_output_missing_columns(self, tmp_path):
        """Test validation fails when required columns are missing."""
        df = pd.DataFrame({
            'id': [1, 2],
            'code': ['def f(): pass', 'def g(): pass']
            # Missing loc, cyclomatic_complexity, static_smell_labels
        })
        csv_path = tmp_path / "test.csv"
        df.to_csv(csv_path, index=False)
        
        result = validate_output(str(csv_path))
        assert result is False

    def test_validate_output_empty_file(self, tmp_path):
        """Test validation fails on empty file."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("")
        
        result = validate_output(str(csv_path))
        assert result is False

    def test_validate_output_not_found(self):
        """Test validation fails when file doesn't exist."""
        result = validate_output("/nonexistent/path/file.csv")
        assert result is False

    def test_validate_output_success(self, tmp_path):
        """Test validation passes when all conditions are met."""
        # Create a DataFrame with all required columns
        data = {
            'id': [1, 2, 3],
            'code': ['def f(): pass', 'def g(): pass', 'def h(): pass'],
            'loc': [1, 2, 3],
            'cyclomatic_complexity': [1, 1, 1],
            'static_smell_labels': ['[]', '[]', '[]']
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "valid.csv"
        df.to_csv(csv_path, index=False)
        
        result = validate_output(str(csv_path))
        assert result is True

    def test_validate_output_below_threshold(self, tmp_path):
        """Test validation fails when completeness is below threshold."""
        # Create data where only 50% rows are complete
        data = {
            'id': [1, 2],
            'code': ['def f(): pass', 'def g(): pass'],
            'loc': [1, None],  # Second row missing loc
            'cyclomatic_complexity': [1, None],
            'static_smell_labels': ['[]', None]
        }
        df = pd.DataFrame(data)
        csv_path = tmp_path / "incomplete.csv"
        df.to_csv(csv_path, index=False)
        
        result = validate_output(str(csv_path))
        assert result is False