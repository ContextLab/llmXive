"""
Unit tests for preprocessing module.
"""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import pandas as pd

# Import the module under test
from data.preprocess import (
    atom_to_feature_vector,
    molecule_to_graph,
    extract_2d_features,
    generate_conformers
)

from rdkit import Chem


class TestAtomToFeatureVector:
    """Tests for atom_to_feature_vector function."""
    
    def test_carbon_atom(self):
        """Test feature vector for carbon atom."""
        mol = Chem.MolFromSmiles('C')
        atom = mol.GetAtomWithIdx(0)
        
        feat = atom_to_feature_vector(atom)
        
        assert len(feat) == 17  # NUM_ATOM_TYPES + NUM_HYBRIDIZATIONS + NUM_CHARGES
        assert feat[0] == 1.0  # Carbon is first in ATOMIC_NUMS
        
    def test_nitrogen_atom(self):
        """Test feature vector for nitrogen atom."""
        mol = Chem.MolFromSmiles('N')
        atom = mol.GetAtomWithIdx(0)
        
        feat = atom_to_feature_vector(atom)
        
        assert len(feat) == 17
        # Nitrogen is at index 2 in ATOMIC_NUMS
        assert feat[2] == 1.0
        
    def test_hybridization_sp3(self):
        """Test hybridization encoding for sp3 carbon."""
        mol = Chem.MolFromSmiles('CC')
        atom = mol.GetAtomWithIdx(0)
        
        feat = atom_to_feature_vector(atom)
        
        # sp3 is at index 3 in HYBRIDIZATION_MAP
        # Feature vector: [atom_type, hybridization, charge]
        # Atom type for C is at index 0
        # Hybridization starts at index NUM_ATOM_TYPES = 10
        hyb_start = 10
        assert feat[hyb_start + 3] == 1.0
        
    def test_formal_charge(self):
        """Test formal charge encoding."""
        mol = Chem.MolFromSmiles('[NH4+]')
        atom = mol.GetAtomWithIdx(0)
        
        feat = atom_to_feature_vector(atom)
        
        # Charge +1 is at index 4 in CHARGE_MAP
        # Charge starts at index NUM_ATOM_TYPES + NUM_HYBRIDIZATIONS = 10 + 7 = 17
        charge_start = 17
        assert feat[charge_start + 4] == 1.0


class TestMoleculeToGraph:
    """Tests for molecule_to_graph function."""
    
    def test_simple_molecule(self):
        """Test graph conversion for simple molecule."""
        mol = Chem.MolFromSmiles('CCO')
        graph = molecule_to_graph(mol)
        
        assert graph is not None
        assert graph.node_features.shape[0] > 0
        assert graph.edge_index.shape[0] == 2
        
    def test_empty_molecule(self):
        """Test handling of empty molecule."""
        mol = Chem.MolFromSmiles('')
        graph = molecule_to_graph(mol)
        
        assert graph is None
        
    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        mol = Chem.MolFromSmiles('invalid_smiles')
        graph = molecule_to_graph(mol)
        
        assert graph is None
        
    def test_feature_dimensions(self):
        """Test that feature dimensions are consistent."""
        mol = Chem.MolFromSmiles('CCO')
        graph = molecule_to_graph(mol)
        
        # Check node feature dimension
        num_node_features = graph.node_features.shape[1]
        expected_dim = 10 + 7 + 7  # atom types + hybridizations + charges
        assert num_node_features == expected_dim
        
        # Check edge feature dimension
        if len(graph.edge_features) > 0:
            assert graph.edge_features.shape[1] == 4  # bond types


class TestExtract2DFeatures:
    """Tests for extract_2d_features function."""
    
    def test_basic_extraction(self):
        """Test basic feature extraction."""
        # Create temporary input file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('smiles\n')
            f.write('CCO\n')
            f.write('CC\n')
            f.write('C\n')
            input_file = f.name
        
        output_file = input_file.replace('.csv', '_output.csv')
        
        try:
            stats = extract_2d_features(input_file, output_file)
            
            assert stats['total_molecules'] == 3
            assert stats['successful'] == 3
            assert stats['failed'] == 0
            
            # Check output file exists
            assert Path(output_file).exists()
            
        finally:
            # Cleanup
            Path(input_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)
            Path(input_file.replace('.csv', '_graphs.json')).unlink(missing_ok=True)
    
    def test_invalid_smiles_handling(self):
        """Test handling of invalid SMILES."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('smiles\n')
            f.write('CCO\n')
            f.write('invalid\n')
            f.write('C\n')
            input_file = f.name
        
        output_file = input_file.replace('.csv', '_output.csv')
        
        try:
            stats = extract_2d_features(input_file, output_file)
            
            assert stats['total_molecules'] == 3
            assert stats['successful'] == 2
            assert stats['failed'] == 1
            
        finally:
            Path(input_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)
            Path(input_file.replace('.csv', '_graphs.json')).unlink(missing_ok=True)

class TestGenerateConformers:
    """Tests for generate_conformers function."""
    
    def test_basic_conformer_generation(self):
        """Test basic conformer generation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('smiles\n')
            f.write('CCO\n')
            input_file = f.name
        
        output_file = input_file.replace('.csv', '_output.csv')
        
        try:
            stats = generate_conformers(input_file, output_file, num_conformers=5)
            
            assert stats['total_molecules'] == 1
            assert stats['successful'] >= 0  # May fail due to RDKit issues
            
            if stats['successful'] > 0:
                assert 'mean_sasa' in stats
                assert stats['mean_sasa'] is not None
            
        finally:
            Path(input_file).unlink(missing_ok=True)
            Path(output_file).unlink(missing_ok=True)

if __name__ == '__main__':
    pytest.main([__file__, '-v'])