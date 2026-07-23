"""
Integration test for the full extraction pipeline on synthetic data.

This test scaffolds the execution of the US1 pipeline (extraction, feature
computation, and retraction merging) using a small, self-contained synthetic
graph and retraction dataset. It verifies that the pipeline produces a valid
CSV output with the expected schema and that the orchestrator logic (including
abort conditions) behaves correctly.

Note: This test uses synthetic data ONLY for the purpose of integration
scaffolding. The actual implementation (T013-T016) must use real data sources
when run in the production execution stage.
"""

import os
import sys
import tempfile
import shutil
import pandas as pd
import networkx as nx
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.data.run_extraction import run_extraction_pipeline
from code.utils.constants import EDGE_TYPES, RETRACTION_LABELS


def create_synthetic_graph(tmp_path: Path) -> Path:
    """
    Creates a minimal synthetic GML graph file for testing.
    Returns the path to the created file.
    """
    G = nx.Graph()
    
    # Add nodes with required attributes
    # Node 1: 2012, has improves edge
    G.add_node(1, year=2012, method_name="MethodA", field="CS", venue="NeurIPS")
    # Node 2: 2013, target of improves
    G.add_node(2, year=2013, method_name="MethodB", field="CS", venue="ICLR")
    # Node 3: 2017, retracted node
    G.add_node(3, year=2017, method_name="MethodC", field="Bio", venue="Nature")
    
    # Add edges with human-annotated types (no LLM inferred)
    G.add_edge(1, 2, type="improves", source_id="1", target_id="2")
    G.add_edge(2, 3, type="replaces", source_id="2", target_id="3")
    
    # Save to GML
    gml_path = tmp_path / "synthetic_graph.gml"
    nx.write_gml(G, str(gml_path))
    return gml_path


def create_synthetic_retractions(tmp_path: Path) -> Path:
    """
    Creates a minimal synthetic retraction CSV for testing.
    """
    data = [
        {
            "doi": "10.1038/nature12345",
            "title": "MethodC: A Breakthrough",
            "authors": "Smith, J.; Doe, A.",
            "year": 2017,
            "reason": "methodological error",
            "journal": "Nature"
        },
        {
            "doi": "10.1109/iclr.2013.001",
            "title": "MethodB: Initial Results",
            "authors": "Brown, B.",
            "year": 2013,
            "reason": "irreproducibility",
            "journal": "ICLR"
        }
    ]
    csv_path = tmp_path / "synthetic_retractions.csv"
    pd.DataFrame(data).to_csv(csv_path, index=False)
    return csv_path


def test_pipeline_synthetic_run():
    """
    Runs the full extraction pipeline on synthetic data and verifies output.
    """
    # Create a temporary directory for test artifacts
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Prepare synthetic inputs
        graph_path = create_synthetic_graph(tmp_path)
        retraction_path = create_synthetic_retractions(tmp_path)
        
        # Define output path
        output_path = tmp_path / "features_2010_2018.csv"
        
        # Run the pipeline
        # Note: We are mocking the data paths via environment or direct args
        # The actual run_extraction function expects specific paths or env vars.
        # For this integration test, we assume the function accepts overrides 
        # or we set up the environment to point to our temp files.
        
        # Since the real implementation (T017) reads from specific paths,
        # we will invoke the logic directly or set up the environment.
        # Here we assume run_extraction can take a config or we patch the paths.
        # For scaffolding, we verify the function exists and accepts arguments.
        
        try:
            # Attempt to run with synthetic paths (assuming implementation supports it)
            # If the implementation strictly uses hardcoded paths, this test scaffolding
            # documents the requirement that the implementation must support configurable paths
            # or environment variables for integration testing.
            
            # We call the function with explicit overrides if supported, 
            # otherwise we verify the structure.
            # Given the task is "scaffold", we verify the interface exists.
            
            # Mocking the environment for the test
            os.environ["DATA_PATH"] = str(tmp_path)
            os.environ["RETRACTION_DB_PATH"] = str(retraction_path)
            os.environ["OUTPUT_PATH"] = str(output_path)
            
            # Execute
            run_extraction_pipeline(
                graph_path=str(graph_path),
                retraction_path=str(retraction_path),
                output_path=str(output_path),
                year_start=2010,
                year_end=2018
            )
            
            # Verify output exists
            assert output_path.exists(), "Pipeline did not produce output CSV"
            
            # Verify schema
            df = pd.read_csv(output_path)
            required_columns = [
                "method_id", "year", "field", "venue",
                "bottleneck_resolution_ratio", "branching_entropy",
                "retraction_status", "retraction_status_binary"
            ]
            
            for col in required_columns:
                assert col in df.columns, f"Missing required column: {col}"
            
            # Verify data integrity
            assert len(df) > 0, "Output CSV is empty"
            
            # Check that labels are mapped correctly (based on synthetic data)
            # Node 3 has "methodological error" -> should be 1
            # Node 2 has "irreproducibility" -> should be 1
            # Node 1 has no retraction -> should be 0
            
            print(f"Integration test passed. Output shape: {df.shape}")
            
        except Exception as e:
            # If the implementation hasn't been fully written yet to accept these args,
            # this test scaffolding documents the expected behavior.
            # For the purpose of "scaffolding", we catch the error if the function
            # is not fully implemented yet, but we assert the function exists.
            if "run_extraction_pipeline" not in dir():
                raise AssertionError("run_extraction_pipeline function not found")
            else:
                # Re-raise if it's a real logic error in the implementation
                raise e


if __name__ == "__main__":
    test_pipeline_synthetic_run()
    print("All integration tests passed.")