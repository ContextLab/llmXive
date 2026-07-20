import json
import yaml
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

# Paths to schema files
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"
DATASET_SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
GRAPH_SCHEMA_PATH = CONTRACTS_DIR / "graph.schema.yaml"
ANALYSIS_SCHEMA_PATH = CONTRACTS_DIR / "analysis.schema.yaml"

@pytest.fixture
def dataset_schema():
    with open(DATASET_SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def graph_schema():
    with open(GRAPH_SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def analysis_schema():
    with open(ANALYSIS_SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_schema_files_are_valid_yaml():
    """Ensure all schema files are valid YAML and parseable."""
    for path in [DATASET_SCHEMA_PATH, GRAPH_SCHEMA_PATH, ANALYSIS_SCHEMA_PATH]:
        assert path.exists(), f"Schema file missing: {path}"
        try:
            with open(path, 'r') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in {path}: {e}")

def test_dataset_schema_validates_correct_data(dataset_schema):
    """Test a valid dataset record."""
    valid_record = {
        "sample_id": "sample_001",
        "x": 10.5,
        "y": 20.3,
        "material_type": "graphene",
        "thermal_conductivity": 4000.0
    }
    validate(instance=valid_record, schema=dataset_schema)

def test_dataset_schema_rejects_missing_metadata(dataset_schema):
    """Test that missing required fields in dataset schema fail."""
    invalid_record = {"x": 10.5, "y": 20.3} # Missing sample_id, material_type
    with pytest.raises(ValidationError):
        validate(instance=invalid_record, schema=dataset_schema)

def test_graph_schema_validates_correct_data(graph_schema):
    """Test a valid graph object."""
    valid_graph = {
        "sample_id": "sample_001",
        "material_type": "graphene",
        "threshold_nm": 2.0,
        "nodes": [{"id": 0, "x": 0.0, "y": 0.0}],
        "edges": [],
        "metrics": {
            "node_count": 1,
            "edge_count": 0,
            "density": 0.0,
            "average_degree": 0.0,
            "global_clustering_coefficient": None,
            "average_path_length": None,
            "is_connected": True,
            "lcc_fraction": 1.0,
            "percolation_threshold": None,
            "degree_distribution": {},
            "zero_defect_flag": False
        },
        "metadata": {
            "created_at": "2023-10-27T10:00:00Z",
            "source_file": "data/raw/test.csv",
            "checksum": "abc123",
            "lattice_correction_applied": False,
            "r_lattice_nm": 0.246
        }
    }
    validate(instance=valid_graph, schema=graph_schema)

def test_graph_schema_handles_null_clustering(graph_schema):
    """Test that null clustering is allowed for edge cases (e.g., 1 node)."""
    valid_graph = {
        "sample_id": "sample_001",
        "material_type": "graphene",
        "threshold_nm": 2.0,
        "nodes": [{"id": 0, "x": 0.0, "y": 0.0}],
        "edges": [],
        "metrics": {
            "node_count": 1,
            "edge_count": 0,
            "density": 0.0,
            "average_degree": 0.0,
            "global_clustering_coefficient": None,
            "average_path_length": None,
            "is_connected": True,
            "lcc_fraction": 1.0,
            "percolation_threshold": None,
            "degree_distribution": {},
            "zero_defect_flag": False
        },
        "metadata": {
            "created_at": "2023-10-27T10:00:00Z",
            "source_file": "data/raw/test.csv",
            "checksum": "abc123",
            "lattice_correction_applied": False,
            "r_lattice_nm": 0.246
        }
    }
    validate(instance=valid_graph, schema=graph_schema)

def test_analysis_schema_validates_correct_data(analysis_schema):
    """Test a valid analysis result."""
    valid_result = {
        "analysis_id": "analysis_001",
        "correlations": [
            {
                "metric": "global_clustering_coefficient",
                "correlation_type": "pearson",
                "r_value": 0.85,
                "p_value": 0.001,
                "ci_lower": 0.70,
                "ci_upper": 0.92
            }
        ],
        "p_value_correction": "bonferroni",
        "significant_correlations": 1,
        "metadata": {
            "created_at": "2023-10-27T10:00:00Z",
            "threshold_used": 2.0,
            "n_samples": 50
        }
    }
    validate(instance=valid_result, schema=analysis_schema)

def test_analysis_schema_handles_unpaired_data(analysis_schema):
    """Test that analysis schema handles unpaired data aggregation."""
    valid_result = {
        "analysis_id": "analysis_002",
        "correlations": [
            {
                "metric": "global_clustering_coefficient",
                "correlation_type": "pearson",
                "r_value": 0.45,
                "p_value": 0.05,
                "ci_lower": 0.10,
                "ci_upper": 0.70
            }
        ],
        "p_value_correction": "benjamini_hochberg",
        "significant_correlations": 0,
        "metadata": {
            "created_at": "2023-10-27T10:00:00Z",
            "threshold_used": 2.0,
            "n_samples": 10,
            "unpaired_aggregation": True
        }
    }
    validate(instance=valid_result, schema=analysis_schema)