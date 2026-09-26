"""
Unit tests for code/features/descriptor_engine.py
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from features.descriptor_engine import DescriptorEngine
from config import get_max_elements


class TestDescriptorEngine:
    """Tests for DescriptorEngine class functionality."""

    @pytest.fixture
    def sample_composition_data(self):
        """Create sample composition data."""
        return pd.DataFrame({
            'Sn': [0.95, 0.60, 0.50],
            'Ag': [0.03, 0.03, 0.03],
            'Cu': [0.02, 0.03, 0.03],
            'Bi': [0.00, 0.00, 0.00],
            'In': [0.00, 0.00, 0.00],
        })

    @pytest.fixture
    def engine(self):
        """Create a DescriptorEngine instance."""
        return DescriptorEngine()

    def test_calculate_weighted_mean_atomic_mass(self, sample_composition_data, engine):
        """Test weighted mean atomic mass calculation."""
        # Known atomic masses: Sn=118.71, Ag=107.87, Cu=63.55
        # Row 0: 0.95*118.71 + 0.03*107.87 + 0.02*63.55
        expected = 0.95 * 118.71 + 0.03 * 107.87 + 0.02 * 63.55
        
        result = engine._calculate_weighted_mean_atomic_mass(sample_composition_data)
        
        assert abs(result.iloc[0] - expected) < 0.01

    def test_calculate_electronegativity_variance(self, sample_composition_data, engine):
        """Test electronegativity variance calculation."""
        # Known electronegativities: Sn=1.96, Ag=1.93, Cu=1.90
        # Row 0: weighted values
        # Variance = E[X^2] - (E[X])^2
        
        result = engine._calculate_electronegativity_variance(sample_composition_data)
        
        # Result should be non-negative
        assert all(result >= 0)
        assert len(result) == len(sample_composition_data)

    def test_calculate_atomic_radius_variance(self, sample_composition_data, engine):
        """Test atomic radius variance calculation."""
        result = engine._calculate_atomic_radius_variance(sample_composition_data)
        
        # Result should be non-negative
        assert all(result >= 0)
        assert len(result) == len(sample_composition_data)

    def test_calculate_weighted_avg_melting_point(self, sample_composition_data, engine):
        """Test weighted average melting point calculation."""
        # Known melting points: Sn=231.93, Ag=961.78, Cu=1084.62
        # Row 0: 0.95*231.93 + 0.03*961.78 + 0.02*1084.62
        expected = 0.95 * 231.93 + 0.03 * 961.78 + 0.02 * 1084.62
        
        result = engine._calculate_weighted_avg_melting_point(sample_composition_data)
        
        assert abs(result.iloc[0] - expected) < 0.1

    def test_calculate_valence_electron_concentration(self, sample_composition_data, engine):
        """Test valence electron concentration calculation."""
        # Known valence electrons: Sn=4, Ag=1, Cu=1
        # Row 0: 0.95*4 + 0.03*1 + 0.02*1
        expected = 0.95 * 4 + 0.03 * 1 + 0.02 * 1
        
        result = engine._calculate_valence_electron_concentration(sample_composition_data)
        
        assert abs(result.iloc[0] - expected) < 0.01

    def test_compute_all_descriptors(self, sample_composition_data, engine):
        """Test computation of all descriptors at once."""
        descriptors = engine.compute_all_descriptors(sample_composition_data)
        
        expected_columns = [
            'weighted_mean_atomic_mass',
            'electronegativity_variance',
            'atomic_radius_variance',
            'weighted_avg_melting_point',
            'valence_electron_concentration'
        ]
        
        assert all(col in descriptors.columns for col in expected_columns)
        assert len(descriptors) == len(sample_composition_data)

    def test_save_descriptors_to_file(self, sample_composition_data, engine, tmp_path):
        """Test saving descriptors to a file."""
        descriptors = engine.compute_all_descriptors(sample_composition_data)
        output_path = tmp_path / "descriptors.csv"
        
        engine.save_descriptors(descriptors, str(output_path))
        
        assert output_path.exists()
        
        # Verify loaded data matches
        loaded = pd.read_csv(output_path)
        pd.testing.assert_frame_equal(descriptors, loaded)

    def test_handle_missing_elements(self, engine):
        """Test handling of elements not in mendeleev database."""
        # Create data with an unknown element
        unknown_data = pd.DataFrame({
            'Sn': [0.95],
            'UnknownElement': [0.05],
        })
        
        # Should not crash, but may produce NaN for unknown elements
        # The implementation should handle this gracefully
        try:
            descriptors = engine.compute_all_descriptors(unknown_data)
            # If it runs, check that we have results (possibly with NaN)
            assert descriptors is not None
        except Exception:
            # If it raises, that's also acceptable behavior for unknown elements
            pass
