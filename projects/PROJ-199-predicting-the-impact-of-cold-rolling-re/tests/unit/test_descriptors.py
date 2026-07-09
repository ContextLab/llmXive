"""
Unit tests for Brass/Copper/S/Goss calculation logic in code/features/descriptors.py.

This test suite validates the volume fraction calculations for major FCC texture
components (Brass, Copper, S, Goss) as defined in the project specification.

The tests verify:
1. Correct identification of orientation components within specified Euler ranges
2. Accurate volume fraction calculation (mass balance check)
3. Proper handling of edge cases (empty datasets, single orientations)
4. Symmetry-aware component matching using orix
"""

import pytest
import numpy as np
from orix.crystal_map import Orientation
from orix.quaternion import Rotation
from orix.crystal import Cubic
from orix.vector import Vector3d

# Import the function under test
from code.features.descriptors import calculate_volume_fractions, get_component_euler_ranges

# Constants for testing
EPSILON = 1e-6  # Tolerance for floating point comparisons


class TestGetComponentEulerRanges:
    """Test that component Euler ranges match the specification."""

    def test_brass_ranges(self):
        """Verify Brass component Euler ranges: [0-45, 35-45, 45-90]."""
        ranges = get_component_euler_ranges()
        brass = ranges['Brass']
        
        # Check order: phi1, Phi, phi2
        assert len(brass) == 3, "Each component should have 3 Euler angle ranges"
        
        # phi1: 0-45 degrees
        assert brass[0][0] == 0.0 and brass[0][1] == 45.0
        
        # Phi: 35-45 degrees
        assert brass[1][0] == 35.0 and brass[1][1] == 45.0
        
        # phi2: 45-90 degrees
        assert brass[2][0] == 45.0 and brass[2][1] == 90.0

    def test_copper_ranges(self):
        """Verify Copper component Euler ranges: [35-45, 35-45, 35-45]."""
        ranges = get_component_euler_ranges()
        copper = ranges['Copper']
        
        assert len(copper) == 3
        assert copper[0][0] == 35.0 and copper[0][1] == 45.0
        assert copper[1][0] == 35.0 and copper[1][1] == 45.0
        assert copper[2][0] == 35.0 and copper[2][1] == 45.0

    def test_s_ranges(self):
        """Verify S component Euler ranges: [35-45, 35-45, 35-45]."""
        ranges = get_component_euler_ranges()
        s = ranges['S']
        
        assert len(s) == 3
        assert s[0][0] == 35.0 and s[0][1] == 45.0
        assert s[1][0] == 35.0 and s[1][1] == 45.0
        assert s[2][0] == 35.0 and s[2][1] == 45.0

    def test_goss_ranges(self):
        """Verify Goss component Euler ranges: [35-45, 35-45, 35-45]."""
        ranges = get_component_euler_ranges()
        goss = ranges['Goss']
        
        assert len(goss) == 3
        assert goss[0][0] == 35.0 and goss[0][1] == 45.0
        assert goss[1][0] == 35.0 and goss[1][1] == 45.0
        assert goss[2][0] == 35.0 and goss[2][1] == 45.0

    def test_all_components_present(self):
        """Ensure all required FCC components are defined."""
        ranges = get_component_euler_ranges()
        required = {'Brass', 'Copper', 'S', 'Goss'}
        assert set(ranges.keys()) == required


