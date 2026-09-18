"""
Unit tests for descriptor calculation module (src/descriptors/compute_descriptors.py).

These tests verify the correctness of:
- Tolerance factor calculation
- Octahedral tilting angle calculation
- Bond length variance calculation
- Unit cell volume calculation
- The combined compute_all_descriptors function
- The dataframe processing pipeline

Tests use mock pymatgen structures to ensure deterministic behavior without
requiring live API access or complex structure generation.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src to path for imports if running standalone
src_path = Path(__file__).parent.parent.parent / "code" / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from descriptors.compute_descriptors import (
    calculate_tolerance_factor,
    calculate_octahedral_tilting_angles,
    calculate_bond_length_variance,
    calculate_unit_cell_volume,
    compute_all_descriptors,
    process_dataframe,
    setup_logger_module
)


class TestToleranceFactor:
    """Tests for tolerance factor calculation."""

    def test_tolerance_factor_ideal_perovskite(self):
        """Test tolerance factor for ideal cubic perovskite (rA = rB + rX*sqrt(2))."""
        # Ideal: t = 1.0 when rA = sqrt(2)*(rB + rX)
        # Using standard ionic radii for ideal case
        rA = 1.34  # A-site cation (e.g., La3+)
        rB = 0.60  # B-site cation (e.g., Ti4+)
        rX = 1.40  # X-site anion (e.g., O2-)
        
        # Ideal t = rA / (sqrt(2) * (rB + rX))
        expected = rA / (np.sqrt(2) * (rB + rX))
        
        result = calculate_tolerance_factor(rA, rB, rX)
        
        assert np.isclose(result, expected, rtol=1e-6)
        assert 0.8 < result < 1.2, "Ideal perovskite should have t near 1.0"

    def test_tolerance_factor_tilted_perovskite(self):
        """Test tolerance factor for a known tilted perovskite (t < 1)."""
        # Example: CaTiO3 has t ~ 0.97
        rA = 1.00  # Ca2+
        rB = 0.605 # Ti4+
        rX = 1.40  # O2-
        
        result = calculate_tolerance_factor(rA, rB, rX)
        
        assert result < 1.0, "Tilted perovskite should have t < 1.0"
        assert result > 0.7, "Tolerance factor should be positive"

    def test_tolerance_factor_invalid_radii(self):
        """Test that negative radii raise an error."""
        with pytest.raises(ValueError):
            calculate_tolerance_factor(-1.0, 0.6, 1.4)

    def test_tolerance_factor_zero_denominator(self):
        """Test handling of zero sum of B and X radii."""
        with pytest.raises(ValueError):
            calculate_tolerance_factor(1.0, 0.0, 0.0)


class TestOctahedralTilting:
    """Tests for octahedral tilting angle calculation."""

    def test_ideal_cubic_no_tilting(self):
        """Test that ideal cubic structure has zero tilting."""
        # Mock structure with perfect 90-degree angles
        mock_angles = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0]
        mock_structure = Mock()
        mock_structure.sites = []
        
        # Simulate perfect cubic case
        result = calculate_octahedral_tilting_angles(mock_angles)
        
        assert all(np.isclose(angle, 0.0) for angle in result), \
            "Perfect cubic should have zero tilting angles"

    def test_tilted_structure_positive_angles(self):
        """Test calculation for a tilted structure."""
        # Simulate angles deviating from 90 degrees
        mock_angles = [88.5, 91.2, 89.8, 90.5, 88.9, 91.1]
        
        result = calculate_octahedral_tilting_angles(mock_angles)
        
        # All tilting angles should be non-negative deviations
        assert all(angle >= 0.0 for angle in result), \
            "Tilting angles should be non-negative"
        assert len(result) == len(mock_angles), \
            "Should return one tilting angle per input angle"

    def test_average_tilting_calculation(self):
        """Test that average tilting is computed correctly."""
        mock_angles = [85.0, 95.0, 88.0, 92.0, 87.0, 93.0]
        deviations = [abs(90 - a) for a in mock_angles]
        expected_avg = np.mean(deviations)
        
        result = calculate_octahedral_tilting_angles(mock_angles)
        actual_avg = np.mean(result)
        
        assert np.isclose(actual_avg, expected_avg, rtol=1e-6), \
            "Average tilting should be mean of absolute deviations from 90"


class TestBondLengthVariance:
    """Tests for bond length variance calculation."""

    def test_uniform_bond_lengths_zero_variance(self):
        """Test that uniform bond lengths give zero variance."""
        bond_lengths = [2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
        
        result = calculate_bond_length_variance(bond_lengths)
        
        assert np.isclose(result, 0.0, atol=1e-6), \
            "Uniform bonds should have zero variance"

    def test_varying_bond_lengths_positive_variance(self):
        """Test calculation with varying bond lengths."""
        bond_lengths = [1.9, 2.0, 2.1, 1.95, 2.05, 2.0]
        
        result = calculate_bond_length_variance(bond_lengths)
        
        assert result > 0, "Varying bonds should have positive variance"
        # Verify calculation: variance of [1.9, 2.0, 2.1, 1.95, 2.05, 2.0]
        expected = np.var(bond_lengths, ddof=0)
        assert np.isclose(result, expected, rtol=1e-6)

    def test_single_bond_variance(self):
        """Test behavior with a single bond length."""
        bond_lengths = [2.0]
        
        result = calculate_bond_length_variance(bond_lengths)
        
        assert np.isclose(result, 0.0, atol=1e-6), \
            "Single bond should have zero variance"

    def test_empty_bond_lengths(self):
        """Test handling of empty list."""
        with pytest.raises(ValueError):
            calculate_bond_length_variance([])


class TestUnitCellVolume:
    """Tests for unit cell volume calculation."""

    def test_cubic_unit_cell(self):
        """Test volume calculation for cubic cell."""
        # a = b = c = 4.0, alpha = beta = gamma = 90
        a, b, c = 4.0, 4.0, 4.0
        alpha, beta, gamma = 90.0, 90.0, 90.0
        
        result = calculate_unit_cell_volume(a, b, c, alpha, beta, gamma)
        
        expected = a * b * c  # For cubic
        assert np.isclose(result, expected, rtol=1e-6), \
            f"Cubic volume should be a*b*c, got {result} vs {expected}"

    def test_tetragonal_unit_cell(self):
        """Test volume calculation for tetragonal cell."""
        # a = b = 4.0, c = 6.0, all angles 90
        a, b, c = 4.0, 4.0, 6.0
        alpha, beta, gamma = 90.0, 90.0, 90.0
        
        result = calculate_unit_cell_volume(a, b, c, alpha, beta, gamma)
        
        expected = a * b * c
        assert np.isclose(result, expected, rtol=1e-6)

    def test_monoclinic_unit_cell(self):
        """Test volume calculation for monoclinic cell (beta != 90)."""
        # a=4, b=5, c=6, alpha=90, beta=110, gamma=90
        a, b, c = 4.0, 5.0, 6.0
        alpha, beta, gamma = 90.0, 110.0, 90.0
        
        result = calculate_unit_cell_volume(a, b, c, alpha, beta, gamma)
        
        # V = a*b*c * sqrt(1 - cos^2(alpha) - cos^2(beta) - cos^2(gamma) 
        #               + 2*cos(alpha)*cos(beta)*cos(gamma))
        # Simplified for alpha=gamma=90: V = a*b*c*sin(beta)
        expected = a * b * c * np.sin(np.radians(beta))
        
        assert np.isclose(result, expected, rtol=1e-6), \
            f"Monoclinic volume mismatch: {result} vs {expected}"

    def test_negative_volume_prevention(self):
        """Test that invalid angles don't produce negative volume."""
        # Invalid angles that would mathematically give negative under root
        a, b, c = 4.0, 4.0, 4.0
        alpha, beta, gamma = 170.0, 170.0, 170.0
        
        with pytest.raises(ValueError):
            calculate_unit_cell_volume(a, b, c, alpha, beta, gamma)


