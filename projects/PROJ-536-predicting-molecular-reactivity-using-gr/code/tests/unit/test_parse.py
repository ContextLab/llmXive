"""
Unit tests for SMILES-to-Graph conversion in src/data/parse.py.
"""

import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
import json

# Add code directory to path if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.parse import smiles_to_graph, parse_reaction_dataframe, calculate_data_validity, get_atom_features
from rdkit import Chem

class TestSmilesToGraph:
    """Tests for the core SMILES to graph conversion function."""

    def test_valid_methane(self):
        """Test conversion of a simple valid molecule: Methane."""
        smiles = "C"
        graph = smiles_to_graph(smiles)
        
        assert graph is not None
        assert 'nodes' in graph
        assert 'edges' in graph
        assert len(graph['nodes']) == 1
        assert len(graph['edges']) == 0 # No bonds in methane
        
        # Check atom features
        atom = graph['nodes'][0]
        assert atom['atomic_num'] == 6
        assert atom['degree'] == 0
        assert atom['hybridization'] == Chem.HybridizationType.SP3

    def test_valid_ethane(self):
        """Test conversion of Ethane."""
        smiles = "CC"
        graph = smiles_to_graph(smiles)
        
        assert graph is not None
        assert len(graph['nodes']) == 2
        # Should have 2 directed edges (u->v, v->u)
        assert len(graph['edges']) == 2
        
        # Check bond features
        bond = graph['edges'][0]['features']
        assert bond['bond_type'] == Chem.BondType.SINGLE

    def test_invalid_smiles(self):
        """Test that invalid SMILES returns None."""
        invalid_smiles = ["C[C", "123", ""]
        for smi in invalid_smiles:
            result = smiles_to_graph(smi)
            assert result is None, f"Expected None for invalid SMILES: {smi}"

    def test_benzene(self):
        """Test conversion of Benzene with aromatic bonds."""
        smiles = "c1ccccc1"
        graph = smiles_to_graph(smiles)
        
        assert graph is not None
        assert len(graph['nodes']) == 6
        
        # Check for aromatic bonds
        has_aromatic = False
        for edge in graph['edges']:
            if edge['features']['bond_type'] == Chem.BondType.AROMATIC:
                has_aromatic = True
                break
        assert has_aromatic

class TestParseReactionDataFrame:
    """Tests for parsing a DataFrame of reactions."""

    def test_parse_valid_reactions(self):
        """Test parsing a DataFrame with valid reactions."""
        data = {
            'reactants_smiles': ['CCO', 'CC'],
            'product_smiles': ['CCO', 'CC'],
            'yield': [0.8, 0.9]
        }
        df = pd.DataFrame(data)
        
        df_parsed, stats = parse_reaction_dataframe(df)
        
        assert 'graph' in df_parsed.columns
        assert stats['valid_reactants'] == 2
        assert stats['valid_products'] == 2
        assert stats['skipped'] == 0
        
        # Check that graphs are not None
        for graph in df_parsed['graph']:
            assert graph is not None

    def test_parse_invalid_reactant(self):
        """Test parsing a DataFrame with an invalid reactant."""
        data = {
            'reactants_smiles': ['CCO', 'INVALID_SMILES'],
            'product_smiles': ['CCO', 'CC'],
            'yield': [0.8, 0.9]
        }
        df = pd.DataFrame(data)
        
        df_parsed, stats = parse_reaction_dataframe(df)
        
        assert stats['invalid_reactants'] == 1
        assert stats['valid_reactants'] == 1
        
        # The row with invalid reactant should have None graph
        assert df_parsed.iloc[1]['graph'] is None

    def test_parse_missing_data(self):
        """Test parsing a DataFrame with missing SMILES."""
        data = {
            'reactants_smiles': ['CCO', None],
            'product_smiles': ['CCO', 'CC'],
            'yield': [0.8, 0.9]
        }
        df = pd.DataFrame(data)
        
        df_parsed, stats = parse_reaction_dataframe(df)
        
        assert stats['skipped'] == 1
        assert df_parsed.iloc[1]['graph'] is None

class TestDataValidityCalculation:
    """Tests for data validity calculation."""

    def test_validity_100_percent(self):
        """Test calculation when all entries are valid."""
        stats = {'total': 100, 'valid_reactants': 100}
        validity = calculate_data_validity(stats)
        assert validity == 100.0

    def test_validity_50_percent(self):
        """Test calculation when half are valid."""
        stats = {'total': 100, 'valid_reactants': 50}
        validity = calculate_data_validity(stats)
        assert validity == 50.0

    def test_validity_zero(self):
        """Test calculation when none are valid."""
        stats = {'total': 100, 'valid_reactants': 0}
        validity = calculate_data_validity(stats)
        assert validity == 0.0

    def test_validity_empty_total(self):
        """Test calculation with zero total."""
        stats = {'total': 0, 'valid_reactants': 0}
        validity = calculate_data_validity(stats)
        assert validity == 0.0