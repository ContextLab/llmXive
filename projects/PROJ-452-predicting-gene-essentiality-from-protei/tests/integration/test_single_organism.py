"""
Integration test for single-organism pipeline (US1).

This test verifies that the full pipeline (Data Loading -> ID Mapping -> Centrality -> Correlation)
executes successfully for a single organism (S. cerevisiae) and produces valid results
in the expected output format.

Prerequisites:
- T012 (PPI Data Loading)
- T013 (Essentiality Data Loading)
- T014 (ID Mapping)
- T015 (Centrality Computation)
- T016 (Correlation Statistics)
- T017 (Orchestration/Main)

This test depends on the implementation of T016 and T017 which are assumed to be
completed alongside this integration test to ensure the pipeline runs end-to-end.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

import pytest

# Project imports
import sys
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from code.config import load_config, get_organisms, get_path, ensure_dirs
from code.data_loader import (
    load_essentiality_for_all_organisms,
    map_ids,
    fetch_string_network,
    load_local_network
)
from code.network_analysis import compute_all_centrality_metrics, load_graph_from_adjacency_list
from code.statistics import calculate_spearman_correlation

# Configure logging for the test
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
TARGET_ORGANISM = "S. cerevisiae"
EXPECTED_OUTPUT_FILE = "results/correlations.json"
MIN_CENTRALITY_TYPES = 3  # degree, betweenness, eigenvector


@pytest.fixture(scope="module")
def config():
    """Load the project configuration."""
    try:
        cfg = load_config()
    except Exception as e:
        pytest.fail(f"Failed to load configuration: {e}")
    return cfg


@pytest.fixture(scope="module")
def organism_id(config):
    """Get the organism ID for the target organism."""
    organisms = get_organisms(config)
    if TARGET_ORGANISM not in organisms:
        pytest.fail(f"Target organism '{TARGET_ORGANISM}' not found in config organisms.")
    return TARGET_ORGANISM


def test_pipeline_execution(organism_id, config):
    """
    Run the full pipeline for a single organism and verify output.
    
    Steps:
    1. Load PPI network (STRING or local fallback)
    2. Load essentiality labels (DEG or local fallback)
    3. Map IDs
    4. Compute centralities
    5. Calculate correlations
    6. Verify output structure and validity
    """
    logger.info(f"Starting integration pipeline for {organism_id}")
    
    # 1. Ensure output directories exist
    results_dir = get_path(config, "results")
    ensure_dirs(results_dir)
    
    # 2. Load PPI Network
    logger.info(f"Loading PPI network for {organism_id}")
    try:
        # Attempt to load from local cache first, then fetch
        local_path = get_path(config, "data") / "raw" / f"{organism_id}_ppi.json"
        if local_path.exists():
            graph = load_local_network(local_path)
        else:
            # Try fetching, but handle failure gracefully for integration test
            # In a real CI, we might mock the fetch or rely on T012 having populated local data
            graph = fetch_string_network(organism_id, config)
    except Exception as e:
        # If we cannot get data, the test fails.
        # Note: T012/T013 should handle the actual fetching. 
        # If they failed previously, this test will catch it.
        pytest.fail(f"Failed to load PPI network: {e}")
    
    assert graph is not None, "Graph is None"
    assert len(graph.nodes()) > 0, "Graph has no nodes"
    logger.info(f"Loaded graph with {len(graph.nodes())} nodes and {len(graph.edges())} edges")
    
    # 3. Load Essentiality Labels
    logger.info(f"Loading essentiality labels for {organism_id}")
    try:
        local_labels_path = get_path(config, "data") / "raw" / f"{organism_id}_essentiality.json"
        if local_labels_path.exists():
            essentiality_data = load_local_essentiality(local_labels_path)
        else:
            essentiality_data = fetch_essentiality_labels(organism_id, config)
    except Exception as e:
        pytest.fail(f"Failed to load essentiality labels: {e}")
    
    assert essentiality_data is not None, "Essentiality data is None"
    assert len(essentiality_data) > 0, "Essentiality data is empty"
    logger.info(f"Loaded {len(essentiality_data)} essentiality labels")
    
    # 4. Map IDs
    logger.info("Mapping gene IDs")
    try:
        mapped_nodes, mapped_labels = map_ids(graph, essentiality_data, organism_id, config)
    except Exception as e:
        pytest.fail(f"Failed to map IDs: {e}")
    
    assert len(mapped_nodes) > 0, "No nodes survived ID mapping"
    assert len(mapped_labels) == len(mapped_nodes), "Mismatch in mapped nodes and labels"
    logger.info(f"Successfully mapped {len(mapped_nodes)} genes")
    
    # 5. Compute Centralities
    logger.info("Computing centrality metrics")
    try:
        centralities = compute_all_centrality_metrics(mapped_nodes, mapped_labels)
    except Exception as e:
        pytest.fail(f"Failed to compute centralities: {e}")
    
    assert centralities is not None, "Centralities result is None"
    assert "degree" in centralities, "Degree centrality missing"
    assert "betweenness" in centralities, "Betweenness centrality missing"
    assert "eigenvector" in centralities, "Eigenvector centrality missing"
    logger.info("Computed all centrality metrics")
    
    # 6. Calculate Correlations
    logger.info("Calculating Spearman correlations")
    try:
        correlations = {}
        for metric_name, values in centralities.items():
            rho, p_value = calculate_spearman_correlation(values, mapped_labels)
            correlations[metric_name] = {
                "rho": rho,
                "p_value": p_value
            }
    except Exception as e:
        pytest.fail(f"Failed to calculate correlations: {e}")
    
    assert len(correlations) > 0, "No correlations calculated"
    
    # 7. Construct Output
    output_data = {
        "organism": organism_id,
        "timestamp": "integration_test_run", # In real run, use datetime
        "sample_size": len(mapped_nodes),
        "correlations": correlations
    }
    
    output_path = Path(results_dir) / EXPECTED_OUTPUT_FILE
    
    # 8. Write Output (Simulating main.py behavior)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Output written to {output_path}")
    
    # 9. Verify Output File Existence and Content
    assert output_path.exists(), f"Output file {output_path} was not created"
    
    with open(output_path, 'r') as f:
        saved_data = json.load(f)
    
    # Assertions on saved data
    assert saved_data["organism"] == organism_id
    assert "correlations" in saved_data
    assert saved_data["correlations"]["degree"]["rho"] is not None
    assert saved_data["correlations"]["degree"]["p_value"] is not None
    
    # Check for statistical validity (rho between -1 and 1)
    rho = saved_data["correlations"]["degree"]["rho"]
    assert -1.0 <= rho <= 1.0, f"Correlation rho {rho} is out of bounds"
    
    logger.info("Integration test passed successfully")
    
    # Cleanup (optional, but good for tests)
    # os.remove(output_path) 

def test_output_schema_validity():
    """
    Verify that the generated output file matches the expected schema structure.
    This acts as a contract test for the output format.
    """
    results_dir = get_path(load_config(), "results")
    output_path = Path(results_dir) / EXPECTED_OUTPUT_FILE
    
    if not output_path.exists():
        pytest.skip("Output file not found. Run test_pipeline_execution first.")
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    # Basic schema checks
    required_keys = ["organism", "sample_size", "correlations"]
    for key in required_keys:
        assert key in data, f"Missing required key: {key}"
    
    assert isinstance(data["correlations"], dict)
    
    for metric, stats in data["correlations"].items():
        assert "rho" in stats, f"Missing 'rho' in {metric}"
        assert "p_value" in stats, f"Missing 'p_value' in {metric}"
        assert isinstance(stats["rho"], (int, float))
        assert isinstance(stats["p_value"], (int, float))

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
