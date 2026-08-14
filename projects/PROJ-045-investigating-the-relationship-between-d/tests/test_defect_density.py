"""
Tests for Defect Density Quantification (T033).
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from dft_runner import calculate_defect_density, process_high_fidelity_subset

class TestDefectDensityCalculation:
    """Unit tests for the defect density calculation logic."""

    def test_calculate_defect_density_basic(self):
        """Test basic defect density calculation."""
        volume = 100.0  # Å^3
        num_defects = 1
        density = calculate_defect_density("test_comp", volume, num_defects)
        expected = 1.0 / 100.0
        assert abs(density - expected) < 1e-9

    def test_calculate_defect_density_multiple_defects(self):
        """Test calculation with multiple defects."""
        volume = 200.0
        num_defects = 4
        density = calculate_defect_density("test_comp", volume, num_defects)
        expected = 4.0 / 200.0
        assert abs(density - expected) < 1e-9

    def test_calculate_defect_density_zero_volume_raises(self):
        """Test that zero volume raises ValueError."""
        with pytest.raises(ValueError):
            calculate_defect_density("test_comp", 0.0, 1)

    def test_calculate_defect_density_negative_volume_raises(self):
        """Test that negative volume raises ValueError."""
        with pytest.raises(ValueError):
            calculate_defect_density("test_comp", -50.0, 1)

class TestDefectDensityMetricsOutput:
    """Integration tests for the output file generation."""

    def test_process_high_fidelity_subset_writes_json(self):
        """Test that the process function writes the correct JSON schema."""
        mock_compositions = [
            {"composition_id": "Li7La3Zr2O12", "volume": 500.0, "num_atoms": 40},
            {"composition_id": "Li10GeP2S12", "volume": 450.0, "num_atoms": 30}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            output_path = tmp.name

        try:
            results = process_high_fidelity_subset(mock_compositions, output_path)
            
            # Verify file exists
            assert os.path.exists(output_path), "Output file was not created."
            
            # Verify content
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            assert isinstance(data, list), "Output should be a list."
            assert len(data) == 2, "Should have 2 entries."
            
            for entry in data:
                assert "composition_id" in entry, "Missing composition_id"
                assert "defect_density" in entry, "Missing defect_density"
                assert "supercell_volume" in entry, "Missing supercell_volume"
                assert isinstance(entry["defect_density"], float), "defect_density must be float"
                assert isinstance(entry["supercell_volume"], float), "supercell_volume must be float"
                assert entry["defect_density"] > 0, "defect_density must be positive"
                assert entry["supercell_volume"] > 0, "supercell_volume must be positive"
        finally:
            # Cleanup
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_schema_compliance_with_verification(self):
        """
        Verify schema matches the requirement:
        {"composition_id": "string", "defect_density": "float", "supercell_volume": "float"}
        """
        mock_compositions = [
            {"composition_id": "TestSystem", "volume": 1000.0, "num_atoms": 100}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            output_path = tmp.name

        try:
            process_high_fidelity_subset(mock_compositions, output_path)
            
            with open(output_path, 'r') as f:
                data = json.load(f)
            
            # Verification step from task description
            assert 'defect_density' in data[0], "Verification failed: 'defect_density' missing in first entry"
            assert isinstance(data[0]['defect_density'], float), "Verification failed: 'defect_density' is not float"
            
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)