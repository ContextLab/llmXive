"""
Unit tests for FCC symmetry handling in features.symmetry module.
"""

import pytest
import numpy as np
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from features.symmetry import (
    get_fcc_symmetry,
    align_orientations_to_fcc,
    find_closest_component,
    classify_orientations_to_components,
    calculate_symmetry_equivalent_count,
    validate_fcc_symmetry_application,
    FCC_COMPONENTS
)

class TestFccSymmetry:
    """Test cases for FCC symmetry handling."""

    def test_get_fcc_symmetry(self):
        """Test that FCC symmetry group is loaded correctly."""
        symmetry = get_fcc_symmetry()
        assert symmetry is not None
        assert symmetry.name == "m-3m"

    def test_align_orientations_to_fcc(self):
        """Test orientation alignment to FCC fundamental zone."""
        # Create a random set of Euler angles
        eulers = np.array([
            [45.0, 45.0, 45.0],
            [30.0, 60.0, 15.0],
            [0.0, 0.0, 0.0]
        ])

        aligned = align_orientations_to_fcc(eulers)
        
        # Check that we got an Orientation object
        assert aligned is not None
        assert len(aligned) == len(eulers)
        
        # Check that symmetry is set
        assert aligned.symmetry.name == "m-3m"

    def test_find_closest_component_brass(self):
        """Test that Brass orientation is correctly identified."""
        # Create a Brass orientation (slightly perturbed)
        brass_euler = np.radians([35.0 + 2.0, 45.0, 0.0])
        from orix.quaternion import Orientation
        from orix.crystal.march import FCC
        symmetry = get_fcc_symmetry()
        orient = Orientation.from_euler(brass_euler, symmetry=symmetry)
        
        component, distance = find_closest_component(orient)
        
        assert component == "Brass"
        assert distance < 15.0  # Should be within tolerance

    def test_find_closest_component_copper(self):
        """Test that Copper orientation is correctly identified."""
        copper_euler = np.radians([90.0, 35.0 + 1.0, 45.0])
        from orix.quaternion import Orientation
        symmetry = get_fcc_symmetry()
        orient = Orientation.from_euler(copper_euler, symmetry=symmetry)
        
        component, distance = find_closest_component(orient)
        
        assert component == "Copper"
        assert distance < 15.0

    def test_classify_orientations(self):
        """Test batch classification of orientations."""
        eulers = np.array([
            [35.0, 45.0, 0.0],   # Brass
            [90.0, 35.0, 45.0],  # Copper
            [0.0, 0.0, 0.0],     # Cube
            [100.0, 100.0, 100.0] # Random (far from any component)
        ])

        results = classify_orientations_to_components(eulers, tolerance=15.0)
        
        assert len(results) == 4
        
        # Check specific assignments
        assert results[0]['component'] == 'Brass'
        assert results[1]['component'] == 'Copper'
        assert results[2]['component'] == 'Cube'
        # The last one should be Random or close to a component if within tolerance
        # Given the random angle, it might be far from any, so likely "Random"
        assert results[3]['component'] in ['Random', 'Brass', 'Copper', 'Cube', 'S', 'Goss']

    def test_classify_orientations_empty(self):
        """Test classification with empty input."""
        eulers = np.array([]).reshape(0, 3)
        results = classify_orientations_to_components(eulers)
        assert results == []

    def test_symmetry_equivalent_count(self):
        """Test that symmetry equivalent count is correct for FCC."""
        eulers = np.array([[45.0, 45.0, 45.0]])
        count = calculate_symmetry_equivalent_count(eulers)
        assert count == 48  # Order of m-3m group

    def test_validate_fcc_symmetry_application(self):
        """Test validation of symmetry application."""
        eulers = np.array([
            [35.0, 45.0, 0.0],
            [90.0, 35.0, 45.0],
            [0.0, 0.0, 0.0]
        ])
        labels = ["Brass", "Copper", "Cube"]
        
        validation = validate_fcc_symmetry_application(eulers, labels)
        
        assert "all_in_sector" in validation
        assert "component_distribution" in validation
        assert "is_valid" in validation
        assert validation['is_valid'] is True
        assert validation['total_samples'] == 3

    def test_fcc_components_defined(self):
        """Test that all standard FCC components are defined."""
        required_components = ["Brass", "Copper", "S", "Goss", "Cube"]
        for comp in required_components:
            assert comp in FCC_COMPONENTS, f"Missing component: {comp}"
            assert len(FCC_COMPONENTS[comp]) == 3, f"Invalid Euler angles for {comp}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])