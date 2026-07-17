import json
import yaml
import pytest
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError

# Define the base path for contracts
BASE_PATH = Path(__file__).parent.parent.parent / "specs" / "001-text-tone-emotional-support" / "contracts"

def load_yaml_schema(schema_name: str) -> dict:
    """Load a YAML schema file."""
    schema_path = BASE_PATH / schema_name
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def generate_valid_stimulus_data() -> dict:
    """Generate a valid stimulus data sample."""
    return {
        "stimulus_id": "S001",
        "text": "Hey, how are you doing? :)",
        "emoji_level": "low",
        "punctuation_type": "standard",
        "length_category": "short",
        "context": "friend"
    }

def generate_valid_rating_data() -> dict:
    """Generate a valid rating data sample."""
    return {
        "participant_id": "P-AB123456",
        "stimulus_id": "S001",
        "relationship_context": "friend",
        "rating": 5,
        "timestamp": "2023-10-27T10:00:00Z"
    }

def generate_valid_analysis_result_data() -> dict:
    """Generate a valid analysis result sample."""
    return {
        "model_id": "M001",
        "fixed_effects": {
            "emoji_level": {"estimate": 0.5, "std_err": 0.1},
            "punctuation_type": {"estimate": 0.2, "std_err": 0.05}
        },
        "random_effects": {
            "Participant": 0.3,
            "Stimulus": 0.1
        },
        "p_values": {
            "emoji_level": 0.001,
            "punctuation_type": 0.04
        },
        "post_hoc_results": [
            {"comparison": "high_vs_none", "estimate": 0.8, "p_value": 0.02}
        ],
        "timestamp": "2023-10-27T12:00:00Z"
    }

@pytest.fixture
def stimulus_schema():
    return load_yaml_schema("stimulus.schema.yaml")

@pytest.fixture
def rating_schema():
    return load_yaml_schema("rating.schema.yaml")

@pytest.fixture
def analysis_result_schema():
    return load_yaml_schema("analysis_result.schema.yaml")

def test_stimulus_schema_valid(stimulus_schema):
    data = generate_valid_stimulus_data()
    validate(instance=data, schema=stimulus_schema)

def test_stimulus_schema_invalid_id(stimulus_schema):
    data = generate_valid_stimulus_data()
    data["stimulus_id"] = "INVALID"
    with pytest.raises(ValidationError):
        validate(instance=data, schema=stimulus_schema)

def test_rating_schema_valid(rating_schema):
    data = generate_valid_rating_data()
    validate(instance=data, schema=rating_schema)

def test_rating_schema_invalid_participant_id(rating_schema):
    data = generate_valid_rating_data()
    data["participant_id"] = "P-INVALID"
    with pytest.raises(ValidationError):
        validate(instance=data, schema=rating_schema)

def test_analysis_result_schema_valid(analysis_result_schema):
    data = generate_valid_analysis_result_data()
    validate(instance=data, schema=analysis_result_schema)

def test_analysis_result_schema_invalid_p_value(analysis_result_schema):
    data = generate_valid_analysis_result_data()
    data["p_values"]["emoji_level"] = 1.5
    with pytest.raises(ValidationError):
        validate(instance=data, schema=analysis_result_schema)
