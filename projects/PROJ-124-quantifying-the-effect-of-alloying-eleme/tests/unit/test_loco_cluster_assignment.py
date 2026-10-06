import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from models.train import extract_primary_element, validate_loco_cluster_assignment, load_family_map

class TestLOCOClusterAssignment:
    """Unit tests for LOCO cluster assignment logic (T053)."""

    def test_extract_primary_element_simple(self):
        """Test extraction with distinct fractions."""
        comp = "Fe:0.6,Cu:0.3,Zr:0.1"
        elem, frac = extract_primary_element(comp)
        assert elem == "Fe"
        assert abs(frac - 0.6) < 1e-6

    def test_extract_primary_element_tie_breaker_atomic_number(self):
        """Test tie-breaker: higher atomic number wins."""
        # Fe (Z=26) vs Cu (Z=29)
        comp = "Fe:0.5,Cu:0.5"
        elem, frac = extract_primary_element(comp)
        assert elem == "Cu", f"Expected Cu (Z=29), got {elem}"
        assert abs(frac - 0.5) < 1e-6

    def test_extract_primary_element_three_way_tie(self):
        """Test three-way tie-breaker."""
        # Al (13), Si (14), P (15)
        comp = "Al:0.3333,Si:0.3333,P:0.3333"
        elem, frac = extract_primary_element(comp)
        assert elem == "P", f"Expected P (Z=15), got {elem}"

    def test_validate_loco_cluster_assignment_passes(self):
        """Test that validation passes on correct data."""
        # Create a valid dataframe
        data = {
            'composition': ['Fe:0.6,Cu:0.3,Zr:0.1', 'Al:0.5,Si:0.5'],
            'log10_Rc': [5.0, 4.0],
            'primary_family': ['Zr-family', 'Other'] # Assuming Zr-family for first, Other for second if not mapped
        }
        df = pd.DataFrame(data)
        
        # Create a simple family map
        family_map = {
            'Zr': 'Zr-family',
            'Fe': 'Fe-family',
            'Cu': 'Cu-family'
        }
        
        # Note: The first row's primary is Fe, but we assigned Zr-family in the dataframe.
        # This should fail validation unless the logic is adjusted.
        # Let's fix the dataframe to match the logic.
        # Primary of 'Fe:0.6...' is Fe. If Fe is not in map, it goes to 'Other'.
        # Let's make sure the dataframe matches the expected logic.
        
        # Re-create with correct expectations
        # Row 1: Fe:0.6... -> Primary Fe. If Fe in map -> Fe-family.
        # Row 2: Al:0.5, Si:0.5 -> Primary Si (Z=14 > Al=13). If Si not in map -> Other.
        
        data_correct = {
            'composition': ['Fe:0.6,Cu:0.3,Zr:0.1', 'Al:0.5,Si:0.5'],
            'log10_Rc': [5.0, 4.0],
            'primary_family': ['Fe-family', 'Other']
        }
        df_correct = pd.DataFrame(data_correct)
        
        family_map_correct = {
            'Fe': 'Fe-family',
            'Zr': 'Zr-family',
            'Cu': 'Cu-family'
        }
        
        result = validate_loco_cluster_assignment(df_correct, family_map_correct)
        assert result['passed'], f"Validation failed: {result['details']}"

    def test_validate_loco_cluster_assignment_fails_on_mismatch(self):
        """Test that validation fails when family assignment is incorrect."""
        data = {
            'composition': ['Fe:0.6,Cu:0.3,Zr:0.1'],
            'log10_Rc': [5.0],
            'primary_family': ['Wrong-Family'] # Intentional mismatch
        }
        df = pd.DataFrame(data)
        
        family_map = {
            'Fe': 'Fe-family',
            'Zr': 'Zr-family',
            'Cu': 'Cu-family'
        }
        
        result = validate_loco_cluster_assignment(df, family_map)
        assert not result['passed'], "Validation should have failed due to mismatch."
        assert any("Mismatch" in detail for detail in result['details'])

    def test_synthetic_tie_dataset_verification(self):
        """
        Explicit verification of the synthetic dataset with tied fractions.
        This test creates a specific synthetic dataset and verifies the tie-breaker logic.
        """
        # Synthetic dataset for T053 verification
        synthetic_data = [
            "Fe:0.5,Cu:0.5",       # Tie: Cu wins (Z=29 > 26)
            "Al:0.4,Si:0.4,Mg:0.2", # Tie between Al, Si: Si wins (Z=14 > 13)
            "Ti:0.33,Hf:0.33,Zr:0.33" # Tie: Hf wins (Z=72 > 40 > 22)
        ]
        
        expected_winners = ["Cu", "Si", "Hf"]
        
        for i, comp in enumerate(synthetic_data):
            elem, _ = extract_primary_element(comp)
            assert elem == expected_winners[i], f"Synthetic test {i} failed: Expected {expected_winners[i]}, got {elem}"