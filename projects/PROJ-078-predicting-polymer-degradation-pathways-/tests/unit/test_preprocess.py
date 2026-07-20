import pytest
import numpy as np
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from rdkit import Chem

# Import the functions we're testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

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
from data_models import PolymerRecord, MolecularGraph


class TestFilterMissingEnvironmentalData:
    """Tests for filter_missing_environmental_data function"""
    
    def test_all_records_valid(self):
        """Test that all records pass when all environmental data is present"""
        records = [
            PolymerRecord(
                id="1", smiles="CCO", degradation_label="hydrolysis",
                temperature=25.0, ph=7.0, uv_intensity=100.0,
                source="test", timestamp="2024-01-01"
            ),
            PolymerRecord(
                id="2", smiles="CCC", degradation_label="oxidation",
                temperature=30.0, ph=6.5, uv_intensity=150.0,
                source="test", timestamp="2024-01-02"
            )
        ]
        
        filtered, excluded = filter_missing_environmental_data(records)
        
        assert len(filtered) == 2
        assert excluded == 0
    
    def test_missing_temperature_excludes(self):
        """Test that records with missing temperature are excluded"""
        records = [
            PolymerRecord(
                id="1", smiles="CCO", degradation_label="hydrolysis",
                temperature=None, ph=7.0, uv_intensity=100.0,
                source="test", timestamp="2024-01-01"
            ),
            PolymerRecord(
                id="2", smiles="CCC", degradation_label="oxidation",
                temperature=30.0, ph=6.5, uv_intensity=150.0,
                source="test", timestamp="2024-01-02"
            )
        ]
        
        filtered, excluded = filter_missing_environmental_data(records)
        
        assert len(filtered) == 1
        assert excluded == 1
        assert filtered[0].id == "2"
    
    def test_missing_ph_excludes(self):
        """Test that records with missing pH are excluded"""
        records = [
            PolymerRecord(
                id="1", smiles="CCO", degradation_label="hydrolysis",
                temperature=25.0, ph=None, uv_intensity=100.0,
                source="test", timestamp="2024-01-01"
            ),
            PolymerRecord(
                id="2", smiles="CCC", degradation_label="oxidation",
                temperature=30.0, ph=6.5, uv_intensity=150.0,
                source="test", timestamp="2024-01-02"
            )
        ]
        
        filtered, excluded = filter_missing_environmental_data(records)
        
        assert len(filtered) == 1
        assert excluded == 1
    
    def test_missing_uv_excludes(self):
        """Test that records with missing UV intensity are excluded"""
        records = [
            PolymerRecord(
                id="1", smiles="CCO", degradation_label="hydrolysis",
                temperature=25.0, ph=7.0, uv_intensity=None,
                source="test", timestamp="2024-01-01"
            ),
            PolymerRecord(
                id="2", smiles="CCC", degradation_label="oxidation",
                temperature=30.0, ph=6.5, uv_intensity=150.0,
                source="test", timestamp="2024-01-02"
            )
        ]
        
        filtered, excluded = filter_missing_environmental_data(records)
        
        assert len(filtered) == 1
        assert excluded == 1
    
    def test_nan_values_excluded(self):
        """Test that NaN values are excluded"""
        records = [
            PolymerRecord(
                id="1", smiles="CCO", degradation_label="hydrolysis",
                temperature=float('nan'), ph=7.0, uv_intensity=100.0,
                source="test", timestamp="2024-01-01"
            ),
            PolymerRecord(
                id="2", smiles="CCC", degradation_label="oxidation",
                temperature=30.0, ph=6.5, uv_intensity=150.0,
                source="test", timestamp="2024-01-02"
            )
        ]
        
        filtered, excluded = filter_missing_environmental_data(records)
        
        assert len(filtered) == 1
        assert excluded == 1
    
    def test_empty_string_values_excluded(self):
        """Test that empty string values are excluded"""
        records = [
            PolymerRecord(
                id="1", smiles="CCO", degradation_label="hydrolysis",
                temperature="", ph=7.0, uv_intensity=100.0,
                source="test", timestamp="2024-01-01"
            ),
            PolymerRecord(
                id="2", smiles="CCC", degradation_label="oxidation",
                temperature=30.0, ph=6.5, uv_intensity=150.0,
                source="test", timestamp="2024-01-02"
            )
        ]
        
        filtered, excluded = filter_missing_environmental_data(records)
        
        assert len(filtered) == 1
        assert excluded == 1
    
    def test_all_records_excluded(self):
        """Test when all records have missing data"""
        records = [
            PolymerRecord(
                id="1", smiles="CCO", degradation_label="hydrolysis",
                temperature=None, ph=None, uv_intensity=None,
                source="test", timestamp="2024-01-01"
            )
        ]
        
        filtered, excluded = filter_missing_environmental_data(records)
        
        assert len(filtered) == 0
        assert excluded == 1


