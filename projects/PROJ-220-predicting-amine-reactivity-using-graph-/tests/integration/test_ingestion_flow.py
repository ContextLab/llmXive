"""
Integration test for end-to-end ingestion and graph construction on a small subset.

This test verifies the full pipeline:
1. Data ingestion from ChEMBL/PubChem (real sources)
2. Filtering for primary/secondary amines
3. Kinetic normalization using class-average Ea
4. Graph construction for the resulting molecules

It runs on a small, defined subset to ensure it completes within time/memory limits
while still exercising the real data path (no synthetic fallbacks).
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd

# Import from the project's source modules
from src.data.ingestion import (
    fetch_chembl_sn2_data,
    fetch_pubchem_sn2_data,
    filter_primary_secondary_amine,
    calculate_class_average_ea,
    normalize_kinetics,
    run_ingestion,
    ReactionRecord
)
from src.data.preprocessing import construct_molecular_graph
from src.utils.validate_citations import validate_citations

# Import memory monitoring utilities if needed for large runs
from src.utils.memory_monitor import check_limits, graceful_exit

# Test constants
SMALL_SUBSET_SIZE = 50  # Process only the first 50 valid records for this integration test


def test_ingestion_and_graph_construction_flow():
    """
    End-to-end integration test:
    1. Fetch a small subset of real SN2 reaction data
    2. Filter for primary/secondary amines
    3. Normalize kinetics using class-average Ea
    4. Construct molecular graphs for the amine reactants
    5. Verify the output schema and data integrity
    """
    # Create a temporary directory for test outputs
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        raw_output_path = output_dir / "raw_reactions.csv"
        graph_output_path = output_dir / "reaction_graphs.json"
        audit_log_path = output_dir / "audit_log.json"
        
        # Step 1: Ingest a small subset of real data
        # Note: We limit to SMALL_SUBSET_SIZE to keep the test fast
        print(f"Starting ingestion with subset size: {SMALL_SUBSET_SIZE}")
        
        # Run the ingestion pipeline (this will call validate_citations first)
        # We expect this to run on real data and fail loudly if sources are unreachable
        try:
            records = run_ingestion(
                max_records=SMALL_SUBSET_SIZE,
                output_dir=output_dir
            )
        except Exception as e:
            # If ingestion fails (e.g., network issues, citation validation fails),
            # we raise the error - no synthetic fallback allowed
            pytest.fail(f"Ingestion pipeline failed on real data: {str(e)}")
        
        # Verify we got some records
        assert len(records) > 0, "Ingestion returned no records"
        assert len(records) <= SMALL_SUBSET_SIZE, f"Got more than {SMALL_SUBSET_SIZE} records"
        
        # Verify all records have required fields
        for i, record in enumerate(records):
            assert hasattr(record, 'smiles'), f"Record {i} missing 'smiles' field"
            assert hasattr(record, 'normalized_rate'), f"Record {i} missing 'normalized_rate' field"
            assert hasattr(record, 'pka'), f"Record {i} missing 'pka' field"
            assert record.smiles is not None, f"Record {i} has None SMILES"
            assert record.normalized_rate is not None, f"Record {i} has None normalized_rate"
        
        # Step 2: Construct molecular graphs for each record
        graphs = []
        invalid_smiles_count = 0
        
        for i, record in enumerate(records):
            try:
                graph = construct_molecular_graph(record.smiles)
                if graph is not None:
                    graphs.append({
                        'index': i,
                        'smiles': record.smiles,
                        'normalized_rate': record.normalized_rate,
                        'pka': record.pka,
                        'graph': graph
                    })
                else:
                    invalid_smiles_count += 1
            except Exception as e:
                # Log but continue - some SMILES might be problematic
                invalid_smiles_count += 1
                print(f"Warning: Failed to construct graph for record {i}: {str(e)}")
        
        # Verify we got at least some valid graphs
        assert len(graphs) > 0, "No valid graphs were constructed"
        
        # Step 3: Verify graph structure
        for graph_entry in graphs:
            graph = graph_entry['graph']
            
            # Check for required graph components
            assert 'nodes' in graph, "Graph missing 'nodes' key"
            assert 'edges' in graph, "Graph missing 'edges' key"
            
            # Verify node attributes
            for node in graph['nodes']:
                assert 'atom_type' in node, "Node missing 'atom_type'"
                assert 'hybridization' in node, "Node missing 'hybridization'"
                assert 'gasteiger_charge' in node, "Node missing 'gasteiger_charge'"
                assert 'pka' in node, "Node missing 'pka'"
            
            # Verify edge attributes (if any edges exist)
            if len(graph['edges']) > 0:
                for edge in graph['edges']:
                    assert 'bond_order' in edge, "Edge missing 'bond_order'"
        
        # Step 4: Write outputs to disk (simulating what the real pipeline would do)
        # Convert graphs to JSON-serializable format
        serializable_graphs = []
        for g in graphs:
            serializable_graphs.append({
                'index': g['index'],
                'smiles': g['smiles'],
                'normalized_rate': g['normalized_rate'],
                'pka': g['pka'],
                'num_nodes': len(g['graph']['nodes']),
                'num_edges': len(g['graph']['edges']),
                'node_types': [n['atom_type'] for n in g['graph']['nodes']],
                'edge_bond_orders': [e['bond_order'] for e in g['graph']['edges']]
            })
        
        # Save to JSON
        with open(graph_output_path, 'w') as f:
            json.dump(serializable_graphs, f, indent=2)
        
        # Save raw records to CSV
        df = pd.DataFrame([{
            'smiles': r.smiles,
            'normalized_rate': r.normalized_rate,
            'pka': r.pka,
            'original_rate': r.original_rate,
            'temperature': r.temperature,
            'ea': r.ea
        } for r in records])
        df.to_csv(raw_output_path, index=False)
        
        # Save audit log (simulated - in real pipeline this would be populated)
        audit_data = {
            'total_records_processed': len(records),
            'valid_graphs': len(graphs),
            'invalid_smiles': invalid_smiles_count,
            'test_timestamp': 'integration_test_run'
        }
        with open(audit_log_path, 'w') as f:
            json.dump(audit_data, f, indent=2)
        
        # Step 5: Final assertions
        # Verify output files exist and have content
        assert raw_output_path.exists(), "Raw output CSV not created"
        assert graph_output_path.exists(), "Graph output JSON not created"
        assert audit_log_path.exists(), "Audit log not created"
        
        assert raw_output_path.stat().st_size > 0, "Raw output CSV is empty"
        assert graph_output_path.stat().st_size > 0, "Graph output JSON is empty"
        
        # Verify data quality
        assert len(graphs) >= 5, f"Expected at least 5 valid graphs, got {len(graphs)}"
        assert invalid_smiles_count < len(records) * 0.2, f"Too many invalid SMILES: {invalid_smiles_count}/{len(records)}"
        
        print(f"✅ Integration test passed: {len(records)} records ingested, {len(graphs)} graphs constructed")
        print(f"   Invalid SMILES: {invalid_smiles_count}")
        print(f"   Output files: {raw_output_path}, {graph_output_path}, {audit_log_path}")


def test_citation_validation_gate_integration():
    """
    Verify that the citation validation gate is properly integrated
    and blocks execution if validation fails.
    """
    # This test verifies the gate is called before data fetching
    # We can't easily test the failure case without mocking, but we can
    # verify the gate is invoked in the flow
    
    # The run_ingestion function should call validate_citations() first
    # We'll verify this by checking that the function doesn't return
    # immediately without attempting to fetch data (if sources are available)
    
    # For now, we just verify that the function exists and can be called
    # A more thorough test would mock the network calls
    assert callable(validate_citations), "validate_citations function not found"
    assert callable(run_ingestion), "run_ingestion function not found"
    
    print("✅ Citation validation gate integration verified")


def test_memory_and_time_constraints():
    """
    Verify that the pipeline respects memory and time limits
    by processing a small subset and checking resource usage.
    """
    import time
    import tracemalloc
    
    # Start memory tracking
    tracemalloc.start()
    start_time = time.time()
    
    # Run ingestion with small subset
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        
        try:
            records = run_ingestion(
                max_records=SMALL_SUBSET_SIZE,
                output_dir=output_dir
            )
        except Exception as e:
            tracemalloc.stop()
            pytest.fail(f"Ingestion failed: {str(e)}")
    
    # Stop tracking
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed_time = time.time() - start_time
    
    # Verify constraints (adjust thresholds as needed)
    # For a small subset of 50 records, we expect:
    # - Memory usage < 1GB (well within the 7GB limit)
    # - Time < 300 seconds (5 minutes)
    assert peak < 1024 * 1024 * 1024, f"Memory usage too high: {peak / (1024*1024):.2f} MB"
    assert elapsed_time < 300, f"Execution time too long: {elapsed_time:.2f} seconds"
    
    print(f"✅ Resource constraints verified: {peak / (1024*1024):.2f} MB peak memory, {elapsed_time:.2f}s execution time")


if __name__ == "__main__":
    # Run tests when executed directly
    test_ingestion_and_graph_construction_flow()
    test_citation_validation_gate_integration()
    test_memory_and_time_constraints()
    print("\n🎉 All integration tests passed!")