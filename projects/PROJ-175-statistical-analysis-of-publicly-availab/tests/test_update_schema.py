import pytest
import json
import yaml
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
from code.data.update_schema import load_amendment_log, load_schema, update_schema, save_schema, main

@pytest.fixture
def temp_schema_file(tmp_path):
    """Create a temporary dataset schema file for testing."""
    schema = {
        "name": "IngredientPair",
        "fields": [
            {
                "name": "IngredientPair",
                "properties": {
                    "ingredient_id": {
                        "type": "str",
                        "description": "Unique identifier for the ingredient pair"
                    },
                    "log_co_occurrence": {
                        "type": "float",
                        "description": "Log-transformed co-occurrence frequency"
                    },
                    "flavor_similarity": {
                        "type": "float",
                        "description": "Flavor similarity score",
                        "source": "Unknown"
                    },
                    "functional_role": {
                        "type": "str",
                        "description": "Functional role of the ingredient"
                    },
                    "compatibility_label": {
                        "type": "int",
                        "description": "Binary compatibility label"
                    }
                }
            }
        ]
    }
    
    schema_file = tmp_path / "dataset.schema.yaml"
    with open(schema_file, 'w') as f:
        yaml.dump(schema, f)
    
    return schema_file

@pytest.fixture
def temp_amendment_file(tmp_path):
    """Create a temporary amendment log file for testing."""
    amendment = {
        "status": "RATIFIED",
        "methodology": "Correlational Analysis",
        "proxy_source": "Recipe1M",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    amendment_file = tmp_path / "amendment_log.json"
    with open(amendment_file, 'w') as f:
        json.dump(amendment, f)
    
    return amendment_file

def test_load_amendment_log_success(temp_amendment_file):
    """Test loading a valid amendment log."""
    with patch('code.data.update_schema.Path') as mock_path:
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.__truediv__.return_value.exists.return_value = True
        
        # Mock the open and json.load
        with patch('builtins.open', MagicMock()) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = json.dumps({
                "status": "RATIFIED",
                "methodology": "Correlational Analysis"
            })
            with patch('json.load', return_value={"status": "RATIFIED", "methodology": "Correlational Analysis"}):
                result = load_amendment_log()
                assert result["status"] == "RATIFIED"
                assert result["methodology"] == "Correlational Analysis"

def test_load_amendment_log_missing_file():
    """Test that load_amendment_log raises FileNotFoundError when file is missing."""
    with patch('code.data.update_schema.Path') as mock_path:
        mock_path.return_value.exists.return_value = False
        
        with pytest.raises(FileNotFoundError, match="Amendment log not found"):
            load_amendment_log()

def test_load_schema_success(temp_schema_file):
    """Test loading a valid schema file."""
    result = load_schema(temp_schema_file)
    assert "fields" in result
    assert len(result["fields"]) == 1
    assert result["fields"][0]["name"] == "IngredientPair"

def test_load_schema_missing_file(tmp_path):
    """Test that load_schema raises FileNotFoundError when file is missing."""
    missing_path = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError, match="Schema file not found"):
        load_schema(missing_path)

def test_update_schema_correlational(temp_schema_file):
    """Test schema update for Correlational Analysis methodology."""
    schema = load_schema(temp_schema_file)
    updated = update_schema(schema, "Correlational Analysis")
    
    flavor_sim = updated["fields"][0]["properties"]["flavor_similarity"]
    assert flavor_sim["description"] == "Recipe1M embedding cosine similarity"
    assert flavor_sim["source"] == "Recipe1M embeddings"
    assert flavor_sim["type"] == "float"

def test_update_schema_causal(temp_schema_file):
    """Test schema update for Causal Independence methodology."""
    schema = load_schema(temp_schema_file)
    updated = update_schema(schema, "Causal Independence")
    
    flavor_sim = updated["fields"][0]["properties"]["flavor_similarity"]
    assert flavor_sim["description"] == "FlavorDB chemical vectors"
    assert flavor_sim["source"] == "FlavorDB chemical matrix"
    assert flavor_sim["type"] == "float"

def test_update_schema_invalid_methodology(temp_schema_file):
    """Test that update_schema raises ValueError for invalid methodology."""
    schema = load_schema(temp_schema_file)
    
    with pytest.raises(ValueError, match="Unknown methodology"):
        update_schema(schema, "Invalid Methodology")

def test_save_schema(tmp_path):
    """Test saving a schema to a file."""
    schema = {
        "name": "TestSchema",
        "fields": [
            {
                "name": "TestField",
                "properties": {
                    "field1": {"type": "str", "description": "Test field"}
                }
            }
        ]
    }
    
    output_path = tmp_path / "test_schema.yaml"
    save_schema(schema, output_path)
    
    assert output_path.exists()
    
    # Verify the content
    with open(output_path, 'r') as f:
        loaded = yaml.safe_load(f)
    
    assert loaded["name"] == "TestSchema"
    assert len(loaded["fields"]) == 1

def test_main_success(temp_schema_file, temp_amendment_file, tmp_path):
    """Test the main function with valid inputs."""
    # Patch paths to use temp directories
    with patch('code.data.update_schema.Path') as mock_path:
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.__truediv__.return_value.exists.return_value = True
        
        # Mock load_amendment_log to return a valid RATIFIED log
        with patch('code.data.update_schema.load_amendment_log') as mock_load_amendment:
            mock_load_amendment.return_value = {
                "status": "RATIFIED",
                "methodology": "Correlational Analysis"
            }
            
            # Mock load_schema and save_schema
            with patch('code.data.update_schema.load_schema') as mock_load:
                mock_load.return_value = {
                    "fields": [
                        {
                            "name": "IngredientPair",
                            "properties": {
                                "flavor_similarity": {
                                    "type": "float",
                                    "description": "Old description"
                                }
                            }
                        }
                    ]
                }
                
                with patch('code.data.update_schema.save_schema') as mock_save:
                    result = main()
                    assert result == 0
                    mock_save.assert_called_once()

def test_main_unratified_amendment(temp_schema_file):
    """Test that main raises error if amendment is not ratified."""
    with patch('code.data.update_schema.Path') as mock_path:
        mock_path.return_value.exists.return_value = True
        
        with patch('code.data.update_schema.load_amendment_log') as mock_load:
            mock_load.return_value = {
                "status": "PENDING",
                "methodology": "Correlational Analysis"
            }
            
            with pytest.raises(RuntimeError, match="Amendment log status is 'PENDING'"):
                main()

def test_main_missing_schema(temp_amendment_file):
    """Test that main raises error if schema file is missing."""
    with patch('code.data.update_schema.Path') as mock_path:
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.__truediv__.return_value.exists.return_value = False
        
        with patch('code.data.update_schema.load_amendment_log') as mock_load:
            mock_load.return_value = {
                "status": "RATIFIED",
                "methodology": "Correlational Analysis"
            }
            
            with pytest.raises(FileNotFoundError, match="Dataset schema not found"):
                main()
