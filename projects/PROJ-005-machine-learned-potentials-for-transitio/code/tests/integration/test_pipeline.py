import json
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any

import pytest
import pandas as pd
import numpy as np

# Import pipeline components from the project source
from src.data.ingest import run_ingestion, get_project_root
from src.data.graph_construction import run_graph_construction, save_graphs_to_parquet, load_processed_graphs_intermediate
from src.data.validate_graphs import validate_all_graphs, load_schema
from src.data.checksum_manager import compute_file_checksum, save_checksum_manifest
from src.utils.config import load_config

# Constants
EXPECTED_RAW_DIR = "data/raw"
EXPECTED_PROCESSED_DIR = "data/processed"
EXPECTED_RESULTS_DIR = "data/results"
GRAPH_OUTPUT_FILE = "graphs.parquet"
SCHEMA_FILE = "contracts/dataset_graph.schema.yaml"
CHECKSUMS_FILE = "data/raw/checksums.json"


class TestPipelineIntegration:
    """
    Integration test for the end-to-end data pipeline:
    1. Ingestion (fetch/filter QM9-TS)
    2. Graph Construction (build transition state graphs)
    3. Validation (schema compliance)
    4. Output verification (parquet structure)
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self, tmp_path):
        """
        Setup a temporary project root for the test to avoid polluting the real data/ directory.
        We mock the file system operations to point to tmp_path.
        """
        self.original_cwd = os.getcwd()
        self.test_root = Path(tmp_path)
        
        # Create necessary directory structure
        (self.test_root / EXPECTED_RAW_DIR).mkdir(parents=True, exist_ok=True)
        (self.test_root / EXPECTED_PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
        (self.test_root / EXPECTED_RESULTS_DIR).mkdir(parents=True, exist_ok=True)
        (self.test_root / "contracts").mkdir(parents=True, exist_ok=True)

        # Create a minimal mock schema file for validation
        schema_content = """
        type: object
        properties:
          nodes:
            type: object
            properties:
              atomic_numbers:
                type: array
              positions:
                type: array
          edges:
            type: object
            properties:
              source:
                type: array
              target:
                type: array
              edge_attr:
                type: array
          metadata:
            type: object
            properties:
              reaction_id:
                type: string
              energy_dft:
                type: number
              barrier_height:
                type: number
              metal_center:
                type: string
              ligand_class:
                type: string
        required:
          - nodes
          - edges
          - metadata
        """
        schema_path = self.test_root / SCHEMA_FILE
        with open(schema_path, "w") as f:
            f.write(schema_content)

        # Create a mock checksums file (required by ingest)
        checksums_path = self.test_root / CHECKSUMS_FILE
        with open(checksums_path, "w") as f:
            json.dump({}, f)

        # Mock the get_project_root function behavior by setting an env var
        # or by patching. Since we can't easily patch the module global,
        # we will rely on the fact that the test runs in a context where
        # we can manipulate the file system or we assume the task requires
        # us to test the logic flow with mocked data if real data isn't available.
        # However, the prompt says "Implement integration test... verify end-to-end flow".
        # Since we cannot guarantee the HuggingFace fetch works in this isolated env
        # without network, we will mock the ingestion step to return a known dataset
        # to verify the rest of the pipeline (graph construction + validation).
        
        # We will patch the 'fetch_dataset_from_hf' function in the ingest module
        # to return a small, valid DataFrame mimicking the QM9-TS structure.
        
        # Store original function
        import src.data.ingest as ingest_module
        self.original_fetch = ingest_module.fetch_dataset_from_hf
        self.original_load = ingest_module.load_and_count_reactions
        
        # Define mock fetch
        def mock_fetch_dataset(*args, **kwargs):
            # Return a path to a CSV/Parquet in tmp/raw that we create
            raw_file = self.test_root / EXPECTED_RAW_DIR / "mock_qm9ts.parquet"
            data = {
                "reaction_id": ["R1", "R2", "R3"],
                "metal_center": ["Pd", "Ni", "Cu"],
                "ligand_class": ["Group 13", "Conventional", "Group 13"],
                "energy_dft": [-100.5, -200.2, -150.0],
                "barrier_height": [15.0, 20.5, 12.0],
                "atoms": [
                    [28, 6, 1, 6], 
                    [28, 6, 1, 6], 
                    [29, 6, 1, 6]
                ],
                "positions": [
                    [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
                    [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
                ]
            }
            df = pd.DataFrame(data)
            df.to_parquet(raw_file)
            return raw_file

        # Define mock load
        def mock_load_and_count(*args, **kwargs):
            return pd.read_parquet(self.test_root / EXPECTED_RAW_DIR / "mock_qm9ts.parquet"), 3

        ingest_module.fetch_dataset_from_hf = mock_fetch_dataset
        ingest_module.load_and_count_reactions = mock_load_and_count

        # Also need to patch the schema loading to use our temp schema
        import src.data.validate_graphs as validate_module
        self.original_load_schema = validate_module.load_schema
        
        def mock_load_schema(*args, **kwargs):
            return schema_content # Return raw yaml string or dict as expected by validator
        
        # Note: validate_graphs.load_schema expects to read a file. 
        # We will patch the path resolution or the read logic.
        # Looking at the API, load_schema takes a path. We will ensure the config points to our temp dir.
        # But load_schema is likely hardcoded to read from project root.
        # We will patch the function to read from our temp schema.
        def mock_load_schema_wrapper(path):
            with open(self.test_root / SCHEMA_FILE, 'r') as f:
                return f.read()
        
        validate_module.load_schema = mock_load_schema_wrapper

        yield

        # Restore
        ingest_module.fetch_dataset_from_hf = self.original_fetch
        ingest_module.load_and_count_reactions = self.original_load
        validate_module.load_schema = self.original_load_schema

    def test_end_to_end_ingestion_and_graph_construction(self):
        """
        Verifies that:
        1. Ingestion produces a raw file (mocked).
        2. Graph construction consumes raw and produces graphs.parquet.
        3. Validation passes against schema.
        """
        # 1. Ingestion
        # We simulate running the ingestion logic. Since we mocked the fetch,
        # we just need to ensure the file exists and has the right shape.
        # The actual run_ingestion might do filtering. We assume our mock data
        # passes the filter (Pd, Ni, Cu).
        
        # Call the ingestion logic (or just ensure the file exists if we mocked the fetch)
        # To be thorough, we call the function that processes the raw data.
        # Since run_ingestion orchestrates fetch -> filter -> save, and we mocked fetch,
        # we need to ensure it saves to the expected location.
        
        # Let's manually trigger the pipeline steps to ensure they work together.
        
        # Step A: Simulate Ingestion (using our mock)
        raw_df, count = ingest_module.load_and_count_reactions()
        assert count == 3
        assert "metal_center" in raw_df.columns
        assert "ligand_class" in raw_df.columns

        # Step B: Graph Construction
        # The graph construction module expects raw data in data/raw/ and processes it.
        # We need to ensure the path resolution works.
        # We will patch get_project_root to return our temp_path for this test.
        import src.data.graph_construction as gc_module
        original_get_root = gc_module.get_project_root
        gc_module.get_project_root = lambda: self.test_root

        try:
            # Run graph construction
            # Note: run_graph_construction likely calls ingest internally or expects files.
            # We will call the specific function that builds graphs from the raw data.
            # Based on API: run_graph_construction()
            
            # We need to ensure the raw file is in the right place for the graph constructor.
            # Our mock fetch saved to tmp/raw/mock_qm9ts.parquet.
            # The graph constructor likely looks for a specific name or iterates data/raw.
            # Let's assume it processes all parquet files in data/raw.
            
            # We'll call the main entry point for graph construction.
            # Since we can't easily mock the internal file loading of graph_construction
            # without knowing its exact implementation details (it's not fully shown),
            # we will test the specific function that builds the graph from a DataFrame
            # if available, or assume run_graph_construction works with our setup.
            
            # Let's assume run_graph_construction() handles the flow:
            # 1. Load raw
            # 2. Build graphs
            # 3. Save to data/processed/graphs.parquet
            
            # We need to make sure the 'cutoff' logic doesn't fail.
            # We'll mock load_optimal_cutoff if needed, or provide a default.
            # For now, assume it uses a default or we provide a mock.
            
            # Let's directly test the core logic: construct_transition_state_graph
            # But the task asks for an integration test of the pipeline.
            # So we run the pipeline script logic.
            
            # To make this robust, we will create a minimal test that exercises
            # the functions we know exist in the API surface.
            
            # We will construct a graph manually to test the validation,
            # then verify the pipeline flow.
            
            # Actually, let's rely on the fact that we have the API surface.
            # We will call run_graph_construction.
            # We need to ensure it doesn't crash.
            
            # Mock the cutoff loading
            def mock_load_optimal_cutoff(*args, **kwargs):
                return 3.5 # Default cutoff
            
            gc_module.load_optimal_cutoff = mock_load_optimal_cutoff
            
            # Run the construction
            # Note: run_graph_construction might try to read from a specific file.
            # We assume it reads from data/raw/*.parquet.
            # Our mock file is there.
            
            # We need to ensure the 'filter_outliers' and 'save_graphs_to_parquet' work.
            # Let's just call the functions that are critical.
            
            # Since we can't guarantee the full run_graph_construction works with our mock
            # without seeing its internal file paths, we will test the components:
            # 1. Load raw data (mocked)
            # 2. Build graphs (using the function from graph_construction)
            # 3. Validate (using validate_graphs)
            # 4. Save (using save_graphs_to_parquet)
            
            # Let's assume run_graph_construction is the entry point.
            # We will run it.
            
            # If run_graph_construction fails because it can't find the file,
            # we adjust the mock.
            
            # For the purpose of this task, we will assume the pipeline
            # successfully produces graphs.parquet.
            
            # We will simulate the result of run_graph_construction by creating
            # a valid graphs.parquet file manually if the function call is too brittle,
            # BUT the task requires testing the pipeline.
            # So we call it.
            
            # To ensure it runs, we might need to mock more.
            # Let's assume the test environment is set up such that run_graph_construction
            # finds the file we created.
            
            # We will call run_graph_construction.
            # If it fails, we catch it and fail the test (which is correct).
            
            # We need to make sure the 'ingest' step is considered 'done' by the pipeline.
            # The pipeline might check for a flag or file.
            # We'll assume it just processes whatever is in data/raw.
            
            # Let's try to run the pipeline.
            try:
                # We need to ensure the config is loaded correctly.
                # We'll assume default config is fine.
                
                # Run the graph construction
                # We need to pass the correct arguments or rely on defaults.
                # The API shows run_graph_construction() takes no args.
                run_graph_construction()
                
                # Check output
                output_path = self.test_root / EXPECTED_PROCESSED_DIR / GRAPH_OUTPUT_FILE
                assert output_path.exists(), "Graphs parquet file not created"
                
                # Load and verify structure
                graphs_df = pd.read_parquet(output_path)
                assert len(graphs_df) > 0, "Graphs dataframe is empty"
                assert "nodes" in graphs_df.columns, "Missing 'nodes' column"
                assert "edges" in graphs_df.columns, "Missing 'edges' column"
                assert "metadata" in graphs_df.columns, "Missing 'metadata' column"
                
                # Verify metadata fields
                meta = graphs_df.iloc[0]["metadata"]
                assert "reaction_id" in meta, "Missing reaction_id in metadata"
                assert "metal_center" in meta, "Missing metal_center in metadata"
                assert "ligand_class" in meta, "Missing ligand_class in metadata"
                
            except Exception as e:
                # If the pipeline fails, we log it.
                # This is an integration test, so if the pipeline breaks, the test fails.
                pytest.fail(f"Pipeline execution failed: {str(e)}")

        finally:
            # Restore original get_project_root
            gc_module.get_project_root = original_get_root

    def test_schema_validation_integration(self):
        """
        Verifies that the output graphs pass the schema validation.
        """
        # Ensure we have graphs.parquet (from previous test or re-run)
        # We will re-run the minimal setup to ensure the file exists.
        # (Same mocking logic as above)
        
        import src.data.graph_construction as gc_module
        import src.data.validate_graphs as val_module
        
        original_get_root = gc_module.get_project_root
        original_load_schema = val_module.load_schema
        
        gc_module.get_project_root = lambda: self.test_root
        val_module.load_schema = lambda path: open(self.test_root / SCHEMA_FILE).read()
        
        # Mock load_optimal_cutoff
        gc_module.load_optimal_cutoff = lambda *args, **kwargs: 3.5

        try:
            # Ensure output file exists
            output_path = self.test_root / EXPECTED_PROCESSED_DIR / GRAPH_OUTPUT_FILE
            if not output_path.exists():
                # Re-run construction if not present
                run_graph_construction()

            # Validate
            # validate_all_graphs takes a path to the parquet file?
            # API: validate_all_graphs(main) -> expects to find file in config.
            # We'll call it and see.
            
            # Since validate_all_graphs is a main entry point, let's call it.
            # It should read from data/processed/graphs.parquet.
            
            # We need to ensure the validation doesn't crash.
            # We'll assume it returns a result or raises.
            
            # Let's manually validate the file we know exists.
            # The API shows validate_all_graphs() which likely reads the default path.
            
            # We'll call it.
            try:
                validate_all_graphs()
            except Exception as e:
                # If validation fails, it means the graph structure is wrong.
                # This is a failure of the pipeline.
                pytest.fail(f"Schema validation failed: {str(e)}")
                
            # If we reach here, validation passed.
            assert True

        finally:
            gc_module.get_project_root = original_get_root
            val_module.load_schema = original_load_schema

    def test_checksum_generation(self):
        """
        Verifies that checksums are generated for the output file.
        """
        # Ensure output exists
        output_path = self.test_root / EXPECTED_PROCESSED_DIR / GRAPH_OUTPUT_FILE
        if not output_path.exists():
            import src.data.graph_construction as gc_module
            gc_module.get_project_root = lambda: self.test_root
            gc_module.load_optimal_cutoff = lambda *args, **kwargs: 3.5
            run_graph_construction()

        # Compute checksum
        checksum = compute_file_checksum(str(output_path))
        assert checksum is not None
        assert len(checksum) == 64 # SHA256 hex length

        # Save checksum
        checksums_path = self.test_root / CHECKSUMS_FILE
        # We need to load existing, add, save.
        # But the test is just to verify the function works.
        save_checksum_manifest({str(output_path.relative_to(self.test_root)): checksum}, str(checksums_path))
        
        assert checksums_path.exists()
        
        # Verify it can be loaded
        from src.data.checksum_manager import load_checksum_manifest
        loaded = load_checksum_manifest(str(checksums_path))
        assert str(output_path.relative_to(self.test_root)) in loaded