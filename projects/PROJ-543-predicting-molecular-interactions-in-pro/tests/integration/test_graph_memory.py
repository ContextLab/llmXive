"""
Integration test for graph construction memory footprint.

This test verifies that the graph construction pipeline for User Story 1
(Data Ingestion) operates within the strict memory constraints (SC-005: 7 GB)
while processing real PDBbind data.

It executes the following steps:
1. Loads a representative subset of the PDBbind refined set using the
   real data loader from code/data/ingest.py.
2. Constructs molecular graphs with 3D coordinates and interaction edges.
3. Monitors peak memory usage during the process using code/utils/io.py.
4. Asserts that peak memory usage does not exceed the defined limit (7 GB).
5. Validates that the resulting graph structure contains expected nodes/edges.

NOTE: This test requires the PDBbind v2020 refined set to be available
(either downloaded by T013 or present in data/raw/). If the real data
source is unavailable, the test will fail loudly as per project constraints.
"""

import os
import sys
import gc
import time
import tempfile
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.ingest import load_pdbbind_refined, construct_molecular_graphs
from utils.io import get_memory_usage_mb, check_memory_limit
from models.entities import MolecularGraph

# Configuration
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
SAMPLE_SIZE = 50  # Number of complexes to process for the integration test
MAX_RUNTIME_SECONDS = 300  # Safety timeout

def test_graph_construction_memory_footprint():
    """
    Integration test: Verify memory footprint of graph construction on real data.
    """
    print(f"Starting memory footprint test with limit: {MEMORY_LIMIT_GB} GB")
    print(f"Loading {SAMPLE_SIZE} complexes from PDBbind refined set...")

    # Ensure real data is available; this will raise an error if data is missing
    # The load_pdbbind_refined function is expected to handle the real data fetching
    # or raise a specific exception if the source is unreachable.
    try:
        complexes_data = load_pdbbind_refined(
            limit=SAMPLE_SIZE,
            force_download=False  # Assume T013 has run or data is present
        )
    except Exception as e:
        # Fail loudly if real data cannot be loaded
        print(f"CRITICAL: Failed to load real PDBbind data: {e}")
        raise RuntimeError(
            f"Integration test aborted: Real data source unavailable. "
            f"Ensure T013 has successfully downloaded the dataset or "
            f"the data is present in data/raw/. Error: {e}"
        ) from e

    if not complexes_data:
        raise RuntimeError("No complexes loaded from PDBbind. Test cannot proceed.")

    print(f"Successfully loaded {len(complexes_data)} complexes.")

    # Garbage collection before measurement
    gc.collect()
    initial_memory_mb = get_memory_usage_mb()
    print(f"Initial memory usage: {initial_memory_mb:.2f} MB")

    graphs: List[MolecularGraph] = []
    peak_memory_mb = initial_memory_mb
    start_time = time.time()

    try:
        for i, complex_data in enumerate(complexes_data):
            # Check for timeout
            if time.time() - start_time > MAX_RUNTIME_SECONDS:
                raise TimeoutError(
                    f"Graph construction exceeded {MAX_RUNTIME_SECONDS}s limit."
                )

            # Construct graph for this complex
            graph = construct_molecular_graphs([complex_data])
            
            if not graph:
                raise RuntimeError(f"Graph construction failed for complex {i}")

            graphs.extend(graph)

            # Periodic memory check
            if (i + 1) % 10 == 0 or i == len(complexes_data) - 1:
                current_memory_mb = get_memory_usage_mb()
                if current_memory_mb > peak_memory_mb:
                    peak_memory_mb = current_memory_mb
                
                print(f"Processed {i+1}/{len(complexes_data)} complexes. "
                      f"Current memory: {current_memory_mb:.2f} MB, Peak: {peak_memory_mb:.2f} MB")

                # Check limit incrementally
                if current_memory_mb > MEMORY_LIMIT_MB:
                    raise MemoryError(
                        f"Memory limit exceeded at complex {i+1}. "
                        f"Current: {current_memory_mb:.2f} MB, Limit: {MEMORY_LIMIT_MB:.2f} MB"
                    )

        # Final memory check
        final_memory_mb = get_memory_usage_mb()
        if final_memory_mb > peak_memory_mb:
            peak_memory_mb = final_memory_mb

        print(f"Graph construction complete. Peak memory usage: {peak_memory_mb:.2f} MB")

        # Assertions
        assert len(graphs) == len(complexes_data), (
            f"Expected {len(complexes_data)} graphs, got {len(graphs)}"
        )

        # Validate graph structure for the first graph
        sample_graph = graphs[0]
        assert isinstance(sample_graph, MolecularGraph), "Graph is not a MolecularGraph instance"
        assert len(sample_graph.nodes) > 0, "Sample graph has no nodes"
        assert len(sample_graph.edges) > 0, "Sample graph has no edges"
        
        # Verify 3D coordinates exist
        for node in sample_graph.nodes:
            assert node.coordinates is not None, "Node missing 3D coordinates"
            assert len(node.coordinates) == 3, "Node coordinates not 3D"

        # Final memory assertion
        assert peak_memory_mb <= MEMORY_LIMIT_MB, (
            f"Peak memory usage ({peak_memory_mb:.2f} MB) exceeded limit ({MEMORY_LIMIT_MB:.2f} MB)"
        )

        print("SUCCESS: Memory footprint test passed.")
        print(f"  - Processed {len(graphs)} complexes")
        print(f"  - Peak memory: {peak_memory_mb:.2f} MB / {MEMORY_LIMIT_MB:.2f} MB")
        print(f"  - Graph structure validated")

    finally:
        # Cleanup
        del complexes_data
        del graphs
        gc.collect()

    return True

if __name__ == "__main__":
    test_graph_construction_memory_footprint()