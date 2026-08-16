import os
import json
import pickle
import hashlib
import tempfile
from pathlib import Path
import pytest

from ingest.graph_builder import build_graph_from_xyz, calculate_node_degree_stats
from ingest.graph_serializer import calculate_checksum, serialize_graph, save_checksum_manifest

# Helper to create a minimal valid XYZ file for testing
def create_test_xyz(path: Path, num_atoms: int = 5):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        f.write(f"{num_atoms}\n")
        f.write("Test structure for T015\n")
        for i in range(num_atoms):
            # Simple cubic arrangement
            x, y, z = i * 2.0, 0.0, 0.0
            f.write(f"Si {x:.4f} {y:.4f} {z:.4f}\n")

class TestGraphSerialization:
    def test_serialization(self, tmp_path):
        """
        T015 Verification:
        1. Build a graph from a known XYZ file.
        2. Serialize it to data/processed/graphs/ (using tmp_path for safety).
        3. Verify the file exists.
        4. Verify the checksum matches the input data.
        """
        # Setup
        xyz_file = tmp_path / "sample_01.xyz"
        output_dir = tmp_path / "graphs"
        output_dir.mkdir()
        
        # Create test data
        create_test_xyz(xyz_file, num_atoms=5)

        # Build graph
        graph_data = build_graph_from_xyz(str(xyz_file), cutoff=3.0)
        
        # Validate basic structure (from T012 logic)
        assert "nodes" in graph_data
        assert "edges" in graph_data
        assert len(graph_data["nodes"]) == 5

        # Serialize graph (T015 implementation)
        checksum = calculate_checksum(xyz_file)
        serialized_path = serialize_graph(graph_data, output_dir, checksum)

        # Verification: File exists
        assert serialized_path.exists(), f"Serialized file {serialized_path} was not created"

        # Verification: File is valid pickle
        with open(serialized_path, 'rb') as f:
            loaded_graph = pickle.load(f)
        
        assert loaded_graph["nodes"] == graph_data["nodes"]
        assert loaded_graph["edges"] == graph_data["edges"]
        assert loaded_graph["metadata"]["input_checksum"] == checksum

        # Verification: Manifest creation
        manifest_path = save_checksum_manifest([{"file": serialized_path.name, "checksum": checksum}], output_dir)
        assert manifest_path.exists()

        # Verification: Checksum integrity
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        assert manifest[0]["checksum"] == checksum
        assert manifest[0]["file"] == serialized_path.name

    def test_serialization_with_invalid_input(self, tmp_path):
        """Test that serialization fails loudly if input graph is missing required fields."""
        output_dir = tmp_path / "graphs"
        output_dir.mkdir()
        
        # Malformed graph data (missing 'nodes')
        bad_graph = {"edges": [[0, 1]]}
        
        with pytest.raises(AssertionError):
            serialize_graph(bad_graph, output_dir, "fake_checksum")