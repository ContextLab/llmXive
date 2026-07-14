import pytest
import yaml
import json
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

@pytest.fixture
def dataset_schema():
    schema_path = CONTRACTS_DIR / "dataset.schema.yaml"
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def output_schema():
    schema_path = CONTRACTS_DIR / "output.schema.yaml"
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_dataset_doc():
    return {
        "metadata": {
            "source": "hotpotqa-fullwiki",
            "version": "1.0",
            "sample_size": 100,
            "seed": 42,
            "timestamp": "2023-10-01T00:00:00Z",
            "split": "train"
        },
        "documents": [
            {
                "id": "doc_1",
                "title": "Test Title",
                "text": "This is a test document text."
            }
        ]
    }

@pytest.fixture
def valid_graphs_doc():
    return {
        "metadata": {
            "source": "hotpotqa-fullwiki",
            "total_documents": 1,
            "timestamp": "2023-10-01T00:00:00Z"
        },
        "graphs": [
            {
                "doc_id": "doc_1",
                "nodes": [
                    {"id": "n1", "attributes": {"term": "test"}}
                ],
                "edges": [
                    {"source": "n1", "target": "n1", "weight": 1.0}
                ]
            }
        ]
    }

@pytest.fixture
def valid_metrics_doc():
    return {
        "metrics": [
            {"metric_name": "recall@10", "value": 0.5},
            {"metric_name": "hypothesis_supported", "value": True}
        ],
        "summary": {
            "hypothesis_supported": True,
            "correlation_r": 0.75,
            "p_value": 0.001
        }
    }

def test_dataset_schema_validates_correct_doc(dataset_schema, valid_dataset_doc):
    validate(instance=valid_dataset_doc, schema=dataset_schema)

def test_dataset_schema_rejects_invalid_source(dataset_schema, valid_dataset_doc):
    valid_dataset_doc["metadata"]["source"] = "invalid_source"
    with pytest.raises(ValidationError):
        validate(instance=valid_dataset_doc, schema=dataset_schema)

def test_dataset_schema_rejects_too_large_sample(dataset_schema, valid_dataset_doc):
    valid_dataset_doc["metadata"]["sample_size"] = 361
    with pytest.raises(ValidationError):
        validate(instance=valid_dataset_doc, schema=dataset_schema)

def test_output_schema_validates_graphs(output_schema, valid_graphs_doc):
    validate(instance=valid_graphs_doc, schema=output_schema)

def test_output_schema_validates_metrics(output_schema, valid_metrics_doc):
    validate(instance=valid_metrics_doc, schema=output_schema)

def test_output_schema_rejects_missing_metadata(output_schema):
    invalid_doc = {"graphs": []}
    with pytest.raises(ValidationError):
        validate(instance=invalid_doc, schema=output_schema)

def test_schema_files_exist():
    assert (CONTRACTS_DIR / "dataset.schema.yaml").exists()
    assert (CONTRACTS_DIR / "output.schema.yaml").exists()

def test_schema_files_are_valid_yaml():
    with open(CONTRACTS_DIR / "dataset.schema.yaml") as f:
        yaml.safe_load(f)
    with open(CONTRACTS_DIR / "output.schema.yaml") as f:
        yaml.safe_load(f)
