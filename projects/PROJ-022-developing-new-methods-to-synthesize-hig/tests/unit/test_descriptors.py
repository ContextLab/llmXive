"""
Unit tests for descriptor calculation module.
"""
import pytest
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from rdkit import Chem
from rdkit.Chem import Descriptors

# Import the module under test
from features.calculate_descriptors import (
    calculate_descriptors_for_smiles,
    process_dataframe,
    calculate_molecular_weight,
    calculate_vdw_volume,
    calculate_hb_counts
)

class TestDescriptorCalculations:
    """Tests for individual descriptor calculation functions."""

    def test_molecular_weight_ethane(self):
        """Test MW calculation for ethane (C2H6)."""
        mol = Chem.MolFromSmiles("CC")
        mw = calculate_molecular_weight(mol)
        # Ethane MW is approx 30.07
        assert 30.0 < mw < 30.1

    def test_vdw_volume_methane(self):
        """Test VdW volume calculation for methane."""
        mol = Chem.MolFromSmiles("C")
        vdw = calculate_vdw_volume(mol)
        # Methane VdW volume is approx 20-25 Angstrom^3
        assert 20.0 < vdw < 30.0

    def test_hb_counts_ethanol(self):
        """Test H-bond counts for ethanol (1 donor, 1 acceptor)."""
        mol = Chem.MolFromSmiles("CCO")
        hba, hbd = calculate_hb_counts(mol)
        assert hba == 1
        assert hbd == 1

    def test_calculate_descriptors_ethanol(self):
        """Test full descriptor calculation for ethanol."""
        smiles = "CCO"
        result = calculate_descriptors_for_smiles(smiles)
        
        assert result is not None
        assert 'molecular_weight' in result
        assert 'vdw_volume' in result
        assert 'h_bond_acceptors' in result
        assert 'h_bond_donors' in result
        
        # Verify H-bond counts
        assert result['h_bond_acceptors'] == 1
        assert result['h_bond_donors'] == 1

    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES returns None."""
        result = calculate_descriptors_for_smiles("INVALID_SMILES_STRING")
        assert result is None

    def test_empty_string_returns_none(self):
        """Test that empty string returns None."""
        result = calculate_descriptors_for_smiles("")
        assert result is None

    def test_none_input_returns_none(self):
        """Test that None input returns None."""
        result = calculate_descriptors_for_smiles(None)
        assert result is None

class TestDataFrameProcessing:
    """Tests for dataframe processing function."""

    def test_process_dataframe_valid(self):
        """Test processing a dataframe with valid SMILES."""
        data = {
            'smiles': ['CC', 'CCO', 'c1ccccc1'],
            'permeability': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        result_df = process_dataframe(df, smiles_col='smiles')
        
        assert 'molecular_weight' in result_df.columns
        assert 'vdw_volume' in result_df.columns
        assert len(result_df) == 3
        
        # Check that MW was calculated correctly for ethane (row 0)
        # Ethane MW ~ 30
        assert 29.0 < result_df.iloc[0]['molecular_weight'] < 31.0

    def test_process_dataframe_with_invalid(self):
        """Test processing a dataframe with mixed valid/invalid SMILES."""
        data = {
            'smiles': ['CC', 'INVALID', 'CCO'],
            'permeability': [10.0, 20.0, 30.0]
        }
        df = pd.DataFrame(data)
        
        result_df = process_dataframe(df, smiles_col='smiles')
        
        assert len(result_df) == 3
        # Valid rows should have values
        assert pd.notna(result_df.iloc[0]['molecular_weight'])
        assert pd.notna(result_df.iloc[2]['molecular_weight'])
        # Invalid row should be NaN
        assert pd.isna(result_df.iloc[1]['molecular_weight'])

    def test_missing_smiles_column(self):
        """Test that missing smiles column raises ValueError."""
        data = {
            'smile': ['CC'], # Wrong column name
            'permeability': [10.0]
        }
        df = pd.DataFrame(data)
        
        with pytest.raises(ValueError):
            process_dataframe(df, smiles_col='smiles')