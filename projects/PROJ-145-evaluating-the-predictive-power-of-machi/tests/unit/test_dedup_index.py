import pytest
import pandas as pd
from pathlib import Path
import json
import sys
import os

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_ingestion import (
    build_deduplicated_composition_index,
    strict_composition_compare,
    generate_all_5_element_combinations
)

def test_build_deduplicated_index():
    """Test that the deduplicated index is built correctly and saved."""
    # Create a mock train dataframe
    train_data = {
        'composition': ['Fe-Cr-Ni-Mn-Co', 'Ti-Zr-Hf-Nb-Ta', 'Al-Cr-Fe-Mn-Ni']
    }
    df = pd.DataFrame(train_data)
    
    # Mock HMAO index (some overlap, some new)
    hmao_index = {'Fe-Cr-Ni-Mn-Co', 'Ti-Zr-Hf-Nb-Ta', 'V-Cr-Mn-Fe-Co'}
    
    index = build_deduplicated_composition_index(df, hmao_index)
    
    # Verify structure
    assert isinstance(index, dict)
    assert len(index) == 4  # 3 from train + 1 new from hmao
    
    # Verify keys are canonical
    assert 'Al-Cr-Fe-Mn-Ni' in index
    assert 'Cr-Fe-Mn-Ni-V' in index # V-Cr-Mn-Fe-Co sorted
    
    # Verify saved file exists
    assert Path("data/processed/deduplicated_composition_index.json").exists()

def test_strict_composition_compare():
    """Test strict string comparison logic."""
    index = {'Al-Cr-Fe-Mn-Ni', 'Fe-Cr-Ni-Mn-Co'}
    
    # Test exact match
    assert strict_composition_compare('Al-Cr-Fe-Mn-Ni', index) is True
    
    # Test non-match
    assert strict_composition_compare('Al-Cr-Fe-Mn-Zn', index) is False
    
    # Test unordered input (should be canonicalized)
    assert strict_composition_compare('Ni-Mn-Fe-Cr-Al', index) is True
    assert strict_composition_compare('Ni-Mn-Fe-Cr-Zn', index) is False

def test_no_hash_collision():
    """Ensure that different compositions with same elements but different counts (if applicable) are distinct.
    Note: Our current model assumes 5-element systems with 1:1 stoichiometry for the string representation.
    If stoichiometry were included, this would be more complex.
    """
    # This test verifies the canonical sorting logic prevents simple permutation collisions
    comp1 = "Fe-Cr-Ni-Mn-Co"
    comp2 = "Co-Mn-Ni-Cr-Fe"
    
    index = {comp1}
    
    # Both should resolve to the same canonical string and match
    assert strict_composition_compare(comp1, index) is True
    assert strict_composition_compare(comp2, index) is True
    
    # But a different set should not match
    comp3 = "Fe-Cr-Ni-Mn-Cu"
    assert strict_composition_compare(comp3, index) is False
