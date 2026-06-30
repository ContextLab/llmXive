import pytest
import json
import yaml
from pathlib import Path
from datetime import datetime
import uuid

# Import validation utilities from the project
from utils.io import validate_json_schema, SchemaValidationError

# Paths to schemas
SCHEMAS_DIR = Path("specs/contracts")
GENERATION_SCHEMA_PATH = SCHEMAS_DIR / "generation_output.schema.yaml"
VALIDITY_SCHEMA_PATH = SCHEMAS_DIR / "validity_scores.schema.yaml"
QUALITATIVE_SCHEMA_PATH = SCHEMAS_DIR / "qualitative_ratings.schema.yaml"

@pytest.fixture
def generation_sample():
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "strategy": "Direct",
        "prompt_id": "prompt_001",
        "prompt_text": "Describe your experience of seeing the color red.",
        "generated_text": "I see a vibrant red. It feels warm.",
        "model_id": "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF",
        "seed": 42,
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 100,
            "top_p": 0.9,
            "top_k": 40
        }
    }

@pytest.fixture
def validity_sample():
    return {
        "sample_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "consistency_score": 0.85,
            "stability_score": 0.92,
            "marker_scores": {
                "sensory": 5,
                "temporal": 3,
                "intentional": 2,
                "total_density": 12.5
            }
        },
        "strategy": "Direct"
    }

@pytest.fixture
def qualitative_sample():
    return {
        "rating_id": str(uuid.uuid4()),
        "sample_id": str(uuid.uuid4()),
        "rater_id": "R001",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "scores": {
            "phenomenological_quality": 4,
            "coherence": 5,
            "first_person_authenticity": 4,
            "overall_rating": 4
        },
        "comments": "Strong phenomenological description.",
        "rubric_version": "v1.0"
    }

def load_schema(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def test_generation_output_schema_valid(generation_sample):
    schema = load_schema(GENERATION_SCHEMA_PATH)
    try:
        validate_json_schema(generation_sample, schema)
    except SchemaValidationError as e:
        pytest.fail(f"Generation sample failed schema validation: {e}")

def test_generation_output_schema_invalid_strategy(generation_sample):
    generation_sample["strategy"] = "InvalidStrategy"
    schema = load_schema(GENERATION_SCHEMA_PATH)
    with pytest.raises(SchemaValidationError):
        validate_json_schema(generation_sample, schema)

def test_validity_scores_schema_valid(validity_sample):
    schema = load_schema(VALIDITY_SCHEMA_PATH)
    try:
        validate_json_schema(validity_sample, schema)
    except SchemaValidationError as e:
        pytest.fail(f"Validity sample failed schema validation: {e}")

def test_validity_scores_schema_missing_metric(validity_sample):
    del validity_sample["metrics"]["consistency_score"]
    schema = load_schema(VALIDITY_SCHEMA_PATH)
    with pytest.raises(SchemaValidationError):
        validate_json_schema(validity_sample, schema)

def test_qualitative_ratings_schema_valid(qualitative_sample):
    schema = load_schema(QUALITATIVE_SCHEMA_PATH)
    try:
        validate_json_schema(qualitative_sample, schema)
    except SchemaValidationError as e:
        pytest.fail(f"Qualitative sample failed schema validation: {e}")

def test_qualitative_ratings_schema_invalid_rater_id(qualitative_sample):
    qualitative_sample["rater_id"] = "INVALID"
    schema = load_schema(QUALITATIVE_SCHEMA_PATH)
    with pytest.raises(SchemaValidationError):
        validate_json_schema(qualitative_sample, schema)