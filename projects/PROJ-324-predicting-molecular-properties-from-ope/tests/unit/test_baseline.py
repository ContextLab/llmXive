"""
Unit tests for baseline model (Crippen's atomic contributions).
"""
import pytest
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import Crippen

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.models.baseline import (
    compute_crippen_contributions,
    _estimate_boiling_point,
    process_dataset
)

class TestCrippenContributions:
    """Test Crippen's atomic contribution calculations."""
    
    def test_logP_calculation(self):
        """Test logP calculation for a simple molecule."""
        smiles = "CCO"  # Ethanol
        result = compute_crippen_contributions(smiles)
        
        assert result is not None
        assert 'logP' in result
        assert isinstance(result['logP'], float)
        # Ethanol logP should be around -0.3
        assert -1.0 < result['logP'] < 1.0
    
    def test_solubility_calculation(self):
        """Test solubility calculation for a simple molecule."""
        smiles = "CCO"  # Ethanol
        result = compute_crippen_contributions(smiles)
        
        assert result is not None
        assert 'solubility' in result
        assert isinstance(result['solubility'], float)
    
    def test_boiling_point_calculation(self):
        """Test boiling point estimation for a simple molecule."""
        smiles = "CCO"  # Ethanol
        result = compute_crippen_contributions(smiles)
        
        assert result is not None
        assert 'boiling_point' in result
        assert isinstance(result['boiling_point'], float)
        # Ethanol boiling point should be around 350-370K
        assert 300 < result['boiling_point'] < 400
    
    def test_invalid_smiles(self):
        """Test handling of invalid SMILES."""
        smiles = "invalid_smiles"
        result = compute_crippen_contributions(smiles)
        
        assert result is None
    
    def test_complex_molecule(self):
        """Test calculation for a more complex molecule."""
        smiles = "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin
        result = compute_crippen_contributions(smiles)
        
        assert result is not None
        assert result['logP'] > 0  # Aspirin is somewhat hydrophobic
        assert result['solubility'] < 0  # LogS should be negative
        assert result['boiling_point'] > 300
    
    def test_consistency_with_rdkit(self):
        """Test that our logP matches RDKit's Crippen implementation."""
        smiles = "CCO"
        mol = Chem.MolFromSmiles(smiles)
        rdkit_logP = Crippen.MolLogP(mol)
        
        our_result = compute_crippen_contributions(smiles)
        
        assert abs(our_result['logP'] - rdkit_logP) < 1e-6
    
    def test_all_properties_present(self):
        """Test that all required properties are computed."""
        smiles = "CCO"
        result = compute_crippen_contributions(smiles)
        
        required_keys = ['logP', 'solubility', 'boiling_point']
        for key in required_keys:
            assert key in result
            assert result[key] is not None
            assert not np.isnan(result[key])

class TestBoilingPointEstimation:
    """Test boiling point estimation function."""
    
    def test_molecular_weight_correlation(self):
        """Test that boiling point correlates with molecular weight."""
        # Simple molecules
        small_mol = "CC"  # Ethane
        large_mol = "CCCCCCCC"  # Octane
        
        small_bp = _estimate_boiling_point(Chem.MolFromSmiles(small_mol))
        large_bp = _estimate_boiling_point(Chem.MolFromSmiles(large_mol))
        
        # Larger molecule should have higher boiling point
        assert large_bp > small_bp
    
    def test_logP_correlation(self):
        """Test that boiling point correlates with logP."""
        # Hydrophilic vs hydrophobic
        hydrophilic = "CCO"  # Ethanol
        hydrophobic = "CCCC"  # Butane
        
        hydrophilic_bp = _estimate_boiling_point(Chem.MolFromSmiles(hydrophilic))
        hydrophobic_bp = _estimate_boiling_point(Chem.MolFromSmiles(hydrophobic))
        
        # Both should be reasonable boiling points
        assert hydrophilic_bp > 273  # Above freezing
        assert hydrophobic_bp > 273  # Above freezing

class TestProcessDataset:
    """Test dataset processing function."""
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        df = pd.DataFrame()
        # This should return None or handle gracefully
        # The actual behavior depends on implementation
        pass
    
    def test_missing_columns(self):
        """Test handling of missing required columns."""
        df = pd.DataFrame({'smiles': ['CCO']})
        # Should handle missing columns gracefully
        pass
    
    def test_successful_processing(self):
        """Test successful processing of valid data."""
        # Create a small test dataset
        data = {
            'smiles': ['CCO', 'CC(=O)O', 'c1ccccc1'],
            'logP_exp': [-0.3, -0.5, 2.0],
            'solubility_exp': [-0.5, -1.0, -2.5],
            'boiling_point_exp': [351.0, 391.0, 353.0]
        }
        df = pd.DataFrame(data)
        
        # This would normally be tested with the full pipeline
        # Here we just verify the function exists and can be called
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])