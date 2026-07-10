"""
Unit tests for descriptor extraction module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from data.descriptors import (
    parse_smiles_to_molecule,
    generate_3d_conformer,
    extract_electronic_descriptors,
    extract_geometric_descriptors,
    extract_all_descriptors,
    run_descriptor_pipeline
)
from rdkit import Chem

class TestDescriptorExtraction:
    """Test suite for descriptor extraction functions."""
    
    @pytest.fixture
    def sample_smiles(self):
        """Provide sample SMILES strings for testing."""
        return [
            "CCO",  # Ethanol
            "CC(=O)OC",  # Ethyl acetate
            "C1=CC=CC=C1",  # Benzene
            "CC1=CC=CC=C1",  # Toluene
            "CC(=O)O",  # Acetic acid
        ]
    
    @pytest.fixture
    def sample_dataframe(self, sample_smiles):
        """Create a sample DataFrame for testing."""
        data = {
            'molecule_id': [f"MOL-{i:03d}" for i in range(len(sample_smiles))],
            'smiles': sample_smiles,
            'potential_v': [0.0, 2.0, 4.0, 0.0, 2.0]
        }
        return pd.DataFrame(data)
    
    def test_parse_smiles_to_molecule(self):
        """Test SMILES parsing functionality."""
        # Valid SMILES
        mol = parse_smiles_to_molecule("CCO")
        assert mol is not None
        assert mol.GetNumAtoms() > 0
        
        # Invalid SMILES
        mol_invalid = parse_smiles_to_molecule("invalid_smiles")
        assert mol_invalid is None
    
    def test_generate_3d_conformer(self):
        """Test 3D conformer generation."""
        mol = Chem.MolFromSmiles("CCO")
        mol = Chem.AddHs(mol)
        
        success = generate_3d_conformer(mol)
        assert success is True
        
        # Check that conformer exists
        conf = mol.GetConformer()
        assert conf is not None
    
    def test_extract_electronic_descriptors(self, sample_smiles):
        """Test electronic descriptor extraction."""
        for smiles in sample_smiles:
            mol = parse_smiles_to_molecule(smiles)
            if mol:
                generate_3d_conformer(mol)
                descriptors = extract_electronic_descriptors(mol)
                
                # Check required keys exist
                assert 'homo' in descriptors
                assert 'lumo' in descriptors
                assert 'band_gap' in descriptors
                
                # Check values are floats
                assert isinstance(descriptors['homo'], float)
                assert isinstance(descriptors['lumo'], float)
                assert isinstance(descriptors['band_gap'], float)
                
                # Check band gap is positive (non-metallic)
                # Note: Some molecules might be flagged as metallic
                assert descriptors['band_gap'] >= 0.0
    
    def test_extract_geometric_descriptors(self, sample_smiles):
        """Test geometric descriptor extraction."""
        for smiles in sample_smiles:
            mol = parse_smiles_to_molecule(smiles)
            if mol:
                generate_3d_conformer(mol)
                descriptors = extract_geometric_descriptors(mol)
                
                # Check required keys exist
                assert 'avg_bond_length' in descriptors
                assert 'min_bond_length' in descriptors
                assert 'max_bond_length' in descriptors
                assert 'avg_bond_angle' in descriptors
                assert 'num_atoms' in descriptors
                assert 'molecular_weight' in descriptors
                
                # Check bond lengths are positive
                assert descriptors['avg_bond_length'] > 0
                assert descriptors['min_bond_length'] > 0
                assert descriptors['max_bond_length'] > 0
                
                # Check angles are in valid range
                assert 0 <= descriptors['avg_bond_angle'] <= 180
    
    def test_extract_all_descriptors(self, sample_dataframe):
        """Test full descriptor extraction on DataFrame."""
        result_df = extract_all_descriptors(sample_dataframe)
        
        # Check result is not empty
        assert not result_df.empty
        assert len(result_df) == len(sample_dataframe)
        
        # Check required columns exist
        required_cols = [
            'molecule_id', 'potential_v',
            'homo', 'lumo', 'band_gap',
            'avg_bond_length', 'min_bond_length', 'max_bond_length',
            'avg_bond_angle', 'num_atoms', 'molecular_weight'
        ]
        
        for col in required_cols:
            assert col in result_df.columns
        
        # Check no missing values in numeric columns
        numeric_cols = result_df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            assert not result_df[col].isna().any()
    
    def test_descriptor_ranges(self, sample_dataframe):
        """Test that extracted descriptors are within reasonable ranges."""
        result_df = extract_all_descriptors(sample_dataframe)
        
        # Bond lengths should be between 0.5 and 3.0 Angstroms
        assert all(result_df['min_bond_length'] >= 0.5)
        assert all(result_df['max_bond_length'] <= 3.0)
        
        # Bond angles should be between 0 and 180 degrees
        assert all(result_df['min_bond_angle'] >= 0)
        assert all(result_df['max_bond_angle'] <= 180)
        
        # HOMO should be negative (typical for stable molecules)
        # LUMO should be greater than HOMO
        assert all(result_df['lumo'] >= result_df['homo'])
        
        # Band gap should be non-negative
        assert all(result_df['band_gap'] >= 0)
    
    def test_metallic_outlier_detection(self):
        """Test that metallic outliers are properly detected."""
        # Create a molecule that might be flagged as metallic
        # (This is a simplified test - real metallic detection depends on the calculation)
        smiles = "C1=CC=CC=C1"  # Benzene
        mol = parse_smiles_to_molecule(smiles)
        if mol:
            generate_3d_conformer(mol)
            descriptors = extract_electronic_descriptors(mol)
            
            # At minimum, the function should not crash
            assert isinstance(descriptors['band_gap'], float)