class TestSmilesToMolecularGraph:
    """Tests for smiles_to_molecular_graph function"""
    
    def test_valid_ethanol_conversion(self):
        """Test conversion of valid ethanol SMILES"""
        smiles = "CCO"
        graph = smiles_to_molecular_graph(smiles)
        
        assert graph is not None
        assert graph.smiles == smiles
        assert graph.num_nodes == 3  # 2 C, 1 O
        assert graph.x.shape[0] == 3
        assert graph.edge_index.shape[1] > 0
    
    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES returns None"""
        invalid_smiles = "invalid_smiles_string"
        graph = smiles_to_molecular_graph(invalid_smiles)
        
        assert graph is None
    
    def test_empty_molecule_returns_none(self):
        """Test that empty molecule returns None"""
        # Empty molecule SMILES
        graph = smiles_to_molecular_graph("")
        
        assert graph is None
    
    def test_graph_has_correct_features(self):
        """Test that graph has correct feature dimensions"""
        smiles = "CCO"
        graph = smiles_to_molecular_graph(smiles)
        
        assert graph is not None
        # x should have 5 features per atom (atomic_num, degree, formal_charge, hybridization, aromatic)
        assert graph.x.shape[1] == 5


class TestIsPolyester:
    """Tests for is_polyester function"""
    
    def test_polyester_detection(self):
        """Test detection of ester group in polyester"""
        # Polyethylene terephthalate (PET) monomer
        smiles = "CC(=O)OC"
        assert is_polyester(smiles) is True
    
    def test_non_polyester_detection(self):
        """Test non-detection in non-polyester"""
        # Simple alcohol
        smiles = "CCO"
        assert is_polyester(smiles) is False
    
    def test_invalid_smiles_returns_false(self):
        """Test that invalid SMILES returns False"""
        assert is_polyester("invalid") is False
    
    def test_empty_smiles_returns_false(self):
        """Test that empty SMILES returns False"""
        assert is_polyester("") is False


class TestFilterPolyesters:
    """Tests for filter_polyesters function"""
    
    def test_filter_polyesters(self):
        """Test filtering to only polyesters"""
        records = [
            PolymerRecord(
                id="1", smiles="CC(=O)OC", degradation_label="hydrolysis",
                temperature=25.0, ph=7.0, uv_intensity=100.0,
                source="test", timestamp="2024-01-01"
            ),
            PolymerRecord(
                id="2", smiles="CCO", degradation_label="oxidation",
                temperature=30.0, ph=6.5, uv_intensity=150.0,
                source="test", timestamp="2024-01-02"
            ),
            PolymerRecord(
                id="3", smiles="CC(=O)OCC(=O)O", degradation_label="hydrolysis",
                temperature=35.0, ph=7.5, uv_intensity=200.0,
                source="test", timestamp="2024-01-03"
            )
        ]
        
        filtered, excluded = filter_polyesters(records)
        
        assert len(filtered) == 2
        assert excluded == 1
        assert filtered[0].id == "1"
        assert filtered[1].id == "3"


class TestApplyEdgeDropout:
    """Tests for apply_edge_dropout function"""
    
    def test_no_dropout(self):
        """Test that dropout_rate=0 preserves all edges"""
        smiles = "CCO"
        original_graph = smiles_to_molecular_graph(smiles)
        
        dropped_graph = apply_edge_dropout(original_graph, dropout_rate=0.0)
        
        assert dropped_graph.num_edges == original_graph.num_edges
    
    def test_dropout_preserves_nodes(self):
        """Test that dropout preserves all nodes"""
        smiles = "CCO"
        original_graph = smiles_to_molecular_graph(smiles)
        
        dropped_graph = apply_edge_dropout(original_graph, dropout_rate=1.0)
        
        # Even with 100% dropout, nodes should remain
        assert dropped_graph.num_nodes == original_graph.num_nodes


class TestCanonicalizeSmiles:
    """Tests for canonicalize_smiles function"""
    
    def test_canonicalization(self):
        """Test that canonicalization produces consistent output"""
        smiles1 = "CCO"
        smiles2 = "OCC"  # Same molecule, different representation
        
        canon1 = canonicalize_smiles(smiles1)
        canon2 = canonicalize_smiles(smiles2)
        
        assert canon1 is not None
        assert canon2 is not None
        assert canon1 == canon2  # Same canonical form
    
    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES returns None"""
        assert canonicalize_smiles("invalid") is None


class TestComputeChecksum:
    """Tests for compute_checksum function"""
    
    def test_string_checksum(self):
        """Test checksum computation for string"""
        data = "test data"
        checksum = compute_checksum(data)
        
        assert len(checksum) == 64  # SHA-256 hex length
        assert checksum.islower()
    
    def test_bytes_checksum(self):
        """Test checksum computation for bytes"""
        data = b"test data"
        checksum = compute_checksum(data)
        
        assert len(checksum) == 64
    
    def test_deterministic(self):
        """Test that checksum is deterministic"""
        data = "test data"
        checksum1 = compute_checksum(data)
        checksum2 = compute_checksum(data)
        
        assert checksum1 == checksum2


class TestSaveDataset:
    """Tests for save_dataset function"""
    
    def test_save_dataset_creates_file(self, tmp_path):
        """Test that save_dataset creates the output file"""
        records = [
            PolymerRecord(
                id="1", smiles="CCO", degradation_label="hydrolysis",
                temperature=25.0, ph=7.0, uv_intensity=100.0,
                source="test", timestamp="2024-01-01"
            )
        ]
        graphs = [smiles_to_molecular_graph("CCO")]
        
        output_path = tmp_path / "test_dataset.json"
        result_path = save_dataset(records, graphs, str(output_path))
        
        assert os.path.exists(result_path)
        assert os.path.exists(str(output_path) + '.sha256')
    
    def test_save_dataset_content(self, tmp_path):
        """Test that saved dataset has correct content"""
        records = [
            PolymerRecord(
                id="1", smiles="CCO", degradation_label="hydrolysis",
                temperature=25.0, ph=7.0, uv_intensity=100.0,
                source="test", timestamp="2024-01-01"
            )
        ]
        graphs = [smiles_to_molecular_graph("CCO")]
        
        output_path = tmp_path / "test_dataset.json"
        save_dataset(records, graphs, str(output_path))
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data['num_records'] == 1
        assert data['records'][0]['id'] == "1"
        assert data['records'][0]['smiles'] == "CCO"