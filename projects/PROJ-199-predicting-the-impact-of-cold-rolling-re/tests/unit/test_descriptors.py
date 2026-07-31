"""
Unit tests for texture descriptor calculation.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.features.descriptors import (
    calculate_texture_index,
    calculate_component_volume_fractions,
    calculate_descriptors,
    COMPONENT_RANGES
)
from code.data.models import MaterialType

class TestTextureIndex:
    """Tests for Texture Index calculation."""

    def test_empty_orientations(self):
        """Test that empty orientations return 0.0."""
        result = calculate_texture_index(np.array([]).reshape(0, 3))
        assert result == 0.0

    def test_single_orientation(self):
        """Test single orientation gives reasonable J-index."""
        orientations = np.array([[0, 0, 0]])
        result = calculate_texture_index(orientations)
        # Single point should have high texture index (perfectly aligned)
        assert result >= 1.0

    def test_random_orientations(self):
        """Test random orientations give lower J-index."""
        np.random.seed(42)
        orientations = np.random.rand(1000, 3) * 360
        result = calculate_texture_index(orientations)
        # Random orientations should have lower J-index than aligned
        assert result < 10.0  # Heuristic threshold

    def test_aligned_orientations(self):
        """Test perfectly aligned orientations give high J-index."""
        orientations = np.array([[35, 45, 35]] * 100)  # All Copper
        result = calculate_texture_index(orientations)
        assert result > 1.0

class TestComponentVolumeFractions:
    """Tests for component volume fraction calculation."""

    def test_empty_orientations(self):
        """Test empty orientations return zeros."""
        result = calculate_component_volume_fractions(np.array([]).reshape(0, 3))
        for comp in COMPONENT_RANGES.keys():
            assert result[comp] == 0.0

    def test_perfect_copper(self):
        """Test perfect Copper orientation gives high Copper fraction."""
        # Copper ideal: (35, 45, 35)
        orientations = np.array([[35, 45, 35]] * 100)
        result = calculate_component_volume_fractions(orientations)
        assert result["Copper"] > 0.5  # Should be significant

    def test_perfect_brass(self):
        """Test perfect Brass orientation gives high Brass fraction."""
        # Brass ideal: (0, 45, 0)
        orientations = np.array([[0, 45, 0]] * 100)
        result = calculate_component_volume_fractions(orientations)
        assert result["Brass"] > 0.5

    def test_mixed_orientations(self):
        """Test mixed orientations give reasonable fractions."""
        # 50% Copper, 50% Brass
        copper = np.array([[35, 45, 35]] * 50)
        brass = np.array([[0, 45, 0]] * 50)
        orientations = np.vstack([copper, brass])
        result = calculate_component_volume_fractions(orientations)
        
        # Should have significant fractions for both
        assert result["Copper"] > 0.3
        assert result["Brass"] > 0.3
        # Sum should be <= 1.0 (some points may not fall in any category)
        total = sum(result.values())
        assert total <= 1.0

class TestCalculateDescriptors:
    """Tests for the main calculate_descriptors function."""

    def test_empty_dataframe(self):
        """Test empty DataFrame returns empty result."""
        df = pd.DataFrame()
        result = calculate_descriptors(df)
        assert result.empty

    def test_single_sample(self):
        """Test single sample calculation."""
        data = {
            'phi1': [35, 35, 35],
            'Phi': [45, 45, 45],
            'phi2': [35, 35, 35],
            'sample_id': ['S1', 'S1', 'S1'],
            'reduction': [50, 50, 50],
            'material': ['Al', 'Al', 'Al']
        }
        df = pd.DataFrame(data)
        result = calculate_descriptors(df)
        
        assert len(result) == 1
        assert result['sample_id'].iloc[0] == 'S1'
        assert 'texture_index' in result.columns
        assert 'volume_fraction_Copper' in result.columns

    def test_multiple_samples(self):
        """Test multiple samples calculation."""
        # Sample 1: Copper texture
        s1 = pd.DataFrame({
            'phi1': [35, 35, 35],
            'Phi': [45, 45, 45],
            'phi2': [35, 35, 35],
            'sample_id': ['S1', 'S1', 'S1'],
            'reduction': [50, 50, 50],
            'material': ['Al', 'Al', 'Al']
        })
        
        # Sample 2: Brass texture
        s2 = pd.DataFrame({
            'phi1': [0, 0, 0],
            'Phi': [45, 45, 45],
            'phi2': [0, 0, 0],
            'sample_id': ['S2', 'S2', 'S2'],
            'reduction': [70, 70, 70],
            'material': ['Cu', 'Cu', 'Cu']
        })
        
        df = pd.concat([s1, s2], ignore_index=True)
        result = calculate_descriptors(df)
        
        assert len(result) == 2
        sample_ids = set(result['sample_id'])
        assert sample_ids == {'S1', 'S2'}

    def test_missing_columns(self):
        """Test that missing required columns raise error."""
        df = pd.DataFrame({'phi1': [0], 'Phi': [0]})  # Missing others
        with pytest.raises(ValueError):
            calculate_descriptors(df)

    def test_output_columns(self):
        """Test that output contains all expected columns."""
        data = {
            'phi1': [35],
            'Phi': [45],
            'phi2': [35],
            'sample_id': ['S1'],
            'reduction': [50],
            'material': ['Al']
        }
        df = pd.DataFrame(data)
        result = calculate_descriptors(df)
        
        expected_cols = [
            'sample_id', 'reduction', 'material', 'texture_index',
            'volume_fraction_Brass', 'volume_fraction_Copper',
            'volume_fraction_S', 'volume_fraction_Goss'
        ]
        
        for col in expected_cols:
            assert col in result.columns

class TestComponentRanges:
    """Tests for component range definitions."""

    def test_all_components_defined(self):
        """Test that all expected components are defined."""
        expected = {'Brass', 'Copper', 'S', 'Goss'}
        assert set(COMPONENT_RANGES.keys()) == expected

    def test_ranges_have_required_fields(self):
        """Test that each component has required fields."""
        required_fields = {'ideal', 'search', 'tolerance'}
        for comp, params in COMPONENT_RANGES.items():
            assert required_fields.issubset(params.keys()), f"Missing fields in {comp}"

    def test_ideal_angles_valid(self):
        """Test that ideal angles are within valid range."""
        for comp, params in COMPONENT_RANGES.items():
            ideal = params['ideal']
            for angle in ideal:
                assert 0 <= angle <= 360, f"Invalid angle {angle} for {comp}"
