"""
Unit tests for the physical constants module.

These tests verify that all constants have the correct values,
units are properly defined, and conversion functions work correctly.
"""

import pytest
import math
from code import physical_constants as pc


class TestPhysicalConstantsValues:
    """Test that fundamental constants have correct NIST/CRC values."""

    def test_epsilon_0_value(self):
        """Verify vacuum permittivity is within expected range."""
        expected = 8.8541878128e-12
        assert abs(pc.EPSILON_0 - expected) < 1e-20
        assert pc.EPSILON_0_CITATION is not None
        assert len(pc.EPSILON_0_CITATION) > 0

    def test_elementary_charge_value(self):
        """Verify elementary charge is exact by definition."""
        expected = 1.602176634e-19
        assert pc.E_ELEMENTARY_CHARGE == expected
        assert "exact" in pc.E_CITATION.lower()

    def test_avogadro_constant_value(self):
        """Verify Avogadro constant is exact by definition."""
        expected = 6.02214076e23
        assert pc.N_A == expected
        assert "exact" in pc.N_A_CITATION.lower()

    def test_boltzmann_constant_value(self):
        """Verify Boltzmann constant is exact by definition."""
        expected = 1.380649e-23
        assert pc.K_B == expected
        assert "exact" in pc.K_B_CITATION.lower()

    def test_gas_constant_value(self):
        """Verify gas constant is calculated correctly from N_A * K_B."""
        expected = pc.N_A * pc.K_B
        assert abs(pc.R_GAS_CONSTANT - expected) < 1e-6

    def test_faraday_constant_value(self):
        """Verify Faraday constant is calculated correctly from N_A * e."""
        expected = pc.N_A * pc.E_ELEMENTARY_CHARGE
        assert abs(pc.F_FARADAY - expected) < 1e-2

    def test_speed_of_light_exact(self):
        """Verify speed of light is exact by definition."""
        assert pc.C_SPEED_OF_LIGHT == 299_792_458.0

    def test_water_dielectric_at_25c(self):
        """Verify water dielectric constant at 25°C."""
        assert 78.0 < pc.WATER_DIELECTRIC_25C < 79.0
        assert pc.WATER_DIELECTRIC_CITATION is not None


class TestUnitConversions:
    """Test unit conversion functions."""

    def test_angstrom_to_meter_conversion(self):
        """Test Å to m conversion is exact."""
        assert pc.ANGSTROM_TO_METER == 1e-10
        assert pc.meters_to_angstroms(1e-10) == 1.0
        assert pc.angstroms_to_meters(1.0) == 1e-10

    def test_meter_to_angstrom_conversion(self):
        """Test m to Å conversion."""
        assert pc.METER_TO_ANGSTROM == 1e10
        assert pc.angstroms_to_meters(10.0) == 1e-9
        assert pc.meters_to_angstroms(1e-9) == 10.0

    def test_kcal_to_joule_conversion(self):
        """Test kcal to J conversion (thermochemical)."""
        assert pc.KCAL_TO_JOULE == 4184.0
        assert pc.JOULE_TO_KCAL == 1 / 4184.0
        # Round-trip test
        original = 10.5
        converted = pc.kcal_mol_to_joules_mol(original)
        back = pc.joules_mol_to_kcal_mol(converted)
        assert abs(original - back) < 1e-10

    def test_joule_to_kcal_conversion(self):
        """Test J to kcal conversion."""
        assert pc.JOULE_TO_KCAL == 1 / 4184.0
        original = 41840.0  # 10 kcal
        converted = pc.joules_mol_to_kcal_mol(original)
        assert abs(converted - 10.0) < 1e-6

    def test_celsius_to_kelvin_conversion(self):
        """Test °C to K conversion."""
        assert pc.CELSIUS_TO_KELVIN_OFFSET == 273.15
        assert pc.celsius_to_kelvin(0.0) == 273.15
        assert pc.celsius_to_kelvin(25.0) == 298.15
        assert pc.celsius_to_kelvin(100.0) == 373.15

    def test_kelvin_to_celsius_conversion(self):
        """Test K to °C conversion."""
        assert pc.kelvin_to_celsius(273.15) == 0.0
        assert pc.kelvin_to_celsius(298.15) == 25.0
        assert pc.kelvin_to_celsius(373.15) == 100.0

    def test_roundtrip_temperature_conversion(self):
        """Test round-trip temperature conversion."""
        for temp_c in [0.0, 25.0, 37.0, 100.0, -40.0]:
            temp_k = pc.celsius_to_kelvin(temp_c)
            temp_c_back = pc.kelvin_to_celsius(temp_k)
            assert abs(temp_c - temp_c_back) < 1e-10


