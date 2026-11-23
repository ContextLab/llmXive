"""
Unit tests for scaffold splitting leakage prevention.
"""

import pandas as pd
import pytest
from code.scaffold_split import scaffold_split

def test_scaffold_leakage_prevention():
    """
    Verify that molecules sharing the same scaffold are not split 
    between the training and testing sets.
    """
    # Create a dataset where molecules are grouped by scaffold_id
    # Scaffold A: 3 molecules, Scaffold B: 2 molecules, Scaffold C: 2 molecules
    data = pd.DataFrame({
        "smiles": ["C1=CC=CC=C1", "C1=CC=CC=C1C", "C1=CC=CC=C1CC", 
                  "CC=CC=C", "CC=CC=CC", 
                  "CCC", "CCCC"],
        "scaffold_id": ["A", "A", "A", "B", "B", "C", "C"]
    })
    
    train, test = scaffold_split(data, seed=42)
    
    # Get unique scaffolds in each set
    train_scaffolds = set(train["scaffold_id"].unique())
    test_scaffolds = set(test["scaffold_id"].unique())
    
    # Intersection must be empty to prevent leakage
    leakage = train_scaffolds.intersection(test_scaffolds)
    assert len(leakage) == 0, f"Scaffold leakage detected for scaffolds: {leakage}"

def test_scaffold_split_callable():
    """Verify the function is callable."""
    data = pd.DataFrame({"smiles": ["C"], "scaffold_id": ["S1"]})
    try:
        scaffold_split(data)
    except Exception as e:
        pytest.fail(f"scaffold_split raised unexpected exception: {e}")
