"""
Unit tests for ingestion filtering logic.
Verifies that non-metallic materials (polymers, composites) are removed
and metallic alloys are retained by the filter_metallic_alloys function.
"""
import pytest
import pandas as pd
import os
import sys

# Ensure the code directory is in the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.ingestion import filter_metallic_alloys


def test_filter_metallic_alloys_removes_polymers():
    """Verify non-metallics are removed."""
    data = {
        "material_type": ["Steel Alloy", "Polymer", "Stainless Steel", "Composite", "Titanium Alloy"],
        "Fe": [100, 0, 70, 0, 0],
        "C": [0, 100, 0.1, 0, 0]
    }
    df = pd.DataFrame(data)
    
    filtered, removed = filter_metallic_alloys(df)
    
    assert len(filtered) == 3
    assert removed == 2
    assert "Polymer" not in filtered["material_type"].values
    assert "Composite" not in filtered["material_type"].values


def test_filter_metallic_alloys_keeps_metals():
    """Verify metallic alloys are kept."""
    data = {
        "material_type": ["Aluminum Alloy", "Copper Alloy", "Nickel Superalloy"],
        "Al": [90, 0, 0],
        "Cu": [0, 90, 0],
        "Ni": [0, 0, 90]
    }
    df = pd.DataFrame(data)
    
    filtered, removed = filter_metallic_alloys(df)
    
    assert len(filtered) == 3
    assert removed == 0


def test_filter_metallic_alloys_empty_input():
    """Verify behavior with empty dataframe."""
    df = pd.DataFrame(columns=["material_type", "Fe"])
    filtered, removed = filter_metallic_alloys(df)
    assert len(filtered) == 0
    assert removed == 0


def test_filter_metallic_alloys_all_nonmetallic():
    """Verify behavior when all inputs are non-metallic."""
    data = {
        "material_type": ["Polymer", "Ceramic", "Composite"],
        "Fe": [0, 0, 0]
    }
    df = pd.DataFrame(data)
    filtered, removed = filter_metallic_alloys(df)
    assert len(filtered) == 0
    assert removed == 3