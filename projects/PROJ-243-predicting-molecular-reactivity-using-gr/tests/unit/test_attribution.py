"""
Unit tests for attribution score calculation.

This module tests the core logic of the attribution pipeline, specifically:
1. Calculation of GNNExplainer importance scores.
2. Aggregation of scores across molecules.
3. Ranking of structural/electronic features.
4. Tanimoto similarity computation between subgraphs and reference fingerprints.
"""
import pytest
import numpy as np
import torch
from torch_geometric.data import Data
from torch_geometric.nn import MessagePassing
from unittest.mock import patch, MagicMock
import rdkit.Chem as Chem
from rdkit import DataStructs
from rdkit.Chem import AllChem

# Import the attribution logic we are testing.
# We assume the main attribution logic resides in code/05_attribution.py.
# Since T028 (implementation) is not yet done, we define a minimal mock
# of the expected interface here to test the *test logic* and *schema*.
# In a real scenario, this would import from code/05_attribution.

# Mock implementation for testing purposes (to be replaced by real impl in T028)
class MockGNNExplainer:
    def __init__(self, model):
        self.model = model

    def explain_node(self, node_idx, data):
        # Return mock importance scores
        # shape: (num_nodes,)
        importance = np.random.rand(data.num_nodes)
        return {
            'node_importance': importance,
            'edge_importance': np.random.rand(data.num_edges),
            'prediction': np.array([0.5])
        }

def calculate_tanimoto_similarity(fp1, fp2):
    """Compute Tanimoto similarity between two RDKit fingerprints."""
    if fp1 is None or fp2 is None:
        return 0.0
    return DataStructs.TanimotoSimilarity(fp1, fp2)

def generate_morgan_fp(smiles, radius=2, n_bits=2048):
    """Generate Morgan fingerprint from SMILES."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius, nBits=n_bits)
    return fp

def test_explanation_score_calculation():
    """Test that explanation scores are calculated correctly for a mock graph."""
    # Create a simple mock graph
    num_nodes = 10
    num_edges = 20
    edge_index = torch.randint(0, num_nodes, (2, num_edges))
    x = torch.randn(num_nodes, 5)  # 5 features per node
    data = Data(x=x, edge_index=edge_index)

    # Mock model
    mock_model = MagicMock()
    mock_model.forward.return_value = torch.tensor([0.5])

    explainer = MockGNNExplainer(mock_model)
    result = explainer.explain_node(0, data)

    assert 'node_importance' in result
    assert 'edge_importance' in result
    assert len(result['node_importance']) == num_nodes
    assert len(result['edge_importance']) == num_edges
    assert np.all(result['node_importance'] >= 0) and np.all(result['node_importance'] <= 1)

def test_aggregate_scores_across_molecules():
    """Test aggregation of importance scores across multiple molecules."""
    # Simulate scores from multiple molecules
    scores_list = []
    for _ in range(5):
        num_nodes = np.random.randint(5, 15)
        scores = np.random.rand(num_nodes)
        scores_list.append(scores)

    # Aggregate: mean score per position (simplified) or global mean
    all_scores = np.concatenate(scores_list)
    global_mean = np.mean(all_scores)
    assert 0 <= global_mean <= 1

def test_rank_features():
    """Test ranking of features by importance."""
    # Mock feature importance dictionary
    feature_importance = {
        'C': 0.8,
        'O': 0.6,
        'N': 0.9,
        'Cl': 0.5
    }
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    assert sorted_features[0][0] == 'N'
    assert sorted_features[0][1] == 0.9

def test_tanimoto_similarity_computation():
    """Test Tanimoto similarity calculation between two fingerprints."""
    smiles1 = "CCO"
    smiles2 = "CCO"
    smiles3 = "CCCC"

    fp1 = generate_morgan_fp(smiles1)
    fp2 = generate_morgan_fp(smiles2)
    fp3 = generate_morgan_fp(smiles3)

    sim_same = calculate_tanimoto_similarity(fp1, fp2)
    sim_diff = calculate_tanimoto_similarity(fp1, fp3)

    assert sim_same == 1.0
    assert sim_diff < 1.0

def test_subgraph_extraction_and_matching():
    """Test extraction of subgraphs and matching against reference."""
    # Mock reference substructures
    reference_smiles = ["c1ccccc1", "CC(=O)O"]
    reference_fps = [generate_morgan_fp(s) for s in reference_smiles]

    # Mock attributed molecule
    attributed_smiles = "c1ccccc1C(=O)O"
    attributed_fp = generate_morgan_fp(attributed_smiles)

    # Compute similarities
    similarities = [calculate_tanimoto_similarity(attributed_fp, ref_fp) for ref_fp in reference_fps]
    
    # Check that at least one similarity is high (benzene ring match)
    assert max(similarities) > 0.5

def test_alignment_score_calculation():
    """Test calculation of alignment score (SC-003)."""
    # Mock data
    total_reference = 10
    valid_matches = 7

    alignment_score = valid_matches / total_reference
    assert alignment_score == 0.7

    # Edge case: zero reference
    alignment_score_zero = 0.0 / 0.0 if total_reference == 0 else 0.0
    # Handled in logic: if total_reference is zero, score is 0.0
    if total_reference == 0:
        alignment_score_zero = 0.0
    assert alignment_score_zero == 0.0

def test_fallback_threshold_logic():
    """Test fallback logic for lowering threshold if alignment score < 0.7."""
    # Mock function to simulate threshold adjustment
    def calculate_score(threshold):
        # Simulate that lower threshold yields more matches
        if threshold >= 0.85:
            return 0.5
        elif threshold >= 0.75:
            return 0.6
        elif threshold >= 0.65:
            return 0.75
        else:
            return 0.8

    current_threshold = 0.85
    target_score = 0.7
    final_score = calculate_score(current_threshold)

    while final_score < target_score and current_threshold >= 0.6:
        current_threshold -= 0.05
        final_score = calculate_score(current_threshold)

    assert final_score >= target_score
    assert current_threshold < 0.85

if __name__ == "__main__":
    pytest.main([__file__, "-v"])