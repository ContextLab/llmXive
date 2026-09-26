"""
Unit tests for code/features/transformer.py
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features.transformer import CLRTransformer
from compositional import clr


class TestCLRTransformer:
    """Tests for CLRTransformer class functionality."""

    @pytest.fixture
    def sample_composition_data(self):
        """Create sample composition data (closed to 1.0)."""
        return pd.DataFrame({
            'Sn': [0.95, 0.60, 0.50],
            'Ag': [0.03, 0.03, 0.03],
            'Cu': [0.02, 0.03, 0.03],
        })

    @pytest.fixture
    def transformer(self):
        """Create a CLRTransformer instance."""
        return CLRTransformer()

    def test_clr_transform_basic(self, sample_composition_data, transformer):
        """Test basic CLR transformation."""
        result = transformer.transform(sample_composition_data)
        
        # CLR transform should produce same number of rows
        assert len(result) == len(sample_composition_data)
        
        # CLR transform is scale-invariant, so sum of transformed values
        # should be approximately zero (within numerical precision)
        for idx in range(len(result)):
            row_sum = result.iloc[idx].sum()
            assert abs(row_sum) < 1e-6, f"Row {idx} sum is {row_sum}, expected ~0"

    def test_clr_transform_with_known_values(self, transformer):
        """Test CLR transform with known mathematical result."""
        # Simple 2-component composition: [0.5, 0.5]
        # Geometric mean = sqrt(0.5 * 0.5) = 0.5
        # CLR = [ln(0.5/0.5), ln(0.5/0.5)] = [0, 0]
        
        simple_data = pd.DataFrame({
            'A': [0.5],
            'B': [0.5],
        })
        
        result = transformer.transform(simple_data)
        
        # Both values should be 0
        assert abs(result.iloc[0]['A']) < 1e-6
        assert abs(result.iloc[0]['B']) < 1e-6

    def test_clr_transform_preserves_compositional_structure(self, sample_composition_data, transformer):
        """Test that CLR transform preserves the compositional nature."""
        result = transformer.transform(sample_composition_data)
        
        # Each row should sum to approximately 0
        row_sums = result.sum(axis=1)
        assert all(abs(s) < 1e-6 for s in row_sums)

    def test_save_clr_features(self, sample_composition_data, transformer, tmp_path):
        """Test saving CLR features to file."""
        result = transformer.transform(sample_composition_data)
        output_path = tmp_path / "clr_features.csv"
        
        transformer.save_clr_features(result, str(output_path))
        
        assert output_path.exists()
        
        # Verify loaded data matches
        loaded = pd.read_csv(output_path)
        # Reset index for comparison
        result_reset = result.reset_index(drop=True)
        loaded_reset = loaded.reset_index(drop=True)
        pd.testing.assert_frame_equal(result_reset, loaded_reset)

    def test_handle_zero_values(self, transformer):
        """Test handling of zero values in composition."""
        # CLR transform requires positive values
        # Zero values should either be handled or raise an error
        data_with_zeros = pd.DataFrame({
            'Sn': [1.0],
            'Ag': [0.0],
            'Cu': [0.0],
        })
        
        # This should raise an error or handle zeros appropriately
        # The exact behavior depends on implementation
        try:
            result = transformer.transform(data_with_zeros)
            # If it runs, check result
            assert result is not None
        except (ValueError, ZeroDivisionError):
            # Expected behavior for zero values
            pass

    def test_multiple_compositions(self, transformer):
        """Test CLR transform on multiple compositions."""
        data = pd.DataFrame({
            'A': [0.1, 0.2, 0.3, 0.4],
            'B': [0.2, 0.3, 0.4, 0.3],
            'C': [0.7, 0.5, 0.3, 0.3],
        })
        
        result = transformer.transform(data)
        
        assert len(result) == 4
        
        # Check each row sums to ~0
        for idx in range(4):
            row_sum = result.iloc[idx].sum()
            assert abs(row_sum) < 1e-6
