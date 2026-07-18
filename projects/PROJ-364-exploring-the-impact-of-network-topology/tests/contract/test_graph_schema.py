"""
Contract test for validating graph output against graph.schema.yaml.

This test ensures that the graph serialization output from the pipeline
strictly conforms to the defined JSON schema.
"""
import json
import yaml
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

# Import the schema object from the shared contract test module
from tests.contract.test_schemas import graph_schema


def test_graph_schema_validates_correct_data():
    """
    Validate that a correctly structured TopologyGraph passes schema validation.
    
    This simulates the output of src/graphs/serializer.py.
    """
    valid_graph = {
        "metadata": {
            "sample_id": "sample_001",
            "material": "graphene",
            "threshold_nm": 2.0,
            "node_count": 100,
            "edge_count": 450,
            "is_connected": True,
            "generation_seed": 42
        },
        "metrics": {
            "clustering_coefficient": 0.45,
            "average_path_length": 3.2,
            "lcc_fraction": 1.0,
            "percolation_threshold": 2.1,
            "degree_distribution": [
                {"degree": 2, "frequency": 10},
                {"degree": 3, "frequency": 50},
                {"degree": 4, "frequency": 40}
            ]
        },
        "lattice_correction": {
            "r_lattice": 100.0,
            "corrected_clustering": 0.44,
            "corrected_path_length": 3.1
        }
    }

    # Validate against the schema loaded in test_schemas
    try:
        validate(instance=valid_graph, schema=graph_schema)
    except ValidationError as e:
        pytest.fail(f"Valid graph data failed schema validation: {e.message}")


def test_graph_schema_rejects_invalid_node_count():
    """
    Ensure the schema rejects data where node_count is not an integer.
    """
    invalid_graph = {
        "metadata": {
            "sample_id": "sample_002",
            "material": "graphene",
            "threshold_nm": 2.0,
            "node_count": "one hundred",  # Should be int
            "edge_count": 450,
            "is_connected": True,
            "generation_seed": 42
        },
        "metrics": {
            "clustering_coefficient": 0.45,
            "average_path_length": 3.2,
            "lcc_fraction": 1.0,
            "percolation_threshold": 2.1,
            "degree_distribution": []
        },
        "lattice_correction": {}
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_graph, schema=graph_schema)
    
    assert "node_count" in str(exc_info.value).lower() or "integer" in str(exc_info.value).lower()


def test_graph_schema_handles_null_clustering():
    """
    Validate that the schema accepts null values for clustering when zero defects exist.
    (Corresponds to T022b edge case handling).
    """
    zero_defect_graph = {
        "metadata": {
            "sample_id": "sample_003",
            "material": "graphene",
            "threshold_nm": 2.0,
            "node_count": 0,
            "edge_count": 0,
            "is_connected": False,
            "generation_seed": 42,
            "zero_defect_flag": True
        },
        "metrics": {
            "clustering_coefficient": None,
            "average_path_length": None,
            "lcc_fraction": 0.0,
            "percolation_threshold": None,
            "degree_distribution": []
        },
        "lattice_correction": {}
    }

    try:
        validate(instance=zero_defect_graph, schema=graph_schema)
    except ValidationError as e:
        pytest.fail(f"Zero-defect graph with null metrics failed validation: {e.message}")


def test_graph_schema_rejects_missing_metadata():
    """
    Ensure the schema rejects data missing required metadata fields.
    """
    incomplete_graph = {
        "metadata": {
            "sample_id": "sample_004",
            # Missing material, threshold_nm, etc.
            "node_count": 50
        },
        "metrics": {},
        "lattice_correction": {}
    }

    with pytest.raises(ValidationError):
        validate(instance=incomplete_graph, schema=graph_schema)


def test_graph_schema_validates_degree_distribution_format():
    """
    Ensure degree_distribution is a list of objects with degree and frequency.
    """
    invalid_dist_graph = {
        "metadata": {
            "sample_id": "sample_005",
            "material": "MoS2",
            "threshold_nm": 2.5,
            "node_count": 50,
            "edge_count": 100,
            "is_connected": True,
            "generation_seed": 42
        },
        "metrics": {
            "clustering_coefficient": 0.3,
            "average_path_length": 4.0,
            "lcc_fraction": 1.0,
            "percolation_threshold": 2.6,
            "degree_distribution": [1, 2, 3]  # Should be list of objects
        },
        "lattice_correction": {}
    }

    with pytest.raises(ValidationError) as exc_info:
        validate(instance=invalid_dist_graph, schema=graph_schema)
    
    # The error should relate to the structure of items in degree_distribution
    assert "degree_distribution" in str(exc_info.value) or "object" in str(exc_info.value).lower()