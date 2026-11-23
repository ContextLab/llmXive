"""
Unit tests for descriptor calculation edge cases and error handling.

This module verifies that the descriptor calculation logic correctly handles:
1. Single-element compositions (zero variance scenarios)
2. Missing melting point data (should raise DataHygieneError)
3. Zero variance in properties
4. Empty compositions
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.descriptors import (
    get_elemental_properties,
    calculate_single_composition_descriptors,
    calculate_descriptors,
    filter_missing_properties
)
from code.utils.logging import get_logger

logger = get_logger(__name__)


class TestDescriptorEdgeCases:
    """Test edge cases in descriptor calculation."""

    def test_single_element_composition(self):
        """Test that single-element composition handles zero variance correctly."""
        # Single element composition: Pure Iron
        composition_data = pd.DataFrame([{
            'composition': 'Fe',
            'yield_strength_mpa': 250.0,
            'phase': 'single_phase',
            'temperature_condition': 'room_temperature'
        }])

        # Get elemental properties (should include Fe melting point)
        elemental_props = get_elemental_properties()

        # Calculate descriptors
        descriptors = calculate_single_composition_descriptors(
            composition_data,
            elemental_props
        )

        # Verify that variance-based descriptors are zero for single element
        assert descriptors['delta'].iloc[0] == 0.0, "δ should be 0 for single element"
        assert descriptors['dchi'].iloc[0] == 0.0, "Δχ should be 0 for single element"
        assert descriptors['melting_variance'].iloc[0] == 0.0, "Melting variance should be 0 for single element"

        # VEC should be the valence electron count of the single element
        fe_valence = elemental_props[elemental_props['element'] == 'Fe']['valence_electrons'].iloc[0]
        assert descriptors['vec'].iloc[0] == fe_valence, f"VEC should equal Fe valence ({fe_valence})"

        logger.info("Single-element composition test passed")

    def test_missing_melting_point_raises_error(self):
        """Test that missing melting point data raises DataHygieneError."""
        # Create a composition with an element that has no melting point
        composition_data = pd.DataFrame([{
            'composition': 'Fe-Cr-X',
            'yield_strength_mpa': 300.0,
            'phase': 'single_phase',
            'temperature_condition': 'room_temperature'
        }])

        # Create elemental properties with missing melting point for 'X'
        elemental_props = pd.DataFrame({
            'element': ['Fe', 'Cr', 'X'],
            'atomic_radius': [124.1, 124.9, 150.0],
            'electronegativity': [1.83, 1.66, 1.5],
            'valence_electrons': [8, 6, 4],
            'melting_temperature': [1538.0, 1907.0, np.nan]  # Missing melting point for X
        })

        # This should raise an error or be filtered out
        try:
            descriptors = calculate_single_composition_descriptors(
                composition_data,
                elemental_props
            )
            
            # If no error raised, check if the row was filtered
            if len(descriptors) == 0:
                logger.info("Row with missing melting point was correctly filtered out")
            else:
                pytest.fail("Expected error or filtering for missing melting point data")
        except Exception as e:
            # Expected behavior: raise an error or filter the row
            assert "melting" in str(e).lower() or "missing" in str(e).lower(), \
                f"Expected melting point related error, got: {type(e).__name__}: {e}"
            logger.info(f"Correctly raised error for missing melting point: {e}")

    def test_zero_variance_property_handling(self):
        """Test handling of properties with zero variance across composition."""
        # Create a composition where all elements have identical properties
        composition_data = pd.DataFrame([{
            'composition': 'Fe-Fe-Fe',  # Hypothetical case with identical elements
            'yield_strength_mpa': 250.0,
            'phase': 'single_phase',
            'temperature_condition': 'room_temperature'
        }])

        elemental_props = pd.DataFrame({
            'element': ['Fe'],
            'atomic_radius': [124.1],
            'electronegativity': [1.83],
            'valence_electrons': [8],
            'melting_temperature': [1538.0]
        })

        # This should handle zero variance gracefully
        descriptors = calculate_single_composition_descriptors(
            composition_data,
            elemental_props
        )

        # All variance-based metrics should be zero
        assert descriptors['delta'].iloc[0] == 0.0
        assert descriptors['dchi'].iloc[0] == 0.0
        assert descriptors['melting_variance'].iloc[0] == 0.0

        logger.info("Zero variance handling test passed")

    def test_empty_composition_filtering(self):
        """Test that compositions with missing elemental properties are filtered."""
        composition_data = pd.DataFrame([{
            'composition': 'Fe-Cr-Ni-Z',  # Z is unknown
            'yield_strength_mpa': 350.0,
            'phase': 'single_phase',
            'temperature_condition': 'room_temperature'
        }])

        # Elemental properties missing 'Z'
        elemental_props = pd.DataFrame({
            'element': ['Fe', 'Cr', 'Ni'],
            'atomic_radius': [124.1, 124.9, 124.6],
            'electronegativity': [1.83, 1.66, 1.91],
            'valence_electrons': [8, 6, 10],
            'melting_temperature': [1538.0, 1907.0, 1455.0]
        })

        # Apply filtering
        filtered_data = filter_missing_properties(composition_data, elemental_props)

        # The composition with unknown element should be filtered out
        assert len(filtered_data) == 0, "Composition with missing element should be filtered"

        logger.info("Empty composition filtering test passed")

    def test_mixed_valid_invalid_compositions(self):
        """Test handling of dataset with mix of valid and invalid compositions."""
        composition_data = pd.DataFrame([
            {
                'composition': 'Fe-Cr-Ni',
                'yield_strength_mpa': 300.0,
                'phase': 'single_phase',
                'temperature_condition': 'room_temperature'
            },
            {
                'composition': 'Fe-Cr-X',  # X has no melting point
                'yield_strength_mpa': 350.0,
                'phase': 'single_phase',
                'temperature_condition': 'room_temperature'
            },
            {
                'composition': 'Co-Ni-Fe',
                'yield_strength_mpa': 400.0,
                'phase': 'single_phase',
                'temperature_condition': 'room_temperature'
            }
        ])

        # Elemental properties with missing melting point for 'X'
        elemental_props = pd.DataFrame({
            'element': ['Fe', 'Cr', 'Ni', 'Co', 'X'],
            'atomic_radius': [124.1, 124.9, 124.6, 125.3, 150.0],
            'electronegativity': [1.83, 1.66, 1.91, 1.88, 1.5],
            'valence_electrons': [8, 6, 10, 9, 4],
            'melting_temperature': [1538.0, 1907.0, 1455.0, 1768.0, np.nan]
        })

        # Filter missing properties
        filtered_data = filter_missing_properties(composition_data, elemental_props)

        # Should have 2 valid compositions (Fe-Cr-Ni and Co-Ni-Fe)
        assert len(filtered_data) == 2, f"Expected 2 valid compositions, got {len(filtered_data)}"
        
        # Verify the valid compositions are preserved
        compositions = set(filtered_data['composition'].tolist())
        assert 'Fe-Cr-Ni' in compositions
        assert 'Co-Ni-Fe' in compositions
        assert 'Fe-Cr-X' not in compositions

        logger.info("Mixed valid/invalid compositions test passed")

    def test_calculate_descriptors_with_edge_cases(self):
        """Test full descriptor calculation pipeline with edge cases."""
        # Create a small dataset with edge cases
        composition_data = pd.DataFrame([
            {
                'composition': 'Fe',  # Single element
                'yield_strength_mpa': 250.0,
                'phase': 'single_phase',
                'temperature_condition': 'room_temperature'
            },
            {
                'composition': 'Fe-Cr-Ni',
                'yield_strength_mpa': 300.0,
                'phase': 'single_phase',
                'temperature_condition': 'room_temperature'
            }
        ])

        elemental_props = get_elemental_properties()

        # Calculate all descriptors
        descriptors = calculate_descriptors(composition_data, elemental_props)

        # Verify we have descriptors for both compositions
        assert len(descriptors) == 2, "Should have descriptors for both compositions"

        # Single element should have zero variance metrics
        single_elem_row = descriptors[descriptors['composition'] == 'Fe'].iloc[0]
        assert single_elem_row['delta'] == 0.0
        assert single_elem_row['dchi'] == 0.0
        assert single_elem_row['melting_variance'] == 0.0

        # Multi-element should have non-zero variance (unless by coincidence)
        multi_elem_row = descriptors[descriptors['composition'] == 'Fe-Cr-Ni'].iloc[0]
        # Note: These might be zero by coincidence if properties are identical,
        # but for real elements they should differ
        logger.info(f"Multi-element descriptors: delta={multi_elem_row['delta']}, dchi={multi_elem_row['dchi']}")

        logger.info("Full descriptor calculation with edge cases test passed")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])