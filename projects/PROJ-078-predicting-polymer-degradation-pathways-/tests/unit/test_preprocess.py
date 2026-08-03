"""
Unit tests for the preprocessing pipeline.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

from preprocess import (
    smiles_to_graph,
    has_ester_group,
    handle_missing_environmental_data,
    process_smiles_to_graphs,
    load_processed_polyester_dataset,
    save_dataset
)


class TestSmilesToGraph:
    """Tests for SMILES to graph conversion."""

    def test_valid_smiles_conversion(self):
        """Test that valid SMILES strings are converted to graphs."""
        smiles = "CC(=O)O"  # Acetic acid (contains ester-like pattern)
        graph = smiles_to_graph(smiles)
        
        assert graph is not None
        assert "nodes" in graph
        assert "node_features" in graph
        assert "edges" in graph
        assert graph["num_nodes"] > 0

    def test_invalid_smiles_returns_none(self):
        """Test that invalid SMILES strings return None."""
        invalid_smiles = "invalid_smiles_123"
        graph = smiles_to_graph(invalid_smiles)
        
        assert graph is None

    def test_empty_smiles_returns_none(self):
        """Test that empty SMILES strings return None."""
        graph = smiles_to_graph("")
        
        assert graph is None

    def test_node_features_shape(self):
        """Test that node features have correct shape."""
        smiles = "CCO"  # Ethanol
        graph = smiles_to_graph(smiles)
        
        assert graph is not None
        node_features = graph["node_features"]
        
        # Each node should have 5 base features + 3 environmental
        for features in node_features:
            assert len(features) == 8  # 5 base + 3 env


class TestHasEsterGroup:
    """Tests for ester group detection."""

    def test_ester_detection_positive(self):
        """Test that ester groups are correctly detected."""
        # Ethyl acetate
        smiles = "CCOC(=O)C"
        assert has_ester_group(smiles) is True

        # Polyethylene terephthalate (simplified)
        smiles = "CC(=O)OC1=CC=C(C=C1)C(=O)O"
        assert has_ester_group(smiles) is True

    def test_ester_detection_negative(self):
        """Test that non-ester compounds are correctly identified."""
        # Ethanol (no ester)
        smiles = "CCO"
        assert has_ester_group(smiles) is False

        # Ethane (no ester)
        smiles = "CC"
        assert has_ester_group(smiles) is False

    def test_invalid_smiles_returns_false(self):
        """Test that invalid SMILES returns False."""
        assert has_ester_group("invalid") is False
        assert has_ester_group("") is False


class TestHandleMissingEnvironmentalData:
    """Tests for environmental data handling."""

    def test_missing_data_flagging(self):
        """Test that records with missing environmental data are flagged."""
        data = {
            "smiles": ["CCO", "CC(=O)O", "CC"],
            "temperature": [25.0, np.nan, 30.0],
            "ph": [7.0, 7.0, np.nan],
            "uv": [0.0, 0.0, 0.0]
        }
        df = pd.DataFrame(data)
        
        cleaned_df, flagged_df = handle_missing_environmental_data(df)
        
        assert len(cleaned_df) == 1  # Only first record is complete
        assert len(flagged_df) == 2  # Second and third have missing data

    def test_complete_data_no_flagging(self):
        """Test that complete data results in no flagged records."""
        data = {
            "smiles": ["CCO", "CC(=O)O"],
            "temperature": [25.0, 30.0],
            "ph": [7.0, 8.0],
            "uv": [0.0, 1.0]
        }
        df = pd.DataFrame(data)
        
        cleaned_df, flagged_df = handle_missing_environmental_data(df)
        
        assert len(cleaned_df) == 2
        assert len(flagged_df) == 0

    def test_flagged_file_creation(self):
        """Test that flagged records are saved to file."""
        data = {
            "smiles": ["CCO", "CC(=O)O"],
            "temperature": [25.0, np.nan],
            "ph": [7.0, 7.0],
            "uv": [0.0, 0.0]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "flagged_env_data.csv"
            cleaned_df, flagged_df = handle_missing_environmental_data(df, str(output_path))
            
            assert output_path.exists()
            assert len(pd.read_csv(output_path)) == 1


class TestProcessSmilesToGraphs:
    """Tests for full SMILES to graphs processing."""

    def test_process_valid_records(self):
        """Test processing of valid records."""
        data = {
            "smiles": ["CC(=O)O", "CCO"],
            "degradation_pathway": ["hydrolysis", "oxidation"],
            "temperature": [25.0, 30.0],
            "ph": [7.0, 8.0],
            "uv": [0.0, 1.0]
        }
        df = pd.DataFrame(data)
        
        graphs_df = process_smiles_to_graphs(df)
        
        assert len(graphs_df) == 2
        assert "graph_data" in graphs_df.columns
        assert all(graphs_df["success"])

    def test_process_mixed_validity(self):
        """Test processing with mixed valid/invalid records."""
        data = {
            "smiles": ["CC(=O)O", "invalid", "CCO"],
            "degradation_pathway": ["hydrolysis", "unknown", "oxidation"],
            "temperature": [25.0, 25.0, 30.0],
            "ph": [7.0, 7.0, 8.0],
            "uv": [0.0, 0.0, 1.0]
        }
        df = pd.DataFrame(data)
        
        graphs_df = process_smiles_to_graphs(df)
        
        # Should only have 2 valid records
        assert len(graphs_df) == 2
        assert graphs_df["success"].all()


class TestSaveDataset:
    """Tests for dataset saving."""

    def test_save_to_parquet(self):
        """Test saving dataset to parquet format."""
        data = {
            "smiles": ["CC(=O)O"],
            "degradation_pathway": ["hydrolysis"],
            "graph_data": [[{"nodes": [0], "num_nodes": 1}]]
        }
        df = pd.DataFrame(data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_graphs.parquet"
            saved_path = save_dataset(df, str(output_path))
            
            assert os.path.exists(saved_path)
            assert saved_path.endswith(".parquet")
            
            # Verify we can read it back
            loaded_df = pd.read_parquet(saved_path)
            assert len(loaded_df) == 1