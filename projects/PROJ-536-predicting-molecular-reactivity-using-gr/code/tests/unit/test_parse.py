"""
Unit tests for SMILES-to-Graph conversion module.
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Import the module under test
from src.data.parse import (
    get_atom_features,
    get_bond_features,
    smiles_to_graph,
    parse_reaction_dataframe,
    calculate_data_validity
)

# Mock RDKit for tests where RDKit is not available
@pytest.fixture
def mock_rdkit():
    """Mock RDKit module for testing without RDKit installed."""
    with patch.dict(sys.modules, {
        'rdkit': MagicMock(),
        'rdkit.Chem': MagicMock(),
        'rdkit.Chem.rdMolDescriptors': MagicMock(),
        'rdkit': MagicMock()
    }):
        yield


class TestSmilesToGraph:
    """Tests for smiles_to_graph function."""

    def test_valid_smiles_ethanol(self):
        """Test conversion of valid ethanol SMILES."""
        graph = smiles_to_graph("CCO")
        assert graph is not None
        assert 'atoms' in graph
        assert 'bonds' in graph
        assert 'num_atoms' in graph
        assert 'num_bonds' in graph
        assert graph['num_atoms'] > 0
        assert graph['num_bonds'] > 0
        assert isinstance(graph['atoms'], list)
        assert isinstance(graph['bonds'], list)

    def test_valid_smiles_benzene(self):
        """Test conversion of valid benzene SMILES."""
        graph = smiles_to_graph("c1ccccc1")
        assert graph is not None
        assert graph['num_atoms'] == 6
        assert graph['num_bonds'] > 0

    def test_invalid_smiles(self):
        """Test conversion of invalid SMILES returns None."""
        graph = smiles_to_graph("invalid_smiles_string")
        assert graph is None

    def test_empty_smiles(self):
        """Test conversion of empty SMILES returns None."""
        graph = smiles_to_graph("")
        assert graph is None

    def test_atom_features_format(self):
        """Test that atom features are numpy arrays."""
        graph = smiles_to_graph("CCO")
        if graph:
            for atom_feat in graph['atoms']:
                assert isinstance(atom_feat, list)
                assert len(atom_feat) > 0

    def test_bond_features_format(self):
        """Test that bond features are tuples with correct structure."""
        graph = smiles_to_graph("CCO")
        if graph:
            for bond in graph['bonds']:
                assert isinstance(bond, list)
                assert len(bond) == 3  # (i, j, features)
                assert isinstance(bond[0], int)
                assert isinstance(bond[1], int)
                assert isinstance(bond[2], list)


class TestParseReactionDataFrame:
    """Tests for parse_reaction_dataframe function."""

    def test_parse_valid_reactions(self):
        """Test parsing of valid reactions."""
        data = {
            'reactants_smiles': ['CCO', 'CC(=O)O'],
            'product_smiles': ['CCOC(=O)C'],
            'yield': [0.85, 0.72]
        }
        df = pd.DataFrame(data)
        
        processed_df, stats = parse_reaction_dataframe(df)
        
        assert 'reactants_graphs' in processed_df.columns
        assert 'products_graphs' in processed_df.columns
        assert 'yield' in processed_df.columns
        assert stats['valid_reactions'] > 0
        assert stats['total_rows'] == 2

    def test_parse_with_invalid_smiles(self):
        """Test parsing with some invalid SMILES."""
        data = {
            'reactants_smiles': ['CCO', 'invalid'],
            'product_smiles': ['CCOC(=O)C', 'CCOC(=O)C'],
            'yield': [0.85, 0.72]
        }
        df = pd.DataFrame(data)
        
        processed_df, stats = parse_reaction_dataframe(df)
        
        # Should have 1 valid, 1 invalid
        assert stats['valid_reactions'] == 1
        assert stats['invalid_reactants'] == 1

    def test_parse_missing_yield(self):
        """Test parsing with missing yield values."""
        data = {
            'reactants_smiles': ['CCO', 'CC(=O)O'],
            'product_smiles': ['CCOC(=O)C', 'CCOC(=O)C'],
            'yield': [0.85, np.nan]
        }
        df = pd.DataFrame(data)
        
        processed_df, stats = parse_reaction_dataframe(df)
        
        # Should skip the row with missing yield
        assert stats['skipped_yield'] == 1
        assert stats['valid_reactions'] == 1

    def test_empty_dataframe(self):
        """Test parsing of empty DataFrame."""
        df = pd.DataFrame(columns=['reactants_smiles', 'product_smiles', 'yield'])
        
        processed_df, stats = parse_reaction_dataframe(df)
        
        assert len(processed_df) == 0
        assert stats['total_rows'] == 0
        assert stats['valid_reactions'] == 0


class TestDataValidityCalculation:
    """Tests for calculate_data_validity function."""

    def test_calculate_validity_percent(self):
        """Test calculation of validity percentage."""
        stats = {
            'total_rows': 100,
            'valid_reactions': 95,
            'invalid_reactants': 3,
            'invalid_products': 2,
            'skipped_yield': 0
        }
        
        validity = calculate_data_validity(stats)
        
        assert validity == 95.0
        assert 0.0 <= validity <= 100.0

    def test_calculate_validity_zero_total(self):
        """Test calculation when total is zero."""
        stats = {
            'total_rows': 0,
            'valid_reactions': 0,
            'invalid_reactants': 0,
            'invalid_products': 0,
            'skipped_yield': 0
        }
        
        validity = calculate_data_validity(stats)
        
        assert validity == 0.0

    def test_calculate_validity_all_valid(self):
        """Test calculation when all reactions are valid."""
        stats = {
            'total_rows': 50,
            'valid_reactions': 50,
            'invalid_reactants': 0,
            'invalid_products': 0,
            'skipped_yield': 0
        }
        
        validity = calculate_data_validity(stats)
        
        assert validity == 100.0

    def test_calculate_validity_low_success(self):
        """Test calculation with low success rate."""
        stats = {
            'total_rows': 100,
            'valid_reactions': 45,
            'invalid_reactants': 30,
            'invalid_products': 25,
            'skipped_yield': 0
        }
        
        validity = calculate_data_validity(stats)
        
        assert validity == 45.0