import pytest
import math
import numpy as np
from code.models.mclean import calculate_mclean_concentration, calculate_mclean_profile, validate_mclean_inputs
from code.errors import ValidationError, ConfigurationError

class TestMcLeanIsotherm:
    """Unit tests for the McLean isotherm calculation."""

    def test_validate_inputs_valid(self):
        """Test that valid inputs pass validation."""
        validate_mclean_inputs(
            segregation_energy_eV=-0.5,
            bulk_composition={"Fe": 0.9, "Cr": 0.1},
            temperature_K=600.0
        ) # Should not raise

    def test_validate_inputs_negative_temp(self):
        """Test that negative temperature raises error."""
        with pytest.raises(ValidationError):
            validate_mclean_inputs(
                segregation_energy_eV=-0.5,
                bulk_composition={"Fe": 0.9, "Cr": 0.1},
                temperature_K=-100.0
            )

    def test_validate_inputs_invalid_composition(self):
        """Test that composition not summing to 1.0 raises error."""
        with pytest.raises(ValidationError):
            validate_mclean_inputs(
                segregation_energy_eV=-0.5,
                bulk_composition={"Fe": 0.5, "Cr": 0.1}, # Sum = 0.6
                temperature_K=600.0
            )

    def test_calculate_concentration_basic(self):
        """Test basic concentration calculation."""
        # E_seg = -0.5 eV, T = 600K
        # X_bulk = 0.1
        # C = X_bulk * exp(-E_seg / (k_B * T))
        # k_B = 8.617333262e-5 eV/K
        # exp(0.5 / (8.617e-5 * 600)) ~ exp(9.66) ~ 15700
        # C ~ 0.1 * 15700 = 1570 -> Capped at 1.0
        
        result = calculate_mclean_concentration(
            segregation_energy_eV=-0.5,
            bulk_fraction=0.1,
            temperature_K=600.0
        )
        
        assert result <= 1.0
        assert result > 0.1 # Should be enriched

    def test_calculate_concentration_positive_energy(self):
        """Test that positive segregation energy leads to depletion."""
        result = calculate_mclean_concentration(
            segregation_energy_eV=0.5,
            bulk_fraction=0.1,
            temperature_K=600.0
        )
        
        assert result < 0.1

    def test_calculate_profile_structure(self):
        """Test that the profile function returns the expected structure."""
        profile = calculate_mclean_profile(
            segregation_energy_eV=-0.3,
            bulk_composition={"Fe": 0.9, "Cr": 0.1},
            temperature_K=600.0,
            num_sites=5
        )
        
        assert "profile" in profile
        assert "equilibrium_concentrations" in profile
        assert len(profile["profile"]) == 5
        assert "Cr" in profile["equilibrium_concentrations"]
        assert len(profile["equilibrium_concentrations"]["Cr"]) == 5

    def test_saturation_flagging(self):
        """Test that high enrichment triggers saturation flags."""
        # Very high segregation energy should saturate
        profile = calculate_mclean_profile(
            segregation_energy_eV=-2.0,
            bulk_composition={"Fe": 0.9, "Cr": 0.1},
            temperature_K=300.0,
            num_sites=5
        )
        
        # Check if saturation flags are present (T016 logic)
        # The function should return a list of flags
        assert "saturation_flags" in profile
        assert any(profile["saturation_flags"]) # At least one should be flagged
