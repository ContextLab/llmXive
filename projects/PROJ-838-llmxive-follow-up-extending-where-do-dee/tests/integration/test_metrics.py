import pytest
import json
import tempfile
import os
from pathlib import Path

from metrics import process_batch, load_graph_from_json, calculate_avg_branching_factor, calculate_global_connectivity


class TestProcessBatch:
    def test_process_batch_with_real_graphs(self):
        # Create a temporary directory for test graphs
        with tempfile.TemporaryDirectory() as tmpdir:
            graphs_dir = Path(tmpdir) / "graphs"
            graphs_dir.mkdir()
            output_file = Path(tmpdir) / "metrics.csv"

            # Create a few mock graph files representing processed DAGs
            # Graph 1: 3 nodes, 2 edges (Chain: 1->2->3)
            g1_data = {"nodes": [1, 2, 3], "edges": [[1, 2], [2, 3]]}
            with open(graphs_dir / "traj_001.json", 'w') as f:
                json.dump(g1_data, f)

            # Graph 2: 4 nodes, 3 edges (Chain: 1->2->3->4)
            g2_data = {"nodes": [1, 2, 3, 4], "edges": [[1, 2], [2, 3], [3, 4]]}
            with open(graphs_dir / "traj_002.json", 'w') as f:
                json.dump(g2_data, f)

            # Graph 3: 2 nodes, 0 edges (Isolated nodes)
            g3_data = {"nodes": [1, 2], "edges": []}
            with open(graphs_dir / "traj_003.json", 'w') as f:
                json.dump(g3_data, f)

            # Graph 4: 3 nodes, 3 edges (Triangle: 1->2, 2->3, 1->3)
            g4_data = {"nodes": [1, 2, 3], "edges": [[1, 2], [2, 3], [1, 3]]}
            with open(graphs_dir / "traj_004.json", 'w') as f:
                json.dump(g4_data, f)

            # Run process_batch
            process_batch(graphs_dir, output_file)

            # Verify output file exists
            assert output_file.exists()

            # Read and verify contents
            with open(output_file, 'r') as f:
                lines = f.readlines()

            # Check header
            assert "trajectory_id" in lines[0]
            assert "global_connectivity" in lines[0]
            assert "avg_branching_factor" in lines[0]

            # Check data rows (4 graphs)
            # Header + 4 data rows
            assert len(lines) == 5

            data_lines = lines[1:]
            assert len(data_lines) == 4

            # Verify specific values
            # traj_001: N=3, E=2.
            #   Connectivity = 2 / (3*2) = 2/6 = 0.333...
            #   Out-degrees: 1->1, 2->1, 3->0. Sum=2. ABF = 2/3 = 0.666...
            # traj_002: N=4, E=3.
            #   Connectivity = 3 / (4*3) = 3/12 = 0.25
            #   Out-degrees: 1->1, 2->1, 3->1, 4->0. Sum=3. ABF = 3/4 = 0.75
            # traj_003: N=2, E=0.
            #   Connectivity = 0.0
            #   ABF = 0.0
            # traj_004: N=3, E=3.
            #   Connectivity = 3 / 6 = 0.5
            #   Out-degrees: 1->2, 2->1, 3->0. Sum=3. ABF = 3/3 = 1.0

            for line in data_lines:
                parts = line.strip().split(',')
                assert len(parts) == 4  # id, connectivity, branching, filename (if included) or just 3 if filename not included
                # Expected format: trajectory_id,global_connectivity,avg_branching_factor
                assert len(parts) >= 3

                traj_id = parts[0]
                connectivity = float(parts[1])
                branching = float(parts[2])

                # Basic sanity checks
                assert 0.0 <= connectivity <= 1.0
                assert branching >= 0.0

                # Verify specific known values for specific files
                if traj_id == "traj_001":
                    assert abs(connectivity - 0.333333) < 0.0001
                    assert abs(branching - 0.666666) < 0.0001
                elif traj_id == "traj_002":
                    assert abs(connectivity - 0.25) < 0.0001
                    assert abs(branching - 0.75) < 0.0001
                elif traj_id == "traj_003":
                    assert connectivity == 0.0
                    assert branching == 0.0
                elif traj_id == "traj_004":
                    assert abs(connectivity - 0.5) < 0.0001
                    assert abs(branching - 1.0) < 0.0001

    def test_process_batch_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graphs_dir = Path(tmpdir) / "graphs"
            graphs_dir.mkdir()
            output_file = Path(tmpdir) / "metrics.csv"

            process_batch(graphs_dir, output_file)

            assert output_file.exists()
            with open(output_file, 'r') as f:
                lines = f.readlines()
            # Should have header only
            assert len(lines) == 1
            assert "trajectory_id" in lines[0]
            assert "global_connectivity" in lines[0]
            assert "avg_branching_factor" in lines[0]

    def test_process_batch_malformed_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            graphs_dir = Path(tmpdir) / "graphs"
            graphs_dir.mkdir()
            output_file = Path(tmpdir) / "metrics.csv"

            # Create a malformed JSON file
            with open(graphs_dir / "bad_traj.json", 'w') as f:
                f.write("{ invalid json }")

            # Create a valid one to ensure batch processing continues
            valid_data = {"nodes": [1], "edges": []}
            with open(graphs_dir / "good_traj.json", 'w') as f:
                json.dump(valid_data, f)

            # process_batch should skip bad files (handled by load_graph_from_json)
            # and produce output for the good one
            process_batch(graphs_dir, output_file)

            assert output_file.exists()
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Should contain header and the good row
            assert "trajectory_id" in content
            assert "good_traj" in content
            assert "bad_traj" not in content # Bad file should be skipped