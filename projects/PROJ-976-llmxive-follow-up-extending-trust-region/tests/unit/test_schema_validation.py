import pytest
import json
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError

# Load schemas
SCHEMA_DIR = Path(__file__).parent.parent.parent / "specs" / "001-llmxive-trb-diversity-profile" / "contracts"

@pytest.fixture
def dataset_schema():
    with open(SCHEMA_DIR / "dataset.schema.yaml", 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def model_output_schema():
    with open(SCHEMA_DIR / "model_output.schema.yaml", 'r') as f:
        return yaml.safe_load(f)

def test_dataset_schema_valid_structure(dataset_schema):
    """Test that a valid dataset feature matrix passes validation."""
    valid_data = {
        "metadata": {
            "source_dataset": "tr-books-tokenized",
            "extraction_timestamp": "2023-10-27T10:00:00Z",
            "config_snapshot": {
                "ngram_order": 4,
                "spacy_model": "en_core_web_sm",
                "batch_size": 32
            },
            "checksum": "a" * 64
        },
        "features": [
            {
                "sample_id": "sample_001",
                "text_length": 150,
                "distinct_4_ratio": 0.85,
                "ngram_entropy": 3.2,
                "syntactic_variation_score": 1.5
            }
        ]
    }
    try:
        validate(instance=valid_data, schema=dataset_schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")

def test_dataset_schema_missing_required_field(dataset_schema):
    """Test that missing required fields fail validation."""
    invalid_data = {
        "metadata": {
            "source_dataset": "tr-books-tokenized",
            "extraction_timestamp": "2023-10-27T10:00:00Z",
            "config_snapshot": {},
            "checksum": "a" * 64
        },
        "features": []
    }
    # Missing config_snapshot.ngram_order
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=dataset_schema)

def test_model_output_schema_valid_structure(model_output_schema):
    """Test that a valid model output passes validation."""
    valid_data = {
        "metadata": {
            "analysis_timestamp": "2023-10-27T11:00:00Z",
            "source_dataset": "tr-books-tokenized",
            "target_dataset": "Tr-beir-formatted",
            "proxy_strategy": "text_length"
        },
        "source_analysis": {
            "pearson_correlation": 0.45,
            "spearman_correlation": 0.42,
            "p_value_pearson": 0.01,
            "p_value_spearman": 0.02,
            "permutation_p_value": 0.03,
            "fpr_proxy_binary": 0.15,
            "valid_proxy": True
        },
        "target_analysis": {
            "pearson_correlation": 0.38,
            "spearman_correlation": 0.35,
            "p_value_pearson": 0.04,
            "p_value_spearman": 0.05,
            "permutation_p_value": 0.06,
            "proxy_stability_variance": 0.8
        },
        "generalization_gap": {
            "correlation_gap": 0.07,
            "stability_forecast_accuracy": 0.85
        },
        "blocking_gaps": []
    }
    try:
        validate(instance=valid_data, schema=model_output_schema)
    except ValidationError as e:
        pytest.fail(f"Valid data failed schema validation: {e.message}")

def test_model_output_schema_invalid_proxy_strategy(model_output_schema):
    """Test that invalid proxy strategy fails validation."""
    invalid_data = {
        "metadata": {
            "analysis_timestamp": "2023-10-27T11:00:00Z",
            "source_dataset": "tr-books-tokenized",
            "target_dataset": "Tr-beir-formatted",
            "proxy_strategy": "invalid_strategy"
        },
        "source_analysis": {
            "pearson_correlation": 0.45,
            "spearman_correlation": 0.42,
            "p_value_pearson": 0.01,
            "p_value_spearman": 0.02,
            "permutation_p_value": 0.03,
            "fpr_proxy_binary": 0.15,
            "valid_proxy": True
        },
        "target_analysis": {
            "pearson_correlation": 0.38,
            "spearman_correlation": 0.35,
            "p_value_pearson": 0.04,
            "p_value_spearman": 0.05,
            "permutation_p_value": 0.06,
            "proxy_stability_variance": 0.8
        },
        "generalization_gap": {
            "correlation_gap": 0.07,
            "stability_forecast_accuracy": 0.85
        },
        "blocking_gaps": []
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_data, schema=model_output_schema)