import os
import json
import yaml
import pytest
import numpy as np
from jsonschema import validate, ValidationError

# Ensure we are in the project root context
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Schema paths
TASK_SCHEMA_PATH = "contracts/task.schema.yaml"
SKILL_SCHEMA_PATH = "contracts/skill.schema.yaml"
LOG_SCHEMA_PATH = "contracts/experiment_log.schema.yaml"
SKILLS_DATA_PATH = "data/raw/skills.json"

def load_schema(schema_path):
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# --- Task Schema Tests ---

def test_task_schema_exists_and_valid():
    """Test that the task schema file is valid YAML and JSON Schema."""
    schema = load_schema(TASK_SCHEMA_PATH)
    assert "$schema" in schema
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert "properties" in schema
    assert "required" in schema
    assert "task_id" in schema["properties"]
    assert "ground_truth_path" in schema["properties"]

def test_task_entry_compliance():
    """Test that a valid task entry conforms to the schema."""
    schema = load_schema(TASK_SCHEMA_PATH)
    
    valid_task = {
        "task_id": "T001",
        "description": "Calculate average of a list",
        "ground_truth_path": ["S1", "S2"],
        "complexity": 2,
        "embedding_vector": [0.1, 0.2, 0.3, 0.4, 0.5],
        "edge_case": False
    }
    
    try:
        validate(instance=valid_task, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid task entry failed schema validation: {e.message}")

def test_task_entry_missing_required():
    """Test that a task entry with missing required fields fails validation."""
    schema = load_schema(TASK_SCHEMA_PATH)
    
    invalid_task = {
        "task_id": "T001",
        "description": "Missing ground truth"
        # Missing ground_truth_path, complexity, embedding_vector
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=schema)

def test_task_entry_extra_properties():
    """Test that extra properties are rejected if additionalProperties is false."""
    schema = load_schema(TASK_SCHEMA_PATH)
    
    invalid_task = {
        "task_id": "T001",
        "description": "Test",
        "ground_truth_path": [],
        "complexity": 1,
        "embedding_vector": [0.1],
        "extra_field": "should fail"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_task, schema=schema)

# --- Skill Schema Tests ---

def test_skill_schema_exists_and_valid():
    """Test that the skill schema file is valid YAML and JSON Schema."""
    schema = load_schema(SKILL_SCHEMA_PATH)
    assert "$schema" in schema
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert "properties" in schema
    assert "required" in schema
    assert "skill_id" in schema["properties"]
    assert "function_code" in schema["properties"]
    assert "embedding_vector" in schema["properties"]
    assert "usage_count" in schema["properties"]
    assert "mean_cosine_similarity" in schema["properties"]

def test_skill_entry_compliance():
    """Test that a valid skill entry conforms to the schema."""
    schema = load_schema(SKILL_SCHEMA_PATH)
    
    valid_skill = {
        "skill_id": "S1",
        "function_code": "def add(a, b): return a + b",
        "embedding_vector": [0.1, 0.2, 0.3],
        "usage_count": 5,
        "mean_cosine_similarity": 0.45
    }
    
    try:
        validate(instance=valid_skill, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid skill entry failed schema validation: {e.message}")

def test_skill_entry_missing_required():
    """Test that a skill entry with missing required fields fails validation."""
    schema = load_schema(SKILL_SCHEMA_PATH)
    
    invalid_skill = {
        "skill_id": "S1"
        # Missing function_code, embedding_vector, usage_count
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_skill, schema=schema)

def test_skill_entry_invalid_types():
    """Test that skill entry with invalid types fails validation."""
    schema = load_schema(SKILL_SCHEMA_PATH)
    
    invalid_skill = {
        "skill_id": "S1",
        "function_code": "def x(): pass",
        "embedding_vector": "not a list", # Should be list
        "usage_count": "five", # Should be int
        "mean_cosine_similarity": 1.5 # Out of range if we enforce -1 to 1 strictly, but schema says min/max
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_skill, schema=schema)

# --- Real Data Contract Tests for Skills (T012 Specific) ---

def test_real_skills_schema_compliance():
    """
    Contract test: Validate that the generated data/raw/skills.json
    file strictly conforms to contracts/skill.schema.yaml.
    """
    if not os.path.exists(SKILLS_DATA_PATH):
        pytest.skip(f"Real data file {SKILLS_DATA_PATH} not found. Run generate_data.py first.")
    
    schema = load_schema(SKILL_SCHEMA_PATH)
    
    with open(SKILLS_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # The file might be a list of skills or a dict with a 'skills' key.
    # Based on typical generate_data.py outputs, we expect a list.
    if isinstance(data, dict) and 'skills' in data:
        skills_list = data['skills']
    elif isinstance(data, list):
        skills_list = data
    else:
        pytest.fail(f"Unexpected data structure in {SKILLS_DATA_PATH}: {type(data)}")
    
    assert len(skills_list) > 0, "Skills list is empty."
    
    errors = []
    for i, skill in enumerate(skills_list):
        try:
            validate(instance=skill, schema=schema)
        except ValidationError as e:
            errors.append(f"Skill {i} (ID: {skill.get('skill_id', 'N/A')}): {e.message}")
    
    if errors:
        pytest.fail(f"Schema validation failed for {len(errors)} skills:\n" + "\n".join(errors))

def test_real_skills_overlap_metrics():
    """
    Contract test: Verify that the mean_cosine_similarity field in real skills
    matches the configured OVERLAP_LEVEL thresholds defined in the spec.
    This ensures the data generation logic respected the overlap contract.
    """
    if not os.path.exists(SKILLS_DATA_PATH):
        pytest.skip(f"Real data file {SKILLS_DATA_PATH} not found. Run generate_data.py first.")
    
    with open(SKILLS_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if isinstance(data, dict) and 'skills' in data:
        skills_list = data['skills']
    elif isinstance(data, list):
        skills_list = data
    else:
        pytest.fail(f"Unexpected data structure in {SKILLS_DATA_PATH}")
    
    # Extract similarity scores
    scores = [s.get('mean_cosine_similarity', 0.0) for s in skills_list]
    
    if not scores:
        pytest.skip("No similarity scores found in skills data.")
    
    # Calculate aggregate metrics
    mean_score = np.mean(scores)
    std_score = np.std(scores)
    
    # Load config to determine expected thresholds
    # We assume config.py is available and has get_experiment_config
    try:
        from code.config import get_experiment_config
        config = get_experiment_config()
        overlap_level = config.get('OVERLAP_LEVEL', 'medium')
    except ImportError:
        # Fallback if config not loaded yet, assume medium for test logic
        overlap_level = 'medium'
    
    # Assertions based on overlap level
    if overlap_level == 'low':
        assert mean_score < 0.30, f"Low overlap expected <0.30, got {mean_score:.4f}"
    elif overlap_level == 'medium':
        assert 0.50 <= mean_score <= 0.80, f"Medium overlap expected [0.50, 0.80], got {mean_score:.4f}"
        # Also check that a significant portion is > 0.50
        high_count = sum(1 for s in scores if s > 0.50)
        assert high_count / len(scores) > 0.30, "Medium overlap requires >30% pairs >0.50"
    elif overlap_level == 'high':
        assert mean_score > 0.80, f"High overlap expected >0.80, got {mean_score:.4f}"
        high_count = sum(1 for s in scores if s > 0.80)
        assert high_count / len(scores) > 0.30, "High overlap requires >30% pairs >0.80"
    
    # Log the metrics for verification
    print(f"Overlap Level: {overlap_level}, Mean Similarity: {mean_score:.4f}, Std Dev: {std_score:.4f}")

# --- Experiment Log Schema Tests ---

def test_log_schema_exists_and_valid():
    """Test that the log schema file is valid YAML and JSON Schema."""
    schema = load_schema(LOG_SCHEMA_PATH)
    assert "$schema" in schema
    assert "properties" in schema
    assert "task_id" in schema["properties"]

def test_log_entry_compliance():
    """Test that a valid log entry conforms to the schema."""
    schema = load_schema(LOG_SCHEMA_PATH)
    
    valid_entry = {
        "task_id": "T001",
        "skill_id": "S1",
        "success": True,
        "latency": 0.5,
        "tokens": 100,
        "retrieval_precision": 1.0,
        "retrieval_diversity": 0.9,
        "pruning_risk_count": 0,
        "library_size": 10,
        "pruning_enabled": False,
        "edge_case": False
    }
    
    try:
        validate(instance=valid_entry, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid log entry failed schema validation: {e.message}")

def test_log_entry_missing_required():
    """Test that a log entry with missing required fields fails validation."""
    schema = load_schema(LOG_SCHEMA_PATH)
    
    invalid_entry = {
        "task_id": "T001",
        "skill_id": "S1"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=schema)

def test_log_entry_extra_properties():
    """Test that extra properties are rejected if additionalProperties is false."""
    schema = load_schema(LOG_SCHEMA_PATH)
    
    invalid_entry = {
        "task_id": "T001",
        "skill_id": "S1",
        "success": True,
        "latency": 0.5,
        "tokens": 100,
        "retrieval_precision": 1.0,
        "retrieval_diversity": 0.9,
        "pruning_risk_count": 0,
        "library_size": 10,
        "pruning_enabled": False,
        "edge_case": False,
        "extra_field": "should fail"
    }
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_entry, schema=schema)