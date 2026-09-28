"""
Unit tests for code/data/clean.py (T012).
"""

import os
import sys
import tempfile
import pandas as pd
from pathlib import Path
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from code.data.clean import canonicalize_smiles, is_primary_substrate, clean_and_filter_data

def test_canonicalize_smiles_valid():
    """Test canonicalization of a valid SMILES string."""
    smiles = "CC(C)Cl"  # Isopropyl chloride (secondary)
    canonical, success = canonicalize_smiles(smiles)
    assert success is True
    assert canonical is not None
    # RDKit canonical SMILES for isopropyl chloride
    assert canonical == "CC(C)Cl"  # This might vary, but should be canonical

def test_canonicalize_smiles_invalid():
    """Test canonicalization of an invalid SMILES string."""
    smiles = "invalid_smiles"
    canonical, success = canonicalize_smiles(smiles)
    assert success is False
    assert canonical is None

def test_is_primary_substrate():
    """Test the is_primary_substrate function."""
    assert is_primary_substrate("primary") is True
    assert is_primary_substrate("secondary") is False
    assert is_primary_substrate("tertiary") is False
    assert is_primary_substrate("unknown") is False

def test_clean_and_filter_data():
    """Test the clean_and_filter_data function."""
    # Create a test DataFrame
    data = {
        'smiles': ['CC(C)Cl', 'CCC(Cl)C', 'CCCl', 'invalid', 'C(C)(C)Cl'],
        'substrate_class': ['secondary', 'tertiary', 'primary', 'secondary', 'unknown']
    }
    df = pd.DataFrame(data)

    # Mock logger
    class MockLogger:
        def warning(self, msg): pass
        def info(self, msg): pass
        def error(self, msg): pass

    cleaned_df, exclusions = clean_and_filter_data(df, MockLogger())

    # Check that primary and unknown rows are excluded
    assert len(cleaned_df) == 3  # secondary, tertiary, and one secondary (invalid SMILES excluded)
    assert 'primary' not in cleaned_df['substrate_class'].values
    assert 'unknown' not in cleaned_df['substrate_class'].values

    # Check exclusions
    assert len(exclusions) >= 2  # At least primary and unknown
    reasons = [e['reason'] for e in exclusions]
    assert 'primary_substrate_filter' in reasons
    assert 'invalid_substrate_label' in reasons

if __name__ == "__main__":
    test_canonicalize_smiles_valid()
    test_canonicalize_smiles_invalid()
    test_is_primary_substrate()
    test_clean_and_filter_data()
    print("All tests passed.")
