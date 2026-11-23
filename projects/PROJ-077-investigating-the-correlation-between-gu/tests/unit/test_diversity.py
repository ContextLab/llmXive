import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.diversity import calculate_shannon_index, validate_input_integrity, run_diversity_pipeline

class TestCalculateShannonIndex:
    """Tests for Shannon index calculation."""
    
    def test_shannon_index_basic(self):
        """Test basic Shannon index calculation."""
        # Simple case: equal abundance
        counts = np.array([[1, 1, 1, 1]])  # 4 taxa, equal abundance
        result = calculate_shannon_index(counts)
        # Shannon = -sum(p * log(p)) = -4 * (0.25 * log(0.25)) = log(4) ≈ 1.386
        expected = np.log(4)
        assert np.isclose(result[0], expected, rtol=1e-5)
    
    def test_shannon_index_single_taxon(self):
        """Test Shannon index with single taxon (should be 0)."""
        counts = np.array([[10, 0, 0, 0]])
        result = calculate_shannon_index(counts)
        assert np.isclose(result[0], 0.0)
    
    def test_shannon_index_dataframe(self):
        """Test Shannon index with DataFrame input."""
        df = pd.DataFrame({
            'taxa1': [1, 2],
            'taxa2': [1, 3],
            'taxa3': [1, 5],
            'taxa4': [1, 0]
        })
        result = calculate_shannon_index(df)
        assert len(result) == 2
        assert result[0] > 0  # Should have some diversity
    
    def test_shannon_index_negative_raises(self):
        """Test that negative counts raise ValueError."""
        counts = np.array([[1, -1, 2]])
        with pytest.raises(ValueError, match="Counts must be non-negative"):
            calculate_shannon_index(counts)
    
    def test_shannon_index_all_zeros(self):
        """Test Shannon index with all zeros (should return 0)."""
        counts = np.array([[0, 0, 0]])
        result = calculate_shannon_index(counts)
        assert np.isclose(result[0], 0.0)

class TestValidateInputIntegrity:
    """Tests for input validation (T020b)."""
    
    def test_valid_integer_counts(self):
        """Test that valid integer counts pass validation."""
        counts = pd.DataFrame({
            'taxa1': [1, 2, 3],
            'taxa2': [4, 5, 6]
        })
        # Should not raise
        validate_input_integrity(counts)
    
    def test_valid_float_abundances(self):
        """Test that valid float relative abundances pass validation."""
        counts = pd.DataFrame({
            'taxa1': [0.1, 0.2, 0.3],
            'taxa2': [0.4, 0.5, 0.6]
        })
        # Should not raise
        validate_input_integrity(counts)
    
    def test_numpy_array_valid(self):
        """Test that valid numpy array passes validation."""
        counts = np.array([[1, 2, 3], [4, 5, 6]])
        # Should not raise
        validate_input_integrity(counts)
    
    def test_non_numeric_column_raises(self):
        """Test that non-numeric columns raise ValueError."""
        counts = pd.DataFrame({
            'taxa1': [1, 2, 3],
            'taxa2': ['a', 'b', 'c']  # Non-numeric
        })
        with pytest.raises(ValueError, match="non-numeric"):
            validate_input_integrity(counts)
    
    def test_nan_values_raises(self):
        """Test that NaN values raise ValueError."""
        counts = pd.DataFrame({
            'taxa1': [1, np.nan, 3],
            'taxa2': [4, 5, 6]
        })
        with pytest.raises(ValueError, match="NaN"):
            validate_input_integrity(counts)
    
    def test_negative_values_raises(self):
        """Test that negative values raise ValueError."""
        counts = pd.DataFrame({
            'taxa1': [1, -2, 3],
            'taxa2': [4, 5, 6]
        })
        with pytest.raises(ValueError, match="negative"):
            validate_input_integrity(counts)
    
    def test_empty_array_raises(self):
        """Test that empty array raises ValueError."""
        counts = pd.DataFrame()
        with pytest.raises(ValueError, match="empty"):
            validate_input_integrity(counts)
    
    def test_invalid_type_raises(self):
        """Test that invalid input type raises ValueError."""
        with pytest.raises(ValueError, match="must be a pandas DataFrame or numpy array"):
            validate_input_integrity([1, 2, 3])  # List is not valid

class TestRunDiversityPipeline:
    """Tests for the full diversity pipeline."""
    
    def test_pipeline_basic(self):
        """Test basic pipeline execution."""
        df = pd.DataFrame({
            'participant_id': [1, 2],
            'taxa1': [10, 20],
            'taxa2': [5, 10],
            'taxa3': [15, 25]
        })
        result = run_diversity_pipeline(df)
        assert 'shannon_index' in result.columns
        assert len(result) == 2
        assert all(result['shannon_index'] > 0)
    
    def test_pipeline_with_metadata(self):
        """Test pipeline correctly excludes metadata columns."""
        df = pd.DataFrame({
            'participant_id': [1, 2],
            'age': [25, 30],
            'taxa1': [10, 20],
            'taxa2': [5, 10]
        })
        result = run_diversity_pipeline(df)
        assert 'shannon_index' in result.columns
        # Metadata columns should remain unchanged
        assert list(result['age']) == [25, 30]
    
    def test_pipeline_no_count_columns(self):
        """Test pipeline with no count columns."""
        df = pd.DataFrame({
            'participant_id': [1, 2],
            'age': [25, 30]
        })
        result = run_diversity_pipeline(df)
        assert 'shannon_index' not in result.columns
    
    def test_pipeline_with_nan_raises(self):
        """Test pipeline raises on NaN in count columns."""
        df = pd.DataFrame({
            'participant_id': [1, 2],
            'taxa1': [10, np.nan],
            'taxa2': [5, 10]
        })
        with pytest.raises(ValueError, match="NaN"):
            run_diversity_pipeline(df)
    
    def test_pipeline_with_negative_raises(self):
        """Test pipeline raises on negative values."""
        df = pd.DataFrame({
            'participant_id': [1, 2],
            'taxa1': [10, -5],
            'taxa2': [5, 10]
        })
        with pytest.raises(ValueError, match="negative"):
            run_diversity_pipeline(df)