import pytest
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import Descriptors

# Import the functions to test
from code.data.descriptors import (
    compute_gasteiger_charges,
    compute_topological_indices,
    process_single_row,
    compute_descriptors_for_dataset
)

class TestGasteigerCharges:
    def test_simple_molecule(self):
        """Test Gasteiger charge computation on a simple molecule."""
        smiles = "CCO"  # Ethanol
        mol = Chem.MolFromSmiles(smiles)
        charges = compute_gasteiger_charges(mol)
        
        assert charges is not None
        assert len(charges) > 0
        # Check that we have reasonable charge values (typically between -0.5 and 0.5)
        for charge in charges:
            assert -1.0 <= charge <= 1.0

    def test_failures_return_none(self):
        """Test that invalid molecules return None."""
        mol = None
        charges = compute_gasteiger_charges(mol)
        assert charges is None

class TestTopologicalIndices:
    def test_molecular_weight(self):
        """Test that molecular weight is computed correctly."""
        smiles = "CCO"  # Ethanol, MW ~46
        mol = Chem.MolFromSmiles(smiles)
        indices = compute_topological_indices(mol)
        
        assert 'molecular_weight' in indices
        assert 40 < indices['molecular_weight'] < 50

    def test_logp(self):
        """Test that LogP is computed."""
        smiles = "CCCC"  # Butane
        mol = Chem.MolFromSmiles(smiles)
        indices = compute_topological_indices(mol)
        
        assert 'logp' in indices
        # Butane has positive LogP
        assert indices['logp'] > 0

    def test_all_indices_present(self):
        """Test that all expected indices are present."""
        smiles = "c1ccccc1"  # Benzene
        mol = Chem.MolFromSmiles(smiles)
        indices = compute_topological_indices(mol)
        
        expected_keys = [
            'molecular_weight', 'logp', 'tpsa', 'heavy_atom_count',
            'num_rotatable_bonds', 'num_aromatic_rings', 'num_aliphatic_rings',
            'num_hbd', 'num_hba', 'bertz_ct', 'kier_alpha'
        ]
        
        for key in expected_keys:
            assert key in indices

class TestProcessSingleRow:
    def test_valid_row(self):
        """Test processing a valid row."""
        row = {'smiles': 'CCO'}
        result, error = process_single_row(row)
        
        assert error is None
        assert result is not None
        assert 'smiles' in result
        assert 'gasteiger_charges' in result
        assert 'molecular_weight' in result

    def test_invalid_smiles(self):
        """Test processing an invalid SMILES string."""
        row = {'smiles': 'invalid_smiles_string'}
        result, error = process_single_row(row)
        
        assert error == 'rdkit_parse_fail'
        assert result is None

    def test_missing_smiles(self):
        """Test processing a row without SMILES."""
        row = {'smiles': None}
        result, error = process_single_row(row)
        
        assert error == 'invalid_smiles'
        assert result is None

class TestComputeDescriptorsForDataset:
    def test_full_pipeline(self):
        """Test the full dataset processing pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a small test dataset
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.csv')
            exclusion_path = os.path.join(tmpdir, 'exclusions.csv')
            
            # Create test data
            test_data = pd.DataFrame({
                'smiles': ['CCO', 'CCCC', 'c1ccccc1', 'invalid'],
                'rate_constant': [1.0, 2.0, 3.0, 4.0]
            })
            test_data.to_csv(input_path, index=False)
            
            # Run descriptor computation
            compute_descriptors_for_dataset(input_path, output_path, exclusion_path)
            
            # Verify output
            assert os.path.exists(output_path)
            output_df = pd.read_csv(output_path)
            
            # Should have 3 valid rows (CCO, CCCC, benzene)
            assert len(output_df) == 3
            
            # Verify exclusion log
            assert os.path.exists(exclusion_path)
            exclusion_df = pd.read_csv(exclusion_path)
            assert len(exclusion_df) == 1
            assert exclusion_df.iloc[0]['reason'] == 'rdkit_parse_fail'

    def test_empty_input(self):
        """Test handling of empty input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = os.path.join(tmpdir, 'input.csv')
            output_path = os.path.join(tmpdir, 'output.csv')
            exclusion_path = os.path.join(tmpdir, 'exclusions.csv')
            
            # Create empty dataframe
            pd.DataFrame(columns=['smiles']).to_csv(input_path, index=False)
            
            # Run descriptor computation
            compute_descriptors_for_dataset(input_path, output_path, exclusion_path)
            
            # Verify output exists and is empty (but has headers)
            assert os.path.exists(output_path)
            output_df = pd.read_csv(output_path)
            assert len(output_df) == 0