"""
Unit tests for T020b: Data Model Generation and Validation.
"""
import os
import sys
import yaml
import pytest
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from generate_data_model import generate_data_model, validate_against_spec, DATA_MODEL_PATH

def test_generate_data_model_structure():
    """Test that the generated model has the correct top-level keys."""
    model = generate_data_model()
    assert "version" in model
    assert "description" in model
    assert "entities" in model
    assert "constraints" in model

def test_required_entities_present():
    """Test that Participant, Stimulus, and Metric entities exist."""
    model = generate_data_model()
    entities = model["entities"]
    assert "Participant" in entities
    assert "Stimulus" in entities
    assert "Metric" in entities

def test_participant_fields():
    """Test that Participant has required fields including optional MMSE."""
    model = generate_data_model()
    participant = model["entities"]["Participant"]
    field_names = [f["name"] for f in participant["fields"]]
    
    assert "participant_id" in field_names
    assert "age" in field_names
    assert "MMSE" in field_names  # Must be present (even if optional in usage)

def test_stimulus_fields():
    """Test that Stimulus has required fields."""
    model = generate_data_model()
    stimulus = model["entities"]["Stimulus"]
    field_names = [f["name"] for f in stimulus["fields"]]
    
    assert "stimulus_id" in field_names
    assert "stimulus_type" in field_names
    assert "checksum_sha256" in field_names

def test_metric_fields():
    """Test that Metric has required WCST fields."""
    model = generate_data_model()
    metric = model["entities"]["Metric"]
    field_names = [f["name"] for f in metric["fields"]]
    
    assert "perseverative_errors" in field_names
    assert "categories_completed" in field_names
    assert "participant_id" in field_names  # FK

def test_validation_passes():
    """Test that the generated model passes internal validation."""
    model = generate_data_model()
    assert validate_against_spec(model) is True

def test_yaml_file_exists_and_loads():
    """Test that the main() function created a valid YAML file."""
    # Run the generator if not already done (side effect of test run)
    # In a real CI, this would ensure the file exists.
    if not DATA_MODEL_PATH.exists():
        # If running locally and file missing, generate it
        from generate_data_model import main
        main()
    
    assert DATA_MODEL_PATH.exists()
    
    with open(DATA_MODEL_PATH, 'r') as f:
        loaded_model = yaml.safe_load(f)
    
    assert loaded_model is not None
    assert "entities" in loaded_model
    assert "Participant" in loaded_model["entities"]