class TestCalculateVolumeFractions:
    """Test volume fraction calculation logic."""

    def test_empty_orientation_list(self):
        """Test handling of empty orientation list."""
        empty_orientations = []
        result = calculate_volume_fractions(empty_orientations)
        
        # All fractions should be 0.0
        assert result['Brass'] == 0.0
        assert result['Copper'] == 0.0
        assert result['S'] == 0.0
        assert result['Goss'] == 0.0
        assert result['Random'] == 0.0
        assert abs(sum(result.values()) - 0.0) < EPSILON

    def test_single_orientation_exact_match(self):
        """Test with a single orientation matching Brass component exactly."""
        # Create an orientation at the center of Brass range: (22.5, 40, 67.5)
        # Note: orix uses radians internally, but our function expects degrees
        phi1 = np.radians(22.5)
        phi = np.radians(40.0)
        phi2 = np.radians(67.5)
        
        # Create orientation using Bunge convention
        orientation = Orientation.from_euler([phi1, phi, phi2], symmetry=Cubic())
        
        result = calculate_volume_fractions([orientation])
        
        # Should be 100% Brass
        assert abs(result['Brass'] - 1.0) < EPSILON
        assert result['Copper'] == 0.0
        assert result['S'] == 0.0
        assert result['Goss'] == 0.0
        assert result['Random'] == 0.0

    def test_mixed_components(self):
        """Test with orientations from multiple components."""
        orientations = []
        
        # Add 3 orientations in Brass range
        for phi1 in [10, 20, 30]:
            phi = 40.0
            phi2 = 60.0
            o = Orientation.from_euler(
                np.radians([phi1, phi, phi2]),
                symmetry=Cubic()
            )
            orientations.append(o)
        
        # Add 2 orientations in Copper range
        for phi1 in [40, 40]:
            phi = 40.0
            phi2 = 40.0
            o = Orientation.from_euler(
                np.radians([phi1, phi, phi2]),
                symmetry=Cubic()
            )
            orientations.append(o)
        
        # Add 1 orientation in S range
        o_s = Orientation.from_euler(
            np.radians([40, 40, 40]),
            symmetry=Cubic()
        )
        orientations.append(o_s)
        
        # Total: 6 orientations
        # Expected: Brass=3/6=0.5, Copper=2/6≈0.333, S=1/6≈0.167, Random=0
        result = calculate_volume_fractions(orientations)
        
        assert abs(result['Brass'] - 0.5) < 0.01
        assert abs(result['Copper'] - 2/6) < 0.01
        assert abs(result['S'] - 1/6) < 0.01
        assert result['Goss'] == 0.0
        
        # Mass balance check
        total = sum(result.values())
        assert abs(total - 1.0) < 0.01, f"Mass balance failed: {total}"

    def test_random_orientations(self):
        """Test that orientations outside all component ranges are classified as Random."""
        # Create orientations far from any component range
        orientations = []
        for phi1 in [0, 90, 180]:
            phi = 0.0
            phi2 = 0.0
            o = Orientation.from_euler(
                np.radians([phi1, phi, phi2]),
                symmetry=Cubic()
            )
            orientations.append(o)
        
        result = calculate_volume_fractions(orientations)
        
        # All should be Random
        assert result['Random'] == 1.0
        assert result['Brass'] == 0.0
        assert result['Copper'] == 0.0
        assert result['S'] == 0.0
        assert result['Goss'] == 0.0

    def test_mass_balance_with_random(self):
        """Verify mass balance when random orientations are present."""
        orientations = []
        
        # 4 Brass, 2 Random
        for i in range(4):
            o = Orientation.from_euler(
                np.radians([20, 40, 60]),
                symmetry=Cubic()
            )
            orientations.append(o)
        
        for i in range(2):
            o = Orientation.from_euler(
                np.radians([0, 0, 0]),
                symmetry=Cubic()
            )
            orientations.append(o)
        
        result = calculate_volume_fractions(orientations)
        
        # Brass should be 4/6, Random should be 2/6
        assert abs(result['Brass'] - 4/6) < 0.01
        assert abs(result['Random'] - 2/6) < 0.01
        
        total = sum(result.values())
        assert abs(total - 1.0) < 0.01

    def test_symmetry_handling(self):
        """Test that orix symmetry is properly applied during matching."""
        # Create an orientation that should match after symmetry operations
        # Use a known Brass orientation
        o1 = Orientation.from_euler(
            np.radians([22.5, 40, 67.5]),
            symmetry=Cubic()
        )
        
        # Apply a symmetry operation to get an equivalent orientation
        # This tests that the function handles symmetry correctly
        sym_ops = Cubic().symmetry_operations
        
        orientations = [o1]
        # Add a symmetry-equivalent orientation
        if len(sym_ops) > 1:
            o2 = o1 * sym_ops[1]
            orientations.append(o2)
        
        result = calculate_volume_fractions(orientations)
        
        # Both should be classified as Brass due to symmetry
        assert result['Brass'] == 1.0
        assert result['Random'] == 0.0

    def test_boundary_conditions(self):
        """Test orientations at the boundary of component ranges."""
        orientations = []
        
        # Orientation at exact boundary of Brass: phi1=45, Phi=35, phi2=45
        o_boundary = Orientation.from_euler(
            np.radians([45, 35, 45]),
            symmetry=Cubic()
        )
        orientations.append(o_boundary)
        
        result = calculate_volume_fractions(orientations)
        
        # Should be classified as Brass (inclusive boundaries)
        assert result['Brass'] == 1.0

    def test_large_dataset_performance(self):
        """Test with a larger dataset to ensure reasonable performance."""
        np.random.seed(42)
        n_orientations = 1000
        
        # Generate random orientations
        orientations = []
        for _ in range(n_orientations):
            phi1 = np.random.uniform(0, 90)
            phi = np.random.uniform(0, 90)
            phi2 = np.random.uniform(0, 90)
            o = Orientation.from_euler(
                np.radians([phi1, phi, phi2]),
                symmetry=Cubic()
            )
            orientations.append(o)
        
        result = calculate_volume_fractions(orientations)
        
        # Check mass balance
        total = sum(result.values())
        assert abs(total - 1.0) < 0.01

    def test_return_type_and_structure(self):
        """Verify the function returns the correct data structure."""
        orientations = [
            Orientation.from_euler(np.radians([22.5, 40, 67.5]), symmetry=Cubic())
        ]
        
        result = calculate_volume_fractions(orientations)
        
        # Should be a dictionary
        assert isinstance(result, dict)
        
        # Should have all required keys
        required_keys = {'Brass', 'Copper', 'S', 'Goss', 'Random'}
        assert set(result.keys()) == required_keys
        
        # All values should be floats between 0 and 1
        for key, value in result.items():
            assert isinstance(value, float)
            assert 0.0 <= value <= 1.0

    def test_goss_detection(self):
        """Test detection of Goss component specifically."""
        # Goss orientation: (0, 45, 90) in Bunge convention
        # Note: The spec says [35-45, 35-45, 35-45] which is unusual for Goss
        # but we follow the spec exactly
        o_goss = Orientation.from_euler(
            np.radians([40, 40, 40]),  # Within spec range
            symmetry=Cubic()
        )
        
        result = calculate_volume_fractions([o_goss])
        
        # Should be classified as Goss per spec ranges
        assert result['Goss'] == 1.0
        assert result['Brass'] == 0.0
        assert result['Copper'] == 0.0
        assert result['S'] == 0.0
        assert result['Random'] == 0.0

    def test_copper_detection(self):
        """Test detection of Copper component specifically."""
        # Copper orientation within spec range [35-45, 35-45, 35-45]
        o_copper = Orientation.from_euler(
            np.radians([40, 40, 40]),
            symmetry=Cubic()
        )
        
        result = calculate_volume_fractions([o_copper])
        
        # Should be classified as Copper per spec ranges
        assert result['Copper'] == 1.0

    def test_s_detection(self):
        """Test detection of S component specifically."""
        # S orientation within spec range [35-45, 35-45, 35-45]
        o_s = Orientation.from_euler(
            np.radians([40, 40, 40]),
            symmetry=Cubic()
        )
        
        result = calculate_volume_fractions([o_s])
        
        # Should be classified as S per spec ranges
        assert result['S'] == 1.0

    def test_robustness_to_single_component_dataset(self):
        """Test dataset containing only one component type."""
        # Create 100 Brass orientations
        orientations = []
        for _ in range(100):
            # Add slight random variation within Brass range
            phi1 = np.random.uniform(0, 45)
            phi = np.random.uniform(35, 45)
            phi2 = np.random.uniform(45, 90)
            o = Orientation.from_euler(
                np.radians([phi1, phi, phi2]),
                symmetry=Cubic()
            )
            orientations.append(o)
        
        result = calculate_volume_fractions(orientations)
        
        assert result['Brass'] == 1.0
        assert result['Copper'] == 0.0
        assert result['S'] == 0.0
        assert result['Goss'] == 0.0
        assert result['Random'] == 0.0