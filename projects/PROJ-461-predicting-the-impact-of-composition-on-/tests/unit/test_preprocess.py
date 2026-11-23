"""
Unit tests for the preprocessing module.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from code.data.preprocess import (
    normalize_element_symbol,
    parse_composition,
    generate_synthetic_data,
    preprocess_data,
    MIN_REAL_ROWS
)


class TestNormalizeElementSymbol:
    """Tests for normalize_element_symbol function."""

    def test_valid_elements(self):
        """Test normalization of valid elements."""
        assert normalize_element_symbol('fe') == 'Fe'
        assert normalize_element_symbol('FE') == 'Fe'
        assert normalize_element_symbol('cu') == 'Cu'
        assert normalize_element_symbol('Zn') == 'Zn'
        assert normalize_element_symbol('  al  ') == 'Al'

    def test_invalid_element(self):
        """Test that invalid elements raise ValueError."""
        with pytest.raises(ValueError):
            normalize_element_symbol('XX')
        
        with pytest.raises(ValueError):
            normalize_element_symbol('')
        
        with pytest.raises(ValueError):
            normalize_element_symbol(None)

    def test_mixed_case(self):
        """Test various case combinations."""
        assert normalize_element_symbol('mG') == 'Mg'
        assert normalize_element_symbol('Ni') == 'Ni'
        assert normalize_element_symbol('nb') == 'Nb'


class TestParseComposition:
    """Tests for parse_composition function."""

    def test_json_format(self):
        """Test parsing JSON format composition."""
        comp_str = "{'Zr': 0.5, 'Cu': 0.4, 'Al': 0.1}"
        result = parse_composition(comp_str)
        
        assert 'Zr' in result
        assert 'Cu' in result
        assert 'Al' in result
        assert abs(result['Zr'] - 0.5) < 1e-6

    def test_colon_separated_format(self):
        """Test parsing colon-separated format."""
        comp_str = "Zr:50, Cu:40, Al:10"
        result = parse_composition(comp_str)
        
        assert len(result) == 3
        assert abs(result['Zr'] - 0.5) < 1e-6
        assert abs(result['Cu'] - 0.4) < 1e-6
        assert abs(result['Al'] - 0.1) < 1e-6

    def test_standard_notation(self):
        """Test parsing standard notation like Zr50Cu40Al10."""
        comp_str = "Zr50Cu40Al10"
        result = parse_composition(comp_str)
        
        assert len(result) == 3
        # Should sum to 1.0
        assert abs(sum(result.values()) - 1.0) < 1e-6

    def test_na_input(self):
        """Test handling of NaN input."""
        result = parse_composition(None)
        assert result == {}
        
        result = parse_composition(float('nan'))
        assert result == {}

    def test_invalid_composition(self):
        """Test handling of invalid composition string."""
        result = parse_composition("invalid_string")
        assert result == {}


class TestGenerateSyntheticData:
    """Tests for generate_synthetic_data function."""

    def test_generated_data_structure(self):
        """Test that generated data has correct structure."""
        df = generate_synthetic_data(n_samples=10, seed=42)
        
        assert len(df) == 10
        assert 'composition' in df.columns
        assert 'density' in df.columns

    def test_composition_validity(self):
        """Test that compositions are valid dictionaries."""
        df = generate_synthetic_data(n_samples=5, seed=42)
        
        for _, row in df.iterrows():
            comp = row['composition']
            assert isinstance(comp, dict)
            assert len(comp) >= 2
            assert len(comp) <= 5
            
            # Check that values sum to approximately 1.0
            total = sum(comp.values())
            assert abs(total - 1.0) < 1e-6
            
            # Check that all values are positive
            assert all(v > 0 for v in comp.values())

    def test_density_positive(self):
        """Test that all densities are positive."""
        df = generate_synthetic_data(n_samples=20, seed=42)
        assert all(df['density'] > 0)

    def test_reproducibility(self):
        """Test that same seed produces same results."""
        df1 = generate_synthetic_data(n_samples=10, seed=123)
        df2 = generate_synthetic_data(n_samples=10, seed=123)
        
        pd.testing.assert_frame_equal(df1, df2)

    def test_different_seeds(self):
        """Test that different seeds produce different results."""
        df1 = generate_synthetic_data(n_samples=10, seed=123)
        df2 = generate_synthetic_data(n_samples=10, seed=456)
        
        # At least some values should be different
        assert not df1.equals(df2)


class TestPreprocessData:
    """Tests for preprocess_data function."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for test data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_preprocess_real_data(self, temp_data_dir):
        """Test preprocessing with sufficient real data."""
        # Create mock raw data with enough rows
        data = []
        for i in range(100):
            data.append({
                'composition': f"Zr{50+i}Cu{40-i}Al10",
                'density': 6.0 + i * 0.01
            })
        
        input_path = temp_data_dir / "raw_data.csv"
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        output_path = temp_data_dir / "clean_data.csv"
        
        stats = preprocess_data(str(input_path), str(output_path))
        
        assert stats['filtered_rows'] == 100
        assert stats['fallback_triggered'] is False
        assert output_path.exists()
        
        # Verify output has no missing densities
        df = pd.read_csv(output_path)
        assert df['density'].notna().all()

    def test_preprocess_insufficient_data_triggers_fallback(self, temp_data_dir):
        """Test that insufficient real data triggers synthetic generation."""
        # Create mock raw data with only 30 rows (< MIN_REAL_ROWS)
        data = []
        for i in range(30):
            data.append({
                'composition': f"Zr{50+i}Cu{40-i}Al10",
                'density': 6.0 + i * 0.01
            })
        
        input_path = temp_data_dir / "raw_data.csv"
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        output_path = temp_data_dir / "clean_data.csv"
        
        stats = preprocess_data(str(input_path), str(output_path))
        
        assert stats['fallback_triggered'] is True
        assert stats['synthetic_rows'] >= MIN_REAL_ROWS
        assert (temp_data_dir / "synthetic_data.csv").exists()

    def test_preprocess_with_missing_density(self, temp_data_dir):
        """Test filtering rows with missing density."""
        data = [
            {'composition': 'Zr50Cu40Al10', 'density': 6.0},
            {'composition': 'Zr55Cu35Al10', 'density': None},
            {'composition': 'Zr60Cu30Al10', 'density': 6.5},
            {'composition': 'Zr65Cu25Al10', 'density': float('nan')},
        ] * 20  # 80 rows, 40 with missing density
        
        input_path = temp_data_dir / "raw_data.csv"
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        output_path = temp_data_dir / "clean_data.csv"
        
        stats = preprocess_data(str(input_path), str(output_path))
        
        assert stats['removed_rows'] == 40
        assert stats['filtered_rows'] == 40
        assert stats['fallback_triggered'] is False

    def test_preprocess_empty_composition(self, temp_data_dir):
        """Test handling of rows with invalid compositions."""
        data = [
            {'composition': 'Zr50Cu40Al10', 'density': 6.0},
            {'composition': 'invalid', 'density': 6.1},
            {'composition': '', 'density': 6.2},
            {'composition': 'Zr55Cu35Al10', 'density': 6.3},
        ] * 20  # 80 rows, 40 with invalid composition
        
        input_path = temp_data_dir / "raw_data.csv"
        pd.DataFrame(data).to_csv(input_path, index=False)
        
        output_path = temp_data_dir / "clean_data.csv"
        
        # Should still work, just skipping invalid rows
        stats = preprocess_data(str(input_path), str(output_path))
        
        # At least some rows should be processed
        assert stats['filtered_rows'] > 0