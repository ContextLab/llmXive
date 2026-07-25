"""
Unit tests for schema generation and validation.
Verifies T005 implementation.
"""
import pytest
import pandas as pd
import os
from pathlib import Path

# Add project root to path
sys_path = Path(__file__).resolve().parent.parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from code.data.schemas import get_repo_metrics_schema, validate_dataframe
from code.config import ensure_directories, CONTRACTS_DIR

def test_schema_structure():
    """Test that the repo metrics schema has required fields."""
    schema = get_repo_metrics_schema()
    required_fields = [
        "url", "primary_language", "unique_authors", "kloc",
        "authorship_diversity", "cve_count", "project_age", "release_count"
    ]
    for field in required_fields:
        assert field in schema, f"Missing field {field} in schema"
        assert schema[field]["required"] is True

def test_dataframe_validation_valid():
    """Test validation passes on a valid dataframe."""
    df = pd.DataFrame({
        "url": ["https://github.com/test/repo"],
        "primary_language": ["Python"],
        "unique_authors": [5],
        "kloc": [10.5],
        "authorship_diversity": [0.47],
        "cve_count": [2],
        "project_age": [3.0],
        "release_count": [10]
    })
    schema = get_repo_metrics_schema()
    errors = validate_dataframe(df, schema)
    assert len(errors) == 0, f"Validation failed unexpectedly: {errors}"

def test_dataframe_validation_missing_column():
    """Test validation fails on missing column."""
    df = pd.DataFrame({
        "url": ["https://github.com/test/repo"],
        "primary_language": ["Python"]
    })
    schema = get_repo_metrics_schema()
    errors = validate_dataframe(df, schema)
    assert len(errors) > 0
    assert any("Missing required column" in e for e in errors)

def test_schema_files_exist():
    """Test that the YAML schema files were generated."""
    ensure_directories()
    assert (CONTRACTS_DIR / "repo_metrics.schema.yaml").exists()
    assert (CONTRACTS_DIR / "model_results.schema.yaml").exists()
    
    # Check content is valid YAML
    import yaml
    with open(CONTRACTS_DIR / "repo_metrics.schema.yaml", "r") as f:
        data = yaml.safe_load(f)
        assert "properties" in data
        assert "url" in data["properties"]