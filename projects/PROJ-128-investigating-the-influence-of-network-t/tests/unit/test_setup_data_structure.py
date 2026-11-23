import os
import yaml
from pathlib import Path
import sys

# Add code directory to path if not already there
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_structure import ensure_directories, create_schema_files

def test_directories_created():
    """Test that all required directories are created."""
    ensure_directories()
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/figures",
        "data/logs",
        "contracts",
        "code/preprocess",
        "code/analysis",
        "code/reports",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    for d in required_dirs:
        assert (Path(".") / d).exists(), f"Directory {d} was not created"

def test_schema_files_created():
    """Test that schema files are created and valid YAML."""
    create_schema_files()
    
    contracts_path = Path("contracts")
    
    # Check dataset.schema.yaml
    dataset_schema_path = contracts_path / "dataset.schema.yaml"
    assert dataset_schema_path.exists(), "dataset.schema.yaml not found"
    
    with open(dataset_schema_path, "r") as f:
        dataset_schema = yaml.safe_load(f)
    
    assert "name" in dataset_schema, "dataset.schema.yaml missing 'name'"
    assert dataset_schema["name"] == "HCP_Dataset_Schema"
    assert "entities" in dataset_schema, "dataset.schema.yaml missing 'entities'"
    assert "subject" in dataset_schema["entities"], "subject entity missing"
    
    # Check output.schema.yaml
    output_schema_path = contracts_path / "output.schema.yaml"
    assert output_schema_path.exists(), "output.schema.yaml not found"
    
    with open(output_schema_path, "r") as f:
        output_schema = yaml.safe_load(f)
    
    assert "name" in output_schema, "output.schema.yaml missing 'name'"
    assert output_schema["name"] == "Pipeline_Output_Schema"
    assert "files" in output_schema, "output.schema.yaml missing 'files'"
    
    # Verify required output files exist in schema
    required_files = [
        "structural_metrics.csv",
        "dynamic_metrics.csv",
        "correlation_results.csv",
        "exclusion_log.json",
        "completeness_report.json"
    ]
    
    for file_name in required_files:
        assert file_name in output_schema["files"], f"Missing schema for {file_name}"
