"""
Integration Test for T014: Oracle Graph Generation

This test verifies that the oracle generator:
1. Produces a valid JSON file at the expected path.
2. The file contains the expected schema (states, transitions).
3. The checksum manifest is generated and valid.
"""
import json
import os
import pytest
from pathlib import Path
import sys

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from oracle.generator import build_oracle_graph, OUTPUT_PATH, MANIFEST_PATH
from utils.checksums import verify_file_checksum

@pytest.fixture(scope="module")
def generated_graph():
    """
    Fixture to generate the graph once for the test session.
    This runs the actual generation logic.
    """
    # Ensure directories exist
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Run generation
    graph_data = build_oracle_graph()
    
    # Save it (simulating the main script behavior)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2, default=str)
    
    # Generate manifest
    from utils.checksums import generate_checksum_manifest
    generate_checksum_manifest(OUTPUT_PATH, MANIFEST_PATH)
    
    return graph_data

class TestT014OracleGeneration:
    def test_output_file_exists(self):
        """Verify that the output file is created."""
        assert OUTPUT_PATH.exists(), f"Output file {OUTPUT_PATH} does not exist."

    def test_output_is_valid_json(self):
        """Verify that the output file is valid JSON."""
        try:
            with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert isinstance(data, dict), "Root element must be a dictionary."
        except json.JSONDecodeError as e:
            pytest.fail(f"Output file is not valid JSON: {e}")

    def test_graph_schema(self, generated_graph):
        """Verify the graph contains required keys: states and transitions."""
        assert "states" in generated_graph, "Graph must contain 'states' key."
        assert "transitions" in generated_graph, "Graph must contain 'transitions' key."
        
        assert isinstance(generated_graph["states"], list), "'states' must be a list."
        assert isinstance(generated_graph["transitions"], list), "'transitions' must be a list."

    def test_checksum_verification(self):
        """Verify that the checksum manifest is valid."""
        assert MANIFEST_PATH.exists(), f"Manifest file {MANIFEST_PATH} does not exist."
        
        is_valid = verify_file_checksum(OUTPUT_PATH, MANIFEST_PATH)
        assert is_valid, "Checksum verification failed."

    def test_non_empty_graph(self, generated_graph):
        """Verify that the graph is not empty (at least one state and transition)."""
        # Depending on the source, it might be empty if no logic is found, 
        # but for a valid run it should have content.
        # We assert > 0 to ensure the generator actually did work.
        assert len(generated_graph.get("states", [])) > 0, "Graph should contain at least one state."
        assert len(generated_graph.get("transitions", [])) > 0, "Graph should contain at least one transition."
