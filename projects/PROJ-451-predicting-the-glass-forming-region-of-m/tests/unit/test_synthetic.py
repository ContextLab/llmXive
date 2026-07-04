"""
Unit tests for synthetic data generator.

Tests verify that the synthetic data generator:
1. Produces valid compositions
2. Computes descriptors correctly
3. Maintains expected phase distribution
4. Generates reproducible results with fixed seed
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.synthetic import (
    generate_composition_from_system,
    generate_synthetic_dataset,
    GLASS_FORMING_SYSTEMS,
    CRYSTALLINE_SYSTEMS
)
from features.descriptors import compute_all_descriptors


class TestCompositionGeneration:
    """Test composition generation from system configurations."""
    
    def test_generate_amorphous_composition(self):
        """Test that amorphous compositions are generated correctly."""
        rng = np.random.default_rng(42)
        system = GLASS_FORMING_SYSTEMS[0]  # Zr-based
        
        result = generate_composition_from_system(system, rng)
        
        assert "composition" in result
        assert "element_fractions" in result
        assert "phase" in result
        assert result["phase"] == "amorphous"
        assert len(result["element_fractions"]) >= 3
        assert len(result["element_fractions"]) <= 5
        
        # Check that fractions sum to 1 (within floating point tolerance)
        total = sum(result["element_fractions"].values())
        assert np.isclose(total, 1.0, atol=1e-6)
    
    def test_generate_crystalline_composition(self):
        """Test that crystalline compositions are generated correctly."""
        rng = np.random.default_rng(42)
        system = CRYSTALLINE_SYSTEMS[0]  # Simple alloys
        
        result = generate_composition_from_system(system, rng)
        
        assert result["phase"] == "crystalline"
        assert "composition" in result
        assert len(result["element_fractions"]) >= 2
    
    def test_composition_string_format(self):
        """Test that composition strings follow expected format."""
        rng = np.random.default_rng(42)
        system = GLASS_FORMING_SYSTEMS[0]
        
        result = generate_composition_from_system(system, rng)
        comp_str = result["composition"]
        
        # Composition should contain element symbols and numbers
        assert len(comp_str) > 0
        assert comp_str[0].isupper()  # First char should be element symbol
        
        # Check that numbers follow element symbols
        has_numbers = any(char.isdigit() for char in comp_str)
        assert has_numbers


class TestDatasetGeneration:
    """Test full dataset generation."""
    
    def test_dataset_size(self):
        """Test that generated dataset has expected size."""
        df = generate_synthetic_dataset(num_samples=100, seed=42)
        assert len(df) == 100
    
    def test_phase_distribution(self):
        """Test that phase distribution matches expected ratio."""
        df = generate_synthetic_dataset(num_samples=1000, amorphous_ratio=0.7, seed=42)
        
        amorphous_count = sum(df["phase"] == "amorphous")
        crystalline_count = sum(df["phase"] == "crystalline")
        
        # Allow small tolerance for rounding
        assert 0.65 <= (amorphous_count / len(df)) <= 0.75
        assert 0.25 <= (crystalline_count / len(df)) <= 0.35
    
    def test_descriptor_computation(self):
        """Test that descriptors are computed for all samples."""
        df = generate_synthetic_dataset(num_samples=50, seed=42)
        
        # Check for expected descriptor columns
        expected_descriptors = [
            "atomic_radius",
            "electronegativity",
            "valence_electron_concentration",
            "atomic_size_mismatch",
            "mixing_enthalpy",
            "atomic_size_difference",
            "valence_electron_size_mismatch",
            "electron_atom_ratio",
            "miedema_heat_of_formation",
            "atomic_packing_factor"
        ]
        
        for col in expected_descriptors:
            assert col in df.columns, f"Missing descriptor: {col}"
    
    def test_descriptor_ranges(self):
        """Test that descriptor values fall within physically reasonable ranges."""
        df = generate_synthetic_dataset(num_samples=100, seed=42)
        
        # Atomic size mismatch (δ) should be non-negative
        assert all(df["atomic_size_mismatch"] >= 0), "Atomic size mismatch should be non-negative"
        
        # Electronegativity should be positive
        assert all(df["electronegativity"] > 0), "Electronegativity should be positive"
        
        # Valence electron concentration should be positive
        assert all(df["valence_electron_concentration"] > 0), "VEC should be positive"
    
    def test_reproducibility(self):
        """Test that same seed produces same results."""
        df1 = generate_synthetic_dataset(num_samples=50, seed=123)
        df2 = generate_synthetic_dataset(num_samples=50, seed=123)
        
        # Compare compositions
        assert list(df1["composition"]) == list(df2["composition"])
        
        # Compare phase labels
        assert list(df1["phase"]) == list(df2["phase"])
        
        # Compare descriptors (with floating point tolerance)
        for col in df1.columns:
            if col not in ["composition", "phase", "source", "generation_seed", "timestamp"]:
                assert np.allclose(df1[col].values, df2[col].values), f"Descriptor {col} not reproducible"
    
    def test_source_metadata(self):
        """Test that source metadata is correctly set."""
        df = generate_synthetic_dataset(num_samples=50, seed=42)
        
        assert all(df["source"] == "synthetic")
        assert all(df["generation_seed"] == 42)
        assert "timestamp" in df.columns


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_minimum_sample_size(self):
        """Test generation with minimum sample size."""
        df = generate_synthetic_dataset(num_samples=1, seed=42)
        assert len(df) == 1
    
    def test_extreme_amorphous_ratio(self):
        """Test with extreme amorphous ratios."""
        # All amorphous
        df1 = generate_synthetic_dataset(num_samples=100, amorphous_ratio=1.0, seed=42)
        assert all(df1["phase"] == "amorphous")
        
        # All crystalline
        df2 = generate_synthetic_dataset(num_samples=100, amorphous_ratio=0.0, seed=42)
        assert all(df2["phase"] == "crystalline")
    
    def test_large_dataset(self):
        """Test generation of larger dataset."""
        df = generate_synthetic_dataset(num_samples=5000, seed=42)
        assert len(df) == 5000
        assert len(df.columns) > 10  # Should have many descriptor columns
