"""
Unit tests for the Defense Allocation Index calculation.
"""
import pytest
import pandas as pd
import numpy as np
import json
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.defense_index import (
    extract_trait_values,
    standardize_traits,
    calculate_dai,
    compile_defense_allocation_index
)

class TestExtractTraitValues:
    """Tests for extract_trait_values function."""
    
    def test_extract_chemical_and_physical_traits(self):
        """Test extraction of chemical and physical traits."""
        species_data = {
            "primary_source_results": {
                "alkaloids": 10.5,
                "thorns": 5.2,
                "terpenoids": 8.3,
                "spines": 3.1
            }
        }
        
        chemical, physical = extract_trait_values(species_data)
        
        assert "alkaloids" in chemical
        assert "terpenoids" in chemical
        assert "thorns" in physical
        assert "spines" in physical
        assert len(chemical) == 2
        assert len(physical) == 2

    def test_extract_from_fallback(self):
        """Test extraction from fallback results."""
        species_data = {
            "primary_source_results": {},
            "fallback_results": {
                "glucosinolates": 7.5,
                "trichomes": 4.2
            }
        }
        
        chemical, physical = extract_trait_values(species_data)
        
        assert "glucosinolates" in chemical
        assert "trichomes" in physical

    def test_extract_with_none_values(self):
        """Test extraction with None values."""
        species_data = {
            "primary_source_results": {
                "alkaloids": None,
                "thorns": 5.2
            }
        }
        
        chemical, physical = extract_trait_values(species_data)
        
        assert "alkaloids" not in chemical or np.isnan(chemical["alkaloids"])
        assert "thorns" in physical

class TestStandardizeTraits:
    """Tests for standardize_traits function."""
    
    def test_standardize_normal_distribution(self):
        """Test standardization with normal distribution."""
        traits = {"a": 10.0, "b": 20.0, "c": 30.0}
        
        standardized = standardize_traits(traits)
        
        assert len(standardized) == 3
        assert np.isclose(np.mean(standardized), 0.0, atol=1e-6)
        assert np.isclose(np.std(standardized), 1.0, atol=1e-6)
    
    def test_standardize_single_value(self):
        """Test standardization with single value."""
        traits = {"a": 10.0}
        
        standardized = standardize_traits(traits)
        
        assert len(standardized) == 1
        assert standardized[0] == 0.0
    
    def test_standardize_constant_values(self):
        """Test standardization with constant values."""
        traits = {"a": 10.0, "b": 10.0, "c": 10.0}
        
        standardized = standardize_traits(traits)
        
        assert len(standardized) == 3
        assert all(s == 0.0 for s in standardized)

class TestCalculateDAI:
    """Tests for calculate_dai function."""
    
    def test_calculate_dai_normal(self):
        """Test DAI calculation with normal values."""
        chemical = {"alkaloids": 10.0, "terpenoids": 20.0}
        physical = {"thorns": 5.0, "spines": 15.0}
        
        dai = calculate_dai(chemical, physical)
        
        assert dai is not None
        assert isinstance(dai, float)
    
    def test_calculate_dai_zero_physical_mean(self):
        """Test DAI calculation when physical mean is zero."""
        # This is a tricky case - if all standardized physical traits are 0
        chemical = {"alkaloids": 10.0}
        physical = {"thorns": 10.0, "spines": 10.0}  # Will standardize to [0, 0]
        
        dai = calculate_dai(chemical, physical)
        
        # Should return None due to division by zero
        assert dai is None
    
    def test_calculate_dai_empty_chemical(self):
        """Test DAI calculation with empty chemical traits."""
        chemical = {}
        physical = {"thorns": 5.0}
        
        dai = calculate_dai(chemical, physical)
        
        assert dai is None
    
    def test_calculate_dai_empty_physical(self):
        """Test DAI calculation with empty physical traits."""
        chemical = {"alkaloids": 5.0}
        physical = {}
        
        dai = calculate_dai(chemical, physical)
        
        assert dai is None

class TestCompileDefenseAllocationIndex:
    """Tests for compile_defense_allocation_index function."""
    
    def test_compile_with_valid_data(self):
        """Test compilation with valid trait data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Create mock trait summary
            trait_summary = {
                "primary_source_results": {
                    "Species_A": {
                        "alkaloids": 10.0,
                        "terpenoids": 20.0,
                        "thorns": 5.0
                    },
                    "Species_B": {
                        "glucosinolates": 15.0,
                        "spines": 8.0,
                        "trichomes": 3.0
                    }
                }
            }
            
            input_path = tmpdir_path / "trait_fallback_summary.json"
            output_path = tmpdir_path / "defense_allocation_index.csv"
            
            with open(input_path, 'w') as f:
                json.dump(trait_summary, f)
            
            results = compile_defense_allocation_index(input_path, output_path)
            
            assert len(results) == 2
            assert output_path.exists()
            
            # Check CSV content
            df = pd.read_csv(output_path)
            assert "species" in df.columns
            assert "dai" in df.columns
            assert len(df) == 2

    def test_compile_with_empty_data(self):
        """Test compilation with no valid data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            trait_summary = {
                "primary_source_results": {}
            }
            
            input_path = tmpdir_path / "trait_fallback_summary.json"
            output_path = tmpdir_path / "defense_allocation_index.csv"
            
            with open(input_path, 'w') as f:
                json.dump(trait_summary, f)
            
            results = compile_defense_allocation_index(input_path, output_path)
            
            assert len(results) == 0
            assert output_path.exists()
            
            # Check CSV has headers
            df = pd.read_csv(output_path)
            assert len(df) == 0