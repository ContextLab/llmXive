import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Add project root to path
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root / "code") not in sys.path:
    sys.path.insert(0, str(code_root / "code"))

from data.save_and_validate_graphs import (
    load_schema, 
    validate_graph_against_schema, 
    main
)
from utils.config import initialize_environment

@pytest.fixture
def temp_schema():
    """Create a temporary schema file for testing."""
    schema = {
        "type": "object",
        "required": ["pdb_id", "ligand_id", "resolution", "water_flag", "coordinates_3d", "atom_type", "charge", "hydrophobicity", "edges"],
        "properties": {
            "pdb_id": {"type": "string"},
            "ligand_id": {"type": "string"},
            "resolution": {"type": "number", "minimum": 0},
            "water_flag": {"type": "boolean"},
            "coordinates_3d": {"type": "array", "items": {"type": "number"}},
            "atom_type": {"type": "array", "items": {"type": "string"}},
            "charge": {"type": "array", "items": {"type": "number"}},
            "hydrophobicity": {"type": "array", "items": {"type": "number"}},
            "edges": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}}}
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(schema, f)
        return f.name

@pytest.fixture
def valid_graph_data():
    """Create a valid graph data structure for testing."""
    return {
        "pdb_id": "1ABC",
        "ligand_id": "LIG1",
        "resolution": 1.5,
        "water_flag": False,
        "coordinates_3d": [0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
        "atom_type": ["C", "C", "O"],
        "charge": [0.0, 0.0, -0.5],
        "hydrophobicity": [0.5, 0.5, -0.2],
        "edges": [[0, 1], [1, 2]]
    }

@pytest.fixture
def invalid_graph_data():
    """Create an invalid graph data structure for testing."""
    return {
        "pdb_id": 123,  # Should be string
        "ligand_id": "LIG1",
        "resolution": -1.0,  # Should be positive
        "water_flag": "yes",  # Should be boolean
        "coordinates_3d": [0.0, 0.0],  # Length not divisible by 3
        "atom_type": "C",  # Should be list
        "charge": [0.0, 0.0, -0.5],
        "hydrophobicity": [0.5, 0.5, -0.2],
        "edges": [[0, "a"], [1, 2]]  # Edge contains non-integer
    }

def test_load_schema(temp_schema):
    """Test loading a schema from a file."""
    schema = load_schema(temp_schema)
    assert "required" in schema
    assert "properties" in schema
    assert "pdb_id" in schema["properties"]
    os.unlink(temp_schema)

def test_load_schema_missing_file():
    """Test loading a non-existent schema file."""
    with pytest.raises(FileNotFoundError):
        load_schema("non_existent_file.yaml")

def test_validate_valid_graph(valid_graph_data, temp_schema):
    """Test validation of a valid graph."""
    schema = load_schema(temp_schema)
    errors = validate_graph_against_schema(valid_graph_data, schema)
    assert len(errors) == 0
    os.unlink(temp_schema)

def test_validate_invalid_graph(invalid_graph_data, temp_schema):
    """Test validation of an invalid graph."""
    schema = load_schema(temp_schema)
    errors = validate_graph_against_schema(invalid_graph_data, schema)
    assert len(errors) > 0
    assert any("pdb_id must be a string" in e for e in errors)
    assert any("resolution must be a positive float" in e for e in errors)
    assert any("water_flag must be a boolean" in e for e in errors)
    assert any("coordinates_3d must be a list of floats with length divisible by 3" in e for e in errors)
    assert any("atom_type must be a list" in e for e in errors)
    assert any("Edge at index 0 must contain integers" in e for e in errors)
    os.unlink(temp_schema)

def test_validate_missing_fields(valid_graph_data, temp_schema):
    """Test validation with missing required fields."""
    incomplete_graph = {k: v for k, v in valid_graph_data.items() if k != "pdb_id"}
    schema = load_schema(temp_schema)
    errors = validate_graph_against_schema(incomplete_graph, schema)
    assert any("Missing required field: pdb_id" in e for e in errors)
    os.unlink(temp_schema)

@pytest.mark.integration
def test_main_integration(temp_schema):
    """
    Integration test for the main function.
    This test mocks the data loading and processing functions to verify the 
    save and validation flow without requiring real PDBbind data.
    """
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    raw_dir = os.path.join(temp_dir, "raw")
    processed_dir = os.path.join(temp_dir, "processed")
    os.makedirs(raw_dir)
    os.makedirs(processed_dir)
    
    # Mock data
    mock_complexes = [
        {"pdb_id": "1ABC", "ligand_id": "LIG1", "resolution": 1.5, "atoms": [], "bonds": []},
        {"pdb_id": "2DEF", "ligand_id": "LIG2", "resolution": 2.0, "atoms": [], "bonds": []}
    ]
    
    mock_graphs = [
        {
            "pdb_id": "1ABC", "ligand_id": "LIG1", "resolution": 1.5, 
            "water_flag": False, "coordinates_3d": [0.0, 0.0, 0.0], 
            "atom_type": ["C"], "charge": [0.0], "hydrophobicity": [0.5], 
            "edges": []
        },
        {
            "pdb_id": "2DEF", "ligand_id": "LIG2", "resolution": 2.0, 
            "water_flag": False, "coordinates_3d": [1.0, 1.0, 1.0], 
            "atom_type": ["O"], "charge": [-0.5], "hydrophobicity": [-0.2], 
            "edges": []
        }
    ]
    
    # Patch the functions
    with patch('data.save_and_validate_graphs.load_pdbbind_refined', return_value=mock_complexes), \
         patch('data.save_and_validate_graphs.filter_by_resolution', return_value=mock_complexes), \
         patch('data.save_and_validate_graphs.construct_molecular_graphs', return_value=mock_graphs), \
         patch('data.save_and_validate_graphs.validate_and_filter_graphs', return_value=(mock_graphs, [])), \
         patch('data.save_and_validate_graphs.process_complex_metadata', return_value=mock_graphs), \
         patch('data.save_and_validate_graphs.get_config', return_value={
             'data_raw_dir': raw_dir,
             'data_processed_dir': processed_dir,
             'schema_path': temp_schema
         }):
        
        # Initialize environment to avoid config errors
        initialize_environment()
        
        # Run main
        main()
        
        # Check output file
        output_file = os.path.join(processed_dir, "processed_graphs.json")
        assert os.path.exists(output_file), f"Output file {output_file} was not created"
        
        with open(output_file, 'r') as f:
            saved_graphs = json.load(f)
        
        assert len(saved_graphs) == 2, f"Expected 2 graphs, got {len(saved_graphs)}"
        assert saved_graphs[0]["pdb_id"] == "1ABC"
        assert saved_graphs[1]["pdb_id"] == "2DEF"
    
    # Cleanup
    shutil.rmtree(temp_dir)