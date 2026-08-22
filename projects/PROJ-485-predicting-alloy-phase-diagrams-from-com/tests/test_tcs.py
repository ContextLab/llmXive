"""
Tests for Topological Consistency Score (TCS) calculation.

Verifies partial match ratio logic for T035.
"""

import pytest
import os
import sys
import tempfile
import csv
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.viz.topological_consistency import (
    extract_phase_boundaries,
    calculate_partial_match_ratio,
    calculate_tcs_from_files,
    calculate_tcs_from_results
)

from utils.error_codes import ErrorCode


class TestTCS:
    """Test suite for Topological Consistency Score calculation."""

    def test_extract_phase_boundaries_basic(self):
        """Test basic extraction of phase boundaries from data."""
        data = [
            {'composition_at%': '30', 'temperature_K': '1000', 'phase': 'alpha'},
            {'composition_at%': '30', 'temperature_K': '1200', 'phase': 'beta'},
            {'composition_at%': '50', 'temperature_K': '1100', 'phase': 'alpha'},
            {'composition_at%': '50', 'temperature_K': '1300', 'phase': 'gamma'},
        ]
        
        boundaries = extract_phase_boundaries(data)
        
        assert 30.0 in boundaries
        assert 50.0 in boundaries
        assert boundaries[30.0] == [1000.0, 1200.0]  # Sorted
        assert boundaries[50.0] == [1100.0, 1300.0]  # Sorted

    def test_extract_phase_boundaries_single_boundary(self):
        """Test extraction when only one boundary exists per composition."""
        data = [
            {'composition_at%': '40', 'temperature_K': '900', 'phase': 'liquid'},
            {'composition_at%': '60', 'temperature_K': '950', 'phase': 'liquid'},
        ]
        
        boundaries = extract_phase_boundaries(data)
        
        assert boundaries[40.0] == [900.0]
        assert boundaries[60.0] == [950.0]

    def test_partial_match_ratio_perfect_match(self):
        """Test perfect match scenario."""
        exp_boundaries = {
            30.0: [1000.0, 1200.0],
            50.0: [1100.0, 1300.0],
            70.0: [1050.0, 1250.0],
        }
        pred_boundaries = {
            30.0: [1000.0, 1200.0],
            50.0: [1100.0, 1300.0],
            70.0: [1050.0, 1250.0],
        }
        
        tcs, matching, total = calculate_partial_match_ratio(exp_boundaries, pred_boundaries)
        
        assert tcs == 1.0
        assert matching == 3
        assert total == 3

    def test_partial_match_ratio_no_match(self):
        """Test scenario with no matching boundaries."""
        exp_boundaries = {
            30.0: [1000.0, 1200.0],
            50.0: [1100.0, 1300.0],
        }
        pred_boundaries = {
            30.0: [1500.0, 1700.0],  # Far off
            50.0: [1600.0, 1800.0],  # Far off
        }
        
        tcs, matching, total = calculate_partial_match_ratio(
            exp_boundaries, pred_boundaries, tolerance=50.0
        )
        
        assert tcs == 0.0
        assert matching == 0
        assert total == 2

    def test_partial_match_ratio_partial_match(self):
        """Test scenario with partial matches."""
        exp_boundaries = {
            30.0: [1000.0, 1200.0],
            50.0: [1100.0, 1300.0],
            70.0: [1050.0, 1250.0],
        }
        pred_boundaries = {
            30.0: [1005.0, 1205.0],  # Within tolerance
            50.0: [1600.0, 1800.0],  # Outside tolerance
            70.0: [1050.0, 1250.0],  # Exact match
        }
        
        tcs, matching, total = calculate_partial_match_ratio(
            exp_boundaries, pred_boundaries, tolerance=50.0
        )
        
        assert tcs == 2.0 / 3.0  # 2 out of 3 match
        assert matching == 2
        assert total == 3

    def test_partial_match_ratio_boundary_count_mismatch(self):
        """Test when boundary counts don't match."""
        exp_boundaries = {
            30.0: [1000.0, 1200.0],  # 2 boundaries
            50.0: [1100.0, 1300.0, 1500.0],  # 3 boundaries
        }
        pred_boundaries = {
            30.0: [1000.0, 1200.0],  # 2 boundaries - match
            50.0: [1100.0, 1300.0],  # 2 boundaries - mismatch
        }
        
        tcs, matching, total = calculate_partial_match_ratio(
            exp_boundaries, pred_boundaries, tolerance=50.0
        )
        
        # Only composition 30.0 should match
        assert tcs == 1.0
        assert matching == 1
        assert total == 2

    def test_partial_match_ratio_no_common_compositions(self):
        """Test when there are no common compositions."""
        exp_boundaries = {30.0: [1000.0], 50.0: [1100.0]}
        pred_boundaries = {70.0: [1200.0], 90.0: [1300.0]}
        
        tcs, matching, total = calculate_partial_match_ratio(exp_boundaries, pred_boundaries)
        
        assert tcs == 0.0
        assert matching == 0
        assert total == 0

    def test_partial_match_ratio_tolerance_effect(self):
        """Test that tolerance parameter affects matching."""
        exp_boundaries = {30.0: [1000.0, 1200.0]}
        pred_boundaries = {30.0: [1040.0, 1240.0]}  # 40K difference
        
        # With 50K tolerance, should match
        tcs_50, _, _ = calculate_partial_match_ratio(
            exp_boundaries, pred_boundaries, tolerance=50.0
        )
        assert tcs_50 == 1.0
        
        # With 30K tolerance, should not match
        tcs_30, _, _ = calculate_partial_match_ratio(
            exp_boundaries, pred_boundaries, tolerance=30.0
        )
        assert tcs_30 == 0.0

    def test_calculate_tcs_from_results(self):
        """Test TCS calculation from in-memory data."""
        exp_data = [
            {'composition_at%': '30', 'temperature_K': '1000', 'phase': 'alpha'},
            {'composition_at%': '30', 'temperature_K': '1200', 'phase': 'beta'},
            {'composition_at%': '50', 'temperature_K': '1100', 'phase': 'alpha'},
            {'composition_at%': '50', 'temperature_K': '1300', 'phase': 'gamma'},
        ]
        
        pred_data = [
            {'composition_at%': '30', 'temperature_K': '1005', 'phase': 'alpha'},
            {'composition_at%': '30', 'temperature_K': '1205', 'phase': 'beta'},
            {'composition_at%': '50', 'temperature_K': '1105', 'phase': 'alpha'},
            {'composition_at%': '50', 'temperature_K': '1305', 'phase': 'gamma'},
        ]
        
        results = calculate_tcs_from_results(exp_data, pred_data, tolerance=50.0)
        
        assert results['tcs_score'] == 1.0
        assert results['matching_slices'] == 2
        assert results['total_slices'] == 2
        assert results['passes_threshold'] is True

    def test_tcs_threshold_check(self):
        """Test that TCS threshold (0.8) is correctly evaluated."""
        # Create data that results in exactly 0.8 TCS
        exp_data = [
            {'composition_at%': str(i), 'temperature_K': str(1000 + i*10), 'phase': 'alpha'}
            for i in range(5)
        ]
        pred_data = [
            {'composition_at%': str(i), 'temperature_K': str(1000 + i*10), 'phase': 'alpha'}
            for i in range(4)  # 4 out of 5 match
        ]
        
        results = calculate_tcs_from_results(exp_data, pred_data, tolerance=50.0)
        
        assert results['tcs_score'] == 0.8
        assert results['passes_threshold'] is True

    def test_tcs_below_threshold(self):
        """Test TCS below threshold."""
        exp_data = [
            {'composition_at%': str(i), 'temperature_K': str(1000 + i*10), 'phase': 'alpha'}
            for i in range(5)
        ]
        pred_data = [
            {'composition_at%': str(i), 'temperature_K': str(1500 + i*10), 'phase': 'alpha'}
            for i in range(5)  # None match
        ]
        
        results = calculate_tcs_from_results(exp_data, pred_data, tolerance=50.0)
        
        assert results['tcs_score'] == 0.0
        assert results['passes_threshold'] is False

    def test_calculate_tcs_from_files(self):
        """Test TCS calculation from CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = os.path.join(tmpdir, 'exp.csv')
            pred_path = os.path.join(tmpdir, 'pred.csv')
            out_path = os.path.join(tmpdir, 'results.json')
            
            # Write experimental data
            with open(exp_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['composition_at%', 'temperature_K', 'phase'])
                writer.writeheader()
                writer.writerows([
                    {'composition_at%': '30', 'temperature_K': '1000', 'phase': 'alpha'},
                    {'composition_at%': '30', 'temperature_K': '1200', 'phase': 'beta'},
                    {'composition_at%': '50', 'temperature_K': '1100', 'phase': 'alpha'},
                ])
            
            # Write predicted data (perfect match)
            with open(pred_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['composition_at%', 'temperature_K', 'phase'])
                writer.writeheader()
                writer.writerows([
                    {'composition_at%': '30', 'temperature_K': '1000', 'phase': 'alpha'},
                    {'composition_at%': '30', 'temperature_K': '1200', 'phase': 'beta'},
                    {'composition_at%': '50', 'temperature_K': '1100', 'phase': 'alpha'},
                ])
            
            results = calculate_tcs_from_files(exp_path, pred_path)
            
            assert results['tcs_score'] == 1.0
            assert results['matching_slices'] == 2
            assert results['total_slices'] == 2
            assert results['passes_threshold'] is True

    def test_tcs_with_different_column_names(self):
        """Test TCS calculation with custom column names."""
        data = [
            {'comp': '30', 'temp': '1000', 'ph': 'alpha'},
            {'comp': '30', 'temp': '1200', 'ph': 'beta'},
        ]
        
        boundaries = extract_phase_boundaries(
            data, 
            composition_col='comp',
            temperature_col='temp',
            phase_col='ph'
        )
        
        assert 30.0 in boundaries
        assert boundaries[30.0] == [1000.0, 1200.0]

    def test_tcs_empty_data(self):
        """Test TCS with empty data."""
        results = calculate_tcs_from_results([], [])
        
        assert results['tcs_score'] == 0.0
        assert results['total_slices'] == 0

    def test_tcs_single_composition(self):
        """Test TCS with single composition."""
        exp_data = [{'composition_at%': '50', 'temperature_K': '1000', 'phase': 'alpha'}]
        pred_data = [{'composition_at%': '50', 'temperature_K': '1000', 'phase': 'alpha'}]
        
        results = calculate_tcs_from_results(exp_data, pred_data)
        
        assert results['tcs_score'] == 1.0
        assert results['total_slices'] == 1

    def test_tcs_partial_match_ratio_formula(self):
        """
        Verify the partial match ratio formula:
        TCS = matching_slices / total_slices
        
        This is the core formula from Methodology Section 4, SC-004.
        """
        # Create scenario with known ratio
        exp_boundaries = {
            10.0: [1000.0],
            20.0: [1000.0],
            30.0: [1000.0],
            40.0: [1000.0],
            50.0: [1000.0],
        }
        pred_boundaries = {
            10.0: [1000.0],  # Match
            20.0: [1000.0],  # Match
            30.0: [1500.0],  # No match
            40.0: [1000.0],  # Match
            50.0: [1500.0],  # No match
        }
        
        tcs, matching, total = calculate_partial_match_ratio(
            exp_boundaries, pred_boundaries, tolerance=50.0
        )
        
        # 3 out of 5 match = 0.6
        assert tcs == 0.6
        assert matching == 3
        assert total == 5
        assert abs(tcs - matching/total) < 1e-9  # Verify formula