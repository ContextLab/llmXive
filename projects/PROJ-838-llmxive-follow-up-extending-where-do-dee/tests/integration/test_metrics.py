import pytest
import json
import os
import tempfile
from pathlib import Path
import networkx as nx
from metrics import process_batch

def test_integration_batch_processing():
    """Integration test for batch metric calculation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a set of test graphs with known metrics
        graphs_data = [
            {
                'filename': 'graph_A.json',
                'nodes': [1, 2, 3],
                'edges': [(1, 2), (2, 3)],
                'expected_connectivity': 2 / 6,
                'expected_branching': 2 / 3
            },
            {
                'filename': 'graph_B.json',
                'nodes': [1, 2, 3, 4],
                'edges': [(1, 2), (2, 3), (3, 4), (4, 1)],
                'expected_connectivity': 4 / 12,
                'expected_branching': 4 / 4
            },
            {
                'filename': 'graph_C.json',
                'nodes': [1],
                'edges': [],
                'expected_connectivity': 0.0,
                'expected_branching': 0.0
            }
        ]
        
        # Save graphs
        graph_path = Path(temp_dir)
        for graph_data in graphs_data:
            with open(graph_path / graph_data['filename'], 'w') as f:
                json.dump({
                    'nodes': graph_data['nodes'],
                    'edges': graph_data['edges']
                }, f)
        
        output_path = graph_path / "metrics.csv"
        process_batch(temp_dir, str(output_path))
        
        # Verify output
        assert output_path.exists()
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = {row['trajectory_id']: row for row in reader}
        
        # Check each graph's metrics
        for graph_data in graphs_data:
            traj_id = graph_data['filename'].replace('.json', '')
            assert traj_id in rows
            
            actual_conn = float(rows[traj_id]['global_connectivity'])
            actual_branch = float(rows[traj_id]['avg_branching_factor'])
            
            assert abs(actual_conn - graph_data['expected_connectivity']) < 1e-6
            assert abs(actual_branch - graph_data['expected_branching']) < 1e-6

import csv