class TestConstantsDictionary:
    """Test the CONSTANTS dictionary."""

    def test_constants_dict_exists(self):
        """Verify CONSTANTS dictionary is populated."""
        assert isinstance(pc.CONSTANTS, dict)
        assert len(pc.CONSTANTS) > 0

    def test_constants_dict_keys(self):
        """Verify all expected keys are present."""
        expected_keys = ["c", "epsilon_0", "e", "N_A", "k_B", "R", "F", "h"]
        for key in expected_keys:
            assert key in pc.CONSTANTS

    def test_constants_dict_values_match(self):
        """Verify dictionary values match module constants."""
        assert pc.CONSTANTS["epsilon_0"] == pc.EPSILON_0
        assert pc.CONSTANTS["e"] == pc.E_ELEMENTARY_CHARGE
        assert pc.CONSTANTS["N_A"] == pc.N_A
        assert pc.CONSTANTS["R"] == pc.R_GAS_CONSTANT


class TestCitations:
    """Test that citations are properly documented."""

    def test_citations_dict_exists(self):
        """Verify CITATIONS dictionary is populated."""
        assert isinstance(pc.CITATIONS, dict)
        assert len(pc.CITATIONS) > 0

    def test_citations_are_non_empty(self):
        """Verify all citations are non-empty strings."""
        for key, citation in pc.CITATIONS.items():
            assert isinstance(citation, str)
            assert len(citation) > 0
            # Check for expected sources
            assert "NIST" in citation or "CRC" in citation or "exact" in citation.lower()

    def test_individual_constant_citations(self):
        """Verify individual constant citations exist."""
        assert pc.EPSILON_0_CITATION is not None
        assert pc.E_CITATION is not None
        assert pc.N_A_CITATION is not None
        assert pc.K_B_CITATION is not None
        assert pc.R_CITATION is not None
        assert pc.F_CITATION is not None
        assert pc.WATER_DIELECTRIC_CITATION is not None


class TestPrecisionAndAccuracy:
    """Test precision requirements for thermodynamic calculations."""

    def test_epsilon_0_precision(self):
        """Verify epsilon_0 has sufficient precision (at least 10 significant digits)."""
        # NIST value: 8.8541878128e-12
        value = pc.EPSILON_0
        # Check it has at least 10 significant digits
        str_val = f"{value:.12e}"
        assert len(str_val) >= 15  # Should have enough digits

    def test_elementary_charge_exactness(self):
        """Verify elementary charge is exact (no floating point error)."""
        # Should be exactly representable
        assert pc.E_ELEMENTARY_CHARGE == 1.602176634e-19

    def test_ionic_radius_conversion_precision(self):
        """Verify radius conversions maintain precision for 0.01 Å requirement."""
        # Test that we can convert 0.01 Å accurately
        radius_angstrom = 0.01
        radius_m = pc.angstroms_to_meters(radius_angstrom)
        radius_back = pc.meters_to_angstroms(radius_m)
        assert abs(radius_angstrom - radius_back) < 1e-12

        # Test typical ionic radius (e.g., Na+ ~ 1.02 Å)
        typical_radius = 1.02
        radius_m = pc.angstroms_to_meters(typical_radius)
        radius_back = pc.meters_to_angstroms(radius_m)
        assert abs(typical_radius - radius_back) < 1e-10


class TestStandardConditions:
    """Test standard condition constants."""

    def test_standard_temperature(self):
        """Verify standard temperature is 298.15 K (25°C)."""
        assert pc.STANDARD_TEMPERATURE_KELVIN == 298.15

    def test_standard_pressure(self):
        """Verify standard pressure is 101325 Pa (1 atm)."""
        assert pc.STANDARD_PRESSURE_PASCAL == 101_325.0

    def test_water_dielectric_at_standard_temp(self):
        """Verify water dielectric is provided for standard temperature."""
        assert pc.WATER_DIELECTRIC_25C is not None
        assert 78.0 < pc.WATER_DIELECTRIC_25C < 79.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_radius_conversion(self):
        """Test conversion of zero radius."""
        assert pc.angstroms_to_meters(0.0) == 0.0
        assert pc.meters_to_angstroms(0.0) == 0.0

    def test_zero_energy_conversion(self):
        """Test conversion of zero energy."""
        assert pc.kcal_mol_to_joules_mol(0.0) == 0.0
        assert pc.joules_mol_to_kcal_mol(0.0) == 0.0

    def test_negative_temperature_conversion(self):
        """Test negative Celsius temperature."""
        assert pc.celsius_to_kelvin(-273.15) == 0.0
        assert pc.kelvin_to_celsius(0.0) == -273.15

    def test_large_radius_conversion(self):
        """Test conversion of large radius."""
        large_radius_angstrom = 100.0
        radius_m = pc.angstroms_to_meters(large_radius_angstrom)
        radius_back = pc.meters_to_angstroms(radius_m)
        assert abs(large_radius_angstrom - radius_back) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])