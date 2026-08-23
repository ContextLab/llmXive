"""
Unit tests for texture descriptor calculation logic.
Tests T018 implementation.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.features.descriptors import (
    calculate_orientation_distance,
    classify_orientation_to_component,
    calculate_component_volume_fractions,
    calculate_texture_index,
    calculate_descriptors
)
from code.data.models import TextureDescriptor

class TestOrientationDistance:
    def test_zero_distance_identical_orientations(self):
        """Distance between identical orientations should be 0."""
        o1 = (39.0, 39.0, 0.0)
        o2 = (39.0, 39.0, 0.0)
        assert calculate_orientation_distance(o1, o2) == 0.0

    def test_distance_symmetry(self):
        """Distance should be symmetric."""
        o1 = (39.0, 39.0, 0.0)
        o2 = (40.0, 40.0, 1.0)
        d1 = calculate_orientation_distance(o1, o2)
        d2 = calculate_orientation_distance(o2, o1)
        assert abs(d1 - d2) < 1e-6

    def test_periodicity_phi1(self):
        """Test periodicity handling for phi1 (0-360)."""
        o1 = (0.0, 0.0, 0.0)
        o2 = (360.0, 0.0, 0.0)
        # Should be 0 due to periodicity
        assert calculate_orientation_distance(o1, o2) == 0.0

    def test_periodicity_phi2(self):
        """Test periodicity handling for phi2 (0-360)."""
        o1 = (0.0, 0.0, 0.0)
        o2 = (0.0, 0.0, 360.0)
        # Should be 0 due to periodicity
        assert calculate_orientation_distance(o1, o2) == 0.0

class TestComponentClassification:
    def test_copper_classification(self):
        """Orientation at Copper center should classify as Copper."""
        # Copper center: (39, 39, 0)
        orientation = (39.0, 39.0, 0.0)
        component, distance = classify_orientation_to_component(orientation)
        assert component == "Copper"
        assert distance == 0.0

    def test_brass_classification(self):
        """Orientation at Brass center should classify as Brass."""
        # Brass center: (40, 60, 45)
        orientation = (40.0, 60.0, 45.0)
        component, distance = classify_orientation_to_component(orientation)
        assert component == "Brass"
        assert distance == 0.0

    def test_outside_tolerance(self):
        """Orientation far from any center should return None."""
        # Far from all centers
        orientation = (100.0, 100.0, 100.0)
        component, distance = classify_orientation_to_component(orientation)
        assert component is None

    def test_within_tolerance(self):
        """Orientation within tolerance should classify correctly."""
        # Within 5 degrees of Copper center
        orientation = (40.0, 39.0, 0.0)
        component, distance = classify_orientation_to_component(orientation)
        assert component == "Copper"
        assert distance <= 5.0

class TestVolumeFractions:
    def test_empty_dataframe(self):
        """Empty dataframe should return all zeros."""
        df = pd.DataFrame(columns=['phi1', 'Phi', 'phi2'])
        fractions = calculate_component_volume_fractions(df)
        assert all(v == 0.0 for v in fractions.values())

    def test_single_component(self):
        """DataFrame with only Copper orientations should yield 1.0 for Copper."""
        data = [
            (39.0, 39.0, 0.0),
            (39.0, 39.0, 0.0),
            (39.0, 39.0, 0.0)
        ]
        df = pd.DataFrame(data, columns=['phi1', 'Phi', 'phi2'])
        fractions = calculate_component_volume_fractions(df)
        assert fractions["Copper"] == 1.0
        assert fractions["Brass"] == 0.0

    def test_mixed_components(self):
        """DataFrame with mixed components should yield correct fractions."""
        # 2 Copper, 2 Brass, 2 S, 2 Goss = 0.25 each
        data = [
            (39.0, 39.0, 0.0), (39.0, 39.0, 0.0),  # Copper
            (40.0, 60.0, 45.0), (40.0, 60.0, 45.0),  # Brass
            (59.0, 37.0, 63.0), (59.0, 37.0, 63.0),  # S
            (0.0, 45.0, 90.0), (0.0, 45.0, 90.0)    # Goss
        ]
        df = pd.DataFrame(data, columns=['phi1', 'Phi', 'phi2'])
        fractions = calculate_component_volume_fractions(df)
        
        assert abs(fractions["Copper"] - 0.25) < 0.01
        assert abs(fractions["Brass"] - 0.25) < 0.01
        assert abs(fractions["S"] - 0.25) < 0.01
        assert abs(fractions["Goss"] - 0.25) < 0.01

class TestTextureIndex:
    def test_perfect_texture(self):
        """Single component (1.0) should yield index 1.0."""
        fractions = {"Brass": 1.0, "Copper": 0.0, "S": 0.0, "Goss": 0.0}
        index = calculate_texture_index(fractions)
        assert index == 1.0

    def test_random_texture(self):
        """Equal distribution (0.25 each) should yield index 0.25."""
        fractions = {
            "Brass": 0.25, "Copper": 0.25, 
            "S": 0.25, "Goss": 0.25
        }
        index = calculate_texture_index(fractions)
        assert abs(index - 0.25) < 1e-6

class TestCalculateDescriptors:
    def test_full_pipeline(self):
        """Test the full calculate_descriptors pipeline."""
        # Create a synthetic dataset with known fractions
        # 100 points: 50 Copper, 50 random (outside all components)
        data = []
        # 50 Copper points
        for _ in range(50):
            data.append((39.0, 39.0, 0.0))
        # 50 random points (far from all components)
        for _ in range(50):
            data.append((100.0, 100.0, 100.0))
        
        df = pd.DataFrame(data, columns=['phi1', 'Phi', 'phi2'])
        df['sample_id'] = 'test_sample_001'
        
        desc = calculate_descriptors(df, sample_id='test_sample_001')
        
        assert isinstance(desc, TextureDescriptor)
        assert desc.sample_id == 'test_sample_001'
        assert abs(desc.copper_fraction - 0.5) < 0.01
        assert abs(desc.random_fraction - 0.5) < 0.01
        assert desc.texture_index > 0.0
        assert desc.texture_index <= 1.0

    def test_mass_balance(self):
        """Verify that sum of fractions + random = 1.0."""
        data = [
            (39.0, 39.0, 0.0), (39.0, 39.0, 0.0),
            (40.0, 60.0, 45.0), (40.0, 60.0, 45.0),
            (59.0, 37.0, 63.0), (59.0, 37.0, 63.0),
            (0.0, 45.0, 90.0), (0.0, 45.0, 90.0)
        ]
        df = pd.DataFrame(data, columns=['phi1', 'Phi', 'phi2'])
        
        desc = calculate_descriptors(df)
        
        total = (desc.brass_fraction + desc.copper_fraction + 
                 desc.s_fraction + desc.goss_fraction + desc.random_fraction)
        
        assert abs(total - 1.0) < 0.01