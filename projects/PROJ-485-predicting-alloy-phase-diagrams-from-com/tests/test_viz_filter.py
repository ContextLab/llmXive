"""
Tests for T038: Exclude complex/metastable systems from visualization.

Verification: Assert Fe-C is not in the generated plots list.
Constraint: Visualization must be limited to 'simple binary systems' (e.g., Cu-Zn, Al-Cu).
"""
import os
import sys
import json
import tempfile
import pytest
from typing import List, Set

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from viz.filter_systems import (
    is_complex_system,
    filter_systems_for_visualization,
    filter_processed_data_by_system,
    verify_exclusion,
    run_filter_systems,
    COMPLEX_SYSTEMS
)


class TestSystemFiltering:
    """Test cases for system filtering functionality."""

    def test_fe_c_is_complex(self):
        """Verify that Fe-C is correctly identified as a complex system."""
        assert is_complex_system("Fe-C") is True
        assert is_complex_system("fe-c") is True
        assert is_complex_system("FE-C") is True

    def test_simple_systems_are_not_complex(self):
        """Verify that simple binary systems are not flagged as complex."""
        simple_systems = ["Cu-Zn", "Al-Cu", "Cu-Al", "Ni-Fe", "Al-Mg"]
        for system in simple_systems:
            assert is_complex_system(system) is False, f"{system} should not be complex"

    def test_filter_excludes_fe_c(self):
        """Verify that Fe-C is excluded from the filtered list."""
        input_systems = ["Cu-Zn", "Al-Cu", "Fe-C", "Cu-Al"]
        filtered = filter_systems_for_visualization(input_systems)
        
        assert "Fe-C" not in filtered
        assert "Cu-Zn" in filtered
        assert "Al-Cu" in filtered
        assert "Cu-Al" in filtered

    def test_filter_excludes_all_complex_systems(self):
        """Verify that all known complex systems are excluded."""
        complex_systems_list = list(COMPLEX_SYSTEMS)
        simple_systems_list = ["Cu-Zn", "Al-Cu", "Ni-Fe"]
        input_systems = complex_systems_list + simple_systems_list
        
        filtered = filter_systems_for_visualization(input_systems)
        
        # Verify no complex systems in output
        for complex_sys in complex_systems_list:
            assert complex_sys not in filtered, f"{complex_sys} should be excluded"
        
        # Verify simple systems are present
        for simple_sys in simple_systems_list:
            assert simple_sys in filtered, f"{simple_sys} should be included"

    def test_verify_exclusion_passes(self):
        """Verify that verification passes when no complex systems are present."""
        systems = ["Cu-Zn", "Al-Cu", "Ni-Fe"]
        assert verify_exclusion(systems) is True

    def test_verify_exclusion_fails_with_complex(self):
        """Verify that verification fails when complex systems are present."""
        systems = ["Cu-Zn", "Fe-C", "Al-Cu"]
        assert verify_exclusion(systems) is False

    def test_filter_processed_data(self):
        """Verify filtering of processed data by system ID."""
        data = [
            {"system_id": "Cu-Zn", "temperature": 500, "composition": 0.5},
            {"system_id": "Fe-C", "temperature": 600, "composition": 0.3},
            {"system_id": "Al-Cu", "temperature": 400, "composition": 0.7},
            {"system_id": "Fe-N", "temperature": 700, "composition": 0.2},
        ]
        
        allowed_systems = ["Cu-Zn", "Al-Cu"]
        filtered = filter_processed_data_by_system(data, allowed_systems)
        
        assert len(filtered) == 2
        assert all(row["system_id"] in allowed_systems for row in filtered)

    def test_run_filter_systems_with_output_file(self):
        """Verify that run_filter_systems writes output file correctly."""
        input_systems = ["Cu-Zn", "Fe-C", "Al-Cu", "Fe-N"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_file = f.name
        
        try:
            filtered = run_filter_systems(
                input_systems=input_systems,
                output_file=output_file
            )
            
            assert "Fe-C" not in filtered
            assert "Fe-N" not in filtered
            assert "Cu-Zn" in filtered
            assert "Al-Cu" in filtered
            
            # Verify file contents
            with open(output_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data == filtered
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)

    def test_empty_input_list(self):
        """Verify handling of empty input list."""
        filtered = filter_systems_for_visualization([])
        assert filtered == []

    def test_all_complex_input(self):
        """Verify handling when all inputs are complex systems."""
        input_systems = ["Fe-C", "Fe-N", "Ti-C"]
        filtered = filter_systems_for_visualization(input_systems)
        assert filtered == []

    def test_case_insensitive_comparison(self):
        """Verify that system comparison is case-insensitive."""
        input_systems = ["fe-c", "FE-C", "Fe-C", "cu-zn", "Cu-Zn"]
        filtered = filter_systems_for_visualization(input_systems)
        
        assert len(filtered) == 1  # Only Cu-Zn should remain
        assert "cu-zn" in filtered or "Cu-Zn" in filtered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])