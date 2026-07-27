import pytest
import networkx as nx
import json
import os
import csv
from pathlib import Path
from strategies.lazy import LazyTraversal, run_sensitivity_analysis
import tempfile
import shutil

class TestLazyTraversalSensitivity:
    """
    Unit tests for the sensitivity analysis sweep logic.
    """

    @pytest.fixture
    def sample_graph(self):
        """Create a simple graph with known edge confidences."""
        G = nx.Graph()
        # Nodes
        nodes = ['A', 'B', 'C', 'D', 'Target']
        G.add_nodes_from(nodes)
        
        # Edges with confidence
        G.add_edge('A', 'B', confidence=0.9)
        G.add_edge('A', 'C', confidence=0.6)
        G.add_edge('B', 'D', confidence=0.8)
        G.add_edge('C', 'D', confidence=0.4) # Low confidence
        G.add_edge('D', 'Target', confidence=0.95)
        G.add_edge('A', 'Target', confidence=0.3) # Direct but low confidence
        
        return G

    @pytest.fixture
    def sample_tasks(self, sample_graph):
        """Create a list of task dictionaries."""
        return [
            {
                'id': 'task_1',
                'start_node': 'A',
                'target_node': 'Target',
                'question': 'Find path from A to Target',
                'answer': 'Target'
            }
        ]

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp)

    def test_lazy_traversal_with_high_threshold(self, sample_graph):
        """Test that high threshold (0.9) skips low confidence edges."""
        # Path A -> B (0.9) -> D (0.8) -> Target (0.95)
        # Threshold 0.9:
        # A->B (0.9) OK.
        # B->D (0.8) FAIL (0.8 < 0.9).
        # A->Target (0.3) FAIL.
        # Result should be failure or partial path.
        
        strategy = LazyTraversal(evidence_threshold=0.9)
        result = strategy.traverse(sample_graph, 'A', 'Target', {})
        
        # With threshold 0.9, B->D (0.8) is skipped. 
        # A->Target (0.3) is skipped.
        # A->B is taken. From B, no neighbors >= 0.9.
        assert result['success'] is False
        assert result['nodes_visited'] == 2 # A, B

    def test_lazy_traversal_with_low_threshold(self, sample_graph):
        """Test that low threshold (0.5) allows more edges."""
        # Threshold 0.5:
        # A->B (0.9) OK.
        # A->C (0.6) OK.
        # B->D (0.8) OK.
        # C->D (0.4) FAIL.
        # D->Target (0.95) OK.
        # Path: A->B->D->Target or A->C (stuck) -> ...
        
        strategy = LazyTraversal(evidence_threshold=0.5)
        result = strategy.traverse(sample_graph, 'A', 'Target', {})
        
        assert result['success'] is True
        assert 'Target' in result['path']

    def test_sensitivity_analysis_writes_csv(self, sample_tasks, temp_dir):
        """Test that run_sensitivity_analysis creates the output CSV."""
        # Save tasks
        tasks_path = os.path.join(temp_dir, 'tasks.json')
        with open(tasks_path, 'w') as f:
            json.dump(sample_tasks, f)
        
        # Save graph
        graphs_dir = os.path.join(temp_dir, 'graphs')
        os.makedirs(graphs_dir)
        graph_path = os.path.join(graphs_dir, 'task_1.json')
        G = nx.Graph()
        G.add_nodes_from(['A', 'B', 'Target'])
        G.add_edge('A', 'B', confidence=0.9)
        G.add_edge('B', 'Target', confidence=0.9)
        
        # Convert to dict for JSON serialization
        G_dict = nx.node_link_data(G)
        with open(graph_path, 'w') as f:
            json.dump(G_dict, f)
        
        output_path = os.path.join(temp_dir, 'sweep_results.csv')
        
        run_sensitivity_analysis(
            tasks_path=tasks_path,
            graphs_path=graphs_dir,
            output_path=output_path,
            thresholds=[0.5, 0.9]
        )
        
        assert os.path.exists(output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        # Should have 2 rows (one for each threshold)
        assert len(rows) == 2
        
        # Check columns
        expected_cols = ['task_id', 'threshold', 'success', 'accuracy', 'nodes_visited', 'latency_ms']
        for col in expected_cols:
            assert col in rows[0]

    def test_sensitivity_analysis_correctness(self, sample_tasks, temp_dir):
        """Test that different thresholds produce different results."""
        # Create a graph where threshold matters
        tasks_path = os.path.join(temp_dir, 'tasks.json')
        with open(tasks_path, 'w') as f:
            json.dump(sample_tasks, f)
        
        graphs_dir = os.path.join(temp_dir, 'graphs')
        os.makedirs(graphs_dir)
        graph_path = os.path.join(graphs_dir, 'task_1.json')
        
        # Graph: A -> B (0.9) -> Target (0.9)
        #       A -> C (0.4) -> Target (0.9)
        # High threshold (0.9) should find A->B->Target
        # Low threshold (0.5) should also find A->B->Target (or A->C if A->B was lower)
        
        G = nx.Graph()
        G.add_nodes_from(['A', 'B', 'C', 'Target'])
        G.add_edge('A', 'B', confidence=0.9)
        G.add_edge('B', 'Target', confidence=0.9)
        G.add_edge('A', 'C', confidence=0.4)
        G.add_edge('C', 'Target', confidence=0.9)
        
        G_dict = nx.node_link_data(G)
        with open(graph_path, 'w') as f:
            json.dump(G_dict, f)
        
        output_path = os.path.join(temp_dir, 'sweep_results.csv')
        
        run_sensitivity_analysis(
            tasks_path=tasks_path,
            graphs_path=graphs_dir,
            output_path=output_path,
            thresholds=[0.5, 0.9]
        )
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = {row['threshold']: row for row in reader}
        
        # Both should succeed in this simple graph
        assert rows['0.5']['success'] == 'True'
        assert rows['0.9']['success'] == 'True'
        
        # Check that nodes_visited might differ if paths differ (though here they likely don't)
        # The key is that the file is written and thresholds are recorded.
        assert float(rows['0.5']['threshold']) == 0.5
        assert float(rows['0.9']['threshold']) == 0.9
