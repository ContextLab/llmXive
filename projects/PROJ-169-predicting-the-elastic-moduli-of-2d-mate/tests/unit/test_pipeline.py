"""
Unit tests for the data ingestion pipeline (T013).
"""
import pytest
import os
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock imports to avoid heavy dependencies in unit tests if possible,
# but we need the actual classes to test serialization.
from data_models.material_graph import MaterialGraph
from ingest.pipeline import serialize_graph, run_pipeline
from ingest.filter import FilterStats

def test_serialize_graph_valid():
    """Test serialization of a valid MaterialGraph."""
    graph = MaterialGraph(
        material_id="test-123",
        formula="MoS2",
        family_id="TMD",
        node_features=np.array([[1.0, 2.0], [3.0, 4.0]]),
        edge_features=np.array([[0.5], [0.6]]),
        target_moduli=np.eye(6), # 6x6 identity
        space_group="187",
        num_atoms=3
    )
    
    result = serialize_graph(graph)
    
    assert result["material_id"] == "test-123"
    assert result["formula"] == "MoS2"
    assert result["family_id"] == "TMD"
    assert result["space_group"] == "187"
    assert result["num_atoms"] == 3
    assert "node_features" in result
    assert "edge_features" in result
    assert "target_moduli" in result
    
    # Check types
    assert isinstance(result["node_features"], list)
    assert isinstance(result["target_moduli"], list)

def test_serialize_graph_missing_tensor():
    """Test that serialization fails gracefully for missing tensor."""
    graph = MaterialGraph(
        material_id="test-456",
        formula="Fake",
        family_id="Fake",
        node_features=np.array([[1.0]]),
        edge_features=np.array([[0.5]]),
        target_moduli=None, # Missing
        space_group="1",
        num_atoms=1
    )
    
    with pytest.raises(ValueError, match="missing target_moduli"):
        serialize_graph(graph)

def test_serialize_graph_missing_features():
    """Test that serialization fails for missing features."""
    graph = MaterialGraph(
        material_id="test-789",
        formula="Fake",
        family_id="Fake",
        node_features=None,
        edge_features=np.array([[0.5]]),
        target_moduli=np.eye(6),
        space_group="1",
        num_atoms=1
    )
    
    with pytest.raises(ValueError, match="missing features"):
        serialize_graph(graph)

@patch('ingest.pipeline.UnifiedDatasetLoader')
@patch('ingest.pipeline.parse_cif_directory')
@patch('ingest.pipeline.filter_graphs')
@patch('ingest.pipeline.save_filter_stats')
@patch('ingest.pipeline.analyze_exclusion_bias')
@patch('ingest.pipeline.write_bias_report')
def test_run_pipeline_mocked(
    mock_write_bias, mock_analyze_bias, mock_save_stats, mock_filter, mock_parse, mock_loader
):
    """Test the pipeline execution with mocked dependencies."""
    # Setup mocks
    mock_loader_instance = MagicMock()
    mock_manifest = MagicMock()
    mock_manifest.cif_dir = Path("/fake/cif_dir")
    mock_loader_instance.run.return_value = mock_manifest
    mock_loader.return_value = mock_loader_instance
    
    # Mock parsed graphs
    mock_graph = MagicMock(spec=MaterialGraph)
    mock_graph.material_id = "m1"
    mock_graph.formula = "X"
    mock_graph.family_id = "F1"
    mock_graph.node_features = np.array([[1.0]])
    mock_graph.edge_features = np.array([[0.5]])
    mock_graph.target_moduli = np.eye(6)
    mock_graph.space_group = "1"
    mock_graph.num_atoms = 1
    
    mock_parse.return_value = [mock_graph]
    
    # Mock filter result
    mock_filter.return_value = ([mock_graph], FilterStats(1, 1, 0, []))
    
    # Mock config
    mock_config = MagicMock()
    mock_config.paths.processed = Path("/fake/output")
    mock_config.paths.raw = Path("/fake/raw")
    mock_config.paths.logs = Path("/fake/logs")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        mock_config.paths.processed = out_dir
        
        result_path = run_pipeline(
            config=mock_config,
            source_type="local_cif_dir",
            source_id="test",
            output_dir=out_dir
        )
        
        assert result_path.exists()
        assert result_path.name == "graphs_v1.parquet"
        
        # Verify calls
        mock_loader.assert_called_once()
        mock_parse.assert_called_once()
        mock_filter.assert_called_once()
        mock_save_stats.assert_called_once()
        mock_analyze_bias.assert_called_once()
        mock_write_bias.assert_called_once()