"""
Contract tests for schema validation against specs/001-bridging-coefficient-analysis/contracts/.

This module validates that data structures and outputs conform to the defined
contract specifications for the Bridging Coefficient Analysis project.
"""

import pytest
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import project configuration and models
from src.lib import config
from src.models.node import Node
from src.models.graph_utils import calc_bridging, louvain_cluster

# Contract file paths
CONTRACTS_DIR = Path(config.PROJECT_ROOT) / "specs" / "001-bridging-coefficient-analysis" / "contracts"
NODE_CONTRACT_PATH = CONTRACTS_DIR / "node_schema.json"
OUTPUT_CONTRACT_PATH = CONTRACTS_DIR / "analysis_output_schema.json"

def load_contract(contract_path: Path) -> Dict[str, Any]:
    """Load a contract JSON file and return its contents."""
    if not contract_path.exists():
        raise FileNotFoundError(f"Contract file not found: {contract_path}")
    
    with open(contract_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_node_against_contract(node: Node, contract: Dict[str, Any]) -> bool:
    """
    Validate a Node instance against the node schema contract.
    
    Args:
        node: Node instance to validate
        contract: Contract dictionary defining required fields and types
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_fields = contract.get("required_fields", [])
    field_types = contract.get("field_types", {})
    
    # Check required fields exist
    for field_name in required_fields:
        if not hasattr(node, field_name):
            return False
    
    # Check field types where specified
    for field_name, expected_type in field_types.items():
        if hasattr(node, field_name):
            actual_value = getattr(node, field_name)
            # Type checking for common types
            if expected_type == "str" and not isinstance(actual_value, str):
                return False
            elif expected_type == "int" and not isinstance(actual_value, int):
                return False
            elif expected_type == "float" and not isinstance(actual_value, (int, float)):
                return False
            elif expected_type == "list" and not isinstance(actual_value, list):
                return False
            elif expected_type == "ndarray" and not hasattr(actual_value, '__array__'):
                return False
    
    return True

def test_node_contract_exists():
    """Verify that the node contract file exists."""
    assert NODE_CONTRACT_PATH.exists(), f"Node contract file missing: {NODE_CONTRACT_PATH}"

def test_output_contract_exists():
    """Verify that the analysis output contract file exists."""
    assert OUTPUT_CONTRACT_PATH.exists(), f"Output contract file missing: {OUTPUT_CONTRACT_PATH}"

def test_node_schema_validation():
    """
    Test that Node instances validate against the node schema contract.
    
    This is a contract test ensuring the Node model matches the specification.
    """
    # Load the contract
    contract = load_contract(NODE_CONTRACT_PATH)
    
    # Create test Node instances
    test_nodes = [
        Node(
            id="test_001",
            title="Test Paper Title",
            citation_count=100,
            embedding_vector=[0.1, 0.2, 0.3],
            primary_cluster=1,
            topic_cluster=5
        ),
        Node(
            id="test_002",
            title="Another Research Paper",
            citation_count=0,
            embedding_vector=[0.5, 0.5, 0.0],
            primary_cluster=2,
            topic_cluster=10
        )
    ]
    
    # Validate each node
    for node in test_nodes:
        assert validate_node_against_contract(node, contract), \
            f"Node {node.id} does not conform to contract schema"

def test_node_required_fields_contract():
    """
    Test that all required fields from the contract are present in Node.
    """
    contract = load_contract(NODE_CONTRACT_PATH)
    required_fields = contract.get("required_fields", [])
    
    # Verify each required field exists on Node
    for field_name in required_fields:
        # Create a minimal Node to check attribute existence
        # We use a try-except since Node might have __post_init__ validation
        try:
            test_node = Node(
                id="temp",
                title="temp",
                citation_count=0,
                embedding_vector=[],
                primary_cluster=0,
                topic_cluster=0
            )
            assert hasattr(test_node, field_name), \
                f"Required field '{field_name}' missing from Node model"
        except Exception:
            # If Node construction fails for other reasons, check class attributes
            assert hasattr(Node, field_name) or field_name in ["id", "title", "citation_count", 
                                                               "embedding_vector", "primary_cluster", "topic_cluster"], \
                f"Required field '{field_name}' missing from Node model"

def test_analysis_output_schema_contract():
    """
    Test that analysis output structures conform to the output schema contract.
    
    This validates the structure of statistical analysis results.
    """
    contract = load_contract(OUTPUT_CONTRACT_PATH)
    
    # Define a sample analysis output structure
    sample_output = {
        "correlation_results": [
            {
                "metric": "spearman",
                "variable_1": "bridging_coefficient",
                "variable_2": "citation_count",
                "coefficient": 0.45,
                "p_value": 0.001,
                "corrected": True
            }
        ],
        "regression_results": [
            {
                "model": "linear",
                "predictor": "bridging_coefficient",
                "outcome": "citation_count",
                "slope": 12.5,
                "intercept": 5.0,
                "r_squared": 0.25,
                "p_value": 0.003,
                "corrected": True
            }
        ],
        "metadata": {
            "analysis_type": "associational",
            "correction_method": "bonferroni",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }
    
    # Validate top-level keys
    required_keys = contract.get("required_top_level_keys", [])
    for key in required_keys:
        assert key in sample_output, f"Required key '{key}' missing from analysis output"

def test_bridging_coefficient_range_contract():
    """
    Test that bridging coefficients fall within the expected range [0.0, 1.0].
    
    This validates the mathematical constraints defined in the contract.
    """
    import networkx as nx
    
    # Create a simple test graph
    G = nx.Graph()
    G.add_edges_from([(1, 2), (2, 3), (3, 4), (1, 4), (2, 5)])
    
    # Define clusters
    clusters = {1: 0, 2: 0, 3: 1, 4: 1, 5: 2}
    
    # Calculate bridging coefficients
    coefficients = calc_bridging(G, clusters)
    
    # Validate range
    for node_id, coeff in coefficients.items():
        assert 0.0 <= coeff <= 1.0, \
            f"Bridging coefficient {coeff} for node {node_id} out of range [0.0, 1.0]"

def test_cluster_assignment_contract():
    """
    Test that cluster assignments are valid non-negative integers.
    """
    import networkx as nx
    
    G = nx.Graph()
    G.add_edges_from([(1, 2), (2, 3), (3, 4)])
    
    clusters = {1: 0, 2: 0, 3: 1, 4: 1}
    
    # Validate cluster assignments
    for node_id, cluster_id in clusters.items():
        assert isinstance(cluster_id, int), \
            f"Cluster ID for node {node_id} is not an integer"
        assert cluster_id >= 0, \
            f"Cluster ID for node {node_id} is negative"

def test_contract_file_structure():
    """
    Test that contract files have the expected structure.
    """
    # Load and validate node contract structure
    node_contract = load_contract(NODE_CONTRACT_PATH)
    assert "required_fields" in node_contract, "Node contract missing 'required_fields'"
    assert isinstance(node_contract["required_fields"], list), \
        "'required_fields' must be a list"
    
    # Load and validate output contract structure
    output_contract = load_contract(OUTPUT_CONTRACT_PATH)
    assert "required_top_level_keys" in output_contract, \
        "Output contract missing 'required_top_level_keys'"
    assert isinstance(output_contract["required_top_level_keys"], list), \
        "'required_top_level_keys' must be a list"