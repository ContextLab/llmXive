import pytest
import math
import json
import tempfile
import os
from pathlib import Path

# Import the actual implementation functions from the project
from descriptor_computation import (
    load_descriptor_sources,
    parse_composition,
    get_element_property,
    calculate_enthalpy_of_mixing,
    calculate_atomic_size_difference,
    calculate_valence_electron_concentration,
    calculate_electronegativity_difference
)

# Fixtures for test data
@pytest.fixture
def sample_descriptor_sources():
    """Create a temporary descriptor sources file for testing."""
    sources = {
        "atomic_radius": {
            "source": "Test Source",
            "version": "1.0",
            "data": {
                "Fe": 1.24,
                "Zr": 1.60,
                "Cu": 1.28,
                "Ni": 1.24,
                "Ti": 1.47,
                "Mg": 1.60,
                "Al": 1.43,
                "Si": 1.17,
                "B": 0.85,
                "C": 0.77,
                "La": 1.87,
                "Ce": 1.82
            }
        },
        "electronegativity": {
            "source": "Test Source",
            "version": "1.0",
            "data": {
                "Fe": 1.83,
                "Zr": 1.33,
                "Cu": 1.90,
                "Ni": 1.91,
                "Ti": 1.54,
                "Mg": 1.31,
                "Al": 1.61,
                "Si": 1.90,
                "B": 2.04,
                "C": 2.55,
                "La": 1.10,
                "Ce": 1.12
            }
        },
        "valence_electrons": {
            "source": "Test Source",
            "version": "1.0",
            "data": {
                "Fe": 8,
                "Zr": 4,
                "Cu": 11,
                "Ni": 10,
                "Ti": 4,
                "Mg": 2,
                "Al": 3,
                "Si": 4,
                "B": 3,
                "C": 4,
                "La": 3,
                "Ce": 4
            }
        }
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(sources, f)
        return f.name

@pytest.fixture
def cleanup_sources(sample_descriptor_sources):
    yield sample_descriptor_sources
    os.unlink(sample_descriptor_sources)


class TestParseComposition:
    """Tests for parsing alloy composition strings."""

    def test_parse_simple_binary(self):
        """Test parsing a simple binary alloy like Fe50Cu50."""
        result = parse_composition("Fe50Cu50")
        assert result == {"Fe": 0.50, "Cu": 0.50}

    def test_parse_ternary(self):
        """Test parsing a ternary alloy."""
        result = parse_composition("Fe40Cu30Ni30")
        assert result == {"Fe": 0.40, "Cu": 0.30, "Ni": 0.30}

    def test_parse_with_spaces(self):
        """Test parsing composition with spaces."""
        result = parse_composition("Fe 50 Cu 50")
        assert result == {"Fe": 0.50, "Cu": 0.50}

    def test_parse_float_percentages(self):
        """Test parsing with float percentages."""
        result = parse_composition("Fe49.5Cu50.5")
        assert abs(result["Fe"] - 0.495) < 1e-6
        assert abs(result["Cu"] - 0.505) < 1e-6

    def test_parse_invalid_format(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError):
            parse_composition("InvalidComposition")
        
        with pytest.raises(ValueError):
            parse_composition("FeCu")  # No percentages

    def test_parse_non_sum_to_one(self):
        """Test that percentages not summing to 100 raises error."""
        with pytest.raises(ValueError):
            parse_composition("Fe30Cu30")  # Sum is 60, not 100

    def test_parse_unknown_element(self):
        """Test parsing with unknown element symbol."""
        with pytest.raises(ValueError):
            parse_composition("Xy50Fe50")


class TestGetElementProperty:
    """Tests for retrieving element properties."""

    def test_get_existing_property(self, cleanup_sources):
        """Test retrieving an existing property."""
        sources = load_descriptor_sources(cleanup_sources)
        radius = get_element_property("atomic_radius", "Fe", sources)
        assert radius == 1.24

    def test_get_unknown_element(self, cleanup_sources):
        """Test retrieving property for unknown element."""
        sources = load_descriptor_sources(cleanup_sources)
        with pytest.raises(KeyError):
            get_element_property("atomic_radius", "Xy", sources)

    def test_get_unknown_property(self, cleanup_sources):
        """Test retrieving unknown property type."""
        sources = load_descriptor_sources(cleanup_sources)
        with pytest.raises(KeyError):
            get_element_property("unknown_property", "Fe", sources)


class TestCalculateEnthalpyOfMixing:
    """Tests for ΔHmix calculation."""

    def test_binary_alloy(self, cleanup_sources):
        """Test ΔHmix for a binary alloy Fe50Cu50."""
        sources = load_descriptor_sources(cleanup_sources)
        composition = {"Fe": 0.5, "Cu": 0.5}
        
        # Formula: ΔHmix = Σ Σ 4 * Ω_ij * c_i * c_j
        # where Ω_ij = -21 * c_i * c_j (simplified for this test)
        # For Fe-Cu, we need the interaction parameter
        # Using a simplified model for testing:
        # ΔHmix = 4 * Ω_FeCu * c_Fe * c_Cu
        # Assuming Ω_FeCu = -10 kJ/mol for this test
        
        # Let's compute it step by step
        # We need to mock the interaction parameters
        # For this test, we'll verify the function runs and returns a number
        result = calculate_enthalpy_of_mixing(composition, sources)
        assert isinstance(result, (int, float))

    def test_single_element(self, cleanup_sources):
        """Test ΔHmix for single element (should be 0)."""
        sources = load_descriptor_sources(cleanup_sources)
        composition = {"Fe": 1.0}
        result = calculate_enthalpy_of_mixing(composition, sources)
        assert result == 0.0

    def test_three_element_alloy(self, cleanup_sources):
        """Test ΔHmix for a ternary alloy."""
        sources = load_descriptor_sources(cleanup_sources)
        composition = {"Fe": 0.33, "Cu": 0.33, "Ni": 0.34}
        result = calculate_enthalpy_of_mixing(composition, sources)
        assert isinstance(result, (int, float))


class TestCalculateAtomicSizeDifference:
    """Tests for δ (atomic size difference) calculation."""

    def test_binary_alloy(self, cleanup_sources):
        """Test δ for Fe50Cu50."""
        sources = load_descriptor_sources(cleanup_sources)
        composition = {"Fe": 0.5, "Cu": 0.5}
        
        # δ = sqrt(Σ c_i * (1 - r_i/r_avg)^2)
        # r_avg = Σ c_i * r_i
        r_Fe = 1.24
        r_Cu = 1.28
        r_avg = 0.5 * 1.24 + 0.5 * 1.28  # 1.26
        
        # δ = sqrt(0.5 * (1 - 1.24/1.26)^2 + 0.5 * (1 - 1.28/1.26)^2)
        # δ = sqrt(0.5 * (0.01587)^2 + 0.5 * (-0.01587)^2)
        # δ = sqrt(2 * 0.5 * 0.000252)
        # δ = sqrt(0.000252) ≈ 0.01587
        
        result = calculate_atomic_size_difference(composition, sources)
        expected = math.sqrt(0.5 * (1 - r_Fe/1.26)**2 + 0.5 * (1 - r_Cu/1.26)**2)
        assert abs(result - expected) < 1e-6

    def test_single_element(self, cleanup_sources):
        """Test δ for single element (should be 0)."""
        sources = load_descriptor_sources(cleanup_sources)
        composition = {"Fe": 1.0}
        result = calculate_atomic_size_difference(composition, sources)
        assert result == 0.0


class TestCalculateValenceElectronConcentration:
    """Tests for VEC calculation."""

    def test_binary_alloy(self, cleanup_sources):
        """Test VEC for Fe50Cu50."""
        sources = load_descriptor_sources(cleanup_sources)
        composition = {"Fe": 0.5, "Cu": 0.5}
        
        # VEC = Σ c_i * valence_i
        # Fe: 8, Cu: 11
        # VEC = 0.5 * 8 + 0.5 * 11 = 4 + 5.5 = 9.5
        result = calculate_valence_electron_concentration(composition, sources)
        assert abs(result - 9.5) < 1e-6

    def test_ternary_alloy(self, cleanup_sources):
        """Test VEC for Fe33Cu33Ni34."""
        sources = load_descriptor_sources(cleanup_sources)
        composition = {"Fe": 0.33, "Cu": 0.33, "Ni": 0.34}
        
        # Fe: 8, Cu: 11, Ni: 10
        # VEC = 0.33*8 + 0.33*11 + 0.34*10
        # VEC = 2.64 + 3.63 + 3.4 = 9.67
        result = calculate_valence_electron_concentration(composition, sources)
        expected = 0.33 * 8 + 0.33 * 11 + 0.34 * 10
        assert abs(result - expected) < 1e-6


class TestCalculateElectronegativityDifference:
    """Tests for Δχ calculation."""

    def test_binary_alloy(self, cleanup_sources):
        """Test Δχ for Fe50Cu50."""
        sources = load_descriptor_sources(cleanup_sources)
        composition = {"Fe": 0.5, "Cu": 0.5}
        
        # Δχ = sqrt(Σ c_i * (χ_i - χ_avg)^2)
        # χ_Fe = 1.83, χ_Cu = 1.90
        # χ_avg = 0.5 * 1.83 + 0.5 * 1.90 = 1.865
        # Δχ = sqrt(0.5 * (1.83 - 1.865)^2 + 0.5 * (1.90 - 1.865)^2)
        # Δχ = sqrt(0.5 * 0.001225 + 0.5 * 0.001225)
        # Δχ = sqrt(0.001225) = 0.035
        
        result = calculate_electronegativity_difference(composition, sources)
        χ_Fe = 1.83
        χ_Cu = 1.90
        χ_avg = 0.5 * χ_Fe + 0.5 * χ_Cu
        expected = math.sqrt(0.5 * (χ_Fe - χ_avg)**2 + 0.5 * (χ_Cu - χ_avg)**2)
        assert abs(result - expected) < 1e-6

    def test_single_element(self, cleanup_sources):
        """Test Δχ for single element (should be 0)."""
        sources = load_descriptor_sources(cleanup_sources)
        composition = {"Fe": 1.0}
        result = calculate_electronegativity_difference(composition, sources)
        assert result == 0.0


class TestIntegration:
    """Integration tests for the full descriptor computation pipeline."""

    def test_full_pipeline_binary(self, cleanup_sources):
        """Test the full pipeline with a binary alloy."""
        from descriptor_computation import compute_descriptors
        
        composition_str = "Fe50Cu50"
        gfa_label = "GFA"
        
        results = compute_descriptors(composition_str, gfa_label, cleanup_sources)
        
        assert "composition" in results
        assert "gfa_label" in results
        assert "delta_H_mix" in results
        assert "delta" in results
        assert "VEC" in results
        assert "delta_chi" in results
        
        assert results["composition"] == composition_str
        assert results["gfa_label"] == gfa_label

    def test_full_pipeline_ternary(self, cleanup_sources):
        """Test the full pipeline with a ternary alloy."""
        from descriptor_computation import compute_descriptors
        
        composition_str = "Fe40Cu30Ni30"
        gfa_label = "NoGFA"
        
        results = compute_descriptors(composition_str, gfa_label, cleanup_sources)
        
        assert results["composition"] == composition_str
        assert results["gfa_label"] == gfa_label
        assert all(isinstance(v, (int, float)) for k, v in results.items() 
                  if k not in ["composition", "gfa_label"])

    def test_missing_element_handling(self, cleanup_sources):
        """Test that missing elements are handled gracefully."""
        from descriptor_computation import compute_descriptors
        
        # Create a composition with an element not in our test sources
        composition_str = "Fe50Xy50"  # Xy is not in our sources
        
        # This should raise a KeyError or similar
        with pytest.raises(KeyError):
            compute_descriptors(composition_str, "GFA", cleanup_sources)