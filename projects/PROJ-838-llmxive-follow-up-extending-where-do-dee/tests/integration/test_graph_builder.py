import pytest
import networkx as nx
from pathlib import Path
import json
import tempfile
import os

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from graph_builder import parse_trajectory, build_dag, save_graph, load_trajectories_from_directory

class TestGraphBuilderIntegration:
    def test_full_pipeline_single_trajectory(self):
        """Test the full pipeline: parse -> build -> save -> load"""
        trajectory = {
            "id": "integration_test_1",
            "spans": [
                {"id": 0, "text": "Initial thought"},
                {"id": 1, "text": "I need to cite to the initial thought"},
                {"id": 2, "text": "Further analysis"},
                {"id": 3, "text": "Refer to previous step for details"}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Parse trajectory
            spans = parse_trajectory(trajectory, cutoff_depth=1.0)
            assert len(spans) == 4
            
            # Step 2: Build DAG
            graph = build_dag(spans)
            assert graph.number_of_nodes() == 4
            # Should have edges from 1->0 and 3->2 (or 3->0, 3->1, 3->2)
            assert graph.number_of_edges() >= 2
            
            # Step 3: Save graph
            output_dir = Path(tmpdir) / "graphs"
            output_path = save_graph(graph, trajectory["id"], output_dir)
            assert output_path.exists()
            
            # Step 4: Load and verify
            with open(output_path, "r") as f:
                saved_data = json.load(f)
            
            assert saved_data["trajectory_id"] == "integration_test_1"
            assert saved_data["num_nodes"] == 4
            assert saved_data["num_edges"] == graph.number_of_edges()
            
            # Reconstruct graph from saved data
            reconstructed = nx.node_link_graph(saved_data["graph"])
            assert reconstructed.number_of_nodes() == graph.number_of_nodes()
            assert reconstructed.number_of_edges() == graph.number_of_edges()

    def test_short_trajectory_handling(self):
        """Test that short trajectories are handled correctly (all spans used)"""
        trajectory = {
            "id": "short_test",
            "spans": [
                {"id": 0, "text": "Only span"}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            spans = parse_trajectory(trajectory, cutoff_depth=0.5)
            # Should return all spans (1) instead of 0
            assert len(spans) == 1
            
            graph = build_dag(spans)
            assert graph.number_of_nodes() == 1
            assert graph.number_of_edges() == 0
            
            output_path = save_graph(graph, trajectory["id"], Path(tmpdir) / "graphs")
            assert output_path.exists()

    def test_empty_trajectory_handling(self):
        """Test that empty trajectories are handled correctly"""
        trajectory = {
            "id": "empty_test",
            "spans": []
        }
        
        spans = parse_trajectory(trajectory, cutoff_depth=0.5)
        assert spans == []
        
        graph = build_dag(spans)
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0

    def test_multiple_trajectories_batch(self):
        """Test processing multiple trajectories"""
        trajectories = [
            {
                "id": "batch_test_1",
                "spans": [{"id": i, "text": f"span {i}"} for i in range(5)]
            },
            {
                "id": "batch_test_2",
                "spans": [{"id": i, "text": f"span {i}"} for i in range(3)]
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmpdir:
          raw_dir = Path(tmpdir) / "raw"
          raw_dir.mkdir()
          
          # Save trajectories
          for traj in trajectories:
              with open(raw_dir / f"{traj['id']}.json", "w") as f:
                  json.dump(traj, f)
          
          # Load and process
          loaded = load_trajectories_from_directory(raw_dir)
          assert len(loaded) == 2
          
          output_dir = Path(tmpdir) / "graphs"
          output_dir.mkdir()
          
          for traj in loaded:
              spans = parse_trajectory(traj, cutoff_depth=0.5)
              graph = build_dag(spans)
              save_graph(graph, traj["id"], output_dir)
          
          # Verify outputs
          graph_files = list(output_dir.glob("*_graph.json"))
          assert len(graph_files) == 2
