"""
Unit tests for T042: Verify Noise Injection Reproducibility.

This test suite validates that the noise injection process is deterministic
and produces identical SHA-256 hashes across multiple runs with the same seed.
It specifically targets the `code/utils/verify_seeds.py` implementation.
"""
import os
import json
import tempfile
import shutil
import hashlib
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from utils.verify_seeds import (
    compute_file_hash,
    set_all_seeds,
    run_noise_injection_repro,
    load_config
)
from graph_utils import inject_noise
import networkx as nx

class TestVerifySeeds:
    """Test suite for seed verification and reproducibility."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test artifacts."""
        tmp = tempfile.mkdtemp()
        yield tmp
        shutil.rmtree(tmp)

    @pytest.fixture
    def sample_graph(self):
        """Create a deterministic sample graph for testing."""
        G = nx.DiGraph()
        # Add nodes with specific IDs to ensure determinism
        nodes = ["A", "B", "C", "D", "E"]
        G.add_nodes_from(nodes)
        
        # Add specific edges
        edges = [
            ("A", "B", "rel1"),
            ("B", "C", "rel2"),
            ("C", "D", "rel3"),
            ("D", "E", "rel4"),
            ("A", "C", "rel5")
        ]
        for src, tgt, rel in edges:
            G.add_edge(src, tgt, relation=rel)
        
        return G

    @pytest.fixture
    def sample_graph_json(self, temp_dir, sample_graph):
        """Save the sample graph to a JSON file."""
        graph_path = Path(temp_dir) / "test_graph.json"
        data = {
            "nodes": list(sample_graph.nodes()),
            "edges": [
                {"source": u, "target": v, "relation": d.get("relation", "")}
                for u, v, d in sample_graph.edges(data=True)
            ]
        }
        with open(graph_path, "w") as f:
            json.dump(data, f, sort_keys=True)
        return str(graph_path)

    def test_compute_file_hash_deterministic(self, temp_dir):
        """Test that computing a hash on the same file produces identical results."""
        file_path = Path(temp_dir) / "test.txt"
        content = "Test content for hashing\n" * 100
        
        # Write the file twice and compare hashes
        with open(file_path, "w") as f:
            f.write(content)
        hash1 = compute_file_hash(str(file_path))
        
        with open(file_path, "w") as f:
            f.write(content)
        hash2 = compute_file_hash(str(file_path))
        
        assert hash1 == hash2, "Hash should be deterministic for same content"
        assert len(hash1) == 64, "SHA-256 hash should be 64 hex characters"

    def test_set_all_seeds_reproducibility(self):
        """Test that setting seeds results in reproducible random states."""
        set_all_seeds(42)
        import numpy as np
        val1 = np.random.rand()
        
        set_all_seeds(42)
        val2 = np.random.rand()
        
        assert val1 == val2, "Seeds should produce identical random sequences"

    def test_inject_noise_deterministic(self, sample_graph):
        """Test that noise injection is deterministic with a fixed seed."""
        # First run
        set_all_seeds(42)
        noisy_graph_1 = inject_noise(sample_graph, ratio=0.1, seed=42)
        edges_1 = sorted([(u, v, d.get('relation', '')) for u, v, d in noisy_graph_1.edges(data=True)])
        
        # Second run
        set_all_seeds(42)
        noisy_graph_2 = inject_noise(sample_graph, ratio=0.1, seed=42)
        edges_2 = sorted([(u, v, d.get('relation', '')) for u, v, d in noisy_graph_2.edges(data=True)])
        
        assert edges_1 == edges_2, "Noise injection should be deterministic with same seed"

    def test_run_noise_injection_repro_identical_hashes(self, temp_dir, sample_graph_json):
        """
        T042 Core Test: Verify that running the noise injection process twice
        with the same seed produces identical file hashes.
        """
        # Setup config for the test
        config = {
            "seed": 42,
            "noise_ratio": 0.1,
            "input_graph_path": sample_graph_json,
            "output_graph_path": str(Path(temp_dir) / "output_noise_42.json")
        }
        
        # Save config to a temporary file
        config_path = Path(temp_dir) / "test_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)
        
        # Load the config back to ensure it works
        loaded_config = load_config(str(config_path))
        
        # Run the reproducibility check (simulating T039 logic)
        # We run it twice and compare the resulting file hashes
        
        # First run
        set_all_seeds(loaded_config["seed"])
        run_noise_injection_repro(loaded_config)
        hash_1 = compute_file_hash(loaded_config["output_graph_path"])
        
        # Second run (re-run the process)
        # Note: In a real scenario, we might clear the file first, but
        # the function should overwrite it deterministically.
        set_all_seeds(loaded_config["seed"])
        run_noise_injection_repro(loaded_config)
        hash_2 = compute_file_hash(loaded_config["output_graph_path"])
        
        # Assert that the hashes are identical
        assert hash_1 == hash_2, (
            f"Reproducibility failed: Hash 1 ({hash_1}) != Hash 2 ({hash_2}). "
            "Noise injection must be deterministic."
        )
        assert hash_1 is not None and len(hash_1) > 0, "Hash must be valid"

    def test_noisy_graph_structure_integrity(self, temp_dir, sample_graph_json):
        """Ensure the noisy graph output is valid JSON and contains expected structure."""
        config = {
            "seed": 42,
            "noise_ratio": 0.1,
            "input_graph_path": sample_graph_json,
            "output_graph_path": str(Path(temp_dir) / "output_noise_42.json")
        }
        
        set_all_seeds(42)
        run_noise_injection_repro(config)
        
        # Verify the output file exists and is valid JSON
        assert os.path.exists(config["output_graph_path"]), "Output file must exist"
        
        with open(config["output_graph_path"], "r") as f:
            data = json.load(f)
        
        assert "nodes" in data, "Output must contain 'nodes'"
        assert "edges" in data, "Output must contain 'edges'"
        assert len(data["nodes"]) > 0, "Output must have nodes"
        assert len(data["edges"]) > 0, "Output must have edges"
        
        # Verify edge count increased (noise added edges)
        # Note: This depends on the inject_noise logic adding edges
        # We assume the base graph has edges and noise adds more
        assert len(data["edges"]) >= 5, "Noisy graph should have at least original edges"

    def test_seed_verification_integration(self, temp_dir, sample_graph_json):
        """
        Integration test: Verify the entire seed verification flow works end-to-end.
        This mimics what T042 expects from verify_seeds.py.
        """
        # Create a state file to store hashes
        state_path = Path(temp_dir) / "state.json"
        state = {
            "artifact_hashes": {
                "graph_noise_42": None
            }
        }
        
        with open(state_path, "w") as f:
            json.dump(state, f)
        
        config = {
            "seed": 42,
            "noise_ratio": 0.1,
            "input_graph_path": sample_graph_json,
            "output_graph_path": str(Path(temp_dir) / "graph_noise_42.json"),
            "state_path": str(state_path)
        }
        
        # First execution
        set_all_seeds(42)
        run_noise_injection_repro(config)
        hash_1 = compute_file_hash(config["output_graph_path"])
        
        # Simulate storing the hash in state
        with open(state_path, "r") as f:
            current_state = json.load(f)
        current_state["artifact_hashes"]["graph_noise_42"] = hash_1
        with open(state_path, "w") as f:
            json.dump(current_state, f)
        
        # Second execution (re-run)
        set_all_seeds(42)
        run_noise_injection_repro(config)
        hash_2 = compute_file_hash(config["output_graph_path"])
        
        # Verify they match
        assert hash_1 == hash_2, "Re-run must produce identical hash"
        
        # Verify the stored hash matches the current file
        with open(state_path, "r") as f:
            final_state = json.load(f)
        assert final_state["artifact_hashes"]["graph_noise_42"] == hash_2, \
            "Stored hash must match current file hash"

    def test_different_seeds_different_hashes(self, temp_dir, sample_graph_json):
        """Verify that different seeds produce different graph structures (and thus different hashes)."""
        config = {
            "seed": 42,
            "noise_ratio": 0.1,
            "input_graph_path": sample_graph_json,
            "output_graph_path": str(Path(temp_dir) / "output_noise_42.json")
        }
        
        # Run with seed 42
        set_all_seeds(42)
        run_noise_injection_repro(config)
        hash_42 = compute_file_hash(config["output_graph_path"])
        
        # Run with seed 123
        config["output_graph_path"] = str(Path(temp_dir) / "output_noise_123.json")
        set_all_seeds(123)
        run_noise_injection_repro(config)
        hash_123 = compute_file_hash(config["output_graph_path"])
        
        # They should be different (with high probability for non-trivial noise)
        # Note: In very rare cases, random noise might coincidentally be the same,
        # but for a ratio of 0.1 on a small graph, this is extremely unlikely.
        # We assert they are different to confirm seed sensitivity.
        assert hash_42 != hash_123, "Different seeds should produce different graphs"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])