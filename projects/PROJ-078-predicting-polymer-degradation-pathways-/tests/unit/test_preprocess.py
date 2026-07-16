import pytest
import json
import os
from pathlib import Path
import tempfile
import numpy as np

# Import functions to test
from preprocess import (
    filter_missing_environmental_data,
    smiles_to_molecular_graph,
    is_polyester,
    filter_polyesters,
    apply_edge_dropout,
    canonicalize_smiles,
    compute_checksum,
    save_dataset
)
from data_models import MolecularGraph

class TestFilterMissingEnvironmentalData:
    def test_missing_env_excludes_record(self):
        """Test that records with missing environmental data are excluded."""
        records = [
            {'id': '1', 'smiles': 'CCO', 'temperature': 25, 'ph': 7.0, 'uv_intensity': 100},
            {'id': '2', 'smiles': 'CC', 'temperature': None, 'ph': 7.0, 'uv_intensity': 100},
            {'id': '3', 'smiles': 'CCC', 'temperature': 25, 'ph': None, 'uv_intensity': 100},
            {'id': '4', 'smiles': 'CCCC', 'temperature': 25, 'ph': 7.0, 'uv_intensity': None},
            {'id': '5', 'smiles': 'CCCCC', 'temperature': 25, 'ph': 7.0, 'uv_intensity': 100}
        ]
        
        filtered = filter_missing_environmental_data(records)
        
        assert len(filtered) == 2
        assert filtered[0]['id'] == '1'
        assert filtered[1]['id'] == '5'

class TestSmilesToMolecularGraph:
    def test_valid_smiles_conversion(self):
        """Test conversion of valid SMILES to MolecularGraph."""
        smiles = 'CCO'
        graph = smiles_to_molecular_graph(smiles)
        
        assert graph is not None
        assert graph.smiles == smiles
        assert graph.num_atoms == 3
        assert graph.num_bonds == 2

    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES returns None."""
        invalid_smiles = 'invalid_smiles_123'
        graph = smiles_to_molecular_graph(invalid_smiles)
        
        assert graph is None

class TestIsPolyester:
    def test_polyester_detection(self):
        """Test detection of polyester functional groups."""
        # Ethylene glycol terephthalate (PET) - typical polyester
        polyester_smiles = 'O=C(OCCOC(=O)c1ccc(C(=O)OCCOC(=O)c2ccc(C(=O)O)cc2)cc1)c3ccc(C(=O)O)cc3'
        assert is_polyester(polyester_smiles) is True
        
        # Ethanol - not a polyester
        non_polyester_smiles = 'CCO'
        assert is_polyester(non_polyester_smiles) is False

class TestFilterPolyesters:
    def test_filter_polyesters(self):
        """Test filtering of polyester records."""
        records = [
            {'id': '1', 'smiles': 'CCO'},  # Not polyester
            {'id': '2', 'smiles': 'O=C(OCCOC(=O)c1ccc(C(=O)OCCOC(=O)c2ccc(C(=O)O)cc2)cc1)c3ccc(C(=O)O)cc3'},  # Polyester
            {'id': '3', 'smiles': 'CC'}  # Not polyester
        ]
        
        filtered = filter_polyesters(records)
        
        assert len(filtered) == 1
        assert filtered[0]['id'] == '2'

class TestApplyEdgeDropout:
    def test_edge_dropout(self):
        """Test edge dropout preserves graph structure."""
        # Create a simple graph
        adj = [[0, 1, 0], [1, 0, 1], [0, 1, 0]]
        graph = MolecularGraph(
            smiles='CCC',
            num_atoms=3,
            num_bonds=2,
            molecular_weight=42.0,
            logp=1.5,
            adjacency_matrix=adj
        )
        
        # Apply dropout with 0% rate
        dropped_graph = apply_edge_dropout(graph, dropout_rate=0.0)
        assert dropped_graph.adjacency_matrix == adj
        
        # Apply dropout with 100% rate (all edges dropped)
        dropped_graph_full = apply_edge_dropout(graph, dropout_rate=1.0)
        assert dropped_graph_full.num_bonds == 0

class TestCanonicalizeSmiles:
    def test_canonicalization(self):
        """Test SMILES canonicalization."""
        smiles = 'CCO'
        canonical = canonicalize_smiles(smiles)
        
        assert canonical is not None
        assert canonical == smiles  # Simple case should remain same

class TestChecksumAndSave:
    def test_compute_checksum(self):
        """Test checksum computation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            checksum = compute_checksum(temp_path)
            assert len(checksum) == 64  # SHA256 hex length
        finally:
            os.unlink(temp_path)

    def test_save_dataset(self):
        """Test dataset saving and checksum generation."""
        records = [{'id': '1', 'data': 'test'}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, 'test.json')
            result = save_dataset(records, output_path)
            
            assert os.path.exists(output_path)
            assert 'checksum' in result
            assert result['record_count'] == 1
            assert result['type'] == 'raw'