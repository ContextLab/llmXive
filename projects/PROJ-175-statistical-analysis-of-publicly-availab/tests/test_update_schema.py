import os
import json
import yaml
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
from code.data.update_schema import update_schema, load_amendment_log, load_schema, save_schema

@pytest.fixture
def temp_schema_dir():
    """Create a temporary directory for schema testing."""
    temp_dir = tempfile.mkdtemp()
    schema_path = os.path.join(temp_dir, "dataset.schema.yaml")
    
    # Create a minimal initial schema
    initial_schema = {
        "name": "recipe_dataset",
        "version": "1.0",
        "fields": [
            {"name": "ingredient_id", "type": "string"},
            {"name": "log_co_occurrence", "type": "float"}
        ],
        "metadata": {}
    }
    
    with open(schema_path, 'w') as f:
        yaml.dump(initial_schema, f)
    
    yield temp_dir, schema_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_amendment_log():
    """Create a temporary amendment log."""
    temp_dir = tempfile.mkdtemp()
    log_path = os.path.join(temp_dir, "amendment_log.json")
    
    log_data = {
        "status": "RATIFIED",
        "methodology": "Correlational Analysis",
        "proxy_source": "Recipe1M",
        "timestamp": "2023-10-27T10:00:00"
    }
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f)
    
    yield log_path
    shutil.rmtree(temp_dir)

def test_update_schema_correlational(temp_schema_dir):
    """Test schema update for Correlational Analysis methodology."""
    _, schema_path = temp_schema_dir
    schema = load_schema(schema_path)
    
    updated = update_schema(schema, "Correlational Analysis", "Recipe1M")
    
    # Find the flavor_similarity field
    flavor_sim = next((f for f in updated["fields"] if f["name"] == "flavor_similarity"), None)
    
    assert flavor_sim is not None, "flavor_similarity field should be added"
    assert flavor_sim["description"] == "Cosine similarity between ingredient embeddings from Recipe1M corpus."
    assert flavor_sim["source"] == "Recipe1M"
    assert updated["metadata"]["methodology"] == "Correlational Analysis"

def test_update_schema_causal(temp_schema_dir):
    """Test schema update for Causal Independence methodology."""
    _, schema_path = temp_schema_dir
    schema = load_schema(schema_path)
    
    updated = update_schema(schema, "Causal Independence", None)
    
    flavor_sim = next((f for f in updated["fields"] if f["name"] == "flavor_similarity"), None)
    
    assert flavor_sim is not None
    assert flavor_sim["description"] == "Chemical vector similarity derived from FlavorDB."
    assert flavor_sim["source"] == "FlavorDB"
    assert updated["metadata"]["methodology"] == "Causal Independence"

def test_save_schema(temp_schema_dir):
    """Test that save_schema writes the file correctly."""
    temp_dir, schema_path = temp_schema_dir
    schema = load_schema(schema_path)
    updated = update_schema(schema, "Correlational Analysis", "Recipe1M")
    
    save_schema(updated, schema_path)
    
    # Reload and verify
    with open(schema_path, 'r') as f:
        reloaded = yaml.safe_load(f)
    
    assert reloaded["metadata"]["methodology"] == "Correlational Analysis"
    assert len(reloaded["fields"]) == 3 # original 2 + flavor_similarity

def test_load_amendment_log_ratified(temp_amendment_log):
    """Test loading a ratified amendment log."""
    log = load_amendment_log(temp_amendment_log)
    assert log["status"] == "RATIFIED"
    assert log["methodology"] == "Correlational Analysis"

def test_load_amendment_log_not_ratified(temp_amendment_log, tmp_path):
    """Test that loading a non-ratified log raises an error."""
    unratified_path = tmp_path / "amendment_unratified.json"
    data = {"status": "PENDING", "methodology": "Causal Independence"}
    with open(unratified_path, 'w') as f:
        json.dump(data, f)
    
    with pytest.raises(RuntimeError, match="Must be 'RATIFIED'"):
        load_amendment_log(str(unratified_path))