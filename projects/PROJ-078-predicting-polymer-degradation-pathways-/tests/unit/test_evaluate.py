"""
Unit tests for evaluate.py functionality.
Specifically for T024b: Ester Attribution Check.
"""
import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np

# Mock torch and rdkit to avoid heavy dependencies in unit tests
# We will mock the imports in the evaluate module
import sys
from unittest.mock import Mock

# Create a mock for torch
mock_torch = MagicMock()
mock_torch.device = MagicMock(return_value='cpu')
mock_torch.load = MagicMock(return_value={'config': {}, 'model_state': {}})
sys.modules['torch'] = mock_torch
sys.modules['torch.nn'] = MagicMock()
sys.modules['torch.nn.functional'] = MagicMock()
sys.modules['torch_geometric'] = MagicMock()
sys.modules['torch_geometric.nn'] = MagicMock()
sys.modules['torch_geometric.data'] = MagicMock()

# Create a mock for rdkit
mock_rdkit = MagicMock()
mock_chem = MagicMock()
mock_mol = MagicMock()
mock_bond = MagicMock()
mock_bond.GetIdx = MagicMock(return_value=0)
mock_mol.GetBonds = MagicMock(return_value=[mock_bond])
mock_chem.MolFromSmiles = MagicMock(return_value=mock_mol)
mock_rdkit.Chem = mock_chem
sys.modules['rdkit'] = mock_rdkit
sys.modules['rdkit.Chem'] = mock_chem

# Now import the module under test
# We need to ensure the mocks are in place before importing
from evaluate import calculate_ester_attribution_percentage, DEGRADATION_LABEL_HYDROLYSIS

def test_calculate_ester_attribution_percentage_empty_predictions():
    """Test with no hydrolysis cases."""
    predictions = [
        {"smiles": "CCO", "true_label": "oxidation"},
        {"smiles": "CCC", "true_label": "photolysis"}
    ]
    model = MagicMock()
    ig = MagicMock()
    
    result = calculate_ester_attribution_percentage(predictions, model, ig)
    
    assert result["total_hydrolysis_cases"] == 0
    assert result["cases_with_ester_in_top_k"] == 0
    assert result["percentage"] == 0.0
    assert result["threshold_met"] == False

def test_calculate_ester_attribution_percentage_no_ester_bonds():
    """Test case where SMILES has no ester bonds."""
    predictions = [
        {"smiles": "CCCC", "true_label": "hydrolysis"} # Alkane, no ester
    ]
    model = MagicMock()
    ig = MagicMock()
    
    # Mock is_ester_bond to return False for all bonds
    with patch('evaluate.is_ester_bond', return_value=False):
        result = calculate_ester_attribution_percentage(predictions, model, ig)
        
        # Should skip this case as no ester bonds found
        assert result["total_hydrolysis_cases"] == 1
        assert result["cases_with_ester_in_top_k"] == 0
        assert result["percentage"] == 0.0

def test_calculate_ester_attribution_percentage_success():
    """Test case where ester bond is in top attribution."""
    # Mock data
    predictions = [
        {"smiles": "CC(=O)OC", "true_label": "hydrolysis"} # Ester
    ]
    model = MagicMock()
    ig = MagicMock()
    
    # Mock the graph conversion and IG computation
    mock_graph = MagicMock()
    mock_graph.edge_index = MagicMock()
    
    # Mock is_ester_bond to return True for the bond
    with patch('evaluate.is_ester_bond', return_value=True):
        with patch('evaluate.smiles_to_molecular_graph', return_value=mock_graph):
            # Mock IG to return attributions where the first bond (ester) has high score
            mock_attr = MagicMock()
            mock_attr.dim = MagicMock(return_value=1)
            mock_attr.detach = MagicMock(return_value=mock_attr)
            mock_attr.cpu = MagicMock(return_value=mock_attr)
            mock_attr.numpy = MagicMock(return_value=np.array([0.9, 0.1])) # First bond is high
            ig.compute = MagicMock(return_value=mock_attr)
            
            result = calculate_ester_attribution_percentage(predictions, model, ig)
            
            assert result["total_hydrolysis_cases"] == 1
            assert result["cases_with_ester_in_top_k"] == 1
            assert result["percentage"] == 100.0
            assert result["threshold_met"] == True

def test_calculate_ester_attribution_percentage_failure():
    """Test case where ester bond is NOT in top attribution."""
    predictions = [
        {"smiles": "CC(=O)OC", "true_label": "hydrolysis"}
    ]
    model = MagicMock()
    ig = MagicMock()
    
    mock_graph = MagicMock()
    mock_graph.edge_index = MagicMock()
    
    with patch('evaluate.is_ester_bond', return_value=True):
        with patch('evaluate.smiles_to_molecular_graph', return_value=mock_graph):
            # Mock IG to return attributions where the ester bond (index 0) is low
            mock_attr = MagicMock()
            mock_attr.dim = MagicMock(return_value=1)
            mock_attr.detach = MagicMock(return_value=mock_attr)
            mock_attr.cpu = MagicMock(return_value=mock_attr)
            mock_attr.numpy = MagicMock(return_value=np.array([0.1, 0.9])) # First bond is low
            ig.compute = MagicMock(return_value=mock_attr)
            
            result = calculate_ester_attribution_percentage(predictions, model, ig)
            
            assert result["total_hydrolysis_cases"] == 1
            assert result["cases_with_ester_in_top_k"] == 0
            assert result["percentage"] == 0.0
            assert result["threshold_met"] == False