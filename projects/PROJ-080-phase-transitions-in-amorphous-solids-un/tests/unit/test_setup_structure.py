import os
import yaml
from pathlib import Path
import pytest

# Import the setup function
from setup_project_structure import main

def test_project_structure_created():
    """Verify that the required directories are created."""
    # Run the setup
    main()

    # Check directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "specs/contracts",
        "state",
    ]

    for dir_path in required_dirs:
        assert Path(dir_path).exists(), f"Directory {dir_path} was not created"
        assert Path(dir_path).is_dir(), f"{dir_path} is not a directory"

def test_schema_files_created():
    """Verify that the schema files are created and valid YAML."""
    # Run the setup
    main()

    schema_files = [
        "specs/contracts/trajectory.schema.yaml",
        "specs/contracts/output.schema.yaml",
    ]

    for file_path in schema_files:
        assert Path(file_path).exists(), f"Schema file {file_path} was not created"
        
        # Verify it is valid YAML
        try:
            with open(file_path, "r") as f:
                content = yaml.safe_load(f)
                assert content is not None, f"Schema file {file_path} is empty or invalid"
                assert "properties" in content or "$schema" in content, f"Schema file {file_path} lacks expected structure"
        except yaml.YAMLError as e:
            pytest.fail(f"Schema file {file_path} is not valid YAML: {e}")

def test_trajectory_schema_validity():
    """Specific checks for trajectory.schema.yaml content."""
    main()
    file_path = "specs/contracts/trajectory.schema.yaml"
    
    with open(file_path, "r") as f:
        schema = yaml.safe_load(f)
    
    # Check required fields
    assert "properties" in schema
    assert "metadata" in schema["properties"]
    assert "frames" in schema["properties"]
    assert "required" in schema
    assert "metadata" in schema["required"]
    assert "frames" in schema["required"]

def test_output_schema_validity():
    """Specific checks for output.schema.yaml content."""
    main()
    file_path = "specs/contracts/output.schema.yaml"
    
    with open(file_path, "r") as f:
        schema = yaml.safe_load(f)
    
    # Check required fields
    assert "properties" in schema
    assert "precursor_metrics" in schema["properties"]
    assert "yield_flags" in schema["properties"]
    assert "required" in schema
    assert "precursor_metrics" in schema["required"]
    assert "yield_flags" in schema["required"]