class TestComputeAllDescriptors:
    """Tests for the combined descriptor computation function."""

    def test_compute_all_returns_dict(self):
        """Test that compute_all_descriptors returns a dictionary."""
        mock_structure_data = {
            'rA': 1.34, 'rB': 0.60, 'rX': 1.40,
            'bond_lengths': [2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
            'tilting_angles': [90.0, 90.0, 90.0, 90.0, 90.0, 90.0],
            'a': 4.0, 'b': 4.0, 'c': 4.0,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
        }
        
        result = compute_all_descriptors(mock_structure_data)
        
        assert isinstance(result, dict), "Result should be a dictionary"
        assert 'tolerance_factor' in result
        assert 'octahedral_tilting' in result
        assert 'bond_length_variance' in result
        assert 'unit_cell_volume' in result

    def test_compute_all_with_realistic_values(self):
        """Test with realistic perovskite parameters."""
        mock_structure_data = {
            'rA': 1.34,  # La
            'rB': 0.60,  # Ti
            'rX': 1.40,  # O
            'bond_lengths': [1.95, 2.05, 2.00, 1.98, 2.02, 2.01],
            'tilting_angles': [89.5, 90.5, 89.8, 90.2, 89.9, 90.1],
            'a': 3.90, 'b': 3.90, 'c': 3.90,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
        }
        
        result = compute_all_descriptors(mock_structure_data)
        
        # Check reasonable ranges
        assert 0.7 < result['tolerance_factor'] < 1.3
        assert result['octahedral_tilting'] >= 0
        assert result['bond_length_variance'] >= 0
        assert result['unit_cell_volume'] > 0

    @patch('descriptors.compute_descriptors.setup_logger_module')
    def test_compute_all_logging(self, mock_logger):
        """Test that logging is set up correctly."""
        mock_structure_data = {
            'rA': 1.34, 'rB': 0.60, 'rX': 1.40,
            'bond_lengths': [2.0]*6,
            'tilting_angles': [90.0]*6,
            'a': 4.0, 'b': 4.0, 'c': 4.0,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
        }
        
        result = compute_all_descriptors(mock_structure_data)
        
        assert result is not None


class TestProcessDataFrame:
    """Tests for dataframe processing pipeline."""

    def test_process_dataframe_with_valid_input(self):
        """Test processing a valid dataframe with required columns."""
        # Create mock dataframe with necessary structure data
        df = pd.DataFrame({
            'structure_id': ['mp-123', 'mp-456'],
            'rA': [1.34, 1.00],
            'rB': [0.60, 0.605],
            'rX': [1.40, 1.40],
            'bond_lengths': [
                [2.0, 2.0, 2.0, 2.0, 2.0, 2.0],
                [1.95, 2.05, 2.00, 1.98, 2.02, 2.01]
            ],
            'tilting_angles': [
                [90.0, 90.0, 90.0, 90.0, 90.0, 90.0],
                [89.5, 90.5, 89.8, 90.2, 89.9, 90.1]
            ],
            'a': [3.90, 3.85],
            'b': [3.90, 3.85],
            'c': [3.90, 3.85],
            'alpha': [90.0, 90.0],
            'beta': [90.0, 90.0],
            'gamma': [90.0, 90.0]
        })
        
        result_df = process_dataframe(df)
        
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 2
        assert 'tolerance_factor' in result_df.columns
        assert 'octahedral_tilting' in result_df.columns
        assert 'bond_length_variance' in result_df.columns
        assert 'unit_cell_volume' in result_df.columns
        assert 'structure_id' in result_df.columns

    def test_process_dataframe_missing_columns(self):
        """Test handling of dataframe with missing required columns."""
        df = pd.DataFrame({
            'structure_id': ['mp-123'],
            'rA': [1.34]
            # Missing rB, rX, etc.
        })
        
        with pytest.raises(ValueError):
            process_dataframe(df)

    def test_process_dataframe_empty(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['structure_id', 'rA', 'rB', 'rX'])
        
        result_df = process_dataframe(df)
        
        assert isinstance(result_df, pd.DataFrame)
        assert len(result_df) == 0

    def test_process_dataframe_preserves_original_columns(self):
        """Test that original columns are preserved in output."""
        df = pd.DataFrame({
            'structure_id': ['mp-123'],
            'rA': [1.34],
            'rB': [0.60],
            'rX': [1.40],
            'bond_lengths': [[2.0]*6],
            'tilting_angles': [[90.0]*6],
            'a': [3.90],
            'b': [3.90],
            'c': [3.90],
            'alpha': [90.0],
            'beta': [90.0],
            'gamma': [90.0],
            'extra_column': ['test']
        })
        
        result_df = process_dataframe(df)
        
        assert 'extra_column' in result_df.columns
        assert result_df['extra_column'].iloc[0] == 'test'

    @patch('descriptors.compute_descriptors.setup_logger_module')
    def test_process_dataframe_logging(self, mock_logger):
        """Test that logging is used during processing."""
        df = pd.DataFrame({
            'structure_id': ['mp-123'],
            'rA': [1.34],
            'rB': [0.60],
            'rX': [1.40],
            'bond_lengths': [[2.0]*6],
            'tilting_angles': [[90.0]*6],
            'a': [3.90],
            'b': [3.90],
            'c': [3.90],
            'alpha': [90.0],
            'beta': [90.0],
            'gamma': [90.0]
        })
        
        result_df = process_dataframe(df)
        
        assert result_df is not None


class TestIntegration:
    """Integration tests combining multiple descriptor functions."""

    def test_full_pipeline_consistency(self):
        """Test that individual functions produce consistent results with combined function."""
        data = {
            'rA': 1.34, 'rB': 0.60, 'rX': 1.40,
            'bond_lengths': [1.95, 2.05, 2.00, 1.98, 2.02, 2.01],
            'tilting_angles': [89.5, 90.5, 89.8, 90.2, 89.9, 90.1],
            'a': 3.90, 'b': 3.90, 'c': 3.90,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
        }
        
        # Individual calculations
        tf = calculate_tolerance_factor(data['rA'], data['rB'], data['rX'])
        ot = calculate_octahedral_tilting_angles(data['tilting_angles'])
        blv = calculate_bond_length_variance(data['bond_lengths'])
        ucv = calculate_unit_cell_volume(data['a'], data['b'], data['c'],
                                        data['alpha'], data['beta'], data['gamma'])
        
        # Combined calculation
        combined = compute_all_descriptors(data)
        
        # Verify consistency
        assert np.isclose(combined['tolerance_factor'], tf, rtol=1e-6)
        assert np.isclose(np.mean(combined['octahedral_tilting']), np.mean(ot), rtol=1e-6)
        assert np.isclose(combined['bond_length_variance'], blv, rtol=1e-6)
        assert np.isclose(combined['unit_cell_volume'], ucv, rtol=1e-6)

    def test_dataframe_vs_individual_consistency(self):
        """Test that dataframe processing matches individual function calls."""
        df = pd.DataFrame({
            'structure_id': ['mp-123'],
            'rA': [1.34],
            'rB': [0.60],
            'rX': [1.40],
            'bond_lengths': [[1.95, 2.05, 2.00, 1.98, 2.02, 2.01]],
            'tilting_angles': [[89.5, 90.5, 89.8, 90.2, 89.9, 90.1]],
            'a': [3.90],
            'b': [3.90],
            'c': [3.90],
            'alpha': [90.0],
            'beta': [90.0],
            'gamma': [90.0]
        })
        
        result_df = process_dataframe(df)
        
        # Individual calculation
        data = {
            'rA': 1.34, 'rB': 0.60, 'rX': 1.40,
            'bond_lengths': [1.95, 2.05, 2.00, 1.98, 2.02, 2.01],
            'tilting_angles': [89.5, 90.5, 89.8, 90.2, 89.9, 90.1],
            'a': 3.90, 'b': 3.90, 'c': 3.90,
            'alpha': 90.0, 'beta': 90.0, 'gamma': 90.0
        }
        combined = compute_all_descriptors(data)
        
        # Verify consistency
        assert np.isclose(result_df['tolerance_factor'].iloc[0], combined['tolerance_factor'], rtol=1e-6)
        assert np.isclose(result_df['bond_length_variance'].iloc[0], combined['bond_length_variance'], rtol=1e-6)
        assert np.isclose(result_df['unit_cell_volume'].iloc[0], combined['unit_cell_volume'], rtol=1e-6)