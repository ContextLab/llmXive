import pytest
import networkx as nx
import json
import csv
from pathlib import Path
import tempfile
from metrics import process_batch, calculate_global_connectivity, calculate_avg_branching_factor

class TestMetricsIntegration:
    def test_full_pipeline_mathematical_verification(self):
        """
        Integration test: Create a known small graph (3 nodes, 2 edges),
        run the batch process, and verify the output matches mathematically derived values.
        
        Graph: 1 -> 2, 2 -> 3 (Linear chain of 3 nodes, 2 edges)
        Expected Global Connectivity: 2 / (3 * 2) = 2/6 = 0.333...
        Expected Avg Branching: (1 + 1 + 0) / 3 = 2/3 = 0.666...
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_dir = Path(tmpdir) / "graphs"
            graph_dir.mkdir()
            output_path = Path(tmpdir) / "metrics.csv"

            # Create known graph
            G = nx.DiGraph()
            G.add_nodes_from([1, 2, 3])
            G.add_edges_from([(1, 2), (2, 3)])
            
            # Save graph
            graph_data = {"nodes": list(G.nodes()), "edges": list(G.edges())}
            graph_file = graph_dir / "known_graph.json"
            with open(graph_file, 'w') as f:
                json.dump(graph_data, f)

            # Run batch
            process_batch(str(graph_dir), str(output_path))

            # Verify output
            assert output_path.exists()
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                
                row = rows[0]
                assert row['filename'] == 'known_graph.json'
                
                # Verify metrics
                conn = float(row['connectivity'])
                branch = float(row['branching_factor'])
                
                expected_conn = 2 / (3 * 2)
                expected_branch = 2 / 3
                
                assert conn == pytest.approx(expected_conn)
                assert branch == pytest.approx(expected_branch)

    def test_batch_multiple_graphs(self):
        """Test processing multiple graphs in one batch."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_dir = Path(tmpdir) / "graphs"
            graph_dir.mkdir()
            output_path = Path(tmpdir) / "metrics.csv"

            # Create two different graphs
            graphs_data = [
                {
                    "name": "graph_A.json",
                    "nodes": [1, 2],
                    "edges": [(1, 2)]
                },
                {
                    "name": "graph_B.json",
                    "nodes": [1, 2, 3, 4],
                    "edges": [(1, 2), (2, 3), (3, 4)]
                }
            ]

            for g_data in graphs_data:
                graph_file = graph_dir / g_data["name"]
                with open(graph_file, 'w') as f:
                    json.dump({"nodes": g_data["nodes"], "edges": g_data["edges"]}, f)

            process_batch(str(graph_dir), str(output_path))

            assert output_path.exists()
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                
                # Check specific values
                # Graph A: 2 nodes, 1 edge -> conn = 1/(2*1) = 0.5, branch = 1/2 = 0.5
                # Graph B: 4 nodes, 3 edges -> conn = 3/(4*3) = 0.25, branch = 3/4 = 0.75
                for row in rows:
                    if row['filename'] == 'graph_A.json':
                        assert float(row['connectivity']) == 0.5
                        assert float(row['branching_factor']) == 0.5
                    elif row['filename'] == 'graph_B.json':
                        assert float(row['connectivity']) == 0.25
                        assert float(row['branching_factor']) == 0.75

    def test_batch_empty_and_zero_edge_cases(self):
        """Test that batch processing handles empty graphs and zero-edge graphs gracefully (returns 0.0)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_dir = Path(tmpdir) / "graphs"
            graph_dir.mkdir()
            output_path = Path(tmpdir) / "metrics.csv"

            # Graph 1: Empty (no nodes, no edges)
            graph_empty = {"nodes": [], "edges": []}
            with open(graph_dir / "empty.json", 'w') as f:
                json.dump(graph_empty, f)

            # Graph 2: Single node, no edges
            graph_single = {"nodes": [1], "edges": []}
            with open(graph_dir / "single.json", 'w') as f:
                json.dump(graph_single, f)

            # Graph 3: Two nodes, no edges
            graph_disconnected = {"nodes": [1, 2], "edges": []}
            with open(graph_dir / "disconnected.json", 'w') as f:
                json.dump(graph_disconnected, f)

            # Run batch
            process_batch(str(graph_dir), str(output_path))

            assert output_path.exists()
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 3

                for row in rows:
                    conn = float(row['connectivity'])
                    branch = float(row['branching_factor'])
                    # All should be 0.0 for these cases
                    assert conn == 0.0
                    assert branch == 0.0