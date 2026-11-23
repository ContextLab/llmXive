import json
import yaml
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

# Base path for contracts relative to code/
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"

@pytest.fixture
def dataset_schema():
    with open(CONTRACTS_DIR / "dataset.schema.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def graph_schema():
    with open(CONTRACTS_DIR / "graph.schema.yaml", "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def analysis_schema():
    with open(CONTRACTS_DIR / "analysis.schema.yaml", "r") as f:
        return yaml.safe_load(f)

def test_dataset_schema_validates_correct_data(dataset_schema):
    valid_data = {
        "metadata": {
            "source": "test_source",
            "material": "graphene",
            "timestamp": "2023-10-27T10:00:00Z",
            "version": "1.0"
        },
        "data": [
            {"x": 1.0, "y": 2.0, "defect_type": "vacancy"},
            {"x": 3.0, "y": 4.0}
        ]
    }
    validate(instance=valid_data, schema=dataset_schema)

def test_dataset_schema_rejects_missing_metadata(dataset_schema):
    invalid_data = {
        "data": [{"x": 1.0, "y": 2.0}]
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=dataset_schema)

def test_graph_schema_validates_correct_data(graph_schema):
    valid_graph = {
        "metadata": {
            "graph_id": "g1",
            "source_dataset": "d1",
            "threshold": 2.0,
            "material": "graphene",
            "timestamp": "2023-10-27T10:00:00Z",
            "is_connected": True,
            "node_count": 10,
            "edge_count": 15
        },
        "nodes": [
            {"id": 0, "x": 0.0, "y": 0.0, "degree": 2},
            {"id": 1, "x": 1.0, "y": 0.0, "degree": 3}
        ],
        "edges": [
            {"source": 0, "target": 1, "distance": 1.0}
        ],
        "topology_metrics": {
            "clustering_coefficient": 0.5,
            "lcc_fraction": 1.0,
            "average_path_length": 2.5,
            "percolation_threshold": 1.8,
            "degree_distribution": [{"degree": 2, "frequency": 0.5}],
            "zero_defect_flag": False
        }
    }
    validate(instance=valid_graph, schema=graph_schema)

def test_graph_schema_handles_null_clustering(graph_schema):
    valid_graph = {
        "metadata": {
            "graph_id": "g2",
            "source_dataset": "d2",
            "threshold": 2.0,
            "material": "graphene",
            "timestamp": "2023-10-27T10:00:00Z",
            "is_connected": False,
            "node_count": 0,
            "edge_count": 0
        },
        "nodes": [],
        "edges": [],
        "topology_metrics": {
            "clustering_coefficient": None,
            "lcc_fraction": 0.0,
            "average_path_length": None,
            "percolation_threshold": 0.0,
            "degree_distribution": [],
            "zero_defect_flag": True
        }
    }
    validate(instance=valid_graph, schema=graph_schema)

def test_analysis_schema_validates_correct_data(analysis_schema):
    valid_analysis = {
        "analysis_id": "a1",
        "timestamp": "2023-10-27T10:00:00Z",
        "data_status": {
            "has_real_data": True,
            "is_unpaired": False,
            "fallback_mode": False
        },
        "correlation_results": [
            {
                "metric_name": "clustering_coefficient",
                "method": "pearson",
                "coefficient": 0.85,
                "p_value": 0.001,
                "corrected_p_value": 0.002,
                "confidence_interval": [0.75, 0.92],
                "significance": True
            }
        ],
        "regression_results": [
            {
                "metric_name": "clustering_coefficient",
                "model_type": "linear",
                "score": 0.72,
                "params": {"slope": 0.5, "intercept": 1.0},
                "aic": 100.5,
                "bic": 105.2
            }
        ],
        "sensitivity_analysis": {
            "std_dev": 0.03,
            "thresholds_tested": [1.5, 2.0, 2.5],
            "target_met": True
        }
    }
    validate(instance=valid_analysis, schema=analysis_schema)

def test_analysis_schema_handles_unpaired_data(analysis_schema):
    valid_analysis = {
        "analysis_id": "a2",
        "timestamp": "2023-10-27T10:00:00Z",
        "data_status": {
            "has_real_data": True,
            "is_unpaired": True,
            "fallback_mode": False
        },
        "correlation_results": [],
        "regression_results": [],
        "sensitivity_analysis": {
            "std_dev": 0.0,
            "thresholds_tested": [2.0],
            "target_met": True
        },
        "population_correlation": {
            "method": "population_mean_correlation",
            "coefficient": 0.6,
            "p_value": 0.04
        }
    }
    validate(instance=valid_analysis, schema=analysis_schema)

def test_schema_files_are_valid_yaml():
    # Ensure the schema files themselves are valid YAML
    for fname in ["dataset.schema.yaml", "graph.schema.yaml", "analysis.schema.yaml"]:
        with open(CONTRACTS_DIR / fname, "r") as f:
            try:
                yaml.safe_load(f)
            except yaml.YAMLError as e:
                pytest.fail(f"Schema file {fname} is not valid YAML: {e}")
