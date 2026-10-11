import pytest
import yaml
from pathlib import Path
from llmxive_toolkit import paths

def test_directories_exist():
    """Verify all required project directories are present."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "figures",
        "code/models",
        "code/metrics",
        "code/stats",
        "code/utils",
        "tests/unit",
        "tests/integration",
    ]
    for d in required_dirs:
        p = paths.root / d
        assert p.is_dir(), f"Required directory {d} is missing"

def test_schema_exists_and_is_correct():
    """Verify the per_sample_errors.schema.yaml exists and contains the correct columns and dtypes."""
    schema_path = paths.root / "specs" / "001-assessing-uncertainty-quantification-tec" / "contracts" / "per_sample_errors.schema.yaml"
    assert schema_path.is_file(), f"Schema file missing at {schema_path}"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    expected_cols = [
        "sample_id",
        "dataset",
        "method",
        "prediction",
        "lower_bound",
        "upper_bound",
        "ground_truth",
        "abs_error",
    ]
    
    columns = schema.get("columns", [])
    col_names = [c["name"] for c in columns]
    
    assert col_names == expected_cols, f"Expected columns {expected_cols}, but found {col_names}"
    
    for col in columns:
        assert "name" in col, f"Column entry {col} missing 'name'"
        assert "dtype" in col, f"Column entry {col} missing 'dtype'"

def test_spec_datasets_listed():
    """Verify SC-005 datasets are listed in spec.md."""
    spec_path = paths.root / "specs" / "001-assessing-uncertainty-quantification-tec" / "spec.md"
    assert spec_path.is_file(), "spec.md not found"
    
    content = spec_path.read_text()
    required_datasets = ["Band Gap", "Thermal Conductivity", "Formation Energy"]
    for ds in required_datasets:
        assert ds in content, f"Dataset '{ds}' not found in spec.md (SC-005)"