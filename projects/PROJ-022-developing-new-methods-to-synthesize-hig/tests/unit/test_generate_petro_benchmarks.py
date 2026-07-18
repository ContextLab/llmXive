"""
Unit tests for petrochemical benchmark generation.
"""

import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from screening.generate_petro_benchmarks import (
    validate_smiles,
    canonicalize_smiles,
    generate_petro_benchmarks,
    save_candidates,
    POLYIMIDE_TEMPLATES,
    POLYSULFONE_TEMPLATES
)

from rdkit import Chem


class TestValidateSmiles:
    """Tests for SMILES validation function."""
    
    def test_valid_smiles(self):
        """Test validation of valid SMILES strings."""
        valid_smiles = ["CCO", "c1ccccc1", "CC(=O)O"]
        for smiles in valid_smiles:
            assert validate_smiles(smiles), f"Expected {smiles} to be valid"
    
    def test_invalid_smiles(self):
        """Test validation of invalid SMILES strings."""
        invalid_smiles = ["invalid", "CC(C", ""]
        for smiles in invalid_smiles:
            assert not validate_smiles(smiles), f"Expected {smiles} to be invalid"
    
    def test_empty_string(self):
        """Test validation of empty string."""
        assert not validate_smiles(""), "Empty string should be invalid"


class TestCanonicalizeSmiles:
    """Tests for SMILES canonicalization function."""
    
    def test_canonicalize_valid_smiles(self):
        """Test canonicalization of valid SMILES."""
        smiles = "CCO"
        canonical = canonicalize_smiles(smiles)
        assert isinstance(canonical, str)
        assert len(canonical) > 0
    
    def test_canonicalize_invalid_smiles(self):
        """Test canonicalization of invalid SMILES."""
        invalid = "invalid"
        canonical = canonicalize_smiles(invalid)
        # Should return original or handle gracefully
        assert canonical is not None


class TestGeneratePetroBenchmarks:
    """Tests for petrochemical benchmark generation."""
    
    def test_generation_count(self):
        """Test that correct number of candidates are generated."""
        num_candidates = 20
        candidates = generate_petro_benchmarks(num_candidates=num_candidates)
        assert len(candidates) == num_candidates, f"Expected {num_candidates} candidates, got {len(candidates)}"
    
    def test_required_fields(self):
        """Test that all required fields are present."""
        candidates = generate_petro_benchmarks()
        required_fields = {"smiles", "name", "source"}
        for candidate in candidates:
            assert required_fields.issubset(candidate.keys()), f"Missing required fields in {candidate}"
    
    def test_smiles_validity(self):
        """Test that generated SMILES are valid."""
        candidates = generate_petro_benchmarks()
        for candidate in candidates:
            assert validate_smiles(candidate["smiles"]), f"Invalid SMILES: {candidate['smiles']}"
    
    def test_source_types(self):
        """Test that correct source types are assigned."""
        candidates = generate_petro_benchmarks()
        sources = {c["source"] for c in candidates}
        expected_sources = {"polyimide", "polysulfone"}
        assert expected_sources.issubset(sources), f"Expected sources {expected_sources}, got {sources}"
    
    def test_unique_smiles(self):
        """Test that generated SMILES are unique."""
        candidates = generate_petro_benchmarks()
        smiles_list = [c["smiles"] for c in candidates]
        assert len(smiles_list) == len(set(smiles_list)), "Duplicate SMILES detected"
    
    def test_deterministic_generation(self):
        """Test that generation is deterministic with seed."""
        candidates1 = generate_petro_benchmarks()
        candidates2 = generate_petro_benchmarks()
        
        smiles1 = [c["smiles"] for c in candidates1]
        smiles2 = [c["smiles"] for c in candidates2]
        
        assert smiles1 == smiles2, "Generation is not deterministic"

class TestSaveCandidates:
    """Tests for candidate saving function."""
    
    def test_save_and_load(self, tmp_path):
        """Test saving and loading candidates."""
        candidates = generate_petro_benchmarks(num_candidates=5)
        output_path = tmp_path / "test_benchmarks.csv"
        
        save_candidates(candidates, str(output_path))
        
        assert output_path.exists(), "Output file was not created"
        
        df = pd.read_csv(output_path)
        assert len(df) == len(candidates), "Loaded data doesn't match saved data"
        assert set(df.columns) == {"smiles", "name", "source", "template_index"}

class TestTemplateConstants:
    """Tests for template constants."""
    
    def test_polyimide_templates_exist(self):
        """Test that polyimide templates are defined."""
        assert len(POLYIMIDE_TEMPLATES) > 0, "No polyimide templates defined"
    
    def test_polysulfone_templates_exist(self):
        """Test that polysulfone templates are defined."""
        assert len(POLYSULFONE_TEMPLATES) > 0, "No polysulfone templates defined"
    
    def test_template_validity(self):
        """Test that templates are valid SMILES."""
        for template in POLYIMIDE_TEMPLATES + POLYSULFONE_TEMPLATES:
            assert validate_smiles(template), f"Invalid template: {template}"