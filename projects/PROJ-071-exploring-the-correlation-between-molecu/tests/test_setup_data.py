"""
Tests for T004: Verify data directories and schema file creation.
"""
import os
import yaml
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.setup_data import main

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent

def test_directories_created(project_root):
    """Verify that required directories exist after running setup."""
    # Run the setup script
    main()

    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    output_dir = data_dir / "output"

    assert raw_dir.exists(), "data/raw/ directory not created"
    assert raw_dir.is_dir(), "data/raw/ is not a directory"
    
    assert processed_dir.exists(), "data/processed/ directory not created"
    assert processed_dir.is_dir(), "data/processed/ is not a directory"
    
    assert output_dir.exists(), "data/output/ directory not created"
    assert output_dir.is_dir(), "data/output/ is not a directory"

def test_schema_file_created(project_root):
    """Verify that output_schema.yaml is created and valid."""
    # Run the setup script
    main()

    schema_path = project_root / "data" / "output_schema.yaml"
    assert schema_path.exists(), "data/output_schema.yaml not created"
    
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    assert "name" in schema, "Schema missing 'name' field"
    assert "version" in schema, "Schema missing 'version' field"
    assert "files" in schema, "Schema missing 'files' field"
    
    # Verify expected files are in schema
    expected_files = [
        "merged_drugs.csv",
        "analysis_results.json",
        "data_insufficiency_report.md",
        "errors.log"
    ]
    
    for file_name in expected_files:
        assert file_name in schema["files"], f"Schema missing expected file: {file_name}"

def test_schema_structure(project_root):
    """Verify schema has correct structure for merged_drugs.csv."""
    main()
    
    schema_path = project_root / "data" / "output_schema.yaml"
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)
    
    csv_schema = schema["files"]["merged_drugs.csv"]
    assert "columns" in csv_schema, "merged_drugs.csv schema missing 'columns'"
    
    expected_columns = [
        "smiles", "molecular_weight", "tpsa", "rotatable_bonds",
        "aromatic_rings", "wiener_index", "zagreb_index", 
        "half_life_hours", "condition_type"
    ]
    
    column_names = [col["name"] for col in csv_schema["columns"]]
    for col_name in expected_columns:
        assert col_name in column_names, f"Schema missing column: {col_name}"