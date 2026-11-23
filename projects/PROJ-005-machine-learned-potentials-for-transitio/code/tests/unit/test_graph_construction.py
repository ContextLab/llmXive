import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock

from src.data.graph_construction import (
    calculate_distance_matrix,
    build_adjacency_matrix,
    calculate_graph_metrics,
    analyze_cutoff,
    run_sensitivity_analysis,
    save_results
)

class TestGraphConstructionUtils:
    def test_calculate_distance_matrix(self):
        # Simple 3 points in 2D
        positions = [[0.0, 0.0], [3.0, 0.0], [0.0, 4.0]]
        dists = calculate_distance_matrix(positions)
        
        assert dists.shape == (3, 3)
        assert np.isclose(dists[0, 1], 3.0)
        assert np.isclose(dists[0, 2], 4.0)
        assert np.isclose(dists[1, 2], 5.0) # 3-4-5 triangle
        assert np.allclose(np.diag(dists), 0.0)

    def test_build_adjacency_matrix(self):
        dists = np.array([
            [0.0, 2.5, 5.0],
            [2.5, 0.0, 3.0],
            [5.0, 3.0, 0.0]
        ])
        
        # Cutoff 3.0
        adj = build_adjacency_matrix(dists, 3.0)
        expected = np.array([
            [0, 1, 0],
            [1, 0, 1],
            [0, 1, 0]
        ])
        np.testing.assert_array_equal(adj, expected)

    def test_calculate_graph_metrics(self):
        adj = np.array([
            [0, 1, 1],
            [1, 0, 0],
            [1, 0, 0]
        ])
        num_nodes = 3
        edge_count = 2 # (0,1) and (0,2)
        
        metrics = calculate_graph_metrics(adj, edge_count, num_nodes)
        
        assert metrics['avg_degree'] == 4.0 / 3.0
        assert metrics['edge_count'] == 2
        assert metrics['density'] == 2.0 / 9.0
        assert metrics['num_nodes'] == 3

class TestAnalyzeCutoff:
    @pytest.fixture
    def mock_df(self):
        # Create a mock dataframe with one simple graph
        data = {
            'atomic_numbers': [[6, 6, 6]],
            'positions': [[[0.0, 0.0, 0.0], [1.5, 0.0, 0.0], [3.0, 0.0, 0.0]]]
        }
        return pd.DataFrame(data)

    def test_analyze_cutoff_single_graph(self, mock_df):
        # Cutoff 2.0: Only 0-1 connected
        # Cutoff 3.5: 0-1 and 1-2 connected (0-2 is 3.0, so also connected if cutoff >= 3.0)
        
        # Test with cutoff 2.0
        metrics = analyze_cutoff(mock_df, 2.0)
        assert metrics['cutoff'] == 2.0
        assert metrics['total_nodes'] == 3
        # 0-1 is 1.5, 1-2 is 1.5. 0-2 is 3.0.
        # Edges: (0,1), (1,2). Total 2 edges.
        assert metrics['total_edges'] == 2
        
        # Test with cutoff 3.5
        metrics = analyze_cutoff(mock_df, 3.5)
        # Edges: (0,1), (1,2), (0,2). Total 3 edges.
        assert metrics['total_edges'] == 3

class TestRunSensitivityAnalysis:
    @patch('src.data.graph_construction.load_processed_graphs_intermediate')
    def test_run_sensitivity_analysis(self, mock_load):
        # Mock data
        mock_df = pd.DataFrame({
            'atomic_numbers': [[1, 1]],
            'positions': [[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]]
        })
        mock_load.return_value = mock_df

        results = run_sensitivity_analysis(cutoffs=[1.0, 2.0])
        
        assert 'cutoffs_analyzed' in results
        assert results['cutoffs_analyzed'] == [1.0, 2.0]
        assert len(results['results']) == 2
        
        # Check structure of first result
        r1 = results['results'][0]
        assert 'cutoff' in r1
        assert 'avg_degree' in r1
        assert 'density' in r1

class TestSaveResults:
    def test_save_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.json"
            data = {"test": 123}
            
            save_results(data, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                loaded = json.load(f)
            assert loaded == data