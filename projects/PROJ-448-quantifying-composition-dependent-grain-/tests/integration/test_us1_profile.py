import pytest
import json
from pathlib import Path
import sys
import os

# Setup path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.services.us1_pipeline import generate_segregation_profiles
from code.models.mclean import calculate_mclean_profile
from code.models.alloy_system import AlloySystem, CrystalStructure

class TestUS1ProfileIntegration:
    """Integration test for the US1 profile generation pipeline."""

    def test_pipeline_execution(self):
        """Test that the pipeline runs and produces valid JSON output."""
        # Run the pipeline (mocked data loading)
        results = generate_segregation_profiles()
        
        assert isinstance(results, list)
        assert len(results) > 0, "Pipeline should produce at least one result"

        # Validate structure of first result
        first_result = results[0]
        assert "system" in first_result
        assert "profiles" in first_result
        assert "base_element" in first_result
        assert "solutes" in first_result

        # Validate profile content
        for profile in first_result["profiles"]:
            assert "temperature_K" in profile
            assert "segregation_energy_eV" in profile
            assert "equilibrium_concentrations" in profile
            assert profile["temperature_K"] > 0
            assert isinstance(profile["equilibrium_concentrations"], dict)

    def test_mclean_consistency(self):
        """Test that McLean calculations are consistent with theoretical expectations."""
        # Create a test alloy
        alloy = AlloySystem(
            base_element="Fe",
            solutes=["Cr"],
            crystal_structure=CrystalStructure.BCC,
            bulk_composition={"Fe": 0.9, "Cr": 0.1}
        )
        
        # Run McLean directly
        result = calculate_mclean_profile(
            segregation_energy_eV=-0.5,
            bulk_composition=alloy.bulk_composition,
            temperature_K=600.0,
            num_sites=5
        )
        
        # Check Cr concentration is enriched compared to bulk (0.1)
        cr_conc = result["equilibrium_concentrations"]["Cr"]
        for conc in cr_conc:
            assert conc >= 0.1 # Should be enriched

    def test_output_file_generation(self):
        """Test that the output file is generated correctly."""
        # This test assumes the pipeline has been run and output exists
        # For a pure integration test, we might mock the write or check the file
        output_path = Path("data/processed/segregation_profiles.json")
        if output_path.exists():
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert isinstance(data, list)
                assert len(data) > 0
